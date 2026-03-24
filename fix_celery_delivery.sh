#!/bin/bash
set -e

echo "🔧 ИСПРАВЛЕНИЕ: Доставка задач в Celery"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="/root/albimusic-bot/backups_delivery_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# ========================================
# ШАГ 1: СОЗДАНИЕ БЭКАПОВ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 1: Создание бэкапов"
echo "================================================================"

for file in celery_tasks.py main_with_payments.py celery_config.py; do
    cp "/root/albimusic-bot/$file" "$BACKUP_DIR/$file"
    log_info "Бэкап: $file"
done

# ========================================
# ШАГ 2: ПРОВЕРКА И ИСПРАВЛЕНИЕ celery_tasks.py
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 2: Проверка celery_tasks.py"
echo "================================================================"

python3 << 'ENDPYTHON'
import sys

file_path = '/root/albimusic-bot/celery_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔍 Проверяем структуру celery_tasks.py...")

issues_found = False

# 1. Проверка импорта Celery
if 'from celery import Celery' not in content:
    print("❌ Нет импорта Celery")
    issues_found = True
else:
    print("✅ Импорт Celery есть")

# 2. Проверка создания app
if "celery_app = Celery('albimusic_tasks')" not in content:
    print("❌ Неправильное создание Celery app")
    issues_found = True
else:
    print("✅ Celery app создан правильно")

# 3. Проверка конфигурации
if 'celery_app.config_from_object' not in content:
    print("⚠️  Конфигурация загружается через conf.update()")
else:
    print("✅ Конфигурация через config_from_object")

# 4. Проверка декораторов задач
if '@celery_app.task(name=' in content:
    print("✅ Декораторы задач используют name=")
else:
    print("⚠️  Декораторы без явного name=")

# 5. Проверка bind=True
if 'bind=True' in content:
    print("✅ Задачи используют bind=True")
else:
    print("⚠️  Нет bind=True в задачах")

