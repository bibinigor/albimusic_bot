#!/usr/bin/env python3
"""
Добавление умной логики определения generation_type
в существующую функцию process_generation_mode
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
    backup_path = f"{FILE_PATH}.backup_smart_logic_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_smart_detection_code():
    """Возвращает код умной логики определения типа"""
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
            logging.info(f"🎤 Detected SONG generation (lyrics present: {len(lyrics)} chars)")
        elif prompt:
            generation_type = 'music'
            logging.info(f"🎵 Detected MUSIC generation (prompt present: {len(prompt)} chars)")
        elif explicit_type:
            generation_type = explicit_type
            logging.info(f"📋 Using explicit generation_type: {explicit_type}")
        else:
            logging.error("❌ Cannot determine generation type - no data found!")
            await callback_query.message.answer(
                "❌ Ошибка: не удалось определить тип генерации\\n"
                "Попробуйте начать заново с кнопки 🎵 Создать песню"
            )
            await state.finish()
            return
        
        # Получаем дополнительные параметры
        style = state_data.get('style', '').strip()
        
'''

def add_smart_logic(content):
    """Вставляет умную логику определения типа после state_data"""
    
    # Паттерн: находим строку с state_data = await state.get_data()
    # и следующую строку (обычно пустую или с logging)
    pattern = r'(state_data = await state\.get_data\(\)\s*\n)(\s*\n)?(\s*logging\.info\(f"User {user_id} selected mode:)'
    
    def replacer(match):
        state_data_line = match.group(1)
        smart_logic = get_smart_detection_code()
        logging_line = match.group(3)
        
        # Вставляем умную логику между state_data и logging
        return state_data_line + smart_logic + '\n        ' + logging_line
    
    new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    if new_content == content:
        log("⚠️  Паттерн не найден, пробуем альтернативный метод...", "🔄")
        
        # Альтернативный метод: построчная вставка
        lines = content.split('\n')
        new_lines = []
        inserted = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Ищем строку с state_data = await state.get_data()
            if 'state_data = await state.get_data()' in line and not inserted:
                # Определяем отступ
                indent = len(line) - len(line.lstrip())
                
                # Проверяем, что следующая строка не содержит умную логику
                next_line = lines[i+1] if i+1 < len(lines) else ''
                if 'УМНОЕ ОПРЕДЕЛЕНИЕ' not in next_line:
                    # Вставляем умную логику с правильным отступом
                    smart_logic_lines = get_smart_detection_code().split('\n')
                    for logic_line in smart_logic_lines:
                        if logic_line.strip():  # Пропускаем пустые строки
                            new_lines.append(' ' * indent + logic_line.lstrip())
                        else:
                            new_lines.append('')
                    
                    inserted = True
                    log(f"Вставлена умная логика после строки {i+1}", "✅")
        
        new_content = '\n'.join(new_lines)
        
        if not inserted:
            log("Не удалось найти место для вставки", "❌")
            return content, False
    
    return new_content, True

def main():
    print("=" * 60)
    print("ДОБАВЛЕНИЕ УМНОЙ ЛОГИКИ ОПРЕДЕЛЕНИЯ ТИПА")
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
    
    # 5. Проверка, не добавлена ли уже умная логика
    if 'УМНОЕ ОПРЕДЕЛЕНИЕ ТИПА ГЕНЕРАЦИИ' in content:
        log("Умная логика уже добавлена", "✅")
        log("Файл не изменен", "ℹ️")
        return True
    
    # 6. Добавление умной логики
    log("Добавление умной логики определения типа...")
    new_content, success = add_smart_logic(content)
    
    if not success:
        log("Не удалось добавить умную логику", "❌")
        return False
    
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
        log("УМНАЯ ЛОГИКА ДОБАВЛЕНА!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\n📋 Что добавлено:")
        print("  ✅ Определение lyrics из state_data")
        print("  ✅ Определение prompt из state_data")
        print("  ✅ Приоритетная логика определения типа")
        print("  ✅ Fallback на explicit_type")
        print("  ✅ Обработка ошибки (если тип не определен)")
        print("  ✅ Детальное логирование")
        print("\n🔍 Логика определения:")
        print("  1. Если есть lyrics → song")
        print("  2. Иначе если есть prompt → music")
        print("  3. Иначе используем explicit_type")
        print("  4. Иначе ошибка и выход")
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
