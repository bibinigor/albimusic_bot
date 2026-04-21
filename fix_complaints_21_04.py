#!/usr/bin/env python3
"""
Обработка жалоб пользователей — 21.04.2026

Юля (@Julia_Denisovnaa, id=1629183873) — "Отправила деньги где песня"
  Платёж 29₽ прошёл в 11:16, is_unlocked=TRUE, но полный трек не доставлен.
  → Отправить 2 аудиофайла вручную + извинения.

Aaaassa (id=8492512614) — "Не генерирует мои песни"
  Генерация bdadc071 → ERROR_NOTIFIED. Токен потерян.
  → Вернуть 1 токен + извинения.

кудряш (@chekniidaaam, id=971949896) — "снова присылает мужскую версию"
  Ещё одна ошибка 21.04 (34517c02, 10:44) → ERROR_NOTIFIED.
  Рефанд за 20.04 (+3 токена) уже зачислен в 07:36.
  → Вернуть 1 токен за ошибку 21.04 + объяснение про голос.

Sheba (@Sheba232012, id=5810528205) — "Я оплатил трэк а мне его не сделали"
  Платёж 29₽ прошёл в 09:08, is_unlocked=TRUE, но полный трек не доставлен.
  → Отправить 2 аудиофайла вручную + извинения.
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

# ── Данные по каждому случаю ──────────────────────────────────────────────────

CASES = [
    {
        'user_id':  1629183873,
        'username': 'Julia_Denisovnaa',
        'name':     'Юля',
        'refund':   0,   # рефанд не нужен — деньги за генерацию уже потрачены корректно
        'send_tracks': [
            'https://tempfile.aiquickdraw.com/r/bad8d3298a1f4d96a4562d9dcf4a137a.mp3',
            'https://tempfile.aiquickdraw.com/r/e99c4b78fd674cf982a8c0fc04fdb962.mp3',
        ],
        'message': (
            "🙏 *Юля, приносим извинения за задержку!*\n\n"
            "Вы оплатили разблокировку трека (29₽), и платёж прошёл успешно — "
            "но из-за технической ошибки в нашем боте полная версия не была "
            "отправлена автоматически.\n\n"
            "Мы отправляем ваши треки прямо сейчас! 🎵\n\n"
            "Спасибо за терпение 💙"
        ),
    },
    {
        'user_id':  8492512614,
        'username': None,
        'name':     'Aaaassa',
        'refund':   1,
        'send_tracks': [],
        'message': (
            "🙏 *Приносим извинения за сбой генерации!*\n\n"
            "Ваш запрос на создание песни завершился с технической ошибкой — "
            "токен был списан, но трек не создан.\n\n"
            "✅ Мы вернули вам *1 токен* на баланс.\n\n"
            "🎵 Попробуйте создать песню снова — сервис работает в штатном режиме.\n\n"
            "Спасибо, что вы с нами! Ваш талант обязательно найдёт своё воплощение 💙"
        ),
    },
    {
        'user_id':  971949896,
        'username': 'chekniidaaam',
        'name':     'кудряш',
        'refund':   1,
        'send_tracks': [],
        'message': (
            "🙏 *кудряш, снова приносим извинения!*\n\n"
            "*1️⃣ Ошибка генерации (21.04, ~10:44):*\n"
            "Один из ваших запросов завершился с ошибкой — токен потерян. "
            "Мы вернули вам *1 токен* за это.\n\n"
            "*2️⃣ Про мужской голос:*\n"
            "Понимаем ваше разочарование 😔 Suno AI не всегда точно следует "
            "пожеланиям по голосу — это ограничение самой нейросети. "
            "Чтобы повысить вероятность женского голоса, попробуйте добавить "
            "в поле «Стиль» такие метки:\n"
            "`female vocals`, `woman singer`, `girl voice`, `soprano`\n"
            "Чем конкретнее — тем лучше. К сожалению, 100% гарантии нет, "
            "но эти метки заметно помогают.\n\n"
            "✅ Итого начислено: *+1 токен*\n\n"
            "🎵 Удачи с вашим треком! 💙"
        ),
    },
    {
        'user_id':  5810528205,
        'username': 'Sheba232012',
        'name':     'Sheba',
        'refund':   0,   # рефанд не нужен — деньги за генерацию потрачены корректно
        'send_tracks': [
            'https://tempfile.aiquickdraw.com/r/35e136ce4dc74680a180343717df4ab1.mp3',
            'https://tempfile.aiquickdraw.com/r/6ecab254be5a41b388a2ae6d9e0231e0.mp3',
        ],
        'message': (
            "🙏 *Sheba, приносим извинения!*\n\n"
            "Ваш трек был успешно создан и оплата прошла, но из-за технической "
            "ошибки в боте он не был доставлен автоматически.\n\n"
            "Отправляем ваш трек прямо сейчас! 🎵\n\n"
            "Спасибо за терпение 💙"
        ),
    },
]


# ── Функции ───────────────────────────────────────────────────────────────────

async def send_tg_message(bot, user_id: int, text: str) -> bool:
    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"  ⚠️  Ошибка отправки сообщения: {e}")
        return False


async def send_tg_audio(bot, user_id: int, url: str, caption: str = '') -> bool:
    try:
        await bot.send_audio(chat_id=user_id, audio=url, caption=caption)
        return True
    except Exception as e:
        print(f"  ⚠️  Ошибка отправки аудио ({url[:60]}...): {e}")
        # Fallback: отправить URL текстом
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"🎵 Ваш трек:\n{url}"
            )
            print(f"  ↳ Отправлен URL текстом (fallback)")
            return True
        except Exception as e2:
            print(f"  ❌ Fallback тоже не удался: {e2}")
            return False


def refund_in_db(conn, user_id: int, tokens: int, username: str, reason: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance + %s WHERE user_id = %s RETURNING balance",
        (tokens, user_id)
    )
    new_bal = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO token_transactions "
        "(user_id, amount, transaction_type, description) "
        "VALUES (%s, %s, 'credit', %s)",
        (user_id, tokens, reason)
    )
    conn.commit()
    cur.close()
    return new_bal


async def main():
    print("=" * 65)
    print("🔄  Обработка жалоб пользователей — 21.04.2026")
    print("=" * 65)

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        print("✅  Подключение к БД установлено\n")
    except Exception as e:
        print(f"❌  Ошибка подключения к БД: {e}")
        sys.exit(1)

    from aiogram import Bot
    bot = Bot(token=BOT_TOKEN, proxy=PROXY)

    for case in CASES:
        uid      = case['user_id']
        name     = case['name']
        username = case['username']
        refund   = case['refund']
        tracks   = case['send_tracks']
        label    = f"@{username}" if username else f"id={uid}"

        print(f"👤  {name} ({label}, id={uid})")

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

        # Рефанд токенов (если нужен)
        new_bal = old_bal
        if refund > 0:
            reason = (
                f"Рефанд {refund} токен(ов) за ошибку генерации 21.04.2026"
                + (f" ({label})" if username else "")
            )
            new_bal = refund_in_db(conn, uid, refund, username or str(uid), reason)
            print(f"  ✅  Начислено: +{refund} токен(а) → баланс {old_bal} → {new_bal}")
        else:
            print(f"  ℹ️  Рефанд не требуется")

        # Текст сообщения (с балансом если был рефанд)
        msg = case['message']
        if refund > 0:
            msg += f"\n\n💰 Ваш текущий баланс: *{new_bal} токен(ов)*"

        # Отправляем сообщение
        ok_msg = await send_tg_message(bot, uid, msg)
        if ok_msg:
            print(f"  📨  Сообщение доставлено")
        else:
            print(f"  ❌  Сообщение не доставлено (пользователь заблокировал бота?)")

        # Отправляем аудиофайлы (если нужно)
        if tracks:
            print(f"  🎵  Отправляю {len(tracks)} аудиофайл(а)...")
            await asyncio.sleep(0.5)
            for i, url in enumerate(tracks, 1):
                ok_audio = await send_tg_audio(bot, uid, url, caption=f"🎵 Трек {i} из {len(tracks)}")
                status = "✅" if ok_audio else "❌"
                print(f"  {status}  Трек {i}: {url[-40:]}")
                await asyncio.sleep(0.8)

        print()

    await bot.close()
    conn.close()

    print("=" * 65)
    print("✅  Обработка завершена!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
