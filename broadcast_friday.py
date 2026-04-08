#!/usr/bin/env python3
"""
broadcast_friday.py — Одноразовая пятничная рассылка пакета «Выходные» за 99₽.

Запускать через cron каждую пятницу (например, в 17:00 по МСК):
  0 14 * * 5 /usr/bin/python3 /root/albimusic-bot/broadcast_friday.py >> /var/log/albimusic/broadcast_friday.log 2>&1

Каждый пользователь получит сообщение ТОЛЬКО ОДИН РАЗ.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync, init_db_pool_sync
from config import BOT_TOKEN as TELEGRAM_BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 30       # Сколько пользователей отправлять за раз
DELAY_BETWEEN = 0.05  # Задержка между отправками (сек.) — не превышать лимиты Telegram


async def send_friday_broadcast():
    """Отправляет пятничную рассылку всем пользователям, кто ещё не получил её"""
    init_db_pool_sync()

    today = datetime.now()
    if today.weekday() != 4:
        # 4 == пятница; если не пятница — выходим
        logger.warning(f"⚠️ Сегодня не пятница ({today.strftime('%A')}). Рассылка не запущена.")
        return

    logger.info("🍻 Запуск пятничной рассылки пакета «Выходные»...")

    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🕺 Забрать пакет «Выходные»", callback_data="pay_99_weekend")
    )

    message_text = (
        "🍻 Пятница! Идёшь тусить, в бар или к друзьям?\n\n"
        "Стань звездой вечеринки! Сделай за пару кликов танцевальный трек, "
        "в котором будут упомянуты все твои друзья по именам. "
        "Включи его на колонке — они выпадут в осадок!\n\n"
        "🔥 Забирай пакет «Выходные» (5 генераций всего за 99₽ вместо 250₽) "
        "и создай разрывной хит для своей компании:"
    )

    # Получаем пользователей, которые ещё не получили рассылку
    users = execute_query_sync(
        """SELECT user_id FROM users
           WHERE (friday_broadcast_sent IS NULL OR friday_broadcast_sent = FALSE)
           AND user_id IS NOT NULL
           ORDER BY created_at ASC"""
    )

    if not users:
        logger.info("✅ Нет пользователей для рассылки (все уже получили)")
        await bot.close()
        return

    total = len(users)
    sent_ok = 0
    failed = 0

    logger.info(f"📋 Найдено {total} пользователей для рассылки")

    for i, (user_id,) in enumerate(users):
        try:
            await bot.send_message(
                user_id,
                message_text,
                reply_markup=markup
            )
            # Отмечаем как отправленное
            execute_query_sync(
                "UPDATE users SET friday_broadcast_sent = TRUE WHERE user_id = %s",
                (user_id,)
            )
            sent_ok += 1

            if sent_ok % 100 == 0:
                logger.info(f"📨 Отправлено: {sent_ok}/{total}")

            # Небольшая пауза чтобы не спамить Telegram API
            await asyncio.sleep(DELAY_BETWEEN)

        except Exception as e:
            err_str = str(e)
            # Если бот заблокирован пользователем — просто отмечаем как отправленное
            if 'blocked' in err_str.lower() or 'deactivated' in err_str.lower() or 'chat not found' in err_str.lower():
                execute_query_sync(
                    "UPDATE users SET friday_broadcast_sent = TRUE WHERE user_id = %s",
                    (user_id,)
                )
                logger.debug(f"⛔ User {user_id} заблокировал бота, помечаем как отправлено")
            else:
                failed += 1
                logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")

            await asyncio.sleep(DELAY_BETWEEN)

    await bot.close()
    logger.info(f"✅ Рассылка завершена. Успешно: {sent_ok}, Ошибок: {failed}, Всего: {total}")


if __name__ == "__main__":
    asyncio.run(send_friday_broadcast())
