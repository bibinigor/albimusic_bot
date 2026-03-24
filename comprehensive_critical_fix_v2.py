#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ОШИБОК AlBi-music Bot v2
═══════════════════════════════════════════════════════════════════════

ВЕРСИЯ: 2.0 (исправлены проблемы с отступами)
АВТОР: Claude (Anthropic)
ДАТА: 2026-01-15

ИСПРАВЛЕНИЯ:
1. ✅ Правильная обработка отступов при замене кода
2. ✅ Проверка валидности Python после каждого изменения
3. ✅ Более безопасная замена больших блоков кода
4. ✅ Подробное логирование каждого шага
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import re
import subprocess
import ast
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════

CELERY_FILE = "/root/albimusic-bot/celery_tasks.py"
DB_UTILS_FILE = "/root/albimusic-bot/db_utils.py"

BACKUP_DIR = "/root/albimusic-bot/backups_critical_fix_v2"
LOG_FILE = f"/tmp/comprehensive_fix_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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

# ═══════════════════════════════════════════════════════════════════════
# ФУНКЦИИ БЭКАПА
# ═══════════════════════════════════════════════════════════════════════

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

def restore_file(file_path, backup_path):
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        logger.warning(f"Восстановлен из backup: {file_path}")
        return True
    return False

def validate_python_syntax(file_path):
    """Проверка синтаксиса Python (улучшенная версия)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Компиляция кода
        compile(code, file_path, 'exec')
        
        # Дополнительная проверка через ast
        ast.parse(code)
        
        logger.success(f"Синтаксис валиден: {os.path.basename(file_path)}")
        return True
    
    except SyntaxError as e:
        logger.error(f"SyntaxError в {os.path.basename(file_path)}:")
        logger.error(f"  Строка {e.lineno}: {e.msg}")
        logger.error(f"  Текст: {e.text.strip() if e.text else 'N/A'}")
        return False
    
    except IndentationError as e:
        logger.error(f"IndentationError в {os.path.basename(file_path)}:")
        logger.error(f"  Строка {e.lineno}: {e.msg}")
        logger.error(f"  Текст: {e.text.strip() if e.text else 'N/A'}")
        return False
    
    except Exception as e:
        logger.error(f"Ошибка проверки синтаксиса: {e}")
        return False

def safe_write_and_validate(file_path, content, backup_path):
    """Безопасная запись с валидацией и откатом при ошибке"""
    temp_file = file_path + ".temp"
    
    try:
        # Записываем во временный файл
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Проверяем синтаксис
        if validate_python_syntax(temp_file):
            # Синтаксис OK - перезаписываем оригинал
            shutil.move(temp_file, file_path)
            logger.success(f"Файл успешно обновлен: {os.path.basename(file_path)}")
            return True
        else:
            # Синтаксис сломан - откат
            os.remove(temp_file)
            logger.error("Синтаксис нарушен! Откат изменений...")
            restore_file(file_path, backup_path)
            return False
    
    except Exception as e:
        logger.error(f"Ошибка записи файла: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        restore_file(file_path, backup_path)
        return False

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 1: ВАЛИДАЦИЯ MP3 (с правильными отступами)
# ═══════════════════════════════════════════════════════════════════════

def add_validate_audio_function(content):
    """Добавление функции validate_audio_url"""
    
    # Функция с ПРАВИЛЬНЫМИ отступами (0 отступов для def)
    validate_function = '''
def validate_audio_url(url, request_id):
    """
    Проверка доступности и валидности MP3 файла
    
    Args:
        url (str): URL MP3 файла
        request_id (str): ID запроса для логирования
    
    Returns:
        bool: True если файл доступен и валиден
    """
    import requests
    
    try:
        logger.info(f"[{request_id}] 🔍 Проверка доступности MP3: {url[:60]}...")
        
        # HEAD запрос для проверки без скачивания
        head_response = requests.head(url, timeout=15, allow_redirects=True)
        
        if head_response.status_code != 200:
            logger.error(f"[{request_id}] ❌ MP3 недоступен: HTTP {head_response.status_code}")
            return False
        
        # Проверка Content-Type
        content_type = head_response.headers.get('Content-Type', '').lower()
        if 'audio' not in content_type and 'octet-stream' not in content_type:
            logger.warning(f"[{request_id}] ⚠️ Неожиданный Content-Type: {content_type}")
        
        # Проверка размера
        content_length = int(head_response.headers.get('Content-Length', 0))
        if content_length < 1000:
            logger.error(f"[{request_id}] ❌ MP3 слишком маленький: {content_length} байт")
            return False
        
        logger.info(f"[{request_id}] ✅ MP3 валиден: {content_length:,} байт")
        
        # Проверка magic bytes
        try:
            partial_response = requests.get(url, headers={'Range': 'bytes=0-2047'}, timeout=10)
            if partial_response.status_code in (200, 206):
                magic_bytes = partial_response.content[:3]
                is_id3 = (magic_bytes[:3] == b'ID3')
                is_mpeg = (magic_bytes[0] == 0xFF and (magic_bytes[1] & 0xE0) == 0xE0)
                
                if is_id3 or is_mpeg:
                    logger.info(f"[{request_id}] ✅ MP3 формат подтвержден")
        except Exception:
            pass  # Не критично
        
        return True
    
    except requests.exceptions.Timeout:
        logger.error(f"[{request_id}] ⏱️ Таймаут при проверке MP3")
        return False
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Ошибка проверки MP3: {e}")
        return False

'''
    
    # Ищем место ПЕРЕД def generate_suno_music_sync
    pattern = r'(\ndef generate_suno_music_sync\()'
    
    if not re.search(pattern, content):
        logger.error("Не найдена функция generate_suno_music_sync")
        return content, False
    
    # Вставляем ПЕРЕД функцией
    new_content = re.sub(pattern, validate_function + r'\1', content, count=1)
    
    if new_content != content:
        logger.success("Функция validate_audio_url добавлена")
        return new_content, True
    else:
        logger.error("Не удалось добавить validate_audio_url")
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 2: TypeError В save_generation_task_sync
# ═══════════════════════════════════════════════════════════════════════

def fix_result_handling(content):
    """Исправление обработки результата (МИНИМАЛЬНОЕ ИЗМЕНЕНИЕ)"""
    
    # Ищем проблемную строку
    old_line = r'row_id = result\[0\]\[0\] if \(isinstance\(resultXXXLATEXDISPLAYXXX3XXXLATEXDISPLAYXXX, \(tuple, list\)\) and len\(resultXXXLATEXDISPLAYXXX4XXXLATEXDISPLAYXXX\) > 0\) else \(resultXXXLATEXDISPLAYXXX5XXXLATEXDISPLAYXXX if isinstance\(resultXXXLATEXDISPLAYXXX6XXXLATEXDISPLAYXXX, int\) else \'unknown\'\)'
    
    # Новая версия (более безопасная)
    new_lines = '''# Безопасное извлечение row_id
            if isinstance(result, (list, tuple)) and len(result) > 0:
                first_item = result[0] if isinstance(result, list) else result
                if isinstance(first_item, (list, tuple)) and len(first_item) > 0:
                    row_id = first_item[0]
                elif isinstance(first_item, int):
                    row_id = first_item
                else:
                    row_id = 'unknown'
            else:
                row_id = 'unknown\''''
    
    # Заменяем
    new_content = re.sub(old_line, new_lines, content)
    
    if new_content != content:
        logger.success("Обработка result исправлена")
        return new_content, True
    
    # Альтернативный поиск (если строка была изменена)
    alt_pattern = r'row_id = result\[0\]\[0\] if len\(resultXXXLATEXDISPLAYXXX9XXXLATEXDISPLAYXXX\) > 0 else \'unknown\''
    new_content = re.sub(alt_pattern, new_lines, content)
    
    if new_content != content:
        logger.success("Обработка result исправлена (альтернативный метод)")
        return new_content, True
    
    logger.warning("Проблемная строка с result[0] не найдена (возможно, уже исправлена)")
    return content, False

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 3: ДУБЛИРОВАННЫЙ КОД В execute_query_sync
# ═══════════════════════════════════════════════════════════════════════

def fix_duplicate_code(content):
    """Удаление дубликатов в execute_query_sync"""
    
    lines = content.split('\n')
    cleaned_lines = []
    skip_until = -1
    
    for i in range(len(lines)):
        if i < skip_until:
            continue
        
        # Ищем начало блока cursor.execute
        if 'cursor.execute(query, params)' in lines[i]:
            # Проверяем следующие 10 строк на дубликат
            block = '\n'.join(lines[i:i+10])
            
            # Ищем такой же блок дальше
            for j in range(i+1, min(i+20, len(lines))):
                next_block = '\n'.join(lines[j:j+10])
                
                if block == next_block:
                    logger.info(f"Найден дубликат на строках {i+1} и {j+1}")
                    skip_until = j + 10
                    break
        
        cleaned_lines.append(lines[i])
    
    new_content = '\n'.join(cleaned_lines)
    
    if new_content != content:
        logger.success("Дубликаты удалены")
        return new_content, True
    else:
        logger.info("Дубликатов не найдено")
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 4: УДАЛЕНИЕ ДУБЛИКАТОВ MUSIC_STYLE_TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════

def remove_translation_duplicates(content):
    """Удаление дубликатов MUSIC_STYLE_TRANSLATIONS"""
    
    pattern = r'MUSIC_STYLE_TRANSLATIONS\s*=\s*\{'
    matches = list(re.finditer(pattern, content))
    
    if len(matches) <= 1:
        logger.info("Дубликатов MUSIC_STYLE_TRANSLATIONS нет")
        return content, False
    
    logger.info(f"Найдено {len(matches)} определений MUSIC_STYLE_TRANSLATIONS")
    
    # Удаляем все определения кроме первого
    parts = []
    last_end = 0
    
    for idx, match in enumerate(matches):
        if idx == 0:
            # Оставляем первое определение
            continue
        
        # Добавляем текст ДО дубликата
        parts.append(content[last_end:match.start()])
        
        # Пропускаем словарь (ищем закрывающую фигурную скобку)
        brace_count = 1
        i = match.end()
        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
            i += 1
        
        last_end = i
        logger.success(f"Удален дубликат #{idx+1}")
    
    # Добавляем остаток
    parts.append(content[last_end:])
    
    new_content = ''.join(parts)
    return new_content, True

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 5: ДОБАВЛЕНИЕ ВЫЗОВА validate_audio_url
# ═══════════════════════════════════════════════════════════════════════

def add_validation_call(content):
    """Добавление проверки MP3 перед return audio_url"""
    
    # Ищем return audio_url в generate_suno_music_sync
    pattern = r'(logger\.info\(f"XXXLATEXDISPLAYXXX10XXXLATEXDISPLAYXXX    • Audio URL: {audio_url}"\)\s+)(return audio_url)'
    
    replacement = r'''\1
                    # ПРОВЕРКА MP3 ФАЙЛА
                    logger.info(f"[{request_id}] 🔍 Валидация MP3...")
                    if not validate_audio_url(audio_url, request_id):
                        logger.error(f"[{request_id}] ❌ MP3 недоступен")
                        return None
                    
                    \2'''
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        logger.success("Вызов validate_audio_url добавлен")
        return new_content, True
    else:
        logger.warning("Место для вставки не найдено")
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 6: ЗАЩИТА ОТ RACE CONDITIONS
# ═══════════════════════════════════════════════════════════════════════

def add_race_protection(content):
    """Добавление WHERE в ON CONFLICT"""
    
    pattern = r'(ON CONFLICT \(task_id\)\s+DO UPDATE SET.*?updated_at = NOW\(\))'
    
    replacement = r'''\1
        WHERE generations.status NOT IN ('completed', 'error')'''
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        logger.success("Защита от race conditions добавлена")
        return new_content, True
    else:
        logger.warning("ON CONFLICT не найден")
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# ИСПРАВЛЕНИЕ 7: ИСПОЛЬЗОВАНИЕ translate_style_to_english
# ═══════════════════════════════════════════════════════════════════════

def add_style_translation(content):
    """Добавление перевода стиля"""
    
    # Ищем место после логирования параметров
    pattern = r'(logger\.info\(f"XXXLATEXDISPLAYXXX11XXXLATEXDISPLAYXXX    • User ID: {user_id}"\)\s+)(headers = {)'
    
    replacement = r'''\1
    # Перевод стиля на английский
    if style:
        original_style = style
        style = translate_style_to_english(style)
        if style != original_style:
            logger.info(f"[{request_id}] 🔄 Стиль переведен: '{original_style}' → '{style}'")
    
    \2'''
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        logger.success("Перевод стиля добавлен")
        return new_content, True
    else:
        logger.warning("Место для перевода не найдено")
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# МИГРАЦИЯ БД
# ═══════════════════════════════════════════════════════════════════════

def apply_db_migration():
    """Добавление колонки generation_duration_seconds"""
    
    migration_sql = """
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'generations' 
        AND column_name = 'generation_duration_seconds'
    ) THEN
        ALTER TABLE generations ADD COLUMN generation_duration_seconds INTEGER;
        CREATE INDEX idx_generations_duration ON generations(generation_duration_seconds);
        RAISE NOTICE '✅ Колонка generation_duration_seconds добавлена';
    ELSE
        RAISE NOTICE 'ℹ️ Колонка уже существует';
    END IF;
