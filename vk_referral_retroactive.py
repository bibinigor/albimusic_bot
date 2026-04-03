#!/usr/bin/env python3
"""
Ретроактивное начисление реферальных бонусов — ТОЛЬКО VK-бот.

ВАЖНО: Обрабатываются ТОЛЬКО пользователи с provider='vk'.
Telegram-пользователи полностью игнорируются — у них отдельная система.

Что делает скрипт:
1. Находит VK-рефереров у которых есть приглашённые с bonus_applied=FALSE
2. Начисляет +2 токена за каждого приглашённого
3. Отправляет VK-сообщение рефереру
4. Ставит bonus_applied=TRUE
"""

import sys
import random
import time
from collections import defaultdict

from db_utils import init_db_pool_sync, execute_query_sync
init_db_pool_sync()

from vk_config import VK_TOKEN
import vk_api

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

print("=" * 65)
print("  VK РЕТРО-НАЧИСЛЕНИЕ РЕФЕРАЛЬНЫХ БОНУСОВ (только VK)")
print("=" * 65)


def send_vk_message(user_id: int, message: str) -> bool:
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.getrandbits(32)
        )
        print(f"    ✅ VK-сообщение отправлено пользователю {user_id}")
        return True
    except Exception as e:
        print(f"    ❌ Не удалось отправить VK-сообщение {user_id}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 1: VK-пользователи у которых invited_by IS NOT NULL,
#         но нет записи в referrals (старые данные без referrals)
# ─────────────────────────────────────────────────────────────────────────────
print("\n📋 ШАГ 1: VK-пользователи с invited_by без записи в referrals")
missing = execute_query_sync("""
    SELECT u.user_id, u.first_name, u.invited_by
    FROM users u
    WHERE u.invited_by IS NOT NULL
      AND u.provider = 'vk'
      AND NOT EXISTS (SELECT 1 FROM referrals r WHERE r.referred_id = u.user_id)
""")
missing = missing or []
print(f"  Найдено: {len(missing)}")

for row in missing:
    referred_id, referred_name, referrer_id = row
    print(f"  Создаю referral: реферер {referrer_id} → приглашённый {referred_id} ({referred_name})")
    execute_query_sync(
        """
        INSERT INTO referrals (referrer_id, referred_id, bonus_applied)
        SELECT %s, %s, FALSE
        WHERE NOT EXISTS (SELECT 1 FROM referrals WHERE referred_id = %s)
        """,
        (int(referrer_id), referred_id, referred_id)
    )

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 2: Все VK-рефереры у которых есть записи bonus_applied=FALSE
# ─────────────────────────────────────────────────────────────────────────────
print("\n💰 ШАГ 2: VK-рефереры с bonus_applied = FALSE")
unpaid = execute_query_sync("""
    SELECT
        r.id,
        r.referrer_id,
        r.referred_id,
        r.created_at,
        u_ref.first_name   AS referrer_name,
        u_ref.balance      AS referrer_balance,
        u_new.first_name   AS referred_name
    FROM referrals r
    JOIN users u_ref ON u_ref.user_id = r.referrer_id AND u_ref.provider = 'vk'
    LEFT JOIN users u_new ON u_new.user_id = r.referred_id
    WHERE r.bonus_applied = FALSE
    ORDER BY r.referrer_id, r.created_at
""")
unpaid = unpaid or []
print(f"  Найдено невыплаченных (только VK-рефереры): {len(unpaid)}")

if not unpaid:
    print("\n✅ Нет ни одного невыплаченного бонуса среди VK-пользователей.")
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 3: Группируем по рефереру и начисляем
# ─────────────────────────────────────────────────────────────────────────────
referrer_map = defaultdict(list)
for row in unpaid:
    ref_id, referrer_id, referred_id, created_at, ref_name, ref_balance, new_name = row
    referrer_map[referrer_id].append({
        'referral_id': ref_id,
        'referred_id': referred_id,
        'referred_name': new_name or '—',
        'referrer_name': ref_name or '—',
        'referrer_balance': ref_balance,
    })

print(f"\n👥 Уникальных VK-рефереров для начисления: {len(referrer_map)}")
print()

total_tokens = 0
total_messages = 0

for referrer_id, invited_list in referrer_map.items():
    count = len(invited_list)
    tokens_to_add = count * 2
    ref_name = invited_list[0]['referrer_name']
    current_balance = invited_list[0]['referrer_balance'] or 0
    invited_names = ', '.join(
        f"{r['referred_name']} ({r['referred_id']})" for r in invited_list
    )

    print(f"🎁 VK-реферер {referrer_id} ({ref_name})")
    print(f"   Баланс: {current_balance} | Приглашённых: {count} | Начислить: +{tokens_to_add} токенов")
    print(f"   Приглашённые: {invited_names}")

    # Начисляем токены только VK-пользователю
    rows = execute_query_sync(
        "UPDATE users SET balance = balance + %s WHERE user_id = %s AND provider = 'vk'",
        (tokens_to_add, referrer_id)
    )
    if rows and rows > 0:
        total_tokens += tokens_to_add
        print(f"   ✅ Баланс обновлён: +{tokens_to_add} токенов")
    else:
        print(f"   ⚠️  UPDATE затронул 0 строк — пропускаем начисление.")

    # Помечаем bonus_applied=TRUE
    for r in invited_list:
        execute_query_sync(
            "UPDATE referrals SET bonus_applied = TRUE WHERE id = %s",
            (r['referral_id'],)
        )
    print(f"   ✅ bonus_applied=TRUE для {count} записей")

    # Формируем VK-сообщение
    if count == 1:
        msg = (
            "🎉 Ваш друг присоединился к ALBI Music ВКонтакте!\n\n"
            "💰 Вам начислено +2 токена за приглашение.\n"
            "Продолжайте приглашать — за каждого получаете 2 токена! 🚀\n\n"
            f"🔗 Ваша реферальная ссылка:\nhttps://vk.com/club235442407?ref={referrer_id}"
        )
    else:
        msg = (
            f"🎉 По вашей ссылке во ВКонтакте зарегистрировались {count} новых друга!\n\n"
            f"💰 Вам начислено +{tokens_to_add} токенов (по 2 за каждого).\n"
            "Продолжайте приглашать — за каждого получаете 2 токена! 🚀\n\n"
            f"🔗 Ваша реферальная ссылка:\nhttps://vk.com/club235442407?ref={referrer_id}"
        )

    sent = send_vk_message(int(referrer_id), msg)
    if sent:
        total_messages += 1

    print()
    time.sleep(0.3)

# ─────────────────────────────────────────────────────────────────────────────
# ИТОГИ
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("  ИТОГИ (только VK)")
print("=" * 65)
print(f"  VK-рефереров обработано:     {len(referrer_map)}")
print(f"  Токенов начислено:            {total_tokens}")
print(f"  VK-сообщений отправлено:      {total_messages}")

remaining = execute_query_sync("""
    SELECT COUNT(*) FROM referrals r
    JOIN users u ON u.user_id = r.referrer_id AND u.provider = 'vk'
    WHERE r.bonus_applied = FALSE
""")
remaining_count = remaining[0][0] if remaining and remaining[0] else 0
if remaining_count == 0:
    print("\n✅ Все реферальные бонусы VK начислены (bonus_applied=TRUE).")
else:
    print(f"\n⚠️  Осталось {remaining_count} невыплаченных VK-бонусов — проверьте логи выше!")
