import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем и исправляем импорты Celery
if 'from celery_tasks import generate_music_task, generate_song_task' not in content:
    # Находим место для вставки импортов (после других импортов)
    imports_end = content.find('@dp.message_handler')
    
    # Вставляем импорты Celery
    celery_import = "\n# Импорты для Celery задач\nfrom celery_tasks import generate_music_task, generate_song_task\n"
    content = content[:imports_end] + celery_import + content[imports_end:]
    
    print("✅ Добавлены импорты Celery")

# Проверяем обработчики генерации музыки
if 'generate_music_task.delay' not in content:
    print("❌ Обработчики не используют Celery задачи")
    
    # Найдем обработчик генерации музыки
    music_handler = content.find('async def process_music_generation')
    if music_handler != -1:
        print("✅ Найден обработчик музыки")
    
    song_handler = content.find('async def process_song_generation')
    if song_handler != -1:
        print("✅ Найден обработчик песни")

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Проверка импортов завершена")
