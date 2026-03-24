#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
ИСПРАВЛЕНИЕ ФОРМАТА СТИЛЯ ДЛЯ SUNO API
═══════════════════════════════════════════════════════════════════════

ПРОБЛЕМА:
Suno API интерпретирует стиль "рэп, хип хоп" как часть лирики

РЕШЕНИЕ:
Оборачивать сложные стили в [квадратные скобки] для разделения
метаданных (Chirp) и лирики (Bark)

ВЕРСИЯ: 1.0
АВТОР: Claude (Anthropic)
ДАТА: 2026-01-15
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import subprocess
import re
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════

CELERY_FILE = "/root/albimusic-bot/celery_tasks.py"
BACKUP_DIR = "/root/albimusic-bot/backups_style_format"

# ═══════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"celery_tasks.py.backup_{timestamp}")
    shutil.copy2(CELERY_FILE, backup_path)
    log(f"✅ Backup: {backup_path}", "✅")
    return backup_path

def check_syntax():
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
    shutil.copy2(backup_path, CELERY_FILE)
    log("⚠️  Восстановлено из backup", "⚠️")

# ═══════════════════════════════════════════════════════════════════════
# ФУНКЦИЯ ФОРМАТИРОВАНИЯ СТИЛЯ
# ═══════════════════════════════════════════════════════════════════════

FORMAT_STYLE_FUNCTION = '''
def format_style_for_suno(style):
    """
    Форматирует стиль для Suno API (оборачивает в [] если нужно)
    
    ПРОБЛЕМА: Suno API путает стиль с лирикой если он сложный
    
    РЕШЕНИЕ: Оборачиваем стиль в [квадратные скобки] для разделения
    инструкций для Chirp (музыка) и Bark (лирика)
    
    Args:
        style (str): Стиль музыки (уже переведенный на английский)
    
    Returns:
        str: Форматированный стиль
    
    Примеры:
        "rock" → "rock"                    (простой стиль)
        "rap, hip hop" → "[rap, hip hop]"  (несколько слов)
        "classical music" → "[classical music]"
    
    Правила:
        1. Если есть запятая → оборачиваем в []
        2. Если несколько слов → оборачиваем в []
        3. Если уже в [] → не трогаем
        4. Простое слово → без скобок
    """
    
    if not style:
        return ""
    
    style = style.strip()
    
    # Уже обернут?
    if style.startswith('[') and style.endswith(']'):
        return style
    
    # Определяем нужны ли скобки
    needs_brackets = (
        ',' in style or                    # Есть запятые
        len(style.split()) > 1 or          # Несколько слов
        any(char in style for char in ['(', ')', '{', '}'])  # Спецсимволы
    )
    
    if needs_brackets:
        logger.info(f"[Suno] Стиль обернут в []: '{style}' → '[{style}]'")
        return f"[{style}]"
    
    return style

'''

# ═══════════════════════════════════════════════════════════════════════
# ДОБАВЛЕНИЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════

def add_format_function(content):
    """Добавляет функцию format_style_for_suno перед generate_suno_music_sync"""
    
    # Ищем функцию generate_suno_music_sync
    pattern = r'(\ndef generate_suno_music_sync\()'
    
    if not re.search(pattern, content):
        log("❌ Не найдена функция generate_suno_music_sync", "❌")
        return content, False
    
    # Вставляем ПЕРЕД функцией
    new_content = re.sub(pattern, FORMAT_STYLE_FUNCTION + r'\1', content, count=1)
    
    if new_content != content:
        log("✅ Функция format_style_for_suno добавлена", "✅")
        return new_content, True
    else:
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# МОДИФИКАЦИЯ ВЫЗОВОВ
# ═══════════════════════════════════════════════════════════════════════

def wrap_style_calls(content):
    """
    Оборачивает все использования style в format_style_for_suno()
    
    БЫЛО:
        "style": style if style else ""
    
    СТАНЕТ:
        "style": format_style_for_suno(style) if style else ""
    """
    
    # Паттерн: "style": style if style else ""
    pattern = r'"style":\s*style\s+if\s+style\s+else\s+""'
    
    replacement = r'"style": format_style_for_suno(style) if style else ""'
    
    # Подсчитываем количество замен
    count = len(re.findall(pattern, content))
    
    if count == 0:
        log("⚠️  Не найдено мест для замены", "⚠️")
        return content, False
    
    # Применяем замену
    new_content = re.sub(pattern, replacement, content)
    
    log(f"✅ Обернуто {count} использований style", "✅")
    
    return new_content, True

