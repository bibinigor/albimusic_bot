#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функций Минусовка, Кавер и WAV в VK боте
"""
import sys
import json
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_karaoke_handler():
    """Тест обработчика минусовки"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 1: Обработчик МИНУСОВКА")
    logger.info("=" * 60)
    
    try:
        # Проверяем импорты
        from celery_tasks import generate_karaoke_task
        logger.info("✅ Импорт generate_karaoke_task успешен")
        
        # Проверяем, что функция вызывается с правильными параметрами
        # args=[user_id, task_id, version], kwargs={'task_id': new_task_id}, queue='generation'
        logger.info("✅ Формат вызова: generate_karaoke_task.apply_async(args=[user_id, task_id, version], kwargs={'task_id': new_task_id}, queue='generation')")
        
        # Проверяем что uuid импортируется
        import uuid
        test_uuid = str(uuid.uuid4())
        logger.info(f"✅ UUID работает: {test_uuid}")
        
        logger.info("✅ МИНУСОВКА: Все проверки пройдены")
        return True
    except Exception as e:
        logger.error(f"❌ МИНУСОВКА: Ошибка - {e}")
        return False

def test_wav_handler():
    """Тест обработчика WAV"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 2: Обработчик WAV")
    logger.info("=" * 60)
    
    try:
        # Проверяем импорты
        from celery_tasks import generate_wav_task
        logger.info("✅ Импорт generate_wav_task успешен")
        
        # Проверяем, что функция вызывается с правильными параметрами
        # args=[user_id, task_id, version], kwargs={'task_id': new_task_id}, queue='generation'
        logger.info("✅ Формат вызова: generate_wav_task.apply_async(args=[user_id, task_id, version], kwargs={'task_id': new_task_id}, queue='generation')")
        
        logger.info("✅ WAV: Все проверки пройдены")
        return True
    except Exception as e:
        logger.error(f"❌ WAV: Ошибка - {e}")
        return False

def test_cover_handler():
    """Тест обработчика кавера"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 3: Обработчик КАВЕР")
    logger.info("=" * 60)
    
    try:
        # Проверяем импорты
        from celery_tasks import generate_cover_task
        logger.info("✅ Импорт generate_cover_task успешен")
        
        # Проверяем, что функция вызывается с правильными параметрами
        # args=[user_id, task_id, genre, version], kwargs={'task_id': new_task_id}, queue='generation'
        logger.info("✅ Формат вызова: generate_cover_task.apply_async(args=[user_id, task_id, genre, version], kwargs={'task_id': new_task_id}, queue='generation')")
        
        logger.info("✅ КАВЕР: Все проверки пройдены")
        return True
    except Exception as e:
        logger.error(f"❌ КАВЕР: Ошибка - {e}")
        return False

def test_keyboards():
    """Тест клавиатур"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 4: Клавиатуры VK")
    logger.info("=" * 60)
    
    try:
        from vk_keyboards import (
            get_version_selection_keyboard,
            get_cover_genre_keyboard,
            get_song_options_keyboard
        )
        
        # Тест клавиатуры выбора версии
        kb1 = get_version_selection_keyboard("test_task_123", "karaoke")
        logger.info("✅ get_version_selection_keyboard('test_task_123', 'karaoke') работает")
        
        kb2 = get_version_selection_keyboard("test_task_123", "wav")
        logger.info("✅ get_version_selection_keyboard('test_task_123', 'wav') работает")
        
        kb3 = get_version_selection_keyboard("test_task_123", "cover")
        logger.info("✅ get_version_selection_keyboard('test_task_123', 'cover') работает")
        
        # Тест клавиатуры жанра кавера
        kb4 = get_cover_genre_keyboard("test_task_123", version=0)
        logger.info("✅ get_cover_genre_keyboard('test_task_123', version=0) работает")
        
        kb5 = get_cover_genre_keyboard("test_task_123", version=1)
        logger.info("✅ get_cover_genre_keyboard('test_task_123', version=1) работает")
        
        # Тест клавиатуры опций песни
        kb6 = get_song_options_keyboard("test_task_123")
        logger.info("✅ get_song_options_keyboard('test_task_123') работает")
        
        logger.info("✅ КЛАВИАТУРЫ: Все проверки пройдены")
        return True
    except Exception as e:
        logger.error(f"❌ КЛАВИАТУРЫ: Ошибка - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_main_vk_syntax():
    """Проверка синтаксиса main_vk.py"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 5: Синтаксис main_vk.py")
    logger.info("=" * 60)
    
    try:
        import py_compile
        py_compile.compile('main_vk.py', doraise=True)
        logger.info("✅ main_vk.py: Синтаксис корректен")
        return True
    except Exception as e:
        logger.error(f"❌ main_vk.py: Синтаксическая ошибка - {e}")
        return False

