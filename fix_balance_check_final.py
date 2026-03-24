# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Исправляем строку 716
content = content.replace(
    'if balance_num <= 0("🎁") and not is_admin(user_id):',
    'if balance_num == 1 and not is_admin(user_id):  # Первая бесплатная генерация'
)

# Исправляем строку 757
content = content.replace(
    'if balance_num <= 0("🎁") and not is_admin(message.from_user.id):',
    'if balance_num == 1 and not is_admin(message.from_user.id):  # Первая бесплатная генерация'
)

# Записываем обратно
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Баланс проверка исправлена правильно")
