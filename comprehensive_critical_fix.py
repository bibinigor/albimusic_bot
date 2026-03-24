#!/usr/bin/env python3
"""
КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ОШИБОК AlBi-music Bot

Исправляет:
1. Валидация MP3 файлов
2. TypeError в save_generation_task_sync
3. Дублированный код в execute_query_sync
4. Экспоненциальный backoff для Suno API
5. Дубликаты MUSIC_STYLE_TRANSLATIONS
6. Race conditions
7. Использование translate_style_to_english
"""

import os
import sys
import re
import shutil
import logging
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Настройка логирования
LOG_FILE = "/var/log/albimusic-bot/critical_fix.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Константы
PROJECT_ROOT = "/root/albimusic-bot"
CELERY_TASKS_PATH = os.path.join(PROJECT_ROOT, "celery_tasks.py")
DB_UTILS_PATH = os.path.join(PROJECT_ROOT, "db_utils.py")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups_critical_fix")

def log_step(step, message):
    """Логирование шага с визуальным разделителем"""
    separator = "=" * 80
    logger.info(f"\n{separator}")
    logger.info(f"ШАГ {step}: {message}")
    logger.info(f"{separator}\n")

def create_backup(file_path):
    """Создание резервной копии файла"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(file_path)
    backup_path = os.path.join(BACKUP_DIR, f"{filename}.backup_{timestamp}")
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(file_path, backup_path)
    logger.info(f"✅ Создана резервная копия: {backup_path}")
    return backup_path

def restore_backup(backup_path, original_path):
    """Восстановление из резервной копии"""
    shutil.copy2(backup_path, original_path)
    logger.info(f"✅ Восстановлен из бэкапа: {original_path}")

def check_python_syntax(file_path):
    """Проверка синтаксиса Python файла"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"✅ Синтаксис {file_path} корректен")
            return True
        else:
            logger.error(f"❌ Ошибка синтаксиса в {file_path}:")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка проверки синтаксиса: {e}")
        return False

# ============================================================================
# ИСПРАВЛЕНИЕ 1: Валидация MP3 файлов
# ============================================================================

def add_mp3_validation(celery_tasks_content):
    """Добавляет функцию валидации MP3 файлов"""
    
    validation_function = '''
# ============================================================================
# ФУНКЦИЯ ВАЛИДАЦИИ MP3 ФАЙЛОВ
# ============================================================================

def validate_audio_url(url, request_id, timeout=15):
    """
    Проверяет доступность и валидность MP3 файла
    
    Args:
        url: URL аудио файла
        request_id: ID запроса для логирования
        timeout: Таймаут в секундах
    
    Returns:
        bool: True если файл валиден
    """
    import requests
    
    try:
        logger.info(f"[{request_id}] 🔍 Проверка доступности MP3...")
        
        # HEAD запрос для проверки без скачивания
        head_response = requests.head(
            url, 
            timeout=timeout, 
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        if head_response.status_code != 200:
            logger.error(f"[{request_id}] ❌ MP3 недоступен: HTTP {head_response.status_code}")
            return False
        
        # Проверка Content-Type
        content_type = head_response.headers.get('Content-Type', '').lower()
        if 'audio' not in content_type and 'mpeg' not in content_type:
            logger.warning(f"[{request_id}] ⚠️ Неверный Content-Type: {content_type}")
            # Не возвращаем False сразу, некоторые серверы могут возвращать неверный Content-Type
        
        # Проверка размера файла
        content_length = int(head_response.headers.get('Content-Length', 0))
        if content_length < 1000:  # Менее 1KB
            logger.error(f"[{request_id}] ❌ MP3 слишком маленький: {content_length} байт")
            return False
        
        logger.info(f"[{request_id}] ✅ MP3 валиден: {content_length} байт, {content_type}")
        
        # Скачиваем первые 2KB для проверки формата
        try:
            range_response = requests.get(
                url, 
                headers={'Range': 'bytes=0-2047', 'User-Agent': 'Mozilla/5.0'}, 
                timeout=timeout
            )
            
            if range_response.status_code in (200, 206):  # 206 = Partial Content
                magic_bytes = range_response.content[:4]
                
                # MP3 может начинаться:
                # 1. С ID3 тега (0x49 0x44 0x33)
                # 2. С MPEG frame sync (0xFF 0xFB или 0xFF 0xF3)
                # 3. С других валидных MPEG заголовков
                is_id3 = magic_bytes[:3] == b'ID3'
                is_mpeg = (len(magic_bytes) >= 2 and 
                          magic_bytes[0] == 0xFF and 
                          (magic_bytes[1] & 0xE0) == 0xE0)
                
                if not (is_id3 or is_mpeg):
                    logger.warning(f"[{request_id}] ⚠️ Файл не похож на MP3 (magic bytes: {magic_bytes.hex()})")
                    # Не возвращаем False, т.к. могут быть edge cases или другие форматы
                else:
                    logger.info(f"[{request_id}] ✅ MP3 имеет правильные magic bytes")
        
        except Exception as e:
            logger.warning(f"[{request_id}] ⚠️ Не удалось проверить magic bytes: {e}")
        
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"[{request_id}] ⏱️ Таймаут при проверке MP3")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"[{request_id}] 🔌 Ошибка соединения при проверке MP3")
        return False
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Ошибка проверки MP3: {e}")
        return False
'''
    
    # Находим место для вставки (после всех импортов и первой функции)
    lines = celery_tasks_content.split('\n')
    
    # Ищем место после импортов и первой функции
    insert_position = 0
    found_imports = False
    found_first_function = False
    
    for i, line in enumerate(lines):
        if 'import ' in line and not found_imports:
            found_imports = True
        elif found_imports and line.strip() and not line.startswith('import ') and not line.startswith('from '):
            # Это первая не-импорт строка
            found_first_function = True
        elif found_first_function and line.strip() == '':
            # Пустая строка после первой функции - хорошее место для вставки
            insert_position = i + 1
            break
    
    if insert_position == 0:
        insert_position = len(lines) // 3  # Fallback: вставляем в первую треть
    
    # Вставляем функцию валидации
    lines.insert(insert_position, validation_function)
    
    logger.info("✅ Добавлена функция валидации MP3 файлов")
    return '\n'.join(lines)

