with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Строка 594 (индекс 593) - исправляем
if len(lines) > 594:
    # Находим строку с проблемой
    for i in range(590, 600):
        if i < len(lines) and '\\n' in lines[i] and 'await message.answer' in lines[i]:
            print(f"Проблемная строка {i+1}: {lines[i][:50]}...")
            # Разделяем строку на две
            parts = lines[i].split('\\n')
            if len(parts) == 2:
                lines[i] = parts[0] + '\\n'
                lines.insert(i+1, '    ' + parts[1])
                print(f"✅ Исправлено: разделено на строки {i+1} и {i+2}")
            break

with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
