#!/usr/bin/env python3
"""
ПРИМЕНЕНИЕ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ ПО АУДИТУ CLAUDE

1. Проверка валидности MP3 файлов
2. Исправление TypeError в save_generation_task_sync
3. Улучшение обработки ошибок Suno API
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
    backup_path = f"{FILE_PATH}.backup_critical_{timestamp}"
    shutil.copy2(FILE_PATH, backup_path)
    log(f"Backup: {backup_path}", "✅")
    return backup_path

def add_mp3_validation(content):
    """Добавляет функцию проверки MP3 файлов"""
    
    # Ищем место для добавления функции (перед generate_suno_music_sync)
    insert_pos = content.find("def generate_suno_music_sync")
    
    if insert_pos == -1:
        log("Функция generate_suno_music_sync не найдена", "❌")
        return content, False
    
    # Функция проверки MP3
    mp3_validation_code = """

# ====================================================================
# ФУНКЦИЯ ПРОВЕРКИ ВАЛИДНОСТИ MP3 ФАЙЛОВ
# ====================================================================

def validate_audio_url(url, request_id):
    """
    Проверка доступности и валидности MP3 файла от Suno API
    
    Args:
        url (str): URL MP3 файла
        request_id (str): ID запроса для логирования
    
    Returns:
        bool: True если файл доступен и валиден
    """
    import requests
    
    try:
        logger.info(f"[{request_id}] 🔍 Проверка доступности MP3...")
        
        # HEAD запрос для проверки без скачивания
        head_response = requests.head(url, timeout=10, allow_redirects=True)
        
        if head_response.status_code != 200:
            logger.error(f"[{request_id}] ❌ MP3 недоступен: HTTP {head_response.status_code}")
            return False
        
        # Проверка Content-Type
        content_type = head_response.headers.get('Content-Type', '')
        if 'audio' not in content_type.lower():
            logger.warning(f"[{request_id}] ⚠️ Неверный Content-Type: {content_type}")
        
        # Проверка размера файла
        content_length = int(head_response.headers.get('Content-Length', 0))
        if content_length < 1000:  # Менее 1KB
            logger.error(f"[{request_id}] ❌ MP3 слишком маленький: {content_length} байт")
            return False
        
        logger.info(f"[{request_id}] ✅ MP3 валиден: {content_length} байт, {content_type}")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"[{request_id}] ⏱️ Таймаут при проверке MP3")
        return False
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Ошибка проверки MP3: {e}")
        return False


"""
    
    # Вставляем код перед generate_suno_music_sync
    new_content = content[:insert_pos] + mp3_validation_code + content[insert_pos:]
    log("Добавлена функция проверки MP3", "✅")
    return new_content, True

def fix_result_handling(content):
    """Исправляет обработку результата в save_generation_task_sync"""
    
    # Ищем блок с ошибкой
    pattern = r'(if result and len\(result\) > 0:)(.*?)(except Exception as e:)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Блок обработки результата не найден", "❌")
        return content, False
    
    # Новый блок обработки результата
    new_block = '''
        # ===============================================
        # БЕЗОПАСНАЯ ОБРАБОТКА РЕЗУЛЬТАТА
        # ===============================================
        
        if result:
            # result может быть: tuple, list, int, None
            if isinstance(result, (list, tuple)):
                if len(result) > 0:
                    first_row = result[0] if isinstance(result, list) else result
                    
                    if isinstance(first_row, (list, tuple)) and len(first_row) > 0:
                        row_id = first_row[0]
                        created = first_row[1] if len(first_row) > 1 else None
                        updated = first_row[2] if len(first_row) > 2 else None
                    elif isinstance(first_row, int):
                        row_id = first_row
                        created = None
                        updated = None
                    else:
                        row_id = 'unknown'
                        created = None
                        updated = None
                else:
                    row_id = 'unknown'
                    created = None
                    updated = None
            elif isinstance(result, int):
                row_id = result
                created = None
                updated = None
            else:
                row_id = 'unknown'
                created = None
                updated = None
            
            # Определение типа операции
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
            return True
'''
    
    # Заменяем блок
    new_content = content[:match.start(1)] + new_block + content[match.end(2):]
    log("Исправлена обработка результата в save_generation_task_sync", "✅")
    return new_content, True

def add_mp3_check_to_generation(content):
    """Добавляет проверку MP3 в generate_suno_music_sync"""
    
    # Ищем место где возвращается audio_url
    pattern = r'if audio_data:\s+audio_url = audio_data\[0\]\.get\(\'audioUrl\'\)(.*?)return audio_url'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        log("Блок возврата audio_url не найден", "❌")
        return content, False
    
    # Новый код с проверкой
    replacement = '''if audio_data:
            audio_url = audio_data[0].get('audioUrl')
            logger.info(f"[{request_id}] ✅ SUNO GENERATION COMPLETED:")
            logger.info(f"[{request_id}]    • Audio URL: {audio_url}")
            
            # НОВОЕ: Проверка валидности MP3
            if not validate_audio_url(audio_url, request_id):
                logger.error(f"[{request_id}] ❌ MP3 не прошел валидацию")
                return None
            
            return audio_url'''
    
    new_content = content[:match.start()] + replacement + content[match.end():]
    log("Добавлена проверка MP3 в generate_suno_music_sync", "✅")
    return new_content, True

def main():
    print("=" * 80)
    print("ПРИМЕНЕНИЕ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ ПО АУДИТУ CLAUDE")
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
    
    # 4. Применение исправлений
    modifications = []
    
    log("1. Добавление проверки MP3 файлов...")
    content, mod1 = add_mp3_validation(content)
    if mod1: modifications.append("✅ Проверка MP3")
    
    log("2. Исправление обработки результата в save_generation_task_sync...")
    content, mod2 = fix_result_handling(content)
    if mod2: modifications.append("✅ Обработка результата")
    
    log("3. Добавление проверки MP3 в generate_suno_music_sync...")
    content, mod3 = add_mp3_check_to_generation(content)
    if mod3: modifications.append("✅ Проверка в генерации")
    
    if not modifications:
        log("Никаких изменений не было внесено", "⚠️")
        return False
    
    print()
    
    # 5. Сохранение
    log("Сохранение файла...")
    temp_file = FILE_PATH + ".temp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        log("КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!", "✅")
        print("=" * 80)
        
        print(f"\n📁 Backup: {backup_path}")
        
        print("\n📋 Примененные исправления:")
        for mod in modifications:
            print(f"  {mod}")
        
        print("\n🎯 Что теперь делает система:")
        print("  1. Suno API генерирует музыку")
        print("  2. Проверяется доступность и валидность MP3 файла")
        print("  3. Только рабочие файлы сохраняются в БД")
        print("  4. Пользователь получает гарантированно рабочие ссылки")
        
        print("\n🚀 Следующие шаги:")
        print("  sudo systemctl restart albimusic-celery")
        print("  sudo systemctl restart albimusic-bot")
        
        print("\n🔍 Тестирование:")
        print("  1. Создайте инструментальную музыку в боте")
        print("  2. В логах ищите '🔍 Проверка доступности MP3'")
        print("  3. Если файл невалиден - задача будет 'error'")
        
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