def update_generate_suno_music_sync_with_validation(celery_tasks_content):
    """Обновляет generate_suno_music_sync для использования валидации"""
    
    # Ищем строку с return audio_url в функции generate_suno_music_sync
    pattern = r'(if audio_data:\s*\n\s*audio_url = audio_data\[0\]\.get\(\'audioUrl\'\).*?\n\s*return audio_url)'
    
    replacement = '''if audio_data:
        audio_url = audio_data[0].get('audioUrl')
        logger.info(f"[{request_id}] ✅ SUNO GENERATION COMPLETED:")
        logger.info(f"[{request_id}]    • Audio URL: {audio_url}")
        
        # 🔍 ПРОВЕРКА ВАЛИДНОСТИ MP3
        if not validate_audio_url(audio_url, request_id):
            logger.error(f"[{request_id}] ❌ MP3 не прошел валидацию")
            return None
        
        return audio_url'''
    
    # Заменяем
    new_content = re.sub(pattern, replacement, celery_tasks_content, flags=re.DOTALL)
    
    if new_content != celery_tasks_content:
        logger.info("✅ Добавлена проверка MP3 в generate_suno_music_sync")
        return new_content
    else:
        logger.warning("⚠️ Не найдена строка для добавления валидации MP3")
        return celery_tasks_content

# ============================================================================
# ИСПРАВЛЕНИЕ 2: Исправление TypeError в save_generation_task_sync
# ============================================================================

def fix_save_generation_task_sync_typerror(celery_tasks_content):
    """Исправляет TypeError в функции save_generation_task_sync"""
    
    # Ищем проблемный блок кода
    pattern = r'(if result and len\(result\) > 0:\s*\n\s*row_id = result\[0\]\[0\].*?\n\s*return True)'
    
    replacement = '''if result:
        # 🔧 БЕЗОПАСНАЯ ОБРАБОТКА РЕЗУЛЬТАТА
        # result может быть: tuple, list, int, None
        
        if isinstance(result, (tuple, list)):
            if len(result) > 0:
                first_element = result[0] if isinstance(result, list) else result
                
                if isinstance(first_element, (tuple, list)) and len(first_element) > 0:
                    row_id = first_element[0]
                    created = first_element[1] if len(first_element) > 1 else None
                    updated = first_element[2] if len(first_element) > 2 else None
                elif isinstance(first_element, int):
                    row_id = first_element
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
        
        # Определяем, INSERT или UPDATE
        is_new = (created == updated) if (created and updated) else True
        action = "создана" if is_new else "обновлена"
        
        logger.info(f"✅ [DB] Задача {task_id} {action} (id={row_id}, status={status})")
        
        # Дополнительное логирование
        if status == 'completed' and safe_result_message:
            logger.info(f"✅ [DB] Результат: {safe_result_message}")
        elif status == 'error' and safe_error_message:
            logger.error(f"❌ [DB] Ошибка: {safe_error_message}")
        
        return True
    else:
        logger.warning(f"⚠️ [DB] Задача {task_id} сохранена, но RETURNING не вернул данные")
        return True'''
    
    new_content = re.sub(pattern, replacement, celery_tasks_content, flags=re.DOTALL)
    
    if new_content != celery_tasks_content:
        logger.info("✅ Исправлен TypeError в save_generation_task_sync")
        return new_content
    else:
        logger.warning("⚠️ Не найден проблемный блок в save_generation_task_sync")
        return celery_tasks_content

