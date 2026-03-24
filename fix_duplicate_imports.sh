#!/bin/bash
set -e

echo "🔧 ИСПРАВЛЕНИЕ: Удаление повторных импортов celery_tasks"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="/root/albimusic-bot/backups_imports_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# ========================================
# БЭКАП
# ========================================
cp /root/albimusic-bot/main_with_payments.py "$BACKUP_DIR/"
log_info "Бэкап создан: $BACKUP_DIR"

# ========================================
# ШАГ 1: АНАЛИЗ ИМПОРТОВ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 1: Анализ текущих импортов"
echo "================================================================"

python3 << 'ENDPYTHON'
file_path = '/root/albimusic-bot/main_with_payments.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("🔍 Поиск всех импортов celery_tasks...")

imports = []
for i, line in enumerate(lines, 1):
    if 'from celery_tasks import' in line or 'import celery_tasks' in line:
        imports.append((i, line.strip()))

print(f"\n📋 Найдено {len(imports)} импортов:\n")

for line_num, line_text in imports:
    print(f"   Строка {line_num}: {line_text}")

if len(imports) > 1:
    print(f"\n❌ ПРОБЛЕМА: Найдено {len(imports)} импортов вместо 1!")
    print(f"   Повторные импорты могут создавать разные экземпляры celery_app")
else:
    print(f"\n✅ Всё в порядке: только 1 импорт")
ENDPYTHON

# ========================================
# ШАГ 2: УДАЛЕНИЕ ПОВТОРНЫХ ИМПОРТОВ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 2: Удаление повторных импортов"
echo "================================================================"

python3 << 'ENDPYTHON'
import re

file_path = '/root/albimusic-bot/main_with_payments.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔧 Удаляем повторные импорты внутри функций...")

# Ищем импорты внутри функций (с отступами)
# Паттерн: от 4 пробелов + from celery_tasks import
pattern = r'^\s{4,}from celery_tasks import.*$'

matches = re.findall(pattern, content, re.MULTILINE)

if matches:
    print(f"\n❌ Найдено {len(matches)} повторных импортов:")
    for match in matches:
        print(f"   • {match.strip()}")
    
    # Удаляем все повторные импорты
    content = re.sub(pattern, '# [УДАЛЕНО] Повторный импорт (используется глобальный)', content, flags=re.MULTILINE)
    
    print(f"\n✅ Повторные импорты закомментированы")
else:
    print(f"\n✅ Повторных импортов не найдено")

# Проверяем что глобальный импорт на месте
if 'from celery_tasks import celery_app, generate_music_task, generate_song_task' in content:
    print(f"✅ Глобальный импорт на месте")
elif 'from celery_tasks import' in content:
    print(f"⚠️  Глобальный импорт есть, но может быть неполным")
    print(f"   Проверьте что импортируются: celery_app, generate_music_task, generate_song_task")
else:
    print(f"❌ НЕТ ГЛОБАЛЬНОГО ИМПОРТА!")
    
    # Добавляем глобальный импорт в начало файла
    # Ищем первые импорты
    import_pos = content.find('import ')
    if import_pos > 0:
        # Вставляем после первого блока импортов
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                continue
            else:
                # Нашли конец блока импортов
                lines.insert(i, 'from celery_tasks import celery_app, generate_music_task, generate_song_task')
                print(f"✅ Добавлен глобальный импорт")
                break
        
        content = '\n'.join(lines)

# Сохраняем
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Файл обновлён")
ENDPYTHON

# Проверка синтаксиса
if python3 -m py_compile /root/albimusic-bot/main_with_payments.py 2>/dev/null; then
    log_info "Синтаксис Python корректен"
else
    log_error "Ошибка синтаксиса!"
    python3 -m py_compile /root/albimusic-bot/main_with_payments.py
    cp "$BACKUP_DIR/main_with_payments.py" /root/albimusic-bot/main_with_payments.py
    exit 1
fi

# ========================================
# ШАГ 3: ПРОВЕРКА ПРАВИЛЬНОСТИ ИМПОРТА
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 3: Проверка что бот использует правильный celery_app"
echo "================================================================"

cat > /tmp/test_bot_celery_app.py << 'ENDTEST'
#!/usr/bin/env python3
import sys

# Имитируем окружение бота
sys.path.insert(0, '/root/albimusic-bot')

print("🔍 ПРОВЕРКА: Бот использует правильный celery_app")
print("="*80)

# Первый импорт (как в боте глобально)
print("\n1️⃣ Первый импорт (глобальный):")
from celery_tasks import celery_app as app1, generate_music_task as task1

print(f"   • celery_app id: {id(app1)}")
print(f"   • celery_app.main: {app1.main}")
print(f"   • generate_music_task id: {id(task1)}")
print(f"   • task1.app id: {id(task1.app)}")

# Проверяем что task1.app это тот же app1
if id(app1) == id(task1.app):
    print(f"   ✅ generate_music_task использует ПРАВИЛЬНЫЙ celery_app")
else:
    print(f"   ❌ generate_music_task использует ДРУГОЙ celery_app!")
    print(f"      app1 id: {id(app1)}")
    print(f"      task1.app id: {id(task1.app)}")

# Второй импорт (как было в функциях бота)
print("\n2️⃣ Повторный импорт (внутри функции):")
from celery_tasks import generate_music_task as task2

print(f"   • generate_music_task id: {id(task2)}")
print(f"   • task2.app id: {id(task2.app)}")

