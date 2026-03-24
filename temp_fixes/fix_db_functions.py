import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем SQLite на PostgreSQL в функции get_user_balance
old_get_user_balance = '''def get_user_balance(user_id):
    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT free_generation_used, balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            free_used, balance = result
            if not free_used:
                return "🎁 1 бесплатная генерация"
            elif balance > 0:
                return f"💰 {balance} доступных генераций"
            else:
                return "❌ 0 доступных генераций"
        return "❌ 0 доступных генераций"
    except sqlite3.Error as e:
        logging.error(f"❌ Ошибка получения баланса {user_id}: {e}")
        return "❌ Ошибка получения баланса"'''

new_get_user_balance = '''def get_user_balance(user_id):
    try:
        from db_utils import execute_query_sync
        result = execute_query_sync('SELECT balance FROM users WHERE user_id = %s', (user_id,))
        if result:
            balance = result[0][0]
            if balance > 0:
                return f"💰 {balance} доступных генераций"
            else:
                return "❌ 0 доступных генераций"
        return "🎁 1 бесплатная генерация (новый пользователь)"
    except Exception as e:
        logging.error(f"❌ Ошибка получения баланса {user_id}: {e}")
        return "❌ Ошибка получения баланса"'''

content = content.replace(old_get_user_balance, new_get_user_balance)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлена функция get_user_balance для PostgreSQL")
