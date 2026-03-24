#!/usr/bin/env python3
import redis
import time

print("=== ТЕСТ ПОДКЛЮЧЕНИЯ К REDIS ===")

# Те же настройки, что в celery_tasks.py
redis_url = 'redis://localhost:6379/0'
print(f"URL: {redis_url}")

try:
    # Подключаемся как Celery
    r = redis.Redis.from_url(redis_url, socket_connect_timeout=5)
    
    print("1. Подключение...")
    print(f"   Ping: {r.ping()}")
    
    print("\n2. Отправка тестового сообщения...")
    test_key = f'test_{int(time.time())}'
    r.set(test_key, 'test_value')
    value = r.get(test_key)
    print(f"   Ключ {test_key}: {value}")
    
    print("\n3. Проверка очереди...")
    # Пробуем отправить в очередь как Celery
    import json
    test_task = {
        'task': 'test_task',
        'id': 'test_id_123',
        'args': [1, 2, 3],
        'kwargs': {}
    }
    
    # Celery использует lpush для очереди
    result = r.lpush('celery', json.dumps(test_task))
    print(f"   Отправлено в очередь 'celery': {result} сообщений")
    
    print(f"   Длина очереди: {r.llen('celery')}")
    
    print("\n4. Чтение из очереди...")
    if r.llen('celery') > 0:
        task_data = r.rpop('celery')
        print(f"   Получено: {task_data}")
    
    print("\n✅ Redis работает корректно")
    
except Exception as e:
    print(f"\n❌ Ошибка Redis: {e}")
    import traceback
    traceback.print_exc()
