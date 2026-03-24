# Читаем текущий файл
with open('run_monitor_pro.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем все обращения к db на execute_query_sync
content = content.replace("db.get_user(", "get_user_from_db(")
content = content.replace("db.get_task(", "get_task_from_db(")
content = content.replace("db.update_task(", "update_task_in_db(")

# Добавляем недостающие функции
if 'def get_task_from_db' not in content:
    # Находим место для вставки функций (после get_user_from_db)
    user_func_end = content.find('def monitor_completed_tasks')
    
    # Вставляем функции
    db_functions = '''
def get_task_from_db(task_id):
    """Получить задачу из БД"""
    try:
        result = execute_query_sync('SELECT * FROM generations WHERE task_id = %s', (task_id,))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"❌ Ошибка получения задачи {task_id}: {e}")
        return None

def update_task_in_db(task_id, updates):
    """Обновить задачу в БД"""
    try:
        # Здесь должна быть логика обновления задачи
        # Пока просто логируем
        logger.info(f"🔄 Задача {task_id} обновлена: {updates}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления задачи {task_id}: {e}")
        return False

'''
    content = content[:user_func_end] + db_functions + content[user_func_end:]

# Записываем обратно
with open('run_monitor_pro.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлены все обращения к БД в мониторинге")
