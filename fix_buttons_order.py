with open('run_monitor_notify.py', 'r') as f:
    content = f.read()

# Находим блок с клавиатурой
import re
pattern = r'(from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton\n\s*keyboard = InlineKeyboardMarkup\(\)\n\s*keyboard.add\(InlineKeyboardButton\("📢 Разместить в канале ALBImusic Chart", callback_data=f"post_{task_id}"\)\))'

if re.search(pattern, content):
    # Заменяем на правильный порядок
    replacement = '''from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📢 Разместить в канале ALBImusic Chart", callback_data=f"post_{task_id}"))
        keyboard.add(InlineKeyboardButton("✅ Перейти в канал ALBImusic Chart", url="https://t.me/ALBImusic_Chart"))'''
    
    content = re.sub(pattern, replacement, content)
    print("✅ Исправлен порядок кнопок")
    
    with open('run_monitor_notify.py', 'w') as f:
        f.write(content)
else:
    print("❌ Не найден блок с клавиатурой")
