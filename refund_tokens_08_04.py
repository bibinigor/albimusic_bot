#!/usr/bin/env python3
"""
Скрипт возврата токенов пострадавшим пользователям 08.04.2026
Причины:
 - NameError: name 'logger' is not defined — бот падал с ошибками у всех
 - GENERATE_LYRIC_FAILED — генерации катерины (1908061062) завершились ошибками
 - The current credits are insufficient — кредиты Suno API кончились
 - Timeout context manager — уведомление об оплате не дошло до катерины
"""

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

# Пользователи для возврата токенов:
# user_id, tokens_to_add, message
REFUNDS = [
    {
        'user_id': 1908061062,
        'name': 'катерина',
        'tokens': 3,
        'message': (
            "🙏 *Уважаемая катерина, приносим извинения!*\n\n"
            "Сегодня в нашем сервисе произошли технические сбои, из-за которых "
            "ваши попытки создать песни завершились с ошибками.\n\n"
            "✅ Мы вернули вам *3 токена* на счёт.\n\n"
            "🔧 Проблема исправлена — сервис работает в штатном режиме.\n\n"
            "🎵 Попробуйте создать песни снова — всё должно работать!"
        ),
    },
    {
        'user_id': 8518041195,
        'name': 'пользователь',
        'tokens': 1,
        'message': (
            "🙏 *Приносим извинения за технические неполадки!*\n\n"
            "Сегодня в работе бота произошёл сбой, который мог повлиять "
            "на вашу попытку создать песню.\n\n"
            "✅ Мы вернули вам *1 токен* на счёт.\n\n"
            "🔧 Проблема исправлена — попробуйте снова!"
        ),
    },
    {
        'user_id': 7598513572,
        'name': 'Prosto Alexander',
        'tokens': 2,
        'message': (
            "🙏 *Здравствуйте, Prosto Alexander!*\n\n"
            "Вы совершенно правы — сегодня бот работал с ошибками. "
            "Причина: технический сбой в обработчиках бота (NameError). "
            "Проблема была диагностирована и устранена.\n\n"
            "✅ В качестве извинения мы начисляем вам *2 токена* бесплатно!\n\n"
            "🎵 Теперь вы можете создавать музыку — всё работает корректно.\n\n"
            "Спасибо за обратную связь — вы помогли нам найти и исправить ошибку! 🎶"
        ),
    },
]


def send_telegram_message(user_id: int, text: str) -> bool:
    """Отправляет сообщение пользователю через Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = httpx.post(url, json={
            "chat_id": user_id,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        data = resp.json()
        if data.get("ok"):
            return True
        else:
            print(f"  ⚠️  Telegram API ошибка: {data.get('description', data)}")
            return False
    except Exception as e:
        print(f"  ⚠️  Исключение при отправке: {e}")
        return False


def main():
    print("=" * 60)
    print("🔄 Возврат токенов пострадавшим пользователям 08.04.2026")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        print("✅ Подключение к БД установлено\n")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        sys.exit(1)

    for refund in REFUNDS:
        uid = refund['user_id']
        tokens = refund['tokens']
        name = refund['name']

        print(f"👤 Обрабатываем: {name} (id={uid})")

        # Получаем текущий баланс
        cur.execute("SELECT balance FROM users WHERE user_id = %s", (uid,))
        row = cur.fetchone()
        if not row:
            print(f"  ❌ Пользователь {uid} не найден в БД. Пропускаем.\n")
            continue

        old_balance = row[0]
        print(f"  💰 Текущий баланс: {old_balance}")

        # Начисляем токены
        cur.execute(
            "UPDATE users SET balance = balance + %s WHERE user_id = %s RETURNING balance",
            (tokens, uid)
        )
        new_balance = cur.fetchone()[0]
        conn.commit()
        print(f"  ✅ Токены начислены: {old_balance} → {new_balance} (+{tokens})")

        # Формируем итоговое сообщение с новым балансом
        full_message = refund['message'] + f"\n\n💰 Ваш текущий баланс: *{new_balance} токен(ов)*"

        # Отправляем уведомление
        if send_telegram_message(uid, full_message):
            print(f"  📨 Уведомление отправлено успешно")
        else:
            print(f"  ❌ Не удалось отправить уведомление (возможно, пользователь не начинал диалог с ботом)")

        print()

    cur.close()
    conn.close()

    print("=" * 60)
    print("✅ Возврат токенов завершён!")
    print("=" * 60)


if __name__ == "__main__":
    main()
