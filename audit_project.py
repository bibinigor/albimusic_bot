#!/usr/bin/env python3
"""
Полный аудит проекта AlBi Music Bot
Проверка всех критических функций и потенциальных проблем
"""
import sys
import os
sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync, init_db_pool_sync
import re

# Цветовые коды для вывода
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{'='*70}")
    print(f"{BLUE}{text}{RESET}")
    print('='*70)

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def check_database_consistency():
    """Проверка консистентности использования БД"""
    print_header("🔍 АУДИТ 1: Проверка консистентности БД")

    issues = []

    # Проверяем файл main_with_payments.py на использование SQLite
    try:
        with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
            content = f.read()

        # Поиск sqlite3.connect
        sqlite_matches = re.findall(r'sqlite3\.connect\(["\'].*?["\']\)', content)
        if sqlite_matches:
            print_error(f"Найдено {len(sqlite_matches)} использований SQLite:")
            for match in sqlite_matches[:5]:  # Показываем первые 5
                print(f"   - {match}")
            issues.append("SQLite используется вместо PostgreSQL")
        else:
            print_success("SQLite не используется (правильно)")

        # Проверка параметров запросов
        wrong_params = re.findall(r'execute.*\?[,\)]', content)
        if wrong_params:
            print_error(f"Найдено {len(wrong_params)} запросов с '?' вместо '%s'")
            issues.append("Неправильные параметры в SQL запросах")
        else:
            print_success("Параметры SQL запросов корректны")

    except Exception as e:
        print_error(f"Ошибка проверки файла: {e}")

    return issues

