#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app
import redis

print("=== ПРОВЕРКА TRANSPORT ===")

# Проверим конфигурацию
print(f"1. Broker URL: {celery_app.conf.broker_url}")
print(f"2. Broker transport: {celery_app.conf.broker_transport}")

# Попробуем подключиться к Redis как Celery
try:
    # Создадим соединение как Celery
    with celery_app.connection() as conn:
        print(f"3. Подключение установлено: {conn}")
        print(f"4. Transport: {conn.transport}")
        print(f"5. Клиент: {conn.client}")
        
        # Проверим, можем ли мы отправить сообщение
        producer = conn.Producer()
        print(f"6. Producer создан: {producer}")
        
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

# Проверим Redis напрямую
print("\n=== ПРЯМАЯ ПРОВЕРКА REDIS ===")
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    print(f"Redis ping: {r.ping()}")
    
    # Посмотрим на ключи
    keys_count = r.dbsize()
    print(f"Всего ключей в db0: {keys_count}")
    
    # Посмотрим на список очередей
    pattern = r.keys('*celery*')
    print(f"Ключей с 'celery': {len(pattern)}")
    if pattern:
        print(f"Пример ключа: {pattern[0]}")
        
except Exception as e:
    print(f"Redis ошибка: {e}")
