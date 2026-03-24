#!/usr/bin/env python3
"""
Исправление незакрытого try блока в функции process_generation_mode
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
    backup_path = f"{FILE_PATH}.backup_try_fix_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def analyze_try_blocks(content):
    """Анализирует структуру try-except блоков"""
    lines = content.split('\n')
    
    try_blocks = []
    except_blocks = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('try:'):
            indent = len(line) - len(line.lstrip())
            try_blocks.append((i + 1, indent, line))
        elif stripped.startswith('except'):
            indent = len(line) - len(line.lstrip())
            except_blocks.append((i + 1, indent, line))
    
    log(f"Найдено try блоков: {len(try_blocks)}", "ℹ️")
    log(f"Найдено except блоков: {len(except_blocks)}", "ℹ️")
    
    return try_blocks, except_blocks

def find_function_bounds(lines, func_name):
    """Находит начало и конец функции"""
    start_line = None
    end_line = None
    func_indent = None
    
    for i, line in enumerate(lines):
        if f'async def {func_name}' in line:
            start_line = i
            func_indent = len(line) - len(line.lstrip())
            log(f"Функция {func_name} найдена на строке {i+1}", "✅")
            break
    
    if start_line is None:
        return None, None
    
    # Ищем конец функции (следующая функция или конец файла)
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        
        # Если встретили новую функцию на том же уровне - это конец
        if line.strip() and not line.startswith(' '):
            end_line = i - 1
            break
        
        # Если встретили декоратор на том же уровне - это конец
        if line.strip().startswith('@') and (len(line) - len(line.lstrip())) == func_indent:
            end_line = i - 1
            break
        
        # Если встретили async def на том же уровне - это конец
        if 'async def' in line and (len(line) - len(line.lstrip())) == func_indent:
            end_line = i - 1
            break
    
    if end_line is None:
        end_line = len(lines) - 1
    
    log(f"Функция занимает строки {start_line+1}-{end_line+1}", "ℹ️")
    return start_line, end_line

def fix_try_except_in_function(content):
    """Исправляет try-except блоки в функции"""
    
    lines = content.split('\n')
    
    # Находим функцию
    start, end = find_function_bounds(lines, 'process_generation_mode')
    
    if start is None:
        log("Функция не найдена", "❌")
        return content, False
    
    # Анализируем try-except внутри функции
    func_lines = lines[start:end+1]
    
    try_found = False
    try_line_idx = None
    try_indent = None
    except_found = False
    
    for i, line in enumerate(func_lines):
        stripped = line.strip()
        
        if stripped.startswith('try:'):
            try_found = True
            try_line_idx = i
            try_indent = len(line) - len(line.lstrip())
            log(f"Try блок на строке {start+i+1} (отступ: {try_indent})", "🔍")
        
        if stripped.startswith('except') and try_found:
            # Проверяем, что except на правильном уровне отступа
            except_indent = len(line) - len(line.lstrip())
            if except_indent == try_indent:
                except_found = True
                log(f"Соответствующий except на строке {start+i+1}", "✅")
                break
    
    if try_found and not except_found:
        log("Найден незакрытый try блок!", "⚠️")
        
        # Находим последнюю строку функции с кодом (не пустую)
        last_code_line = end
        for i in range(end, start, -1):
            if lines[i].strip() and not lines[i].strip().startswith('#'):
                last_code_line = i
                break
        
        # Определяем отступ для except блока (такой же как у try)
        except_indent = try_indent
        
        # Создаем except блок
        except_block = [
            '',
            ' ' * except_indent + 'except Exception as e:',
            ' ' * (except_indent + 4) + 'logging.error(f"❌ Critical error in process_generation_mode: {e}", exc_info=True)',
            ' ' * (except_indent + 4) + 'try:',
            ' ' * (except_indent + 8) + 'await callback_query.message.answer(',
            ' ' * (except_indent + 12) + '"❌ Произошла критическая ошибка\\n"',
            ' ' * (except_indent + 12) + '"Попробуйте ещё раз или обратитесь в поддержку"',
            ' ' * (except_indent + 8) + ')',
            ' ' * (except_indent + 8) + 'await state.finish()',
            ' ' * (except_indent + 4) + 'except:',
            ' ' * (except_indent + 8) + 'pass',
        ]
        
        # Вставляем except блок после последней строки функции
        lines[last_code_line+1:last_code_line+1] = except_block
        
        log(f"Добавлен except блок после строки {last_code_line+1}", "✅")
        
        return '\n'.join(lines), True
    
    elif try_found and except_found:
        log("Try-except блок уже корректен", "✅")
        return content, False
    
    else:
        log("Try блок не найден в функции", "ℹ️")
        return content, False

def main():
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ TRY-EXCEPT БЛОКА")
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
    
    # 4. Анализ
    log("Анализ структуры...")
    analyze_try_blocks(content)
    
    # 5. Исправление
    log("Исправление try-except...")
    new_content, modified = fix_try_except_in_function(content)
    
    if not modified:
        log("Изменений не требуется", "ℹ️")
        return True
    
    # 6. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 7. Проверка синтаксиса
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
        log("TRY-EXCEPT ИСПРАВЛЕН!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\n📋 Что исправлено:")
        print("  ✅ Добавлен except блок для try")
        print("  ✅ Добавлена обработка критических ошибок")
        print("  ✅ Сохранена вся умная логика")
        print("\n🚀 Следующий шаг:")
        print("  sudo systemctl restart albimusic-bot")
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print("\n" + "=" * 60)
        print("ДЕТАЛИ ОШИБКИ:")
        print("=" * 60)
        print(result.stderr)
        
        # Показываем контекст ошибки
        error_match = re.search(r'line (\d+)', result.stderr)
        if error_match:
            error_line = int(error_match.group(1))
            print(f"\nКонтекст ошибки (строки {error_line-3} - {error_line+3}):")
            print("=" * 60)
            
            with open(temp_file, 'r') as f:
                temp_lines = f.readlines()
            
            for i in range(max(0, error_line-4), min(len(temp_lines), error_line+3)):
                marker = "→→→" if i == error_line - 1 else "   "
                print(f"{marker} {i+1:4d} | {temp_lines[i].rstrip()}")
        
        os.remove(temp_file)
        log("Файл не изменен", "⚠️")
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
