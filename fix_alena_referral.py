#!/usr/bin/env python3
"""
Ретроактивное начисление бонуса Алёне (404699723)
за приглашённую подругу (440855527), которая нажала "Начать" сегодня,
но не была зарегистрирована из-за бага с обработчиком "начать".
"""
import random
from db_utils import execute_query_sync, init_db_pool_sync
init_db_pool_sync()

from vk_config import VK_TOKEN
import vk_api
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

REFERRER_ID = 404699723  # Алёна Бибина — пригласитель
REFERRED_ID  = 440855527  # подруга — нажала "Начать" в 08:10, но не зарегистрировалась

print("=" * 60)
print("  РЕТРОАКТИВНЫЙ БОНУС ДЛЯ АЛЁНЫ")
print("=" * 60)

# 1. Получаем инфо о подруге (чтобы записать в users)
try:
    info = vk.users.get(user_ids=REFERRED_ID)[0]
    first_name = info.get("first_name", "Пользователь")
    username   = info.get("screen_name", "")
    print(f"Подруга: {first_name} ({username}), id={REFERRED_ID}")
except Exception as e:
    first_name = "Пользователь"
    username   = ""
    print(f"Не удалось получить инфо о {REFERRED_ID}: {e}")

# 2. Регистрируем подругу в users как VK-пользователя
execute_query_sync(
    """
    INSERT INTO users (user_id, username, first_name, balance, created_at, provider, invited_by)
    VALUES (%s, %s, %s, 1, NOW(), 'vk', %s)
    ON CONFLICT (user_id) DO UPDATE SET
        provider   = 'vk',
        invited_by = EXCLUDED.invited_by
    """,
    (REFERRED_ID, username, first_name, REFERRER_ID)
)
print(f"✅ Подруга {REFERRED_ID} ({first_name}) зарегистрирована/обновлена в БД (provider=vk, invited_by={REFERRER_ID})")

# 3. Создаём запись в referrals (если нет)
execute_query_sync(
    """
    INSERT INTO referrals (referrer_id, referred_id, bonus_applied)
    SELECT %s, %s, FALSE
    WHERE NOT EXISTS (SELECT 1 FROM referrals WHERE referred_id = %s)
    """,
    (REFERRER_ID, REFERRED_ID, REFERRED_ID)
)
print(f"✅ Запись referrals создана: реферер {REFERRER_ID} -> приглашённый {REFERRED_ID}")

# 4. Начисляем 2 токена Алёне (только VK-пользователю)
rows = execute_query_sync(
    "UPDATE users SET balance = balance + 2 WHERE user_id = %s AND provider = 'vk'",
    (REFERRER_ID,)
)
if rows and rows > 0:
    print(f"✅ Алёне ({REFERRER_ID}) начислено +2 токена")
    # Помечаем бонус выплаченным
    execute_query_sync(
        "UPDATE referrals SET bonus_applied = TRUE WHERE referred_id = %s",
        (REFERRED_ID,)
    )
    print(f"✅ bonus_applied=TRUE для реферала {REFERRED_ID}")
else:
    print(f"⚠️ UPDATE баланса затронул 0 строк — Алёна не найдена как VK-пользователь!")

# 5. Отправляем VK-сообщение Алёне
try:
    vk.messages.send(
        user_id=REFERRER_ID,
        message=(
            "🎉 По вашей реферальной ссылке зарегистрировался новый друг!\n\n"
            "💰 Вам начислено +2 токена за приглашение.\n"
            "Продолжайте приглашать — за каждого получаете 2 токена! 🚀\n\n"
            f"🔗 Ваша ссылка: https://vk.com/club235442407?ref={REFERRER_ID}"
        ),
        random_id=random.getrandbits(32)
    )
    print(f"✅ VK-сообщение отправлено Алёне ({REFERRER_ID})")
except Exception as e:
    print(f"❌ Ошибка VK-сообщения: {e}")

# Итог
bal = execute_query_sync("SELECT balance FROM users WHERE user_id = %s", (REFERRER_ID,))
print(f"\n💰 Итоговый баланс Алёны: {bal[0][0] if bal and bal[0] else '?'} токенов")
