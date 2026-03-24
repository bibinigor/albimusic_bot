#!/bin/bash
set -e

echo "🔍 ГЛУБОКАЯ ДИАГНОСТИКА: Почему задачи не публикуются в Redis"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# ========================================
# ШАГ 1: ПРОВЕРКА СОСТОЯНИЯ CELERY APP
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 1: Детальная проверка состояния Celery app"
echo "================================================================"

cat > /tmp/diagnose_celery_state.py << 'ENDTEST'
#!/usr/bin/env python3
import sys
import logging

# МАКСИМАЛЬНОЕ логирование
logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, '/root/albimusic-bot')

print("🔍 ДЕТАЛЬНАЯ ПРОВЕРКА CELERY APP")
print("="*80)

try:
    from celery_tasks import celery_app, generate_music_task
    
    print(f"\n1️⃣ БАЗОВАЯ ИНФОРМАЦИЯ:")
    print(f"   • App name: {celery_app.main}")
    print(f"   • App ID: {id(celery_app)}")
    print(f"   • Task ID: {id(generate_music_task)}")
    print(f"   • Task.app ID: {id(generate_music_task.app)}")
    
    if id(celery_app) == id(generate_music_task.app):
        print(f"   ✅ Задача использует правильный app")
    else:
        print(f"   ❌ Задача использует ДРУГОЙ app!")
    
    print(f"\n2️⃣ КОНФИГУРАЦИЯ:")
    print(f"   • broker_url: {celery_app.conf.broker_url}")
    print(f"   • result_backend: {celery_app.conf.result_backend}")
    print(f"   • task_always_eager: {celery_app.conf.task_always_eager}")
    print(f"   • task_eager_propagates: {celery_app.conf.task_eager_propagates}")
    
    print(f"\n3️⃣ ПРОВЕРКА ПОДКЛЮЧЕНИЯ К BROKER:")
    
    # Получаем соединение
    try:
        conn = celery_app.connection()
        print(f"   ✅ Connection object создан")
        print(f"      • Hostname: {conn.hostname}")
        print(f"      • Port: {conn.port}")
        print(f"      • Virtual host: {conn.virtual_host}")
        print(f"      • Transport: {conn.transport}")
        
        # Проверяем connected
        print(f"      • Connected: {conn.connected}")
        
        # Пытаемся подключиться
        print(f"\n   🔌 Пытаемся подключиться...")
        conn.connect()
        print(f"   ✅ Подключение установлено")
        
        # Проверяем что соединение работает
        conn.heartbeat_check()
        print(f"   ✅ Heartbeat OK")
        
        # Закрываем
        conn.release()
        print(f"   ✅ Соединение закрыто")
        
    except Exception as e:
        print(f"   ❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\n4️⃣ ПРОВЕРКА PRODUCER:")
    
    try:
        # Получаем producer
        with celery_app.producer_or_acquire() as producer:
            print(f"   ✅ Producer создан")
            print(f"      • Connection: {producer.connection}")
            print(f"      • Channel: {producer.channel}")
            print(f"      • Exchange: {producer.exchange}")
            
            # Проверяем что producer может публиковать
            print(f"\n   🧪 Тест публикации через Producer...")
            
            # Создаём тестовое сообщение
            test_message = {
                'id': 'test-producer-001',
                'task': 'test_task',
                'args': [42],
                'kwargs': {}
            }
            
            # Пытаемся опубликовать
            producer.publish(
                test_message,
                routing_key='celery',
                exchange='',
                serializer='json'
            )
            
            print(f"   ✅ Producer.publish() выполнен без ошибок")
            
    except Exception as e:
        print(f"   ❌ ОШИБКА PRODUCER: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n5️⃣ ПРОВЕРКА apply_async() С ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ:")
    
    # Включаем DEBUG для kombu
    kombu_logger = logging.getLogger('kombu')
    kombu_logger.setLevel(logging.DEBUG)
    
    print(f"\n   🚀 Отправка задачи...")
    
    try:
        result = generate_music_task.apply_async(
            args=[338544009, 'Диагностический тест'],
            kwargs={'task_id': 'diagnose_001'}
        )
        
        print(f"\n   ✅ apply_async() завершён:")
        print(f"      • Task ID: {result.id}")
        print(f"      • State: {result.state}")
        print(f"      • Backend: {result.backend}")
        
        # Проверяем Redis
        import redis
        import time
        
        time.sleep(1)
        
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        
        queue_len = r.llen('celery')
        print(f"\n   📊 Проверка Redis:")
        print(f"      • Длина очереди 'celery': {queue_len}")
        
        if queue_len > 0:
            print(f"      ✅ ЗАДАЧА В ОЧЕРЕДИ!")
            tasks = r.lrange('celery', 0, -1)
            for i, task in enumerate(tasks, 1):
                print(f"         {i}. {task.decode('utf-8')[:100]}...")
        else:
            print(f"      ❌ ОЧЕРЕДЬ ПУСТА!")
            print(f"\n      🔍 Все ключи в Redis db=0:")
            
            keys = r.keys('*')
            print(f"         Всего ключей: {len(keys)}")
            
            for key in keys:
                key_str = key.decode('utf-8')
                key_type = r.type(key).decode('utf-8')
                print(f"         • {key_str} ({key_type})")
        
    except Exception as e:
        print(f"\n   ❌ ОШИБКА apply_async(): {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

ENDTEST

python3 /tmp/diagnose_celery_state.py

# ========================================
# ШАГ 2: ТЕСТ С ЯВНЫМ send_task()
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 2: Тест с явным send_task()"
echo "================================================================"

cat > /tmp/test_send_task.py << 'ENDTEST'
#!/usr/bin/env python3
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, '/root/albimusic-bot')

