from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул соединений с БД
init_db_pool_sync()

USER_ID = 5690658238  # ID пользователя @rasablen

# Проверяем все генерации пользователя, включая неуспешные
generations = execute_query_sync(
    """SELECT created_at, status, prompt, audio_url, is_free, custom_mode
       FROM generations 
       WHERE user_id = %s 
       ORDER BY created_at DESC""",
    (USER_ID,)
)

print("\nВсе попытки генерации:")
if generations:
    for gen_date, status, prompt, audio_url, is_free, custom_mode in generations:
        print(f"\nДата: {gen_date}")
        print(f"Статус: {status}")
        print(f"Промпт: {prompt[:100]}...")
        print(f"Бесплатная: {'Да' if is_free else 'Нет'}")
        print(f"Кастомный режим: {'Да' if custom_mode else 'Нет'}")
        print("---")
else:
    print("Генераций не найдено")

# Проверяем все попытки начать генерацию (через логи состояний FSM)
try:
    fsm_logs = execute_query_sync(
        """SELECT created_at, state, data
           FROM fsm_logs
           WHERE user_id = %s
           ORDER BY created_at DESC""",
        (USER_ID,)
    )
    
    print("\nИстория состояний FSM:")
    if fsm_logs:
        for log_date, state, data in fsm_logs:
            print(f"\nДата: {log_date}")
            print(f"Состояние: {state}")
            print(f"Данные: {data}")
            print("---")
    else:
        print("Логов FSM не найдено")
except:
    print("\nТаблица fsm_logs не существует")