#!/usr/bin/env python3
"""
ИСПРАВЛЕНИЕ ОБРАБОТКИ РЕЗУЛЬТАТА В save_generation_task_sync

ПРОБЛЕМА:
- result[0] может быть int (например, 123)
- Код пытается сделать len(result[0]) на int
- TypeError: object of type 'int' has no len()

РЕШЕНИЕ:
- Правильная проверка типа результата
- Безопасное извлечение данных
"""

import os
import re
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/celery_tasks.py"

def log(msg, symbol="•"):
    print(f"{symbol} {msg}")

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{FILE_PATH}.backup_result_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_fixed_result_handling():
    """Возвращает ИСПРАВЛЕННУЮ часть обработки результата"""
    return '''        # ===============================================
        # ВЫПОЛНЕНИЕ ЗАПРОСА
        # ===============================================
        
        result = execute_query_sync(query, params)
        
        # ===============================================
        # ОБРАБОТКА РЕЗУЛЬТАТА
        # ===============================================
        
        if result:
            # result может быть:
            # 1. tuple с данными: (123, datetime, datetime)
            # 2. список tuples: [(123, datetime, datetime)]
            # 3. просто число (rowcount): 1
            
            # Определяем тип результата
            if isinstance(result, (list, tuple)) and len(result) > 0:
                # Если это список/tuple, берем первый элемент
                first_row = result[0] if isinstance(result, list) else result
                
                # Извлекаем данные безопасно
                if isinstance(first_row, (list, tuple)) and len(first_row) > 0:
                    row_id = first_row[0] if len(first_row) > 0 else 'unknown'
                    created = first_row[1] if len(first_row) > 1 else None
                    updated = first_row[2] if len(first_row) > 2 else None
                else:
                    # first_row это скаляр (число)
                    row_id = first_row
                    created = None
                    updated = None
            else:
                # Если это просто число (rowcount)
                row_id = 'unknown'
                created = None
                updated = None
            
            # Определяем, была ли это новая запись
            is_new = (created == updated) if (created and updated) else None
            
            if is_new is True:
                action = "создана"
            elif is_new is False:
                action = "обновлена"
            else:
                action = "сохранена"
            
            logger.info(f"✅ [DB] Задача {task_id} {action} (id={row_id}, status={status})")
            
            # Дополнительное логирование для completed/error
            if status == 'completed' and safe_result_message:
                logger.info(f"✅ [DB] Результат: {safe_result_message}")
            elif status == 'error' and safe_error_message:
                logger.error(f"❌ [DB] Ошибка: {safe_error_message}")
            
            return True
        else:
            logger.warning(f"⚠️ [DB] Задача {task_id} - пустой результат от БД")
            return True  # Считаем успехом (запрос выполнен)
'''

def fix_result_handling_in_function(content):
    """Заменяет блок обработки результата в save_generation_task_sync"""
    
    # Ищем блок от "result = execute_query_sync" до "return False" (обработка ошибок)
    pattern = r'(result = execute_query_sync\(query, params\))(.*?)(except Exception as e:)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Блок обработки результата НЕ НАЙДЕН", "❌")
        return content, False
    
    # Заменяем блок обработки результата
    new_content = (
        content[:match.start()] +
        get_fixed_result_handling() +
        '\n        ' +
        content[match.end(2):]
    )
    
    log("Блок обработки результата ИСПРАВЛЕН", "✅")
    return new_content, True

def add_detailed_logging():
    """Возвращает улучшенный блок логирования для отладки"""
    return '''        # DEBUG: Детальное логирование результата (можно удалить после отладки)
        if result:
            logger.debug(f"🔍 [DB DEBUG] Тип result: {type(result)}")
            logger.debug(f"🔍 [DB DEBUG] Значение result: {result}")
            if isinstance(result, (list, tuple)) and len(result) > 0:
                logger.debug(f"🔍 [DB DEBUG] Тип result[0]: {type(result[0])}")
                logger.debug(f"🔍 [DB DEBUG] Значение result[0]: {result[0]}")
'''

def main():
    print("=" * 80)
    print("ИСПРАВЛЕНИЕ ОБРАБОТКИ РЕЗУЛЬТАТА В save_generation_task_sync")
    print("=" * 80)
    print()
    
    # 1. Проверка файла
    log("Проверка файла...")
    if not os.path.exists(FILE_PATH):
        log("ОШИБКА: Файл не найден", "❌")
        return False
    
    # 2. Backup
    log("Создание backup...")
    backup_path = create_backup()
    print()
    
    # 3. Чтение
    log("Чтение файла...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 4. Исправление
    log("Исправление обработки результата...")
    new_content, modified = fix_result_handling_in_function(content)
    
    if not modified:
        log("ОШИБКА: Блок не найден или не исправлен", "❌")
        return False
    
    print()
    
    # 5. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 6. Проверка синтаксиса
    log("Проверка синтаксиса Python...")
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'py_compile', temp_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("Синтаксис корректен", "✅")
        shutil.move(temp_file, FILE_PATH)
        
        print()
        print("=" * 80)
        log("ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!", "✅")
        print("=" * 80)
        
        print(f"\n📁 Backup: {backup_path}")
        
        print("\n📋 Что исправлено:")
        print("  ✅ Добавлена проверка типа result")
        print("  ✅ Безопасное извлечение данных из tuple/list/int")
        print("  ✅ Обработка всех возможных форматов результата")
        print("  ✅ Улучшено логирование")
        
        print("\n🎯 Логика обработки:")
        print("  1. Проверка: result существует?")
        print("  2. Проверка: result это list/tuple?")
        print("  3. Извлечение: row_id, created, updated (если есть)")
        print("  4. Определение: создана или обновлена запись")
        print("  5. Логирование результата")
        
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        
        print("\n🔍 Проверка:")
        print("  # Тестовая генерация")
        print("  # Логи должны показывать:")
        print("  sudo journalctl -u albimusic-celery -f | grep -E '\\[DB\\]'")
        print()
        print("  # Ожидаем:")
        print("  ✅ [DB] Задача xxx создана (id=123, status=processing)")
        print("  ✅ [DB] Задача xxx обновлена (id=123, status=completed)")
        
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print()
        print("=" * 80)
        print("ДЕТАЛИ ОШИБКИ:")
        print("=" * 80)
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