print("🔍 ТЕСТ: Явный send_task() вместо apply_async()")
print("="*80)

try:
    from celery_tasks import celery_app
    
    print(f"\n✅ Celery app загружен")
    
    # Отправляем задачу через send_task()
    print(f"\n🚀 Отправка через send_task()...")
    
    result = celery_app.send_task(
        'generate_music_task',
        args=[338544009, 'Тест через send_task'],
        kwargs={'task_id': 'send_task_test_001'}
    )
    
    print(f"\n✅ send_task() завершён:")
    print(f"   • Task ID: {result.id}")
    print(f"   • State: {result.state}")
    
    # Проверяем Redis
    import redis
    import time
    
    time.sleep(1)
    
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    queue_len = r.llen('celery')
    
    print(f"\n📊 Redis:")
    print(f"   • Длина очереди: {queue_len}")
    
    if queue_len > 0:
        print(f"   ✅ ЗАДАЧА В REDIS!")
    else:
        print(f"   ❌ ЗАДАЧА НЕ В REDIS!")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

ENDTEST

python3 /tmp/test_send_task.py

# ========================================
# ШАГ 3: ПРОВЕРКА БИБЛИОТЕКИ KOMBU
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 3: Проверка kombu (библиотека для работы с broker)"
echo "================================================================"

cat > /tmp/test_kombu_direct.py << 'ENDTEST'
#!/usr/bin/env python3
import sys

print("🔍 ТЕСТ: Прямая работа с kombu")
print("="*80)

try:
    from kombu import Connection, Exchange, Queue, Producer
    
    print(f"\n✅ kombu импортирован")
    
    # Создаём соединение
    conn = Connection('redis://127.0.0.1:6379/0')
    
    print(f"\n🔌 Подключаемся к Redis через kombu...")
    conn.connect()
    print(f"✅ Подключение установлено")
    
    # Создаём producer
    with conn.Producer() as producer:
        print(f"\n📤 Публикуем тестовое сообщение...")
        
        producer.publish(
            {'test': 'message', 'id': 'kombu-test-001'},
            routing_key='celery',
            exchange='',
            serializer='json'
        )
        
        print(f"✅ Сообщение опубликовано")
    
    # Проверяем Redis
    import redis
    import time
    
    time.sleep(1)
    
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    queue_len = r.llen('celery')
    
    print(f"\n📊 Redis:")
    print(f"   • Длина очереди: {queue_len}")
    
    if queue_len > 0:
        print(f"   ✅ СООБЩЕНИЕ В REDIS!")
        
        # Читаем сообщение
        msg = r.lrange('celery', -1, -1)[0]
        print(f"   • Последнее сообщение: {msg.decode('utf-8')[:100]}...")
    else:
        print(f"   ❌ СООБЩЕНИЕ НЕ В REDIS!")
    
    conn.release()
    print(f"\n✅ Соединение закрыто")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

