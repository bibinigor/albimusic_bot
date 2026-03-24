import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим и исправляем строку с ошибкой
fixed_lines = []
for i, line in enumerate(lines):
    if "from aiogram.dispatcher import" in line and "^" in lines[i+1] if i+1 < len(lines) else False:
        # Это строка с ошибкой - пропускаем её
        continue
    elif "from aiogram.dispatcher import" in line:
        # Проверяем что импорт завершен
        if "Dispatcher" in line or "FSMContext" in line:
            fixed_lines.append(line)
        else:
            # Добавляем недостающие импорты
            fixed_lines.append("from aiogram.dispatcher import Dispatcher, FSMContext\n")
    else:
        fixed_lines.append(line)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Синтаксис исправлен")
