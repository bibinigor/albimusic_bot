#!/usr/bin/env python3
"""
Финальное комплексное исправление:
1. Удаление мусорного кода
2. Добавление создания записи в БД
3. Исправление отступов
4. Проверка синтаксиса
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
    backup_path = f"{FILE_PATH}.backup_final_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def get_complete_fixed_function():
    """Полностью исправленная функция с созданием записи в БД"""
    return '''@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Умный обработчик выбора режима генерации
    Автоматически определяет тип по данным в состоянии
    Создает запись в БД перед отправкой в Celery
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
                "Попробуйте начать заново с кнопки 🎵 Создать песню"
            )
            await state.finish()
            return
        
        # Получаем дополнительные параметры
        style = state_data.get('style', '').strip()
        
        mode_name = 'Творческий режим' if mode == 'creative' else 'Точный режим'
        custom_mode = (mode == 'creative')
        
        logging.info(f"User {user_id} selected {mode_name} for {generation_type.upper()} generation")
        
        # Уведомляем пользователя о начале
        type_emoji = "🎤" if generation_type == 'song' else "🎵"
        type_text = "песни" if generation_type == 'song' else "музыки"
        
        await callback_query.message.answer(
            f"{type_emoji} Начинаем генерацию {type_text}\\n"
            f"✅ Режим: {mode_name}\\n\\n"
            "⏱ Подготовка займёт 1-2 минуты..."
        )
        
        # ========== ГЕНЕРАЦИЯ И ЗАПУСК ЗАДАЧИ ==========
        
        if generation_type == 'song':
            # --- ГЕНЕРАЦИЯ ПЕСНИ ---
            
            if not lyrics:
                logging.error(f"Song generation requested but no lyrics found!")
                await callback_query.message.answer("❌ Ошибка: текст песни не найден")
                await state.finish()
                return
            
            logging.info(f"Starting SONG generation for user {user_id}")
            logging.info(f"  Style: '{style}'")
            logging.info(f"  Lyrics length: {len(lyrics)} chars")
            logging.info(f"  Mode: {'Creative' if custom_mode else 'Exact'}")
            
            # ========== СОЗДАНИЕ ЗАПИСИ В БД ==========
            try:
                # Генерируем task_id заранее
                import uuid
                task_id = str(uuid.uuid4())
                
                # Формируем описание для БД
                style_text = style if style else 'Не указан'
                lyrics_preview = lyrics[:100] + ('...' if len(lyrics) > 100 else '')
                prompt_for_db = f"Стиль: {style_text}. Текст: {lyrics_preview}"
                
                # Создаём начальную запись в БД
                logging.info(f"📝 Creating DB record for song task {task_id}")
                
                from db_utils import execute_query_sync
                result = execute_query_sync(
                    """INSERT INTO generations 
                       (task_id, user_id, prompt, status, created_at) 
                       VALUES (%s, %s, %s, %s, NOW())
                       RETURNING id""",
                    (task_id, int(user_id), prompt_for_db, 'pending')
                )
                
                if result and len(result) > 0:
                    db_id = result[0][0]
                    logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")
                else:
                    logging.error(f"❌ Failed to create DB record for task {task_id}")
                    await callback_query.message.answer(
                        "❌ Ошибка при создании задачи в БД\\n"
                        "Попробуйте ещё раз через минуту"
                    )
                    await state.finish()
                    return
                    
            except Exception as db_error:
                logging.error(f"❌ Database error: {db_error}", exc_info=True)
                await callback_query.message.answer(
                    "❌ Ошибка базы данных\\n"
                    "Попробуйте позже или обратитесь в поддержку"
                )
                await state.finish()
                return
            
            # ========== ЗАПУСК CELERY ЗАДАЧИ ==========
            try:
                from celery_tasks import generate_song_task
                
                # Запускаем задачу с явным task_id
                task = generate_song_task.apply_async(
                    args=[int(user_id), lyrics, style, custom_mode],
                    task_id=task_id
                )
                
                logging.info(f"🚀 Song generation Celery task started: {task.id}")
                
                await callback_query.message.answer(
                    f"✅ Задача создания песни запущена\\n"
                    f"📋 ID: {task.id[:8]}...\\n\\n"
                    f"Ожидайте результат в течение 2-3 минут"
                )
                
            except Exception as celery_error:
                logging.error(f"❌ Celery error: {celery_error}", exc_info=True)
                
                # Обновляем статус в БД на failed
                try:
                    execute_query_sync(
                        "UPDATE generations SET status = %s WHERE task_id = %s",
                        ('failed', task_id)
                    )
                except:
                    pass
                
                await callback_query.message.answer(
                    "❌ Ошибка при запуске генерации\\n"
                    "Попробуйте позже"
                )
                await state.finish()
                return
            
        else:
            # --- ГЕНЕРАЦИЯ МУЗЫКИ ---
            
            if not prompt:
                logging.error(f"Music generation requested but no prompt found!")
                await callback_query.message.answer("❌ Ошибка: описание музыки не найдено")
                await state.finish()
                return
            
            logging.info(f"Starting MUSIC generation for user {user_id}")
            logging.info(f"  Prompt: '{prompt[:100]}...'")
            logging.info(f"  Mode: {'Creative' if custom_mode else 'Exact'}")
            
            # Формируем финальный промпт
            final_prompt = f"{prompt}. {'творческая интерпретация' if custom_mode else 'точное соответствие'}"
            
            # ========== СОЗДАНИЕ ЗАПИСИ В БД ==========
            try:
                # Генерируем task_id заранее
                import uuid
                task_id = str(uuid.uuid4())
                
                # Формируем описание для БД (первые 200 символов)
                prompt_for_db = final_prompt[:200] + ('...' if len(final_prompt) > 200 else '')
                
                # Создаём начальную запись в БД
                logging.info(f"📝 Creating DB record for music task {task_id}")
                
                from db_utils import execute_query_sync
                result = execute_query_sync(
                    """INSERT INTO generations 
                       (task_id, user_id, prompt, status, created_at) 
                       VALUES (%s, %s, %s, %s, NOW())
                       RETURNING id""",
                    (task_id, int(user_id), prompt_for_db, 'pending')
                )
                
                if result and len(result) > 0:
                    db_id = result[0][0]
                    logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")
                else:
                    logging.error(f"❌ Failed to create DB record for task {task_id}")
                    await callback_query.message.answer(
                        "❌ Ошибка при создании задачи в БД\\n"
                        "Попробуйте ещё раз через минуту"
                    )
                    await state.finish()
                    return
                    
            except Exception as db_error:
                logging.error(f"❌ Database error: {db_error}", exc_info=True)
                await callback_query.message.answer(
                    "❌ Ошибка базы данных\\n"
                    "Попробуйте позже или обратитесь в поддержку"
                )
                await state.finish()
                return
            
            # ========== ЗАПУСК CELERY ЗАДАЧИ ==========
            try:
                from celery_tasks import generate_music_task
                
                # Запускаем задачу с явным task_id
                task = generate_music_task.apply_async(
                    args=[int(user_id), final_prompt],
                    task_id=task_id
                )
                
                logging.info(f"🚀 Music generation Celery task started: {task.id}")
                
                await callback_query.message.answer(
                    f"✅ Задача создания музыки запущена\\n"
                    f"📋 ID: {task.id[:8]}...\\n\\n"
                    f"Ожидайте результат в течение 2-3 минут"
                )
                
            except Exception as celery_error:
                logging.error(f"❌ Celery error: {celery_error}", exc_info=True)
                
                # Обновляем статус в БД на failed
                try:
                    execute_query_sync(
                        "UPDATE generations SET status = %s WHERE task_id = %s",
                        ('failed', task_id)
                    )
                except:
                    pass
                
                await callback_query.message.answer(
                    "❌ Ошибка при запуске генерации\\n"
                    "Попробуйте позже"
                )
                await state.finish()
                return
        
        # Завершаем состояние
        await state.finish()
        
    except Exception as e:
        logging.error(f"❌ Critical error in process_generation_mode: {e}", exc_info=True)
        try:
            await callback_query.message.answer(
                "❌ Произошла критическая ошибка\\n"
                "Попробуйте ещё раз или обратитесь в поддержку"
            )
            await state.finish()
        except:
            pass


'''

def main():
    print("=" * 60)
    print("ФИНАЛЬНОЕ КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ")
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
    
    # 4. Удаление ВСЕХ вхождений process_generation_mode
    log("Удаление всех старых версий функции...")
    
    # Паттерн для поиска функции (включая мусор после неё)
    pattern = r'@dp\.callback_query_handler\(lambda c: c\.data and c\.data\.startswith\([\'"]mode_[\'"]\).*?\).*?async def process_generation_mode.*?(?=\n@dp\.|async def [a-z_]+\(|if __name__|$)'
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    log(f"Найдено вхождений: {len(matches)}", "🔍")
    
    # Удаляем все вхождения (от последнего к первому)
    for i, match in enumerate(reversed(matches)):
        log(f"Удаляем вхождение {len(matches) - i} на позиции {match.start()}", "🗑️")
        content = content[:match.start()] + content[match.end():]
    
    # 5. Удаление мусорных строк
    log("Очистка мусорного кода...")
    
    # Удаляем строки типа "if name == '__main__':" внутри кода
    content = re.sub(r'\n\s*if name == [\'"]__main__[\'"]:.*?\n', '\n', content)
    
    # Удаляем лишние декораторы
    content = re.sub(r'\n\s*# ========== ОБРАБОТЧИК РЕЖИМА ГЕНЕРАЦИИ ==========\s*\n\s*@dp\.callback_query_handler.*?\n(?!async def)', '\n', content)
    
    # 6. Поиск места для вставки
    log("Поиск места для вставки правильной функции...")
    
    # Ищем if __name__ == '__main__':
    main_match = re.search(r'if __name__ == ["\']__main__["\']:', content)
    
    if not main_match:
        log("ОШИБКА: Не найден if __name__", "❌")
        return False
    
    insert_pos = main_match.start()
    log(f"Место вставки: позиция {insert_pos}", "✅")
    
    # 7. Вставка правильной функции
    log("Вставка исправленной функции...")
    correct_function = get_complete_fixed_function()
    
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
        log("ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\n📋 Что исправлено:")
        print("  ✅ Удален весь мусорный код")
        print("  ✅ Добавлена умная логика определения типа")
        print("  ✅ Создание записи в БД перед Celery")
        print("  ✅ Передача task_id в Celery задачи")
        print("  ✅ Исправлены все отступы")
        print("  ✅ Добавлена полная обработка ошибок")
        print("  ✅ Улучшено логирование")
        print("\n🚀 Следующие шаги:")
        print("  1. sudo systemctl restart albimusic-bot")
        print("  2. sudo systemctl restart albimusic-celery")
        print("  3. ./monitor_db_creation.sh")
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
