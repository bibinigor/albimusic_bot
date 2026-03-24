#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app
import redis

print("=== ПРОВЕРКА ОЧЕРЕДЕЙ ===")

# Проверим все базы данных Redis
for db in [0, 1, 2]:
    try:
        r = redis.Redis(host='localhost', port=6379, db=db)
        keys = r.keys('*')
        print(f"\nDatabase {db}: {len(keys)} ключей")
        
        # Ищем очереди
        queue_keys = [k for k in keys if isinstance(k, bytes) and not b'task-meta' in k and not b'kombu' in k]
        if queue_keys:
            print(f"  Возможные очереди: {queue_keys[:5]}")
            
        # Проверим kombu очереди (Celery использует kombu)
        kombu_keys = [k for k in keys if isinstance(k, bytes) and b'kombu' in k]
        if kombu_keys:
            print(f"  Kombu ключи: {kombu_keys[:5]}")
            
    except Exception as e:
        print(f"Database {db} ошибка: {e}")

# Проверим конфигурацию Celery для очередей
print("\n=== КОНФИГУРАЦИЯ CELERY ===")
print(f"task_default_queue: {celery_app.conf.task_default_queue}")
print(f"task_queues: {celery_app.conf.task_queues}")
print(f"task_routes: {celery_app.conf.task_routes}")

# Попробуем посмотреть через kombu
try:
    from kombu import Exchange, Queue
    
    # Получим exchange по умолчанию
    default_exchange = Exchange(celery_app.conf.task_default_exchange, 
                               type='direct')
    
    print(f"\nExchange по умолчанию: {default_exchange}")
    
    # Проверим, можем ли мы получить очередь
    with celery_app.connection() as conn:
        with conn.channel() as channel:
            queue = Queue(celery_app.conf.task_default_queue, 
                         exchange=default_exchange, 
                         routing_key=celery_app.conf.task_default_routing_key)
            
            declared = queue(channel)
            print(f"Очередь: {declared}")
            print(f"Сообщения в очереди: {declared.queue_declare().message_count}")
            
except Exception as e:
    print(f"Ошибка kombu: {e}")
    import traceback
    traceback.print_exc()
