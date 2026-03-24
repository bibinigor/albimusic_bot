#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
ОБНОВЛЕНИЕ ФУНКЦИИ format_style_for_suno
═══════════════════════════════════════════════════════════════════════

ЗАДАЧА:
Объединить перевод стиля и форматирование в одну функцию

ИЗМЕНЕНИЯ:
1. format_style_for_suno теперь сама переводит стиль
2. Удален дублирующий блок перевода на строке 317
3. Добавлено детальное логирование

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
BACKUP_DIR = "/root/albimusic-bot/backups_format_style_update"

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
# НОВАЯ ВЕРСИЯ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════

NEW_FORMAT_FUNCTION = '''def format_style_for_suno(style):
    """
    Форматирует стиль для Suno API (перевод + обертка в [])
    
    ПРОБЛЕМА: Suno API интерпретирует стиль без [] как часть лирики
    
    РЕШЕНИЕ: 
    1. Переводим стиль на английский
    2. Оборачиваем в [квадратные скобки] для разделения
       метаданных (Chirp) и лирики (Bark)
    
    Args:
        style (str): Стиль музыки (на русском или английском)
    
    Returns:
        str: Отформатированный стиль для Suno API
    
    Примеры:
        "рок" → "rock"
        "рэп, хип хоп" → "[rap, hip hop]"
        "классическая музыка" → "[classical music]"
        "rock" → "rock"
        "hard rock" → "[hard rock]"
    
    Правила обертки:
        1. Если есть запятая → оборачиваем в []
        2. Если несколько слов → оборачиваем в []
        3. Если уже в [] → не трогаем
        4. Простое одно слово → без скобок
    """
    
    if not style:
        return ""
    
    # Запоминаем оригинальный стиль для логирования
    original_style = style.strip()
    
    # ═══════════════════════════════════════════════════════════════
    # ШАГ 1: ПЕРЕВОД НА АНГЛИЙСКИЙ
    # ═══════════════════════════════════════════════════════════════
    
    translated_style = translate_style_to_english(original_style)
    
    # Логируем перевод (только если изменился)
    if translated_style != original_style:
        logger.info(f"[Suno] 🔄 Стиль переведен: '{original_style}' → '{translated_style}'")
    
    # ═══════════════════════════════════════════════════════════════
    # ШАГ 2: ФОРМАТИРОВАНИЕ (ОБЕРТКА В [])
    # ═══════════════════════════════════════════════════════════════
    
    style = translated_style.strip()
    
    # Уже обернут в []?
    if style.startswith('[') and style.endswith(']'):
        logger.info(f"[Suno] ℹ️  Стиль уже в []: '{style}'")
        return style
    
    # Определяем нужны ли скобки
    needs_brackets = (
        ',' in style or                                          # Есть запятые
        len(style.split()) > 1 or                                # Несколько слов
        any(char in style for char in ['(', ')', '{', '}'])      # Спецсимволы
    )
    
    if needs_brackets:
        formatted_style = f"[{style}]"
        logger.info(f"[Suno] 📦 Стиль обернут в []: '{style}' → '{formatted_style}'")
        return formatted_style
    
    # Простой стиль - без изменений
    logger.info(f"[Suno] ✅ Стиль без изменений: '{style}'")
    return style
'''

# ═══════════════════════════════════════════════════════════════════════
# ЗАМЕНА ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════

def replace_format_function(content):
    """Заменяет старую функцию format_style_for_suno на новую"""
    
    # Ищем старую функцию (от def до конца функции)
    pattern = r'def format_style_for_suno\(style\):.*?(?=\n(?:def |@|class |#\s*═{3,}|\Z))'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("⚠️  Функция format_style_for_suno не найдена", "⚠️")
        return content, False
    
    # Заменяем старую функцию новой
    new_content = re.sub(pattern, NEW_FORMAT_FUNCTION, content, count=1, flags=re.DOTALL)
    
    if new_content != content:
        log("✅ Функция format_style_for_suno обновлена", "✅")
        return new_content, True
    else:
        return content, False

# ═══════════════════════════════════════════════════════════════════════
# УДАЛЕНИЕ ДУБЛИРУЮЩЕГО БЛОКА ПЕРЕВОДА
# ═══════════════════════════════════════════════════════════════════════

