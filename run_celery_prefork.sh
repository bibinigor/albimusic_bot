#!/bin/bash
source venv/bin/activate
celery -A celery_tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --hostname=albimusic_prefork_worker \
    --queues=generation
