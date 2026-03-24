#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app
import celery
import kombu
import redis

print("=== ВЕРСИИ БИБЛИОТЕК ===")
print(f"Celery: {celery.__version__}")
print(f"Kombu: {kombu.__version__}")
print(f"Redis-py: {redis.__version__}")

print("\n=== НАСТРОЙКИ СЕРИАЛИЗАЦИИ ===")
print(f"task_serializer: {celery_app.conf.task_serializer}")
print(f"accept_content: {celery_app.conf.accept_content}")
print(f"result_serializer: {celery_app.conf.result_serializer}")

print("\n=== НАСТРОЙКИ БРОКЕРА ===")
print(f"broker_url: {celery_app.conf.broker_url}")
print(f"broker_connection_retry_on_startup: {celery_app.conf.get('broker_connection_retry_on_startup', 'Not set')}")

# Проверим, есть ли известные проблемы
print("\n=== ПРОВЕРКА ИЗВЕСТНЫХ ПРОБЛЕМ ===")

# Celery 5.x имеет проблему с broker_connection_retry_on_startup
if celery.__version__.startswith('5.'):
    print(f"Celery 5.x detected - checking broker_connection_retry_on_startup")
    if not celery_app.conf.get('broker_connection_retry_on_startup', False):
        print("  WARNING: broker_connection_retry_on_startup is not set to True!")
        print("  This is a known issue in Celery 5.x")
        
# Проверим настройки transport_options
print(f"broker_transport_options: {celery_app.conf.get('broker_transport_options', {})}")