# ═══════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 80)
    print("  ИСПРАВЛЕНИЕ ФОРМАТА СТИЛЯ ДЛЯ SUNO API")
    print("═" * 80 + "\n")
    
    log("ПРОБЛЕМА: Suno включает стиль в текст песни")
    log("РЕШЕНИЕ: Оборачивать стиль в [квадратные скобки]")
    print()
    
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
    
    log(f"✅ Прочитано {len(content)} символов", "✅")
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ПРОВЕРКА: УЖЕ ИСПРАВЛЕНО?
    # ═══════════════════════════════════════════════════════════════════
    
    log("Проверка существующих изменений...")
    
    if 'def format_style_for_suno(' in content:
        log("ℹ️  Функция format_style_for_suno уже существует", "ℹ️")
        
        if 'format_style_for_suno(style)' in content:
            log("ℹ️  Функция уже используется", "ℹ️")
            print("\n✅ ИСПРАВЛЕНИЕ УЖЕ ПРИМЕНЕНО\n")
            return True
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ
    # ═══════════════════════════════════════════════════════════════════
    
    log("Применение исправлений...")
    print()
    
    # 1. Добавление функции
    log("1️⃣  Добавление функции format_style_for_suno...")
    content, ok1 = add_format_function(content)
    
    if not ok1:
        log("❌ Не удалось добавить функцию", "❌")
        return False
    
    print()
    
    # 2. Модификация вызовов
    log("2️⃣  Модификация использования style...")
    content, ok2 = wrap_style_calls(content)
    
    if not ok2:
        log("⚠️  Не удалось изменить вызовы (возможно уже изменено)", "⚠️")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # СОХРАНЕНИЕ
    # ═══════════════════════════════════════════════════════════════════
    
    log("Сохранение изменений...")
    
    temp_file = CELERY_FILE + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        shutil.move(temp_file, CELERY_FILE)
        log("✅ Файл сохранен", "✅")
    else:
        log("❌ Ошибка синтаксиса:", "❌")
        print(result.stderr)
        os.remove(temp_file)
        restore_backup(backup_path)
        return False
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ФИНАЛЬНАЯ ПРОВЕРКА
    # ═══════════════════════════════════════════════════════════════════
    
    log("Финальная проверка...")
    
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        final_content = f.read()
    
    checks = [
        ('format_style_for_suno' in final_content, "Функция определена"),
        ('format_style_for_suno(style)' in final_content, "Функция используется"),
    ]
    
    for ok, msg in checks:
        if ok:
            log(f"✅ {msg}", "✅")
        else:
            log(f"❌ {msg}", "❌")
    
    all_ok = all(ok for ok, _ in checks)
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ИТОГИ
    # ═══════════════════════════════════════════════════════════════════
    
    print("═" * 80)
    
    if all_ok:
        print("✅ ИСПРАВЛЕНИЕ ПРИМЕНЕНО УСПЕШНО")
    else:
        print("⚠️  НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
    
    print("═" * 80)
    print()
    
    print("📁 Backup:")
    print(f"  • {backup_path}")
    print()
    
    if all_ok:
        print("🎯 ЧТО ИЗМЕНИЛОСЬ:")
        print()
        print("  БЫЛО:")
        print('    "style": style if style else ""')
        print()
        print("  СТАЛО:")
        print('    "style": format_style_for_suno(style) if style else ""')
        print()
        print("  ЭФФЕКТ:")
        print('    "рэп, хип хоп" → "[rap, hip hop]"')
        print('    "rock" → "rock"')
        print()
        print("🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print()
        print("  1. Перезапустить Celery:")
        print("     sudo systemctl restart albimusic-celery")
        print()
        print("  2. Перезапустить бота:")
        print("     sudo systemctl restart albimusic-bot")
        print()
        print("  3. Протестировать:")
        print("     Отправьте запрос на генерацию со стилем 'рэп, хип хоп'")
        print()
        print("  4. Проверить логи:")
        print("     sudo journalctl -u albimusic-celery -f | grep 'Стиль обернут'")
        print()
    
    return all_ok

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
