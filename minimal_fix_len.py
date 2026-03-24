#!/usr/bin/env python3
"""
МИНИМАЛЬНОЕ ТОЧЕЧНОЕ ИСПРАВЛЕНИЕ len(result[0])

ЦЕЛЬ:
- Исправить ТОЛЬКО строку с len(result[0])
- НЕ трогать остальной код
- НЕ ломать структуру try-except
"""

import os
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/celery_tasks.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_minimal_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def minimal_fix(content):
    """
    Минимальное исправление ТОЛЬКО проблемной строки
    
    БЫЛО:
        row_id = result[0][0] if len(result[0]) > 0 else 'unknown'
    
    СТАНЕТ:
        row_id = result[0][0] if (isinstance(result[0], (tuple, list)) and len(result[0]) > 0) else (result[0] if isinstance(result[0], int) else 'unknown')
    """
    
    # Точная замена проблемной строки
    old_line = "row_id = result[0][0] if len(result[0]) > 0 else 'unknown'"
    
    new_line = "row_id = result[0][0] if (isinstance(result[0], (tuple, list)) and len(result[0]) > 0) else (result[0] if isinstance(result[0], int) else 'unknown')"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        log("Строка с len(result[0]) исправлена", "✅")
        return content, True
    else:
        log("Проблемная строка НЕ найдена", "❌")
        log("Возможно, файл уже был изменен", "⚠️")
        return content, False

def main():
    print("=" * 80)
    print("МИНИМАЛЬНОЕ ТОЧЕЧНОЕ ИСПРАВЛЕНИЕ len(result[0])")
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
    
    # 4. Минимальное исправление
    log("Исправление проблемной строки...")
    new_content, modified = minimal_fix(content)
    
    if not modified:
        print()
        log("ВНИМАНИЕ: Строка не найдена или уже исправлена", "⚠️")
        
        # Показываем похожие строки для диагностики
        print("\n🔍 Поиск похожих строк:")
        for i, line in enumerate(content.split('\n'), 1):
            if 'row_id = result[0]' in line or 'len(result[0])' in line:
                print(f"  Строка {i}: {line.strip()}")
        
        response = input("\n❓ Продолжить всё равно? (y/n): ")
        if response.lower() != 'y':
            return False
    
    print()
    
    # 5. Сохранение
    log("Сохранение файла...")
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 6. Проверка синтаксиса
    log("Проверка синтаксиса Python...")
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'py_compile', FILE_PATH],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("Синтаксис корректен", "✅")
        
        print()
        print("=" * 80)
        log("МИНИМАЛЬНОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!", "✅")
        print("=" * 80)
        
        print(f"\n📁 Backup: {backup_path}")
        
        print("\n📋 Что изменено:")
        print("  ✅ Добавлена проверка isinstance() перед len()")
        print("  ✅ Обработка случая, когда result[0] это int")
        print("  ✅ Сохранена вся остальная структура кода")
        
        print("\n🎯 Конкретное изменение:")
        print("  БЫЛО:")
        print("    row_id = result[0][0] if len(result[0]) > 0 else 'unknown'")
        print()
        print("  СТАЛО:")
        print("    row_id = result[0][0] if (isinstance(result[0], (tuple, list)) and len(result[0]) > 0)")
        print("             else (result[0] if isinstance(result[0], int) else 'unknown')")
        
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        
        print("\n🔍 Проверка:")
        print("  sudo journalctl -u albimusic-celery -f | grep -E 'TypeError|len\\(\\)|\\[DB\\]'")
        
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print()
        print("=" * 80)
        print("ДЕТАЛИ ОШИБКИ:")
        print("=" * 80)
        print(result.stderr)
        
        log("Восстановление из backup...", "⚠️")
        shutil.copy2(backup_path, FILE_PATH)
        
        print("\n⚠️ Файл восстановлен из backup")
        print("📋 Возможные причины ошибки:")
        print("  1. Файл уже был изменен другим скриптом")
        print("  2. Строка с ошибкой находится в другом месте")
        print("  3. Синтаксис Python был нарушен ранее")
        
        print("\n🔍 Рекомендация: Проверьте файл вручную:")
        print(f"  grep -n 'len(result\\[0\\])' {FILE_PATH}")
        
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
