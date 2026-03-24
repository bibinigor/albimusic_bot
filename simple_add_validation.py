#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
ПРОСТОЕ ТОЧЕЧНОЕ ДОБАВЛЕНИЕ ВЫЗОВОВ ФУНКЦИЙ
═══════════════════════════════════════════════════════════════════════

ЗАДАЧИ:
1. Добавить вызов validate_audio_url после логирования Total time
2. Добавить перевод стиля после логирования User ID

МЕТОД: Построчный поиск и вставка (БЕЗ сложных regex)

ВЕРСИЯ: 1.0
АВТОР: Claude (Anthropic)
ДАТА: 2026-01-15
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════

CELERY_FILE = "/root/albimusic-bot/celery_tasks.py"
BACKUP_DIR = "/root/albimusic-bot/backups_simple"

# Коды для вставки
VALIDATION_CODE = '''                
                # 🔍 ПРОВЕРКА ВАЛИДНОСТИ MP3
                logger.info(f"[{request_id}] 🔍 Валидация MP3...")
                if not validate_audio_url(audio_url, request_id):
                    logger.error(f"[{request_id}] ❌ MP3 не прошел валидацию")
                    return None
'''

TRANSLATION_CODE = '''    
    # 🔄 ПЕРЕВОД СТИЛЯ НА АНГЛИЙСКИЙ
    if style:
        original_style = style
        style = translate_style_to_english(style)
        if style != original_style:
            logger.info(f"[{request_id}] 🔄 СТИЛЬ ПЕРЕВЕДЕН: '{original_style}' → '{style}'")
'''

# ═══════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════

def log(msg, symbol="•"):
    """Простое логирование"""
    print(f"{symbol} {msg}")