def remove_duplicate_translation(content):
    """
    Удаляет дублирующий блок перевода стиля на строке ~317
    
    ИЩЕМ:
        # 🔄 ПЕРЕВОД СТИЛЯ НА АНГЛИЙСКИЙ
        if style:
            original_style = style
            style = translate_style_to_english(style)
            if style != original_style:
                logger.info(...)
    
    УДАЛЯЕМ этот блок (теперь перевод внутри format_style_for_suno)
    """
    
    # Паттерн дублирующего блока
    pattern = r'\s*# 🔄 ПЕРЕВОД СТИЛЯ НА АНГЛИЙСКИЙ\s+if style:\s+original_style = style\s+style = translate_style_to_english\(style\)\s+if style != original_style:\s+logger\.info\(f"XXXLATEXDISPLAYXXX0XXXLATEXDISPLAYXXX 🔄 СТИЛЬ ПЕРЕВЕДЕН:.*?"\)\s*\n'
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if not matches:
        log("ℹ️  Дублирующий блок перевода не найден (возможно уже удален)", "ℹ️")
        return content, False
    
    # Удаляем все найденные блоки
    new_content = re.sub(pattern, '\n', content, flags=re.DOTALL)
    
    count = len(matches)
    log(f"✅ Удалено {count} дублирующих блоков перевода", "✅")
    
    return new_content, True

# ═══════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 80)
    print("  ОБНОВЛЕНИЕ ФУНКЦИИ format_style_for_suno")
    print("═" * 80 + "\n")
    
    log("ЗАДАЧА: Объединить перевод и форматирование стиля")
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
    # ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ
    # ═══════════════════════════════════════════════════════════════════
    
    log("Применение изменений...")
    print()
    
    changes = []
    
    # 1. Замена функции
    log("1️⃣  Обновление функции format_style_for_suno...")
    content, ok1 = replace_format_function(content)
    
    if ok1:
        changes.append("Функция обновлена")
    else:
        log("⚠️  Не удалось обновить функцию", "⚠️")
    
    print()
    
    # 2. Удаление дубликатов
    log("2️⃣  Удаление дублирующего блока перевода...")
    content, ok2 = remove_duplicate_translation(content)
    
    if ok2:
        changes.append("Дубликаты удалены")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # СОХРАНЕНИЕ
    # ═══════════════════════════════════════════════════════════════════
    
    if not changes:
        log("ℹ️  Нет изменений для сохранения", "ℹ️")
        return True
    
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
        ('translate_style_to_english(original_style)' in final_content, 
         "Перевод внутри format_style_for_suno"),
        ('format_style_for_suno(style)' in final_content, 
         "Функция используется"),
        (final_content.count('translate_style_to_english(style)') == 1,
         "Нет дублирующих переводов вне функции")
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
        print("✅ ОБНОВЛЕНИЕ ПРИМЕНЕНО УСПЕШНО")
    else:
        print("⚠️  НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
    
    print("═" * 80)
    print()
    
    print("📋 Применено:")
    for change in changes:
        print(f"  ✅ {change}")
    print()
    
    print("📁 Backup:")
    print(f"  • {backup_path}")
    print()
    
    if all_ok:
        print("🎯 ЧТО ИЗМЕНИЛОСЬ:")
        print()
        print("  БЫЛО (2 отдельных вызова):")
        print("    1. translate_style_to_english(style)  # Перевод")
        print("    2. format_style_for_suno(style)       # Форматирование")
        print()
        print("  СТАЛО (всё в одной функции):")
        print("    format_style_for_suno(style)  # Перевод + форматирование")
        print()
        print("  ПРИМЕРЫ:")
        print('    "рок" → "rock"')
        print('    "рэп, хип хоп" → "[rap, hip hop]"')
        print('    "классическая музыка" → "[classical music]"')
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
        print("     Отправьте запрос: 'Создай песню в стиле рэп, хип хоп'")
        print()
        print("  4. Проверить логи:")
        print("     sudo journalctl -u albimusic-celery -f | grep -E 'переведен|обернут'")
        print()
        print("  Ожидаемые логи:")
        print("     [Suno] 🔄 Стиль переведен: 'рэп, хип хоп' → 'rap, hip hop'")
        print("     [Suno] 📦 Стиль обернут в []: 'rap, hip hop' → '[rap, hip hop]'")
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
