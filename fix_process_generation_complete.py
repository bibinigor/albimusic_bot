#!/usr/bin/env python3
"""
Комплексное исправление функции process_generation_mode:
1. Добавление умной логики определения generation_type
2. Исправление всех отступов
3. Удаление мусорного кода
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
    backup_path = f"{FILE_PATH}.backup_complete_fix_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_correct_function():
    """Возвращает правильную версию функции"""
    return '''@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Умный обработчик выбора режима генерации
    Автоматически определяет тип по данным в состоянии
    """
    try:
        await callback_query.answer()
        
        mode = callback_query.data.replace('mode_', '')
        user_id = str(callback_query.from_user.id)
        
        # Получаем данные из состояния
        state_data = await state.get_data()
        
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
            logging.info(f"Detected SONG generation (lyrics present: {len(lyrics)} chars)")
        elif prompt:
            generation_type = 'music'
            logging.info(f"Detected MUSIC generation (prompt present: {len(prompt)} chars)")
        elif explicit_type:
            generation_type = explicit_type
            logging.info(f"Using explicit generation_type: {explicit_type}")
        else:
            logging.error("Cannot determine generation type - no data found!")
            await callback_query.message.answer(
                "❌ Ошибка: не удалось определить тип генерации\\n"
                "Попробуйте начать заново с /song или /music"
            )
            await state.finish()
            return
        
        # Получаем дополнительные параметры
        style = state_data.get('style', '').strip()
        
        mode_name = 'Творческий режим' if mode == 'creative' else 'Точный режим'
        custom_mode = (mode == 'creative')
        
        logging.info(f"User {user_id} selected {mode_name} for {generation_type.upper()} generation")
        
        # Сохраняем выбор
        await state.update_data(generation_mode=mode)
        
        # Уведомляем пользователя
        type_emoji = "🎤" if generation_type == 'song' else "🎵"
        type_text = "песни" if generation_type == 'song' else "музыки"
        
        await callback_query.message.answer(
            f"{type_emoji} Генерация {type_text}\\n"
            f"✅ Режим: {mode_name}\\n\\n"
            "⏱ Начинаем генерацию, это займёт 1-2 минуты..."
        )
        
        # ========== ЗАПУСК ГЕНЕРАЦИИ ==========
        
        if generation_type == 'song':
            # --- ГЕНЕРАЦИЯ ПЕСНИ ---
            
            if not lyrics:
                logging.error(f"Song generation requested but no lyrics found!")
                await callback_query.message.answer("❌ Ошибка: текст песни не найден")
                await state.finish()
                return
            
            logging.info(f"Starting SONG generation:")
            logging.info(f"  User: {user_id}")
            logging.info(f"  Style: '{style}'")
            logging.info(f"  Lyrics length: {len(lyrics)} chars")
            logging.info(f"  Mode: {'Creative' if custom_mode else 'Exact'}")
            
            # Импортируем задачу
            from celery_tasks import generate_song_task
            
            # Запускаем Celery задачу
            task = generate_song_task.delay(
                user_id=int(user_id),
                lyrics=lyrics,
                style=style,
                custom_mode=custom_mode
            )
            
            logging.info(f"✅ Song generation task started: {task.id}")
            
            await callback_query.message.answer(
                f"🎤 Задача создания песни запущена\\n"
                f"📋 ID задачи: {task.id}\\n\\n"
                f"Ожидайте результат..."
            )
            
        else:
            # --- ГЕНЕРАЦИЯ МУЗЫКИ ---
            
            if not prompt:
                logging.error(f"Music generation requested but no prompt found!")
                await callback_query.message.answer("❌ Ошибка: описание музыки не найдено")
                await state.finish()
                return
            
            logging.info(f"Starting MUSIC generation:")
            logging.info(f"  User: {user_id}")
            logging.info(f"  Prompt: '{prompt[:100]}...'")
            logging.info(f"  Mode: {'Creative' if custom_mode else 'Exact'}")
            
            # Импортируем задачу
            from celery_tasks import generate_music_task
            
            # Формируем финальный промпт
            final_prompt = f"{prompt}. {'творческая интерпретация' if custom_mode else 'точное соответствие'}"
            
            # Запускаем Celery задачу
            task = generate_music_task.delay(
                user_id=int(user_id),
                prompt=final_prompt
            )
            
            logging.info(f"✅ Music generation task started: {task.id}")
            
            await callback_query.message.answer(
                f"🎵 Задача создания музыки запущена\\n"
                f"📋 ID задачи: {task.id}\\n\\n"
                f"Ожидайте результат..."
            )
        
        # Завершаем состояние
        await state.finish()
        
    except Exception as e:
        logging.error(f"❌ Error in process_generation_mode: {e}", exc_info=True)
        await callback_query.message.answer(
            "❌ Произошла ошибка при запуске генерации\\n"
            "Попробуйте ещё раз или обратитесь в поддержку"
        )
        await state.finish()


'''

def main():
    print("=" * 60)
    print("КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ process_generation_mode")
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
    
    # 4. Поиск и удаление старой функции + мусора
    log("Поиск старой функции process_generation_mode...")
    
    # Паттерн: находим от @dp.callback_query_handler(mode_) до следующей функции или if __name__
    pattern = r'@dp\.callback_query_handler\(lambda c: c\.data and c\.data\.startswith\([\'"]mode_[\'"]\).*?\).*?async def process_generation_mode.*?(?=\n@dp\.|async def [a-z_]+\(|if __name__|$)'
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if not matches:
        log("ОШИБКА: Функция не найдена", "❌")
        return False
    
    log(f"Найдено вхождений: {len(matches)}", "🔍")
    
    # Удаляем ВСЕ вхождения старой функции
    for i, match in enumerate(reversed(matches)):
        log(f"Удаляем вхождение {len(matches) - i} на позиции {match.start()}", "🗑️")
        content = content[:match.start()] + content[match.end():]
    
    # 5. Удаляем мусорные строки типа "if name == '__main__':" внутри кода
    log("Очистка мусорного кода...")
    content = re.sub(r'\nif name == [\'"]__main__[\'"]:.*?\n', '\n', content)
    
    # 6. Находим место для вставки правильной функции (перед if __name__)
    log("Поиск места для вставки...")
    main_match = re.search(r'if __name__ == ["\']__main__["\']:', content)
    
    if not main_match:
        log("ОШИБКА: Не найден if __name__", "❌")
        return False
    
    insert_pos = main_match.start()
    log(f"Место вставки найдено: позиция {insert_pos}", "✅")
    
    # 7. Вставляем правильную функцию
    log("Вставка правильной функции...")
    correct_function = get_correct_function()
    
    content = (
        content[:insert_pos] +
        correct_function +
        '\n\n' +
        content[insert_pos:]
    )
    
    # 8. Сохранение
    log("Сохранение файла...")
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
        shutil.move(temp_file, FILE_PATH)
        
        print("=" * 60)
        log("ФУНКЦИЯ ИСПРАВЛЕНА!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\nИзменения:")
        print("  ✅ Добавлена умная логика определения generation_type")
        print("  ✅ Исправлены все отступы")
        print("  ✅ Удален мусорный код")
        print("  ✅ Добавлена обработка ошибок")
        print("  ✅ Улучшено логирование")
        print("\nТеперь выполните:")
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
