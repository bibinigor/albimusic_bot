with open('run_monitor_pro.py', 'r') as f:
    content = f.read()

# Добавляем импорт в начало файла
if 'from db_utils import execute_query_sync' not in content:
    # Находим место после импортов
    import_end = content.find('bot = Bot(token=config.BOT_TOKEN)')
    if import_end != -1:
        content = content[:import_end] + 'from db_utils import execute_query_sync\\n\\n' + content[import_end:]

# Заменяем вызовы функций
content = content.replace('execute_query_sync(', 'result = execute_query_sync(')
content = content.replace("'SELECT task_id, user_id, audio_url, custom_mode, prompt FROM generations WHERE status = $1 AND notified = $2',", "'SELECT task_id, user_id, audio_url, custom_mode, prompt FROM generations WHERE status = %s AND notified = %s',")
content = content.replace("'completed', False", "'completed', False)")

# Исправляем обработку результатов
content = content.replace('for task in completed_tasks:', 'for task in result:')

with open('run_monitor_pro.py', 'w') as f:
    f.write(content)

print('✅ Мониторинг окончательно исправлен')
