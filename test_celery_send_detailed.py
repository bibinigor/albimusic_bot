#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app, generate_song_task
import redis
import time

print("=== ДЕТАЛЬНАЯ ПРОВЕРКА ОТПРАВКИ ===")

# Тест 1: Прямая отправка через celery_app
print("\n1. Тест: Отправка через celery_app.send_task()")
task1 = celery_app.send_task(
    'celery_tasks.generate_song_task',
    args=[999888, 'ТЕСТ через send_task', 'СТИЛЬ тест'],
    kwargs={'custom_mode': False}
)
print(f"   Задача отправлена: {task1.id}")
print(f"   Статус: {task1.status}")

# Проверим Redis
r = redis.Redis(host='localhost', port=6379, db=0)
print(f"   Redis ключи kombu: {len(r.keys('kombu*'))}")

# Тест 2: Отправка через .delay()
print("\n2. Тест: Отправка через .delay()")
task2 = generate_song_task.delay(999888, 'ТЕСТ через delay', 'СТИЛЬ тест', custom_mode=False)
print(f"   Задача отправлена: {task2.id}")
print(f"   Статус: {task2.status}")
print(f"   Redis ключи kombu: {len(r.keys('kombu*'))}")

# Тест 3: Проверим, видит ли Celery задачи
print("\n3. Тест: Проверка через Celery inspect")
try:
    i = celery_app.control.inspect()
    active = i.active()
    scheduled = i.scheduled()
    reserved = i.reserved()
    
    print(f"   Активные задачи: {active}")
    print(f"   Запланированные: {scheduled}")
    print(f"   Зарезервированные: {reserved}")
    
except Exception as e:
    print(f"   Ошибка inspect: {e}")

# Тест 4: Проверим connection напрямую
print("\n4. Тест: Прямая проверка подключения")
try:
    with celery_app.connection() as conn:
        print(f"   Подключение: {conn.connected}")
        
        # Проверим producer
        producer = conn.Producer()
        print(f"   Producer: {producer}")
        
        # Попробуем отправить напрямую
        from kombu import Exchange, Queue
        exchange = Exchange('celery', type='direct')
        queue = Queue('celery', exchange=exchange, routing_key='celery')
        
        print(f"   Exchange: {exchange}")
        print(f"   Queue: {queue}")
        
except Exception as e:
    print(f"   Ошибка: {e}")
    import traceback
    traceback.print_exc()

print(f"\n⏱️  Ожидание 30 секунд...")
time.sleep(30)
print(f"\nФинальные статусы:")
print(f"  Задача 1: {task1.status}")
print(f"  Задача 2: {task2.status}")
