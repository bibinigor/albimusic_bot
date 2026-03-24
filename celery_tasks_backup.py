#!/usr/bin/env python3
import time
import logging
from celery import Celery
import config
from db_utils import execute_query_sync

# Инициализация пула БД
from db_utils import init_db_pool_sync
init_db_pool_sync()

import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация Celery
celery_app = Celery('albimusic_tasks', 
                    broker='redis://localhost:6379/1',  # Используем Redis как брокер
                    backend='redis://localhost:6379/2')  # Отдельная база для результатов

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    worker_send_task_events=False,
    task_send_sent_event=False
)