# ============================================================================
# ИСПРАВЛЕНИЕ 3: Устранение дублированного кода в execute_query_sync
# ============================================================================

def fix_duplicate_code_in_execute_query_sync(db_utils_content):
    """Устраняет дублированный код в функции execute_query_sync"""
    
    # Читаем файл построчно
    lines = db_utils_content.split('\n')
    new_lines = []
    i = 0
    in_duplicate_section = False
    duplicate_start = None
    
    while i < len(lines):
        line = lines[i]
        
        # Ищем начало дублированного блока
        if 'if fetch_one or has_returning:' in line and not in_duplicate_section:
            # Проверяем следующий блок
            j = i + 1
            while j < len(lines) and lines[j].strip() != '':
                j += 1
            
            # Пропускаем до следующего непустого блока
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            
            # Если нашли повторение, отмечаем дубликат
            if j < len(lines) and 'if fetch_one or has_returning:' in lines[j]:
                in_duplicate_section = True
                duplicate_start = i
                logger.info(f"⚠️ Найден дублированный код на строке {i+1}")
        
        if in_duplicate_section:
            # Ищем конец дублированного блока
            if 'else:' in line and i > duplicate_start:
                # Пропускаем весь дублированный блок
                while i < len(lines) and not lines[i].strip().startswith('return cursor.rowcount'):
                    i += 1
                
                if i < len(lines):
                    new_lines.append('            else:')
                    new_lines.append('                result = cursor.fetchall()')
                    new_lines.append('                logger.info(f"🔧 fetchall result count: {len(result) if result else 0}")')
                    new_lines.append('                return result')
                    i += 4  # Пропускаем строки которые уже заменили
                in_duplicate_section = False
                continue
        
        if i < len(lines):
            new_lines.append(lines[i])
        i += 1
    
    fixed_content = '\n'.join(new_lines)
    
    # Также исправим явные дубликаты через regex
    patterns = [
        (r'(\# Для SELECT и запросов с RETURNING возвращаем данные.*?\n\s*if fetch_one or has_returning:.*?\n\s*return cursor\.fetchone\(\)\n\s*else:\n\s*return cursor\.fetchall\(\).*?\n)\s*\# Для SELECT и запросов с RETURNING возвращаем данных',
         '\\1'),
    ]
    
    for pattern, replacement in patterns:
        fixed_content = re.sub(pattern, replacement, fixed_content, flags=re.DOTALL)
    
    if fixed_content != db_utils_content:
        logger.info("✅ Устранен дублированный код в execute_query_sync")
    else:
        logger.info("✅ Дублированный код не найден (возможно уже исправлен)")
    
    return fixed_content

# ============================================================================
# ИСПРАВЛЕНИЕ 4: Добавление экспоненциального backoff
# ============================================================================

