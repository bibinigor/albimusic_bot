#!/usr/bin/env python3
"""
ТЕСТОВЫЙ СКРИПТ ДЛЯ ПРОВЕРКИ МИНУСОВКИ/КАВЕРА/WAV
Создаёт реальные запросы и отслеживает их выполнение
"""

import sys
import time
import logging
sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync, init_db_pool_sync
from celery_tasks import generate_karaoke_task, generate_cover_task, generate_wav_task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация БД
init_db_pool_sync()

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def wait_for_task_completion(task_id, timeout=300):
    """Ждет завершения задачи в БД"""
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        result = execute_query_sync(
            "SELECT status, audio_url FROM generations WHERE task_id = %s",
            (task_id,)
        )
        
        if result:
            status = result[0][0]
            audio_url = result[0][1]
            
            if status == 'completed':
                logger.info(f"✅ Задача {task_id[:8]}... завершена успешно!")
                logger.info(f"   Audio URL: {audio_url[:100] if audio_url else 'None'}...")
                return True, audio_url
            elif status == 'error':
                logger.error(f"❌ Задача {task_id[:8]}... завершена с ошибкой!")
                logger.error(f"   Error: {audio_url[:200] if audio_url else 'None'}")
                return False, audio_url
        
        time.sleep(5)
        print(".", end="", flush=True)
    
    logger.error(f"⏰ Таймаут ожидания задачи {task_id[:8]}...")
    return False, None

