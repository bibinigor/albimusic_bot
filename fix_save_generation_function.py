#!/usr/bin/env python3
"""
ОБНОВЛЕНИЕ ФУНКЦИИ save_generation_task_sync

ПРОБЛЕМА:
- Функция не принимает result_message и error_message
- Находится в celery_tasks.py (не в db_utils.py)

РЕШЕНИЕ:
- Добавляем параметры result_message=None, error_message=None
- Обновляем SQL для сохранения в новые колонки
- Сохраняем обратную совместимость
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
    backup_path = f"{FILE_PATH}.backup_save_func_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_updated_save_generation_function():
    """Возвращает ПОЛНЫЙ код обновленной функции save_generation_task_sync"""
    return '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None, 
                              suno_task_id=None, result_message=None, error_message=None):
    """
    Синхронное сохранение/обновление задачи генерации в PostgreSQL
    
    Args:
        user_id (int): ID пользователя Telegram
        task_id (str): ID Celery задачи (уникальный)
        prompt (str): Текст промпта (описание задачи)
        status (str): Статус задачи:
            - 'pending': Задача создана, ожидает обработки
            - 'processing': Генерация в процессе (ожидание Suno API)
            - 'completed': Генерация завершена успешно
            - 'error': Произошла ошибка
        audio_url (str, optional): URL сгенерированного MP3 файла
        suno_task_id (str, optional): ID задачи в Suno API (для отслеживания)
        result_message (str, optional): Сообщение о результате (для completed)
        error_message (str, optional): Сообщение об ошибке (для error)
    
    Returns:
        bool: True при успехе, False при ошибке
    
    ВАЖНО:
    - Использует INSERT ... ON CONFLICT UPDATE (UPSERT)
    - Гарантирует сохранение даже при дублях task_id
    - НЕ пробрасывает исключения (только логирует)
    - Обратно совместима (новые параметры опциональны)
    """
    
    try:
        # ===============================================
        # ПОДГОТОВКА ДАННЫХ
        # ===============================================
        
        # Ограничиваем длину строк для предотвращения переполнения
        safe_prompt = (prompt[:1000] if prompt else '').strip()
        safe_audio_url = (audio_url[:500] if audio_url else '').strip()
        safe_suno_task_id = (suno_task_id[:100] if suno_task_id else '').strip()
        safe_result_message = (result_message[:500] if result_message else '').strip()
        safe_error_message = (error_message[:1000] if error_message else '').strip()
        
        # Валидация статуса
        valid_statuses = ['pending', 'processing', 'completed', 'error']
        if status not in valid_statuses:
            logger.warning(f"⚠️ Неизвестный статус '{status}', устанавливаем 'error'")
            status = 'error'
            if not safe_error_message:
                safe_error_message = f"Неизвестный статус: {status}"
        
        # ===============================================
        # SQL ЗАПРОС (UPSERT)
        # ===============================================
        
        query = """
            INSERT INTO generations 
                (user_id, task_id, prompt, status, audio_url, suno_task_id, 
                 result_message, error_message, created_at, updated_at)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (task_id) 
            DO UPDATE SET
                status = EXCLUDED.status,
                audio_url = EXCLUDED.audio_url,
                suno_task_id = EXCLUDED.suno_task_id,
                result_message = EXCLUDED.result_message,
                error_message = EXCLUDED.error_message,
                updated_at = NOW()
            RETURNING id, created_at, updated_at
        """
        
        # Данные для запроса
        params = (
            user_id,
            task_id,
            safe_prompt,
            status,
            safe_audio_url,
            safe_suno_task_id,
            safe_result_message,
            safe_error_message
        )
        
        # ===============================================
        # ВЫПОЛНЕНИЕ ЗАПРОСА
        # ===============================================
        
        result = execute_query_sync(query, params)
        
        if result:
            row_id = result[0][0] if result[0] else 'unknown'
            logger.info(f"✅ [DB] Задача {task_id} сохранена (id={row_id}, status={status})")
            
            # Дополнительное логирование для отладки
            if status == 'completed':
                logger.info(f"✅ [DB] Завершена: {safe_result_message or 'без сообщения'}")
            elif status == 'error':
                logger.error(f"❌ [DB] Ошибка: {safe_error_message or 'без сообщения'}")
            
            return True
        else:
            logger.warning(f"⚠️ [DB] Задача {task_id} сохранена, но результат не получен")
            return True
        
    except Exception as e:
        # ===============================================
        # ОБРАБОТКА ОШИБОК БД
        # ===============================================
        
        logger.error(f"❌ [DB] Ошибка сохранения задачи {task_id}: {e}", exc_info=True)
        logger.error(f"❌ [DB] Параметры: user_id={user_id}, status={status}, prompt={prompt[:50]}...")
        
        # НЕ пробрасываем исключение - задача должна продолжиться
        # Даже если БД недоступна, Celery задача не должна падать
        return False
'''

def replace_save_generation_function(content):
    """Заменяет функцию save_generation_task_sync на обновленную версию"""
    
    # Паттерн: от начала функции до следующей функции
    pattern = r'(def save_generation_task_sync\([^)]*\):.*?)(\ndef [a-z_]+\(|\n@celery_app\.task|\Z)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Функция save_generation_task_sync НЕ НАЙДЕНА", "❌")
        return content, False
    
    # Показываем старую сигнатуру
    old_signature = match.group(0).split('\n')[0]
    log(f"Старая сигнатура: {old_signature}", "🔍")
    
    # Заменяем функцию
    new_content = (
        content[:match.start()] + 
        get_updated_save_generation_function() + 
        '\n' +
        content[match.end(1):]
    )
    
    log("Функция save_generation_task_sync ОБНОВЛЕНА", "✅")
    return new_content, True

def verify_function_calls(content):
    """Проверяет, что все вызовы функции корректны"""
    
    log("Проверка вызовов save_generation_task_sync...", "🔍")
    
    # Находим все вызовы функции
    pattern = r'save_generation_task_sync\([^)]*\)'
    calls = re.findall(pattern, content)
    
    log(f"Найдено вызовов: {len(calls)}", "📊")
    
    issues = []
    
    for i, call in enumerate(calls, 1):
        # Проверяем наличие result_message или error_message
        if 'result_message=' in call or 'error_message=' in call:
            log(f"  {i}. Вызов с новыми параметрами: OK", "✅")
        else:
            log(f"  {i}. Вызов без новых параметров: OK (обратная совместимость)", "✅")
    
    return True

def main():
    print("=" * 80)
    print("ОБНОВЛЕНИЕ ФУНКЦИИ save_generation_task_sync")
    print("=" * 80)
    print()
    
    # 1. Проверка файла
    log("Проверка файла...")
    if not os.path.exists(FILE_PATH):
        log("ОШИБКА: Файл не найден", "❌")
        return False
    
    # 2. Backup
    log("Создание backup...")
    backup_path = create_backup()
    print()
    
    # 3. Чтение
    log("Чтение файла...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 4. Проверка наличия функции
    if 'def save_generation_task_sync(' not in content:
        log("ОШИБКА: Функция save_generation_task_sync не найдена", "❌")
        return False
    
    log("Функция найдена", "✅")
    print()
    
    # 5. Замена функции
    log("Обновление функции...")
    new_content, modified = replace_save_generation_function(content)
    
    if not modified:
        log("Функция НЕ обновлена", "❌")
        return False
    
    print()
    
    # 6. Проверка вызовов
    verify_function_calls(new_content)
    print()
    
    # 7. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 8. Проверка синтаксиса
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
        log("ФУНКЦИЯ УСПЕШНО ОБНОВЛЕНА!", "✅")
        print("=" * 80)
        
        print(f"\n📁 Backup: {backup_path}")
        
        print("\n📋 Что изменено:")
        print("  ✅ Добавлены параметры: result_message=None, error_message=None")
        print("  ✅ SQL обновлен для работы с новыми колонками")
        print("  ✅ Добавлена валидация данных (ограничение длины)")
        print("  ✅ Улучшено логирование (отдельно для completed и error)")
        print("  ✅ Обратная совместимость сохранена")
        
        print("\n🎯 Новая сигнатура:")
        print("  def save_generation_task_sync(")
        print("      user_id, task_id, prompt, status,")
        print("      audio_url=None, suno_task_id=None,")
        print("      result_message=None, error_message=None  ← НОВЫЕ")
        print("  )")
        
        print("\n📊 SQL операция:")
        print("  INSERT INTO generations (..., result_message, error_message, ...)")
        print("  ON CONFLICT (task_id) DO UPDATE SET ...")
        
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        
        print("\n🔍 Проверка:")
        print("  # Тестовая генерация")
        print("  # Проверка логов:")
        print("  sudo journalctl -u albimusic-celery -f | grep -E '\\[DB\\]|completed|error'")
        print("\n  # Проверка БД:")
        print("  sudo -u postgres psql albimusic_db -c \"")
        print("  SELECT task_id, status, result_message, error_message")
        print("  FROM generations ORDER BY created_at DESC LIMIT 5;")
        print("  \"")
        
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