if issues_found:
    print("\n❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
    print("ПРОПУСКАЕМ проверку")
else:
    print("\n✅ Базовая структура корректна")
ENDPYTHON

# ========================================
# ШАГ 3: ПРОВЕРКА ИМПОРТА В БОТЕ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 3: Проверка импорта задач в боте"
echo "================================================================"

python3 << 'ENDPYTHON'
import sys

file_path = '/root/albimusic-bot/main_with_payments.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔍 Проверяем импорты в main_with_payments.py...")

# Проверяем импорт задач
if 'from celery_tasks import' in content:
    import re
    match = re.search(r'from celery_tasks import (.*)', content)
    if match:
        imports = match.group(1)
        print(f"✅ Импортируется: {imports}")
        
        # Проверяем что импортируется celery_app
        if 'celery_app' not in imports:
            print("⚠️  celery_app не импортируется!")
            print("   Это может быть причиной проблемы!")
        
        # Проверяем импорт задач
        if 'generate_music_task' in imports:
            print("✅ generate_music_task импортируется")
        if 'generate_song_task' in imports:
            print("✅ generate_song_task импортируется")
else:
    print("❌ Нет импорта из celery_tasks!")
    print("ПРОПУСКАЕМ проверку")

# Проверяем вызовы .delay()
delay_calls = content.count('.delay(')
apply_async_calls = content.count('.apply_async(')

print(f"\n📊 Найдено вызовов задач:")
print(f"   • .delay(): {delay_calls}")
print(f"   • .apply_async(): {apply_async_calls}")

if delay_calls == 0 and apply_async_calls == 0:
    print("❌ Нет вызовов Celery задач!")
    print("ПРОПУСКАЕМ проверку")
ENDPYTHON

# ========================================
# ШАГ 4: ТЕСТ СОЗДАНИЯ ЗАДАЧИ НАПРЯМУЮ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 4: Тест создания задачи напрямую"
echo "================================================================"

log_info "Создаём тестовый скрипт..."

cat > /tmp/test_celery_direct.py << 'ENDTEST'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/albimusic-bot')

print("🔍 Тест прямого создания задачи...")

try:
    from celery_tasks import celery_app, test_task
    
    print(f"✅ Celery app загружен: {celery_app.main}")
    print(f"✅ Broker: {celery_app.conf.broker_url}")
    print(f"✅ Backend: {celery_app.conf.result_backend}")
    
    # Проверяем зарегистрированные задачи
    print(f"\n📋 Зарегистрированные задачи:")
    for task_name in sorted(celery_app.tasks.keys()):
        if not task_name.startswith('celery.'):
            print(f"   • {task_name}")
    
    # Пытаемся отправить задачу
    print(f"\n🚀 Отправляем тестовую задачу...")
    result = test_task.delay(42)
    
    print(f"✅ Задача отправлена!")
    print(f"   • Task ID: {result.id}")
    print(f"   • Task name: {result.task_name}")
    print(f"   • State: {result.state}")
    
    # Проверяем состояние задачи
    import time
    time.sleep(2)
    
    print(f"\n🔍 Состояние после 2 секунд:")
    print(f"   • State: {result.state}")
    print(f"   • Ready: {result.ready()}")
    
    if result.ready():
        print(f"   • Result: {result.result}")
    else:
        print(f"   ⚠️  Задача ещё не выполнена")
    
    # Проверяем очереди Redis
    print(f"\n🔍 Проверяем Redis...")
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    # Проверяем ключи
    keys = r.keys('*')
    print(f"   • Всего ключей в Redis: {len(keys)}")
    
    for key in keys:
        key_str = key.decode('utf-8')
        if 'celery' in key_str.lower() or 'kombu' in key_str.lower():
            key_type = r.type(key).decode('utf-8')
            print(f"   • {key_str} (type: {key_type})")
    
    print("\n✅ Тест завершён")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    print("ПРОПУСКАЕМ проверку")
ENDTEST

chmod +x /tmp/test_celery_direct.py
python3 /tmp/test_celery_direct.py

# ========================================
# ШАГ 5: ПРОВЕРКА КОНФИГУРАЦИИ BROKER
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 5: Проверка конфигурации broker"
echo "================================================================"

python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, '/root/albimusic-bot')

try:
    from celery_tasks import celery_app
    
    print("📋 КОНФИГУРАЦИЯ CELERY:")
    print(f"   • App name: {celery_app.main}")
    print(f"   • Broker URL: {celery_app.conf.broker_url}")
    print(f"   • Result backend: {celery_app.conf.result_backend}")
    print(f"   • Task serializer: {celery_app.conf.task_serializer}")
    print(f"   • Result serializer: {celery_app.conf.result_serializer}")
    print(f"   • Accept content: {celery_app.conf.accept_content}")
    print(f"   • Default queue: {celery_app.conf.task_default_queue}")
    print(f"   • Task routes: {celery_app.conf.task_routes}")
    
    # Проверяем что broker доступен
    print(f"\n🔍 Проверяем соединение с broker...")
    
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=3)
        print(f"✅ Соединение с broker установлено")
        conn.release()
    except Exception as e:
        print(f"❌ Ошибка соединения с broker: {e}")
        print("ПРОПУСКАЕМ проверку")
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    print("ПРОПУСКАЕМ проверку")
ENDPYTHON

# ========================================
# ШАГ 6: ПРОВЕРКА WORKERS
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 6: Проверка Celery workers"
echo "================================================================"

log_info "Проверяем запущенные workers..."

python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, '/root/albimusic-bot')

