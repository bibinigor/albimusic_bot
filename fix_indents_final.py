import re

with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Номера строк для исправления (индексы с 0)
lines_to_indent = [856, 857, 858, 859, 860, 861, 862, 863]  # строки 857-864

for line_num in lines_to_indent:
    if line_num < len(lines):
        # Удаляем возможные пробелы в начале, добавляем 8 пробелов (двойной отступ)
        lines[line_num] = '        ' + lines[line_num].lstrip()

with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("✅ Отступы исправлены для строк 857-864")
print("Проверяемые строки после исправления:")
for i in range(855, 866):
    print(f"{i+1}: {lines[i].rstrip() if i < len(lines) else ''}")
