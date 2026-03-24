#!/usr/bin/env python3
"""
Простое построчное удаление старой логики
"""

import os
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

def log(msg):
    print(f"• {msg}")

def main():
    print("=" * 60)
    print("ПРОСТОЕ УДАЛЕНИЕ СТРОК")
    print("=" * 60)
    
    # Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = f"{FILE_PATH}.backup_simple_{timestamp}"
    shutil.copy2(FILE_PATH, backup)
    log(f"Backup: {backup}")
    
    # Читаем файл
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_process_generation_mode = False
    found_state_data = False
    found_smart_logic = False
    removed = 0
    
    for i, line in enumerate(lines):
        # Находим функцию
        if 'async def process_generation_mode' in line:
            in_process_generation_mode = True
            log(f"Найдена функция на строке {i+1}")
            new_lines.append(line)
            continue
        
        # Внутри функции
        if in_process_generation_mode:
            
            # Нашли получение state_data
            if 'state_data = await state.get_data()' in line:
                found_state_data = True
                new_lines.append(line)
                log(f"Найдено state_data на строке {i+1}")
                continue
            
            # После state_data до умной логики - УДАЛЯЕМ
            if found_state_data and not found_smart_logic:
                
                # Нашли начало умной логики - больше не удаляем
                if 'УМНОЕ ОПРЕДЕЛЕНИЕ' in line or 'Приоритет 1' in line or "lyrics = state_data.get('lyrics'" in line:
                    found_smart_logic = True
                    log(f"Найдена умная логика на строке {i+1}")
                    log(f"Удалено строк: {removed}")
                    in_process_generation_mode = False  # Дальше не трогаем
                    new_lines.append(line)
                    continue
                
                # Пропускаем пустые строки и комментарии между state_data и умной логикой
                if line.strip() == '' or line.strip().startswith('#'):
                    new_lines.append(line)
                    continue
                
                # Это старая логика - УДАЛЯЕМ
                removed += 1
                if removed <= 10:
                    log(f"  Удаляем строку {i+1}: {line.strip()[:60]}...")
                continue
        
        # Все остальное - оставляем
        new_lines.append(line)
    
    # Сохраняем
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # Проверка синтаксиса
    log("Проверка синтаксиса...")
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', temp_file],
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        log("✅ Синтаксис корректен")
        shutil.move(temp_file, FILE_PATH)
        print("=" * 60)
        print(f"✅ УДАЛЕНО {removed} СТРОК")
        print("=" * 60)
        print("Перезапустите бота:")
        print("  sudo systemctl restart albimusic-bot")
        return True
    else:
        print("❌ ОШИБКА:", result.stderr)
        os.remove(temp_file)
        shutil.copy2(backup, FILE_PATH)
        return False

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