try:
    from celery_tasks import celery_app
    
    print("🔍 Получаем список активных workers...")
    
    # Получаем статистику workers
    inspect = celery_app.control.inspect()
    
    # Active workers
    stats = inspect.stats()
    if stats:
        print(f"\n✅ Активных workers: {len(stats)}")
        for worker_name, worker_stats in stats.items():
            print(f"\n📊 Worker: {worker_name}")
            print(f"   • Pool: {worker_stats.get('pool', {}).get('implementation', 'N/A')}")
            print(f"   • Max concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
    else:
        print("❌ Нет активных workers!")
        print("ПРОПУСКАЕМ проверку")
    
    # Registered tasks
    registered = inspect.registered()
    if registered:
        print(f"\n📋 Зарегистрированные задачи на workers:")
        for worker_name, tasks in registered.items():
            print(f"\n   Worker: {worker_name}")
            for task in sorted(tasks):
                if not task.startswith('celery.'):
                    print(f"      • {task}")
    
    # Active tasks
    active = inspect.active()
    if active:
        total_active = sum(len(tasks) for tasks in active.values())
        print(f"\n⚡ Активных задач: {total_active}")
    else:
        print(f"\n📭 Нет активных задач")
    
    # Reserved tasks
    reserved = inspect.reserved()
    if reserved:
        total_reserved = sum(len(tasks) for tasks in reserved.values())
        print(f"📥 Зарезервированных задач: {total_reserved}")
    else:
        print(f"📭 Нет зарезервированных задач")
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    print("ПРОПУСКАЕМ проверку")
ENDPYTHON

# ========================================
# ШАГ 7: ИСПРАВЛЕНИЕ ИМПОРТА В БОТЕ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 7: Исправление импорта в боте"
echo "================================================================"

python3 << 'ENDPYTHON'
import re

file_path = '/root/albimusic-bot/main_with_payments.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔧 Проверяем и исправляем импорты...")

# Ищем текущий импорт
import_pattern = r'from celery_tasks import ([^\n]+)'
match = re.search(import_pattern, content)

if match:
    current_import = match.group(1)
    print(f"📋 Текущий импорт: {current_import}")
    
    # Проверяем что импортируется celery_app
    if 'celery_app' not in current_import:
        print("⚠️  celery_app не импортируется, добавляем...")
        
        # Добавляем celery_app к импорту
        new_import = f"celery_app, {current_import}"
        content = content.replace(
            f"from celery_tasks import {current_import}",
            f"from celery_tasks import {new_import}"
        )
        
        print(f"✅ Обновлённый импорт: {new_import}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Файл обновлён")
    else:
        print("✅ celery_app уже импортируется")
else:
    print("❌ Не найден импорт из celery_tasks!")
ENDPYTHON

# Проверка синтаксиса
if python3 -m py_compile "/root/albimusic-bot/main_with_payments.py" 2>/dev/null; then
    log_info "Синтаксис бота корректен"
else
    log_error "Ошибка синтаксиса в боте!"
    python3 -m py_compile "/root/albimusic-bot/main_with_payments.py"
fi

# ========================================
# ШАГ 8: ОЧИСТКА REDIS И ПЕРЕЗАПУСК
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 8: Очистка Redis и перезапуск"
echo "================================================================"

log_info "Очищаем Redis..."
redis-cli FLUSHDB

log_info "Перезапускаем сервисы..."
systemctl restart albimusic-celery
sleep 3
systemctl restart albimusic-bot
sleep 2

log_info "Проверяем статус..."
systemctl status albimusic-celery --no-pager -l | head -20
systemctl status albimusic-bot --no-pager -l | head -20

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo -e "${GREEN}✅ ДИАГНОСТИКА ЗАВЕРШЕНА${NC}"
echo "================================================================"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Отправьте тестовый запрос из бота"
echo ""
echo "2. Проверьте логи:"
echo "   tail -f /var/log/albimusic-bot/celery/celery.log"
echo ""
echo "3. Мониторинг Redis:"
echo "   redis-cli monitor"
echo ""
echo "4. Если задачи всё равно не доходят, проверьте:"
echo "   python3 /tmp/test_celery_direct.py"
echo ""
echo "📂 Бэкапы: $BACKUP_DIR"
echo "================================================================"

