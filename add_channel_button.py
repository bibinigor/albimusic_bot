with open('run_monitor_notify.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'keyboard.add(InlineKeyboardButton("📢 Разместить в канале"' in line:
        # Добавляем вторую кнопку после этой
        lines.insert(i + 1, '        keyboard.add(InlineKeyboardButton("✅ Перейти в канал ALBImusic Chart", url="https://t.me/ALBImusic_Chart"))\\n')
        print(f"✅ Вторая кнопка добавлена после строки {i+1}")
        break

with open('run_monitor_notify.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
