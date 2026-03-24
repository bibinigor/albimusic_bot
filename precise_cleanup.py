#!/usr/bin/env python3
"""
Точечное удаление дублирующихся строк в process_generation_mode
"""

import os
import re
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_precise_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def main():
    print("=" * 60)
    print("ТОЧЕЧНАЯ ОЧИСТКА ДУБЛИРУЮЩЕГОСЯ КОДА")
    print("=" * 60)
    
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
        lines = f.readlines()
    
    # 4. Поиск и удаление старых строк
    log("Поиск дублирующихся блоков...")
    
    new_lines = []
    in_old_block = False
    in_function = False
    removed_lines = 0
    
    for i, line in enumerate(lines):
        
        # Находим начало функции process_generation_mode
        if 'async def process_generation_mode' in line:
            in_function = True
            new_lines.append(line)
            continue
        
        if not in_function:
            new_lines.append(line)
            continue
        
        # Конец функции (следующая функция или декоратор)
        if in_function and (line.startswith('async def ') or line.startswith('@') or line.startswith('if __name__')):
            in_function = False
            new_lines.append(line)
            continue
        
        # Ищем старый блок внутри функции
        # Признаки старого блока:
        # 1. generation_type = state_data.get('generation_type', 'music')
        # 2. НЕ содержит комментарии про "умную логику" или "приоритет"
        
        if in_function and "generation_type = state_data.get('generation_type'" in line:
            # Проверяем что это СТАРЫЙ блок (не умная логика)
            # Старый блок - это просто присваивание без комментариев
            if i > 0 and 'УМНОЕ ОПРЕДЕЛЕНИЕ' not in lines[i-1] and 'Приоритет' not in lines[i-1]:
                log(f"Найдена старая логика на строке {i+1}", "🔍")
                in_old_block = True
                removed_lines += 1
                continue
        
        # Пропускаем строки старого блока
        if in_old_block:
            # Признаки конца старого блока:
            # - Пустая строка
            # - Комментарий про умную логику
            # - lyrics = state_data.get
            
            if not line.strip():
                in_old_block = False
                new_lines.append(line)
                continue
            
            if 'УМНОЕ ОПРЕДЕЛЕНИЕ' in line or 'Приоритет' in line or "lyrics = state_data.get" in line:
                in_old_block = False
                new_lines.append(line)
                continue
            
            # Пропускаем строку старого блока
            removed_lines += 1
            continue
        
        # Исправляем logger на logging (если нужно)
        # Но сначала проверяем есть ли определение logger
        if i < 30 and 'logger = ' in line and 'logging.getLogger' not in line:
            # Исправляем определение
            line = line.replace('logger = logger', 'logger = logging.getLogger(__name__)')
        
        new_lines.append(line)
    
    log(f"Удалено строк: {removed_lines}", "✅")
    
    # 5. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # 6. Проверка синтаксиса
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
        
        print("=" * 60)
        log("ТОЧЕЧНАЯ ОЧИСТКА ВЫПОЛНЕНА!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print(f"\nУдалено строк: {removed_lines}")
        print("\nТеперь выполните:")
        print("  sudo systemctl restart albimusic-bot")
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
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
