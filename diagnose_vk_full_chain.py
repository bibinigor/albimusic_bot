#!/usr/bin/env python3
"""
ПОЛНАЯ ДИАГНОСТИКА ЦЕПОЧКИ МИНУСОВКА/КАВЕР/WAV для VK
Проверяет КАЖДЫЙ этап от запроса до доставки результата
"""

import sys
import logging
sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync, init_db_pool_sync
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_issue(issue_num, description):
    print(f"\n❌ ПРОБЛЕМА #{issue_num}: {description}")

def print_ok(text):
    print(f"✅ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

# Инициализация БД
init_db_pool_sync()

print_header("ДИАГНОСТИКА ЦЕПОЧКИ VK: МИНУСОВКА/КАВЕР/WAV")

issues_found = []

# ============================================================
# ПРОВЕРКА 1: Функция send_vk_result в celery_tasks.py
# ============================================================
print_header("ПРОВЕРКА 1: Функция send_vk_result()")

try:
    with open('celery_tasks.py', 'r', encoding='utf-8') as f:
        celery_content = f.read()
    
    if 'def send_vk_result' in celery_content:
        print_ok("Функция send_vk_result() найдена")
        
        # Проверяем что она вызывается в минусовке
        if 'send_vk_result(user_id, message, url_to_send)' in celery_content:
            print_ok("send_vk_result() вызывается для отправки результатов")
        else:
            issues_found.append("send_vk_result() не вызывается для отправки результатов")
            print_issue(len(issues_found), issues_found[-1])
        
        # Проверяем обработку ошибок
        if 'except Exception as' in celery_content.split('def send_vk_result')[1].split('def ')[0]:
            print_ok("send_vk_result() имеет обработку ошибок")
        else:
            issues_found.append("send_vk_result() НЕ имеет обработки ошибок")
            print_issue(len(issues_found), issues_found[-1])
    else:
        issues_found.append("Функция send_vk_result() НЕ НАЙДЕНА в celery_tasks.py!")
        print_issue(len(issues_found), issues_found[-1])
        
except Exception as e:
    issues_found.append(f"Ошибка чтения celery_tasks.py: {e}")
    print_issue(len(issues_found), issues_found[-1])

# ============================================================
# ПРОВЕРКА 2: Задачи в celery_tasks.py
# ============================================================
print_header("ПРОВЕРКА 2: Celery задачи для минусовки/кавера/WAV")

tasks_to_check = [
    ('generate_karaoke_task', 'минусовки'),
    ('generate_cover_task', 'кавера'),
    ('generate_wav_task', 'WAV')
]

for task_name, description in tasks_to_check:
    if f'def {task_name}' in celery_content:
        print_ok(f"Задача {task_name} ({description}) существует")
        
        # Проверяем что задача сохраняет результат в БД
        task_code = celery_content.split(f'def {task_name}')[1].split('def ')[0]
        
        if 'save_generation_task_sync' in task_code or 'execute_query_sync' in task_code:
            print_ok(f"  └─ Сохраняет результат в БД")
        else:
            issues_found.append(f"{task_name} НЕ сохраняет результат в БД")
            print_issue(len(issues_found), issues_found[-1])
        
        # Проверяем отправку результата
        if 'send_vk_result' in task_code:
            print_ok(f"  └─ Отправляет результат через send_vk_result()")
        else:
            issues_found.append(f"{task_name} НЕ отправляет результат пользователю!")
            print_issue(len(issues_found), issues_found[-1])
    else:
        issues_found.append(f"Задача {task_name} ({description}) НЕ НАЙДЕНА!")
        print_issue(len(issues_found), issues_found[-1])

# ============================================================
# ПРОВЕРКА 3: Обработчики в main_vk.py
# ============================================================
print_header("ПРОВЕРКА 3: Обработчики кнопок в main_vk.py")

try:
    with open('main_vk.py', 'r', encoding='utf-8') as f:
        main_vk_content = f.read()
    
    handlers_to_check = [
        ('action == "karaoke_v1" or action == "karaoke_v2"', 'выбор версии минусовки'),
        ('action == "wav_v1" or action == "wav_v2"', 'выбор версии WAV'),
        ('action == "cover_v1" or action == "cover_v2"', 'выбор версии кавера'), 
        ('action == "cover_genre"', 'выбор жанра кавера'),
    ]
    
    for handler_check, description in handlers_to_check:
        if handler_check in main_vk_content:
            print_ok(f"Обработчик для {description} найден")
            
            # Проверяем что вызывается apply_async
            handler_code = main_vk_content.split(handler_check)[1].split('elif action ==')[0]
            
            if '.apply_async(' in handler_code:
                print_ok(f"  └─ Использует .apply_async() (асинхронно)")
            else:
                issues_found.append(f"Обработчик {description} НЕ использует .apply_async()!")
                print_issue(len(issues_found), issues_found[-1])
                
            # Проверяем что списывается баланс ДО запуска
            if 'UPDATE users SET balance = balance -' in handler_code:
                print_ok(f"  └─ Списывает баланс ДО запуска задачи")
            else:
                issues_found.append(f"Обработчик {description} НЕ списывает баланс перед запуском!")
                print_issue(len(issues_found), issues_found[-1])
        else:
            issues_found.append(f"Обработчик для {description} НЕ НАЙДЕН!")
            print_issue(len(issues_found), issues_found[-1])
            
except Exception as e:
    issues_found.append(f"Ошибка чтения main_vk.py: {e}")
    print_issue(len(issues_found), issues_found[-1])

# ============================================================
# ПРОВЕРКА 4: Записи в БД
# ============================================================
print_header("ПРОВЕРКА 4: Последние задачи минусовки/кавера/WAV в БД")

try:
    # Проверяем минусовки
    karaoke_tasks = execute_query_sync("""
        SELECT task_id, user_id, status, created_at 
        FROM generations 
        WHERE prompt ILIKE '%минусовка%' 
        ORDER BY created_at DESC 
        LIMIT 3
    """)
    
    if karaoke_tasks:
        print_ok(f"Найдено {len(karaoke_tasks)} задач минусовки:")
        for task_id, user_id, status, created_at in karaoke_tasks:
            print(f"  • {task_id[:8]}... - user {user_id} - статус: {status} - {created_at}")
            
            if status != 'completed':
                issues_found.append(f"Минусовка {task_id[:8]}... имеет статус '{status}' вместо 'completed'")
                print_issue(len(issues_found), issues_found[-1])
    else:
        print_info("Задач минусовки в БД не найдено (может быть норма если не тестировали)")
    
    # Проверяем каверы
    cover_tasks = execute_query_sync("""
        SELECT task_id, user_id, status, created_at 
        FROM generations 
        WHERE prompt ILIKE '%кавер%' 
        ORDER BY created_at DESC 
        LIMIT 3
    """)
    
    if cover_tasks:
        print_ok(f"Найдено {len(cover_tasks)} задач кавера:")
        for task_id, user_id, status, created_at in cover_tasks:
            print(f"  • {task_id[:8]}... - user {user_id} - статус: {status} - {created_at}")
            
            if status != 'completed':
                issues_found.append(f"Кавер {task_id[:8]}... имеет статус '{status}' вместо 'completed'")
                print_issue(len(issues_found), issues_found[-1])
    else:
        print_info("Задач кавера в БД не найдено (может быть норма если не тестировали)")
    
    # Проверяем WAV
    wav_tasks = execute_query_sync("""
        SELECT task_id, user_id, status, created_at 
        FROM generations 
        WHERE prompt ILIKE '%WAV%' 
        ORDER BY created_at DESC 
        LIMIT 3
    """)
    
    if wav_tasks:
        print_ok(f"Найдено {len(wav_tasks)} задач WAV:")
        for task_id, user_id, status, created_at in wav_tasks:
            print(f"  • {task_id[:8]}... - user {user_id} - статус: {status} - {created_at}")
            
            if status != 'completed':
                issues_found.append(f"WAV {task_id[:8]}... имеет статус '{status}' вместо 'completed'")
                print_issue(len(issues_found), issues_found[-1])
    else:
        print_info("Задач WAV в БД не найдено (может быть норма если не тестировали)")
        
except Exception as e:
    issues_found.append(f"Ошибка проверки БД: {e}")
    print_issue(len(issues_found), issues_found[-1])

# ============================================================
# ПРОВЕРКА 5: Ошибки в БД
# ============================================================
print_header("ПРОВЕРКА 5: Задачи со статусом ERROR")

try:
    error_tasks = execute_query_sync("""
        SELECT task_id, user_id, prompt, audio_url, created_at 
        FROM generations 
        WHERE status = 'error' 
        AND (prompt ILIKE '%минусовка%' OR prompt ILIKE '%кавер%' OR prompt ILIKE '%WAV%')
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    if error_tasks:
        issues_found.append(f"Найдено {len(error_tasks)} задач с ошибками!")
        print_issue(len(issues_found), issues_found[-1])
        
        for task_id, user_id, prompt, audio_url, created_at in error_tasks:
            print(f"  • {task_id[:8]}... - {prompt[:50]}...")
            print(f"    Ошибка: {audio_url[:100] if audio_url else 'нет описания'}")
            print(f"    Дата: {created_at}")
    else:
        print_ok("Ошибок в последних задачах не найдено")
        
except Exception as e:
    issues_found.append(f"Ошибка проверки ошибок в БД: {e}")
    print_issue(len(issues_found), issues_found[-1])

# ============================================================
# ПРОВЕРКА 6: VK Token и доступность API
# ============================================================
print_header("ПРОВЕРКА 6: VK API доступность")

try:
    from vk_config import VK_TOKEN, VK_GROUP_ID
    import vk_api
    
    print_ok("VK_TOKEN найден в конфиге")
    print_ok(f"VK_GROUP_ID: {VK_GROUP_ID}")
    
    # Попытка подключиться к VK API
    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
        
        # Проверяем группу
        group_info = vk.groups.getById(group_id=VK_GROUP_ID)
        if group_info:
            print_ok(f"VK API доступен, группа: {group_info[0].get('name', 'N/A')}")
    except Exception as vk_error:
        issues_found.append(f"VK API недоступен: {vk_error}")
        print_issue(len(issues_found), issues_found[-1])
        
except Exception as e:
    issues_found.append(f"Ошибка проверки VK config: {e}")
    print_issue(len(issues_found), issues_found[-1])

# ============================================================
# ПРОВЕРКА 7: Celery worker статус
# ============================================================
print_header("ПРОВЕРКА 7: Celery workers")

try:
    import subprocess
    result = subprocess.run(['celery', '-A', 'celery_tasks', 'inspect', 'active'], 
                          capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print_ok("Celery workers активны")
        if 'generate_karaoke_task' in result.stdout or 'generate_cover_task' in result.stdout:
            print_info("Есть активные задачи минусовки/кавера")
    else:
        issues_found.append(f"Celery workers не отвечают: {result.stderr}")
        print_issue(len(issues_found), issues_found[-1])
        
except Exception as e:
    print_info(f"Не удалось проверить Celery: {e}")

# ============================================================
# ИТОГОВЫЙ ОТЧЕТ
# ============================================================
print_header("ИТОГОВЫЙ ОТЧЕТ")

if issues_found:
    print(f"\n🔴 НАЙДЕНО {len(issues_found)} ПРОБЛЕМ:\n")
    for i, issue in enumerate(issues_found, 1):
        print(f"{i}. {issue}")
    
    print("\n" + "="*70)
    print("РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
    print("="*70)
    
    print("""
1. КРИТИЧНО: Проверить что send_vk_result() работает надежно
2. Добавить retry механизм в send_vk_result()
3. Убедиться что результаты сохраняются в БД перед отправкой
4. Проверить логи VK API на ошибки отправки
5. Создать отдельный монитор для VK (аналог run_monitor_notify.py)
6. Добавить подробное логирование в каждую задачу
    """)
else:
    print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Проблем не найдено.")
    print("\nЕсли минусовки/каверы/WAV все еще не работают:")
    print("1. Проверьте логи Celery: journalctl -u celery-worker -n 100")
    print("2. Проверьте логи VK бота: journalctl -u vk-bot -n 100")
    print("3. Запустите тестовый запрос и отследите его по логам")

print("\n" + "="*70)