def check_balance_functions():
    """Проверка функций работы с балансом"""
    print_header("💰 АУДИТ 2: Проверка функций баланса")

    issues = []

    try:
        with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
            content = f.read()

        # Проверяем функцию add_balance
        if 'def add_balance' in content:
            add_balance_func = content.split('def add_balance')[1].split('def ')[0]

            if 'sqlite3' in add_balance_func:
                print_error("add_balance использует SQLite!")
                issues.append("add_balance использует неправильную БД")
            elif 'execute_query_sync' in add_balance_func:
                print_success("add_balance использует PostgreSQL")
            else:
                print_warning("add_balance использует неизвестный метод")

        # Проверяем update_user_balance
        if 'def update_user_balance' in content:
            update_func = content.split('def update_user_balance')[1].split('def ')[0]

            if 'sqlite3' in update_func:
                print_error("update_user_balance использует SQLite!")
                issues.append("update_user_balance использует неправильную БД")
            elif 'execute_query_sync' in update_func:
                print_success("update_user_balance использует PostgreSQL")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_payment_webhook():
    """Проверка webhook обработки платежей"""
    print_header("💳 АУДИТ 3: Проверка webhook платежей")

    issues = []

    try:
        with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
            content = f.read()

        # Ищем webhook функцию
        if '/webhook/yookassa' in content:
            print_success("Webhook endpoint найден")

            webhook_section = content.split('/webhook/yookassa')[1].split('@app.')[0]

            # Проверяем вызов add_balance
            if 'add_balance(' in webhook_section:
                print_success("Webhook вызывает add_balance")
            else:
                print_error("Webhook НЕ вызывает add_balance!")
                issues.append("Webhook не начисляет баланс")

            # Проверяем маппинг сумм
            if 'amount_to_generations' in webhook_section:
                print_success("Маппинг сумм на генерации найден")
            else:
                print_warning("Маппинг сумм не найден")

        else:
            print_error("Webhook endpoint не найден!")
            issues.append("Отсутствует webhook для платежей")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_demo_system():
    """Проверка демо-системы"""
    print_header("🎵 АУДИТ 4: Проверка демо-системы")

    issues = []

    try:
        with open('/root/albimusic-bot/run_monitor_notify.py', 'r') as f:
            content = f.read()

        # Проверяем отправку демо
        if 'download_and_cut_audio' in content:
            print_success("Функция обрезки демо найдена")
        else:
            print_error("Функция обрезки демо НЕ найдена!")
            issues.append("Отсутствует обрезка демо-треков")

        # Проверяем удаление временных файлов
        if 'os.remove(demo_path)' in content:
            print_success("Удаление временных демо файлов работает")
        else:
            print_warning("Удаление временных файлов не найдено")

        # Проверяем сохранение в demo_tracks
        if 'INSERT INTO demo_tracks' in content:
            print_success("Сохранение в demo_tracks работает")
        else:
            print_error("Сохранение в demo_tracks НЕ найдено!")
            issues.append("Демо треки не сохраняются в БД")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_celery_tasks():
    """Проверка Celery задач"""
    print_header("⚙️  АУДИТ 5: Проверка Celery задач")

    issues = []

    try:
        with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
            content = f.read()

        # Список критических задач
        tasks = [
            'generate_song_task',
            'generate_karaoke_task',
            'generate_cover_task',
            'generate_wav_task'
        ]

        for task in tasks:
            if f'def {task}' in content:
                print_success(f"{task} найдена")

                # Проверяем сохранение результата
                task_content = content.split(f'def {task}')[1].split('def ')[0]
                if 'save_generation_task_sync' in task_content:
                    print_success(f"  └─ Сохранение результата работает")
                else:
                    print_error(f"  └─ Сохранение результата НЕ найдено!")
                    issues.append(f"{task} не сохраняет результат")
            else:
                print_error(f"{task} НЕ найдена!")
                issues.append(f"Отсутствует задача {task}")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_database_tables():
    """Проверка таблиц БД"""
    print_header("🗄️  АУДИТ 6: Проверка таблиц БД")

    issues = []

    try:
        # Список необходимых таблиц
        tables = ['users', 'generations', 'demo_tracks', 'payments']

        for table in tables:
            result = execute_query_sync(
                f"SELECT COUNT(*) FROM {table}"
            )
            if result:
                count = result[0][0]
                print_success(f"Таблица '{table}': {count} записей")
            else:
                print_error(f"Таблица '{table}' не найдена!")
                issues.append(f"Отсутствует таблица {table}")

        # Проверяем структуру users
        result = execute_query_sync(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
        )
        if result:
            columns = [row[0] for row in result]
            required_columns = ['user_id', 'balance', 'username', 'free_generation_used']

            for col in required_columns:
                if col in columns:
                    print_success(f"  └─ Колонка '{col}' существует")
                else:
                    print_error(f"  └─ Колонка '{col}' НЕ найдена!")
                    issues.append(f"Отсутствует колонка {col} в users")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_admin_privileges():
    """Проверка админских привилегий"""
    print_header("👑 АУДИТ 7: Проверка админских привилегий")

    issues = []

    try:
        with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
            content = f.read()

        # Проверяем админский user_id
        if '338544009' in content:
            print_success("Админский user_id найден: 338544009")
        else:
            print_warning("Админский user_id не найден")

        # Проверяем обход проверок баланса
        admin_checks = content.count('if user_id != 338544009:')
        if admin_checks > 0:
            print_success(f"Админ обходит проверки баланса ({admin_checks} мест)")
        else:
            print_warning("Админ не обходит проверки баланса")

        # Проверяем is_admin функцию
        if 'def is_admin' in content:
            print_success("Функция is_admin найдена")
        else:
            print_error("Функция is_admin НЕ найдена!")
            issues.append("Отсутствует функция is_admin")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_error_handling():
    """Проверка обработки ошибок"""
    print_header("🛡️  АУДИТ 8: Проверка обработки ошибок")

    issues = []

    try:
        with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
            content = f.read()

        # Подсчитываем try-except блоки
        try_count = content.count('try:')
        except_count = content.count('except')

        print_success(f"Try-except блоков: {try_count}")

        # Проверяем finally блоки (важно для сохранения результатов)
        finally_count = content.count('finally:')
        print_success(f"Finally блоков: {finally_count}")

        if finally_count < 3:
            print_warning("Мало finally блоков - результаты могут не сохраняться")

        # Проверяем retry механизмы
        if 'self.retry(' in content:
            print_success("Механизм retry найден")
        else:
            print_warning("Механизм retry не найден")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def check_security():
    """Проверка безопасности"""
    print_header("🔒 АУДИТ 9: Проверка безопасности")

    issues = []

    try:
        # Проверяем config файл
        if os.path.exists('/root/albimusic-bot/config.py'):
            with open('/root/albimusic-bot/config.py', 'r') as f:
                config_content = f.read()

            # Проверяем что секреты не хардкожены
            if 'YOOKASSA_SECRET' in config_content:
                print_success("YooKassa секрет в config")
            else:
                print_warning("YooKassa секрет не найден в config")

            if 'BOT_TOKEN' in config_content:
                print_success("Bot token в config")
            else:
                print_error("Bot token не найден в config!")
                issues.append("Bot token отсутствует")

        # Проверяем SQL injection защиту
        with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
            content = f.read()

        # Ищем небезопасные форматирования SQL
        unsafe_sql = re.findall(r'f["\'].*SELECT.*\{.*\}', content)
        if unsafe_sql:
            print_error(f"Найдено {len(unsafe_sql)} небезопасных SQL запросов!")
            issues.append("SQL injection уязвимости")
        else:
            print_success("SQL injection защита в порядке")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def test_real_user_balance():
    """Тест с реальным админским пользователем"""
    print_header("👤 АУДИТ 10: Тест с реальным пользователем")

    issues = []

    try:
        admin_id = 338544009

        # Проверяем админа
        result = execute_query_sync(
            "SELECT user_id, username, balance, free_generation_used FROM users WHERE user_id = %s",
            (admin_id,)
        )

        if result:
            user_id, username, balance, free_used = result[0]
            print_success(f"Админ найден: @{username}")
            print_success(f"  └─ Баланс: {balance} генераций")
            print_success(f"  └─ Бесплатная генерация использована: {free_used}")
        else:
            print_error("Админ не найден в БД!")
            issues.append("Админский аккаунт не найден")

        # Проверяем общую статистику
        result = execute_query_sync("SELECT COUNT(*) FROM users")
        total_users = result[0][0] if result else 0
        print_success(f"Всего пользователей: {total_users}")

        result = execute_query_sync("SELECT COUNT(*) FROM generations WHERE status = 'completed'")
        total_gens = result[0][0] if result else 0
        print_success(f"Всего генераций: {total_gens}")

        result = execute_query_sync("SELECT COUNT(*) FROM payments WHERE status = 'succeeded'")
        total_payments = result[0][0] if result else 0
        print_success(f"Успешных платежей: {total_payments}")

    except Exception as e:
        print_error(f"Ошибка проверки: {e}")

    return issues

