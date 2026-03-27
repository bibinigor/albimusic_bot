from db_utils import execute_query_sync, init_db_pool_sync

def update_balance_settings():
    # Инициализируем подключение к БД
    init_db_pool_sync()
    
    try:
        # Обновляем баланс для существующих пользователей с нулевым балансом
        result = execute_query_sync(
            "UPDATE users SET balance = 10 WHERE balance = 0 RETURNING user_id, balance"
        )
        if result:
            print(f"✅ Баланс успешно обновлен до 10 для пользователей: {result}")
        else:
            print("ℹ️ Нет пользователей с нулевым балансом")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    update_balance_settings()