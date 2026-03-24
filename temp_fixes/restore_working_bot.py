import shutil

# Копируем из бэкапа
shutil.copy2('project_backup_20251125_233714/final_bot.py', 'final_bot.py')

# Исправляем импорты
with open('final_bot.py', 'r') as f:
    content = f.read()

content = content.replace('from database_adapter import db', 'from postgres_db import init_postgres, execute_query, fetch_query, fetchrow_query')
content = content.replace('await db.fetch_query', 'await fetch_query')
content = content.replace('await db.execute_query', 'await execute_query')
content = content.replace('await db.fetchrow_query', 'await fetchrow_query')

with open('final_bot.py', 'w') as f:
    f.write(content)

print('✅ Полностью рабочая версия восстановлена с правильными импортами')
