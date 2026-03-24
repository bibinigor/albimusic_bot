"""
winback.py — Рассылка для возврата неактивных пользователей @AlBimusic_bot

Три сегмента:
  A — Никогда не генерировали: День 3, 10, 21
  B — Слышали демо, не заплатили: День 2, 7, 21
  C — Платили, ушли: День 14

Запуск через cron (каждый день в 11:00 МСК = 08:00 UTC):
  0 8 * * * cd /root/albimusic-bot && /root/albimusic-bot/venv/bin/python3 winback.py >> /var/log/albimusic/winback.log 2>&1
"""
import asyncio
import logging
import sys
import os
import psycopg2
import psycopg2.extras
from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, UserDeactivated
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("albi_winback")

# ─── Конфиг БД и бота ────────────────────────────────────────

BOT_TOKEN = os.getenv('BOT_TOKEN', '8078747945:AAELaCEzbPUdwwilFBy_TJi9LsBb5scyzVU')
BOT_USERNAME = 'AlBimusic_bot'

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'albimusic_bot'),
    'user': os.getenv('DB_USER', 'albimusic_user'),
    'password': os.getenv('DB_PASSWORD', 'aXAnAixKT6@?B9'),
}


def db_execute(sql, params=None, fetch_all=False):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch_all:
                    return cur.fetchall()
    finally:
        conn.close()


# ─── Тексты сообщений ────────────────────────────────────────

# Сегмент A: зашёл, ничего не создал
MSG_A1 = """\
🎵 *Ты ещё не создал свою первую песню!*

Это проще, чем кажется: выбери жанр, опиши идею \\
(или дай нам придумать за тебя) — и через 2 минуты \\
у тебя готовый трек.

*Первая генерация — бесплатно.*

👉 /start → «🎵 Создать песню»"""

MSG_A2 = """\
🎁 *День рождения друга? Признание? Просто «я думаю о тебе»?*

Персональная песня — самый необычный подарок, \\
который люди запоминают надолго.

AI создаёт её за 2 минуты по твоему описанию.

*Первая песня — бесплатно.*
*Пригласи друга — получишь ещё 2 токена бесплатно!*

👉 /start"""

MSG_A3 = """\
🎶 *Мы всё ещё здесь — и твоя первая песня тоже.*

Сотни людей уже создали треки под дни рождения, \\
признания и просто настроение.

*Первая генерация всегда бесплатна.* \\
А если позовёшь друга — получишь 2 дополнительных токена.

👉 /start"""

# Сегмент B: слушал демо, не разблокировал
MSG_B1 = """\
🎧 *Твоя демо-запись всё ещё здесь!*

Ты уже слышал свой трек — теперь самое время \\
получить *полную версию без ограничений*.

Разблокировать → *1 токен (50₽)*

Нет токенов? *Пригласи друга* — получишь 2 токена бесплатно!

👉 /start → «📂 История»"""

MSG_B2 = """\
💌 *Кому бы ты отправил свой трек?*

Другу? Любимому человеку? Выложил бы в сторис?

Из бота можно поделиться прямо в один клик. \\
А полная версия стоит всего *1 токен (50₽)*.

Нет токенов — пригласи друга, получишь 2 бесплатно 🎁

👉 /start"""

MSG_B3 = """\
🎵 *Трек всё ещё ждёт тебя.*

Кстати — можешь сделать *кавер в другом стиле* (2 токена) \\
или *экспортировать в WAV* для монтажа (1 токен).

Полная версия — *1 токен (50₽).* \\
Или пригласи друга и получи 2 токена бесплатно 🌟

👉 /start → «📂 История»"""

# Сегмент C: платил, ушёл
MSG_C1 = """\
🌟 *Давно не создавал новый трек!*

Твоя история генераций сохранена — всё ещё доступна.

Попробуй что-то новое: *кавер в другом жанре* \\
или *инструментальную версию* своей идеи.

👉 /start → «🎵 Создать песню»"""


# ─── Запросы к БД ────────────────────────────────────────────

