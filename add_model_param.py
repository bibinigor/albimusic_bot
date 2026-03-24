import re

with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем "model": "V5" в каждый блок данных
# БЛОК 1: custom_mode=True - добавляем после styleWeight
content = re.sub(
    r'(\s*"styleWeight": 0\.9,\s*\n\s*"vocalsGender": vocal_gender,)',
    r'\1\n                "model": "V5",',
    content
)

# БЛОК 2: custom_mode=False - добавляем после styleWeight  
content = re.sub(
    r'(\s*"styleWeight": 0\.8,\s*\n\s*"vocalsGender": vocal_gender,)',
    r'\1\n                "model": "V5",',
    content
)

# БЛОК 3: instrumental - добавляем после styleWeight
content = re.sub(
    r'(\s*"styleWeight": 0\.8,\s*\n\s*"callBackUrl": "https://albi-music\.ru/webhook/suno")',
    r'\1,\n            "model": "V5"',
    content
)

with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Параметр "model": "V5" добавлен во все блоки данных')
