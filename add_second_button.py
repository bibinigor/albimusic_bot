with open('run_monitor_notify.py', 'r') as f:
    lines = f.readlines()

# Находим строку с кнопкой "Разместить в канале"
for i, line in enumerate(lines):
    if 'Разместить в канале ALBImusic Chart' in line:
        # Добавляем вторую кнопку после этой строки
        second_button = '        keyboard.add(InlineKeyboardButton("✅ Перейти в канал ALBImusic Chart", url="https://t.me/ALBImusic_Chart"))\n'
        lines.insert(i + 1, second_button)
        print(f"✅ Вторая кнопка добавлена после строки {i+1}")
        break

with open('run_monitor_notify.py', 'w') as f:
    f.writelines(lines)
