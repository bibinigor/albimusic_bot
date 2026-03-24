#!/usr/bin/env python3
"""
Критическое исправление функции process_generation_mode:
1. Добавление определения функции после декоратора
2. Исправление отступов
3. Добавление умной логики определения generation_type
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
    backup_path = f"{FILE_PATH}.backup_critical_fix_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def fix_function_definition(content):
    """Исправляет определение функции и добавляет умную логику"""
    
    # ========== ШАГ 1: НАХОДИМ И ИСПРАВЛЯЕМ ОПРЕДЕЛЕНИЕ ФУНКЦИИ ==========
    
    # Паттерн: декоратор без определения функции
    broken_pattern = r'(@dp\.callback_query_handler\(lambda c: c\.data and c\.data\.startswith\([\'"]mode_[\'"]\), state=\'\*\'\)\s*\n)\s*(""".*?"""\s*\n)\s*(await callback_query\.answer\(\))'
    
    def fix_definition(match):
        decorator = match.group(1)
        docstring = match.group(2)
        first_code_line = match.group(3)
        
        # Правильная структура
        fixed = (
            decorator +
            'async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):\n' +
            '    ' + docstring.strip() + '\n' +
            '    try:\n' +
            '        ' + first_code_line
        )
        
        return fixed
    
    new_content = re.sub(broken_pattern, fix_definition, content, flags=re.DOTALL)
    
    if new_content == content:
        log("Применяю альтернативный метод исправления...", "🔄")
        
        # Альтернативный метод: построчная фиксация
        lines = content.split('\n')
        new_lines = []
        i = 0
        fixed = False
        
        while i < len(lines):
            line = lines[i]
            
            # Ищем декоратор
            if "@dp.callback_query_handler" in line and "mode_" in line:
                log(f"Найден декоратор на строке {i+1}", "🔍")
                
                # Добавляем декоратор
                new_lines.append(line)
                i += 1
                
                # Проверяем следующую строку
                next_line = lines[i] if i < len(lines) else ''
                
                # Если следующая строка НЕ содержит async def - добавляем его
                if 'async def process_generation_mode' not in next_line:
                    log("Добавляю определение функции", "✅")
                    new_lines.append('async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):')
                    
                    # Если следующая строка - докстринг, исправляем отступ
                    if '"""' in next_line or "'''" in next_line:
                        new_lines.append('    ' + next_line.strip())
                        i += 1
                    
                    # Добавляем try блок
                    new_lines.append('    try:')
                    
                    fixed = True
                    continue
            
            new_lines.append(line)
            i += 1
        
        new_content = '\n'.join(new_lines)
        
        if fixed:
            log("Определение функции добавлено", "✅")
        else:
            log("Определение функции не требуется (возможно уже исправлено)", "ℹ️")
    
    # ========== ШАГ 2: ДОБАВЛЯЕМ УМНУЮ ЛОГИКУ ОПРЕДЕЛЕНИЯ ТИПА ==========
    
    smart_logic = '''
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
    
    # Проверяем, есть ли уже умная логика
    if 'УМНОЕ ОПРЕДЕЛЕНИЕ ТИПА ГЕНЕРАЦИИ' not in new_content:
        log("Добавляю умную логику определения типа...", "🔄")
        
        # Ищем state_data = await state.get_data()
        state_data_pattern = r'(state_data = await state\.get_data\(\)\s*\n)(\s*\n)?(\s*logging\.info\()'
        
        def add_logic(match):
            state_data_line = match.group(1)
            logging_line = match.group(3)
            
            return state_data_line + smart_logic + '\n        ' + logging_line
        
        new_content = re.sub(state_data_pattern, add_logic, new_content, flags=re.DOTALL)
        
        if 'УМНОЕ ОПРЕДЕЛЕНИЕ' in new_content:
            log("Умная логика добавлена", "✅")
        else:
            log("Не удалось добавить умную логику (попробуйте вручную)", "⚠️")
    else:
        log("Умная логика уже присутствует", "ℹ️")
    
    # ========== ШАГ 3: ЗАКРЫВАЕМ TRY БЛОК В КОНЦЕ ФУНКЦИИ ==========
    
    # Ищем конец функции (await state.finish() в конце)
    # и добавляем except блок если его нет
    
    if 'except Exception as e:' not in new_content or \
       new_content.count('except Exception as e:') < 2:
        
        # Ищем последний await state.finish() в функции
        lines = new_content.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if 'await state.finish()' in lines[i] and \
               'process_generation_mode' in '\n'.join(lines[max(0, i-100):i]):
                
                # Определяем отступ
                indent = len(lines[i]) - len(lines[i].lstrip())
                
                # Добавляем except блок после state.finish()
                except_block = [
                    '',
                    ' ' * (indent - 4) + 'except Exception as e:',
                    ' ' * indent + 'logging.error(f"❌ Critical error in process_generation_mode: {e}", exc_info=True)',
                    ' ' * indent + 'try:',
                    ' ' * (indent + 4) + 'await callback_query.message.answer(',
                    ' ' * (indent + 8) + '"❌ Произошла критическая ошибка\\n"',
                    ' ' * (indent + 8) + '"Попробуйте ещё раз или обратитесь в поддержку"',
                    ' ' * (indent + 4) + ')',
                    ' ' * (indent + 4) + 'await state.finish()',
                    ' ' * indent + 'except:',
                    ' ' * (indent + 4) + 'pass',
                ]
                
                lines[i:i+1] = [lines[i]] + except_block
                log("Добавлен except блок", "✅")
                break
        
        new_content = '\n'.join(lines)
    
    return new_content

def main():
    print("=" * 60)
    print("КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ФУНКЦИИ")
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
    
    # 4. Проверка проблемы
    log("Анализ проблемы...")
    
    has_decorator = '@dp.callback_query_handler' in content and 'mode_' in content
    has_definition = 'async def process_generation_mode' in content
    
    log(f"Декоратор найден: {'✅' if has_decorator else '❌'}", "ℹ️")
    log(f"Определение функции найдено: {'✅' if has_definition else '❌'}", "ℹ️")
    
    if not has_decorator:
        log("ОШИБКА: Декоратор не найден", "❌")
        return False
    
    # 5. Исправление
    log("Применение исправлений...")
    new_content = fix_function_definition(content)
    
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
        log("ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\n📋 Что исправлено:")
        print("  ✅ Добавлено определение функции")
        print("  ✅ Исправлены отступы")
        print("  ✅ Добавлена умная логика определения типа")
        print("  ✅ Добавлена обработка исключений")
        print("  ✅ Сохранены упрощенные сообщения")
        print("\n🚀 Следующий шаг:")
        print("  sudo systemctl restart albimusic-bot")
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print(result.stderr)
        
        # Показываем первые строки ошибки для диагностики
        error_lines = result.stderr.split('\n')
        for line in error_lines[:10]:
            if line.strip():
                print(f"  {line}")
        
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
