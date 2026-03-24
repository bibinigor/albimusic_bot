import fileinput
import sys

with open('final_bot.py', 'r') as f:
    content = f.read()

# Заменяем database_adapter на postgres_db
content = content.replace('from database_adapter import db', 'from postgres_db import db, init_postgres')

with open('final_bot.py', 'w') as f:
    f.write(content)

print('✅ Импорты исправлены в final_bot.py')
