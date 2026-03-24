#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import generate_song_task

# Данные как в боте
user_id = 338544009
lyrics = "ТЕКСТ ИЗ БОТА: Солнце светит ярко, птицы поют"
style = "СТИЛЬ ИЗ БОТА: Поп-музыка"
custom_mode = False

print("=== ИМИТАЦИЯ ВЫЗОВА ИЗ БОТА ===")
print(f"user_id: {user_id}")
print(f"lyrics: {lyrics}")
print(f"style: {style}")
print(f"custom_mode: {custom_mode}")

# Вызываем как в боте (строка 432 из main_with_payments.py)
task = generate_song_task.delay(user_id, lyrics, style, custom_mode)

print(f"\nЗадача отправлена через .delay()")
print(f"ID задачи: {task.id}")
print(f"Статус: {task.status}")

# Давайте проверим очередь сразу
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
queue_len = r.llen('celery')
print(f"\nДлина очереди celery сразу после отправки: {queue_len}")

if queue_len > 0:
    task_data = r.lrange('celery', 0, 0)[0]
    print(f"Первая задача в очереди: {task_data[:200]}...")
