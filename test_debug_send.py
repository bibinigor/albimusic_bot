#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import generate_song_task
import redis

print("=== ДЕТАЛЬНАЯ ОТЛАДКА ОТПРАВКИ ===")

# Подготовим тестовые данные
user_id = 338544009
lyrics = "ДЕТАЛЬНЫЙ ТЕСТ ТЕКСТА"
style = "ДЕТАЛЬНЫЙ ТЕСТ СТИЛЯ"

# Проверим Redis до отправки
r = redis.Redis(host='localhost', port=6379, db=0)
print(f"1. Сообщений в очереди до отправки: {r.llen('celery')}")

# Отправим задачу
print(f"\n2. Отправляем задачу...")
task = generate_song_task.delay(user_id, lyrics, style, custom_mode=False)
print(f"   ID задачи: {task.id}")
print(f"   Статус: {task.status}")

# Проверим Redis сразу после отправки
print(f"\n3. Сообщений в очереди после отправки: {r.llen('celery')}")

# Проверим, есть ли задача в Redis как ключ
task_key = f'celery-task-meta-{task.id}'
print(f"\n4. Проверяем ключ задачи: {task_key}")
task_exists = r.exists(task_key)
print(f"   Ключ существует: {task_exists}")

if task_exists:
    task_data = r.get(task_key)
    print(f"   Данные задачи: {task_data[:100]}...")

# Попробуем отправить задачу другим способом
print(f"\n5. Пробуем отправить через apply_async...")
task2 = generate_song_task.apply_async(
    args=[user_id, lyrics, style],
    kwargs={'custom_mode': False},
    queue='celery',  # Явно указываем очередь
    routing_key='celery'
)
print(f"   ID задачи 2: {task2.id}")
print(f"   Сообщений в очереди после apply_async: {r.llen('celery')}")

# Проверим через kombu
print(f"\n6. Проверяем через Kombu bindings...")
bindings = r.smembers('_kombu.binding.celery')
print(f"   Bindings для очереди celery: {bindings}")
