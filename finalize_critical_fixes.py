#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
ФИНАЛИЗАЦИЯ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ AlBi-music Bot
═══════════════════════════════════════════════════════════════════════

ЗАДАЧИ:
1. ✅ Добавить вызов validate_audio_url в generate_suno_music_sync
2. ✅ Добавить использование translate_style_to_english
3. ✅ Исправить миграцию БД (albimusic_bot вместо albimusic_db)
4. ✅ Создать тестовый скрипт проверки

ВЕРСИЯ: 1.0
АВТОР: Claude (Anthropic)
ДАТА: 2026-01-15
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import re
import subprocess
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════

CELERY_FILE = "/root/albimusic-bot/celery_tasks.py"
BACKUP_DIR = "/root/albimusic-bot/backups_finalize"
LOG_FILE = f"/tmp/finalize_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
CORRECT_DB_NAME = "albimusic_bot"  # ✅ ПРАВИЛЬНОЕ ИМЯ БД

# ═══════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════

class Logger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.start_time = datetime.now()
    
    def log(self, msg, level="INFO", symbol="•"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {msg}"
        print(f"{symbol} {msg}")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    
    def info(self, msg): self.log(msg, "INFO", "•")
    def success(self, msg): self.log(msg, "SUCCESS", "✅")
    def warning(self, msg): self.log(msg, "WARNING", "⚠️")
    def error(self, msg): self.log(msg, "ERROR", "❌")
    
    def section(self, title):
        separator = "═" * 80
        print(f"\n{separator}\n  {title}\n{separator}\n")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{separator}\n  {title}\n{separator}\n\n")

logger = Logger(LOG_FILE)

def create_backup_dir():
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    logger.success(f"Директория бэкапов: {BACKUP_DIR}")

def backup_file(file_path):
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        return None
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(file_path)
    backup_path = os.path.join(BACKUP_DIR, f"{filename}.backup_{timestamp}")
    shutil.copy2(file_path, backup_path)
    logger.success(f"Backup: {backup_path}")
    return backup_path

def check_syntax(file_path):
    """Проверка синтаксиса Python"""
    result = subprocess.run(
        ['python3', '-m', 'py_compile', file_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.success(f"Синтаксис OK: {os.path.basename(file_path)}")
        return True
    else:
        logger.error(f"Ошибка синтаксиса: {os.path.basename(file_path)}")
        logger.error(result.stderr)
        return False

def restore_from_backup(file_path, backup_path):
    """Восстановление из бэкапа"""
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        logger.warning(f"Восстановлено из backup: {file_path}")
        return True
    return False

# ═══════════════════════════════════════════════════════════════════════
# ЗАДАЧА 1: ДОБАВИТЬ ВЫЗОВ validate_audio_url
# ═══════════════════════════════════════════════════════════════════════

def add_validation_call(content):
    """
    Добавить проверку MP3 перед return audio_url
    
    БЫЛО:
        audio_url = audio_data[0].get('audioUrl')
        logger.info(...)
        return audio_url
    
    СТАНЕТ:
        audio_url = audio_data[0].get('audioUrl')
        logger.info(...)
        
        # Проверка валидности MP3
        if not validate_audio_url(audio_url, request_id):
            return None
        
        return audio_url
    """
    
    # Точный паттерн из файла
    pattern = r'''(audio_url = audio_data\[0\]\.get\('audioUrl'\)\s+logger\.info\(f"XXXLATEXDISPLAYXXX2XXXLATEXDISPLAYXXX ✅ SUNO GENERATION COMPLETED:"\)\s+logger\.info\(f"XXXLATEXDISPLAYXXX3XXXLATEXDISPLAYXXX    • Audio URL: {audio_url}"\)\s+logger\.info\(f"XXXLATEXDISPLAYXXX4XXXLATEXDISPLAYXXX    • Total time: {time\.time\(\) - start_time:.2f}s"\)\s+)(return audio_url)'''
    
    replacement = r'''\1
                # 🔍 ПРОВЕРКА ВАЛИДНОСТИ MP3
                logger.info(f"[{request_id}] 🔍 Валидация MP3...")
                if not validate_audio_url(audio_url, request_id):
                    logger.error(f"[{request_id}] ❌ MP3 не прошел валидацию")
                    return None
                
                \2'''
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        logger.success("Вызов validate_audio_url добавлен")
        return new_content, True
    else:
        logger.warning("Паттерн для добавления вызова не найден")
        
        # Альтернативный паттерн (упрощенный)
        alt_pattern = r'''(logger\.info\(f"XXXLATEXDISPLAYXXX5XXXLATEXDISPLAYXXX    • Total time:.*?"\)\s+)(return audio_url)'''
        
        alt_replacement = r'''\1
                # 🔍 ПРОВЕРКА ВАЛИДНОСТИ MP3
                logger.info(f"[{request_id}] 🔍 Валидация MP3...")
                if not validate_audio_url(audio_url, request_id):
                    logger.error(f"[{request_id}] ❌ MP3 не прошел валидацию")
                    return None
                
                \2'''
        
        new_content = re.sub(alt_pattern, alt_replacement, content, flags=re.DOTALL)
        
        if new_content != content:
            logger.success("Вызов validate_audio_url добавлен (альтернативный метод)")
            return new_content, True
        else:
            logger.error("Не удалось найти место для вставки")
            return content, False

# ═══════════════════════════════════════════════════════════════════════
# ЗАДАЧА 2: ИСПОЛЬЗОВАНИЕ translate_style_to_english
# ═══════════════════════════════════════════════════════════════════════

def add_style_translation(content):
    """
    Добавить перевод стиля перед созданием headers
    
    Ищем место после логирования параметров:
        logger.info(f"[{request_id}]    • User ID: {user_id}")
        
        headers = {
    """
    
    # Точный паттерн
    pattern = r'''(logger\.info\(f"XXXLATEXDISPLAYXXX6XXXLATEXDISPLAYXXX    • User ID: {user_id}"\)\s+)(headers = {)'''
    
    replacement = r'''\1
    # ═══════════════════════════════════════════════════════════════
    # ПЕРЕВОД СТИЛЯ НА АНГЛИЙСКИЙ (если содержит русские буквы)
    # ═══════════════════════════════════════════════════════════════
    
    if style:
        original_style = style
        style = translate_style_to_english(style)
        
        if style != original_style:
            logger.info(f"[{request_id}] 🔄 СТИЛЬ ПЕРЕВЕДЕН:")
            logger.info(f"[{request_id}]    • Оригинал: {original_style}")
            logger.info(f"[{request_id}]    • Перевод: {style}")
    
    \2'''
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        logger.success("Перевод стиля добавлен")
        return new_content, True
    else:
        logger.warning("Паттерн для перевода стиля не найден")
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# ЗАДАЧА 3: МИГРАЦИЯ БД
# ═══════════════════════════════════════════════════════════════════════

def create_db_migration_script():
    """Создание SQL скрипта миграции с правильным именем БД"""
    
    migration_sql = f"""
-- ═══════════════════════════════════════════════════════════════════════
-- МИГРАЦИЯ: Добавление колонки generation_duration_seconds
-- ═══════════════════════════════════════════════════════════════════════
-- База данных: {CORRECT_DB_NAME}
-- Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ═══════════════════════════════════════════════════════════════════════

DO $$ 
BEGIN
    -- Проверяем существование колонки
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'generations' 
        AND column_name = 'generation_duration_seconds'
    ) THEN
        -- Добавляем колонку
        ALTER TABLE generations 
        ADD COLUMN generation_duration_seconds INTEGER;
        
        RAISE NOTICE '✅ Колонка generation_duration_seconds добавлена';
        
        -- Создаем индекс для аналитики
        CREATE INDEX IF NOT EXISTS idx_generations_duration 
        ON generations(generation_duration_seconds) 
        WHERE generation_duration_seconds IS NOT NULL;
        
        RAISE NOTICE '✅ Индекс idx_generations_duration создан';
    ELSE
        RAISE NOTICE 'ℹ️  Колонка generation_duration_seconds уже существует';
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════════
-- ПРОВЕРКА РЕЗУЛЬТАТА
-- ═══════════════════════════════════════════════════════════════════════

SELECT 
    column_name AS "Колонка",
    data_type AS "Тип",
    is_nullable AS "NULL?"
FROM information_schema.columns
WHERE table_name = 'generations'
AND column_name = 'generation_duration_seconds';
"""
    
    migration_file = "/tmp/add_duration_column_fixed.sql"
    
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(migration_sql)
    
    logger.info(f"SQL миграция создана: {migration_file}")
    
    return migration_file

def apply_db_migration():
    """Применение миграции БД с правильным именем"""
    
    logger.section("МИГРАЦИЯ БАЗЫ ДАННЫХ")
    
    migration_file = create_db_migration_script()
    
    logger.info(f"Применение миграции к БД '{CORRECT_DB_NAME}'...")
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', CORRECT_DB_NAME, '-f', migration_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.success("Миграция БД успешно применена")
        
        # Выводим результат
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            if line.strip():
                logger.info(f"  {line}")
        
        return True
    else:
        logger.error("Ошибка применения миграции БД:")
        logger.error(result.stderr)
        return False

# ═══════════════════════════════════════════════════════════════════════
# ЗАДАЧА 4: ТЕСТОВЫЙ СКРИПТ ПРОВЕРКИ
# ═══════════════════════════════════════════════════════════════════════

def create_verification_script():
    """Создание скрипта проверки всех исправлений"""
    
    verification_script = '''#!/usr/bin/env python3
"""
СКРИПТ ПРОВЕРКИ ИСПРАВЛЕНИЙ
"""

import re
import sys

CELERY_FILE = "/root/albimusic-bot/celery_tasks.py"

def check(name, condition, success_msg, fail_msg):
    """Проверка условия"""
    if condition:
        print(f"✅ {name}: {success_msg}")
        return True
    else:
        print(f"❌ {name}: {fail_msg}")
        return False

def main():
    print("\\n" + "═" * 80)
    print("  ПРОВЕРКА ИСПРАВЛЕНИЙ AlBi-music Bot")
    print("═" * 80 + "\\n")
    
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # 1. Функция validate_audio_url определена
    checks.append(check(
        "Функция validate_audio_url",
        'def validate_audio_url(url, request_id):' in content,
        "Определена",
        "НЕ найдена"
    ))
    
    # 2. Функция validate_audio_url вызывается
    checks.append(check(
        "Вызов validate_audio_url",
        'validate_audio_url(audio_url, request_id)' in content,
        "Присутствует",
        "НЕ найден"
    ))
    
    # 3. Только один MUSIC_STYLE_TRANSLATIONS
    count = len(re.findall(r'MUSIC_STYLE_TRANSLATIONS\\s*=\\s*{', content))
    checks.append(check(
        "MUSIC_STYLE_TRANSLATIONS",
        count == 1,
        f"Единственный словарь (без дубликатов)",
        f"Найдено {count} определений"
    ))
    
    # 4. Защита от race conditions
    checks.append(check(
        "Race condition защита",
        "WHERE generations.status NOT IN ('completed', 'error')" in content,
        "WHERE условие присутствует",
        "WHERE условие НЕ найдено"
    ))
    
    # 5. Использование translate_style_to_english
    checks.append(check(
        "Перевод стиля",
        'style = translate_style_to_english(style)' in content,
        "Вызов присутствует",
        "Вызов НЕ найден"
    ))
    
    # 6. Синтаксис Python
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', CELERY_FILE], capture_output=True)
    checks.append(check(
        "Синтаксис Python",
        result.returncode == 0,
        "Корректный",
        "ОШИБКИ"
    ))
    
    print("\\n" + "═" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ({passed}/{total})")
        print("═" * 80 + "\\n")
        return 0
    else:
        print(f"⚠️  ПРОЙДЕНО {passed}/{total} ПРОВЕРОК")
        print("═" * 80 + "\\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    script_path = "/root/albimusic-bot/verify_fixes.py"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(verification_script)
    
    os.chmod(script_path, 0o755)
    
    logger.success(f"Скрипт проверки создан: {script_path}")
    
    return script_path

# ═══════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n╔" + "═" * 78 + "╗")
    print("║  ФИНАЛИЗАЦИЯ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ".center(80) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    logger.info(f"Старт: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Лог: {LOG_FILE}\n")
    
    # ═══════════════════════════════════════════════════════════════════
    # ПОДГОТОВКА
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 1: ПОДГОТОВКА")
    
    if not os.path.exists(CELERY_FILE):
        logger.error(f"Файл не найден: {CELERY_FILE}")
        return False
    
    logger.success(f"Файл найден: {CELERY_FILE}")
    print()
    
    create_backup_dir()
    print()
    
    backup_path = backup_file(CELERY_FILE)
    print()
    
    if not backup_path:
        logger.error("Не удалось создать backup")
        return False
    
    # ═══════════════════════════════════════════════════════════════════
    # ИСПРАВЛЕНИЯ
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 2: ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ")
    
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modifications = []
    
    # 1. Добавление вызова validate_audio_url
    logger.info("1️⃣  Добавление вызова validate_audio_url...")
    content, ok = add_validation_call(content)
    if ok:
        modifications.append("validation_call")
    print()
    
    # 2. Использование translate_style_to_english
    logger.info("2️⃣  Добавление использования translate_style_to_english...")
    content, ok = add_style_translation(content)
    if ok:
        modifications.append("style_translation")
    print()
    
    # Проверка: были ли изменения?
    if content == original_content:
        logger.warning("⚠️  Никаких изменений не было сделано")
        logger.info("Возможно, исправления уже применены ранее")
    else:
        # Сохранение с проверкой синтаксиса
        logger.info("Сохранение изменений...")
        
        temp_file = CELERY_FILE + ".temp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("Проверка синтаксиса...")
        if check_syntax(temp_file):
            shutil.move(temp_file, CELERY_FILE)
            logger.success("Изменения применены успешно")
        else:
            os.remove(temp_file)
            logger.error("Ошибка синтаксиса! Откат...")
            restore_from_backup(CELERY_FILE, backup_path)
            return False
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # МИГРАЦИЯ БД
    # ═══════════════════════════════════════════════════════════════════
    
    if not apply_db_migration():
        logger.warning("⚠️  Миграция БД не применена")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # СОЗДАНИЕ СКРИПТА ПРОВЕРКИ
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 3: СОЗДАНИЕ СКРИПТА ПРОВЕРКИ")
    
    verification_script = create_verification_script()
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ЗАПУСК ПРОВЕРКИ
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 4: ПРОВЕРКА РЕЗУЛЬТАТОВ")
    
    logger.info("Запуск скрипта проверки...")
    print()
    
    result = subprocess.run(['python3', verification_script], capture_output=False)
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ИТОГИ
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ИТОГИ")
    
    if modifications:
        logger.success("ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
        print()
        
        print("📋 Выполнено:")
        for i, mod in enumerate(modifications, 1):
            print(f"  {i}. ✅ {mod}")
        print()
    
    print("📁 Резервная копия:")
    print(f"  • {backup_path}")
    print()
    
    print("🔍 Скрипт проверки:")
    print(f"  • {verification_script}")
    print()
    
    print("🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print()
    print("  1. Проверка результатов:")
    print(f"     python3 {verification_script}")
    print()
    print("  2. Перезапуск Celery:")
    print("     sudo systemctl restart albimusic-celery")
    print()
    print("  3. Перезапуск бота:")
    print("     sudo systemctl restart albimusic-bot")
    print()
    print("  4. Мониторинг логов:")
    print("     sudo journalctl -u albimusic-celery -f | grep -E 'validate_audio|переведен|\\[DB\\]'")
    print()
    print("  5. Тестовая генерация:")
    print("     Отправьте запрос на генерацию музыки в бота")
    print()
    
    return result.returncode == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
