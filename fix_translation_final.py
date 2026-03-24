with open('celery_tasks.py', 'r') as f:
    content = f.read()

# 1. Добавляем недостающие переводы в словарь
add_to_dict = '''
        # Пропущенные переводы
        "соло": "solo",
        "ударные": "drums",'''

# Вставляем после строки с инструментами
if '"ударные": "drums",' not in content:
    content = content.replace('        # Инструменты', f'        # Инструменты\n        "ударные": "drums",')

# 2. Убираем вредные "улучшения" которые портят перевод
bad_improvements = '''    # Улучшения для Suno
    improvements = [
        ("electric guitar", "electric guitar solo"),
        ("bass", "bass guitar"),
        ("drums", "drum kit"),
        ("male vocal", "male rock vocal"),'''

good_improvements = '''    # Улучшения для Suno (упрощенные)
    improvements = []'''

if bad_improvements in content:
    content = content.replace(bad_improvements, good_improvements)
    print("✅ Убраны вредные 'улучшения'")
else:
    print("⚠️ Блок 'улучшений' не найден в ожидаемом формате")

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Словарь перевода исправлен")
