#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app

print("=== КОНФИГУРАЦИЯ CELERY ===")
print(f"Брокер: {celery_app.conf.broker_url}")
print(f"Бэкенд результатов: {celery_app.conf.result_backend}")
print(f"Очереди по умолчанию: {celery_app.conf.task_default_queue}")
print(f"Exchange по умолчанию: {celery_app.conf.task_default_exchange}")
print(f"Ключ маршрутизации по умолчанию: {celery_app.conf.task_default_routing_key}")

# Проверим, как создается соединение с брокером
try:
    with celery_app.connection() as conn:
        print(f"\nПодключение к брокеру установлено")
        print(f"Транспорт: {conn.info.get('transport')}")
        
        # Попробуем отправить тестовое сообщение
        from kombu import Exchange, Queue
        
        default_exchange = Exchange('celery', type='direct')
        default_queue = Queue('celery', exchange=default_exchange, routing_key='celery')
        
        with conn.channel() as channel:
            queue = default_queue(channel)
            queue.declare()
            print(f"Очередь 'celery' существует")
            
except Exception as e:
    print(f"\nОшибка подключения к брокеру: {e}")
