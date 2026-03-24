#!/usr/bin/env python3
"""
Упрощение технических сообщений для пользователя
Заменяет только тексты, сохраняя всю логику
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
    backup_path = f"{FILE_PATH}.backup_messages_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def simplify_messages(content):
    """Заменяет технические сообщения на простые"""
    
    changes_made = 0
    
    # ========== ЗАМЕНА 1: Первое уведомление о начале генерации ==========
    
    old_message_1 = r'await callback_query\.message\.answer\(\s*f"{type_emoji} Начинаем генерацию {type_text}\\n"\s*f"✅ Режим: {mode_name}\\n\\n"\s*"⏱ Подготовка займёт 1-2 минуты\.\.\."\s*\)'
    
    new_message_1 = 'await callback_query.message.answer(\n            "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"\n        )'
    
    if re.search(old_message_1, content, re.DOTALL):
        content = re.sub(old_message_1, new_message_1, content, flags=re.DOTALL)
        log("Заменено первое уведомление", "✅")
        changes_made += 1
    else:
        log("Первое уведомление не найдено (возможно уже изменено)", "⚠️")
    
    # ========== ЗАМЕНА 2: Сообщение после запуска Celery задачи (ПЕСНЯ) ==========
    
    old_message_2 = r'await callback_query\.message\.answer\(\s*f"✅ Задача создания песни запущена\\n"\s*f"📋 ID: {task\.idXXXLATEXDISPLAYXXX0XXXLATEXDISPLAYXXX}\.\.\.\\n\\n"\s*f"Ожидайте результат в течение 2-3 минут"\s*\)'
    
    new_message_2 = 'await callback_query.message.answer(\n                    "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"\n                )'
    
    if re.search(old_message_2, content, re.DOTALL):
        content = re.sub(old_message_2, new_message_2, content, flags=re.DOTALL)
        log("Заменено сообщение после запуска задачи (песня)", "✅")
        changes_made += 1
    else:
        log("Сообщение для песни не найдено (возможно уже изменено)", "⚠️")
    
    # ========== ЗАМЕНА 3: Сообщение после запуска Celery задачи (МУЗЫКА) ==========
    
    old_message_3 = r'await callback_query\.message\.answer\(\s*f"✅ Задача создания музыки запущена\\n"\s*f"📋 ID: {task\.idXXXLATEXDISPLAYXXX1XXXLATEXDISPLAYXXX}\.\.\.\\n\\n"\s*f"Ожидайте результат в течение 2-3 минут"\s*\)'
    
    new_message_3 = 'await callback_query.message.answer(\n                    "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"\n                )'
    
    if re.search(old_message_3, content, re.DOTALL):
        content = re.sub(old_message_3, new_message_3, content, flags=re.DOTALL)
        log("Заменено сообщение после запуска задачи (музыка)", "✅")
        changes_made += 1
    else:
        log("Сообщение для музыки не найдено (возможно уже изменено)", "⚠️")
    
    # ========== АЛЬТЕРНАТИВНЫЙ МЕТОД: Построчная замена ==========
    
    if changes_made < 3:
        log("Применяю альтернативный метод замены...", "🔄")
        
        # Разбиваем на строки
        lines = content.split('\n')
        new_lines = []
        i = 0
        alt_changes = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Ищем строки с await callback_query.message.answer внутри process_generation_mode
            if 'await callback_query.message.answer(' in line:
                # Читаем следующие 5 строк для анализа
                block = '\n'.join(lines[i:min(i+6, len(lines))])
                
                # Проверяем технические сообщения
                if any(phrase in block for phrase in [
                    'Начинаем генерацию',
                    'Задача создания песни запущена',
                    'Задача создания музыки запущена',
                    'ID:',
                    'Подготовка займёт'
                ]):
                    # Находим закрывающую скобку
                    bracket_count = 0
                    end_line = i
                    
                    for j in range(i, min(i+10, len(lines))):
                        bracket_count += lines[j].count('(') - lines[j].count(')')
                        if bracket_count == 0:
                            end_line = j
                            break
                    
                    # Получаем отступ
                    indent = len(line) - len(line.lstrip())
                    
                    # Заменяем весь блок
                    new_lines.append(' ' * indent + 'await callback_query.message.answer(')
                    new_lines.append(' ' * (indent + 4) + '"⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"')
                    new_lines.append(' ' * indent + ')')
                    
                    log(f"Заменен блок на строках {i+1}-{end_line+1}", "✅")
                    alt_changes += 1
                    
                    # Пропускаем весь блок
                    i = end_line + 1
                    continue
            
            new_lines.append(line)
            i += 1
        
        if alt_changes > 0:
            content = '\n'.join(new_lines)
            changes_made += alt_changes
            log(f"Применен альтернативный метод: {alt_changes} замен", "✅")
    
    return content, changes_made

def main():
    print("=" * 60)
    print("УПРОЩЕНИЕ СООБЩЕНИЙ ДЛЯ ПОЛЬЗОВАТЕЛЯ")
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
    
    # 4. Проверка наличия функции
    if 'async def process_generation_mode' not in content:
        log("ОШИБКА: Функция process_generation_mode не найдена", "❌")
        return False
    
    log("Функция найдена", "✅")
    
    # 5. Замена сообщений
    log("Замена технических сообщений...")
    new_content, changes = simplify_messages(content)
    
    if changes == 0:
        log("Изменений не внесено (возможно уже упрощено)", "⚠️")
        return True
    
    log(f"Выполнено замен: {changes}", "✅")
    
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
        log("СООБЩЕНИЯ УПРОЩЕНЫ!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print(f"\nВыполнено замен: {changes}")
        print("\n📝 Новый текст:")
        print("  ⏳ Генерация вашей композиции началась.")
        print("     Это займет 2-5 минут, подождите пожалуйста!")
        print("     Результат я пришлю сюда в чат")
        print("\n🔍 Что НЕ изменено:")
        print("  ✅ Логирование")
        print("  ✅ Обработка ошибок")
        print("  ✅ Создание записей в БД")
        print("  ✅ Запуск Celery задач")
        print("\n🚀 Следующий шаг:")
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
