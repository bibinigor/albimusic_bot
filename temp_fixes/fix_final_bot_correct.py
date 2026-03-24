with open('final_bot.py', 'r') as f:
    content = f.read()

# Убираем неправильный импорт db
content = content.replace('from postgres_db import db, init_postgres', 'from postgres_db import init_postgres, execute_query, fetch_query, fetchrow_query')

# Заменяем использование db.fetch_query на fetch_query
content = content.replace('await db.fetch_query', 'await fetch_query')
content = content.replace('await db.execute_query', 'await execute_query')
content = content.replace('await db.fetchrow_query', 'await fetchrow_query')

with open('final_bot.py', 'w') as f:
    f.write(content)

print('✅ Импорты и вызовы БД исправлены')
