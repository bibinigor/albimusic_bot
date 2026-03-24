with open('final_bot.py', 'r') as f:
    lines = f.readlines()

# Находим и исправляем проблемные строки 130-140
new_lines = []
i = 0
while i < len(lines):
    if i >= 129 and i <= 139:  # Строки 130-140 (индексы 0-based)
        if 'welcome_text = (' in lines[i]:
            new_lines.append(lines[i])
            new_lines.append('        "🎵 Добро пожаловать в AlBi-music!\\\\n\\\\n"\n')
            new_lines.append('        "Я помогу вам создать уникальную музыку и песни с помощью AI.\\\\n\\\\n"\n')
            new_lines.append('        "👇 Выберите действие:"\n')
            # Пропускаем старые проблемные строки
            while i < len(lines) and ')' not in lines[i]:
                i += 1
            if i < len(lines):
                new_lines.append(lines[i])
        else:
            new_lines.append(lines[i])
    else:
        new_lines.append(lines[i])
    i += 1

with open('final_bot.py', 'w') as f:
    f.writelines(new_lines)

print('✅ Дублирование в welcome_text исправлено')
