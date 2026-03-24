import re

# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Новая улучшенная функция add_generation
new_function = '''def add_generation(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False):
    """Добавление генерации с защитой от дублирования"""
    try:
        from db_utils import execute_query_sync
        
        # ПРОВЕРКА: Уже есть такая задача?
        check_result = execute_query_sync(
            'SELECT id FROM generations WHERE user_id = %s AND task_id = %s',
            (user_id, task_id),
            fetch_one=True
        )
        
        if check_result:
            # Задача уже существует
            logging.info(f"⚠️  Задача {task_id} уже существует в БД для пользователя {user_id}")
            return False
        
        # Если задачи нет - создаем
        execute_query_sync(
            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())', 
            (user_id, task_id, prompt, audio_url, is_free, custom_mode, 'pending')
        )
        logging.info(f"✅ Добавлена генерация {task_id} для пользователя {user_id}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Ошибка добавления генерации {user_id}: {e}")
        return False'''

# Заменяем старую функцию на новую
old_function_pattern = r'def add_generation\(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False\):.*?\n\s+except Exception as e:\s+logging\.error\(f".*?{e}"\)'

# Простая замена по точному тексту
old_function_text = '''def add_generation(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False):
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s, %s)', 
            (user_id, task_id, prompt, audio_url, is_free, custom_mode)
        )
    except Exception as e:
        logging.error(f"❌ Ошибка добавления генерации {user_id}: {e}")'''

if old_function_text in content:
    content = content.replace(old_function_text, new_function)
    print("✅ Функция add_generation обновлена с защитой от дублирования!")
    
    # Сохраняем изменения
    with open('main_with_payments.py', 'w') as f:
        f.write(content)
    
    print("📋 Изменения:")
    print("1. Добавлена проверка существования задачи перед INSERT")
    print("2. Добавлен статус 'pending' по умолчанию")
    print("3. Добавлено логирование успеха/дублирования")
else:
    print("❌ Не удалось найти функцию add_generation для замены")
    print("Проверьте содержимое файла вручную")
