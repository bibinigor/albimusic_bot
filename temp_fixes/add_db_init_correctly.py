# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку с созданием бота
bot_line = -1
for i, line in enumerate(lines):
    if 'bot = Bot(token=API_TOKEN)' in line:
        bot_line = i
        break

if bot_line != -1:
    # Вставляем инициализацию БД после создания бота
    init_lines = [
        '\n',
        '# Инициализация пула соединений с БД\n',
        'from db_utils import init_db_pool_sync\n',
        'init_db_pool_sync()\n',
        'logging.info("✅ Пул соединений с БД инициализирован")\n',
        '\n'
    ]
    
    # Вставляем после строки с созданием бота
    lines[bot_line+1:bot_line+1] = init_lines
    
    # Записываем обратно
    with open('main_with_payments.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Инициализация БД добавлена после создания бота")
else:
    print("❌ Не найдена строка создания бота")
