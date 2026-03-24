import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Убираем текущую инициализацию
content = re.sub(r'from db_utils import init_db_pool_sync\s+init_db_pool_sync\(\)\s+logging\.info\("✅ Пул соединений с БД инициализирован"\)', '', content)

# Находим место после настройки логирования и создания бота
bot_creation = content.find('bot = Bot(token=API_TOKEN)')
if bot_creation != -1:
    # Находим конец строки с созданием бота
    end_of_line = content.find('\n', bot_creation)
    
    # Добавляем инициализацию БД после создания бота
    init_code = '''
# Инициализация пула соединений с БД
from db_utils import init_db_pool_sync
init_db_pool_sync()
logging.info("✅ Пул соединений с БД инициализирован")
'''
    content = content[:end_of_line] + init_code + content[end_of_line:]

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Перемещена инициализация пула БД")
