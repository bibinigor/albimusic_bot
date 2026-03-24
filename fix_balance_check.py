# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Добавляем новую функцию для получения числового баланса
new_function = '''
def get_balance_number(user_id):
    """Возвращает числовой баланс пользователя"""
    try:
        from db_utils import execute_query_sync
        result = execute_query_sync('SELECT balance FROM users WHERE user_id = %s', (user_id,))
        if result:
            return result[0][0]
        return 1  # Новый пользователь
    except Exception as e:
        logging.error(f"❌ Ошибка получения числового баланса {user_id}: {e}")
        return 0
'''

# Вставляем новую функцию после get_user_balance
import re
pattern = r'(def get_user_balance\(.*?\):.*?\n)(?=def|\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_function = match.group(1)
    new_content = old_function + '\n\n' + new_function + '\n\n'
    content = content.replace(old_function, new_content)

# Заменяем все проверки balance == "❌ 0 доступных генераций" на get_balance_number(user_id) <= 0
content = content.replace(
    'balance = get_user_balance(user_id)\n    if balance == "❌ 0 доступных генераций" and not is_admin(user_id):',
    'balance_num = get_balance_number(user_id)\n    if balance_num <= 0 and not is_admin(user_id):'
)

content = content.replace(
    'balance = get_user_balance(message.from_user.id)\n    if balance == "❌ 0 доступных генераций" and not is_admin(message.from_user.id):',
    'balance_num = get_balance_number(message.from_user.id)\n    if balance_num <= 0 and not is_admin(message.from_user.id):'
)

# Записываем обратно
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Исправлена проверка баланса")