def get_segment_a(tier):
    """Зашли, ничего не создали. Tier 1/2/3 по давности."""
    windows = {
        1: ("3 days",  "10 days"),   # 3-9 дней неактивны
        2: ("10 days", "21 days"),   # 10-20 дней
        3: ("21 days", "90 days"),   # 21+ дней
    }
    start, end = windows[tier]
    return db_execute(f"""
        SELECT user_id FROM users
        WHERE free_generation_used = false
          AND last_active < NOW() - INTERVAL '{start}'
          AND last_active > NOW() - INTERVAL '{end}'
          AND winback_sent < 3
          AND (last_winback_at IS NULL OR last_winback_at < NOW() - INTERVAL '4 days')
          AND last_active > NOW() - INTERVAL '90 days'
    """, fetch_all=True) or []


def get_segment_b(tier):
    """Слышали демо, не заплатили. Tier 1/2/3 по давности."""
    windows = {
        1: ("2 days",  "7 days"),
        2: ("7 days",  "21 days"),
        3: ("21 days", "90 days"),
    }
    start, end = windows[tier]
    return db_execute(f"""
        SELECT u.user_id FROM users u
        WHERE u.free_generation_used = true
          AND NOT EXISTS (
              SELECT 1 FROM payments p
              WHERE p.user_id = u.user_id AND p.status = 'succeeded'
          )
          AND u.last_active < NOW() - INTERVAL '{start}'
          AND u.last_active > NOW() - INTERVAL '{end}'
          AND u.winback_sent < 3
          AND (u.last_winback_at IS NULL OR u.last_winback_at < NOW() - INTERVAL '4 days')
    """, fetch_all=True) or []


def get_segment_c():
    """Платили, ушли 14+ дней назад."""
    return db_execute("""
        SELECT u.user_id FROM users u
        WHERE EXISTS (
            SELECT 1 FROM payments p
            WHERE p.user_id = u.user_id AND p.status = 'succeeded'
        )
          AND u.last_active < NOW() - INTERVAL '14 days'
          AND u.last_active > NOW() - INTERVAL '90 days'
          AND u.winback_sent < 3
          AND (u.last_winback_at IS NULL OR u.last_winback_at < NOW() - INTERVAL '7 days')
    """, fetch_all=True) or []


def mark_winback(user_id):
    db_execute("""
        UPDATE users
        SET winback_sent = winback_sent + 1,
            last_winback_at = NOW()
        WHERE user_id = %s
    """, (user_id,))


def mark_blocked(user_id):
    """Заблокировал бота — ставим winback_sent = 99, больше не беспокоим."""
    db_execute("UPDATE users SET winback_sent = 99 WHERE user_id = %s", (user_id,))


# ─── Основная логика ─────────────────────────────────────────

TIERS = [
    ("A1", get_segment_a, 1, MSG_A1),
    ("A2", get_segment_a, 2, MSG_A2),
    ("A3", get_segment_a, 3, MSG_A3),
    ("B1", get_segment_b, 1, MSG_B1),
    ("B2", get_segment_b, 2, MSG_B2),
    ("B3", get_segment_b, 3, MSG_B3),
    ("C",  None,          0, MSG_C1),
]


async def send_winback():
    bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
    total_sent = 0
    total_blocked = 0
    total_errors = 0

    segments = [
        ("A1", get_segment_a(1),  MSG_A1),
        ("A2", get_segment_a(2),  MSG_A2),
        ("A3", get_segment_a(3),  MSG_A3),
        ("B1", get_segment_b(1),  MSG_B1),
        ("B2", get_segment_b(2),  MSG_B2),
        ("B3", get_segment_b(3),  MSG_B3),
        ("C",  get_segment_c(),   MSG_C1),
    ]

    for name, users, msg in segments:
        log.info(f"Сегмент {name}: {len(users)} пользователей")
        for row in users:
            uid = row['user_id']
            try:
                await bot.send_message(uid, msg)
                mark_winback(uid)
                total_sent += 1
                await asyncio.sleep(0.05)
            except (BotBlocked, ChatNotFound, UserDeactivated):
                mark_blocked(uid)
                total_blocked += 1
            except Exception as e:
                log.warning(f"Ошибка uid={uid} сегмент={name}: {e}")
                total_errors += 1

    session = await bot.get_session()
    if session:
        await session.close()

    log.info(
        f"Готово: отправлено {total_sent}, "
        f"заблокировали бота {total_blocked}, "
        f"ошибок {total_errors}"
    )


if __name__ == "__main__":
    asyncio.run(send_winback())