ENDTEST

python3 /tmp/test_kombu_direct.py

# ========================================
# ШАГ 4: ПРОВЕРКА ВЕРСИЙ БИБЛИОТЕК
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 4: Проверка версий библиотек"
echo "================================================================"

log_info "Версии библиотек:"
pip3 list | grep -E "celery|redis|kombu|amqp|billiard|vine"

# ========================================
# ШАГ 5: СРАВНЕНИЕ С МИНИМАЛЬНОЙ КОНФИГУРАЦИЕЙ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 5: Тест с минимальной конфигурацией Celery"
echo "================================================================"

cat > /tmp/test_minimal.py << 'ENDTEST'
#!/usr/bin/env python3
from celery import Celery
import logging

logging.basicConfig(level=logging.DEBUG)

print("🔍 ТЕСТ: Минимальная конфигурация Celery")
print("="*80)

# Создаём минимальный app
app = Celery('minimal')

# ЯВНАЯ конфигурация (без словаря)
app.conf.broker_url = 'redis://127.0.0.1:6379/0'
app.conf.result_backend = 'redis://127.0.0.1:6379/2'
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.task_always_eager = False

print(f"\n✅ App создан")
print(f"   • broker_url: {app.conf.broker_url}")
print(f"   • task_always_eager: {app.conf.task_always_eager}")

@app.task(name='minimal_task')
def test():
    return 42

print(f"\n✅ Задача зарегистрирована")

# Отправляем
print(f"\n🚀 Отправка задачи...")

result = test.apply_async()

print(f"\n✅ Задача отправлена:")
print(f"   • Task ID: {result.id}")
print(f"   • State: {result.state}")

# Проверяем Redis
import redis
import time

time.sleep(1)

r = redis.Redis(host='127.0.0.1', port=6379, db=0)
queue_len = r.llen('celery')

print(f"\n📊 Redis:")
print(f"   • Длина очереди: {queue_len}")

if queue_len > 0:
    print(f"   ✅ МИНИМАЛЬНАЯ КОНФИГУРАЦИЯ РАБОТАЕТ!")
    print(f"   Проблема в основной конфигурации celery_tasks.py")
else:
    print(f"   ❌ ДАЖЕ МИНИМАЛЬНАЯ КОНФИГУРАЦИЯ НЕ РАБОТАЕТ!")
    print(f"   Проблема глубже - возможно с Redis или kombu")

ENDTEST

python3 /tmp/test_minimal.py

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo -e "${BLUE}📊 ИТОГИ ГЛУБОКОЙ ДИАГНОСТИКИ${NC}"
echo "================================================================"
echo ""
echo "Проанализируйте выводы тестов выше:"
echo ""
echo "1️⃣ Если Producer.publish() работает, но apply_async() НЕ публикует:"
echo "   → Проблема в вызове apply_async()"
echo "   → Используйте send_task() вместо apply_async()"
echo ""
echo "2️⃣ Если kombu напрямую работает, но Celery НЕ публикует:"
echo "   → Проблема в конфигурации Celery app"
echo "   → Проверьте порядок инициализации"
echo ""
echo "3️⃣ Если минимальная конфигурация работает:"
echo "   → Проблема в celery_tasks.py"
echo "   → Сравните конфигурации"
echo ""
echo "4️⃣ Если НИЧЕГО не работает:"
echo "   → Проблема с Redis или kombu"
echo "   → Переустановите библиотеки"
echo ""
echo "================================================================"