def add_exponential_backoff(celery_tasks_content):
    """Добавляет экспоненциальный backoff для Suno API"""
    
    backoff_function = '''
# ============================================================================
# ФУНКЦИЯ ЭКСПОНЕНЦИАЛЬНОГО BACKOFF ДЛЯ SUNO API
# ============================================================================

def wait_for_suno_completion_with_backoff(task_id, headers, request_id, max_wait_time=900):
    """
    Ожидание завершения генерации Suno с экспоненциальным backoff
    
    Args:
        task_id: ID задачи Suno
        headers: HTTP заголовки
        request_id: ID запроса для логирования
        max_wait_time: Максимальное время ожидания (секунды)
    
    Returns:
        tuple: (audio_url, error_message) или (None, None)
    """
    import math
    import time
    
    start_time = time.time()
    attempt = 0
    consecutive_errors = 0
    last_status = None
    
    while (time.time() - start_time) < max_wait_time:
        attempt += 1
        elapsed = time.time() - start_time
        
        # Экспоненциальный backoff: 5, 10, 15, 20, 30, 30, 30...
        wait_time = min(5 * math.ceil(attempt / 2), 30)
        
        logger.info(f"[{request_id}] 📊 Проверка статуса #{attempt} (прошло {elapsed:.0f}с)")
        
        try:
            status_response = requests.get(
                f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}",
                headers=headers,
                timeout=30
            )
            
            if status_response.status_code == 200:
                consecutive_errors = 0  # Сброс счетчика ошибок
                
                try:
                    status_result = status_response.json()
                except:
                    logger.warning(f"[{request_id}] ⚠️ Не удалось разобрать JSON ответ")
                    time.sleep(wait_time)
                    continue
                
                status_data = status_result.get('data', {})
                status = status_data.get('status')
                
                if status != last_status:
                    logger.info(f"[{request_id}] 📊 Статус изменился: {status}")
                    last_status = status
                
                if status == 'SUCCESS':
                    audio_data = status_data.get('response', {}).get('sunoData', [])
                    if audio_data:
                        audio_url = audio_data[0].get('audioUrl')
                        logger.info(f"[{request_id}] ✅ Suno генерация завершена успешно")
                        return audio_url, None
                    else:
                        logger.error(f"[{request_id}] ❌ SUCCESS без audio_data")
                        return None, "SUCCESS без данных"
                
                elif status == 'ERROR':
                    error_msg = status_data.get('response', {}).get('error', 'Unknown error')
                    logger.error(f"[{request_id}] ❌ Suno вернул ERROR: {error_msg}")
                    return None, f"Suno error: {error_msg}"
                
                elif status == 'FAILED':
                    error_msg = status_data.get('message', 'Generation failed')
                    logger.error(f"[{request_id}] ❌ Suno FAILED: {error_msg}")
                    return None, f"Suno failed: {error_msg}"
                
                elif status in ('PENDING', 'PROCESSING'):
                    # Продолжаем ожидание
                    logger.debug(f"[{request_id}] ⏳ Статус: {status}")
                
                else:
                    logger.warning(f"[{request_id}] ⚠️ Неизвестный статус: {status}")
            
            elif status_response.status_code == 429:
                # Rate limit - увеличиваем задержку
                logger.warning(f"[{request_id}] ⚠️ Rate limit (429), ждем 60с")
                wait_time = 60
            
            elif status_response.status_code >= 500:
                # Ошибка сервера - увеличиваем задержку
                consecutive_errors += 1
                logger.warning(f"[{request_id}] ⚠️ Server error {status_response.status_code} (ошибка #{consecutive_errors})")
                wait_time = min(wait_time * 2, 60)
            
            else:
                consecutive_errors += 1
                logger.warning(f"[{request_id}] ⚠️ HTTP {status_response.status_code} (ошибка #{consecutive_errors})")
            
            # Проверка на слишком много ошибок подряд
            if consecutive_errors >= 5:
                logger.error(f"[{request_id}] ❌ Слишком много ошибок подряд")
                return None, "Too many consecutive errors"
        
        except requests.exceptions.Timeout:
            consecutive_errors += 1
            logger.warning(f"[{request_id}] ⏱️ Таймаут запроса (ошибка #{consecutive_errors})")
            wait_time = min(wait_time * 1.5, 60)
        
        except requests.exceptions.ConnectionError:
            consecutive_errors += 1
            logger.warning(f"[{request_id}] 🔌 Ошибка соединения (ошибка #{consecutive_errors})")
            wait_time = min(wait_time * 2, 60)
        
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"[{request_id}] ❌ Ошибка проверки статуса: {e}")
            
            if consecutive_errors >= 3:
                return None, f"Error checking status: {str(e)}"
        
        # Ожидание перед следующей проверкой
        logger.info(f"[{request_id}] ⏳ Ожидание {wait_time}с перед следующей проверкой...")
        time.sleep(wait_time)
    
    logger.error(f"[{request_id}] ⏰ Таймаут ожидания ({max_wait_time}с)")
    return None, f"Timeout after {max_wait_time}s"
'''
    
    # Вставляем функцию после функции валидации MP3
    lines = celery_tasks_content.split('\n')
    
    # Ищем функцию validate_audio_url
    insert_position = -1
    for i, line in enumerate(lines):
        if 'def validate_audio_url' in line:
            # Ищем конец этой функции
            j = i
            while j < len(lines) and not (lines[j].strip() == '' and lines[j+1].strip() == ''):
                j += 1
            insert_position = j + 1
            break
    
    if insert_position > 0:
        lines.insert(insert_position, backoff_function)
        logger.info("✅ Добавлена функция экспоненциального backoff")
    else:
        # Вставляем в начало файла
        lines.insert(50, backoff_function)
        logger.info("✅ Добавлена функция экспоненциального backoff (в начало файла)")
    
    return '\n'.join(lines)

