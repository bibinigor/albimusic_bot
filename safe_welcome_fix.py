with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку с welcome_text
for i, line in enumerate(lines):
    if 'welcome_text = "' in line:
        # Заменяем ВСЮ строку (и следующие если многострочная)
        new_welcome = '''    welcome_text = """🎵 Привет! Я AlBi-music — твой личный композитор с искусственным интеллектом!

🔥 Попробуй создать песню <b>БЕСПЛАТНО</b>! 

• 🎵 Можешь создать любую музыку под настроение (для видеоролика или для тренировки или медитации!
• 🔥 А можешь дать мне стихи и я создам тебе классную песню! 

🚀 Прямо сейчас нажми «Создать песню»!"""'''
        
        lines[i] = new_welcome + '\\n'
        print(f"✅ Приветствие заменено в строке {i+1}")
        
        # Меняем parse_mode на следующей строке
        for j in range(i, min(i+5, len(lines))):
            if 'parse_mode="Markdown"' in lines[j]:
                lines[j] = lines[j].replace('parse_mode="Markdown"', 'parse_mode="HTML"')
                print(f"✅ parse_mode изменён в строке {j+1}")
        break

with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
