#!/usr/bin/env python3
"""
ИСПРАВЛЕНИЕ finally БЛОКОВ В CELERY ЗАДАЧАХ

ПРОБЛЕМА:
- finally выполняется ВСЕГДА (даже при успехе)
- Статус 'completed' может быть установлен ДО реального завершения

РЕШЕНИЕ:
- Убрать finally
- Явно сохранять статус в try и except
- Использовать промежуточные статусы
"""

import os
import re
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/celery_tasks.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_finally_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_correct_generate_song_task():
    """Возвращает ПРАВИЛЬНУЮ версию generate_song_task БЕЗ finally"""
    return '''@celery_app.task(bind=True, name='generate_song_task')
def generate_song_task(self, user_id, lyrics, style, custom_mode=False, task_id=None):
    """
    Celery задача генерации песни через Suno API
    
    ВАЖНО: НЕ используем finally - он выполняется ВСЕГДА
    """
    
    # Если task_id не передан, используем ID самой Celery задачи
    if not task_id:
        task_id = self.request.id
    
    logger.info(f"🎤 Начало генерации ПЕСНИ для пользователя {user_id} (task_id: {task_id})")
    
    # Инициализация переменных
    audio_url = None
    result_status = 'processing'  # ✅ Начальный статус
    result_message = 'Генерация начата'
    
    try:
        # 1. СОХРАНЯЕМ ЗАДАЧУ КАК 'processing' (НЕ 'pending'!)
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=f"Стиль: {style if style else 'Не указан'}. Текст: {lyrics[:100]}...",
            status='processing',  # ✅ Явно указываем статус
            audio_url=None
        )
        
        # 2. ГЕНЕРАЦИЯ (БЛОКИРУЮЩАЯ, ДО 15 МИНУТ)
        logger.info(f"📡 Отправка запроса в Suno API...")
        
        audio_url = generate_suno_music_sync(
            prompt=f"Стиль: {style}. Текст: {lyrics}",
            is_song=True,
            custom_mode=custom_mode,
            user_id=user_id,
            task_id=task_id
        )
        
        # 3. ПРОВЕРКА РЕЗУЛЬТАТА
        if not audio_url:
            logger.error(f"❌ Suno API вернул пустой результат для {user_id}")
            result_status = 'error'
            result_message = 'Генерация не удалась (пустой результат)'
        else:
            logger.info(f"✅ Генерация завершена успешно для {user_id}: {audio_url}")
            result_status = 'completed'  # ✅ ТОЛЬКО здесь!
            result_message = 'Генерация успешна'
        
        # 4. СОХРАНЕНИЕ ФИНАЛЬНОГО РЕЗУЛЬТАТА
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=f"Стиль: {style if style else 'Не указан'}. Текст: {lyrics[:100]}...",
            status=result_status,
            audio_url=audio_url,
            result_message=result_message
        )
        
        logger.info(f"✅ Задача {task_id} завершена со статусом: {result_status}")
        
        return {
            'status': result_status,
            'audio_url': audio_url,
            'message': result_message,
            'task_id': task_id
        }
        
    except Exception as e:
        # ❌ ОБРАБОТКА ИСКЛЮЧЕНИЙ
        logger.error(f"❌ Критическая ошибка в generate_song_task для {user_id}: {e}", exc_info=True)
        
        error_message = str(e)[:500]  # Ограничиваем длину
        
        try:
            # Пытаемся сохранить ошибку в БД
            save_generation_task_sync(
                user_id=user_id,
                task_id=task_id,
                prompt=f"Стиль: {style if style else 'Не указан'}. Текст: {lyrics[:100]}...",
                status='error',
                audio_url=None,
                result_message=f"Ошибка: {error_message}"
            )
        except Exception as db_error:
            logger.error(f"❌ Не удалось сохранить ошибку в БД: {db_error}")
        
        # Повторно пробрасываем исключение для Celery
        raise
'''

