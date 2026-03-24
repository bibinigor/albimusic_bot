# Читаем файл построчно
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Исправляем строку 123 (индекс 122)
if len(lines) > 122:
    # Заменяем проблемную строку
    lines[122] = '\n\n@celery_app.task(bind=True)\n'
    
    # Записываем обратно
    with open('celery_tasks.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Строка 123 исправлена")
else:
    print("❌ Файл короче чем ожидалось")
