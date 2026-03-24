#!/usr/bin/env python3
"""
Чистый Python скрипт для добавления обработчика mode_
Без shell heredoc проблем
"""

import os
import re
import shutil
import subprocess
from datetime import datetime

# Конфигурация
FILE_PATH = "/root/albimusic-bot/main_with_payments.py"
BACKUP_DIR = "/root/albimusic-bot/backups"

# Цвета для вывода
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log(message, color=Colors.NC):
    print(f"{color}{message}{Colors.NC}")

def create_backup(file_path):
    """Создает backup файла"""
    # Создаем директорию для backups
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"main_with_payments.py.backup_{timestamp}")
    
    shutil.copy2(file_path, backup_path)
    log(f"✅ Backup создан: {backup_path}", Colors.GREEN)
    return backup_path

def check_syntax(file_path):
    """Проверяет синтаксис Python файла"""
    result = subprocess.run(
        ['python3', '-m', 'py_compile', file_path],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stderr

def find_handler_exists(content):
    """Проверяет, существует ли обработчик process_generation_mode"""
    return 'def process_generation_mode' in content

def find_insertion_point(content):
    """
    Находит лучшее место для вставки обработчика
    Варианты (в порядке приоритета):
    1. После последнего @dp.callback_query_handler
    2. Перед if __name__ == "__main__"
    """
    
    # Вариант 1: После последнего callback_query_handler
    # Ищем все вхождения
    pattern = r'@dp\.callback_query_handler.*?\n.*?async def .*?:\n(?:    .*?\n)*?(?=\n(?:@|async def|if __name__|def [a-z_]+\()|$)'
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if matches:
        # Берем последнее совпадение
        last_match = matches[-1]
        insertion_point = last_match.end()
        log(f"✓ Найдено место после последнего callback_query_handler", Colors.CYAN)
        return insertion_point, "after_callback"
    
    # Вариант 2: Перед if __name__
    match = re.search(r'if __name__ == "__main__":', content)
    if match:
        insertion_point = match.start()
        log(f"✓ Найдено место перед if __name__", Colors.CYAN)
        return insertion_point, "before_main"
    
    # Если ничего не найдено - в конец файла
    log(f"⚠️  Место не найдено, добавляем в конец", Colors.YELLOW)
    return len(content), "end"

def get_handler_code():
    """Возвращает код минимального обработчика"""
    return '''

# ========== ОБРАБОТЧИК ВЫБОРА РЕЖИМА ГЕНЕРАЦИИ ==========
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """Минимальный обработчик выбора режима генерации"""
    try:
        await callback_query.answer()
        
        mode = callback_query.data.replace('mode_', '')
        mode_name = 'Точный режим' if mode == 'exact' else 'Творческий режим'
        
        logger.info(f"User {callback_query.from_user.id} selected generation mode: {mode}")
        
        # Сохраняем выбор режима
        await state.update_data(generation_mode=mode)
        
        # Уведомляем пользователя
        await callback_query.message.answer(
            f"✅ Выбран: {mode_name}\\n\\n"
            "⏱ Генерация началась, ожидайте результат..."
        )
        
        # Завершаем состояние
        await state.finish()
        
    except Exception as e:
        logger.error(f"Error in process_generation_mode: {e}", exc_info=True)
        await callback_query.message.answer("❌ Произошла ошибка при выборе режима")
        await state.finish()


'''

def remove_old_handler(content):
    """Удаляет старый обработчик process_generation_mode если он есть"""
    pattern = r'@dp\.callback_query_handler.*?mode_.*?\n.*?async def process_generation_mode.*?\n(?:    .*?\n)*?(?=\n(?:@|async def|if __name__|def [a-z_]+\()|$)'
    
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    if new_content != content:
        log("✓ Старый обработчик удален", Colors.YELLOW)
        return new_content
    
    return content

def main():
    log("╔═══════════════════════════════════════════════════════════╗", Colors.CYAN)
    log("║       ДОБАВЛЕНИЕ ОБРАБОТЧИКА mode_ callback              ║", Colors.CYAN)
    log("╚═══════════════════════════════════════════════════════════╝", Colors.CYAN)
    
    # Проверка существования файла
    if not os.path.exists(FILE_PATH):
        log(f"❌ Файл не найден: {FILE_PATH}", Colors.RED)
        return False
    
    log(f"\n[1] Чтение файла...", Colors.BLUE)
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    log(f"✓ Прочитано {len(content)} символов", Colors.GREEN)
    
    # Проверка текущего синтаксиса
    log(f"\n[2] Проверка текущего синтаксиса...", Colors.BLUE)
    is_valid, error = check_syntax(FILE_PATH)
    if not is_valid:
        log(f"❌ Файл содержит синтаксические ошибки:", Colors.RED)
        log(error, Colors.RED)
        return False
    log("✓ Синтаксис корректен", Colors.GREEN)
    
    # Создание backup
    log(f"\n[3] Создание backup...", Colors.BLUE)
    backup_path = create_backup(FILE_PATH)
    
    # Проверка наличия обработчика
    log(f"\n[4] Проверка существующего обработчика...", Colors.BLUE)
    if find_handler_exists(content):
        log("⚠️  Обработчик process_generation_mode уже существует", Colors.YELLOW)
        log("Удаляем старый обработчик...", Colors.YELLOW)
        content = remove_old_handler(content)
    else:
        log("✓ Обработчик не найден, можно добавлять", Colors.GREEN)
    
    # Поиск места вставки
    log(f"\n[5] Поиск места для вставки...", Colors.BLUE)
    insertion_point, location_type = find_insertion_point(content)
    log(f"✓ Место найдено: позиция {insertion_point} ({location_type})", Colors.GREEN)
    
    # Вставка обработчика
    log(f"\n[6] Вставка обработчика...", Colors.BLUE)
    handler_code = get_handler_code()
    new_content = content[:insertion_point] + handler_code + content[insertion_point:]
    log("✓ Обработчик вставлен", Colors.GREEN)
    
    # Сохранение во временный файл
    log(f"\n[7] Проверка синтаксиса нового кода...", Colors.BLUE)
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    is_valid, error = check_syntax(temp_file)
    
    if is_valid:
        log("✓ Синтаксис нового кода корректен", Colors.GREEN)
        
        # Сохранение финального файла
        log(f"\n[8] Сохранение файла...", Colors.BLUE)
        shutil.move(temp_file, FILE_PATH)
        log("✓ Файл сохранен", Colors.GREEN)
        
        # Финальная проверка
        log(f"\n[9] Финальная проверка...", Colors.BLUE)
        is_valid, error = check_syntax(FILE_PATH)
        if is_valid:
            log("✅ ОБРАБОТЧИК УСПЕШНО ДОБАВЛЕН!", Colors.GREEN)
            log(f"Backup сохранен в: {backup_path}", Colors.CYAN)
            return True
        else:
            log("❌ Финальная проверка не прошла", Colors.RED)
            log("Восстанавливаем из backup...", Colors.YELLOW)
            shutil.copy2(backup_path, FILE_PATH)
            return False
    else:
        log("❌ Новый код содержит синтаксические ошибки:", Colors.RED)
        log(error, Colors.RED)
        log("Файл не изменен", Colors.YELLOW)
        os.remove(temp_file)
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        log("\n╔═══════════════════════════════════════════════════════════╗", Colors.GREEN)
        log("║  ГОТОВО! Теперь перезапустите бота:                      ║", Colors.GREEN)
        log("║  sudo systemctl restart albimusic-bot                    ║", Colors.GREEN)
        log("╚═══════════════════════════════════════════════════════════╝", Colors.GREEN)
        exit(0)
    else:
        log("\n╔═══════════════════════════════════════════════════════════╗", Colors.RED)
        log("║  ОШИБКА! Проверьте вывод выше                             ║", Colors.RED)
        log("╚═══════════════════════════════════════════════════════════╝", Colors.RED)
        exit(1)
