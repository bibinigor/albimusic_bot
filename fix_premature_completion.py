#!/usr/bin/env python3
"""
Исправление преждевременного статуса completed:
1. Убираем finally блок
2. Добавляем обработку всех статусов Suno
3. Сохраняем статус только после реального завершения
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
    backup_path = f"{FILE_PATH}.backup_completion_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def fix_generate_song_task(content):
    """Убирает finally блок и добавляет правильное сохранение статуса"""
    
    # Паттерн для поиска функции generate_song_task
    pattern = r'(def generate_song_task\([^)]+\):.*?)(finally:.*?execute_query_sync.*?\))'
    
    if not re.search(pattern, content, re.DOTALL):
        log("finally блок не найден в generate_song_task", "⚠️")
        return content, False
    
    # Заменяем finally на явное сохранение в try
    def replacement(match):
        func_start = match.group(1)
        
        # Новый код без finally
        new_code = func_start + '''
        
        # ✅ Сохраняем статус после завершения генерации
        if not audio_url:
            result_status = 'error'
            result_message = 'Генерация не удалась'
        else:
            result_status = 'completed'
            result_message = 'Генерация успешна'
        
        execute_query_sync(
            "UPDATE generations SET status = %s, audio_url = %s, result_message = %s, updated_at = NOW() WHERE task_id = %s",
            (result_status, audio_url or '', result_message, task_id)
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в generate_song_task: {e}", exc_info=True)
        try:
            execute_query_sync(
                "UPDATE generations SET status = 'error', error_message = %s, updated_at = NOW() WHERE task_id = %s",
                (str(e)[:500], task_id)
            )
        except Exception as db_error:
            logger.error(f"❌ Не удалось сохранить ошибку в БД: {db_error}")
'''
        
        return new_code
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    log("finally блок заменен на явное сохранение", "✅")
    return new_content, True

def fix_suno_status_handling(content):
    """Добавляет обработку всех статусов Suno API"""
    
    # Ищем блок обработки статусов
    pattern = r"(elif status in \['PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS'\]:.*?continue)"
    
    replacement = r"""elif status in ['PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS', 'PROCESSING', 'QUEUED']:
                    logger.info(f"⏳ Ожидание генерации... Статус: {status} (попытка {i+1}/90)")
                    continue"""
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Добавляем обработку неизвестных статусов
    pattern2 = r"(else:.*?logger\.error.*?return None)"
    
    replacement2 = r"""elif status in ['FAILED', 'ERROR']:
                    logger.error(f"❌ Генерация провалилась со статусом: {status}")
                    return None
                else:
                    logger.warning(f"⚠️ Неизвестный статус Suno: {status}, продолжаем ожидание...")
                    continue  # ✅ НЕ ПРЕРЫВАЕМ"""
    
    new_content = re.sub(pattern2, replacement2, new_content, flags=re.DOTALL)
    
    log("Обработка статусов Suno улучшена", "✅")
    return new_content, True

def main():
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ ПРЕЖДЕВРЕМЕННОГО COMPLETED")
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
    
    # 4. Исправление generate_song_task
    log("Исправление generate_song_task...")
    content, modified1 = fix_generate_song_task(content)
    
    # 5. Исправление обработки статусов
    log("Исправление обработки статусов Suno...")
    content, modified2 = fix_suno_status_handling(content)
    
    if not (modified1 or modified2):
        log("Изменений не требуется", "ℹ️")
        return True
    
    # 6. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        log("ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!", "✅")
        print("=" * 60)
        print(f"\nBackup: {backup_path}")
        print("\n📋 Что исправлено:")
        print("  ✅ Убран finally блок")
        print("  ✅ Статус сохраняется только после реального завершения")
        print("  ✅ Добавлена обработка всех статусов Suno")
        print("  ✅ Неизвестные статусы не прерывают ожидание")
        print("\n🚀 Следующий шаг:")
        print("  sudo systemctl restart albimusic-bot")
        print("  sudo systemctl restart albimusic-celery")
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
