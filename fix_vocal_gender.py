import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Добавляем функцию определения пола вокала из стиля
gender_function = '''
def detect_vocal_gender_from_style(style):
    """Определяет пол вокала из описания стиля"""
    if not style:
        return None
    
    style_lower = style.lower()
    
    # Ключевые слова для мужского вокала
    male_keywords = ['мужск', 'male', 'мужской', 'мужчина', 'парень', 'man', 'голос мужчин']
    
    # Ключевые слова для женского вокала  
    female_keywords = ['женск', 'female', 'женский', 'женщина', 'девушка', 'woman', 'голос женщин']
    
    for keyword in male_keywords:
        if keyword in style_lower:
            return "m"
    
    for keyword in female_keywords:
        if keyword in style_lower:
            return "f"
    
    # По умолчанию None (Suno сам решит)
    return None
'''

# Вставляем функцию после импортов
if 'def detect_vocal_gender_from_style' not in content:
    # Находим место после logger
    logger_pos = content.find('logger = logging.getLogger(__name__)')
    if logger_pos != -1:
        insert_pos = content.find('\\n', logger_pos) + 1
        new_content = content[:insert_pos] + gender_function + content[insert_pos:]
        
        # Теперь исправляем данные для custom_mode чтобы использовать определение пола
        pattern = r'"vocalGender": "m",  # Мужской вокал по умолчанию'
        replacement = '"vocalGender": detect_vocal_gender_from_style(style),  # Автоматическое определение пола из стиля'
        
        new_content = re.sub(pattern, replacement, new_content)
        
        with open('celery_tasks.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Добавлено автоматическое определение пола вокала из стиля!")
        print("Теперь система будет анализировать описание стиля и определять:")
        print("- 'мужской', 'male' → мужской вокал (m)")
        print("- 'женский', 'female' → женский вокал (f)")
        print("- Если не указано → Suno сам решает (None)")
    else:
        print("❌ Не найдено место для вставки функции")
else:
    print("✅ Функция уже существует")
