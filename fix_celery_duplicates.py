#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов функции translate_style_to_english() 
из celery_tasks.py и объединения всех словарей MUSIC_STYLE_TRANSLATIONS
"""

import re
import os
from datetime import datetime

# Конфигурация
FILE_PATH = '/root/albimusic-bot/celery_tasks.py'

def main():
    print("🔧 СКРИПТ ИСПРАВЛЕНИЯ celery_tasks.py")
    print("=" * 50)
    
    # 1. Создаем бэкап
    BACKUP_PATH = f'/root/albimusic-bot/celery_tasks_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    print(f"\n📦 Создание бэкапа: {BACKUP_PATH}")
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            original_content = f.read()

        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print("✅ Бэкап создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return
    
    # Простой подход: удаляем дубликаты вручную
    # Функции находятся на строках: 180, 286, 392, 498, 551
    # Оставляем строку 74
    
    lines = original_content.split('\n')
    print(f"\n📖 Исходный файл: {len(lines)} строк")
    
    # Простой метод: находим начало и конец каждой функции
    # Функция начинается с "def translate_style_to_english(russian_style):"
    # и заканчивается перед следующим "def " или концом файла
    
    # Найдем все строки с определением функции
    func_starts = []
    for i, line in enumerate(lines):
        if 'def translate_style_to_english(russian_style):' in line:
            func_starts.append(i)
    
    print(f"🔍 Найдено функций: {len(func_starts)} на строках: {func_starts}")
    
    if len(func_starts) <= 1:
        print("✅ Дубликатов не найдено, файл уже исправлен")
        return
    
    # Найдем конец каждой функции
    func_ranges = []
    for start in func_starts:
        end = start
        for i in range(start + 1, len(lines)):
            # Если нашли начало другой функции или конец файла
            if i < len(lines) - 1 and lines[i+1].strip().startswith('def '):
                end = i
                break
            if i == len(lines) - 1:
                end = i
                break
            # Если нашли начало другого блока
            if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t') and not lines[i].startswith('#'):
                # Проверяем, не начало ли это новой функции/класса
                if not lines[i].startswith('class ') and not lines[i].startswith('def ') and not lines[i].startswith('@'):
                    end = i - 1
                    break
        func_ranges.append((start, end))
    
    print(f"📊 Диапазоны функций:")
    for i, (start, end) in enumerate(func_ranges):
        print(f"   Функция #{i+1}: строки {start+1}-{end+1}")
    
    # Оставляем первую функцию, удаляем остальные
    keep_range = func_ranges[0]
    remove_ranges = func_ranges[1:]
    
    print(f"\n✅ Оставляем функцию: строки {keep_range[0]+1}-{keep_range[1]+1}")
    print(f"🗑️  Удаляем {len(remove_ranges)} дубликатов:")
    for start, end in remove_ranges:
        print(f"   - строки {start+1}-{end+1}")
    
    # Собираем все словари MUSIC_STYLE_TRANSLATIONS
    all_translations = {}
    
    # Ищем словари в исходном контенте
    dict_pattern = r'MUSIC_STYLE_TRANSLATIONS\s*=\s*\{([^}]+(?:\}[^}]+)*)\}'
    matches = re.finditer(dict_pattern, original_content, re.DOTALL)
    
    for match in matches:
        dict_content = match.group(1)
        # Ищем все пары ключ-значение
        pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', dict_content)
        for key, value in pairs:
            # Пропускаем некорректные ключи
            if 'logger' not in key and 'Authorization' not in key and 'Content-Type' not in key:
                all_translations[key] = value
    
    print(f"\n📚 Собрано переводов: {len(all_translations)}")
    
    # Создаем новый файл
    new_lines = []
    
    # Копируем все до второй функции
    second_func_start = func_starts[1] if len(func_starts) > 1 else len(lines)
    for i in range(second_func_start):
        new_lines.append(lines[i])
    
    # Добавляем объединенный словарь
    new_lines.append('\n# ' + '=' * 60)
    new_lines.append('# ОБЪЕДИНЕННЫЙ СЛОВАРЬ ПЕРЕВОДОВ МУЗЫКАЛЬНЫХ СТИЛЕЙ')
    new_lines.append('# ' + '=' * 60)
    new_lines.append('MUSIC_STYLE_TRANSLATIONS = {')
    
    # Сортируем ключи для читаемости
    sorted_keys = sorted(all_translations.keys())
    for key in sorted_keys:
        new_lines.append(f'    "{key}": "{all_translations[key]}",')
    
    new_lines.append('}\n')
    
    # Пропускаем все оставшиеся дубликаты и добавляем хвост файла
    # Найдем конец последней функции
    last_func_end = func_ranges[-1][1] if func_ranges else len(lines)
    
    for i in range(last_func_end + 1, len(lines)):
        new_lines.append(lines[i])
    
    # Записываем новый файл
    print(f"\n💾 Запись исправленного файла...")
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"✅ Файл успешно записан: {len(new_lines)} строк")
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        return
    
    # Проверка синтаксиса
    print("\n🔍 Проверка синтаксиса...")
    try:
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', FILE_PATH], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Синтаксис корректен")
        else:
            print(f"❌ Ошибка синтаксиса:\n{result.stderr}")
    except Exception as e:
        print(f"⚠️  Не удалось проверить синтаксис: {e}")
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТ:")
    print(f"Исходный файл: {len(lines)} строк")
    print(f"Новый файл: {len(new_lines)} строк")
    print(f"Удалено строк: {len(lines) - len(new_lines)}")
    print(f"Удалено функций: {len(remove_ranges)}")
    print(f"Объединено переводов: {len(all_translations)}")
    print(f"\n✅ ВСЕ ДУБЛИКАТЫ УДАЛЕНЫ!")

if __name__ == "__main__":
    main()
