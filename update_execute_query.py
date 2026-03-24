import re

# Читаем файл
with open('db_utils.py', 'r') as f:
    content = f.read()

# Обновляем сигнатуру функции
new_signature = 'def execute_query_sync(query, params=None, fetch_one=False):'

# Заменяем старую сигнатуру
if 'def execute_query_sync(query, params=None):' in content:
    content = content.replace('def execute_query_sync(query, params=None):', new_signature)
    print("✅ Сигнатура функции обновлена (добавлен fetch_one)")
else:
    print("❌ Не найдена старая сигнатура")

# Обновляем логику внутри функции
# Найдем блок с cursor.execute
pattern = r'(\s+)with conn\.cursor\(\) as cursor:\s*\n\s+cursor\.execute\(query, params\)\s*\n\s+if query\.strip\(\)\.upper\(\)\.startswith\(\'SELECT\'\):\s*\n\s+return cursor\.fetchall\(\)'

match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
if match:
    indent = match.group(1)
    old_block = match.group(0)
    
    # Новая логика с fetch_one
    new_block = f'''{indent}with conn.cursor() as cursor:
{indent}    cursor.execute(query, params)
{indent}    if query.strip().upper().startswith('SELECT'):
{indent}        if fetch_one:
{indent}            return cursor.fetchone()
{indent}        else:
{indent}            return cursor.fetchall()
{indent}    else:'''
    
    content = content.replace(old_block, new_block)
    print("✅ Логика функции обновлена (добавлена поддержка fetch_one)")
else:
    print("❌ Не найден блок с cursor.execute")

# Сохраняем изменения
with open('db_utils.py', 'w') as f:
    f.write(content)

print()
print("📋 Обновления в execute_query_sync:")
print("1. Добавлен параметр fetch_one=False")
print("2. Если fetch_one=True, возвращает cursor.fetchone()")
print("3. Если fetch_one=False, возвращает cursor.fetchall() (как было)")
