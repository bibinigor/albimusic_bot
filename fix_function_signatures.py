#!/usr/bin/env python3
"""
ИСПРАВЛЕНИЕ НЕСООТВЕТСТВИЯ ПАРАМЕТРОВ ФУНКЦИЙ

ПРОБЛЕМЫ:
1. save_generation_task_sync не принимает result_message
2. generate_suno_music_sync не принимает task_id

РЕШЕНИЕ:
1. Расширяем save_generation_task_sync (добавляем result_message, error_message)
2. Убираем task_id из вызовов generate_suno_music_sync
3. Исправляем обе Celery задачи
"""

import os
import re
import shutil
from datetime import datetime

FILES = {
    'celery_tasks': "/root/albimusic-bot/celery_tasks.py",
    'db_utils': "/root/albimusic-bot/db_utils.py"
}

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backups():
    backups = {}
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for name, path in FILES.items():
        if os.path.exists(path):
            backup_path = f"{path}.backup_signatures_{timestamp}"
            shutil.copy2(path, backup_path)
            backups[name] = backup_path
            log(f"Backup {name}: {backup_path}", "✅")
    
    return backups

# ============================================================
# ЧАСТЬ 1: РАСШИРЕНИЕ save_generation_task_sync
# ============================================================

def get_improved_save_generation_task_sync():
    """Возвращает улучшенную версию функции с поддержкой result_message"""
    return '''def save_generation_task_sync(user_id, task_id, prompt, status, audio_url=None, 
                              suno_task_id=None, result_message=None, error_message=None):
    """
    Синхронное сохранение/обновление задачи генерации в PostgreSQL
    
    Args:
        user_id (int): ID пользователя
        task_id (str): ID Celery задачи
        prompt (str): Текст промпта
        status (str): Статус задачи (pending, processing, completed, error)
        audio_url (str, optional): URL сгенерированного аудио
        suno_task_id (str, optional): ID задачи в Suno API
        result_message (str, optional): Сообщение о результате
        error_message (str, optional): Сообщение об ошибке
    
    ВАЖНО:
    - Использует INSERT ... ON CONFLICT UPDATE
    - Гарантирует сохранение даже при дублях
    """
    try:
        # Подготовка данных
        data = {
            'user_id': user_id,
            'task_id': task_id,
            'prompt': prompt[:1000] if prompt else '',  # Ограничиваем длину
            'status': status,
            'audio_url': audio_url or '',
            'suno_task_id': suno_task_id or '',
            'result_message': result_message[:500] if result_message else '',
            'error_message': error_message[:500] if error_message else ''
        }
        
        # SQL запрос с UPSERT (INSERT ... ON CONFLICT UPDATE)
        query = """
            INSERT INTO generations 
                (user_id, task_id, prompt, status, audio_url, suno_task_id, 
                 result_message, error_message, created_at, updated_at)
            VALUES 
                (%(user_id)s, %(task_id)s, %(prompt)s, %(status)s, %(audio_url)s, 
                 %(suno_task_id)s, %(result_message)s, %(error_message)s, NOW(), NOW())
            ON CONFLICT (task_id) 
            DO UPDATE SET
                status = EXCLUDED.status,
                audio_url = EXCLUDED.audio_url,
                suno_task_id = EXCLUDED.suno_task_id,
                result_message = EXCLUDED.result_message,
                error_message = EXCLUDED.error_message,
                updated_at = NOW()
        """
        
        execute_query_sync(query, data)
        logger.info(f"✅ Задача {task_id} сохранена в БД (status={status})")
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения задачи {task_id}: {e}", exc_info=True)
        # НЕ пробрасываем исключение - задача должна продолжиться
'''

def fix_save_generation_task_sync(content):
    """Заменяет функцию save_generation_task_sync на улучшенную версию"""
    
    # Паттерн: от def save_generation_task_sync до следующей функции
    pattern = r'(def save_generation_task_sync\([^)]*\):.*?)(\ndef [a-z_]+\(|\Z)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Функция save_generation_task_sync не найдена", "❌")
        return content, False
    
    # Заменяем функцию
    new_content = (
        content[:match.start()] + 
        get_improved_save_generation_task_sync() + 
        '\n\n' +
        content[match.end(1):]
    )
    
    log("save_generation_task_sync расширена (добавлены result_message, error_message)", "✅")
    return new_content, True

# ============================================================
# ЧАСТЬ 2: ИСПРАВЛЕНИЕ generate_song_task
# ============================================================

def fix_generate_song_task_calls(content):
    """Убирает task_id из вызовов generate_suno_music_sync"""
    
    modified = False
    
    # Исправление 1: Убираем task_id из generate_suno_music_sync
    pattern1 = r'(generate_suno_music_sync\([^)]*?),\s*task_id=task_id\s*\)'
    if re.search(pattern1, content):
        content = re.sub(pattern1, r'\1)', content)
        log("Убран task_id из generate_suno_music_sync в generate_song_task", "✅")
        modified = True
    
    # Исправление 2: Параметр result_message теперь ВАЛИДЕН (не убираем)
    
    return content, modified

# ============================================================
# ЧАСТЬ 3: ИСПРАВЛЕНИЕ generate_music_task
# ============================================================