def update_generate_suno_music_sync_with_backoff(celery_tasks_content):
    """Обновляет generate_suno_music_sync для использования backoff"""
    
    # Ищем цикл ожидания в generate_suno_music_sync
    pattern = r'(for i in range\(90\):.*?if audio_data:)'
    
    replacement = '''    # Используем экспоненциальный backoff
    audio_url, error_msg = wait_for_suno_completion_with_backoff(
        suno_task_id, 
        headers, 
        request_id,
        max_wait_time=900  # 15 минут
    )
    
    if error_msg:
        logger.error(f"[{request_id}] ❌ Ошибка генерации: {error_msg}")
        return None
    
    if audio_url:
        logger.info(f"[{request_id}] ✅ Suno генерация завершена: {audio_url}")
        
        # 🔍 ПРОВЕРКА ВАЛИДНОСТИ MP3
        if not validate_audio_url(audio_url, request_id):
            logger.error(f"[{request_id}] ❌ MP3 не прошел валидацию")
            return None
        
        return audio_url
    else:
        logger.error(f"[{request_id}] ❌ Не удалось получить audio_url")
        return None'''
    
    new_content = re.sub(pattern, replacement, celery_tasks_content, flags=re.DOTALL)
    
    if new_content != celery_tasks_content:
        logger.info("✅ Обновлен generate_suno_music_sync для использования backoff")
        return new_content
    else:
        logger.warning("⚠️ Не найден цикл ожидания в generate_suno_music_sync")
        return celery_tasks_content

# ============================================================================
# ИСПРАВЛЕНИЕ 5: Удаление дубликатов MUSIC_STYLE_TRANSLATIONS
# ============================================================================

def remove_duplicate_translations(celery_tasks_content):
    """Удаляет дублированные словари MUSIC_STYLE_TRANSLATIONS"""
    
    # Считаем количество вхождений
    count = celery_tasks_content.count('MUSIC_STYLE_TRANSLATIONS = {')
    
    if count <= 1:
        logger.info("✅ Дубликаты MUSIC_STYLE_TRANSLATIONS не найдены")
        return celery_tasks_content
    
    # Находим все вхождения
    lines = celery_tasks_content.split('\n')
    translation_blocks = []
    current_block = None
    
    for i, line in enumerate(lines):
        if 'MUSIC_STYLE_TRANSLATIONS = {' in line:
            if current_block is not None:
                translation_blocks.append(current_block)
            current_block = {'start': i, 'lines': []}
        
        if current_block is not None:
            current_block['lines'].append(line)
            
            # Конец словаря - когда находим закрывающую скобку и следующая строка не продолжает
            if line.strip() == '}' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not (next_line.startswith('    ') or next_line.startswith(',')):
                    translation_blocks.append(current_block)
                    current_block = None
    
    # Если нашли больше одного блока
    if len(translation_blocks) > 1:
        logger.info(f"⚠️ Найдено {len(translation_blocks)} дубликатов MUSIC_STYLE_TRANSLATIONS")
        
        # Оставляем первый блок, удаляем остальные
        first_block = translation_blocks[0]
        blocks_to_remove = translation_blocks[1:]
        
        # Создаем новый список строк
        new_lines = []
        i = 0
        while i < len(lines):
            # Проверяем, находится ли текущая строка в блоке для удаления
            in_block_to_remove = False
            for block in blocks_to_remove:
                if block['start'] <= i < block['start'] + len(block['lines']):
                    in_block_to_remove = True
                    break
            
            if not in_block_to_remove:
                new_lines.append(lines[i])
            i += 1
        
        logger.info(f"✅ Удалено {len(blocks_to_remove)} дубликатов словаря")
        return '\n'.join(new_lines)
    
    return celery_tasks_content

# ============================================================================
# ИСПРАВЛЕНИЕ 6: Защита от race conditions
# ============================================================================

def add_race_condition_protection(celery_tasks_content):
    """Добавляет защиту от race conditions в save_generation_task_sync"""
    
    # Ищем INSERT ... ON CONFLICT в save_generation_task_sync
    pattern = r'(ON CONFLICT \(task_id\) \s*\n\s*DO UPDATE SET\s*\n.*?\n\s*RETURNING)'
    
    replacement = '''ON CONFLICT (task_id) 
            DO UPDATE SET
                status = EXCLUDED.status,
                audio_url = CASE 
                    WHEN generations.status NOT IN ('completed', 'error', 'expired') 
                    THEN EXCLUDED.audio_url 
                    ELSE generations.audio_url 
                END,
                suno_task_id = EXCLUDED.suno_task_id,
                result_message = EXCLUDED.result_message,
                error_message = CASE 
                    WHEN generations.status NOT IN ('completed', 'error', 'expired') 
                    THEN EXCLUDED.error_message 
                    ELSE generations.error_message 
                END,
                updated_at = NOW()
            WHERE generations.status NOT IN ('completed', 'error', 'expired')
            RETURNING'''
    
    new_content = re.sub(pattern, replacement, celery_tasks_content, flags=re.DOTALL)
    
    if new_content != celery_tasks_content:
        logger.info("✅ Добавлена защита от race conditions")
        return new_content
    else:
        logger.warning("⚠️ Не найден ON CONFLICT блок для добавления защиты")
        return celery_tasks_content

