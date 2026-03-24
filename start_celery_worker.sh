#!/bin/bash
cd /root/albimusic-bot
source venv/bin/activate

# Генерируем уникальное имя воркера
WORKER_NAME="albimusic_$(hostname)_$(date +%s)"

# Запускаем Celery worker с уникальным именем
celery -A celery_config.celery_app worker \
    --queues=generation \
    --loglevel=info \
    --concurrency=1 \
    --hostname=$WORKER_NAME
