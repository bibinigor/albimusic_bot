with open('celery_tasks.py', 'r') as f:
    lines = f.readlines()

# Находим строку с improvements = []
for i, line in enumerate(lines):
    if 'improvements = []' in line:
        # Удаляем неправильные строки после этого
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith('('):
            lines[j] = ''
            j += 1
        break

with open('celery_tasks.py', 'w') as f:
    f.writelines(lines)

print('✅ Исправлены отступы в блоке improvements')
