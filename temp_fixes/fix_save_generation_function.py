# Читаем текущий файл
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Обновляем сигнатуру функции и SQL запрос
old_function = '''def save_generation_task_sync(user_id, task_id, prompt, status):
    """Синхронное сохранение задачи в БД"""
    try:
        execute_query_sync(
            """INSERT INTO generations (user_id, task_id, prompt, status, created_at) 
            VALUES (%s, %s, %s, %s, NOW())""",
            (user_id, task_id, prompt, status)
        )'''

new_function = '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None):
    """Синхронное сохранение задачи в БД"""
    try:
        execute_query_sync(
            """INSERT INTO generations (user_id, task_id, prompt, status, audio_url, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())""",
            (user_id, task_id, prompt, status, audio_url)
        )'''

content = content.replace(old_function, new_function)

# Записываем обратно
with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Обновлена функция save_generation_task_sync для поддержки audio_url")
