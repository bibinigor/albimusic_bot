#!/usr/bin/env python3
"""
Скрипт возврата токенов и рассылки извинений — инцидент 20.04.2026
Причина: Закончились кредиты Suno API (~19:30–22:57 мск).
Генерации завершались с ERROR_NOTIFIED, токены пользователей списывались.
Токены Suno пополнены в 22:57.

Пострадавшие:
  @mil_ks      (2011313078) — 2 ошибки (22:13, 22:40) → +3 токена
  @quperq      (1793381615) — 5 ошибок (22:10–22:14) → +5 токенов
  @chekniidaaam (971949896) — 2 ошибки (19:30, 23:34) + жалоба на голос → +3 токена
"""

import asyncio
import psycopg2
import sys

BOT_TOKEN = '8078747945:AAELaCEzbPUdwwilFBy_TJi9LsBb5scyzVU'
PROXY     = 'socks5://127.0.0.1:9050'

DB_PARAMS = {
    'host':     'localhost',
    'port':     5432,
    'database': 'albimusic_bot',
    'user':     'albimusic_user',
    'password': 'aXAnAixKT6@?B9',
}

REFUNDS = [
    {
        'user_id':  2011313078,
        'username': 'mil_ks',
        'name':     'Вероника',
        'tokens':   3,
        'message': (
            "🙏 *Вероника, приносим искренние извинения!*\n\n"
            "20 апреля в нашем сервисе закончились кредиты Suno AI — из-за этого "
            "ваши два заказа (в 22:13 и 22:40) завершились с ошибкой, хотя вы "
            "оплатили их реальными деньгами.\n\n"
            "✅ Мы вернули вам *3 токена* (2 за потерянные генерации + 1 в знак "
            "извинения).\n\n"
            "🔧 Проблема устранена — Suno AI работает в штатном режиме с 22:57.\n\n"
            "🎵 Попробуйте создать песни снова — всё готово к работе!\n\n"
            "Спасибо за терпение 💙"
        ),
    },
    {
        'user_id':  1793381615,
        'username': 'quperq',
        'name':     '44',
        'tokens':   5,
        'message': (
            "🙏 *Приносим извинения за технический сбой!*\n\n"
            "20 апреля у нашего сервиса закончились кредиты Suno AI. "
            "Из-за этого 5 ваших генераций (22:10–22:14) упали с ошибкой — "
            "при этом токены были списаны. Вы всё поняли правильно: токены "
            "потратились именно на эти ошибочные попытки.\n\n"
            "✅ Мы вернули вам *5 токенов* — ровно столько, сколько было потеряно.\n\n"
            "🔧 Проблема устранена с 22:57 — вы это уже заметили по успешным "
            "генерациям после этого времени.\n\n"
            "🎵 Создавайте музыку — всё работает!\n\n"
            "Спасибо, что остаётесь с нами 💙"
        ),
    },
    {
        'user_id':  971949896,
        'username': 'chekniidaaam',
        'name':     'кудряш',
        'tokens':   3,
        'message': (
            "🙏 *кудряш, приносим извинения сразу по двум поводам!*\n\n"
            "*1️⃣ Ошибки генерации:*\n"
            "20 апреля закончились кредиты Suno AI, из-за чего 2 ваших генерации "
            "(в ~19:30 и ~23:34) завершились с ошибкой.\n\n"
            "*2️⃣ Мужской голос вместо женского:*\n"
            "Suno AI старается учитывать пожелания по голосу из промпта, но "
            "не гарантирует точное соблюдение — это ограничение самого AI. "
            "Попробуйте в стиле добавить явные метки, например: "
            "`female vocals`, `woman singer`, `girl voice` — это повышает "
            "вероятность женского голоса, хотя 100% гарантии нет.\n\n"
            "✅ Мы вернули вам *3 токена* (2 за ошибки + 1 за неудобства с голосом).\n\n"
            "🎵 Попробуйте ещё раз — удачи с треком! 💙"
        ),
    },
]


async def send_tg_message(user_id: int, text: str) -> bool:
    """Отправляет сообщение через aiogram с SOCKS5-прокси (Tor)."""
    try:
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN, proxy=PROXY)
        await bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')
        await bot.close()
        return True
    except Exception as e:
        print(f"  ⚠️  Telegram ошибка: {e}")
        try:
            await bot.close()
        except Exception:
            pass
        return False


def refund_in_db(conn, user_id: int, tokens: int, username: str) -> int:
    """Начисляет токены и пишет транзакцию. Возвращает новый баланс."""
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance + %s WHERE user_id = %s RETURNING balance",
        (tokens, user_id)
    )
    new_bal = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO token_transactions (user_id, amount, transaction_type, description) "
        "VALUES (%s, %s, 'credit', %s)",
        (user_id, tokens,
         f'Рефанд {tokens} токен(ов) за инцидент с Suno API 20.04.2026 (@{username})')
    )
    conn.commit()
    cur.close()
    return new_bal


async def main():
    print("=" * 65)
    print("🔄  Рефанд + извинения — инцидент Suno API 20.04.2026")
    print("=" * 65)

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        print("✅  Подключение к БД установлено\n")
    except Exception as e:
        print(f"❌  Ошибка подключения к БД: {e}")
        sys.exit(1)

    for r in REFUNDS:
        uid      = r['user_id']
        tokens   = r['tokens']
        name     = r['name']
        username = r['username']

        print(f"👤  {name} (@{username}, id={uid})")

        # Текущий баланс
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
        row = cur.fetchone()
        cur.close()
        if not row:
            print(f"  ❌  Пользователь не найден в БД. Пропускаем.\n")
            continue

        old_bal = row[0]
        print(f"  💰  Баланс до: {old_bal}")

        new_bal = refund_in_db(conn, uid, tokens, username)
        print(f"  ✅  Начислено: +{tokens} → баланс {old_bal} → {new_bal}")

        full_msg = r['message'] + f"\n\n💰 Ваш текущий баланс: *{new_bal} токен(ов)*"

        ok = await send_tg_message(uid, full_msg)
        if ok:
            print(f"  📨  Сообщение доставлено")
        else:
            print(f"  ❌  Не удалось отправить (пользователь заблокировал бота?)")

        print()

    conn.close()
    print("=" * 65)
    print("✅  Рефанд завершён!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
