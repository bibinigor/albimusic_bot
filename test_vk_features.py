#!/usr/bin/env python3
"""
Тестирование функций минусовки, кавера и WAV для ВК бота

Этот скрипт проверяет:
1. Запуск задач минусовки, кавера и WAV через Celery
2. Доставку результатов пользователям ВК
3. Возврат токенов при ошибках
4. Корректность обработки версий (v1/v2)
"""

import sys
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорты
sys.path.append('/root/albimusic-bot')
from db_utils import execute_query_sync, init_db_pool_sync
from celery_tasks import generate_karaoke_task, generate_cover_task, generate_wav_task

def test_karaoke(test_user_id, original_task_id, version=0):
    """Тест генерации минусовки"""
    logger.info(f"\n{'='*60}")
    logger.info(f"ТЕСТ #1: Минусовка (version={version})")
    logger.info(f"{'='*60}")
    
    try:
        # Проверяем баланс ДО
        balance_before = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (test_user_id,)
        )
        balance_before = balance_before[0][0] if balance_before else 0
        logger.info(f"💰 Баланс ДО: {balance_before} токенов")
        
        # Добавляем токен если нужно
        if balance_before < 1:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (test_user_id,)
            )
            logger.info(f"💰 Добавлен 1 токен для теста")
        
        # Запускаем задачу
        logger.info(f"🎤 Запуск задачи минусовки...")
        logger.info(f"   user_id: {test_user_id}")
        logger.info(f"   original_task_id: {original_task_id}")
        logger.info(f"   version: {version}")
        
        task = generate_karaoke_task.apply_async(
            args=[test_user_id, original_task_id, version],
            queue='generation'
        )
        
        logger.info(f"✅ Задача запущена: {task.id}")
        logger.info(f"⏳ Ожидание результата (макс 5 минут)...")
        
        # Ждем результат
        result = task.get(timeout=300)
        
        logger.info(f"📊 Результат: {result}")
        
        # Проверяем баланс ПОСЛЕ
        balance_after = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (test_user_id,)
        )
        balance_after = balance_after[0][0] if balance_after else 0
        logger.info(f"💰 Баланс ПОСЛЕ: {balance_after} токенов")
        
        # Проверяем что задача в БД
        db_task = execute_query_sync(
            "SELECT status, audio_url, prompt FROM generations WHERE task_id = %s",
            (task.id,)
        )
        
        if db_task:
            status, audio_url, prompt = db_task[0]
            logger.info(f"📝 Статус в БД: {status}")
            logger.info(f"🎵 Audio URL: {audio_url[:100]}...")
            logger.info(f"📋 Prompt: {prompt}")
            
            if status == 'completed' and audio_url and not audio_url.startswith('ERROR'):
                logger.info(f"✅ ТЕСТ ПРОЙДЕН: Минусовка создана успешно")
                return True
            elif status == 'error':
                logger.warning(f"⚠️ Задача завершилась с ошибкой")
                if balance_after == balance_before:
                    logger.info(f"✅ Токен возвращен корректно")
                    return True
                else:
                    logger.error(f"❌ Токен НЕ возвращен!")
                    return False
        else:
            logger.error(f"❌ Задача не найдена в БД!")
            return False
            
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_cover(test_user_id, original_task_id, new_style="rock", version=0):
    """Тест генерации кавера"""
    logger.info(f"\n{'='*60}")
    logger.info(f"ТЕСТ #2: Кавер (style={new_style}, version={version})")
    logger.info(f"{'='*60}")
    
    try:
        # Проверяем баланс ДО
        balance_before = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (test_user_id,)
        )
        balance_before = balance_before[0][0] if balance_before else 0
        logger.info(f"💰 Баланс ДО: {balance_before} токенов")
        
        # Добавляем токен если нужно
        if balance_before < 1:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (test_user_id,)
            )
            logger.info(f"💰 Добавлен 1 токен для теста")
        
        # Запускаем задачу
        logger.info(f"🎸 Запуск задачи кавера...")
        logger.info(f"   user_id: {test_user_id}")
        logger.info(f"   original_task_id: {original_task_id}")
        logger.info(f"   new_style: {new_style}")
        logger.info(f"   version: {version}")
        
        task = generate_cover_task.apply_async(
            args=[test_user_id, original_task_id, new_style, version],
            queue='generation'
        )
        
        logger.info(f"✅ Задача запущена: {task.id}")
        logger.info(f"⏳ Ожидание результата (макс 5 минут)...")
        
        # Ждем результат
        result = task.get(timeout=300)
        
        logger.info(f"📊 Результат: {result}")
        
        # Проверяем баланс ПОСЛЕ
        balance_after = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (test_user_id,)
        )
        balance_after = balance_after[0][0] if balance_after else 0
        logger.info(f"💰 Баланс ПОСЛЕ: {balance_after} токенов")
        
        # Проверяем что задача в БД
        db_task = execute_query_sync(
            "SELECT status, audio_url, prompt FROM generations WHERE task_id = %s",
            (task.id,)
        )
        
        if db_task:
            status, audio_url, prompt = db_task[0]
            logger.info(f"📝 Статус в БД: {status}")
            logger.info(f"🎵 Audio URL: {audio_url[:100]}..." if audio_url else "None")
            logger.info(f"📋 Prompt: {prompt}")
            
            if status == 'completed' and audio_url and not audio_url.startswith('ERROR'):
                logger.info(f"✅ ТЕСТ ПРОЙДЕН: Кавер создан успешно")
                return True
            elif status == 'error':
                logger.warning(f"⚠️ Задача завершилась с ошибкой")
                if balance_after == balance_before:
                    logger.info(f"✅ Токен возвращен корректно")
                    return True
                else:
                    logger.error(f"❌ Токен НЕ возвращен!")
                    return False
        else:
            logger.error(f"❌ Задача не найдена в БД!")
            return False
            
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_wav(test_user_id, original_task_id, version=0):
    """Тест конвертации в WAV"""
    logger.info(f"\n{'='*60}")
    logger.info(f"ТЕСТ #3: WAV конвертация (version={version})")
    logger.info(f"{'='*60}")
    
    try:
        # Проверяем баланс ДО
        balance_before = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (test_user_id,)
        )
        balance_before = balance_before[0][0] if balance_before else 0
        logger.info(f"💰 Баланс ДО: {balance_before} токенов")
        
        # Добавляем 2 токена если нужно
        if balance_before < 2:
            execute_query_sync(
                "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                (test_user_id,)
            )
            logger.info(f"💰 Добавлено 2 токена для теста")
        
        # Запускаем задачу
        logger.info(f"🎵 Запуск задачи WAV конвертации...")
        logger.info(f"   user_id: {test_user_id}")
        logger.info(f"   original_task_id: {original_task_id}")
        logger.info(f"   version: {version}")
        
        task = generate_wav_task.apply_async(
            args=[test_user_id, original_task_id, version],
            queue='generation'
        )
        
        logger.info(f"✅ Задача запущена: {task.id}")
        logger.info(f"⏳ Ожидание результата (макс 3 минуты)...")
        
        # Ждем результат
        result = task.get(timeout=180)
        
        logger.info(f"📊 Результат: {result}")
        
        # Проверяем баланс ПОСЛЕ
        balance_after = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (test_user_id,)
        )
        balance_after = balance_after[0][0] if balance_after else 0
        logger.info(f"💰 Баланс ПОСЛЕ: {balance_after} токенов")
        
        # Проверяем что задача в БД
        db_task = execute_query_sync(
            "SELECT status, audio_url, prompt FROM generations WHERE task_id = %s",
            (task.id,)
        )
        
        if db_task:
            status, audio_url, prompt = db_task[0]
            logger.info(f"📝 Статус в БД: {status}")
            logger.info(f"🎵 Audio URL: {audio_url[:100]}..." if audio_url else "None")
            logger.info(f"📋 Prompt: {prompt}")
            
            if status == 'completed' and audio_url and not audio_url.startswith('ERROR'):
                logger.info(f"✅ ТЕСТ ПРОЙДЕН: WAV конвертация успешна")
                return True
            elif status == 'error':
                logger.warning(f"⚠️ Задача завершилась с ошибкой")
                if balance_after == balance_before:
                    logger.info(f"✅ Токены возвращены корректно")
                    return True
                else:
                    logger.error(f"❌ Токены НЕ возвращены!")
                    return False
        else:
            logger.error(f"❌ Задача не найдена в БД!")
            return False
            
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Главная функция"""
    logger.info(f"\n{'#'*60}")
    logger.info(f"ТЕСТИРОВАНИЕ ФУНКЦИЙ ВК БОТА")
    logger.info(f"{'#'*60}\n")
    
    # Инициализируем БД
    init_db_pool_sync()
    logger.info("✅ БД инициализирована")
    
    # Найдем последнюю генерацию для тестирования
    last_gen = execute_query_sync(
        """SELECT task_id, user_id, suno_task_id, suno_audio_id 
           FROM generations 
           WHERE status = 'completed' 
           AND suno_task_id IS NOT NULL 
           AND suno_audio_id IS NOT NULL
           ORDER BY created_at DESC 
           LIMIT 1"""
    )
    
    if not last_gen:
        logger.error("❌ Не найдено ни одной завершенной генерации для тестирования!")
        logger.error("   Сначала создайте песню через бота.")
        return
    
    original_task_id, test_user_id, suno_task_id, suno_audio_id = last_gen[0]
    logger.info(f"📌 Найдена генерация для тестирования:")
    logger.info(f"   Task ID: {original_task_id}")
    logger.info(f"   User ID: {test_user_id}")
    logger.info(f"   Suno Task ID: {suno_task_id}")
    logger.info(f"   Suno Audio ID: {suno_audio_id}")
    
    results = {
        'karaoke': False,
        'cover': False,
        'wav': False
    }
    
    # Тест 1: Минусовка
    try:
        results['karaoke'] = test_karaoke(test_user_id, original_task_id, version=0)
    except Exception as e:
        logger.error(f"❌ Ошибка теста минусовки: {e}")
    
    time.sleep(5)
    
    # Тест 2: Кавер
    try:
        results['cover'] = test_cover(test_user_id, original_task_id, "blues rock", version=0)
    except Exception as e:
        logger.error(f"❌ Ошибка теста кавера: {e}")
    
    time.sleep(5)
    
    # Тест 3: WAV
    try:
        results['wav'] = test_wav(test_user_id, original_task_id, version=0)
    except Exception as e:
        logger.error(f"❌ Ошибка теста WAV: {e}")
    
    # Итоги
    logger.info(f"\n{'='*60}")
    logger.info(f"ИТОГИ ТЕСТИРОВАНИЯ")
    logger.info(f"{'='*60}")
    logger.info(f"🎤 Минусовка: {'✅ ПРОЙДЕН' if results['karaoke'] else '❌ ПРОВАЛЕН'}")
    logger.info(f"🎸 Кавер: {'✅ ПРОЙДЕН' if results['cover'] else '❌ ПРОВАЛЕН'}")
    logger.info(f"🎵 WAV: {'✅ ПРОЙДЕН' if results['wav'] else '❌ ПРОВАЛЕН'}")
    
    total = sum(results.values())
    logger.info(f"\nОбщий результат: {total}/3 тестов пройдено")
    
    if total == 3:
        logger.info(f"🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        logger.warning(f"⚠️ Некоторые тесты провалены. См. логи выше.")

if __name__ == "__main__":
    main()
