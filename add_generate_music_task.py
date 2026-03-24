#!/usr/bin/env python3
"""
ДОБАВЛЕНИЕ НЕДОСТАЮЩЕЙ ФУНКЦИИ generate_music_task

Эта функция была утеряна при восстановлении из бэкапа.
"""

import os
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/celery_tasks.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_add_music_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_generate_music_task_code():
    """Возвращает код функции generate_music_task"""
    return '''

# ====================================================================
# CELERY ЗАДАЧА: ГЕНЕРАЦИЯ ИНСТРУМЕНТАЛЬНОЙ МУЗЫКИ
# ====================================================================

@celery_app.task(bind=True, name='generate_music_task')
def generate_music_task(self, user_id, prompt, task_id=None):
    """
    Celery задача для генерации ИНСТРУМЕНТАЛЬНОЙ музыки через Suno API
    
    Args:
        user_id (int): ID пользователя Telegram
        prompt (str): Описание стиля музыки
        task_id (str, optional): ID задачи (если не передан, используется self.request.id)
    
    Returns:
        dict: Результат генерации
    
    ВАЖНО:
    - НЕ использует finally блок (проблема преждевременного completed)
    - Статус 'processing' → ожидание 15 минут → 'completed' или 'error'
    - Явная обработка исключений
    """
    
    # Если task_id не передан, используем ID Celery задачи
    if not task_id:
        task_id = self.request.id
    
    logger.info(f"🎵 [MUSIC] Начало генерации инструментальной музыки для пользователя {user_id}")
    logger.info(f"🎵 [MUSIC] Task ID: {task_id}")
    logger.info(f"🎵 [MUSIC] Prompt: {prompt[:100]}...")
    
    # Инициализация переменных
    audio_url = None
    result_status = 'processing'
    result_message = 'Генерация начата'
    
    # Таймеры для мониторинга
    import time
    task_start = time.time()
    
    try:
        # ==========================================
        # 1. СОХРАНЕНИЕ ЗАДАЧИ СО СТАТУСОМ 'processing'
        # ==========================================
        logger.info(f"💾 [MUSIC] Сохранение задачи в БД (status=processing)...")
        
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=f"Инструментальная музыка: {prompt[:200]}",
            status='processing',
            audio_url=None
        )
        
        logger.info(f"✅ [MUSIC] Задача сохранена в БД")
        
        # ==========================================
        # 2. ВЫЗОВ SUNO API (БЛОКИРУЮЩИЙ, ДО 15 МИНУТ)
        # ==========================================
        logger.info(f"📡 [MUSIC] Отправка запроса в Suno API...")
        logger.info(f"📡 [MUSIC] Параметры: is_song=False, custom_mode=False")
        
        api_start = time.time()
        
        audio_url = generate_suno_music_sync(
            prompt=prompt,
            is_song=False,  # ✅ ИНСТРУМЕНТАЛЬНАЯ музыка
            custom_mode=False,
            user_id=user_id,
            task_id=task_id
        )
        
        api_duration = time.time() - api_start
        logger.info(f"⏱️ [MUSIC] Suno API ответил за {api_duration:.1f} сек")
        
        # ==========================================
        # 3. ПРОВЕРКА РЕЗУЛЬТАТА
        # ==========================================
        if not audio_url:
            logger.error(f"❌ [MUSIC] Suno API вернул пустой результат")
            result_status = 'error'
            result_message = 'Генерация не удалась (пустой результат от Suno API)'
        else:
            logger.info(f"✅ [MUSIC] Генерация успешна!")
            logger.info(f"✅ [MUSIC] Audio URL: {audio_url}")
            result_status = 'completed'  # ✅ ТОЛЬКО здесь статус меняется на completed!
            result_message = 'Генерация успешна'
        
        # ==========================================
        # 4. СОХРАНЕНИЕ ФИНАЛЬНОГО РЕЗУЛЬТАТА
        # ==========================================
        logger.info(f"💾 [MUSIC] Обновление задачи в БД (status={result_status})...")
        
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=f"Инструментальная музыка: {prompt[:200]}",
            status=result_status,
            audio_url=audio_url,
            result_message=result_message
        )
        
        total_duration = time.time() - task_start
        logger.info(f"✅ [MUSIC] Задача {task_id} завершена за {total_duration:.1f} сек")
        logger.info(f"✅ [MUSIC] Финальный статус: {result_status}")
        
        # ==========================================
        # 5. ВОЗВРАТ РЕЗУЛЬТАТА
        # ==========================================
        return {
            'status': result_status,
            'audio_url': audio_url,
            'message': result_message,
            'task_id': task_id,
            'duration': total_duration
        }
        
    except Exception as e:
        # ==========================================
        # ❌ ОБРАБОТКА ИСКЛЮЧЕНИЙ
        # ==========================================
        logger.error(f"❌ [MUSIC] Критическая ошибка в generate_music_task: {e}", exc_info=True)
        
        error_message = str(e)[:500]  # Ограничиваем длину
        error_duration = time.time() - task_start
        
        logger.error(f"❌ [MUSIC] Задача провалилась за {error_duration:.1f} сек")
        
        try:
            # Пытаемся сохранить ошибку в БД
            logger.info(f"💾 [MUSIC] Сохранение ошибки в БД...")
            
            save_generation_task_sync(
                user_id=user_id,
                task_id=task_id,
                prompt=f"Инструментальная музыка: {prompt[:200]}",
                status='error',
                audio_url=None,
                result_message=f"Ошибка: {error_message}"
            )
            
            logger.info(f"✅ [MUSIC] Ошибка сохранена в БД")
            
        except Exception as db_error:
            logger.error(f"❌ [MUSIC] Не удалось сохранить ошибку в БД: {db_error}")
        
        # Повторно пробрасываем исключение для Celery
        raise

'''