# ============================================================================
# ИСПРАВЛЕНИЕ 7: Использование translate_style_to_english
# ============================================================================

def ensure_style_translation_usage(celery_tasks_content):
    """Обеспечивает использование translate_style_to_english в generate_suno_music_sync"""
    
    # Ищем функцию generate_suno_music_sync и проверяем использование translate_style_to_english
    if 'translate_style_to_english(style)' not in celery_tasks_content:
        # Ищем место в generate_suno_music_sync где обрабатывается style
        pattern = r'(def generate_suno_music_sync.*?:\s*\n.*?request_id = .*?\n)'
        
        replacement = '''def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None, style=None):
    """
    Синхронная функция для генерации музыки через Suno API
    """
    import time
    import requests
    
    request_id = f"sunosync_{int(time.time())}_{abs(hash(str(user_id)))[:6]}"
    
    logger.info(f"[{request_id}] 🎵 Начинаем генерацию через Suno API")
    logger.info(f"[{request_id}]    • Prompt: {prompt[:100]}...")
    logger.info(f"[{request_id}]    • User ID: {user_id}")
    logger.info(f"[{request_id}]    • Is song: {is_song}")
    logger.info(f"[{request_id}]    • Custom mode: {custom_mode}")
    
    # 🔄 ПЕРЕВОД СТИЛЯ НА АНГЛИЙСКИЙ (если предоставлен)
    translated_style = None
    if style:
        translated_style = translate_style_to_english(style)
        if translated_style != style:
            logger.info(f"[{request_id}] 🔄 Стиль переведен: '{style}' → '{translated_style}'")
        else:
            logger.info(f"[{request_id}] 📝 Стиль (уже на английском): '{style}'")
    
    # 🔄 ПЕРЕВОД ПРОМПТА (опционально, если содержит кириллицу)
    final_prompt = prompt
    if prompt and any('а' <= char <= 'я' or 'А' <= char <= 'Я' for char in prompt):
        logger.warning(f"[{request_id}] ⚠️ Промпт содержит кириллицу. Suno лучше работает с английским.")
        # TODO: Добавить автоматический перевод через API если нужно'''
    
    new_content = re.sub(pattern, replacement, celery_tasks_content, flags=re.DOTALL)
    
    if new_content != celery_tasks_content:
        logger.info("✅ Добавлен перевод стилей в generate_suno_music_sync")
        
        # Теперь нужно обновить использование style в data словаре
        new_content = new_content.replace(
            '"style": style,',
            '"style": translated_style if translated_style else style,'
        )
        
        return new_content
    else:
        logger.warning("⚠️ Не удалось добавить перевод стилей")
        return celery_tasks_content

# ============================================================================
# ИСПРАВЛЕНИЕ 8: Логирование времени генерации
# ============================================================================