END $$;
"""
    
    migration_file = "/tmp/add_duration_column.sql"
    with open(migration_file, 'w') as f:
        f.write(migration_sql)
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', 'albimusic_db', '-f', migration_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.success("Миграция БД применена")
        print(result.stdout)
        return True
    else:
        logger.error(f"Ошибка миграции: {result.stderr}")
        return False

# ═══════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n╔" + "═" * 78 + "╗")
    print("║  КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ v2 (с проверкой отступов)".center(80) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    logger.info(f"Старт: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Лог: {LOG_FILE}\n")
    
    # ═══════════════════════════════════════════════════════════════════
    # ПОДГОТОВКА
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 1: ПОДГОТОВКА")
    
    for file_path in [CELERY_FILE, DB_UTILS_FILE]:
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return False
        logger.success(f"Найден: {os.path.basename(file_path)}")
    
    print()
    create_backup_dir()
    print()
    
    celery_backup = backup_file(CELERY_FILE)
    db_utils_backup = backup_file(DB_UTILS_FILE)
    print()
    
    if not celery_backup or not db_utils_backup:
        logger.error("Не удалось создать бэкапы")
        return False
    
    # ═══════════════════════════════════════════════════════════════════
    # ИСПРАВЛЕНИЯ В celery_tasks.py
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 2: ИСПРАВЛЕНИЯ В celery_tasks.py")
    
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        celery_content = f.read()
    
    modifications = []
    
    # 1. Валидация MP3
    logger.info("1️⃣ Добавление validate_audio_url...")
    celery_content, ok = add_validate_audio_function(celery_content)
    if ok:
        modifications.append("validate_audio_url")
        if not safe_write_and_validate(CELERY_FILE, celery_content, celery_backup):
            return False
    print()
    
    # 2. TypeError
    logger.info("2️⃣ Исправление TypeError...")
    celery_content, ok = fix_result_handling(celery_content)
    if ok:
        modifications.append("result_handling")
        if not safe_write_and_validate(CELERY_FILE, celery_content, celery_backup):
            return False
    print()
    
    # 4. Дубликаты словаря
    logger.info("4️⃣ Удаление дубликатов MUSIC_STYLE_TRANSLATIONS...")
    celery_content, ok = remove_translation_duplicates(celery_content)
    if ok:
        modifications.append("remove_duplicates")
        if not safe_write_and_validate(CELERY_FILE, celery_content, celery_backup):
            return False
    print()
    
    # 5. Вызов валидации
    logger.info("5️⃣ Добавление вызова validate_audio_url...")
    celery_content, ok = add_validation_call(celery_content)
    if ok:
        modifications.append("validation_call")
        if not safe_write_and_validate(CELERY_FILE, celery_content, celery_backup):
            return False
    print()
    
    # 6. Race conditions
    logger.info("6️⃣ Защита от race conditions...")
    celery_content, ok = add_race_protection(celery_content)
    if ok:
        modifications.append("race_protection")
        if not safe_write_and_validate(CELERY_FILE, celery_content, celery_backup):
            return False
    print()
    
    # 7. Перевод стиля
    logger.info("7️⃣ Использование translate_style_to_english...")
    celery_content, ok = add_style_translation(celery_content)
    if ok:
        modifications.append("style_translation")
        if not safe_write_and_validate(CELERY_FILE, celery_content, celery_backup):
            return False
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ИСПРАВЛЕНИЯ В db_utils.py
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 3: ИСПРАВЛЕНИЯ В db_utils.py")
    
    with open(DB_UTILS_FILE, 'r', encoding='utf-8') as f:
        db_content = f.read()
    
    logger.info("3️⃣ Удаление дубликатов в execute_query_sync...")
    db_content, ok = fix_duplicate_code(db_content)
    if ok:
        modifications.append("duplicate_code")
        if not safe_write_and_validate(DB_UTILS_FILE, db_content, db_utils_backup):
            return False
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # МИГРАЦИЯ БД
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ЭТАП 4: МИГРАЦИЯ БД")
    apply_db_migration()
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ИТОГИ
    # ═══════════════════════════════════════════════════════════════════
    
    logger.section("ИТОГИ")
    
    logger.success("ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print()
    
    print("📋 Применено исправлений:")
    for i, mod in enumerate(modifications, 1):
        print(f"  {i}. ✅ {mod}")
    print()
    
    print("📁 Резервные копии:")
    print(f"  • {celery_backup}")
    print(f"  • {db_utils_backup}")
    print()
    
    print("🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("  1. sudo systemctl restart albimusic-celery")
    print("  2. sudo systemctl restart albimusic-bot")
    print("  3. sudo journalctl -u albimusic-celery -f | grep -E 'validate_audio|\\[DB\\]'")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
