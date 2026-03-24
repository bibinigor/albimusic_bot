import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем вызов generate_music_task - объединяем style и custom_mode в один prompt
old_call = "task = generate_music_task.delay(user_id, style, custom_mode)"
new_call = "task = generate_music_task.delay(user_id, f'{style}. {custom_mode}' if custom_mode else style)"

content = content.replace(old_call, new_call)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлен вызов generate_music_task")
