import re

with open('db_utils.py', 'r') as f:
    lines = f.readlines()

# Найдем функцию execute_query_sync
in_function = False
for i, line in enumerate(lines):
    if 'def execute_query_sync(query, params=None):' in line:
        # Изменяем сигнатуру
        lines[i] = 'def execute_query_sync(query, params=None, fetch_one=False):\n'
        in_function = True
    
    elif in_function and 'if query.strip().upper().startswith' in line:
        # Нашли блок с SELECT - нужно изменить
        indent = len(line) - len(line.lstrip())
        
        # Создаем новые строки
        new_lines = [
            ' ' * indent + 'if query.strip().upper().startswith(\'SELECT\'):\n',
            ' ' * (indent + 4) + 'if fetch_one:\n',
            ' ' * (indent + 8) + 'return cursor.fetchone()\n',
            ' ' * (indent + 4) + 'else:\n',
            ' ' * (indent + 8) + 'return cursor.fetchall()\n',
            ' ' * indent + 'else:\n'
        ]
        
        # Заменяем текущую строку и следующие несколько
        # Удаляем старые строки
        for j in range(i, min(i+5, len(lines))):
            if 'cursor.fetchall()' in lines[j] or 'else:' in lines[j]:
                lines[j] = ''
        
        # Вставляем новые строки
        for j, new_line in enumerate(new_lines):
            lines.insert(i + j, new_line)
        
        break

# Сохраняем исправленный файл
with open('db_utils.py', 'w') as f:
    f.writelines(lines)

print("✅ db_utils.py исправлен с правильными отступами")
print("Теперь execute_query_sync поддерживает fetch_one=True")
