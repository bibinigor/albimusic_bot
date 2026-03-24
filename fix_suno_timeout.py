#!/usr/bin/env python3
import re

with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
    content = f.read()

# Находим цикл ожидания и увеличиваем время/попытки
# Было: for i in range(30):  # 30 попыток по 10 секунд = 5 минут
# Стало: for i in range(90):  # 90 попыток по 10 секунд = 15 минут

# Также добавим логирование прогресса

new_content = re.sub(
    r'# Ожидаем завершения генерации\n\s+for i in range\(30\):  # 30 попыток по 10 секунд = 5 минут\n\s+time\.sleep\(10\)',
    '''# Ожидаем завершения генерации (увеличено для медленного Suno API)
            for i in range(90):  # 90 попыток по 10 секунд = 15 минут
                time.sleep(10)''',
    content
)

# Добавим проверку на долгое ожидание
new_content = re.sub(
    r'logger\.info\(f"📊 Статус задачи Suno {task_id}: {status} \(попытка {i\+1}\)"\)',
    '''logger.info(f"📊 Статус задачи Suno {task_id}: {status} (попытка {i+1}/90)")
                    # Если Suno слишком долго думает, возможно проблема
                    if i > 30 and status == "PENDING":
                        logger.warning(f"⚠️ Suno API очень медленный: задача {task_id} все еще PENDING после {i*10} секунд")''',
    new_content
)

with open('/root/albimusic-bot/celery_tasks.py', 'w') as f:
    f.write(new_content)

print("✅ Таймауты увеличены: 15 минут вместо 5")
print("✅ Добавлено логирование медленных задач")
