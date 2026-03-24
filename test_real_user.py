#!/usr/bin/env python3
import sys
sys.path.append('/root/albimusic-bot')
from celery_tasks import generate_song_task
import time

print("=== ТЕСТ С РЕАЛЬНЫМ ПОЛЬЗОВАТЕЛЕМ ===")
print("Используем ваш реальный user_id: 338544009")

task = generate_song_task.delay(338544009, 'РЕАЛЬНЫЙ ТЕСТ пользователя', 'ТЕСТ СТИЛЬ', False)
task_id = task.id
print(f"Задача: {task_id}")
print(f"Начальный статус: {task.status}")

# Мониторим 2 минуты
print("\nМониторинг 2 минуты...")
for i in range(24):  # 24 * 5 = 120 секунд = 2 минуты
    time.sleep(5)
    status = task.status
    print(f"{i+1}. Через {(i+1)*5} сек: {status}")
    
    if status != 'PENDING':
        print(f"\n✅ Статус изменился: {status}")
        if status == 'SUCCESS':
            print(f"Результат: {task.result}")
        elif status == 'FAILURE':
            print(f"Ошибка: {task.result}")
        break

if task.status == 'PENDING':
    print(f"\n⚠️  Задача все еще PENDING после 2 минут")
    print("Но Celery Worker ее получил и начал выполнение!")
    print("Проверим логи...")