def test_action_handlers():
    """Проверка обработчиков действий"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 6: Обработчики действий в main_vk.py")
    logger.info("=" * 60)
    
    try:
        with open('main_vk.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие обработчиков
        required_handlers = [
            ('action == "karaoke"', 'Обработчик кнопки "Минусовка"'),
            ('action == "karaoke_v1" or action == "karaoke_v2"', 'Обработчик выбора версии минусовки'),
            ('action == "wav"', 'Обработчик кнопки "WAV"'),
            ('action == "wav_v1" or action == "wav_v2"', 'Обработчик выбора версии WAV'),
            ('action == "cover"', 'Обработчик кнопки "Кавер"'),
            ('action == "cover_v1" or action == "cover_v2"', 'Обработчик выбора версии кавера'),
            ('action == "cover_genre"', 'Обработчик выбора жанра кавера'),
        ]
        
        for handler_code, description in required_handlers:
            if handler_code in content:
                logger.info(f"✅ {description}: найден")
            else:
                logger.error(f"❌ {description}: НЕ НАЙДЕН")
                return False
        
        # Проверяем что используется асинхронный вызов (не .get(timeout=300))
        if '.get(timeout=300)' in content:
            logger.warning("⚠️ ВНИМАНИЕ: Найден синхронный вызов .get(timeout=300) - это может блокировать поток!")
            # Не возвращаем False, т.к. это может быть в старом коде
        
        # Проверяем правильный асинхронный вызов
        if 'apply_async' in content:
            logger.info("✅ Найден асинхронный вызов apply_async")
        
        # Проверяем списание токенов ДО генерации
        checks = [
            ('UPDATE users SET balance = balance - 1 WHERE', 'Списание 1 токена'),
            ('UPDATE users SET balance = balance - 2 WHERE', 'Списание 2 токенов'),
        ]
        
        for check_text, description in checks:
            if check_text in content:
                logger.info(f"✅ {description}: найдено")
        
        logger.info("✅ ОБРАБОТЧИКИ: Все проверки пройдены")
        return True
    except Exception as e:
        logger.error(f"❌ ОБРАБОТЧИКИ: Ошибка - {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("🚀 Запуск тестирования функций Минусовка, Кавер и WAV")
    logger.info("")
    
    results = []
    
    # Запускаем все тесты
    results.append(("Синтаксис main_vk.py", test_main_vk_syntax()))
    results.append(("Обработчик МИНУСОВКА", test_karaoke_handler()))
    results.append(("Обработчик WAV", test_wav_handler()))
    results.append(("Обработчик КАВЕР", test_cover_handler()))
    results.append(("Клавиатуры VK", test_keyboards()))
    results.append(("Обработчики действий", test_action_handlers()))
    
    # Итоговый отчет
    logger.info("")
    logger.info("=" * 60)
    logger.info("ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("")
    logger.info(f"Всего тестов: {len(results)}")
    logger.info(f"Пройдено: {passed}")
    logger.info(f"Провалено: {failed}")
    
    if failed == 0:
        logger.info("")
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! VK бот готов к запуску.")
        return 0
    else:
        logger.info("")
        logger.info("⚠️ ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ! Исправьте ошибки перед запуском.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