# Сравниваем
if id(task1) == id(task2):
    print(f"   ✅ Повторный импорт вернул ТУ ЖЕ задачу")
else:
    print(f"   ⚠️  Повторный импорт вернул ДРУГУЮ задачу")
    print(f"      task1 id: {id(task1)}")
    print(f"      task2 id: {id(task2)}")

if id(task1.app) == id(task2.app):
    print(f"   ✅ Обе задачи используют ОДИН celery_app")
else:
    print(f"   ❌ Задачи используют РАЗНЫЕ celery_app!")

# Проверяем конфигурацию
print("\n3️⃣ Конфигурация celery_app:")
print(f"   • Broker: {app1.conf.broker_url}")
print(f"   • Backend: {app1.conf.result_backend}")
print(f"   • Always eager: {app1.conf.task_always_eager}")

if app1.conf.task_always_eager:
    print(f"   ❌ ПРОБЛЕМА: task_always_eager = True!")
    print(f"      Задачи будут выполняться локально, не через Redis")
else:
    print(f"   ✅ task_always_eager = False (правильно)")

# Тест отправки задачи
print("\n4️⃣ Тест отправки задачи:")

try:
    result = task1.apply_async(
        args=[338544009, 'Тест после исправления импортов'],
        kwargs={'task_id': 'test_fixed_imports_001'}
    )
    
    print(f"   ✅ Задача создана:")
    print(f"      • Task ID: {result.id}")
    print(f"      • State: {result.state}")
    
    # Проверяем Redis
    import redis
    import time
    
    time.sleep(1)  # Даём время на публикацию
    
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    
    # Ищем задачу в очереди
    queue_len = r.llen('celery')
    print(f"\n   📊 Очередь 'celery':")
    print(f"      • Длина: {queue_len}")
    
    if queue_len > 0:
        print(f"      ✅ ЗАДАЧИ ЕСТЬ В ОЧЕРЕДИ!")
        
        # Показываем первую задачу
        first_task = r.lrange('celery', 0, 0)
        if first_task:
            import json
            task_data = json.loads(first_task[0])
            print(f"      • Task ID в очереди: {task_data.get('headers', {}).get('id', 'N/A')}")
    else:
        print(f"      ❌ ОЧЕРЕДЬ ПУСТА!")
        print(f"         Задача НЕ была отправлена в Redis")
    
    # ВЕРДИКТ
    print(f"\n{'='*80}")
    if queue_len > 0:
        print(f"✅ УСПЕХ! Задачи попадают в Redis после исправления импортов!")
    else:
        print(f"❌ ПРОВАЛ! Проблема всё ещё есть")
    print(f"{'='*80}")
    
except Exception as e:
    print(f"\n❌ ОШИБКА при отправке задачи: {e}")
    import traceback
    traceback.print_exc()

ENDTEST

chmod +x /tmp/test_bot_celery_app.py
python3 /tmp/test_bot_celery_app.py

# ========================================
# ШАГ 4: ПЕРЕЗАПУСК БОТА
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 4: Перезапуск бота"
echo "================================================================"

log_info "Перезапускаем бота..."
systemctl restart albimusic-bot

sleep 3

if systemctl is-active --quiet albimusic-bot; then
    log_info "Бот запущен"
else
    log_error "Бот не запустился!"
    journalctl -u albimusic-bot -n 50 --no-pager
    exit 1
fi

# ========================================
# ШАГ 5: МОНИТОРИНГ REDIS
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 5: Настройка мониторинга Redis"
echo "================================================================"

cat > /tmp/monitor_redis_publish.sh << 'ENDMONITOR'
#!/bin/bash
echo "🔍 Мониторинг Redis (ждём PUBLISH команд)"
echo "================================================================"
echo "Отправьте тестовый запрос из бота..."
echo ""
redis-cli monitor | grep --line-buffered -E "PUBLISH|LPUSH|RPUSH|celery"
ENDMONITOR

chmod +x /tmp/monitor_redis_publish.sh

log_info "Скрипт мониторинга создан: /tmp/monitor_redis_publish.sh"

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo -e "${BLUE}✅ ИСПРАВЛЕНИЕ ИМПОРТОВ ЗАВЕРШЕНО${NC}"
echo "================================================================"
echo ""
echo "📋 ЧТО БЫЛО СДЕЛАНО:"
echo ""
echo "1. ✅ Удалены все повторные импорты celery_tasks внутри функций"
echo "2. ✅ Проверено что используется один глобальный celery_app"
echo "3. ✅ Протестирована отправка задачи"
echo "4. ✅ Перезапущен бот"
echo ""
echo "📂 Бэкап: $BACKUP_DIR"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Проверьте вывод теста выше"
echo ""
echo "2. Если видите '✅ ЗАДАЧИ ЕСТЬ В ОЧЕРЕДИ!' - всё работает!"
echo ""
echo "3. Запустите мониторинг Redis в отдельном терминале:"
echo "   /tmp/monitor_redis_publish.sh"
echo ""
echo "4. Отправьте тестовый запрос из Telegram бота"
echo ""
echo "5. В мониторинге должны увидеть:"
echo "   • LPUSH celery '...'"
echo "   • PUBLISH celery.task '...'"
echo ""
echo "6. Следите за логами бота:"
echo "   journalctl -u albimusic-bot -f"
echo ""
echo "================================================================"

