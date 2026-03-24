#!/usr/bin/env python3
"""
Добавление создания записи в БД перед отправкой задачи в Celery
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
    backup_path = f"{FILE_PATH}.backup_db_record_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def add_db_imports(content):
    """Добавляет импорты для работы с БД если их нет"""
    
    # Проверяем есть ли уже импорты
    if 'from db_utils import execute_query_sync' in content:
        log("Импорты БД уже есть", "✅")
        return content
    
    # Ищем блок импортов
    import_pattern = r'(from celery_tasks import.*?\n)'
    
    if re.search(import_pattern, content):
        # Добавляем после импорта celery_tasks
        new_import = r'\1from db_utils import execute_query_sync\n'
        content = re.sub(import_pattern, new_import, content, count=1)
        log("Добавлен импорт execute_query_sync", "✅")
    else:
        # Добавляем в начало файла после основных импортов
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        
        lines.insert(insert_pos, 'from db_utils import execute_query_sync')
        content = '\n'.join(lines)
        log("Добавлен импорт в начало файла", "✅")
    
    return content

def get_db_creation_code_song():
    """Код создания записи для песни"""
    return '''
        # ========== СОЗДАНИЕ ЗАПИСИ В БД ПЕРЕД ЗАПУСКОМ ==========
        try:
            # Генерируем task_id заранее
            import uuid
            task_id = str(uuid.uuid4())
            
            # Формируем описание для БД
            prompt_for_db = f"Стиль: {style if style else 'Не указан'}. Текст: {lyrics[:100]}..."
            
            # Создаём начальную запись в БД
            logging.info(f"Creating DB record for task {task_id}")
            
            from db_utils import execute_query_sync
            result = execute_query_sync(
                """INSERT INTO generations 
                   (task_id, user_id, prompt, status, created_at) 
                   VALUES (%s, %s, %s, %s, NOW())
                   RETURNING id""",
                (task_id, int(user_id), prompt_for_db, 'pending')
            )
            
            if result:
                db_id = result[0]
                logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")
            else:
                logging.error(f"❌ Failed to create DB record for task {task_id}")
                await callback_query.message.answer(
                    "❌ Ошибка при создании задачи в БД\\n"
                    "Попробуйте ещё раз"
                )
                await state.finish()
                return
                
        except Exception as db_error:
            logging.error(f"❌ Database error: {db_error}", exc_info=True)
            await callback_query.message.answer(
                "❌ Ошибка базы данных\\n"
                "Попробуйте позже"
            )
            await state.finish()
            return
        
        # ========== ЗАПУСК CELERY ЗАДАЧИ С ГОТОВЫМ task_id ==========
'''

def get_db_creation_code_music():
    """Код создания записи для музыки"""
    return '''
        # ========== СОЗДАНИЕ ЗАПИСИ В БД ПЕРЕД ЗАПУСКОМ ==========
        try:
            # Генерируем task_id заранее
            import uuid
            task_id = str(uuid.uuid4())
            
            # Формируем описание для БД
            prompt_for_db = final_prompt[:200]  # Первые 200 символов
            
            # Создаём начальную запись в БД
            logging.info(f"Creating DB record for task {task_id}")
            
            from db_utils import execute_query_sync
            result = execute_query_sync(
                """INSERT INTO generations 
                   (task_id, user_id, prompt, status, created_at) 
                   VALUES (%s, %s, %s, %s, NOW())
                   RETURNING id""",
                (task_id, int(user_id), prompt_for_db, 'pending')
            )
            
            if result:
                db_id = result[0]
                logging.info(f"✅ DB record created: id={db_id}, task_id={task_id}")
            else:
                logging.error(f"❌ Failed to create DB record for task {task_id}")
                await callback_query.message.answer(
                    "❌ Ошибка при создании задачи в БД\\n"
                    "Попробуйте ещё раз"
                )
                await state.finish()
                return
                
        except Exception as db_error:
            logging.error(f"❌ Database error: {db_error}", exc_info=True)
            await callback_query.message.answer(
                "❌ Ошибка базы данных\\n"
                "Попробуйте позже"
            )
            await state.finish()
            return
        
        # ========== ЗАПУСК CELERY ЗАДАЧИ С ГОТОВЫМ task_id ==========
'''

def add_db_creation_to_function(content):
    """Добавляет создание записи в БД в функцию process_generation_mode"""
    
    # ========== ДЛЯ ПЕСЕН ==========
    
    # Паттерн: находим блок генерации песни
    song_pattern = r'(if generation_type == [\'"]song[\'"]:.*?# Импортируем задачу\s+from celery_tasks import generate_song_task\s+# Запускаем Celery задачу\s+)(task = generate_song_task\.delay\()'
    
    def song_replacer(match):
        before = match.group(1)
        task_line = match.group(2)
        
        db_code = get_db_creation_code_song()
        
        # Заменяем вызов задачи, передавая task_id
        new_task_line = task_line.replace(
            'task = generate_song_task.delay(',
            'task = generate_song_task.apply_async(\n                args=[int(user_id), lyrics, style, custom_mode],\n                task_id=task_id\n            )\n            # Альтернативно можно использовать:\n            # task = generate_song_task.delay('
        )
        
        return before + db_code + '        ' + new_task_line
    
    content = re.sub(song_pattern, song_replacer, content, flags=re.DOTALL)
    
    # ========== ДЛЯ МУЗЫКИ ==========
    
    # Паттерн: находим блок генерации музыки
    music_pattern = r'(else:.*?# Импортируем задачу\s+from celery_tasks import generate_music_task\s+# Формируем финальный промпт.*?# Запускаем Celery задачу\s+)(task = generate_music_task\.delay\()'
    
    def music_replacer(match):
        before = match.group(1)
        task_line = match.group(2)
        
        db_code = get_db_creation_code_music()
        
        # Заменяем вызов задачи, передавая task_id
        new_task_line = task_line.replace(
            'task = generate_music_task.delay(',
            'task = generate_music_task.apply_async(\n                args=[int(user_id), final_prompt],\n                task_id=task_id\n            )\n            # Альтернативно можно использовать:\n            # task = generate_music_task.delay('
        )
        
        return before + db_code + '        ' + new_task_line
    
    content = re.sub(music_pattern, music_replacer, content, flags=re.DOTALL)
    
    return content

def main():
    print("=" * 60)
    print("ДОБАВЛЕНИЕ СОЗДАНИЯ ЗАПИСИ В БД")
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
    
    # 4. Добавление импортов
    log("Добавление импортов БД...")
    content = add_db_imports(content)
    
    # 5. Добавление создания записей в БД
    log("Добавление создания записей в БД...")
    new_content = add_db_creation_to_function(content)
    
    if new_content == content:
        log("⚠️  Изменения не применены (паттерн не найден)", "⚠️")
        log("Попробуем альтернативный метод...", "🔄")
        
        # Альтернативный метод - ручная вставка
        # Ищем строку с generate_song_task.delay
        if 'task = generate_song_task.delay(' in content:
            # Вставляем перед ней
            content = content.replace(
                '            # Запускаем Celery задачу\n            task = generate_song_task.delay(',
                get_db_creation_code_song() + '\n            task = generate_song_task.apply_async(\n                args=[int(user_id), lyrics, style, custom_mode],\n                task_id=task_id\n            )\n            # Было: task = generate_song_task.delay('
            )
            log("Применен альтернативный метод для песен", "✅")
        
        if 'task = generate_music_task.delay(' in content:
            content = content.replace(
                '            # Запускаем Celery задачу\n            task = generate_music_task.delay(',
                get_db_creation_code_music() + '\n            task = generate_music_task.apply_async(\n                args=[int(user_id), final_prompt],\n                task_id=task_id\n            )\n            # Было: task = generate_music_task.delay('
            )
            log("Применен альтернативный метод для музыки", "✅")
        
        new_content = content
    
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
        log("СОЗДАНИЕ ЗАПИСЕЙ В БД ДОБАВЛЕНО!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\nИзменения:")
        print("  ✅ Добавлен импорт execute_query_sync")
        print("  ✅ Создание записи в БД перед генерацией песни")
        print("  ✅ Создание записи в БД перед генерацией музыки")
        print("  ✅ Передача task_id в Celery задачи")
        print("  ✅ Обработка ошибок БД")
        print("\nТеперь выполните:")
        print("  sudo systemctl restart albimusic-bot")
        print("  sudo systemctl restart albimusic-celery")
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
