import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Добавляем логирование входящих параметров в generate_song_task
pattern = r'logger.info\(f"🔄 Запуск генерации песни для пользователя \{user_id\}, задача \{task_id\}"\)'
replacement = '''logger.info(f"🔄 Запуск генерации песни для пользователя {user_id}, задача {task_id}")
        logger.info(f"📥 ВХОДЯЩИЕ ПАРАМЕТРЫ:")
        logger.info(f"   lyrics: {lyrics}")
        logger.info(f"   style: {style}")
        logger.info(f"   custom_mode: {custom_mode}")'''

if pattern in content:
    content = content.replace(pattern, replacement)
    print("✅ Добавлено логирование параметров в generate_song_task")
else:
    print("❌ Не найдена строка для замены")

with open('celery_tasks.py', 'w') as f:
    f.write(content)
