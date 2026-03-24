import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим место для добавления инициализации БД (после импортов)
imports_end = content.find('logging.basicConfig')
if imports_end == -1:
    imports_end = content.find('bot = Bot(token=API_TOKEN)')

# Добавляем инициализацию пула БД
init_code = '''
# Инициализация пула соединений с БД
from db_utils import init_db_pool_sync
init_db_pool_sync()
logging.info("✅ Пул соединений с БД инициализирован")
'''

# Вставляем код после импортов
content = content[:imports_end] + init_code + content[imports_end:]

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Добавлена инициализация пула БД")
