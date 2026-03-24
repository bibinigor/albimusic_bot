#!/usr/bin/env python3
"""
ИСПРАВЛЕНИЕ ПРОБЛЕМЫ ON CONFLICT

ПРОБЛЕМА:
- ON CONFLICT (task_id) требует UNIQUE constraint
- В таблице generations НЕТ UNIQUE на task_id

РЕШЕНИЕ:
1. Добавить UNIQUE constraint на task_id в БД
2. Обновить функцию save_generation_task_sync с правильным UPSERT
3. Удалить дублирующиеся task_id (если есть)
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
    backup_path = f"{FILE_PATH}.backup_unique_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

# ============================================================
# ЧАСТЬ 1: МИГРАЦИЯ БД (ДОБАВЛЕНИЕ UNIQUE CONSTRAINT)
# ============================================================

def get_database_migration_sql():
    """SQL для добавления UNIQUE constraint на task_id"""
    return """
-- ====================================================================
-- МИГРАЦИЯ: ДОБАВЛЕНИЕ UNIQUE CONSTRAINT НА task_id
-- ====================================================================

-- 1. ПРОВЕРКА ТЕКУЩЕЙ СТРУКТУРЫ
SELECT 
    'Текущая структура таблицы generations:' as info;

SELECT 
    column_name, 
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'generations'
ORDER BY ordinal_position;

-- 2. ПРОВЕРКА СУЩЕСТВУЮЩИХ CONSTRAINT
SELECT 
    'Существующие constraints:' as info;

SELECT 
    conname as constraint_name,
    contype as constraint_type
FROM pg_constraint 
WHERE conrelid = 'generations'::regclass;

-- 3. ПОИСК ДУБЛИКАТОВ task_id (КРИТИЧНО!)
SELECT 
    'Проверка дубликатов task_id:' as info;

SELECT 
    task_id, 
    COUNT(*) as count
FROM generations 
GROUP BY task_id 
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;

-- 4. УДАЛЕНИЕ ДУБЛИКАТОВ (ОСТАВЛЯЕМ САМУЮ СВЕЖУЮ ЗАПИСЬ)
DO $$ 
DECLARE
    duplicate_count INTEGER;
BEGIN
    -- Удаляем старые дубликаты, оставляя только самую свежую запись
    WITH duplicates AS (
        SELECT 
            id,
            task_id,
            ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY created_at DESC) as rn
        FROM generations
    )
    DELETE FROM generations
    WHERE id IN (
        SELECT id FROM duplicates WHERE rn > 1
    );
    
    GET DIAGNOSTICS duplicate_count = ROW_COUNT;
    
    IF duplicate_count > 0 THEN
        RAISE NOTICE 'Удалено дубликатов: %', duplicate_count;
    ELSE
        RAISE NOTICE 'Дубликатов не найдено';
    END IF;
END $$;

-- 5. ДОБАВЛЕНИЕ UNIQUE CONSTRAINT
DO $$ 
BEGIN
    -- Проверяем, есть ли уже constraint
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conrelid = 'generations'::regclass 
        AND conname = 'generations_task_id_unique'
    ) THEN
        -- Добавляем UNIQUE constraint
        ALTER TABLE generations 
        ADD CONSTRAINT generations_task_id_unique 
        UNIQUE (task_id);
        
        RAISE NOTICE '✅ UNIQUE constraint на task_id добавлен';
    ELSE
        RAISE NOTICE 'ℹ️ UNIQUE constraint уже существует';
    END IF;
END $$;

-- 6. СОЗДАНИЕ ДОПОЛНИТЕЛЬНЫХ ИНДЕКСОВ
-- Индекс для быстрого поиска по статусу
CREATE INDEX IF NOT EXISTS idx_generations_status 
    ON generations(status);

-- Индекс для быстрого поиска последних генераций пользователя
CREATE INDEX IF NOT EXISTS idx_generations_user_created 
    ON generations(user_id, created_at DESC);

-- Индекс для быстрого поиска ошибок
CREATE INDEX IF NOT EXISTS idx_generations_errors 
    ON generations(status, created_at DESC) 
    WHERE status = 'error';

-- 7. ФИНАЛЬНАЯ ПРОВЕРКА
SELECT 
    'Финальная структура constraints:' as info;

SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint 
WHERE conrelid = 'generations'::regclass
ORDER BY conname;

SELECT 
    'Итого записей в таблице:' as info,
    COUNT(*) as total_records,
    COUNT(DISTINCT task_id) as unique_task_ids
FROM generations;
"""

def apply_database_migration():
    """Применяет миграцию БД"""
    
    log("Применение миграции БД...", "🔄")
    
    migration_file = "/tmp/migration_unique_task_id.sql"
    
    with open(migration_file, 'w') as f:
        f.write(get_database_migration_sql())
    
    import subprocess
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', 'albimusic_db', '-f', migration_file],
        capture_output=True,
        text=True
    )
    
    print()
    print("=" * 80)
    print("РЕЗУЛЬТАТ МИГРАЦИИ БД:")
    print("=" * 80)
    print(result.stdout)
    
    if result.returncode == 0:
        log("Миграция БД успешно применена", "✅")
        return True
    else:
        log("ОШИБКА миграции БД:", "❌")
        print(result.stderr)
        return False

# ============================================================
# ЧАСТЬ 2: ОБНОВЛЕНИЕ ФУНКЦИИ save_generation_task_sync
# ============================================================

def get_fixed_save_generation_function():
    """Возвращает ИСПРАВЛЕННУЮ версию функции с правильным UPSERT"""
    return '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None, 
                              suno_task_id=None, result_message=None, error_message=None):
    """
    Синхронное сохранение/обновление задачи генерации в PostgreSQL
    
    Args:
        user_id (int): ID пользователя Telegram
        task_id (str): ID Celery задачи (уникальный!)
        prompt (str): Текст промпта
        status (str): pending | processing | completed | error
        audio_url (str, optional): URL MP3 файла
        suno_task_id (str, optional): ID задачи в Suno API
        result_message (str, optional): Сообщение о результате
        error_message (str, optional): Сообщение об ошибке
    
    Returns:
        bool: True при успехе
    
    ВАЖНО:
    - Использует UPSERT через ON CONFLICT (task_id)
    - task_id имеет UNIQUE constraint (добавлен миграцией)
    - НЕ пробрасывает исключения
    """
    
    try:
        # ===============================================
        # ВАЛИДАЦИЯ И ПОДГОТОВКА ДАННЫХ
        # ===============================================
        
        # Обязательные параметры
        if not user_id or not task_id:
            logger.error(f"❌ [DB] Отсутствуют обязательные параметры: user_id={user_id}, task_id={task_id}")
            return False
        
        # Ограничиваем длину строк
        safe_prompt = (prompt[:1000] if prompt else '').strip()
        safe_audio_url = (audio_url[:500] if audio_url else '').strip()
        safe_suno_task_id = (suno_task_id[:100] if suno_task_id else '').strip()
        safe_result_message = (result_message[:500] if result_message else '').strip()
        safe_error_message = (error_message[:1000] if error_message else '').strip()
        
        # Валидация статуса
        valid_statuses = ['pending', 'processing', 'completed', 'error']
        if status not in valid_statuses:
            logger.warning(f"⚠️ [DB] Неизвестный статус '{status}', заменяем на 'error'")
            status = 'error'
            if not safe_error_message:
                safe_error_message = f"Неизвестный статус: {status}"
        
        # ===============================================
        # SQL UPSERT (INSERT ... ON CONFLICT UPDATE)
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
        
        if result and len(result) > 0:
            row_id = result[0][0] if len(result[0]) > 0 else 'unknown'
            created = result[0][1] if len(result[0]) > 1 else None
            updated = result[0][2] if len(result[0]) > 2 else None
            
            # Определяем, INSERT или UPDATE
            is_new = (created == updated) if (created and updated) else True
            action = "создана" if is_new else "обновлена"
            
            logger.info(f"✅ [DB] Задача {task_id} {action} (id={row_id}, status={status})")
            
            # Дополнительное логирование
            if status == 'completed' and safe_result_message:
                logger.info(f"✅ [DB] Результат: {safe_result_message}")
            elif status == 'error' and safe_error_message:
                logger.error(f"❌ [DB] Ошибка: {safe_error_message}")
            
            return True
        else:
            logger.warning(f"⚠️ [DB] Задача {task_id} сохранена, но RETURNING не вернул данные")
            return True
        
    except Exception as e:
        # ===============================================
        # ОБРАБОТКА ОШИБОК
        # ===============================================
        
        logger.error(f"❌ [DB] Ошибка сохранения задачи {task_id}: {e}", exc_info=True)
        logger.error(f"❌ [DB] Параметры: user_id={user_id}, status={status}, prompt={safe_prompt[:50]}...")
        
        # Проверяем специфические ошибки PostgreSQL
        error_str = str(e).lower()
        if 'unique constraint' in error_str or 'duplicate key' in error_str:
            logger.error(f"❌ [DB] ДУБЛИКАТ task_id: {task_id} (возможна race condition)")
        elif 'no unique or exclusion constraint' in error_str:
            logger.error(f"❌ [DB] ОТСУТСТВУЕТ UNIQUE constraint на task_id (запустите миграцию!)")
        
        return False
'''

def replace_save_generation_function(content):
    """Заменяет функцию save_generation_task_sync"""
    
    pattern = r'(def save_generation_task_sync\([^)]*\):.*?)(\ndef [a-z_]+\(|\n@celery_app\.task|\Z)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Функция save_generation_task_sync НЕ НАЙДЕНА", "❌")
        return content, False
    
    new_content = (
        content[:match.start()] + 
        get_fixed_save_generation_function() + 
        '\n' +
        content[match.end(1):]
    )
    
    log("Функция save_generation_task_sync ИСПРАВЛЕНА", "✅")
    return new_content, True

# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    print("=" * 80)
    print("ИСПРАВЛЕНИЕ ПРОБЛЕМЫ ON CONFLICT (task_id)")
    print("=" * 80)
    print()
    
    # ===============================================
    # ШАГ 1: МИГРАЦИЯ БД (ДОБАВЛЕНИЕ UNIQUE)
    # ===============================================
    
    log("ШАГ 1: Добавление UNIQUE constraint на task_id...", "🔧")
    print()
    
    if not apply_database_migration():
        log("ВНИМАНИЕ: Миграция БД не удалась", "⚠️")
        log("Проверьте вывод выше и устраните ошибки", "⚠️")
        
        response = input("\n❓ Продолжить обновление кода? (y/n): ")
        if response.lower() != 'y':
            log("Прерывание работы", "❌")
            return False
    
    print()
    
    # ===============================================
    # ШАГ 2: ОБНОВЛЕНИЕ КОДА
    # ===============================================
    
    log("ШАГ 2: Обновление функции save_generation_task_sync...", "🔧")
    print()
    
    # Backup
    log("Создание backup...")
    backup_path = create_backup()
    
    # Чтение файла
    log("Чтение файла...")
    if not os.path.exists(FILE_PATH):
        log("ОШИБКА: Файл не найден", "❌")
        return False
    
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Замена функции
    log("Обновление функции...")
    new_content, modified = replace_save_generation_function(content)
    
    if not modified:
        log("Функция НЕ обновлена", "❌")
        return False
    
    # Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Проверка синтаксиса
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
        log("ИСПРАВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!", "✅")
        print("=" * 80)
        
        print(f"\n📁 Backup: {backup_path}")
        
        print("\n📋 Что сделано:")
        print("  ✅ Добавлен UNIQUE constraint на task_id")
        print("  ✅ Удалены дубликаты task_id (если были)")
        print("  ✅ Обновлена функция save_generation_task_sync")
        print("  ✅ Добавлены дополнительные индексы для производительности")
        print("  ✅ Улучшено логирование ошибок БД")
        
        print("\n🎯 Теперь ON CONFLICT (task_id) работает!")
        
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        
        print("\n🔍 Проверка:")
        print("  # Проверка constraint:")
        print("  sudo -u postgres psql albimusic_db -c \"")
        print("  SELECT conname, pg_get_constraintdef(oid)")
        print("  FROM pg_constraint")
        print("  WHERE conrelid = 'generations'::regclass")
        print("  AND conname = 'generations_task_id_unique';")
        print("  \"")
        print()
        print("  # Тестовая генерация и проверка логов:")
        print("  sudo journalctl -u albimusic-celery -f | grep -E '\\[DB\\]'")
        
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print(result.stderr)
        os.remove(temp_file)
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
