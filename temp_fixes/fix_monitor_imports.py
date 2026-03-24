with open('run_monitor_pro.py', 'r') as f:
    content = f.read()

# Добавляем импорт db_utils
if 'from db_utils import execute_query_sync' not in content:
    import_end = content.find('bot = Bot(token=config.BOT_TOKEN)')
    if import_end != -1:
        content = content[:import_end] + 'from db_utils import execute_query_sync\\n\\n' + content[import_end:]

# Заменяем асинхронные вызовы на синхронные
content = content.replace('await self.init_db()', '# await self.init_db()  # Пропускаем инициализацию')
content = content.replace("await self.db.fetch_query(", "result = execute_query_sync(")
content = content.replace("'completed', False", "'completed', False)")
content = content.replace('for task in tasks:', 'for task in (result or []):')
content = content.replace("await self.db.execute_query(", "execute_query_sync(")
content = content.replace("task['task_id']", "task[0]")  # task_id
content = content.replace("task['user_id']", "task[1]")  # user_id  
content = content.replace("task['audio_url']", "task[2]")  # audio_url
content = content.replace("task['prompt']", "task[3]")  # prompt

with open('run_monitor_pro.py', 'w') as f:
    f.write(content)

print('✅ Импорты мониторинга исправлены')
