#!/usr/bin/env python3
"""
Быстрое исправление: result[0][0] → result[0] или result
"""

import os
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

def fix_result_access():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем result[0][0] на result[0]
    old_code1 = """                if result and len(result) > 0:
                    db_id = result[0][0]
                    logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")"""
    
    new_code1 = """                if result:
                    # result может быть int (ID) или кортеж (ID,)
                    db_id = result[0] if isinstance(result, tuple) else result
                    logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")"""
    
    # Исправляем result[0][0] на result[0]
    old_code2 = """                if result and len(result) > 0:
                    db_id = result[0][0]
                    logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")"""
    
    new_code2 = """                if result:
                    # result может быть int (ID) или кортеж (ID,)
                    db_id = result[0] if isinstance(result, tuple) else result
                    logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")"""
    
    if old_code1 in content:
        content = content.replace(old_code1, new_code1)
        print("✅ Исправлен первый блок")
    
    if old_code2 in content:
        content = content.replace(old_code2, new_code2)
        print("✅ Исправлен второй блок")
    
    # Backup
    backup = f"{FILE_PATH}.backup_quick_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(FILE_PATH, backup)
    print(f"Backup: {backup}")
    
    # Сохраняем
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл исправлен")
    print("Перезапусти бота: sudo systemctl restart albimusic-bot")

if __name__ == "__main__":
    try:
        fix_result_access()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
