#!/usr/bin/env python3
"""
Ретроактивное начисление реферальных бонусов.
Начисляет 2 токена всем пользователям, чьи рефералы уже зарегистрированы,
но бонус ещё не был выплачен (bonus_applied = FALSE или запись отсутствует).
"""
import sys
import json
import time

# Инициализируем пул БД
from db_utils import init_db_pool_sync, execute_query_sync
init_db_pool_sync()

# Инициализируем VK API
from vk_config import VK_TOKEN
import vk_api
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

def send_vk_message(user_id, message):
    """Отправить сообщение пользователю в VK."""
    try:
        import random
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.getrandbits(32)
        )
        print(f"  ✅ Сообщение отправлено пользователю {user_id}")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка отправки сообщения пользователю {user_id}: {e}")
        return False

print("=" * 60)
print("РЕТРОАКТИВНОЕ НАЧИСЛЕНИЕ РЕФЕРАЛЬНЫХ БОНУСОВ")
print("=" * 60)

# 1. Пользователи с invited_by, у которых НЕТ записи в referrals
missing_in_referrals = execute_query_sync("""
    SELECT u.user_id, u.first_name, u.invited_by
    FROM users u
    WHERE u.invited_by IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM referrals r WHERE r.referred_id = u.user_id)
""")

print(f"\n📋 Пользователи с invited_by без записи в referrals: {len(missing_in_referrals) if missing_in_referrals else 0}")
for row in (missing_in_referrals or []):
    referred_id, referred_name, referrer_id = row
    print(f"  Создаю запись: referrer={referrer_id} → referred={referred_id} ({referred_name})")
    execute_query_sync(
        "INSERT INTO referrals (referrer_id, referred_id, bonus_applied) SELECT %s, %s, FALSE WHERE NOT EXISTS (SELECT 1 FROM referrals WHERE referred_id = %s)",
        (int(referrer_id), referred_id, referred_id)
    )

# 2. Все записи в referrals с bonus_applied = FALSE
unpaid = execute_query_sync("""
    SELECT r.referrer_id, r.referred_id,
           u_ref.first_name as referrer_name,
           u_new.first_name as referred_name
    FROM referrals r
    LEFT JOIN users u_ref ON u_ref.user_id = r.referrer_id
    LEFT JOIN users u_new ON u_new.user_id = r.referred_id
    WHERE r.bonus_applied = FALSE
    ORDER BY r.created_at ASC
""")

print(f"\n💰 Невыплаченные бонусы (bonus_applied=FALSE): {len(unpaid) if unpaid else 0}")

if not unpaid:
    print("\n✅ Все бонусы уже выплачены. Ничего делать не нужно.")
    sys.exit(0)

# Группируем рефералов по рефереру (один реферер мог пригласить нескольких)
from collections import defaultdict
referrer_map = defaultdict(list)
for row in unpaid:
    referrer_id, referred_id, referrer_name, referred_name = row
    referrer_map[referrer_id].append((referred_id, referred_name))

print(f"\n👥 Уникальных рефереров для начисления: {len(referrer_map)}")
print()

total_awarded = 0
total_tokens = 0

for referrer_id, referred_list in referrer_map.items():
    count = len(referred_list)
    tokens_to_award = count * 2
    referred_names = ', '.join([f"{name or 'Неизвестный'}({uid})" for uid, name in referred_list])

    print(f"🎁 Реферер {referrer_id}: {count} приглашённых → +{tokens_to_award} токенов")
    print(f"   Приглашённые: {referred_names}")

    # Начисляем токены
    execute_query_sync(
        "UPDATE users SET balance = balance + %s WHERE user_id = %s",
        (tokens_to_award, referrer_id)
    )

    # Помечаем все их рефералы как выплаченные
    for referred_id, _ in referred_list:
        execute_query_sync(
            "UPDATE referrals SET bonus_applied = TRUE WHERE referred_id = %s",
            (referred_id,)
        )

    # Получаем новый баланс
    bal = execute_query_sync("SELECT balance FROM users WHERE user_id = %s", (referrer_id,))
    new_balance = bal[0][0] if bal and bal[0] else '?'

    # Формируем и отправляем сообщение
    if count == 1:
        referred_id_single, referred_name_single = referred_list[0]
        msg = (
            f"🎉 Ваш реферальный бонус!\n\n"
            f"Ваш друг {referred_name_single or 'Неизвестный'} уже присоединился к ALBI Music.\n\n"
            f"💰 Вам начислено +{tokens_to_award} токена за приглашение.\n"
            f"📊 Ваш текущий баланс: {new_balance} токенов"
        )
    else:
        msg = (
            f"🎉 Ваши реферальные бонусы!\n\n"
            f"По вашим приглашениям уже присоединились {count} друга:\n"
            + ''.join([f"• {name or 'Неизвестный'}\n" for _, name in referred_list]) +
            f"\n💰 Вам начислено +{tokens_to_award} токенов за приглашения.\n"
            f"📊 Ваш текущий баланс: {new_balance} токенов"
        )

    send_vk_message(referrer_id, msg)

    total_awarded += 1
    total_tokens += tokens_to_award

    # Пауза чтобы не превысить лимиты VK API
    time.sleep(0.5)

print()
print("=" * 60)
print(f"✅ ГОТОВО: {total_awarded} рефереров получили токены, итого +{total_tokens} токенов")
print("=" * 60)
