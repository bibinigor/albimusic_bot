#!/usr/bin/env python3
"""
Комплексное исправление генерации:
1. Умный обработчик process_generation_mode (определяет тип автоматически)
2. Явная установка generation_type в process_song_style
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
    backup_path = f"{FILE_PATH}.backup_complete_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_smart_handler():
    """Возвращает умный обработчик (Вариант 1)"""
    return '''# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
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
            logger.info(f"Detected SONG generation (lyrics present: {len(lyrics)} chars)")
        elif prompt:
            generation_type = 'music'
            logger.info(f"Detected MUSIC generation (prompt present: {len(prompt)} chars)")
        elif explicit_type:
            generation_type = explicit_type
            logger.info(f"Using explicit generation_type: {explicit_type}")
        else:
            logger.error("Cannot determine generation type - no data found!")
            await callback_query.message.answer(
                "❌ Ошибка: не удалось определить тип генерации\\n"
                "Попробуйте начать заново с /song или /music"
            )
            await state.finish()
            return
        
        # Получаем дополнительные параметры
        style = state_data.get('style', '').strip()
        is_free = state_data.get('is_free', False)
        
        mode_name = 'Точный режим' if mode == 'exact' else 'Творческий режим'
        custom_mode = (mode == 'creative')
        
        logger.info(f"User {user_id} selected {mode_name} for {generation_type.upper()} generation")
        
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
                logger.error(f"Song generation requested but no lyrics found!")
                await callback_query.message.answer("❌ Ошибка: текст песни не найден")
                await state.finish()
                return
            
            logger.info(f"Starting SONG generation:")
            logger.info(f"  User: {user_id}")
            logger.info(f"  Style: '{style}'")
            logger.info(f"  Lyrics length: {len(lyrics)} chars")
            logger.info(f"  Mode: {'Creative' if custom_mode else 'Exact'}")
            logger.info(f"  Free tier: {is_free}")
            
            # Импортируем задачу
            from celery_tasks import generate_song_task
            
            # Запускаем Celery задачу
            task = generate_song_task.delay(
                user_id=int(user_id),
                lyrics=lyrics,
                style=style,
                custom_mode=custom_mode
            )
            
            logger.info(f"✅ Song generation task started: {task.id}")
            
            await callback_query.message.answer(
                f"🎤 Задача создания песни запущена\\n"
                f"📋 ID задачи: {task.id}\\n\\n"
                f"Ожидайте результат..."
            )
            
        else:
            # --- ГЕНЕРАЦИЯ МУЗЫКИ ---
            
            if not prompt:
                logger.error(f"Music generation requested but no prompt found!")
                await callback_query.message.answer("❌ Ошибка: описание музыки не найдено")
                await state.finish()
                return
            
            logger.info(f"Starting MUSIC generation:")
            logger.info(f"  User: {user_id}")
            logger.info(f"  Prompt: '{prompt[:100]}...'")
            logger.info(f"  Mode: {'Creative' if custom_mode else 'Exact'}")
            logger.info(f"  Free tier: {is_free}")
            
            # Импортируем задачу
            from celery_tasks import generate_music_task
            
            # Запускаем Celery задачу
            task = generate_music_task.delay(
                user_id=int(user_id),
                prompt=prompt
            )
            
            logger.info(f"✅ Music generation task started: {task.id}")
            
            await callback_query.message.answer(
                f"🎵 Задача создания музыки запущена\\n"
                f"📋 ID задачи: {task.id}\\n\\n"
                f"Ожидайте результат..."
            )
        
        # Завершаем состояние
        await state.finish()
        
    except Exception as e:
        logger.error(f"❌ Error in process_generation_mode: {e}", exc_info=True)
        await callback_query.message.answer(
            "❌ Произошла ошибка при запуске генерации\\n"
            "Попробуйте ещё раз или обратитесь в поддержку"
        )
        await state.finish()


'''

def find_function(content, func_name):
    """Находит функцию в коде"""
    pattern = rf'^async def {func_name}\(.*?\):'
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        return None, None
    
    start = match.start()
    rest = content[match.end():]
    lines = rest.split('\n')
    
    # Находим конец функции
    indent = None
    offset = 0
    
    for i, line in enumerate(lines):
        if i == 0:
            continue
        
        if indent is None and line.strip() and not line.strip().startswith('#'):
            indent = len(line) - len(line.lstrip())
            continue
        
        if indent is not None and line.strip():
            current_indent = len(line) - len(line.lstrip())
            if current_indent < indent:
                break
        
        offset += len(line) + 1
    
    return start, match.end() + offset

def update_process_song_style(content):
    """Обновляет process_song_style для установки generation_type (Вариант 2)"""
    
    # Ищем строку с await state.update_data внутри process_song_style
    # Должна быть примерно такая строка:
    # await state.update_data(lyrics=lyrics, style=style)
    
    pattern = r'(async def process_song_style.*?)(await state\.update_data\([^)]*lyrics=lyrics[^)]*\))'
    
    def replacer(match):
        func_part = match.group(1)
        update_line = match.group(2)
        
        # Проверяем, есть ли уже generation_type
        if 'generation_type' in update_line:
            return match.group(0)  # Уже есть, не меняем
        
        # Добавляем generation_type
        new_update = update_line.replace(')', ", generation_type='song')")
        
        return func_part + new_update
    
    new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    return new_content

def main():
    print("=" * 60)
    print("КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ГЕНЕРАЦИИ")
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
    
    # ========== ВАРИАНТ 1: Умный обработчик ==========
    
    log("ВАРИАНТ 1: Установка умного обработчика...", "🔧")
    
    # Удаляем старый обработчик
    pattern = r'# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========.*?(?=\n# =====|\n@dp\.|\nasync def |\nif __name__|$)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Находим место вставки
    main_match = re.search(r'if __name__ == ["\']__main__["\']:', content)
    
    if not main_match:
        log("ОШИБКА: Не найден if __name__", "❌")
        return False
    
    # Вставляем новый обработчик
    new_handler = get_smart_handler()
    content = content[:main_match.start()] + new_handler + content[main_match.start():]
    
    log("✅ Умный обработчик установлен", "✅")
    
    # ========== ВАРИАНТ 2: Установка generation_type ==========
    
    log("ВАРИАНТ 2: Добавление generation_type в process_song_style...", "🔧")
    
    updated_content = update_process_song_style(content)
    
    if updated_content != content:
        content = updated_content
        log("✅ generation_type='song' добавлен в состояние", "✅")
    else:
        log("⚠️  generation_type уже установлен или не найдена нужная строка", "⚠️")
    
    # ========== Сохранение и проверка ==========
    
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        log("КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ПРИМЕНЕНО!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\nИзменения:")
        print("  ✅ Вариант 1: Умный обработчик (автоопределение типа)")
        print("  ✅ Вариант 2: Явная установка generation_type")
        print("\nПреимущества:")
        print("  • Работает даже если забыли установить тип")
        print("  • Чистая архитектура с явным указанием")
        print("  • Подробное логирование")
        print("  • Защита от ошибок")
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
