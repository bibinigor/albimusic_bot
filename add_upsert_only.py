import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Наша исправленная функция save_generation_task_sync (UPSERT)
upsert_function = '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None):
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

# Найдем и заменим старую функцию
old_pattern = r'def save_generation_task_sync\(user_id, task_id, prompt, status, audio_url=None\):.*?except Exception as e:.*?logger\.error\(f".*?{e}"\)'

if re.search(old_pattern, content, re.DOTALL):
    content = re.sub(old_pattern, upsert_function, content, flags=re.DOTALL)
    print("✅ Функция save_generation_task_sync заменена на UPSERT версию")
else:
    print("❌ Не найдена старая функция save_generation_task_sync")
    # Добавим функцию в конец файла перед последней строкой
    if 'def save_generation_task_sync' not in content:
        # Найдем последнюю функцию и добавим после нее
        content += '\n\n' + upsert_function
        print("✅ Функция save_generation_task_sync добавлена")

with open('celery_tasks.py', 'w') as f:
    f.write(content)