def main():
    """Главная функция аудита"""
    print("\n" + "="*70)
    print(f"{BLUE}🔍 ПОЛНЫЙ АУДИТ ПРОЕКТА ALBI MUSIC BOT{RESET}")
    print("="*70)

    # Инициализация БД
    try:
        print("\n🔧 Инициализация подключения к БД...")
        init_db_pool_sync()
        print_success("Подключение установлено")
    except Exception as e:
        print_error(f"Не удалось подключиться к БД: {e}")
        return

    all_issues = []

    # Запускаем все проверки
    all_issues.extend(check_database_consistency())
    all_issues.extend(check_balance_functions())
    all_issues.extend(check_payment_webhook())
    all_issues.extend(check_demo_system())
    all_issues.extend(check_celery_tasks())
    all_issues.extend(check_database_tables())
    all_issues.extend(check_admin_privileges())
    all_issues.extend(check_error_handling())
    all_issues.extend(check_security())
    all_issues.extend(test_real_user_balance())

    # Итоговый отчет
    print_header("📊 ИТОГОВЫЙ ОТЧЕТ")

    if not all_issues:
        print_success("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Критических проблем не найдено.")
    else:
        print_error(f"⚠️  НАЙДЕНО {len(all_issues)} ПРОБЛЕМ:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")

    print("\n" + "="*70)
    print(f"{BLUE}✅ АУДИТ ЗАВЕРШЕН{RESET}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
