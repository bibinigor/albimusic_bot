#!/usr/bin/env python3
import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Заменяем RabbitMQ на Redis как брокер
# Было: broker='amqp://albimusic:StrongPassword123!@localhost:5672//'
# Стало: broker='redis://localhost:6379/1'

old_broker = "broker='amqp://albimusic:StrongPassword123!@localhost:5672//'"
new_broker = "broker='redis://localhost:6379/1'  # Используем Redis как брокер"

content = content.replace(old_broker, new_broker)

# Также обновляем backend (используем другую базу Redis)
old_backend = "backend='redis://localhost:6379/0'"
new_backend = "backend='redis://localhost:6379/2'  # Отдельная база для результатов"

content = content.replace(old_backend, new_backend)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Конфигурация Celery обновлена: RabbitMQ → Redis")
print("   Брокер: redis://localhost:6379/1")
print("   Бэкенд: redis://localhost:6379/2")
