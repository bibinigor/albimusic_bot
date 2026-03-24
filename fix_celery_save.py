import re

# Читаем файл
with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Новая функция save_generation_task_sync с UPSERT
new_function = '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None):
    """Синхронное сохранение/обновление задачи в БД"""
    try:
        # Пробуем найти существующую задачу
        existing = execute_query_sync(
            "SELECT id FROM generations WHERE user_id = %s AND task_id = %s",
            (user_id, task_id),
            fetch_one=True
        )
        
        if existing:
            # ОБНОВЛЯЕМ существующую задачу
            execute_query_sync(
                """UPDATE generations 
                SET status = %s, audio_url = %s, completed_at = NOW() 
                WHERE user_id = %s AND task_id = %s""",
                (status, audio_url, user_id, task_id)
            )
            logger.info(f"✅ Задача {task_id} ОБНОВЛЕНА в БД (статус: {status})")
        else:
            # СОЗДАЕМ новую задачу
            execute_query_sync(
                """INSERT INTO generations (user_id, task_id, prompt, status, audio_url, created_at) 
                VALUES (%s, %s, %s, %s, %s, NOW())""",
                (user_id, task_id, prompt, status, audio_url)
            )
            logger.info(f"✅ Задача {task_id} СОЗДАНА в БД (статус: {status})")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения задачи {task_id}: {e}")
        return False'''

# Заменяем старую функцию
old_function = '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None):
    """Синхронное сохранение задачи в БД"""
    try:
        execute_query_sync(
            """INSERT INTO generations (user_id, task_id, prompt, status, audio_url, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())""",
            (user_id, task_id, prompt, status, audio_url)
        )
        logger.info(f"✅ Задача {task_id} сохранена в БД")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения задачи {task_id}: {e}")
        return False'''

if old_function in content:
    content = content.replace(old_function, new_function)
    print("✅ Функция save_generation_task_sync обновлена на UPSERT!")
else:
    print("❌ Не удалось найти старую функцию")

# Сохраняем изменения
with open('celery_tasks.py', 'w') as f:
    f.write(content)

print()
print("📋 Изменения:")
print("1. Теперь функция проверяет, существует ли задача")
print("2. Если существует - UPDATE (обновляет статус и audio_url)")
print("3. Если не существует - INSERT (создает новую)")
print("4. Добавлено поле completed_at при UPDATE")
