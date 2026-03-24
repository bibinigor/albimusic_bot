from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул соединений с БД
init_db_pool_sync()

USER_ID = 5690658238  # ID пользователя @rasablen

# Проверяем историю платежей
payments = execute_query_sync(
    """SELECT created_at, amount, status, payment_id 
       FROM payments 
       WHERE user_id = %s 
       ORDER BY created_at DESC""",
    (USER_ID,)
)

print("\nИстория платежей:")
if payments:
    for payment_date, amount, status, payment_id in payments:
        print(f"Дата: {payment_date}")
        print(f"Сумма: {amount}")
        print(f"Статус: {status}")
        print(f"ID платежа: {payment_id}")
        print("---")
else:
    print("Платежей не найдено")

# Проверяем историю реферальных начислений
referrals = execute_query_sync(
    """SELECT r.created_at, u.username as referred_user
       FROM referrals r
       JOIN users u ON u.user_id = r.referred_id
       WHERE r.referrer_id = %s
       ORDER BY r.created_at DESC""",
    (USER_ID,)
)

print("\nИстория реферальных начислений:")
if referrals:
    for ref_date, referred_user in referrals:
        print(f"Дата: {ref_date}")
        print(f"Пригласил: @{referred_user}")
        print("---")
else:
    print("Реферальных начислений не найдено")

# Проверяем логи изменения баланса (если есть такая таблица)
try:
    balance_logs = execute_query_sync(
        """SELECT created_at, old_balance, new_balance, reason
           FROM balance_logs
           WHERE user_id = %s
           ORDER BY created_at DESC""",
        (USER_ID,)
    )
    
    print("\nИстория изменений баланса:")
    if balance_logs:
        for log_date, old_bal, new_bal, reason in balance_logs:
            print(f"Дата: {log_date}")
            print(f"Было: {old_bal} → Стало: {new_bal}")
            print(f"Причина: {reason}")
            print("---")
    else:
        print("Логов изменения баланса не найдено")
except:
    print("\nТаблица balance_logs не существует")