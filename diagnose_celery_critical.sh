#!/bin/bash
set -e

echo "🔍 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Почему задачи не в Redis"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${BLUE}📝 $1${NC}"; }

# ========================================
# ШАГ 1: ВКЛЮЧАЕМ МАКСИМАЛЬНОЕ ЛОГИРОВАНИЕ
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 1: Включаем детальное логирование Celery"
echo "================================================================"

cat > /tmp/test_celery_verbose.py << 'ENDTEST'
#!/usr/bin/env python3
import sys
import os
import logging

# МАКСИМАЛЬНОЕ ЛОГИРОВАНИЕ
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Включаем debug логи для Celery
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Включаем логи для kombu (библиотека для работы с broker)
kombu_logger = logging.getLogger('kombu')
kombu_logger.setLevel(logging.DEBUG)

# Включаем логи для Redis
redis_logger = logging.getLogger('redis')
redis_logger.setLevel(logging.DEBUG)

sys.path.insert(0, '/root/albimusic-bot')

print("="*80)
print("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА ОТПРАВКИ ЗАДАЧИ")
print("="*80)

try:
    from celery_tasks import celery_app, generate_music_task
    
    print(f"\n✅ Celery app загружен: {celery_app.main}")
    print(f"✅ Broker URL: {celery_app.conf.broker_url}")
    print(f"✅ Result backend: {celery_app.conf.result_backend}")
    
    # Проверяем конфигурацию сериализации
    print(f"\n📋 КОНФИГУРАЦИЯ СЕРИАЛИЗАЦИИ:")
    print(f"   • task_serializer: {celery_app.conf.task_serializer}")
    print(f"   • result_serializer: {celery_app.conf.result_serializer}")
    print(f"   • accept_content: {celery_app.conf.accept_content}")
    
    # Проверяем очереди
    print(f"\n📋 КОНФИГУРАЦИЯ ОЧЕРЕДЕЙ:")
    print(f"   • task_default_queue: {celery_app.conf.task_default_queue}")
    print(f"   • task_routes: {celery_app.conf.task_routes}")
    
    # Проверяем соединение с broker ВРУЧНУЮ
    print(f"\n🔍 ПРОВЕРКА СОЕДИНЕНИЯ С BROKER...")
    
    try:
        with celery_app.connection_or_acquire() as conn:
            print(f"✅ Соединение установлено")
            print(f"   • Hostname: {conn.hostname}")
            print(f"   • Port: {conn.port}")
            print(f"   • Virtual host: {conn.virtual_host}")
            print(f"   • Transport: {conn.transport}")
            
            # Проверяем что соединение реально работает
            conn.connect()
            print(f"✅ Соединение активно")
            
    except Exception as e:
        print(f"❌ ОШИБКА СОЕДИНЕНИЯ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Пытаемся отправить задачу с детальным логированием
    print(f"\n🚀 ОТПРАВКА ТЕСТОВОЙ ЗАДАЧИ...")
    print(f"   Смотрите логи выше для деталей...")
    
    result = generate_music_task.apply_async(
        args=[338544009, 'Тестовая музыка для диагностики'],
        kwargs={'task_id': 'diagnostic_test_001'},
        countdown=5  # Отложенный запуск на 5 секунд
    )
    
    print(f"\n✅ ЗАДАЧА СОЗДАНА:")
    print(f"   • Task ID: {result.id}")
    print(f"   • Task name: {result.task_name}")
    print(f"   • State: {result.state}")
    print(f"   • Backend: {result.backend}")
    
    # Проверяем backend
    print(f"\n🔍 ПРОВЕРКА RESULT BACKEND...")
    try:
        backend_result = result.backend.get(result.id)
        print(f"   • Backend result: {backend_result}")
    except Exception as e:
        print(f"   • Backend result: None (задача ещё не выполнена)")
    
    # Ждём и проверяем состояние
    import time
    print(f"\n⏳ Ожидание 3 секунды...")
    time.sleep(3)
    
    print(f"\n🔍 СОСТОЯНИЕ ПОСЛЕ ОЖИДАНИЯ:")
    print(f"   • State: {result.state}")
    print(f"   • Ready: {result.ready()}")
    
    # Проверяем Redis напрямую
    print(f"\n🔍 ПРОВЕРКА REDIS НАПРЯМУЮ...")
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    # Ищем ключи связанные с задачей
    task_keys = []
    for key in r.keys('*'):
        key_str = key.decode('utf-8')
        if result.id in key_str or 'diagnostic_test' in key_str:
            task_keys.append(key_str)
    
    if task_keys:
        print(f"   ✅ Найдены ключи задачи в Redis:")
        for key in task_keys:
            print(f"      • {key}")
    else:
        print(f"   ❌ НЕТ КЛЮЧЕЙ ЗАДАЧИ В REDIS!")
        print(f"   Это подтверждает что задача не была отправлена в broker")
    
    # Проверяем ВСЕ ключи в Redis
    print(f"\n🔍 ВСЕ КЛЮЧИ В REDIS:")
    all_keys = r.keys('*')
    print(f"   • Всего ключей: {len(all_keys)}")
    
    for key in all_keys:
        key_str = key.decode('utf-8')
        key_type = r.type(key).decode('utf-8')
        
        if key_type == 'list':
            length = r.llen(key)
            print(f"   • {key_str} (list, len={length})")
        elif key_type == 'set':
            length = r.scard(key)
            print(f"   • {key_str} (set, len={length})")
        elif key_type == 'zset':
            length = r.zcard(key)
            print(f"   • {key_str} (zset, len={length})")
        else:
            print(f"   • {key_str} ({key_type})")
    
    print("\n" + "="*80)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
ENDTEST

chmod +x /tmp/test_celery_verbose.py

log_info "Запускаем детальную диагностику..."
echo ""
python3 /tmp/test_celery_verbose.py 2>&1 | tee /tmp/celery_diagnostic.log
echo ""

log_info "Логи сохранены в: /tmp/celery_diagnostic.log"

# ========================================
# ШАГ 2: ПРОВЕРКА КОНФИГУРАЦИИ BROKER
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 2: Проверка конфигурации broker в файлах"
echo "================================================================"

log_info "Проверяем celery_tasks.py..."
grep -n "broker_url" /root/albimusic-bot/celery_tasks.py || log_warn "Не найден broker_url"

log_info "Проверяем celery_config.py..."
if [ -f "/root/albimusic-bot/celery_config.py" ]; then
    grep -n "broker_url" /root/albimusic-bot/celery_config.py || log_warn "Не найден broker_url"
else
    log_warn "Файл celery_config.py не существует!"
fi

# ========================================
# ШАГ 3: ТЕСТ ПРЯМОЙ ПУБЛИКАЦИИ В REDIS
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 3: Тест прямой публикации в Redis (обход Celery)"
echo "================================================================"

cat > /tmp/test_redis_publish.py << 'ENDTEST'
#!/usr/bin/env python3
import redis
import json
import uuid

print("🔍 Тест прямой публикации в Redis...")

r = redis.Redis(host='localhost', port=6379, db=0)

# Создаём задачу вручную (имитируя Celery)
task_id = str(uuid.uuid4())
task_data = {
    'id': task_id,
    'task': 'generate_music_task',
    'args': [338544009, 'Тест'],
    'kwargs': {'task_id': 'manual_test_123'},
}

print(f"✅ Создана задача: {task_id}")

# Публикуем в очередь celery
queue_key = 'celery'

try:
    # Сериализуем
    task_json = json.dumps(task_data)
    
    # Публикуем в список (очередь)
    r.lpush(queue_key, task_json)
    
    print(f"✅ Задача опубликована в очередь: {queue_key}")
    
    # Проверяем длину очереди
    queue_len = r.llen(queue_key)
    print(f"✅ Длина очереди: {queue_len}")
    
    # Читаем задачу обратно
    task_from_queue = r.lrange(queue_key, 0, 0)
    print(f"✅ Задача в очереди: {task_from_queue[0].decode('utf-8')[:100]}...")
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
ENDTEST

python3 /tmp/test_redis_publish.py

# ========================================
# ШАГ 4: СРАВНЕНИЕ С АРХИВНОЙ ВЕРСИЕЙ
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 4: Сравнение конфигурации с архивной версией"
echo "================================================================"

ARCHIVE_CELERY="/tmp/albi_archive_check/albi_final/albimusic-bot/celery_tasks.py"

if [ -f "$ARCHIVE_CELERY" ]; then
    log_info "Сравниваем создание Celery app..."
    
    echo ""
    echo "🔍 ТЕКУЩАЯ ВЕРСИЯ:"
    grep -A 5 "celery_app = Celery" /root/albimusic-bot/celery_tasks.py | head -10
    
    echo ""
    echo "🔍 АРХИВНАЯ ВЕРСИЯ:"
    grep -A 5 "celery_app = Celery" "$ARCHIVE_CELERY" | head -10
    
    echo ""
    log_info "Сравниваем конфигурацию broker..."
    
    echo ""
    echo "🔍 ТЕКУЩАЯ ВЕРСИЯ:"
    grep -A 3 "broker_url" /root/albimusic-bot/celery_tasks.py || echo "Не найдено"
    
    echo ""
    echo "🔍 АРХИВНАЯ ВЕРСИЯ:"
    grep -A 3 "broker_url" "$ARCHIVE_CELERY" || echo "Не найдено"
else
    log_warn "Архивная версия не найдена"
fi

# ========================================
# ШАГ 5: ПРОВЕРКА ВЕРСИЙ БИБЛИОТЕК
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 5: Проверка версий библиотек"
echo "================================================================"

log_info "Версии установленных пакетов:"
pip3 list | grep -E "celery|redis|kombu|amqp|billiard"

# ========================================
# ШАГ 6: СОЗДАНИЕ МИНИМАЛЬНОЙ ТЕСТОВОЙ КОНФИГУРАЦИИ
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 6: Тест с минимальной конфигурацией"
echo "================================================================"

cat > /tmp/test_minimal_celery.py << 'ENDTEST'
#!/usr/bin/env python3
from celery import Celery
import logging

logging.basicConfig(level=logging.DEBUG)

print("🔍 Тест с минимальной конфигурацией Celery...")

# Создаём минимальный Celery app
app = Celery('minimal_test')
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

print(f"✅ App создан: {app.main}")

@app.task(name='minimal_test_task')
def test_task(x):
    return x * 2

print(f"✅ Задача зарегистрирована")

# Пытаемся отправить
result = test_task.apply_async(args=[42])

print(f"✅ Задача отправлена:")
print(f"   • Task ID: {result.id}")
print(f"   • State: {result.state}")

# Проверяем Redis
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

import time
time.sleep(1)

# Ищем задачу
found = False
for key in r.keys('*'):
    key_str = key.decode('utf-8')
    if result.id in key_str or 'minimal_test' in key_str:
        print(f"   ✅ Найден ключ: {key_str}")
        found = True

if not found:
    print(f"   ❌ Задача НЕ НАЙДЕНА в Redis!")
    print(f"   Все ключи:")
    for key in r.keys('*'):
        print(f"      • {key.decode('utf-8')}")
ENDTEST

python3 /tmp/test_minimal_celery.py

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo -e "${BLUE}📊 ИТОГИ ДИАГНОСТИКИ${NC}"
echo "================================================================"
echo ""
echo "Проверьте логи выше и найдите:"
echo ""
echo "1. ❌ Если есть ошибки CONNECTION или TIMEOUT:"
echo "   → Проблема с соединением Redis"
echo ""
echo "2. ❌ Если есть ошибки SERIALIZATION:"
echo "   → Проблема с сериализацией аргументов задачи"
echo ""
echo "3. ❌ Если задачи НЕ появляются в Redis:"
echo "   → Celery не отправляет задачи в broker"
echo "   → Возможно неправильная конфигурация broker_url"
echo ""
echo "4. ✅ Если минимальный тест РАБОТАЕТ:"
echo "   → Проблема в конфигурации основного app"
echo ""
echo "================================================================"
echo ""
echo "📂 Все логи сохранены в /tmp/"
echo ""

