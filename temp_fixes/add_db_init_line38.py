# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Добавляем инициализацию БД после строки 38 (создание бота)
init_lines = [
    '\n',
    '# Инициализация пула соединений с БД\n',
    'from db_utils import init_db_pool_sync\n',
    'init_db_pool_sync()\n',
    'logging.info("✅ Пул соединений с БД инициализирован")\n',
    '\n'
]

# Вставляем после строки 38 (индекс 37 в 0-based)
lines[38:38] = init_lines

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Инициализация БД добавлена после создания бота")
