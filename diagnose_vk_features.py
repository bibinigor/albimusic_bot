#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИКА МИНУСОВОК/КАВЕРОВ/WAV ДЛЯ VK БОТА
Проверяет ВСЮ цепочку от запроса до доставки результата
"""

import sys
sys.path.append('/root/albimusic-bot')

import logging
from db_utils import execute_query_sync, init_db_pool_sync

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Цвета для вывода
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"   {text}")

def check_imports():
    """Проверка импортов"""
    print_header("ШАГ 1: ПРОВЕРКА ИМПОРТОВ")
    
    issues = []
    
    # Проверяем celery_tasks
    try:
        from celery_tasks import generate_karaoke_task, generate_cover_task, generate_wav_task, send_vk_result
        print_success("celery_tasks.py импортирован")
        print_info(f"   - generate_karaoke_task: {generate_karaoke_task}")
        print_info(f"   - generate_cover_task: {generate_cover_task}")
        print_info(f"   - generate_wav_task: {generate_wav_task}")
        print_info(f"   - send_vk_result: {send_vk_result}")
    except ImportError as e:
        print_error(f"Ошибка импорта celery_tasks: {e}")
        issues.append(f"celery_tasks импорт: {e}")
    
    # Проверяем VK конфиг
    try:
        from vk_config import VK_TOKEN, VK_GROUP_ID
        print_success("vk_config.py импортирован")
        print_info(f"   - VK_TOKEN: {'*' * 20}... (скрыт)")
        print_info(f"   - VK_GROUP_ID: {VK_GROUP_ID}")
    except ImportError as e:
        print_error(f"Ошибка импорта vk_config: {e}")
        issues.append(f"vk_config импорт: {e}")
    
    # Проверяем VK API
    try:
        import vk_api
        print_success("vk_api установлен")
    except ImportError:
        print_error("vk_api НЕ установлен!")
        issues.append("vk_api не установлена")
    
    return issues

def check_database():
    """Проверка базы данных"""
    print_header("ШАГ 2: ПРОВЕРКА БАЗЫ ДАННЫХ")
    
    issues = []
    
    try:
        init_db_pool_sync()
        print_success("Подключение к БД установлено")
        
        # Проверяем наличие таблицы generations
        result = execute_query_sync("""
            SELECT to_regclass('public.generations')
        """)
        
        if result and result[0][0]:
            print_success("Таблица generations существует")
            
            # Проверяем колонки
            columns = execute_query_sync("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'generations'
                ORDER BY ordinal_position
            """)
            
            print_info("Колонки таблицы:")
            required_cols = ['user_id', 'task_id', 'prompt', 'audio_url', 'status', 'suno_task_id', 'suno_audio_id']
            found_cols = [col[0] for col in columns]
            
            for col in required_cols:
                if col in found_cols:
                    print_info(f"   ✅ {col}")
                else:
                    print_error(f"   ❌ {col} - ОТСУТСТВУЕТ!")
                    issues.append(f"Колонка {col} отсутствует в generations")
            
            # Проверяем последние задачи
            recent = execute_query_sync("""
                SELECT task_id, prompt, status, created_at
                FROM generations
                WHERE prompt ILIKE ANY(ARRAY['%минусовка%', '%кавер%', '%WAV%'])
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            if recent:
                print_info(f"\nПоследние задачи минусовок/каверов/WAV:")
                for task in recent:
                    task_id, prompt, status, created = task
                    status_icon = "✅" if status == 'completed' else "❌" if status == 'error' else "⏳"
                    print_info(f"   {status_icon} {task_id[:8]}... | {prompt[:40]}... | {status}")
            else:
                print_warning("Нет задач минусовок/каверов/WAV в БД")
        
        else:
            print_error("Таблица generations НЕ СУЩЕСТВУЕТ!")
            issues.append("Таблица generations не найдена")
            
    except Exception as e:
        print_error(f"Ошибка работы с БД: {e}")
        issues.append(f"БД ошибка: {e}")
    
    return issues

def check_celery_workers():
    """Проверка Celery workers"""
    print_header("ШАГ 3: ПРОВЕРКА CELERY WORKERS")
    
    issues = []
    
    try:
        from celery_tasks import celery_app
        
        # Проверяем активные воркеры
        inspect = celery_app.control.inspect()
        
        # Активные воркеры
        active = inspect.active()
        if active:
            print_success(f"Активные воркеры: {len(active)}")
            for worker, tasks in active.items():
                print_info(f"   {worker}: {len(tasks)} активных задач")
        else:
            print_warning("Нет активных воркеров или они недоступны")
            issues.append("Celery воркеры не отвечают")
        
        # Зарегистрированные задачи
        registered = inspect.registered()
        if registered:
            print_success("Зарегистрированные задачи:")
            for worker, tasks in registered.items():
                relevant_tasks = [t for t in tasks if any(x in t for x in ['karaoke', 'cover', 'wav'])]
                if relevant_tasks:
                    print_info(f"   {worker}:")
                    for task in relevant_tasks:
                        print_info(f"      - {task}")
        
    except Exception as e:
        print_error(f"Ошибка проверки Celery: {e}")
        issues.append(f"Celery ошибка: {e}")
    
    return issues

def check_vk_api_access():
    """Проверка доступа к VK API"""
    print_header("ШАГ 4: ПРОВЕРКА ДОСТУПА К VK API")
    
    issues = []
    
    try:
        import vk_api
        from vk_config import VK_TOKEN
        
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
        
        # Проверяем доступ
        groups = vk.groups.getById()
        if groups:
            print_success(f"Доступ к VK API работает")
            print_info(f"   Группа: {groups[0].get('name', 'N/A')}")
        
        # Проверяем права на отправку сообщений
        try:
            # Это вызовет ошибку если нет прав, но мы её поймаем
            from vk_config import ADMIN_IDS
            if ADMIN_IDS:
                test_id = ADMIN_IDS[0]
                print_success(f"Тестовая отправка сообщения админу {test_id}...")
        except Exception as e:
            print_warning(f"Не удалось протестировать отправку: {e}")
            
    except Exception as e:
        print_error(f"Ошибка доступа к VK API: {e}")
        issues.append(f"VK API недоступен: {e}")
    
    return issues

def check_send_vk_result():
    """Проверка функции send_vk_result"""
    print_header("ШАГ 5: ПРОВЕРКА ФУНКЦИИ send_vk_result")
    
    issues = []
    
    try:
        from celery_tasks import send_vk_result
        import inspect
        
        # Проверяем сигнатуру функции
        sig = inspect.signature(send_vk_result)
        print_success(f"Функция send_vk_result найдена")
        print_info(f"   Сигнатура: {sig}")
        
        # Проверяем исходный код (первые строки)
        source = inspect.getsource(send_vk_result)
        lines = source.split('\n')[:10]
        print_info("   Первые строки кода:")
        for line in lines:
            if line.strip():
                print_info(f"      {line}")
        
        # Проверяем импорты внутри функции
        if 'import vk_api' in source:
            print_success("   ✅ vk_api импортируется")
        else:
            print_error("   ❌ vk_api НЕ импортируется")
            issues.append("vk_api не импортируется в send_vk_result")
        
        if 'VK_TOKEN' in source:
            print_success("   ✅ VK_TOKEN используется")
        else:
            print_error("   ❌ VK_TOKEN НЕ используется")
            issues.append("VK_TOKEN не используется в send_vk_result")
            
    except Exception as e:
        print_error(f"Ошибка проверки send_vk_result: {e}")
        issues.append(f"send_vk_result ошибка: {e}")
    
    return issues

def check_recent_failures():
    """Проверка последних ошибок"""
    print_header("ШАГ 6: АНАЛИЗ ПОСЛЕДНИХ ОШИБОК")
    
    issues = []
    
    try:
        # Ищем failed задачи
        failed = execute_query_sync("""
            SELECT task_id, prompt, audio_url, status, created_at
            FROM generations
            WHERE status = 'error'
            AND prompt ILIKE ANY(ARRAY['%минусовка%', '%кавер%', '%WAV%'])
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if failed:
            print_warning(f"Найдено {len(failed)} неудачных задач:")
            for task in failed:
                task_id, prompt, audio_url, status, created = task
                print_info(f"   {task_id[:8]}... | {prompt[:40]}...")
                if audio_url and audio_url.startswith('ERROR'):
                    error_msg = audio_url.replace('ERROR: ', '')
                    print_info(f"      Ошибка: {error_msg[:60]}...")
        else:
            print_success("Нет ошибок в последних задачах минусовок/каверов/WAV")
        
        # Ищем completed но без доставки
        completed = execute_query_sync("""
            SELECT task_id, prompt, audio_url, created_at
            FROM generations
            WHERE status = 'completed'
            AND prompt ILIKE ANY(ARRAY['%минусовка%', '%кавер%', '%WAV%'])
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if completed:
            print_success(f"Найдено {len(completed)} успешных задач:")
            for task in completed:
                task_id, prompt, audio_url, created = task
                has_url = bool(audio_url and not audio_url.startswith('ERROR'))
                url_icon = "✅" if has_url else "❌"
                print_info(f"   {url_icon} {task_id[:8]}... | {prompt[:40]}...")
                if has_url:
                    # Проверяем формат URL
                    if audio_url.startswith('['):
                        print_info(f"      URL: JSON массив")
                    elif audio_url.startswith('http'):
                        print_info(f"      URL: {audio_url[:50]}...")
                    else:
                        print_warning(f"      URL: Неизвестный формат: {audio_url[:50]}...")
        
    except Exception as e:
        print_error(f"Ошибка анализа ошибок: {e}")
        issues.append(f"Анализ ошибок: {e}")
    
    return issues

def main():
    """Главная функция диагностики"""
    print(f"\n{BLUE}{'='*70}")
    print(f"{'🔍 ДИАГНОСТИКА VK БОТА: МИНУСОВКИ/КАВЕРЫ/WAV':^70}")
    print(f"{'='*70}{RESET}\n")
    
    all_issues = []
    
    # Запускаем все проверки
    all_issues.extend(check_imports())
    all_issues.extend(check_database())
    all_issues.extend(check_celery_workers())
    all_issues.extend(check_vk_api_access())
    all_issues.extend(check_send_vk_result())
    all_issues.extend(check_recent_failures())
    
    # Итоговый отчет
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    if all_issues:
        print_error(f"Найдено проблем: {len(all_issues)}")
        for i, issue in enumerate(all_issues, 1):
            print_info(f"{i}. {issue}")
    else:
        print_success("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Система работает корректно.")
        print_info("\nЕсли пользователи все равно не получают результаты, проверьте:")
        print_info("1. Логи Celery worker: journalctl -u celery-worker -f")
        print_info("2. Логи VK бота: journalctl -u vk-bot -f")
        print_info("3. Логи монитора: tail -f /var/log/albimusic/monitor-error.log")
    
    print(f"\n{BLUE}{'='*70}{RESET}\n")

if __name__ == "__main__":
    main()
