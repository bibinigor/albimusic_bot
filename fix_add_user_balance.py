# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Ищем функцию add_user и исправляем INSERT запрос
old_insert = "'INSERT INTO users (user_id, username, first_name, invited_by) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id) DO NOTHING'"
new_insert = "'INSERT INTO users (user_id, username, first_name, invited_by, balance) VALUES ($1, $2, $3, $4, 1) ON CONFLICT (user_id) DO NOTHING'"

content = content.replace(old_insert, new_insert)

# Также нужно исправить SQLite версию (если она еще есть)
old_sqlite_insert = "'INSERT INTO users (user_id, username, first_name, invited_by) VALUES (?, ?, ?, ?) ON CONFLICT (user_id) DO NOTHING'"
new_sqlite_insert = "'INSERT INTO users (user_id, username, first_name, invited_by, balance) VALUES (?, ?, ?, ?, 1) ON CONFLICT (user_id) DO NOTHING'"

content = content.replace(old_sqlite_insert, new_sqlite_insert)

# Записываем обратно
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Функция add_user исправлена - новые пользователи получат balance = 1")
