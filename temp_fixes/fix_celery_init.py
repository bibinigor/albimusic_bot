import fileinput
import sys

# Читаем файл и добавляем инициализацию пула
new_lines = []
with open('celery_tasks.py', 'r') as f:
    lines = f.readlines()
    
    # Ищем место после импортов
    for i, line in enumerate(lines):
        new_lines.append(line)
        if 'from db_utils import execute_query_sync' in line:
            # Добавляем инициализацию после импорта
            new_lines.append('\n')
            new_lines.append('# Инициализация пула БД\n')
            new_lines.append('from db_utils import init_db_pool_sync\n')
            new_lines.append('init_db_pool_sync()\n')
            new_lines.append('\n')

# Записываем обратно
with open('celery_tasks.py', 'w') as f:
    f.writelines(new_lines)

print('✅ Инициализация пула БД добавлена в celery_tasks.py')
