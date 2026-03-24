#!/usr/bin/env python3
"""
Комплексная очистка main_with_payments.py:
1. Удаление дубликатов if __name__ == '__main__'
2. Добавление обработчика process_generation_mode
3. Очистка структуры файла
"""

import os
import re
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    """Создает backup с timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_cleanup_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def find_all_main_blocks(content):
    """Находит все блоки if __name__ == '__main__'"""
    pattern = r'if __name__ == ["\']__main__["\']:'
    matches = list(re.finditer(pattern, content))
    return matches

def extract_main_block(content, start_pos):
    """Извлекает полный блок if __name__ от start_pos до конца или следующего def/class"""
    lines = content[start_pos:].split('\n')
    
    block_lines = [lines[0]]  # if __name__ строка
    
    # Собираем все строки с отступом (входящие в блок)
    for line in lines[1:]:
        # Если строка пустая или с отступом - часть блока
        if not line.strip() or line.startswith((' ', '\t')):
            block_lines.append(line)
        # Если встретили новое определение на уровне модуля - конец блока
        elif line.startswith(('def ', 'class ', '@', 'if __name__')):
            break
        else:
            # Непонятная строка на уровне модуля - тоже конец блока
            break
    
    return '\n'.join(block_lines)

def remove_handler_duplicates(content):
    """Удаляет дубликаты обработчика process_generation_mode"""
    pattern = r'@dp\.callback_query_handler.*?mode_.*?\n.*?async def process_generation_mode.*?\n(?:    .*?\n)*?(?=\n(?:@|async def|if __name__|def [a-z_]|class |$))'
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if len(matches) > 1:
        log(f"Найдено {len(matches)} дубликатов обработчика", "⚠️")
        # Удаляем все кроме первого
        for match in reversed(matches[1:]):
            content = content[:match.start()] + content[match.end():]
        log("Дубликаты обработчика удалены", "✅")
    elif len(matches) == 1:
        log("Найден один обработчик (норма)", "✅")
    else:
        log("Обработчик не найден", "ℹ️")
    
    return content

def main():
    print("=" * 60)
    print("ОЧИСТКА И ИСПРАВЛЕНИЕ СТРУКТУРЫ ФАЙЛА")
    print("=" * 60)
    
    # 1. Проверка файла
    log("Проверка файла...")
    if not os.path.exists(FILE_PATH):
        log(f"ОШИБКА: Файл не найден", "❌")
        return False
    
    # 2. Создание backup
    log("Создание backup...")
    backup_path = create_backup()
    
    # 3. Чтение файла
    log("Чтение файла...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 4. Поиск всех блоков if __name__
    log("Поиск блоков if __name__...")
    main_blocks = find_all_main_blocks(content)
    
    if len(main_blocks) == 0:
        log("ОШИБКА: Не найден блок if __name__", "❌")
        return False
    
    log(f"Найдено блоков if __name__: {len(main_blocks)}", "ℹ️")
    
    if len(main_blocks) > 1:
        log("Обнаружены дубликаты!", "⚠️")
        
        # Находим самый полный/последний блок
        blocks_data = []
        for i, match in enumerate(main_blocks):
            block = extract_main_block(content, match.start())
            blocks_data.append({
                'index': i,
                'start': match.start(),
                'block': block,
                'length': len(block)
            })
            log(f"  Блок {i+1}: позиция {match.start()}, длина {len(block)} символов", "  ")
        
        # Выбираем самый длинный блок (обычно самый полный)
        best_block = max(blocks_data, key=lambda x: x['length'])
        log(f"Выбран блок {best_block['index']+1} как основной", "✅")
        
        # Удаляем все блоки if __name__
        for match in reversed(main_blocks):
            # Находим конец блока
            block_content = extract_main_block(content, match.start())
            block_end = match.start() + len(block_content)
            content = content[:match.start()] + content[block_end:]
        
        log("Все блоки if __name__ удалены", "✅")
        
        # Добавляем лучший блок в конец
        content = content.rstrip() + '\n\n\n' + best_block['block'] + '\n'
        log("Основной блок if __name__ добавлен в конец файла", "✅")
    
    # 5. Удаление дубликатов обработчика
    log("Проверка дубликатов обработчика...")
    content = remove_handler_duplicates(content)
    
    # 6. Проверка наличия обработчика
    log("Проверка обработчика process_generation_mode...")
    has_handler = 'def process_generation_mode' in content
    
    if not has_handler:
        log("Обработчик не найден, добавляем", "ℹ️")
        
        # Находим место перед if __name__
        match = re.search(r'if __name__ == ["\']__main__["\']:', content)
        if match:
            insertion_point = match.start()
            
            handler_code = '''
# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора режима генерации"""
    await callback_query.answer()
    mode = callback_query.data.replace('mode_', '')
    mode_name = 'Точный режим' if mode == 'exact' else 'Творческий режим'
    logger.info(f"User {callback_query.from_user.id} selected mode: {mode}")
    await callback_query.message.answer(f"✅ Выбран: {mode_name}")
    await state.finish()


'''
            content = content[:insertion_point] + handler_code + content[insertion_point:]
            log("Обработчик добавлен", "✅")
    else:
        log("Обработчик уже существует", "✅")
    
    # 7. Очистка лишних пустых строк
    log("Очистка форматирования...")
    # Убираем более 3 подряд идущих пустых строк
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    log("Форматирование очищено", "✅")
    
    # 8. Сохранение во временный файл
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 9. Проверка синтаксиса
    log("Проверка синтаксиса...")
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'py_compile', temp_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("Синтаксис корректен", "✅")
        
        # Сохраняем файл
        shutil.move(temp_file, FILE_PATH)
        
        # Финальная проверка
        result = subprocess.run(
            ['python3', '-m', 'py_compile', FILE_PATH],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("=" * 60)
            log("ФАЙЛ УСПЕШНО ОЧИЩЕН И ИСПРАВЛЕН!", "✅")
            print("=" * 60)
            print(f"\nBackup: {backup_path}")
            print("\nИзменения:")
            print(f"  • Удалено дубликатов if __name__: {len(main_blocks) - 1}")
            print(f"  • Обработчик: {'добавлен' if not has_handler else 'проверен'}")
            print(f"  • Форматирование: очищено")
            print("\nТеперь выполните:")
            print("  sudo systemctl restart albimusic-bot")
            return True
        else:
            log("ОШИБКА финальной проверки", "❌")
            print(result.stderr)
            shutil.copy2(backup_path, FILE_PATH)
            return False
    else:
        log("ОШИБКА: Синтаксические ошибки в новом коде", "❌")
        print(result.stderr)
        os.remove(temp_file)
        log("Файл не изменен", "ℹ️")
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
