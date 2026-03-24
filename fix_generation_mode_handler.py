#!/usr/bin/env python3
"""
Исправление обработчика process_generation_mode
Правильная обработка песен и музыки
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
    backup_path = f"{FILE_PATH}.backup_handler_fix_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_corrected_handler():
    """Возвращает исправленный обработчик"""
    return '''# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора режима генерации (для музыки и песен)"""
    try:
        await callback_query.answer()
        
        mode = callback_query.data.replace('mode_', '')
        user_id = str(callback_query.from_user.id)
        
        # Получаем данные из состояния
        state_data = await state.get_data()
        
        # ВАЖНО: Определяем тип генерации
        # Проверяем наличие lyrics - если есть, это песня
        lyrics = state_data.get('lyrics', '')
        style = state_data.get('style', '')
        prompt = state_data.get('prompt', '')
        
        # Определяем тип по наличию данных
        if lyrics:
            generation_type = 'song'
        elif prompt:
            generation_type = 'music'
        else:
            # Fallback на значение из состояния
            generation_type = state_data.get('generation_type', 'music')
        
        is_free = state_data.get('is_free', False)
        mode_name = 'Точный режим' if mode == 'exact' else 'Творческий режим'
        custom_mode = (mode == 'creative')
        
        logger.info(f"User {user_id} selected {mode_name} for {generation_type} generation")
        
        # Уведомляем пользователя
        await callback_query.message.answer(
            f"✅ Выбран: {mode_name}\\n\\n"
            "⏱ Генерация началась, это займёт 1-2 минуты..."
        )
        
        # Запускаем генерацию в зависимости от типа
        if generation_type == 'song':
            # ========== ГЕНЕРАЦИЯ ПЕСНИ ==========
            
            if not lyrics:
                await callback_query.message.answer("❌ Ошибка: текст песни не найден")
                await state.finish()
                return
            
            logger.info(f"Starting SONG generation for user {user_id}:")
            logger.info(f"  Style: '{style}'")
            logger.info(f"  Lyrics length: {len(lyrics)} chars")
            logger.info(f"  Custom mode: {custom_mode}")
            logger.info(f"  Is free: {is_free}")
            
            # Импортируем задачу генерации песни
            from celery_tasks import generate_song_task
            
            # Запускаем Celery задачу для песни
            task = generate_song_task.delay(
                user_id=int(user_id),
                lyrics=lyrics,
                style=style,
                custom_mode=custom_mode
            )
            
            logger.info(f"Song generation task started: {task.id}")
            
            # Сохраняем task_id для отслеживания
            await callback_query.message.answer(
                f"🎵 Задача генерации песни запущена\\n"
                f"ID: {task.id}"
            )
            
        else:
            # ========== ГЕНЕРАЦИЯ МУЗЫКИ ==========
            
            if not prompt:
                await callback_query.message.answer("❌ Ошибка: описание музыки не найдено")
                await state.finish()
                return
            
            logger.info(f"Starting MUSIC generation for user {user_id}:")
            logger.info(f"  Prompt: '{prompt[:100]}...'")
            logger.info(f"  Custom mode: {custom_mode}")
            logger.info(f"  Is free: {is_free}")
            
            # Импортируем задачу генерации музыки
            from celery_tasks import generate_music_task
            
            # Запускаем Celery задачу для музыки
            task = generate_music_task.delay(
                user_id=int(user_id),
                prompt=prompt
            )
            
            logger.info(f"Music generation task started: {task.id}")
            
            # Сохраняем task_id для отслеживания
            await callback_query.message.answer(
                f"🎵 Задача генерации музыки запущена\\n"
                f"ID: {task.id}"
            )
        
        # Завершаем состояние
        await state.finish()
        
    except Exception as e:
        logger.error(f"Error in process_generation_mode: {e}", exc_info=True)
        await callback_query.message.answer(
            "❌ Произошла ошибка при запуске генерации\\n"
            "Попробуйте ещё раз или обратитесь в поддержку"
        )
        await state.finish()


'''

def main():
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ ОБРАБОТЧИКА process_generation_mode")
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
    
    # 4. Поиск и удаление старого обработчика
    log("Поиск старого обработчика...")
    
    pattern = r'# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========\s*@dp\.callback_query_handler.*?mode_.*?\n.*?async def process_generation_mode.*?\n(?:    .*?\n)*?(?=\n(?:# =====|@dp\.|async def|if __name__|def [a-z_]|class |$))'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        log(f"Найден на позиции {match.start()}", "✅")
        # Удаляем старый
        content = content[:match.start()] + content[match.end():]
        log("Старый обработчик удалён", "✅")
    else:
        log("Старый обработчик не найден (возможно уже удалён)", "⚠️")
    
    # 5. Поиск места вставки (перед if __name__)
    log("Поиск места для нового обработчика...")
    
    main_match = re.search(r'if __name__ == ["\']__main__["\']:', content)
    
    if not main_match:
        log("ОШИБКА: Не найден if __name__", "❌")
        return False
    
    insertion_point = main_match.start()
    log(f"Место найдено: позиция {insertion_point}", "✅")
    
    # 6. Вставка нового обработчика
    log("Вставка исправленного обработчика...")
    new_handler = get_corrected_handler()
    content = content[:insertion_point] + new_handler + content[insertion_point:]
    log("Обработчик вставлен", "✅")
    
    # 7. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        log("ОБРАБОТЧИК УСПЕШНО ИСПРАВЛЕН!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\nИзменения:")
        print("  • Правильное определение типа генерации")
        print("  • Проверка lyrics для песен, prompt для музыки")
        print("  • Вызов правильных Celery задач")
        print("  • Улучшенное логирование")
        print("\nТеперь выполните:")
        print("  sudo systemctl restart albimusic-bot")
        return True
    else:
        log("ОШИБКА синтаксиса:", "❌")
        print(result.stderr)
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
