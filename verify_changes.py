from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул соединений с БД
init_db_pool_sync()

# Проверяем текущий баланс
user_info = execute_query_sync(
    "SELECT user_id, balance FROM users WHERE username = 'rasablen'",
    ()
)

if user_info:
    user_id, balance = user_info[0]
    print(f"\nТекущий баланс @rasablen: {balance} токенов")

    # Проверяем логи изменений баланса
    balance_logs = execute_query_sync(
        """SELECT created_at, old_balance, new_balance, change_amount, reason
           FROM balance_logs 
           WHERE user_id = %s 
           ORDER BY created_at DESC""",
        (user_id,)
    )
    
    print("\nИстория изменений баланса:")
    if balance_logs:
        for log_date, old_bal, new_bal, change, reason in balance_logs:
            print(f"\nДата: {log_date}")
            print(f"Изменение: {old_bal} → {new_bal} ({change:+d})")
            print(f"Причина: {reason}")
    else:
        print("Логи изменений не найдены")
else:
    print("Пользователь не найден")