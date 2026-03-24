with open('run_monitor_notify.py', 'r') as f:
    lines = f.readlines()

# Находим строки с клавиатурой
new_lines = []
i = 0
while i < len(lines):
    if 'keyboard.add(InlineKeyboardButton("📢 Разместить в канале"' in lines[i]:
        # Это оригинальная строка - меняем текст
        lines[i] = lines[i].replace('Разместить в канале', 'Разместить в канале ALBImusic Chart')
        new_lines.append(lines[i])
        
        # Добавляем вторую кнопку после неё
        new_lines.append('        keyboard.add(InlineKeyboardButton("✅ Перейти в канал ALBImusic Chart", url="https://t.me/ALBImusic_Chart"))\n')
        i += 1
    else:
        new_lines.append(lines[i])
        i += 1

with open('run_monitor_notify.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Кнопки исправлены")
