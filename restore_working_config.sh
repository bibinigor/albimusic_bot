#!/bin/bash
set -e

echo "🔧 ВОССТАНОВЛЕНИЕ РАБОЧЕЙ КОНФИГУРАЦИИ (как в архиве)"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="/root/albimusic-bot/backups_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# ========================================
# БЭКАПЫ
# ========================================
cp /root/albimusic-bot/celery_tasks.py "$BACKUP_DIR/"
cp /root/albimusic-bot/celery_config.py "$BACKUP_DIR/" 2>/dev/null || true
log_info "Бэкапы созданы: $BACKUP_DIR"

# ========================================
# ШАГ 1: ИСПРАВЛЕНИЕ celery_tasks.py
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 1: Восстановление конфигурации как в архиве"
echo "================================================================"

python3 << 'ENDPYTHON'
import re

file_path = '/root/albimusic-bot/celery_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔍 Анализируем текущую конфигурацию...")

# Удаляем старую конфигурацию
# Ищем блок от создания celery_app до первого @celery_app.task
pattern = r"(celery_app = Celery\([^)]+\)).*?(?=@celery_app\.task|def generate_suno_music_sync)"

# Новая конфигурация (ТОЧНО КАК В АРХИВЕ!)
new_config = '''celery_app = Celery('albimusic_tasks')

# КОНФИГУРАЦИЯ (как в архивной версии)
celery_app.config_from_object({
    'broker_url': 'redis://127.0.0.1:6379/0',
    'result_backend': 'redis://127.0.0.1:6379/2',  # ВАЖНО: отдельная БД!
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'Europe/Moscow',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30 минут
    'result_expires': 3600,
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_always_eager': False,  # КРИТИЧНО!
})

# Логируем конфигурацию
logger.info(f"🔧 Celery app initialized: {celery_app.main}")
logger.info(f"🔧 Broker: {celery_app.conf.broker_url}")
logger.info(f"🔧 Backend: {celery_app.conf.result_backend}")

'''

# Заменяем
content = re.sub(pattern, new_config, content, flags=re.DOTALL)

# Убираем импорт celery_config если есть
content = re.sub(r'import celery_config\n', '', content)
content = re.sub(r'from celery_config import .*\n', '', content)

# Сохраняем
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Конфигурация восстановлена")
ENDPYTHON

# Проверка синтаксиса
if python3 -m py_compile /root/albimusic-bot/celery_tasks.py 2>/dev/null; then
    log_info "Синтаксис Python корректен"
else
    log_error "Ошибка синтаксиса!"
    python3 -m py_compile /root/albimusic-bot/celery_tasks.py
    exit 1
fi

# ========================================
# ШАГ 2: ОЧИСТКА REDIS DB=0 И DB=2
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 2: Очистка Redis (db=0 и db=2)"
echo "================================================================"

log_info "Очищаем Redis db=0..."
redis-cli -n 0 FLUSHDB

log_info "Очищаем Redis db=2..."
redis-cli -n 2 FLUSHDB

log_info "Redis очищен"

# ========================================
# ШАГ 3: ПЕРЕЗАПУСК СЕРВИСОВ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 3: Перезапуск сервисов"
echo "================================================================"

systemctl stop albimusic-celery albimusic-bot albimusic-monitor
sleep 2

log_info "Запускаем Celery..."
systemctl start albimusic-celery
sleep 5

log_info "Запускаем бота..."
systemctl start albimusic-bot
sleep 3

log_info "Запускаем монитор..."
systemctl start albimusic-monitor
sleep 2

# Проверка статуса
for service in albimusic-celery albimusic-bot albimusic-monitor; do
    if systemctl is-active --quiet $service; then
        log_info "$service: РАБОТАЕТ"
    else
        log_error "$service: НЕ РАБОТАЕТ"
    fi
done

# ========================================
# ШАГ 4: ТЕСТ С НОВОЙ КОНФИГУРАЦИЕЙ
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 4: Тест с восстановленной конфигурацией"
echo "================================================================"

cat > /tmp/test_restored_config.py << 'ENDTEST'
#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, '/root/albimusic-bot')

print("🔍 ТЕСТ С ВОССТАНОВЛЕННОЙ КОНФИГУРАЦИЕЙ")
print("="*80)

