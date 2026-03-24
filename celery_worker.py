#!/usr/bin/env python3
"""
Запуск Celery worker с прямым управлением пулом PostgreSQL
"""

import os
import sys
import logging
import signal

# ВАЖНО: monkey patch ДОЛЖЕН быть самым первым
import eventlet
print("🚀 Applying eventlet monkey patch...")
eventlet.monkey_patch()
print("✅ Eventlet monkey patch applied.")

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

# Теперь импортируем модули
from celery_tasks import celery_app
from db_utils import initialize_pool_for_worker, shutdown_pool_for_worker

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"📡 Received signal {signum}. Shutting down worker and DB pool.")
    shutdown_pool_for_worker()
    sys.exit(0)

def run_celery_worker():
    """Главная функция для запуска worker'а"""
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Инициализация пула перед запуском worker'а
    try:
        initialize_pool_for_worker()
        logger.info("✅ DB pool initialized for worker process.")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not initialize DB pool. Worker will not start. Error: {e}")
        return

    # Запускаем Celery worker
    logger.info("🚀 Starting Celery worker...")
    
    try:
        celery_app.start(argv=[
            'worker',
            '--loglevel=info',
            '--pool=eventlet', 
            '--concurrency=10',
            '--hostname=albimusic_eventlet_worker',
            '--queues=generation'
        ])
    except Exception as e:
        logger.error(f"❌ Error executing Celery worker: {e}")
    finally:
        # Гарантируем закрытие пула при любом завершении
        shutdown_pool_for_worker()

if __name__ == '__main__':
    run_celery_worker()