def create_backup():
    """Создание бэкапа"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"celery_tasks.py.backup_{timestamp}")
    shutil.copy2(CELERY_FILE, backup_path)
    log(f"✅ Backup: {backup_path}", "✅")
    return backup_path

def check_syntax():
    """Проверка синтаксиса Python"""
    result = subprocess.run(
        ['python3', '-m', 'py_compile', CELERY_FILE],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        log("✅ Синтаксис корректен", "✅")
        return True
    else:
        log("❌ Ошибка синтаксиса:", "❌")
        print(result.stderr)
        return False

def restore_backup(backup_path):
    """Восстановление из бэкапа"""
    shutil.copy2(backup_path, CELERY_FILE)
    log("⚠️  Восстановлено из backup", "⚠️")

# ═══════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 1: ДОБАВЛЕНИЕ ПРОВЕРКИ MP3
# ═══════════════════════════════════════════════════════════════════════

def add_mp3_validation(lines):
    """
    Добавить проверку MP3 после строки с Total time
    
    ИЩЕМ:
        logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")
        return audio_url
    
    ЗАМЕНЯЕМ НА:
        logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")
        
        # Проверка MP3
        if not validate_audio_url(...):
            return None
        
        return audio_url
    """
    
    new_lines = []
    added = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Ищем строку с Total time
        if not added and '• Total time:' in line and 'time.time() - start_time' in line:
            log(f"Найдена строка Total time на строке {i+1}", "🔍")
            
            # Проверяем следующую строку - должна быть return audio_url
            if i + 1 < len(lines) and 'return audio_url' in lines[i + 1]:
                log("Найден return audio_url на следующей строке", "🔍")
                
                # Вставляем код проверки ПЕРЕД return
                for code_line in VALIDATION_CODE.split('\n'):
                    new_lines.append(code_line)
                
                added = True
                log("✅ Код проверки MP3 добавлен", "✅")
        
        i += 1
    
    if not added:
        log("⚠️  Не удалось найти место для вставки проверки MP3", "⚠️")
        log("   Ищем строку: logger.info(f\"[{request_id}]    • Total time:\")", "ℹ️")
        return None
    
    return new_lines

# ═══════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ 2: ДОБАВЛЕНИЕ ПЕРЕВОДА СТИЛЯ
# ═══════════════════════════════════════════════════════════════════════

def add_style_translation(lines):
    """
    Добавить перевод стиля после строки с User ID
    
    ИЩЕМ:
        logger.info(f"[{request_id}]    • User ID: {user_id}")
        
        headers = {
    
    ЗАМЕНЯЕМ НА:
        logger.info(f"[{request_id}]    • User ID: {user_id}")
        
        # Перевод стиля
        if style:
            style = translate_style_to_english(style)
        
        headers = {
    """
    
    new_lines = []
    added = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Ищем строку с User ID
        if not added and '• User ID:' in line and '{user_id}' in line:
            log(f"Найдена строка User ID на строке {i+1}", "🔍")
            
            # Ищем следующую строку с headers (может быть не сразу)
            next_headers_line = -1
            for j in range(i + 1, min(i + 5, len(lines))):
                if 'headers = {' in lines[j] or 'headers={' in lines[j]:
                    next_headers_line = j
                    break
            
            if next_headers_line != -1:
                log(f"Найден headers на строке {next_headers_line+1}", "🔍")
                
                # Копируем все строки между User ID и headers
                for j in range(i + 1, next_headers_line):
                    new_lines.append(lines[j])
                
                # Вставляем код перевода ПЕРЕД headers
                for code_line in TRANSLATION_CODE.split('\n'):
                    new_lines.append(code_line)
                
                # Пропускаем строки, которые уже скопировали
                i = next_headers_line - 1
                
                added = True
                log("✅ Код перевода стиля добавлен", "✅")
        
        i += 1
    
    if not added:
        log("⚠️  Не удалось найти место для вставки перевода стиля", "⚠️")
        log("   Ищем строку: logger.info(f\"[{request_id}]    • User ID:\")", "ℹ️")
        return None
    
    return new_lines

# ═══════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 80)
    print("  ПРОСТОЕ ДОБАВЛЕНИЕ ВЫЗОВОВ ФУНКЦИЙ")
    print("═" * 80 + "\n")
    
    # ═══════════════════════════════════════════════════════════════════
    # ПРОВЕРКА ФАЙЛА
    # ═══════════════════════════════════════════════════════════════════
    
    log("Проверка файла...")
    
    if not os.path.exists(CELERY_FILE):
        log(f"❌ Файл не найден: {CELERY_FILE}", "❌")
        return False
    
    log(f"✅ Файл найден: {CELERY_FILE}", "✅")
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # БЭКАП
    # ═══════════════════════════════════════════════════════════════════
    
    log("Создание backup...")
    backup_path = create_backup()
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ЧТЕНИЕ ФАЙЛА
    # ═══════════════════════════════════════════════════════════════════
    
    log("Чтение файла...")
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    log(f"Прочитано {len(lines)} строк", "✅")
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ПРОВЕРКА: УЖЕ ЕСТЬ ИЗМЕНЕНИЯ?
    # ═══════════════════════════════════════════════════════════════════
    
    log("Проверка существующих изменений...")
    
    has_validation = 'validate_audio_url(audio_url, request_id)' in content
    has_translation = 'translate_style_to_english(style)' in content
    
    if has_validation:
        log("ℹ️  Вызов validate_audio_url уже присутствует", "ℹ️")
    
    if has_translation:
        log("ℹ️  Вызов translate_style_to_english уже присутствует", "ℹ️")
    
    if has_validation and has_translation:
        log("ℹ️  Все изменения уже применены", "ℹ️")
        print("\n✅ НЕТ НЕОБХОДИМОСТИ В ИЗМЕНЕНИЯХ\n")
        return True
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ
    # ═══════════════════════════════════════════════════════════════════
    
    log("Применение изменений...")
    print()
    
    modified_lines = lines
    changes_made = []
    
    # 1. Добавление проверки MP3
    if not has_validation:
        log("1️⃣  Добавление проверки MP3...")
        result = add_mp3_validation(modified_lines)
        
        if result is None:
            log("❌ Не удалось добавить проверку MP3", "❌")
            log("   Восстановление из backup...", "⚠️")
            restore_backup(backup_path)
            return False
        
        modified_lines = result
        changes_made.append("MP3 validation")
        print()
    else:
        log("1️⃣  Проверка MP3 пропущена (уже есть)", "ℹ️")
        print()
    
    # 2. Добавление перевода стиля
    if not has_translation:
        log("2️⃣  Добавление перевода стиля...")
        result = add_style_translation(modified_lines)
        
        if result is None:
            log("❌ Не удалось добавить перевод стиля", "❌")
            log("   Восстановление из backup...", "⚠️")
            restore_backup(backup_path)
            return False
        
        modified_lines = result
        changes_made.append("Style translation")
        print()
    else:
        log("2️⃣  Перевод стиля пропущен (уже есть)", "ℹ️")
        print()
    
    # ═══════════════════════════════════════════════════════════════════
    # СОХРАНЕНИЕ
    # ═══════════════════════════════════════════════════════════════════
    
    if not changes_made:
        log("ℹ️  Нет изменений для сохранения", "ℹ️")
        return True
    
    log("Сохранение изменений...")
    
    new_content = '\n'.join(modified_lines)
    
    # Сначала сохраняем во временный файл
    temp_file = CELERY_FILE + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    log("✅ Временный файл создан", "✅")
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ПРОВЕРКА СИНТАКСИСА
    # ═══════════════════════════════════════════════════════════════════
    
    log("Проверка синтаксиса...")
    
    result = subprocess.run(
        ['python3', '-m', 'py_compile', temp_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("✅ Синтаксис корректен", "✅")
        
        # Перемещаем временный файл на место оригинала
        shutil.move(temp_file, CELERY_FILE)
        log("✅ Файл сохранен", "✅")
    else:
        log("❌ Ошибка синтаксиса:", "❌")
        print(result.stderr)
        
        # Удаляем временный файл
        os.remove(temp_file)
        
        # Восстанавливаем из backup
        log("⚠️  Восстановление из backup...", "⚠️")
        restore_backup(backup_path)
        
        return False
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ФИНАЛЬНАЯ ПРОВЕРКА
    # ═══════════════════════════════════════════════════════════════════
    
    log("Финальная проверка...")
    
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        final_content = f.read()
    
    checks = []
    
    # Проверка 1: validate_audio_url вызывается
    if 'validate_audio_url(audio_url, request_id)' in final_content:
        log("✅ Вызов validate_audio_url присутствует", "✅")
        checks.append(True)
    else:
        log("❌ Вызов validate_audio_url НЕ НАЙДЕН", "❌")
        checks.append(False)
    
    # Проверка 2: translate_style_to_english используется
    if 'translate_style_to_english(style)' in final_content:
        log("✅ Вызов translate_style_to_english присутствует", "✅")
        checks.append(True)
    else:
        log("❌ Вызов translate_style_to_english НЕ НАЙДЕН", "❌")
        checks.append(False)
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ИТОГИ
    # ═══════════════════════════════════════════════════════════════════
    
    print("═" * 80)
    
    if all(checks):
        print("✅ ВСЕ ИЗМЕНЕНИЯ ПРИМЕНЕНЫ УСПЕШНО")
    else:
        print("⚠️  НЕКОТОРЫЕ ИЗМЕНЕНИЯ НЕ ПРИМЕНЕНЫ")
    
    print("═" * 80)
    print()
    
    print("📋 Применено:")
    for change in changes_made:
        print(f"  ✅ {change}")
    print()
    
    print("📁 Backup:")
    print(f"  • {backup_path}")
    print()
    
    print("🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print()
    print("  1. Запустить проверку:")
    print("     python3 /root/albimusic-bot/verify_fixes.py")
    print()
    print("  2. Перезапустить Celery:")
    print("     sudo systemctl restart albimusic-celery")
    print()
    print("  3. Перезапустить бота:")
    print("     sudo systemctl restart albimusic-bot")
    print()
    print("  4. Проверить логи:")
    print("     sudo journalctl -u albimusic-celery -f | grep -E 'Валидация|ПЕРЕВЕДЕН'")
    print()
    
    return all(checks)

# ═══════════════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем\n")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
