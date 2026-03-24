from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул соединений с БД
init_db_pool_sync()

# Получаем информацию о пользователе
user_info = execute_query_sync(
    "SELECT user_id, balance, created_at, free_generation_used FROM users WHERE username = %s",
    ("rasablen",)
)

if user_info:
    user_id, balance, created_at, free_gen_used = user_info[0]
    print(f"\nИнформация о пользователе @rasablen:")
    print(f"ID: {user_id}")
    print(f"Баланс: {balance} токенов")
    print(f"Создан: {created_at}")
    print(f"Бесплатная генерация использована: {'Да' if free_gen_used else 'Нет'}")
    
    # Получаем историю генераций
    generations = execute_query_sync(
        """SELECT created_at, status, prompt, audio_url 
           FROM generations 
           WHERE user_id = %s 
           ORDER BY created_at DESC 
           LIMIT 5""",
        (user_id,)
    )
    
    if generations:
        print("\nПоследние генерации:")
        for gen_date, status, prompt, audio_url in generations:
            print(f"\nДата: {gen_date}")
            print(f"Статус: {status}")
            print(f"Промпт: {prompt[:100]}...")
            print(f"URL: {audio_url[:100]}...")
    else:
        print("\nГенераций не найдено")
        
    # Получаем историю реферальных начислений
    referrals = execute_query_sync(
        """SELECT created_at 
           FROM referrals 
           WHERE referrer_id = %s 
           ORDER BY created_at DESC""",
        (user_id,)
    )
    
    if referrals:
        print(f"\nРеферальные начисления ({len(referrals)}):")
        for ref_date, in referrals:
            print(f"- {ref_date}")
else:
    print("Пользователь не найден")