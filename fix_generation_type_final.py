#!/usr/bin/env python3
"""
Финальное исправление: установка generation_type='song' во всех нужных местах
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
    backup_path = f"{FILE_PATH}.backup_final_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def fix_generation_type(content):
    """Исправляет установку generation_type в нужных местах"""
    
    changes_made = []
    
    # ========== ИСПРАВЛЕНИЕ 1: process_song_lyrics ==========
    # Ищем: await state.update_data(lyrics=message.text)
    # Внутри функции process_song_lyrics
    
    pattern1 = r'(async def process_song_lyrics.*?)(await state\.update_data\(lyrics=message\.text\))'
    
    def replacer1(match):
        func_part = match.group(1)
        update_line = match.group(2)
        
        # Проверяем, есть ли уже generation_type
        if 'generation_type' in update_line:
            return match.group(0)
        
        # Добавляем generation_type
        new_line = update_line.replace(
            'lyrics=message.text)',
            "lyrics=message.text, generation_type='song')"
        )
        
        changes_made.append("process_song_lyrics")
        return func_part + new_line
    
    content = re.sub(pattern1, replacer1, content, flags=re.DOTALL)
    
    # ========== ИСПРАВЛЕНИЕ 2: process_song_style ==========
    # Ищем: await state.update_data(style=message.text)
    # Внутри функции process_song_style
    
    pattern2 = r'(async def process_song_style.*?)(await state\.update_data\(style=message\.text\))'
    
    def replacer2(match):
        func_part = match.group(1)
        update_line = match.group(2)
        
        # Проверяем, есть ли уже generation_type
        if 'generation_type' in update_line:
            return match.group(0)
        
        # Добавляем generation_type
        new_line = update_line.replace(
            'style=message.text)',
            "style=message.text, generation_type='song')"
        )
        
        changes_made.append("process_song_style")
        return func_part + new_line
    
    content = re.sub(pattern2, replacer2, content, flags=re.DOTALL)
    
    # ========== ИСПРАВЛЕНИЕ 3: Другие возможные места ==========
    # Ищем все update_data с lyrics или style, но без generation_type
    
    # Паттерн для lyrics без generation_type
    pattern3 = r'await state\.update_data\(([^)]*lyrics=[^)]*)\)'
    
    matches = list(re.finditer(pattern3, content))
    for match in reversed(matches):
        line = match.group(0)
        inner = match.group(1)
        
        # Если уже есть generation_type - пропускаем
        if 'generation_type' in inner:
            continue
        
        # Добавляем generation_type
        new_line = line.replace(')', ", generation_type='song')")
        content = content[:match.start()] + new_line + content[match.end():]
        changes_made.append("additional lyrics update")
    
    return content, changes_made

def main():
    print("=" * 60)
    print("ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ generation_type")
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
        content = f.read()
    
    original_content = content
    
    # 4. Применение исправлений
    log("Применение исправлений...")
    content, changes = fix_generation_type(content)
    
    if not changes:
        log("⚠️  Изменения не требуются (уже исправлено)", "⚠️")
        return True
    
    log(f"Внесено изменений: {len(changes)}", "✅")
    for change in changes:
        log(f"  • {change}", "  ")
    
    # 5. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        log("ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print(f"\nИзменено функций: {len(set(changes))}")
        for func in set(changes):
            print(f"  ✅ {func}")
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
