import re

# Читаем файл
with open('celery_tasks.py', 'r') as f:
    content = f.read()

# 1. Увеличиваем таймаут запроса с 60 до 300 секунд
content = content.replace('timeout=60', 'timeout=300')

# 2. Увеличиваем цикл ожидания с 90 до 180 попыток (30 минут)
content = re.sub(r'for i in range\((\d+)\):', 'for i in range(180):', content)

# 3. Увеличиваем порог предупреждения с 30 до 60 (10 минут)
content = content.replace('if i > 30 and status == "PENDING":', 'if i > 60 and status == "PENDING":')

# Сохраняем изменения
with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Таймауты увеличены:")
print("   - Таймаут запроса: 60 → 300 секунд (5 минут)")
print("   - Цикл ожидания: 90 → 180 попыток (30 минут)")
print("   - Предупреждение о медленном API: через 10 минут")
