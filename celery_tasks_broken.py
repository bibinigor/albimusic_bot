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

# Инициализация Celery с RabbitMQ
celery_app = Celery('albimusic_tasks', 
                    broker='amqp://albimusic:StrongPassword123!@localhost:5672//',
                    backend='redis://localhost:6379/0')

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_default_queue='celery',
    task_ignore_result=True,
    worker_hijack_root_logger=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
)

def save_generation_task_sync(user_id, task_id, prompt, status='pending', audio_url=''):
    try:
        # Сначала проверяем существует ли задача
        from db_utils import execute_query_sync
        existing = execute_query_sync(
            'SELECT id FROM generations WHERE task_id = %s',
            (task_id,)
        )
        
        if existing:
            # Обновляем существующую запись
            execute_query_sync(
                'UPDATE generations SET prompt = %s, audio_url = %s, status = %s, completed_at = CASE WHEN %s IN (%s, %s) THEN NOW() ELSE NULL END WHERE task_id = %s',
                (prompt, audio_url, status, status, 'completed', 'error', task_id)
            )
        else:
            # Создаем новую запись
            execute_query_sync(
                'INSERT INTO generations (user_id, task_id, prompt, audio_url, status, created_at) VALUES (%s, %s, %s, %s, %s, NOW())',
                (user_id, task_id, prompt, audio_url, status)
            )
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения задачи {task_id}: {e}")
        return False

def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None):
    """Синхронная версия генерации музыки через Suno API"""
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if is_song:
        if custom_mode:
            data = {
                "prompt": prompt,
                "customMode": True,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
        else:
            data = {
                "prompt": prompt,
                "customMode": False,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
    else:
        data = {
            "prompt": prompt,
            "customMode": False,
            "instrumental": True,
            "model": "V5",
            "callBackUrl": "https://example.com/callback"
        }
    
    try:
        # ДЕБАГ: логируем что отправляем
        logger.info(f"🚀 SUNO DEBUG: Отправляем prompt в Suno")
        logger.info(f"   Prompt (первые 200 символов): {prompt[:200]}")
        logger.info(f"   Prompt length: {len(prompt)}")
        logger.info(f"   Is song: {is_song}, Custom mode: {custom_mode}")
        
        # Создаем задачу генерации
        # ДЕТАЛЬНЫЙ ДЕБАГ Suno API
        logger.info("=" * 50)
        logger.info(f"🚀 SUNO API REQUEST DETAILS:")
        logger.info(f"   Prompt полный: {prompt}")
        logger.info(f"   Prompt длина: {len(prompt)}")
        logger.info(f"   Prompt первые 300 символов: {prompt[:300]}")
        logger.info(f"   Prompt последние 100 символов: {prompt[-100:]}")
        logger.info(f"   Data: {data}")
        logger.info("=" * 50)
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            task_id = result['data']['taskId']
            logger.info(f"🎵 Задача Suno создана: {task_id} для пользователя {user_id}")
            
            # Ожидаем завершения генерации
            for i in range(30):  # 30 попыток по 10 секунд = 5 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['data']['status']
                    logger.info(f"📊 Статус задачи Suno {task_id}: {status} (попытка {i+1})")
                    
                    if status == 'SUCCESS':
                        audio_url = status_data['data']['audioUrl']
                        logger.info(f"✅ Генерация Suno завершена для пользователя {user_id}")
                        return audio_url
                    elif status in ['FAILED', 'ERROR']:
                        logger.error(f"❌ Ошибка генерации Suno для пользователя {user_id}: {status}")
                        return None
                else:
                    logger.warning(f"⚠️ Не удалось получить статус задачи {task_id}")
            
            logger.error(f"❌ Таймаут генерации для пользователя {user_id}")
            return None
        else:
            logger.error(f"❌ Ошибка создания задачи Suno: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение при генерации Suno: {e}")
        return None

@celery_app.task(bind=True, name='celery_tasks.generate_music_task')
def generate_music_task(self, user_id, prompt):
    """Синхронная задача генерации музыки"""
    task_id = self.request.id
    logger.info(f"🔄 Запуск генерации музыки для пользователя {user_id}, задача {task_id}")
    
    try:
        # Сохраняем задачу в БД
        save_success = save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            status='processing'
        )
        
        if not save_success:
            logger.error(f"❌ Не удалось сохранить задачу {task_id} в БД")
            return {'status': 'error', 'message': 'Ошибка сохранения задачи'}
        
        # Реальная генерация через Suno API
        audio_url = generate_suno_music_sync(
            prompt=prompt,
            is_song=False,
            custom_mode=False,
            user_id=user_id
        )
        
        # Если генерация не удалась, возвращаем ошибку
        if not audio_url:
            logger.error(f"❌ Suno API вернул пустой результат для пользователя {user_id}")
            save_generation_task_sync(
                user_id=user_id,
                task_id=task_id,
                prompt=prompt,
                status='error'
            )
            return {'status': 'error', 'message': 'Генерация не удалась'}
        
        # Сохраняем результат в БД
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url=audio_url,
            status='completed'
        )
        
        logger.info(f"✅ Задача {task_id} сохранена в БД")
        return {'status': 'success', 'user_id': user_id, 'audio_url': audio_url, 'task_id': task_id}
        
    except Exception as e:
        logger.error(f"❌ Ошибка в задаче generate_music_task: {e}")
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            status='error'
        )
        return {'status': 'error', 'message': str(e)}

