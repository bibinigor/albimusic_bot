# Читаем текущий файл
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем проблему с экранированием
content = content.replace('\\n\\n@celery_app.task', '\n\n@celery_app.task')

# Записываем обратно
with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлена синтаксическая ошибка")
