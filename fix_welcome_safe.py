import re

with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем строку с welcome_text
found = False
for i, line in enumerate(lines):
    if 'welcome_text = """' in line:
        start_idx = i
        # Ищем конец блока
        for j in range(i, len(lines)):
            if '"""' in lines[j] and j != i:
                end_idx = j
                # Заменяем весь блок
                new_welcome = '''    welcome_text = """🎵 Привет! Я AlBi-music — твой личный композитор с искусственным интеллектом!

🔥 Попробуй создать песню <b>БЕСПЛАТНО</b>! 

• 🎵 Можешь создать любую музыку под настроение (для видеоролика или для тренировки или медитации!
• 🔥 А можешь дать мне стихи и я создам тебе классную песню! 

🚀 Прямо сейчас нажми «Создать песню»!"""'''
                
                # Удаляем старые строки и вставляем новую
                del lines[start_idx:end_idx+1]
                lines.insert(start_idx, new_welcome + '\\n')
                found = True
                print("✅ Приветствие заменено")
                break
        if found:
            break

# 2. Меняем parse_mode на HTML для этого сообщения
for i, line in enumerate(lines):
    if 'await message.answer(welcome_text' in line:
        # Находим parse_mode в этой или следующей строке
        if 'parse_mode="Markdown"' in line:
            lines[i] = line.replace('parse_mode="Markdown"', 'parse_mode="HTML"')
        elif i+1 < len(lines) and 'parse_mode="Markdown"' in lines[i+1]:
            lines[i+1] = lines[i+1].replace('parse_mode="Markdown"', 'parse_mode="HTML"')
        print("✅ parse_mode изменён на HTML")
        break

with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
