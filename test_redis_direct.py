#!/usr/bin/env python3
import redis

# Проверим подключение
try:
    r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
    print(f"Пинг Redis: {r.ping()}")
    
    # Проверим конфигурацию
    print(f"Информация о сервере:")
    info = r.info()
    print(f"  Версия Redis: {info.get('redis_version')}")
    print(f"  Подключенные клиенты: {info.get('connected_clients')}")
    
    # Проверим все базы данных
    for key in info.keys():
        if key.startswith('db'):
            print(f"  {key}: {info[key]}")
            
except Exception as e:
    print(f"Ошибка: {e}")
