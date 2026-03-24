with open('celery_tasks.py', 'r') as f:
    lines = f.readlines()

# Находим и удаляем лишнюю строку с ']'
for i, line in enumerate(lines):
    if line.strip() == ']' and i > 70 and i < 80:
        # Проверяем, что это именно лишняя скобка (не относится к словарю)
        if i+1 < len(lines) and 'for key, value in improvements:' in lines[i+1]:
            lines[i] = ''  # Удаляем эту строку
            print(f'✅ Удалена лишняя скобка в строке {i+1}')
            break

with open('celery_tasks.py', 'w') as f:
    f.writelines(lines)
