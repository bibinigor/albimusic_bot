#!/usr/bin/env python3
import redis
import sys

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    response = r.ping()
    print(f"Redis подключен: {response}")
    
    # Проверим очередь
    queue_length = r.llen('celery')
    print(f"Длина очереди celery: {queue_length}")
    
    # Проверим ключи
    keys = r.keys('*')
    print(f"Все ключи в Redis: {keys}")
    
except Exception as e:
    print(f"Ошибка подключения к Redis: {e}")
    sys.exit(1)
