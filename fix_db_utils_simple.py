# Прочитаем файл
with open('db_utils.py', 'r') as f:
    lines = f.readlines()

# Найдем начало функции execute_query_sync
start_line = -1
for i, line in enumerate(lines):
    if 'def execute_query_sync(query, params=None):' in line:
        start_line = i
        lines[i] = 'def execute_query_sync(query, params=None, fetch_one=False):\n'
        break

if start_line != -1:
    # Найдем строку с cursor.fetchall()
    for i in range(start_line, len(lines)):
        if 'cursor.fetchall()' in lines[i]:
            # Вставляем новую логику
            indent = len(lines[i]) - len(lines[i].lstrip())
            indent_str = ' ' * indent
            
            # Удаляем старую строку
            lines[i] = ''
            
            # Вставляем новые строки
            new_lines = [
                f'{indent_str}if fetch_one:\n',
                f'{indent_str}    return cursor.fetchone()\n',
                f'{indent_str}else:\n',
                f'{indent_str}    return cursor.fetchall()\n'
            ]
            
            # Вставляем перед следующей строкой
            for j, new_line in enumerate(new_lines):
                lines.insert(i + j, new_line)
            break
    
    print("✅ Функция execute_query_sync обновлена")
    
    # Сохраняем
    with open('db_utils.py', 'w') as f:
        f.writelines(lines)
else:
    print("❌ Не найдена функция execute_query_sync")
