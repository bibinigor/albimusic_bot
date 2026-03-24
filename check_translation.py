import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Найдём блок с объединением стиля и текста (который мы добавляли)
pattern = r'# ОБЪЕДИНЕНИЕ СТИЛЯ И ТЕКСТА[\s\S]*?prompt = lyrics  # Только текст песни если стиль не указан'

match = re.search(pattern, content)
if match:
    print("✅ Найден блок объединения стиля и текста:")
    print("-" * 50)
    print(match.group(0))
    print("-" * 50)
    
    # Проверим, есть ли вызов translate_style_to_english
    if 'translate_style_to_english' in match.group(0):
        print("✅ Вызов translate_style_to_english ПРИСУТСТВУЕТ в коде")
    else:
        print("❌ Вызов translate_style_to_english ОТСУТСТВУЕТ в коде!")
else:
    print("❌ Блок объединения стиля и текста не найден!")
    
# Теперь найдём саму функцию translate_style_to_english
print("\n" + "="*50)
print("Проверка функции translate_style_to_english:")
trans_pattern = r'def translate_style_to_english[\s\S]*?return translated_style'
trans_match = re.search(trans_pattern, content)
if trans_match:
    print("✅ Функция перевода найдена в файле")
else:
    print("❌ Функция перевода НЕ найдена в файле!")
