with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Находим блок формирования данных для Suno
import re
pattern = r'data = \{.*?"prompt": prompt,.*?\}'

def replace_data_block(match):
    old_block = match.group(0)
    # Заменяем на правильную структуру
    new_block = '''    data = {
        "prompt": prompt,  # ТОЛЬКО текст песни
        "style": style if style else "",  # ТОЛЬКО стиль (отдельно!)
        "title": prompt[:50] if prompt else "",  # Заголовок из первых 50 символов текста
        "customMode": custom_mode,
        "instrumental": is_instrumental,
        "styleWeight": 0.8,
        "vocalGender": vocal_gender,
        "weirdnessConstraint": 0.3,
        "duration": 60,
        "model": "V5",
        "callBackUrl": "https://example.com/callback"
    }'''
    return new_block

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replace_data_block, content, flags=re.DOTALL)
    print("✅ Исправлена передача параметров в Suno API")
    print("Теперь style и prompt передаются отдельно")
else:
    print("❌ Не найден блок данных для Suno API")

with open('celery_tasks.py', 'w') as f:
    f.write(content)
