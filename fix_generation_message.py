#!/usr/bin/env python3
"""
Исправление сообщения во время генерации
"""

import os
import re
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

def fix_message():
    # Backup
    backup = f"{FILE_PATH}.backup_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(FILE_PATH, backup)
    print(f"Backup: {backup}")
    
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем первое сообщение
    old_msg1 = '''await callback_query.message.answer(
            f"{type_emoji} Начинаем генерацию {type_text}\\\\n"
            f"✅ Режим: {mode_name}\\\\n\\\\n"
            "⏱ Подготовка займёт 1-2 минуты..."
        )'''
    
    new_msg1 = '''await callback_query.message.answer(
            "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
        )'''
    
    # Исправляем второе сообщение (песня)
    old_msg2 = '''await callback_query.message.answer(
                    f"✅ Задача создания песни запущена\\\\n"
                    f"📋 ID: {task.id[:8]}...\\\\n\\\\n"
                    f"Ожидайте результат в течение 2-3 минут"
                )'''
    
    new_msg2 = '''await callback_query.message.answer(
                    "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
                )'''
    
    # Исправляем третье сообщение (музыка)
    old_msg3 = '''await callback_query.message.answer(
                    f"✅ Задача создания музыки запущена\\\\n"
                    f"📋 ID: {task.id[:8]}...\\\\n\\\\n"
                    f"Ожидайте результат в течение 2-3 минут"
                )'''
    
    new_msg3 = '''await callback_query.message.answer(
                    "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
                )'''
    
    changes = 0
    
    if old_msg1 in content:
        content = content.replace(old_msg1, new_msg1)
        changes += 1
        print("✅ Исправлено первое сообщение")
    
    if old_msg2 in content:
        content = content.replace(old_msg2, new_msg2)
        changes += 1
        print("✅ Исправлено сообщение для песни")
    
    if old_msg3 in content:
        content = content.replace(old_msg3, new_msg3)
        changes += 1
        print("✅ Исправлено сообщение для музыки")
    
    if changes == 0:
        print("⚠️  Сообщения не найдены, попробуем альтернативный поиск")
        
        # Альтернативный поиск по фрагментам
        content = re.sub(r'Начинаем генерацию.*?Подготовка займёт 1-2 минуты\.\.\.', 
                        '⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат', 
                        content)
        
        content = re.sub(r'Задача создания песни запущена.*?Ожидайте результат в течение 2-3 минут', 
                        '⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат', 
                        content)
        
        content = re.sub(r'Задача создания музыки запущена.*?Ожидайте результат в течение 2-3 минут', 
                        '⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат', 
                        content)
        
        print("✅ Сообщения исправлены (альтернативный метод)")
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Исправлено сообщений: {changes}")
    print("Проверка синтаксиса...")
    
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', FILE_PATH],
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Синтаксис корректен")
        print("\nПерезапусти бота: sudo systemctl restart albimusic-bot")
    else:
        print("❌ Ошибка синтаксиса:")
        print(result.stderr)
        print("Восстанавливаем из backup...")
        shutil.copy2(backup, FILE_PATH)

if __name__ == "__main__":
    try:
        fix_message()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