def add_function_after_generate_song_task(content):
    """Добавляет generate_music_task сразу после generate_song_task"""
    
    # Ищем конец функции generate_song_task
    import re
    
    # Паттерн: конец функции generate_song_task (до следующей функции или конца файла)
    pattern = r'(def generate_song_task\(.*?\n.*?)(\n\n@celery_app\.task|\n\ndef [a-z_]+\(|\n\n# =====|\Z)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Не найдена функция generate_song_task для вставки после нее", "❌")
        return content, False
    
    # Вставляем новую функцию после generate_song_task
    insert_pos = match.end(1)
    
    new_content = (
        content[:insert_pos] + 
        get_generate_music_task_code() + 
        content[insert_pos:]
    )
    
    log("Функция generate_music_task добавлена после generate_song_task", "✅")
    return new_content, True

def main():
    print("=" * 80)
    print("ДОБАВЛЕНИЕ ФУНКЦИИ generate_music_task")
    print("=" * 80)
    print()
    
    # 1. Проверка файла
    log("Проверка файла...")
    if not os.path.exists(FILE_PATH):
        log("ОШИБКА: Файл не найден", "❌")
        return False
    
    # 2. Проверка наличия функции
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def generate_music_task(' in content:
        log("Функция generate_music_task уже существует", "ℹ️")
        return True
    
    log("Функция generate_music_task НЕ найдена", "🔍")
    
    # 3. Backup
    log("Создание backup...")
    backup_path = create_backup()
    
    # 4. Добавление функции
    log("Добавление функции generate_music_task...")
    new_content, modified = add_function_after_generate_song_task(content)
    
    if not modified:
        log("Не удалось добавить функцию", "❌")
        return False
    
    # 5. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 6. Проверка синтаксиса
    log("Проверка синтаксиса Python...")
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'py_compile', temp_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("Синтаксис корректен", "✅")
        shutil.move(temp_file, FILE_PATH)
        
        print()
        print("=" * 80)
        log("ФУНКЦИЯ УСПЕШНО ДОБАВЛЕНА!", "✅")
        print("=" * 80)
        print(f"\n📁 Backup: {backup_path}")
        print("\n📋 Добавлено:")
        print("  ✅ Функция generate_music_task (инструментальная музыка)")
        print("  ✅ Параметры: user_id, prompt, task_id")
        print("  ✅ is_song=False (инструментальная)")
        print("  ✅ Без finally блока (правильная архитектура)")
        print("\n🎯 Отличия от generate_song_task:")
        print("  • Не требует lyrics (текста песни)")
        print("  • Не использует custom_mode")
        print("  • Только prompt (описание стиля)")
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        print("\n🔍 Проверка:")
        print("  # В Telegram боте попробуйте:")
        print("  1. Создать песню → Инструментальная музыка")
        print("  2. Введите описание (например: 'спокойная классическая музыка')")
        print("  3. Следите за логами:")
        print("     sudo journalctl -u albimusic-celery -f | grep MUSIC")
        
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print()
        print("=" * 80)
        print("ДЕТАЛИ ОШИБКИ:")
        print("=" * 80)
        print(result.stderr)
        
        os.remove(temp_file)
        log("Восстановление из backup...", "⚠️")
        shutil.copy2(backup_path, FILE_PATH)
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
