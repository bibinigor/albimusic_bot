#!/usr/bin/env python3
"""
Скрипт для очистки словаря MUSIC_STYLE_TRANSLATIONS 
от некорректных записей в celery_tasks.py
"""

import re
import os
from datetime import datetime

# Конфигурация
FILE_PATH = '/root/albimusic-bot/celery_tasks.py'

def main():
    print("🔧 СКРИПТ ОЧИСТКИ СЛОВАРЯ MUSIC_STYLE_TRANSLATIONS")
    print("=" * 60)
    
    # Создаем бэкап
    BACKUP_PATH = f'/root/albimusic-bot/celery_tasks_clean_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    print(f"\n📦 Создание бэкапа...")
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            original_content = f.read()

        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ Бэкап создан: {BACKUP_PATH}")
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return
    
    # Простая очистка: удаляем все строки с logger, эмодзи и кодом из словаря
    lines = original_content.split('\n')
    new_lines = []
    in_dict = False
    
    for line in lines:
        # Находим начало словаря
        if 'MUSIC_STYLE_TRANSLATIONS = {' in line:
            in_dict = True
            new_lines.append(line)
            continue
        
        # Находим конец словаря
        if in_dict and line.strip() == '}':
            in_dict = False
            new_lines.append(line)
            continue
        
        # Если внутри словаря
        if in_dict:
            # Проверяем, не является ли строка некорректной
            invalid_indicators = [
                'logger',
                'error',
                'warning',
                'Exception',
                'def ',
                'return',
                'try:',
                'except',
                'if ',
                '❌',
                '✅',
                '⚠️',
                '🔥',
                'f"',
                "f'",
                '{user_id}',
                '{e}',
                '{response.',
            ]
            
            is_invalid = any(indicator in line for indicator in invalid_indicators)
            
            # Также проверяем, является ли это корректной парой ключ-значение
            # Формат: "ключ": "значение"
            if '"' in line and ':' in line and not is_invalid:
                # Проверяем наличие кавычек и двоеточия
                if line.count('"') >= 4 and ':' in line:
                    new_lines.append(line)
                else:
                    print(f"   🗑️  Пропускаем некорректную строку: {line[:50]}...")
            elif not is_invalid and (line.strip().startswith('#') or not line.strip()):
                # Комментарии и пустые строки оставляем
                new_lines.append(line)
            else:
                print(f"   🗑️  Удаляем некорректную строку: {line[:50]}...")
        else:
            # Вне словаря оставляем как есть
            new_lines.append(line)
    
    # Записываем файл
    print(f"\n💾 Запись исправленного файла...")
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print("✅ Файл успешно записан")
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        return
    
    # Проверка синтаксиса
    print(f"\n🔍 Проверка синтаксиса Python...")
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'py_compile', FILE_PATH],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ Синтаксис корректен")
    else:
        print(f"❌ Ошибка синтаксиса:\n{result.stderr}")
        return
    
    print("\n" + "=" * 60)
    print("✅ ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО!")

if __name__ == "__main__":
    main()
