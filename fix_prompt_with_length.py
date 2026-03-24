import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Находим и исправляем функцию generate_song_task - добавляем указание длины
pattern = r'if custom_mode:\s+# В custom_mode=true: стиль в поле style, текст в prompt\s+prompt = lyrics\s+use_style = style'
replacement = '''if custom_mode:
            # В custom_mode=true: стиль в поле style, текст в prompt + указание длины
            prompt = f"{lyrics} [Длина песни: 3 минуты]"
            use_style = style'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Добавлено указание длины в промпт для custom_mode=true")
print("Теперь промпт будет: 'текст [Длина песни: 3 минуты]'")
