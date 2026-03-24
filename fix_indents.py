with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Исправляем отступы для строк 858-865 (индексы 857-864)
for i in range(857, 865):  # строки 858-865 в файле (индексы 857-864)
    if i < len(lines):
        # Добавляем 4 пробела в начало строки
        if not lines[i].startswith('    '):
            lines[i] = '    ' + lines[i]

with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("✅ Исправлены отступы строк 858-865")
