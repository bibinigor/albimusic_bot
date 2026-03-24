from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул соединений с БД
init_db_pool_sync()

# Получаем информацию о реферале
referral_info = execute_query_sync(
    """
    SELECT 
        r.created_at as ref_date,
        u1.user_id as referrer_id,
        u1.username as referrer_username,
        u1.balance as referrer_balance,
        u2.user_id as referred_id,
        u2.username as referred_username,
        u2.created_at as signup_date
    FROM referrals r
    JOIN users u1 ON u1.user_id = r.referrer_id
    JOIN users u2 ON u2.user_id = r.referred_id
    WHERE u1.username = 'rasablen' AND u2.username = 'narkot1k_i'
    """
)

if referral_info:
    ref_date, referrer_id, referrer_username, referrer_balance, referred_id, referred_username, signup_date = referral_info[0]
    print("\nИнформация о реферальной связи:")
    print(f"Дата реферала: {ref_date}")
    print(f"Реферер: @{referrer_username} (ID: {referrer_id})")
    print(f"Текущий баланс реферера: {referrer_balance}")
    print(f"Приглашенный: @{referred_username} (ID: {referred_id})")
    print(f"Дата регистрации приглашенного: {signup_date}")
    
    # Проверяем историю изменений баланса реферера
    balance_changes = execute_query_sync(
        """
        SELECT created_at, balance 
        FROM users_balance_history 
        WHERE user_id = %s 
        AND created_at >= %s 
        ORDER BY created_at ASC
        """,
        (referrer_id, ref_date)
    )
    
    if balance_changes:
        print("\nИзменения баланса после реферала:")
        for change_date, balance in balance_changes:
            print(f"{change_date}: {balance} токенов")
    else:
        print("\nИстория изменений баланса не найдена")
else:
    print("Реферальная связь не найдена")