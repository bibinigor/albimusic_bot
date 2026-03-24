from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул соединений с БД
init_db_pool_sync()

# Создаем таблицу balance_logs
execute_query_sync("""
CREATE TABLE IF NOT EXISTS balance_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    old_balance INTEGER NOT NULL,
    new_balance INTEGER NOT NULL,
    change_amount INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

# Создаем индексы
execute_query_sync("""
CREATE INDEX IF NOT EXISTS balance_logs_user_id_idx ON balance_logs(user_id);
CREATE INDEX IF NOT EXISTS balance_logs_created_at_idx ON balance_logs(created_at);
""")

# Обновляем функцию update_user_balance в main_with_payments.py, чтобы она логировала изменения
execute_query_sync("""
CREATE OR REPLACE FUNCTION log_balance_change() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO balance_logs (user_id, old_balance, new_balance, change_amount, reason)
    VALUES (
        NEW.user_id,
        OLD.balance,
        NEW.balance,
        NEW.balance - OLD.balance,
        'Balance update via trigger'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

# Создаем триггер
execute_query_sync("""
DROP TRIGGER IF EXISTS balance_change_trigger ON users;
CREATE TRIGGER balance_change_trigger
AFTER UPDATE OF balance ON users
FOR EACH ROW
WHEN (OLD.balance IS DISTINCT FROM NEW.balance)
EXECUTE FUNCTION log_balance_change();
""")

print("✅ Таблица balance_logs и триггер созданы успешно")

# Начисляем 2 токена пользователю @rasablen
user_info = execute_query_sync(
    "SELECT balance FROM users WHERE username = 'rasablen'",
    ()
)

if user_info:
    current_balance = user_info[0][0]
    execute_query_sync(
        """UPDATE users SET balance = balance + 2 WHERE username = 'rasablen'""",
        ()
    )
    
    # Добавляем запись в лог
    execute_query_sync(
        """INSERT INTO balance_logs (user_id, old_balance, new_balance, change_amount, reason)
           VALUES ((SELECT user_id FROM users WHERE username = 'rasablen'),
                  %s, %s, 2, 'Восстановление реферального бонуса от 22.03.2026')""",
        (current_balance, current_balance + 2)
    )
    print("✅ Баланс пользователя @rasablen обновлен: +2 токена")