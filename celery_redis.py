#!/usr/bin/env python3
"""
Celery с Redis как брокером (работает стабильнее)
"""
import sys
import os

# Используем системный Python с нашим venv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv', 'lib', 'python3.10', 'site-packages'))

import time
import logging
from celery import Celery
import config
from db_utils import execute_query_sync

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация Celery с Redis как брокером И бэкендом
celery_app = Celery('albimusic_redis', 
                    broker='redis://localhost:6379/1',  # БД 1 для брокера
                    backend='redis://localhost:6379/2') # БД 2 для результатов

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_ignore_result=False,  # Включаем результаты для отладки
    broker_connection_retry_on_startup=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100
)

import requests

def save_generation_task_sync(user_id, task_id, prompt, audio_url, status='processing'):
    """Синхронное сохранение задачи генерации в БД"""
    try:
        execute_query_sync(
            "INSERT INTO generations (user_id, task_id, prompt, audio_url, status, created_at) "
            "VALUES (%s, %s, %s, %s, %s, NOW()) "
            "ON CONFLICT (task_id) DO UPDATE SET audio_url = EXCLUDED.audio_url, status = EXCLUDED.status",
            (user_id, task_id, prompt, audio_url, status)
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения задачи в БД: {e}")
        return False

@celery_app.task(bind=True, name='albimusic_redis.generate_music_task')
def generate_music_task(self, user_id, prompt):
    """Синхронная задача генерации инструментальной музыки"""
    task_id = self.request.id
    logger.info(f"🎵 ЗАДАЧА ПОЛУЧЕНА (Redis): user_id={user_id}, prompt={prompt}")
    
    try:
        # Тестовая задача - сразу возвращаем успех
        logger.info(f"✅ Тестовая задача выполнена для user_id={user_id}")
        
        # Сохраняем результат в БД
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url='http://test.com/audio.mp3',
            status='completed'
        )
        
        return {'status': 'success', 'audio_url': 'http://test.com/audio.mp3', 'task_id': task_id}
            
    except Exception as e:
        error_msg = f"Ошибка генерации музыки: {str(e)}"
        logger.error(error_msg)
        
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url='',
            status='error'
        )
        
        return {'status': 'error', 'message': str(e)}

@celery_app.task(bind=True, name='albimusic_redis.generate_song_task')
def generate_song_task(self, user_id, lyrics, style, custom_mode=False):
    """Синхронная задача генерации песни с текстом"""
    task_id = self.request.id
    logger.info(f"🔄 ЗАДАЧА ПОЛУЧЕНА (Redis): user_id={user_id}, style={style}, lyrics_len={len(lyrics) if lyrics else 0}")
    
    try:
        # Формируем prompt
        prompt = f"Стиль: {style}. Текст: {lyrics}"
        logger.info(f"📝 СФОРМИРОВАН PROMPT: {prompt[:200]}...")
        
        # Сохраняем задачу в БД
        save_success = save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url='',
            status='processing'
        )
        
        # Тестовая задача - сразу возвращаем успех
        logger.info(f"✅ Тестовая задача песни выполнена")
        
        # Обновляем запись в БД
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url='http://test.com/song.mp3',
            status='completed'
        )
        
        return {'status': 'success', 'audio_url': 'http://test.com/song.mp3', 'task_id': task_id}
            
    except Exception as e:
        error_msg = f"Ошибка генерации песни: {str(e)}"
        logger.error(error_msg)
        
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url='',
            status='error'
        )
        
        return {'status': 'error', 'message': str(e)}

# Тестовая задача
@celery_app.task
def test_task():
    logger.info("✅ Тестовая задача Redis выполнена")
    return "redis_test_ok"

if __name__ == '__main__':
    # Тест: запускаем воркер
    celery_app.worker_main(['worker', '--loglevel=info'])
