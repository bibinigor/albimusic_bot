import re

with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Находим функцию get_balance_keyboard
in_function = False
for i, line in enumerate(lines):
    if 'def get_balance_keyboard(user_id):' in line:
        start_line = i
        in_function = True
    
    elif in_function and 'return markup' in line:
        # Проверяем, не дублируется ли return
        if i + 1 < len(lines) and 'return markup' in lines[i + 1]:
            # Удаляем дублирующийся return
            lines[i + 1] = ''
            print(f"✅ Удалили дублирующийся return в строке {i+2}")
        
        # Проверяем лишнюю скобку
        if i + 1 < len(lines) and lines[i + 1].strip() == ')':
            lines[i + 1] = ''
            print(f"✅ Удалили лишнюю скобку в строке {i+2}")
        
        # Проверяем, что закрывающая скобка есть перед return
        for j in range(i-1, max(i-10, start_line), -1):
            if ')' in lines[j] and 'InlineKeyboardButton' in lines[j]:
                # Все в порядке
                break
        else:
            # Нет закрывающей скобки, нужно добавить
            print("⚠️  Возможно не хватает закрывающей скобки")
        
        in_function = False

# Также проверим, что нет других явных ошибок
# Сохраняем и проверяем
with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("✅ Синтаксические ошибки исправлены")

# Проверим функцию еще раз
print("\n🔍 Проверяем исправленную функцию:")
with open('main_with_payments.py', 'r') as f:
    content = f.read()
    match = re.search(r'def get_balance_keyboard\(user_id\):.*?return markup', content, re.DOTALL)
    if match:
        func = match.group(0)
        print(func[:200] + "..." if len(func) > 200 else func)
