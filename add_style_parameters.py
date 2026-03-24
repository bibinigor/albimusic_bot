import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Исправляем данные для custom_mode=true добавляя styleWeight и другие параметры
pattern1 = r'data = \{\s*"prompt": prompt,\s*"style": style if style else "pop",\s*"title": f"Song for user \{user_id\}" if user_id else "Generated Song",\s*"customMode": True,\s*"instrumental": False,\s*"model": "V5",\s*"callBackUrl": "https://example.com/callback"\s*\}'
replacement1 = '''data = {
                "prompt": prompt,
                "style": style if style else "pop",
                "title": f"Song for user {user_id}" if user_id else "Generated Song",
                "customMode": True,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback",
                "styleWeight": 0.9,  # Высокий вес стиля (0-1)
                "vocalGender": "m",  # Мужской вокал по умолчанию
                "weirdnessConstraint": 0.3  # Низкая креативность, высокая точность
            }'''

# Для instrumental музыки
pattern2 = r'data = \{\s*"prompt": prompt,\s*"customMode": False,\s*"instrumental": True,\s*"model": "V5",\s*"callBackUrl": "https://example.com/callback"\s*\}'
replacement2 = '''data = {
                "prompt": prompt,
                "customMode": False,
                "instrumental": True,
                "model": "V5",
                "callBackUrl": "https://example.com/callback",
                "styleWeight": 0.9
            }'''

# Для non-custom_mode песен
pattern3 = r'data = \{\s*"prompt": prompt,\s*"customMode": False,\s*"instrumental": False,\s*"model": "V5",\s*"callBackUrl": "https://example.com/callback"\s*\}'
replacement3 = '''data = {
                "prompt": prompt,
                "customMode": False,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback",
                "styleWeight": 0.9
            }'''

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)  
content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Добавлены параметры контроля стиля в Suno API!")
print("Добавлены:")
print("1. styleWeight: 0.9 - высокий приоритет стилю")
print("2. vocalGender: 'm' - мужской вокал по умолчанию")
print("3. weirdnessConstraint: 0.3 - низкая креативность, высокая точность")
print("")
print("Это должно заставить Suno точнее следовать описанию стиля!")
