#!/usr/bin/env python3
"""Скрипт: подарить 1 токен пользователю @XomRksa и отправить уведомление в Telegram."""

import psycopg2
import httpx
import sys

# Конфигурация
BOT_TOKEN = '8078747945:AAELaCEzbPUdwwilFBy_TJi9LsBb5scyzVU'
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'albimusic_bot',
    'user': 'albimusic_user',
    'password': 'aXAnAixKT6@?B9',
}
TARGET_USERNAME = 'XomRksa'

def main():
    # 1. Подключаемся к БД и ищем пользователя
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    print(f"🔍 Ищем пользователя @{TARGET_USERNAME} в базе данных...")
    cur.execute(
        "SELECT user_id, username, first_name, balance FROM users WHERE LOWER(username) = LOWER(%s)",
        (TARGET_USERNAME,)
    )
    row = cur.fetchone()

    if not row:
        print(f"❌ Пользователь @{TARGET_USERNAME} не найден в базе данных.")
        cur.close()
        conn.close()
        sys.exit(1)

    user_id, username, first_name, old_balance = row
    print(f"✅ Найден: user_id={user_id}, @{username}, имя={first_name}, баланс={old_balance}")

    # 2. Добавляем 1 токен
    cur.execute(
        "UPDATE users SET balance = balance + 1 WHERE user_id = %s RETURNING balance",
        (user_id,)
    )
    new_balance = cur.fetchone()[0]
    conn.commit()
    print(f"💰 Баланс обновлён: {old_balance} → {new_balance}")

    cur.close()
    conn.close()

    # 3. Отправляем сообщение в Telegram
    message_text = (
        "🎁 *Вам подарили 1 токен!*\n\n"
        "Поздравляем — на ваш счёт начислен 1 токен для генерации музыки в AlBi Music 🎵\n\n"
        f"Ваш текущий баланс: *{new_balance} токен(ов)*\n\n"
        "Приятного творчества! 🚀"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = httpx.post(url, json={
        "chat_id": user_id,
        "text": message_text,
        "parse_mode": "Markdown",
    })
    data = resp.json()

    if data.get("ok"):
        print(f"✅ Сообщение успешно отправлено пользователю @{username} (id={user_id})")
    else:
        print(f"❌ Ошибка отправки сообщения: {data}")
        sys.exit(1)

if __name__ == "__main__":
    main()
