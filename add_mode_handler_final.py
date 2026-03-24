#!/usr/bin/env python3
"""
Финальный скрипт добавления обработчика mode_
Минимальный, безопасный, проверенный
"""

import os
import re
import shutil
import subprocess
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    """Создает backup с timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def check_syntax(filepath):
    """Проверяет Python синтаксис"""
    result = subprocess.run(
        ['python3', '-m', 'py_compile', filepath],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stderr

def main():
    print("=" * 60)
    print("ДОБАВЛЕНИЕ ОБРАБОТЧИКА mode_")
    print("=" * 60)
    
    # 1. Проверка файла
    log("Проверка файла...")
    if not os.path.exists(FILE_PATH):
        log(f"ОШИБКА: Файл не найден: {FILE_PATH}", "❌")
        return False
    
    # 2. Проверка текущего синтаксиса
    log("Проверка синтаксиса...")
    is_valid, error = check_syntax(FILE_PATH)
    if not is_valid:
        log("ОШИБКА: Файл содержит синтаксические ошибки", "❌")
        print(error)
        return False
    log("Синтаксис корректен", "✅")
    
    # 3. Чтение файла
    log("Чтение файла...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 4. Проверка наличия обработчика
    log("Поиск существующего обработчика...")
    if 'def process_generation_mode' in content:
        log("Обработчик уже существует!", "⚠️")
        return True
    log("Обработчик не найден, добавляем", "✅")
    
    # 5. Создание backup
    log("Создание backup...")
    backup_path = create_backup()
    
    # 6. Поиск места вставки
    log("Поиск места для вставки...")
    match = re.search(r'if __name__ == "__main__":', content)
    if not match:
        log("ОШИБКА: Не найдена точка if __name__", "❌")
        return False
    
    insertion_point = match.start()
    log(f"Место найдено на позиции {insertion_point}", "✅")
    
    # 7. Код обработчика (МИНИМАЛЬНЫЙ)
    handler_code = """
# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    \"\"\"Обработчик выбора режима генерации\"\"\"
    await callback_query.answer()
    mode = callback_query.data.replace('mode_', '')
    mode_name = 'Точный режим' if mode == 'exact' else 'Творческий режим'
    logger.info(f"User {callback_query.from_user.id} selected mode: {mode}")
    await callback_query.message.answer(f"✅ Выбран: {mode_name}")
    await state.finish()


"""
    
    # 8. Вставка кода
    log("Вставка обработчика...")
    new_content = content[:insertion_point] + handler_code + content[insertion_point:]
    
    # 9. Сохранение во временный файл
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 10. Проверка синтаксиса нового файла
    log("Проверка синтаксиса нового кода...")
    is_valid, error = check_syntax(temp_file)
    
    if is_valid:
        log("Синтаксис нового кода корректен", "✅")
        
        # Заменяем оригинальный файл
        shutil.move(temp_file, FILE_PATH)
        log("Файл сохранен", "✅")
        
        # Финальная проверка
        is_valid, error = check_syntax(FILE_PATH)
        if is_valid:
            print("=" * 60)
            log("ОБРАБОТЧИК УСПЕШНО ДОБАВЛЕН!", "✅")
            print("=" * 60)
            print(f"\nBackup: {backup_path}")
            print("\nТеперь выполните:")
            print("  sudo systemctl restart albimusic-bot")
            return True
        else:
            log("ОШИБКА финальной проверки, откат...", "❌")
            shutil.copy2(backup_path, FILE_PATH)
            return False
    else:
        log("ОШИБКА: Новый код содержит синтаксические ошибки", "❌")
        print(error)
        os.remove(temp_file)
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