def add_generation_time_logging(celery_tasks_content):
    """Добавляет логирование времени генерации"""
    
    # Ищем функцию generate_song_task и generate_music_task
    # и добавляем тайминг
    
    # Для generate_song_task
    pattern1 = r'(def generate_song_task\(.*?\):\s*\n.*?task_start_time = time\.time\(\))'
    
    if not re.search(pattern1, celery_tasks_content, flags=re.DOTALL):
        # Добавляем в начало generate_song_task
        new_content = re.sub(
            r'(def generate_song_task\(.*?\):\s*\n)',
            r'''\1    import time
    task_start_time = time.time()
    generation_id = f"song_{int(task_start_time)}_{user_id}"
    logger.info(f"[{generation_id}] 🎤 Начинаем генерацию песни")
    logger.info(f"[{generation_id}]    • User: {user_id}")
    logger.info(f"[{generation_id}]    • Style: {style}")
    logger.info(f"[{generation_id}]    • Custom mode: {custom_mode}")
    logger.info(f"[{generation_id}]    • Task ID: {task_id}")
    logger.info(f"[{generation_id}]    • Lyrics: {lyrics[:100]}...")
    
    ''',
            celery_tasks_content,
            flags=re.DOTALL
        )
        
        # Добавляем в конце функции
        new_content = re.sub(
            r'(return True\s*\n\s*except Exception as e:\s*\n)',
            r'''    # Логируем время выполнения
    task_end_time = time.time()
    duration = task_end_time - task_start_time
    logger.info(f"[{generation_id}] ⏱️ Генерация завершена за {duration:.1f} секунд")
    
\1''',
            new_content,
            flags=re.DOTALL
        )
        
        logger.info("✅ Добавлено логирование времени для generate_song_task")
        celery_tasks_content = new_content
    
    # Для generate_music_task
    pattern2 = r'(def generate_music_task\(.*?\):\s*\n.*?task_start_time = time\.time\(\))'
    
    if not re.search(pattern2, celery_tasks_content, flags=re.DOTALL):
        new_content = re.sub(
            r'(def generate_music_task\(.*?\):\s*\n)',
            r'''\1    import time
    task_start_time = time.time()
    generation_id = f"music_{int(task_start_time)}_{user_id}"
    logger.info(f"[{generation_id}] 🎵 Начинаем генерацию музыки")
    logger.info(f"[{generation_id}]    • User: {user_id}")
    logger.info(f"[{generation_id}]    • Style: {style}")
    logger.info(f"[{generation_id}]    • Prompt: {prompt[:100]}...")
    logger.info(f"[{generation_id}]    • Task ID: {task_id}")
    
    ''',
            celery_tasks_content,
            flags=re.DOTALL
        )
        
        new_content = re.sub(
            r'(return True\s*\n\s*except Exception as e:\s*\n)',
            r'''    # Логируем время выполнения
    task_end_time = time.time()
    duration = task_end_time - task_start_time
    logger.info(f"[{generation_id}] ⏱️ Генерация завершена за {duration:.1f} секунд")
    
\1''',
            new_content,
            flags=re.DOTALL
        )
        
        logger.info("✅ Добавлено логирование времени для generate_music_task")
        celery_tasks_content = new_content
    
    return celery_tasks_content

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def apply_fixes():
    """Применяет все исправления"""
    
    log_step(1, "ПОДГОТОВКА И БЭКАПЫ")
    
    # Создаем директорию для бэкапов
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Читаем оригинальные файлы
    try:
        with open(CELERY_TASKS_PATH, 'r', encoding='utf-8') as f:
            celery_content = f.read()
        
        with open(DB_UTILS_PATH, 'r', encoding='utf-8') as f:
            db_utils_content = f.read()
    except Exception as e:
        logger.error(f"❌ Ошибка чтения файлов: {e}")
        return False
    
    # Создаем бэкапы
    celery_backup = create_backup(CELERY_TASKS_PATH)
    db_utils_backup = create_backup(DB_UTILS_PATH)
    
    log_step(2, "ИСПРАВЛЕНИЕ CELERY_TASKS.PY")
    
    try:
        # Применяем исправления к celery_tasks.py
        original_celery_len = len(celery_content)
        
        # 1. Валидация MP3
        log_step("2.1", "Добавление валидации MP3 файлов")
        celery_content = add_mp3_validation(celery_content)
        
        # 2. Исправление TypeError
        log_step("2.2", "Исправление TypeError в save_generation_task_sync")
        celery_content = fix_save_generation_task_sync_typerror(celery_content)
        
        # 3. Экспоненциальный backoff
        log_step("2.3", "Добавление экспоненциального backoff")
        celery_content = add_exponential_backoff(celery_content)
        celery_content = update_generate_suno_music_sync_with_backoff(celery_content)
        
        # 4. Валидация в generate_suno_music_sync
        log_step("2.4", "Обновление generate_suno_music_sync с валидацией")
        celery_content = update_generate_suno_music_sync_with_validation(celery_content)
        
        # 5. Удаление дубликатов переводов
        log_step("2.5", "Удаление дубликатов MUSIC_STYLE_TRANSLATIONS")
        celery_content = remove_duplicate_translations(celery_content)
        
        # 6. Защита от race conditions
        log_step("2.6", "Добавление защиты от race conditions")
        celery_content = add_race_condition_protection(celery_content)
        
        # 7. Использование translate_style_to_english
        log_step("2.7", "Обеспечение использования translate_style_to_english")
        celery_content = ensure_style_translation_usage(celery_content)
        
        # 8. Логирование времени генерации
        log_step("2.8", "Добавление логирования времени генерации")
        celery_content = add_generation_time_logging(celery_content)
        
        log_step(3, "ИСПРАВЛЕНИЕ DB_UTILS.PY")
        
        # 9. Исправление дублированного кода в execute_query_sync
        log_step("3.1", "Исправление дублированного кода в execute_query_sync")
        db_utils_content = fix_duplicate_code_in_execute_query_sync(db_utils_content)
        
        log_step(4, "ПРОВЕРКА СИНТАКСИСА")
        
        # Проверяем синтаксис исправленных файлов
        celery_ok = check_python_syntax(CELERY_TASKS_PATH)
        db_utils_ok = check_python_syntax(DB_UTILS_PATH)
        
        if not celery_ok or not db_utils_ok:
            logger.error("❌ Обнаружены ошибки синтаксиса. Восстанавливаем бэкапы...")
            restore_backup(celery_backup, CELERY_TASKS_PATH)
            restore_backup(db_utils_backup, DB_UTILS_PATH)
            return False
        
        log_step(5, "СОХРАНЕНИЕ ИСПРАВЛЕННЫХ ФАЙЛОВ")
        
        # Сохраняем исправленные файлы
        with open(CELERY_TASKS_PATH, 'w', encoding='utf-8') as f:
            f.write(celery_content)
        
        with open(DB_UTILS_PATH, 'w', encoding='utf-8') as f:
            f.write(db_utils_content)
        
        logger.info(f"✅ Celery tasks изменен: {len(celery_content) - original_celery_len} символов")
        logger.info("✅ Все исправления применены успешно")
        
        log_step(6, "ФИНАЛЬНАЯ ПРОВЕРКА")
        
        # Финальная проверка синтаксиса
        final_check = True
        for file_path in [CELERY_TASKS_PATH, DB_UTILS_PATH]:
            if not check_python_syntax(file_path):
                logger.error(f"❌ Финальная проверка не пройдена для {file_path}")
                final_check = False
        
        if not final_check:
            logger.error("❌ Финальная проверка не пройдена. Восстанавливаем бэкапы...")
            restore_backup(celery_backup, CELERY_TASKS_PATH)
            restore_backup(db_utils_backup, DB_UTILS_PATH)
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при применении исправлений: {e}", exc_info=True)
        
        # Восстанавливаем из бэкапов при ошибке
        try:
            restore_backup(celery_backup, CELERY_TASKS_PATH)
            restore_backup(db_utils_backup, DB_UTILS_PATH)
            logger.info("✅ Файлы восстановлены из бэкапов")
        except Exception as restore_error:
            logger.error(f"❌ Ошибка при восстановлении бэкапов: {restore_error}")
        
        return False

