import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем SQLite на PostgreSQL в функции add_generation
old_add_generation = '''def add_generation(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False):
    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode) VALUES (?, ?, ?, ?, ?, ?)', 
                      (user_id, task_id, prompt, audio_url, is_free, custom_mode))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"❌ Ошибка добавления генерации {user_id}: {e}")'''

new_add_generation = '''def add_generation(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False):
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s, %s)', 
            (user_id, task_id, prompt, audio_url, is_free, custom_mode)
        )
    except Exception as e:
        logging.error(f"❌ Ошибка добавления генерации {user_id}: {e}")'''

content = content.replace(old_add_generation, new_add_generation)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлена функция add_generation для PostgreSQL")
