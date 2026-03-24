#!/usr/bin/env python3
"""
Хирургическое исправление функции process_generation_mode:
1. Вставка умной логики после state_data
2. Исправление отступов
3. Сохранение всего остального кода
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
    backup_path = f"{FILE_PATH}.backup_surgical_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_smart_logic_block():
    """Возвращает блок умной логики с правильными отступами"""
    return '''
        # ========== УМНОЕ ОПРЕДЕЛЕНИЕ ТИПА ГЕНЕРАЦИИ ==========
        # Приоритет 1: Проверяем наличие lyrics (если есть → песня)
        lyrics = state_data.get('lyrics', '').strip()
        
        # Приоритет 2: Проверяем наличие prompt (если есть → музыка)
        prompt = state_data.get('prompt', '').strip()
        
        # Приоритет 3: Fallback на явное указание типа
        explicit_type = state_data.get('generation_type', None)
        
        # Определяем финальный тип
        if lyrics:
            generation_type = 'song'
            logging.info(f"🎤 Detected SONG generation (lyrics: {len(lyrics)} chars)")
        elif prompt:
            generation_type = 'music'
            logging.info(f"🎵 Detected MUSIC generation (prompt: {len(prompt)} chars)")
        elif explicit_type:
            generation_type = explicit_type
            logging.info(f"📋 Using explicit type: {explicit_type}")
        else:
            logging.error("❌ Cannot determine generation type!")
            await callback_query.message.answer(
                "❌ Ошибка: не удалось определить тип генерации\\n"
                "Попробуйте начать заново с 🎵 Создать песню"
            )
            await state.finish()
            return
        
        # Получаем дополнительные параметры
        style = state_data.get('style', '').strip()
'''

def surgical_insert_logic(content):
    """Хирургически вставляет умную логику и исправляет отступы"""
    
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    in_target_function = False
    state_data_found = False
    logic_inserted = False
    function_indent = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Находим начало функции
        if 'async def process_generation_mode' in line:
            in_target_function = True
            function_indent = len(line) - len(line.lstrip())
            log(f"Функция найдена на строке {i+1}, отступ: {function_indent}", "✅")
            new_lines.append(line)
            i += 1
            continue
        
        # Ищем state_data = await state.get_data()
        if in_target_function and not logic_inserted and 'state_data = await state.get_data()' in line:
            state_data_found = True
            log(f"Найден state_data на строке {i+1}", "🔍")
            
            # Добавляем строку с state_data
            new_lines.append(line)
            
            # Пропускаем следующие пустые строки
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            
            # Вставляем умную логику
            smart_logic = get_smart_logic_block()
            new_lines.extend(smart_logic.split('\n'))
            
            log("Умная логика вставлена", "✅")
            logic_inserted = True
            
            # Теперь пропускаем весь битый код до следующей понятной структуры
            # Ищем либо следующий декоратор, либо if generation_type ==, либо await callback_query.message.answer
            
            skip_mode = True
            while i < len(lines) and skip_mode:
                current = lines[i].strip()
                
                # Останавливаемся на следующем значимом блоке
                if current.startswith('@dp.'):
                    skip_mode = False
                    break
                elif current.startswith('async def'):
                    skip_mode = False
                    break
                elif 'await callback_query.message.answer' in current and 'Генерация вашей композиции началась' in current:
                    # Это наше сообщение пользователю - сохраняем
                    skip_mode = False
                    break
                elif current.startswith('if generation_type ==') or current.startswith('if __name__'):
                    skip_mode = False
                    break
                
                log(f"Пропускаем битую строку {i+1}: {current[:60]}", "🗑️")
                i += 1
            
            continue
        
        # Если мы внутри функции и логика уже вставлена
        if in_target_function and logic_inserted:
            # Проверяем, не вышли ли мы из функции
            if line.strip() and not line.startswith(' '):
                in_target_function = False
            elif '@dp.' in line or 'async def' in line:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= function_indent:
                    in_target_function = False
        
        new_lines.append(line)
        i += 1
    
    if not logic_inserted:
        log("Умная логика не была вставлена (state_data не найден)", "⚠️")
        return content, False
    
    return '\n'.join(new_lines), True

def fix_indentation_errors(content):
    """Исправляет очевидные ошибки отступов"""
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        # Если строка начинается с неправильного количества пробелов
        if line and line[0] == ' ':
            # Проверяем кратность 4
            spaces = len(line) - len(line.lstrip())
            if spaces % 4 != 0:
                # Округляем до ближайшего кратного 4
                correct_spaces = ((spaces + 2) // 4) * 4
                fixed_line = ' ' * correct_spaces + line.lstrip()
                log(f"Исправлен отступ на строке {i+1}: {spaces} → {correct_spaces}", "🔧")
                new_lines.append(fixed_line)
                continue
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)

def main():
    print("=" * 60)
    print("ХИРУРГИЧЕСКОЕ ИСПРАВЛЕНИЕ ФУНКЦИИ")
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
    
    # 4. Проверка наличия умной логики
    if 'УМНОЕ ОПРЕДЕЛЕНИЕ ТИПА ГЕНЕРАЦИИ' in content:
        log("Умная логика уже присутствует", "ℹ️")
        
        # Только исправляем отступы
        log("Исправление отступов...")
        content = fix_indentation_errors(content)
        
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Проверка синтаксиса
        import subprocess
        result = subprocess.run(
            ['python3', '-m', 'py_compile', FILE_PATH],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            log("Синтаксис корректен", "✅")
            return True
        else:
            log("Ошибка синтаксиса:", "❌")
            print(result.stderr)
            return False
    
    # 5. Вставка умной логики
    log("Вставка умной логики...")
    new_content, modified = surgical_insert_logic(content)
    
    if not modified:
        log("Не удалось вставить логику", "❌")
        return False
    
    # 6. Исправление отступов
    log("Исправление отступов...")
    new_content = fix_indentation_errors(new_content)
    
    # 7. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 8. Проверка синтаксиса
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
        log("ФУНКЦИЯ ИСПРАВЛЕНА!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\n📋 Что сделано:")
        print("  ✅ Вставлена умная логика определения типа")
        print("  ✅ Удален битый код")
        print("  ✅ Исправлены отступы")
        print("  ✅ Сохранены все исправления")
        print("\n🚀 Следующий шаг:")
        print("  sudo systemctl restart albimusic-bot")
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print("\n" + "=" * 60)
        print("ДЕТАЛИ ОШИБКИ:")
        print("=" * 60)
        print(result.stderr)
        
        # Показываем контекст
        error_match = re.search(r'line (\d+)', result.stderr)
        if error_match:
            error_line = int(error_match.group(1))
            print(f"\nКонтекст (строки {error_line-5} - {error_line+5}):")
            print("=" * 60)
            
            with open(temp_file, 'r') as f:
                temp_lines = f.readlines()
            
            for i in range(max(0, error_line-6), min(len(temp_lines), error_line+5)):
                marker = "→→→" if i == error_line - 1 else "   "
                indent = len(temp_lines[i]) - len(temp_lines[i].lstrip())
                print(f"{marker} {i+1:4d} [{indent:2d}] | {temp_lines[i].rstrip()}")
        
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