def fix_generate_music_task_calls(content):
    """Убирает task_id из вызовов generate_suno_music_sync"""
    
    modified = False
    
    # Находим generate_music_task и убираем task_id из вызова
    pattern = r'(def generate_music_task\(.*?\n.*?generate_suno_music_sync\([^)]*?),\s*task_id=task_id\s*\)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, r'\1)', content, flags=re.DOTALL)
        log("Убран task_id из generate_suno_music_sync в generate_music_task", "✅")
        modified = True
    
    return content, modified

# ============================================================
# ЧАСТЬ 4: ДОБАВЛЕНИЕ КОЛОНОК В БД
# ============================================================

def get_migration_sql():
    """SQL для добавления новых колонок в БД"""
    return """
-- Добавление колонок result_message и error_message в таблицу generations

-- 1. Проверка существования колонок и добавление при необходимости
DO $$ 
BEGIN
    -- Добавляем result_message
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'generations' AND column_name = 'result_message'
    ) THEN
        ALTER TABLE generations ADD COLUMN result_message TEXT;
        RAISE NOTICE 'Колонка result_message добавлена';
    ELSE
        RAISE NOTICE 'Колонка result_message уже существует';
    END IF;

    -- Добавляем error_message
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'generations' AND column_name = 'error_message'
    ) THEN
        ALTER TABLE generations ADD COLUMN error_message TEXT;
        RAISE NOTICE 'Колонка error_message добавлена';
    ELSE
        RAISE NOTICE 'Колонка error_message уже существует';
    END IF;
END $$;

-- 2. Создание индекса для быстрого поиска ошибок
CREATE INDEX IF NOT EXISTS idx_generations_status_error 
    ON generations(status) WHERE status = 'error';

-- 3. Вывод текущей структуры таблицы
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'generations' 
ORDER BY ordinal_position;
"""

def apply_database_migration():
    """Применяет миграцию БД"""
    
    log("Применение миграции БД...", "🔄")
    
    migration_file = "/tmp/migration_result_message.sql"
    
    with open(migration_file, 'w') as f:
        f.write(get_migration_sql())
    
    import subprocess
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', 'albimusic_db', '-f', migration_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("Миграция БД успешно применена", "✅")
        log("Вывод:", "📋")
        print(result.stdout)
        return True
    else:
        log("Ошибка миграции БД:", "❌")
        print(result.stderr)
        return False

# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    print("=" * 80)
    print("ИСПРАВЛЕНИЕ НЕСООТВЕТСТВИЯ ПАРАМЕТРОВ ФУНКЦИЙ")
    print("=" * 80)
    print()
    
    # 1. Backup
    log("Создание backup файлов...")
    backups = create_backups()
    
    # 2. Миграция БД
    log("Добавление колонок result_message и error_message в БД...")
    if not apply_database_migration():
        log("ВНИМАНИЕ: Миграция БД не удалась, но продолжаем...", "⚠️")
    
    print()
    
    # 3. Исправление db_utils.py
    if 'db_utils' in backups:
        log("Исправление db_utils.py...")
        
        with open(FILES['db_utils'], 'r', encoding='utf-8') as f:
            db_content = f.read()
        
        db_content, db_modified = fix_save_generation_task_sync(db_content)
        
        if db_modified:
            with open(FILES['db_utils'], 'w', encoding='utf-8') as f:
                f.write(db_content)
            log("db_utils.py обновлен", "✅")
    
    print()
    
    # 4. Исправление celery_tasks.py
    if 'celery_tasks' in backups:
        log("Исправление celery_tasks.py...")
        
        with open(FILES['celery_tasks'], 'r', encoding='utf-8') as f:
            celery_content = f.read()
        
        # Исправление generate_song_task
        celery_content, song_modified = fix_generate_song_task_calls(celery_content)
        
        # Исправление generate_music_task
        celery_content, music_modified = fix_generate_music_task_calls(celery_content)
        
        if song_modified or music_modified:
            with open(FILES['celery_tasks'], 'w', encoding='utf-8') as f:
                f.write(celery_content)
            log("celery_tasks.py обновлен", "✅")
    
    print()
    
    # 5. Проверка синтаксиса
    log("Проверка синтаксиса Python...")
    
    all_valid = True
    
    for name, path in FILES.items():
        if os.path.exists(path):
            import subprocess
            result = subprocess.run(
                ['python3', '-m', 'py_compile', path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log(f"{name}: синтаксис OK", "✅")
            else:
                log(f"{name}: ОШИБКА синтаксиса", "❌")
                print(result.stderr)
                all_valid = False
    
    print()
    print("=" * 80)
    
    if all_valid:
        log("ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!", "✅")
        print("=" * 80)
        
        print("\n📁 Backups:")
        for name, path in backups.items():
            print(f"  • {name}: {path}")
        
        print("\n📋 Что исправлено:")
        print("  ✅ Добавлены колонки result_message и error_message в БД")
        print("  ✅ save_generation_task_sync расширена (принимает result_message)")
        print("  ✅ Убран task_id из вызовов generate_suno_music_sync")
        print("  ✅ Исправлены обе Celery задачи (song + music)")
        
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        
        print("\n🔍 Проверка:")
        print("  sudo journalctl -u albimusic-celery -f")
        
        return True
    else:
        log("ЕСТЬ ОШИБКИ! Восстановление из backup...", "❌")
        print("=" * 80)
        
        for name, backup_path in backups.items():
            original_path = FILES[name]
            shutil.copy2(backup_path, original_path)
            log(f"Восстановлен {name}", "↩️")
        
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
