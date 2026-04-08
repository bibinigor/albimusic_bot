#!/usr/bin/env python3
"""
🔄 VK Win-back: отправка напоминания пользователям через 24 часа после первой генерации
Запускать через cron: каждый час
  0 * * * * /root/albimusic-bot/web_venv/bin/python3 /root/albimusic-bot/vk_winback.py >> /var/log/albimusic/vk_winback.log 2>&1

Логика:
  - Ищем VK-пользователей у которых:
    1. Ровно 1 завершённая генерация (completed)
    2. Она была создана от 22 до 26 часов назад (24ч ± 2ч допуск)
    3. Нет ни одного платежа (status='succeeded')
    4. Флаг winback_sent IS NULL или FALSE
  - Отправляем им сообщение с кнопкой "5 треков за 99₽"
"""

import os
import sys
import logging
from datetime import datetime

sys.path.append('/root/albimusic-bot')

from db_utils import init_db_pool_sync, execute_query_sync

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [vk_winback] %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ─── Конфигурация VK API ────────────────────────────────────────────────────
try:
    from vk_config import VK_GROUP_TOKEN, VK_GROUP_ID
except ImportError:
    VK_GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN', '')
    VK_GROUP_ID   = os.getenv('VK_GROUP_ID', '')

# ─── Текст сообщения ────────────────────────────────────────────────────────
WINBACK_MESSAGE = (
    "👋 Привет! Вчера ты создал свою первую песню в ALBI Music 🎵\n\n"
    "Понравилось? Большинство наших пользователей не останавливаются на одной!\n\n"
    "🎁 Специально для тебя — пакет «Старт»: 5 полных треков всего за 99₽\n"
    "Хватит на: трек про друга, признание в любви, поздравление маме или просто для кайфа!\n\n"
    "👇 Жми кнопку «Баланс» и выбери пакет 99₽ — предложение ограничено!"
)


def send_vk_message(user_id: int, message: str) -> bool:
    """Отправляет сообщение пользователю VK через API."""
    try:
        import requests
        import random

        resp = requests.post(
            'https://api.vk.com/method/messages.send',
            params={
                'user_id':       user_id,
                'message':       message,
                'random_id':     random.randint(1, 2**31),
                'access_token':  VK_GROUP_TOKEN,
                'v':             '5.131',
            },
            timeout=10
        )
        data = resp.json()
        if 'error' in data:
            logger.warning(f"VK API error for user {user_id}: {data['error']}")
            return False
        logger.info(f"✅ Win-back отправлен user {user_id} (msg_id={data.get('response')})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки win-back для {user_id}: {e}")
        return False


def main():
    init_db_pool_sync()
    logger.info("🚀 VK Win-back запущен")

    # Проверяем: есть ли колонка winback_sent в таблице users
    # Если нет — создаём
    try:
        execute_query_sync(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS winback_sent BOOLEAN DEFAULT FALSE"
        )
    except Exception as e:
        logger.warning(f"⚠️ Не удалось добавить колонку winback_sent: {e}")

    # Ищем кандидатов на win-back
    candidates = execute_query_sync(
        """
        SELECT u.user_id
        FROM users u
        WHERE u.provider = 'vk'
          AND (u.winback_sent IS NULL OR u.winback_sent = FALSE)
          -- Ровно 1 завершённая генерация
          AND (
              SELECT COUNT(*)
              FROM generations g
              WHERE g.user_id = u.user_id AND g.status = 'completed'
          ) = 1
          -- Первая генерация была 22–26 часов назад
          AND (
              SELECT MAX(g2.created_at)
              FROM generations g2
              WHERE g2.user_id = u.user_id AND g2.status = 'completed'
          ) BETWEEN NOW() - INTERVAL '26 hours' AND NOW() - INTERVAL '22 hours'
          -- Нет ни одного успешного платежа
          AND NOT EXISTS (
              SELECT 1 FROM payments p
              WHERE p.user_id = u.user_id AND p.status = 'succeeded'
          )
        LIMIT 50
        """
    )

    if not candidates:
        logger.info("ℹ️ Нет кандидатов для win-back")
        return

    logger.info(f"📋 Найдено кандидатов для win-back: {len(candidates)}")

    sent_count = 0
    for (user_id,) in candidates:
        success = send_vk_message(user_id, WINBACK_MESSAGE)
        if success:
            # Помечаем как отправленный
            try:
                execute_query_sync(
                    "UPDATE users SET winback_sent = TRUE WHERE user_id = %s",
                    (user_id,)
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка обновления winback_sent для {user_id}: {e}")
        else:
            # Если ошибка отправки — тоже помечаем чтобы не спамить
            try:
                execute_query_sync(
                    "UPDATE users SET winback_sent = TRUE WHERE user_id = %s",
                    (user_id,)
                )
            except Exception:
                pass

        # Небольшая пауза между сообщениями (VK rate limit)
        import time
        time.sleep(0.3)

    logger.info(f"✅ Win-back завершён. Отправлено: {sent_count}/{len(candidates)}")


if __name__ == "__main__":
    main()