def test_karaoke():
    """Тест минусовки"""
    print_header("ТЕСТ 1: МИНУСОВКА (KARAOKE)")
    
    # Находим последнюю успешно сгенерированную песню
    song = execute_query_sync("""
        SELECT task_id, user_id, suno_task_id, suno_audio_id 
        FROM generations 
        WHERE status = 'completed' 
        AND suno_task_id IS NOT NULL 
        AND suno_audio_id IS NOT NULL
        AND prompt NOT ILIKE '%минусовка%'
        AND prompt NOT ILIKE '%кавер%'
        AND prompt NOT ILIKE '%WAV%'
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    if not song or not song[0]:
        logger.error("❌ Не найдено подходящей песни для теста минусовки")
        return False
    
    original_task_id, user_id, suno_task_id, suno_audio_id = song[0]
    logger.info(f"📝 Оригинальная песня: {original_task_id[:8]}...")
    logger.info(f"   User: {user_id}")
    logger.info(f"   Suno Task ID: {suno_task_id}")
    logger.info(f"   Suno Audio ID: {suno_audio_id}")
    
    # Запускаем минусовку для версии 0
    logger.info("🚀 Запускаю генерацию минусовки...")
    celery_result = generate_karaoke_task.apply_async(
        args=[user_id, original_task_id, 0],  # version=0
        queue='generation'
    )
    
    task_id = celery_result.id
    logger.info(f"   Celery Task ID: {task_id}")
    
    # Ждем завершения
    success, audio_url = wait_for_task_completion(task_id, timeout=300)
    
    if success:
        logger.info("✅ МИНУСОВКА: ТЕСТ ПРОЙДЕН!")
        return True
    else:
        logger.error("❌ МИНУСОВКА: ТЕСТ ПРОВАЛЕН!")
        return False

def test_cover():
    """Тест кавера"""
    print_header("ТЕСТ 2: КАВЕР (COVER)")
    
    # Находим последнюю успешно сгенерированную песню
    song = execute_query_sync("""
        SELECT task_id, user_id 
        FROM generations 
        WHERE status = 'completed' 
        AND audio_url IS NOT NULL
        AND prompt NOT ILIKE '%минусовка%'
        AND prompt NOT ILIKE '%кавер%'
        AND prompt NOT ILIKE '%WAV%'
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    if not song or not song[0]:
        logger.error("❌ Не найдено подходящей песни для теста кавера")
        return False
    
    original_task_id, user_id = song[0]
    logger.info(f"📝 Оригинальная песня: {original_task_id[:8]}...")
    logger.info(f"   User: {user_id}")
    
    # Запускаем кавер
    new_style = "blues rock"
    logger.info(f"🚀 Запускаю генерацию кавера в стиле '{new_style}'...")
    celery_result = generate_cover_task.apply_async(
        args=[user_id, original_task_id, new_style, 0],  # version=0
        queue='generation'
    )
    
    task_id = celery_result.id
    logger.info(f"   Celery Task ID: {task_id}")
    
    # Ждем завершения
    success, audio_url = wait_for_task_completion(task_id, timeout=300)
    
    if success:
        logger.info("✅ КАВЕР: ТЕСТ ПРОЙДЕН!")
        return True
    else:
        logger.error("❌ КАВЕР: ТЕСТ ПРОВАЛЕН!")
        return False

def test_wav():
    """Тест WAV конвертации"""
    print_header("ТЕСТ 3: WAV КОНВЕРТАЦИЯ")
    
    # Находим последнюю успешно сгенерированную песню
    song = execute_query_sync("""
        SELECT task_id, user_id, suno_task_id, suno_audio_id 
        FROM generations 
        WHERE status = 'completed' 
        AND suno_task_id IS NOT NULL 
        AND suno_audio_id IS NOT NULL
        AND prompt NOT ILIKE '%минусовка%'
        AND prompt NOT ILIKE '%кавер%'
        AND prompt NOT ILIKE '%WAV%'
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    if not song or not song[0]:
        logger.error("❌ Не найдено подходящей песни для теста WAV")
        return False
    
    original_task_id, user_id, suno_task_id, suno_audio_id = song[0]
    logger.info(f"📝 Оригинальная песня: {original_task_id[:8]}...")
    logger.info(f"   User: {user_id}")
    logger.info(f"   Suno Task ID: {suno_task_id}")
    logger.info(f"   Suno Audio ID: {suno_audio_id}")
    
    # Запускаем WAV конвертацию
    logger.info("🚀 Запускаю конвертацию в WAV...")
    celery_result = generate_wav_task.apply_async(
        args=[user_id, original_task_id, 0],  # version=0
        queue='generation'
    )
    
    task_id = celery_result.id
    logger.info(f"   Celery Task ID: {task_id}")
    
    # Ждем завершения
    success, audio_url = wait_for_task_completion(task_id, timeout=300)
    
    if success:
        logger.info("✅ WAV: ТЕСТ ПРОЙДЕН!")
        return True
    else:
        logger.error("❌ WAV: ТЕСТ ПРОВАЛЕН!")
        return False

if __name__ == "__main__":
    print_header("ЗАПУСК ТЕСТОВ МИНУСОВКИ/КАВЕРА/WAV")
    
    results = {
        'karaoke': False,
        'cover': False,
        'wav': False
    }
    
    # Запускаем тесты
    try:
        results['karaoke'] = test_karaoke()
    except Exception as e:
        logger.error(f"❌ Ошибка теста минусовки: {e}")
    
    time.sleep(5)
    
    try:
        results['cover'] = test_cover()
    except Exception as e:
        logger.error(f"❌ Ошибка теста кавера: {e}")
    
    time.sleep(5)
    
    try:
        results['wav'] = test_wav()
    except Exception as e:
        logger.error(f"❌ Ошибка теста WAV: {e}")
    
    # Итоговый отчет
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    print(f"\n🎤 Минусовка: {'✅ ПРОЙДЕН' if results['karaoke'] else '❌ ПРОВАЛЕН'}")
    print(f"🎸 Кавер: {'✅ ПРОЙДЕН' if results['cover'] else '❌ ПРОВАЛЕН'}")
    print(f"🎵 WAV: {'✅ ПРОЙДЕН' if results['wav'] else '❌ ПРОВАЛЕН'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Функции работают корректно.")
    else:
        print("\n❌ ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ! Требуется дополнительная отладка.")
        print("\n💡 Проверьте логи Celery: journalctl -u celery-worker -n 200")
    
    print("\n" + "=" * 70)