@celery_app.task(bind=True, name='celery_tasks.generate_song_task')
def generate_song_task(self, user_id, lyrics, style, custom_mode=False):
    """Синхронная задача генерации песни с текстом"""
    task_id = self.request.id
    logger.info(f"🔄 Запуск генерации песни для пользователя {user_id}, задача {task_id}")
    
    try:
        # Формируем prompt для Suno: стиль + текст
        prompt = f"Стиль: {style}. Текст: {lyrics}"
        
        # Сохраняем задачу в БД
        save_success = save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            status='processing'
        )
        
        if not save_success:
            logger.error(f"❌ Не удалось сохранить задачу {task_id} в БД")
            return {'status': 'error', 'message': 'Ошибка сохранения задачи'}
        
        # Реальная генерация через Suno API
        audio_url = generate_suno_music_sync(
            prompt=prompt,
            is_song=True,
            custom_mode=custom_mode,
            user_id=user_id
        )
        
        # Если генерация не удалась, возвращаем ошибку
        if not audio_url:
            logger.error(f"❌ Suno API вернул пустой результат для пользователя {user_id}")
            save_generation_task_sync(
                user_id=user_id,
                task_id=task_id,
                prompt=prompt,
                status='error'
            )
            return {'status': 'error', 'message': 'Генерация не удалась'}
        
        # Сохраняем результат в БД
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            audio_url=audio_url,
            status='completed'
        )
        
        logger.info(f"✅ Задача {task_id} сохранена в БД")
        return {'status': 'success', 'user_id': user_id, 'audio_url': audio_url, 'task_id': task_id}
        
    except Exception as e:
        logger.error(f"❌ Ошибка в задаче generate_song_task: {e}")
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            status='error'
        )
        return {'status': 'error', 'message': str(e)}

@celery_app.task
def test_task():
    """Тестовая задача"""
    logger.info("=" * 50)
    logger.info(f"🎵 CELERY TASK RECEIVED PARAMETERS:")
    logger.info(f"   user_id: {user_id}")
    logger.info(f"   lyrics (first 50): {lyrics[:50] if lyrics else "None"}")
    logger.info(f"   lyrics length: {len(lyrics) if lyrics else 0}")
    logger.info(f"   style: {style}")
    logger.info(f"   custom_mode: {custom_mode}")
    logger.info("=" * 50)
    logger.info("✅ Тестовая задача выполнена")
    return {'status': 'success', 'message': 'Test task completed'}