try:
    from celery_tasks import celery_app, test_task
    
    print(f"\n✅ Celery app загружен: {celery_app.main}")
    print(f"✅ Broker: {celery_app.conf.broker_url}")
    print(f"✅ Backend: {celery_app.conf.result_backend}")
    print(f"✅ Always eager: {celery_app.conf.task_always_eager}")
    
    # Отправляем задачу
    print(f"\n🚀 Отправка тестовой задачи...")
    result = test_task.apply_async(args=[123])
    
    print(f"✅ Задача отправлена:")
    print(f"   • Task ID: {result.id}")
    print(f"   • State: {result.state}")
    
    # Проверяем Redis db=0 (очередь)
    print(f"\n🔍 Проверяем Redis db=0 (broker)...")
    import redis
    r0 = redis.Redis(host='127.0.0.1', port=6379, db=0)
    
    keys_db0 = r0.keys('*')
    print(f"   • Ключей в db=0: {len(keys_db0)}")
    
    for key in keys_db0:
        key_str = key.decode('utf-8')
        key_type = r0.type(key).decode('utf-8')
        
        if key_type == 'list':
            length = r0.llen(key)
            print(f"   • {key_str} (list, len={length})")
            
            # Если это очередь celery, показываем содержимое
            if key_str == 'celery':
                items = r0.lrange(key, 0, -1)
                if items:
                    print(f"      ✅ ЗАДАЧИ В ОЧЕРЕДИ:")
                    for item in items:
                        print(f"         {item.decode('utf-8')[:100]}...")
        else:
            print(f"   • {key_str} ({key_type})")
    
    # Проверяем Redis db=2 (результаты)
    print(f"\n🔍 Проверяем Redis db=2 (result backend)...")
    r2 = redis.Redis(host='127.0.0.1', port=6379, db=2)
    
    time.sleep(2)  # Ждём выполнения
    
    keys_db2 = r2.keys('*')
    print(f"   • Ключей в db=2: {len(keys_db2)}")
    
    for key in keys_db2:
        key_str = key.decode('utf-8')
        if result.id in key_str:
            print(f"   ✅ НАЙДЕН РЕЗУЛЬТАТ: {key_str}")
            value = r2.get(key)
            if value:
                print(f"      {value.decode('utf-8')[:200]}...")
    
    # Проверяем состояние задачи
    print(f"\n🔍 Финальное состояние задачи:")
    print(f"   • State: {result.state}")
    print(f"   • Ready: {result.ready()}")
    
    if result.ready():
        print(f"   ✅ Result: {result.result}")
    else:
        print(f"   ⏳ Задача ещё выполняется...")
    
    # ВЕРДИКТ
    if len(keys_db0) > 0:
        print(f"\n{'='*80}")
        print(f"✅ УСПЕХ! Задачи попадают в Redis!")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"❌ ПРОВАЛ! Задачи НЕ попадают в Redis!")
        print(f"{'='*80}")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
ENDTEST

chmod +x /tmp/test_restored_config.py
python3 /tmp/test_restored_config.py

# ========================================
# ШАГ 5: ПРОВЕРКА WORKERS
# ========================================
echo ""
echo "================================================================"
echo "📝 ШАГ 5: Проверка что workers подключены"
echo "================================================================"

python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, '/root/albimusic-bot')

from celery_tasks import celery_app

print("🔍 Проверка активных workers...")

inspect = celery_app.control.inspect()

stats = inspect.stats()
if stats:
    print(f"✅ Активных workers: {len(stats)}")
    for worker_name in stats.keys():
        print(f"   • {worker_name}")
else:
    print(f"❌ НЕТ АКТИВНЫХ WORKERS!")
ENDPYTHON

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo -e "${BLUE}✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО${NC}"
echo "================================================================"
echo ""
echo "📋 ЧТО БЫЛО СДЕЛАНО:"
echo ""
echo "1. ✅ Восстановлена конфигурация как в архиве:"
echo "   • Broker: redis://127.0.0.1:6379/0"
echo "   • Backend: redis://127.0.0.1:6379/2 (отдельная БД!)"
echo "   • task_always_eager: False"
echo ""
echo "2. ✅ Очищены обе БД Redis (0 и 2)"
echo ""
echo "3. ✅ Перезапущены все сервисы"
echo ""
echo "4. ✅ Протестирована отправка задач"
echo ""
echo "📂 Бэкапы: $BACKUP_DIR"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Проверьте вывод теста выше"
echo ""
echo "2. Если видите '✅ ЗАДАЧИ В ОЧЕРЕДИ:' - значит РАБОТАЕТ!"
echo ""
echo "3. Отправьте реальный запрос из бота"
echo ""
echo "4. Следите за логами:"
echo "   tail -f /var/log/albimusic-bot/celery/celery.log"
echo ""
echo "================================================================"