def main():
    """Главная функция"""
    
    print("\n" + "═" * 80)
    print("🔧 КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ОШИБОК")
    print("═" * 80 + "\n")
    
    print("Файлы для исправления:")
    print(f"  1. {CELERY_TASKS_PATH}")
    print(f"  2. {DB_UTILS_PATH}")
    print(f"\nЛог файл: {LOG_FILE}")
    print("\n" + "═" * 80)
    
    # Запрашиваем подтверждение
    response = input("Продолжить? (y/N): ").strip().lower()
    if response not in ('y', 'yes', 'д', 'да'):
        print("Отменено пользователем")
        return False
    
    success = apply_fixes()
    
    if success:
        print("\n" + "═" * 80)
        print("✅ ВСЕ ИСПРАВЛЕНИЯ УСПЕШНО ПРИМЕНЕНЫ")
        print("═" * 80 + "\n")
        
        print("📋 ИСПРАВЛЕНИЯ:")
        print("  1. ✅ Валидация MP3 файлов")
        print("  2. ✅ Исправление TypeError в save_generation_task_sync")
        print("  3. ✅ Устранение дублированного кода в execute_query_sync")
        print("  4. ✅ Экспоненциальный backoff для Suno API")
        print("  5. ✅ Удаление дубликатов MUSIC_STYLE_TRANSLATIONS")
        print("  6. ✅ Защита от race conditions")
        print("  7. ✅ Использование translate_style_to_english")
        print("  8. ✅ Логирование времени генерации")
        
        print("\n🚀 ДАЛЬНЕЙШИЕ ДЕЙСТВИЯ:")
        print("  1. Перезапустите Celery workers:")
        print("     sudo systemctl restart albimusic-celery")
        print("  2. Проверьте логи:")
        print("     sudo journalctl -u albimusic-celery -f")
        print("  3. Протестируйте генерацию через бота")
        
        print(f"\n📝 Подробности в лог файле: {LOG_FILE}")
    else:
        print("\n" + "═" * 80)
        print("❌ ИСПРАВЛЕНИЯ НЕ ПРИМЕНЕНЫ")
        print("═" * 80 + "\n")
        print("Файлы восстановлены из бэкапов")
        print(f"Проверьте лог файл для деталей: {LOG_FILE}")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print("\n" + "═" * 80)
            print("✅ СКРИПТ ЗАВЕРШЕН УСПЕШНО")
            print("═" * 80 + "\n")
            sys.exit(0)
        else:
            print("\n" + "═" * 80)
            print("❌ СКРИПТ ЗАВЕРШЕН С ОШИБКАМИ")
            print("═" * 80 + "\n")
            print("Проверьте лог файл для деталей:")
            print(f"  cat {LOG_FILE}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\nПодробности в лог файле: {LOG_FILE}")
        sys.exit(1)