def get_correct_generate_music_task():
    """Возвращает ПРАВИЛЬНУЮ версию generate_music_task БЕЗ finally"""
    return '''@celery_app.task(bind=True, name='generate_music_task')
def generate_music_task(self, user_id, prompt, task_id=None):
    """
    Celery задача генерации инструментальной музыки через Suno API
    
    ВАЖНО: НЕ используем finally - он выполняется ВСЕГДА
    """
    
    # Если task_id не передан, используем ID самой Celery задачи
    if not task_id:
        task_id = self.request.id
    
    logger.info(f"🎵 Начало генерации МУЗЫКИ для пользователя {user_id} (task_id: {task_id})")
    
    # Инициализация переменных
    audio_url = None
    result_status = 'processing'  # ✅ Начальный статус
    result_message = 'Генерация начата'
    
    try:
        # 1. СОХРАНЯЕМ ЗАДАЧУ КАК 'processing'
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=f"Музыка: {prompt[:200]}...",
            status='processing',
            audio_url=None
        )
        
        # 2. ГЕНЕРАЦИЯ (БЛОКИРУЮЩАЯ, ДО 15 МИНУТ)
        logger.info(f"📡 Отправка запроса в Suno API...")
        
        audio_url = generate_suno_music_sync(
            prompt=prompt,
            is_song=False,  # Инструментальная музыка
            custom_mode=False,
            user_id=user_id,
            task_id=task_id
        )
        
        # 3. ПРОВЕРКА РЕЗУЛЬТАТА
        if not audio_url:
            logger.error(f"❌ Suno API вернул пустой результат для {user_id}")
            result_status = 'error'
            result_message = 'Генерация не удалась (пустой результат)'
        else:
            logger.info(f"✅ Генерация завершена успешно для {user_id}: {audio_url}")
            result_status = 'completed'  # ✅ ТОЛЬКО здесь!
            result_message = 'Генерация успешна'
        
        # 4. СОХРАНЕНИЕ ФИНАЛЬНОГО РЕЗУЛЬТАТА
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=f"Музыка: {prompt[:200]}...",
            status=result_status,
            audio_url=audio_url,
            result_message=result_message
        )
        
        logger.info(f"✅ Задача {task_id} завершена со статусом: {result_status}")
        
        return {
            'status': result_status,
            'audio_url': audio_url,
            'message': result_message,
            'task_id': task_id
        }
        
    except Exception as e:
        # ❌ ОБРАБОТКА ИСКЛЮЧЕНИЙ
        logger.error(f"❌ Критическая ошибка в generate_music_task для {user_id}: {e}", exc_info=True)
        
        error_message = str(e)[:500]
        
        try:
            save_generation_task_sync(
                user_id=user_id,
                task_id=task_id,
                prompt=f"Музыка: {prompt[:200]}...",
                status='error',
                audio_url=None,
                result_message=f"Ошибка: {error_message}"
            )
        except Exception as db_error:
            logger.error(f"❌ Не удалось сохранить ошибку в БД: {db_error}")
        
        raise
'''

def replace_function(content, func_name, new_func_code):
    """Заменяет функцию целиком (от декоратора до следующей функции)"""
    
    # Паттерн: от @celery_app.task до следующего @
    pattern = rf'(@celery_app\.task.*?def {func_name}\(.*?\n)(.*?)(?=\n@celery_app\.task|\n@app\.|\nif __name__|$)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log(f"Функция {func_name} не найдена", "❌")
        return content, False
    
    # Заменяем функцию
    new_content = content[:match.start()] + new_func_code + content[match.end():]
    
    log(f"Функция {func_name} заменена", "✅")
    return new_content, True

def main():
    print("=" * 80)
    print("УДАЛЕНИЕ finally БЛОКОВ ИЗ CELERY ЗАДАЧ")
    print("=" * 80)
    print()
    
    # 1. Проверка
    log("Проверка файла...")
    if not os.path.exists(FILE_PATH):
        log("ОШИБКА: Файл не найден", "❌")
        return False
    
    # 2. Backup
    log("Создание backup...")
    backup_path = create_backup()
    
    # 3. Чтение
    log("Чтение файла...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 4. Проверка наличия finally
    finally_count = content.count('finally:')
    log(f"Найдено finally блоков: {finally_count}", "🔍")
    
    if finally_count == 0:
        log("finally блоки уже удалены", "ℹ️")
        return True
    
    # 5. Замена generate_song_task
    log("Замена generate_song_task...")
    content, modified1 = replace_function(
        content,
        'generate_song_task',
        get_correct_generate_song_task()
    )
    
    # 6. Замена generate_music_task
    log("Замена generate_music_task...")
    content, modified2 = replace_function(
        content,
        'generate_music_task',
        get_correct_generate_music_task()
    )
    
    if not (modified1 or modified2):
        log("Изменений не требуется", "ℹ️")
        return True
    
    # 7. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 8. Проверка синтаксиса
    log("Проверка синтаксиса...")
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
        log("ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!", "✅")
        print("=" * 80)
        print(f"\n📁 Backup: {backup_path}")
        print("\n📋 Что исправлено:")
        print("  ✅ Удалены finally блоки из generate_song_task")
        print("  ✅ Удалены finally блоки из generate_music_task")
        print("  ✅ Статус 'processing' устанавливается в начале")
        print("  ✅ Статус 'completed' ТОЛЬКО после реального завершения")
        print("  ✅ Статус 'error' при исключениях")
        print("\n🎯 Логика:")
        print("  1. Задача создается со статусом 'processing'")
        print("  2. generate_suno_music_sync ждет до 15 минут")
        print("  3. Статус обновляется ТОЛЬКО после завершения")
        print("  4. При ошибках статус явно устанавливается в 'error'")
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        print("\n🔍 Проверка:")
        print("  sudo journalctl -u albimusic-celery -f")
        
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
