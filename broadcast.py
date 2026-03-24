"""
broadcast.py — Рассылка сообщений пользователям AlBi Music бота

ИСПОЛЬЗОВАНИЕ:
  python3 broadcast.py           — тестовый режим (только тебе)
  python3 broadcast.py --send    — полная рассылка всем пользователям

ПЕРЕД ЗАПУСКОМ:
  Вставь своё сообщение в MESSAGE ниже.
  Переменные доступны: {name} — имя или @username пользователя
"""

import asyncio
import argparse
import logging
import sys
import psycopg2
from datetime import datetime
import httpx

# ─────────────────────────────────────────────
#  НАСТРОЙКИ — МЕНЯЙ ЗДЕСЬ
# ─────────────────────────────────────────────

BOT_TOKEN = "8078747945:AAELaCEzbPUdwwilFBy_TJi9LsBb5scyzVU"
ADMIN_ID  = 338544009   # твой user_id — для тестового режима

# Текст сообщения. {name} заменится на имя пользователя.
# Поддерживает HTML: <b>жирный</b>, <i>курсив</i>, <a href="...">ссылка</a>
MESSAGE = """🎵 <b>Новости ALBI Music для {name}!</b>

🔓 <b>Полная версия песни — теперь в 3 раза дешевле!</b>

Раньше вы получали 45-секундное демо, а чтобы разблокировать полную версию — нужно было заплатить 300 ₽. Мы снизили этот порог до <b>100 ₽ (1 токен)</b> 🎉

✨ <b>Что ещё изменилось:</b>

🎵 Раньше минимальный пакет — 10 песен за 500 ₽
→ Теперь можно купить <b>1 токен за 100 ₽</b> и сразу создать одну песню в двух вариантах

Попробуй прямо сейчас 👉 @AlBimusic_bot""".strip()

# Inline-кнопка под сообщением (None — без кнопки)
BUTTON_TEXT = None
BUTTON_URL  = None

# Задержка между сообщениями (секунд). 1.0 — безопасно, 0.5 — быстро но рискованно
DELAY = 1.0

# ─────────────────────────────────────────────
#  ПОДКЛЮЧЕНИЕ К БД
# ─────────────────────────────────────────────

DB = dict(
    host="localhost",
    port=5432,
    database="albimusic_bot",
    user="albimusic_user",
    password="aXAnAixKT6@?B9",
)

# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("broadcast")


def get_users(test_mode: bool) -> list[dict]:
    """Возвращает список пользователей из БД."""
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    if test_mode:
        cur.execute(
            "SELECT user_id, username, first_name FROM users WHERE user_id = %s",
            (ADMIN_ID,)
        )
    else:
        cur.execute(
            "SELECT user_id, username, first_name FROM users ORDER BY created_at"
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"user_id": r[0], "username": r[1], "first_name": r[2]} for r in rows]


def make_name(user: dict) -> str:
    """Формирует имя для обращения."""
    if user["first_name"]:
        return user["first_name"]
    if user["username"]:
        return f"@{user['username']}"
    return "друг"


async def send_one(client: httpx.AsyncClient, user: dict) -> str:
    """Отправляет сообщение одному пользователю. Возвращает статус."""
    name = make_name(user)
    text = MESSAGE.format(name=name)

    payload = {
        "chat_id":    user["user_id"],
        "text":       text,
        "parse_mode": "HTML",
    }

    if BUTTON_TEXT and BUTTON_URL:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": BUTTON_TEXT, "url": BUTTON_URL}]]
        }

    try:
        r = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=10,
        )
        data = r.json()

        if data.get("ok"):
            return "ok"

        code = data.get("error_code", 0)
        desc = data.get("description", "")

        if code == 403:
            return "blocked"   # пользователь заблокировал бота
        if code == 429:
            return "ratelimit"
        return f"error:{code}:{desc}"

    except Exception as e:
        return f"exception:{e}"


async def run(test_mode: bool):
    users = get_users(test_mode)

    if not users:
        log.error("Пользователи не найдены в БД!")
        sys.exit(1)

    mode_label = "ТЕСТ" if test_mode else "ПОЛНАЯ РАССЫЛКА"
    log.info(f"Режим: {mode_label}")
    log.info(f"Пользователей: {len(users)}")
    log.info(f"Задержка: {DELAY}s между сообщениями")

    if not test_mode:
        log.info("Начинаю через 5 секунд... (Ctrl+C для отмены)")
        await asyncio.sleep(5)

    stats = {"ok": 0, "blocked": 0, "error": 0, "ratelimit": 0}
    start = datetime.now()

    async with httpx.AsyncClient() as client:
        for i, user in enumerate(users, 1):
            status = await send_one(client, user)

            uid  = user["user_id"]
            name = make_name(user)

            if status == "ok":
                stats["ok"] += 1
                log.info(f"[{i}/{len(users)}] ✅ {uid} ({name})")

            elif status == "blocked":
                stats["blocked"] += 1
                log.info(f"[{i}/{len(users)}] 🚫 {uid} ({name}) — заблокировал бота")

            elif status == "ratelimit":
                stats["ratelimit"] += 1
                log.warning(f"[{i}/{len(users)}] ⏳ {uid} — rate limit, жду 30 сек...")
                await asyncio.sleep(30)
                # повторная попытка
                status2 = await send_one(client, user)
                if status2 == "ok":
                    stats["ok"] += 1
                    stats["ratelimit"] -= 1

            else:
                stats["error"] += 1
                log.warning(f"[{i}/{len(users)}] ❌ {uid} ({name}) — {status}")

            if i < len(users):
                await asyncio.sleep(DELAY)

    elapsed = (datetime.now() - start).seconds
    log.info("─" * 50)
    log.info(f"ГОТОВО за {elapsed}с")
    log.info(f"  ✅ Отправлено:    {stats['ok']}")
    log.info(f"  🚫 Заблокировали: {stats['blocked']}")
    log.info(f"  ❌ Ошибки:        {stats['error']}")
    log.info(f"  ⏳ Rate limit:    {stats['ratelimit']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Полная рассылка (без флага — только тест)")
    args = parser.parse_args()

    asyncio.run(run(test_mode=not args.send))
