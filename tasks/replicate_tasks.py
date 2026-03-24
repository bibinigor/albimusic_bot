#!/usr/bin/env python3
"""
Celery задачи для Replicate функций
"""

import logging
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_tasks import celery_app
from services.replicate_service import get_replicate_service
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)


# ==================== ВИДЕО ====================

@celery_app.task(name='tasks.generate_video_task', bind=True)
def generate_video_task(self, user_id: int, audio_url: str, duration: int, task_id: str = None):
    """
    Генерация видео из аудио через Runway Gen-3
    
    Args:
        user_id: ID пользователя
        audio_url: URL аудио файла
        duration: Длительность видео (5 или 10 секунд)
        task_id: ID задачи (опционально)
    """
    task_id = task_id or self.request.id
    cost_tokens = 2 if duration == 5 else 3
    
    try:
        logger.info(f"🎬 Начало генерации видео: user={user_id}, duration={duration}s, task={task_id}")
        
        # Обновляем статус в БД
        execute_query_sync(
            """INSERT INTO video_generations (user_id, task_id, audio_url, duration, status, cost_tokens)
               VALUES (%s, %s, %s, %s, 'processing', %s)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, audio_url, duration, cost_tokens)
        )
        
        # Генерируем видео через Replicate
        service = get_replicate_service()
        result = service.generate_video(audio_url, duration)
        
        if result['status'] == 'success':
            video_url = result['video_url']
            
            # Сохраняем результат
            execute_query_sync(
                """UPDATE video_generations 
                   SET video_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (video_url, task_id)
            )
            
            # Обновляем счетчик
            execute_query_sync(
                "UPDATE users SET videos_created = videos_created + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Видео готово: user={user_id}, task={task_id}")
            return {"status": "success", "video_url": video_url, "task_id": task_id}
        else:
            # Ошибка генерации - ВОЗВРАЩАЕМ ТОКЕНЫ
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE video_generations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (cost_tokens, user_id)
            )
            
            logger.error(f"❌ Ошибка генерации видео: {error_msg}. Токены возвращены: {cost_tokens}")
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": cost_tokens}
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в generate_video_task: {e}")
        
        # Сохраняем ошибку в БД и ВОЗВРАЩАЕМ ТОКЕНЫ
        try:
            execute_query_sync(
                """UPDATE video_generations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (str(e), task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (cost_tokens, user_id)
            )
            logger.info(f"💰 Токены возвращены: {cost_tokens} для user {user_id}")
        except Exception as refund_error:
            logger.error(f"❌ Ошибка возврата токенов: {refund_error}")
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": cost_tokens}


# ==================== ФОТО ====================

@celery_app.task(name='tasks.animate_photo_task', bind=True)
def animate_photo_task(self, user_id: int, image_url: str, task_id: str = None):
    """Оживление фото через Runway Motion Brush"""
    task_id = task_id or self.request.id
    
    try:
        logger.info(f"🎬 Оживление фото: user={user_id}, task={task_id}")
        
        execute_query_sync(
            """INSERT INTO photo_operations (user_id, task_id, operation_type, input_url, status, cost_tokens)
               VALUES (%s, %s, 'animate', %s, 'processing', 1)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, image_url)
        )
        
        service = get_replicate_service()
        result = service.animate_image(image_url)
        
        if result['status'] == 'success':
            video_url = result['video_url']
            
            execute_query_sync(
                """UPDATE photo_operations 
                   SET output_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (video_url, task_id)
            )
            
            execute_query_sync(
                "UPDATE users SET photos_processed = photos_processed + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Фото оживлено: user={user_id}, task={task_id}")
            return {"status": "success", "video_url": video_url, "task_id": task_id}
        else:
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE photo_operations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
            
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": 1}
            
    except Exception as e:
        logger.error(f"❌ Ошибка в animate_photo_task: {e}")
        
        # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
        except:
            pass
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": 1}


@celery_app.task(name='tasks.dance_person_task', bind=True)
def dance_person_task(self, user_id: int, person_image_url: str, dance_video_url: str, task_id: str = None):
    """Танец-персонаж через Animate Anyone"""
    task_id = task_id or self.request.id
    
    try:
        logger.info(f"💃 Создание танца: user={user_id}, task={task_id}")
        
        execute_query_sync(
            """INSERT INTO photo_operations (user_id, task_id, operation_type, input_url, input_url_2, status, cost_tokens)
               VALUES (%s, %s, 'dance', %s, %s, 'processing', 2)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, person_image_url, dance_video_url)
        )
        
        service = get_replicate_service()
        result = service.animate_person_dance(person_image_url, dance_video_url)
        
        if result['status'] == 'success':
            video_url = result['video_url']
            
            execute_query_sync(
                """UPDATE photo_operations 
                   SET output_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (video_url, task_id)
            )
            
            execute_query_sync(
                "UPDATE users SET photos_processed = photos_processed + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Танец создан: user={user_id}, task={task_id}")
            return {"status": "success", "video_url": video_url, "task_id": task_id}
        else:
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE photo_operations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 2 для user {user_id}")
            
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": 2}
            
    except Exception as e:
        logger.error(f"❌ Ошибка в dance_person_task: {e}")
        
        # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 2 для user {user_id}")
        except:
            pass
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": 2}


@celery_app.task(name='tasks.upscale_photo_task', bind=True)
def upscale_photo_task(self, user_id: int, image_url: str, task_id: str = None):
    """Апскейл фото 4x через Real-ESRGAN"""
    task_id = task_id or self.request.id
    
    try:
        logger.info(f"⬆️ Апскейл фото: user={user_id}, task={task_id}")
        
        execute_query_sync(
            """INSERT INTO photo_operations (user_id, task_id, operation_type, input_url, status, cost_tokens)
               VALUES (%s, %s, 'upscale', %s, 'processing', 1)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, image_url)
        )
        
        service = get_replicate_service()
        result = service.upscale_image(image_url, scale=4)
        
        if result['status'] == 'success':
            upscaled_url = result['image_url']
            
            execute_query_sync(
                """UPDATE photo_operations 
                   SET output_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (upscaled_url, task_id)
            )
            
            execute_query_sync(
                "UPDATE users SET photos_processed = photos_processed + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Апскейл выполнен: user={user_id}, task={task_id}")
            return {"status": "success", "image_url": upscaled_url, "task_id": task_id}
        else:
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE photo_operations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
            
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": 1}
            
    except Exception as e:
        logger.error(f"❌ Ошибка в upscale_photo_task: {e}")
        
        # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
        except:
            pass
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": 1}


@celery_app.task(name='tasks.remove_bg_task', bind=True)
def remove_bg_task(self, user_id: int, image_url: str, task_id: str = None):
    """Удаление фона через RMBG-1.4"""
    task_id = task_id or self.request.id
    
    try:
        logger.info(f"🗑️ Удаление фона: user={user_id}, task={task_id}")
        
        execute_query_sync(
            """INSERT INTO photo_operations (user_id, task_id, operation_type, input_url, status, cost_tokens)
               VALUES (%s, %s, 'remove_bg', %s, 'processing', 1)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, image_url)
        )
        
        service = get_replicate_service()
        result = service.remove_background(image_url)
        
        if result['status'] == 'success':
            result_url = result['image_url']
            
            execute_query_sync(
                """UPDATE photo_operations 
                   SET output_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (result_url, task_id)
            )
            
            execute_query_sync(
                "UPDATE users SET photos_processed = photos_processed + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Фон удален: user={user_id}, task={task_id}")
            return {"status": "success", "image_url": result_url, "task_id": task_id}
        else:
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE photo_operations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
            
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": 1}
            
    except Exception as e:
        logger.error(f"❌ Ошибка в remove_bg_task: {e}")
        
        # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
        except:
            pass
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": 1}


# ==================== ИЗОБРАЖЕНИЯ ====================

@celery_app.task(name='tasks.generate_image_task', bind=True)
def generate_image_task(self, user_id: int, prompt: str, aspect_ratio: str = "1:1", task_id: str = None):
    """
    Генерация изображения через FLUX.1 [dev]
    
    Args:
        user_id: ID пользователя
        prompt: Текстовое описание изображения
        aspect_ratio: Соотношение сторон ('1:1', '9:16', '16:9', '3:4', '4:3')
        task_id: ID задачи (опционально)
    """
    task_id = task_id or self.request.id
    
    try:
        logger.info(f"🎨 Начало генерации изображения: user={user_id}, aspect={aspect_ratio}, task={task_id}")
        
        # Обновляем статус в БД
        execute_query_sync(
            """INSERT INTO image_generations (user_id, task_id, prompt, aspect_ratio, status, cost_tokens)
               VALUES (%s, %s, %s, %s, 'processing', 1)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, prompt, aspect_ratio)
        )
        
        # Генерируем изображение через Replicate
        service = get_replicate_service()
        result = service.generate_image(prompt, aspect_ratio)
        
        if result['status'] == 'success':
            image_url = result['image_url']
            
            # Сохраняем результат
            execute_query_sync(
                """UPDATE image_generations 
                   SET image_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (image_url, task_id)
            )
            
            # Обновляем счетчик
            execute_query_sync(
                "UPDATE users SET images_generated = images_generated + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Изображение готово: user={user_id}, task={task_id}")
            return {"status": "success", "image_url": image_url, "task_id": task_id}
        else:
            # Ошибка генерации - ВОЗВРАЩАЕМ ТОКЕНЫ
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE image_generations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.error(f"❌ Ошибка генерации изображения: {error_msg}. Токены возвращены: 1")
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": 1}
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в generate_image_task: {e}")
        
        # Сохраняем ошибку в БД и ВОЗВРАЩАЕМ ТОКЕНЫ
        try:
            execute_query_sync(
                """UPDATE image_generations 
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (str(e), task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"💰 Токены возвращены: 1 для user {user_id}")
        except Exception as refund_error:
            logger.error(f"❌ Ошибка возврата токенов: {refund_error}")
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": 1}


@celery_app.task(name='tasks.generate_video_by_description_task', bind=True)
def generate_video_by_description_task(self, user_id: int, description: str, task_id: str = None):
    """
    Генерация видео по текстовому описанию через Runway Gen-3
    
    Args:
        user_id: ID пользователя
        description: Текстовое описание видео
        task_id: ID задачи (опционально)
    """
    task_id = task_id or self.request.id
    cost_tokens = 3
    
    try:
        logger.info(f"🎨 Начало генерации видео по описанию: user={user_id}, task={task_id}")
        
        # Обновляем статус в БД
        execute_query_sync(
            """INSERT INTO video_generations (user_id, task_id, prompt, status, cost_tokens)
               VALUES (%s, %s, %s, 'processing', %s)
               ON CONFLICT (task_id) DO UPDATE SET status = 'processing'""",
            (user_id, task_id, description, cost_tokens)
        )
        
        # Генерируем видео через Replicate
        service = get_replicate_service()
        result = service.generate_video_by_description(description)
        
        if result['status'] == 'success':
            video_url = result['video_url']
            
            # Сохраняем результат
            execute_query_sync(
                """UPDATE video_generations
                   SET video_url = %s, status = 'completed', completed_at = NOW()
                   WHERE task_id = %s""",
                (video_url, task_id)
            )
            
            # Обновляем счетчик
            execute_query_sync(
                "UPDATE users SET videos_created = videos_created + 1 WHERE user_id = %s",
                (user_id,)
            )
            
            logger.info(f"✅ Видео по описанию готово: user={user_id}, task={task_id}")
            return {"status": "success", "video_url": video_url, "task_id": task_id}
        else:
            # Ошибка генерации - ВОЗВРАЩАЕМ ТОКЕНЫ
            error_msg = result.get('error', 'Unknown error')
            execute_query_sync(
                """UPDATE video_generations
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (error_msg, task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (cost_tokens, user_id)
            )
            
            logger.error(f"❌ Ошибка генерации видео по описанию: {error_msg}. Токены возвращены: {cost_tokens}")
            return {"status": "error", "error": error_msg, "task_id": task_id, "refunded": cost_tokens}
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в generate_video_by_description_task: {e}")
        
        # Сохраняем ошибку в БД и ВОЗВРАЩАЕМ ТОКЕНЫ
        try:
            execute_query_sync(
                """UPDATE video_generations
                   SET status = 'failed', error_message = %s, completed_at = NOW()
                   WHERE task_id = %s""",
                (str(e), task_id)
            )
            
            # ИСПРАВЛЕНО: Возврат токенов при критической ошибке
            execute_query_sync(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (cost_tokens, user_id)
            )
            logger.info(f"💰 Токены возвращены: {cost_tokens} для user {user_id}")
        except Exception as refund_error:
            logger.error(f"❌ Ошибка возврата токенов: {refund_error}")
        
        return {"status": "error", "error": str(e), "task_id": task_id, "refunded": cost_tokens}


if __name__ == "__main__":
    # Тестирование задач
    logging.basicConfig(level=logging.INFO)
    print("✅ Replicate tasks модуль загружен")
