import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Найдем функцию add_payment
add_payment_pattern = r'def add_payment\(user_id, amount, status, payment_id\):.*?except sqlite3\.Error as e:.*?logging\.error\(f".*?{e}"\)'

# Новая функция для PostgreSQL
new_add_payment = '''def add_payment(user_id, amount, status, payment_id):
    """Добавление платежа в PostgreSQL"""
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'INSERT INTO payments (user_id, amount, status, payment_id, created_at) VALUES (%s, %s, %s, %s, NOW())', 
            (user_id, amount, status, payment_id)
        )
        logging.info(f"✅ Платеж {payment_id} добавлен в БД")
    except Exception as e:
        logging.error(f"❌ Ошибка добавления платежа {user_id}: {e}")'''

# Найдем функцию update_payment_status
update_payment_pattern = r'def update_payment_status\(payment_id, status\):.*?except sqlite3\.Error as e:.*?logging\.error\(f".*?{e}"\)'

# Новая функция для PostgreSQL
new_update_payment = '''def update_payment_status(payment_id, status):
    """Обновление статуса платежа в PostgreSQL"""
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'UPDATE payments SET status = %s WHERE payment_id = %s', 
            (status, payment_id)
        )
        logging.info(f"✅ Статус платежа {payment_id} обновлен на {status}")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления платежа {payment_id}: {e}")'''

# Заменяем функции
if re.search(add_payment_pattern, content, re.DOTALL):
    content = re.sub(add_payment_pattern, new_add_payment, content, flags=re.DOTALL)
    print("✅ Функция add_payment обновлена для PostgreSQL")
else:
    print("⚠️ Не найдена функция add_payment")

if re.search(update_payment_pattern, content, re.DOTALL):
    content = re.sub(update_payment_pattern, new_update_payment, content, flags=re.DOTALL)
    print("✅ Функция update_payment_status обновлена для PostgreSQL")
else:
    print("⚠️ Не найдена функция update_payment_status")

# Сохраняем
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print()
print("📋 Функции платежей теперь работают с PostgreSQL")
print("Теперь платежи будут сохраняться в правильную БД")
