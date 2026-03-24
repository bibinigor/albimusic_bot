import re

# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Новая исправленная функция add_generation
new_function = '''def add_generation(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False):
    """Добавление генерации с защитой от дублирования"""
    try:
        from db_utils import execute_query_sync
        
        # ПРОВЕРКА: Уже есть такая задача?
        existing_task = execute_query_sync(
            'SELECT id FROM generations WHERE user_id = %s AND task_id = %s',
            (user_id, task_id),
            fetch_one=True
        )
        
        if existing_task:
            # Задача уже существует
            logging.info(f"⚠️  Задача {task_id} уже существует в БД для пользователя {user_id}")
            return False
        
        # Если задачи нет - создаем
        result = execute_query_sync(
            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())', 
            (user_id, task_id, prompt, audio_url, is_free, custom_mode, 'pending')
        )
        
        if result:
            logging.info(f"✅ Добавлена генерация {task_id} для пользователя {user_id}")
            return True
        else:
            logging.error(f"❌ Не удалось добавить генерацию {task_id} для пользователя {user_id}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Ошибка добавления генерации {user_id}: {e}")
        return False'''

# Найдем и заменим функцию add_generation
# Ищем от def add_generation до следующей функции def
pattern = r'(def add_generation\(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False\):.*?\n)(?=def \w+|\Z)'

match = re.search(pattern, content, re.DOTALL)
if match:
    old_function = match.group(1)
    content = content.replace(old_function, new_function + '\n\n')
    print("✅ Функция add_generation обновлена!")
    
    # Сохраняем изменения
    with open('main_with_payments.py', 'w') as f:
        f.write(content)
    
    print("📋 Что исправлено:")
    print("1. Проверка существования задачи теперь работает с fetch_one=True")
    print("2. Проверка if existing_task (а не if check_result)")
    print("3. Проверка результата INSERT (if result)")
    print("4. Возвращаем True/False в зависимости от успеха")
else:
    print("❌ Не удалось найти функцию add_generation")
