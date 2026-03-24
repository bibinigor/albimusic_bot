#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app
import kombu

print("=== KOMBU КОНФИГУРАЦИЯ ===")
print(f"1. Broker URL: {celery_app.conf.broker_url}")
print(f"2. Broker transport: {celery_app.conf.broker_transport}")
print(f"3. Broker transport options: {celery_app.conf.get('broker_transport_options', {})}")

# Проверим подключение
try:
    with celery_app.connection() as conn:
        print(f"\n4. Подключение: {conn}")
        print(f"5. Transport: {conn.transport}")
        
        # Получим канал
        with conn.channel() as channel:
            print(f"6. Канал: {channel}")
            
            # Проверим exchange
            from kombu import Exchange
            exchange = Exchange('celery', type='direct', channel=channel)
            print(f"7. Exchange: {exchange}")
            
            # Проверим binding
            print(f"\n8. Проверка bindings...")
            
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
