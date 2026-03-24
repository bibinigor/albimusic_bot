#!/bin/bash
set -e

echo "🚀 КОМПЛЕКСНОЕ ВОССТАНОВЛЕНИЕ СИСТЕМЫ"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="/root/albimusic-bot/backups_comprehensive_$(date +%Y%m%d_%H%M%S)"
ARCHIVE_DIR="/tmp/albi_archive_check/albi_final/albimusic-bot"

mkdir -p "$BACKUP_DIR"

# ========================================
# ФУНКЦИИ
# ========================================
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}📝 $1${NC}"
}

backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        log_info "Бэкап: $(basename $file)"
    fi
}

check_syntax() {
    local file=$1
    if python3 -m py_compile "$file" 2>/dev/null; then
        log_info "Синтаксис OK: $(basename $file)"
        return 0
    else
        log_error "ОШИБКА синтаксиса: $(basename $file)"
        python3 -m py_compile "$file"
        return 1
    fi
}

# ========================================
# ШАГ 1: СОЗДАНИЕ БЭКАПОВ
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 1/6: Создание бэкапов"
echo "================================================================"

backup_file "/root/albimusic-bot/celery_tasks.py"
backup_file "/root/albimusic-bot/celery_config.py"
backup_file "/root/albimusic-bot/main_with_payments.py"
backup_file "/root/albimusic-bot/run_monitor_notify.py"

log_info "Бэкапы сохранены в: $BACKUP_DIR"

# ========================================
# ШАГ 2: ВОССТАНОВЛЕНИЕ celery_config.py ИЗ АРХИВА
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 2/6: Восстановление celery_config.py из архива"
echo "================================================================"

if [ -f "$ARCHIVE_DIR/celery_config.py" ]; then
    cp "$ARCHIVE_DIR/celery_config.py" "/root/albimusic-bot/celery_config.py"
    log_info "celery_config.py восстановлен из архива"
else
    log_warn "Архивная версия не найдена, создаём новую"
    
    cat > /root/albimusic-bot/celery_config.py << 'ENDCONFIG'
# Celery Configuration
from kombu import Queue

# Broker settings
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Moscow'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100

# Task time limits
task_soft_time_limit = 1800  # 30 минут
task_time_limit = 2000       # 33 минуты

# Result backend settings
result_expires = 3600

# Queue configuration
task_default_queue = 'celery'
task_queues = (
    Queue('celery', routing_key='celery'),
)

# Task routing
task_routes = {
    'generate_music_task': {'queue': 'celery'},
    'generate_song_task': {'queue': 'celery'},
}

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
ENDCONFIG

    log_info "Создан новый celery_config.py"
fi

# ========================================
# ШАГ 3: ИСПРАВЛЕНИЕ celery_tasks.py
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 3/6: Исправление celery_tasks.py"
echo "================================================================"

python3 << 'ENDPYTHON'
import re
import sys

file_path = '/root/albimusic-bot/celery_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔍 Анализируем текущую структуру...")

# 1. Проверяем есть ли import celery_config
if 'import celery_config' not in content and 'from celery_config import' not in content:
    print("❌ Нет импорта celery_config")
    
    # Находим строку после импорта config
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == 'import config':
            lines.insert(i + 1, 'import celery_config')
            print("✅ Добавлен: import celery_config")
            break
    
    content = '\n'.join(lines)
else:
    print("✅ Импорт celery_config уже есть")

# 2. Проверяем создание Celery app
if "celery_app = Celery('albimusic_tasks')" not in content:
    print("❌ Неправильное создание Celery app")
    
    # Заменяем создание app
    old_app = r"celery_app = Celery\('.*?'\)"
    new_app = "celery_app = Celery('albimusic_tasks')"
    content = re.sub(old_app, new_app, content)
    print("✅ Исправлено создание Celery app")
else:
    print("✅ Celery app создан правильно")

# 3. Проверяем конфигурацию через celery_config
if 'celery_app.config_from_object(celery_config)' not in content:
    print("❌ Нет загрузки конфигурации из celery_config")
    
    # Ищем строку после создания celery_app
    pattern = r"(celery_app = Celery\('albimusic_tasks'\))"
    replacement = r"\1\ncelery_app.config_from_object(celery_config)"
    content = re.sub(pattern, replacement, content)
    print("✅ Добавлена загрузка конфигурации")
else:
    print("✅ Конфигурация загружается правильно")

# 4. Убираем дублирующую конфигурацию
if 'celery_app.conf.update(' in content:
    print("⚠️  Найдена дублирующая конфигурация через conf.update()")
    
    # Комментируем блок conf.update
    pattern = r'(celery_app\.conf\.update\([\s\S]*?\n\))'
    content = re.sub(pattern, r'# \1  # Закомментировано: используем celery_config.py', content)
    print("✅ Закомментирована дублирующая конфигурация")

# 5. Проверяем импорт json
if 'import json' not in content:
    lines = content.split('\n')
    lines.insert(0, 'import json')
    content = '\n'.join(lines)
    print("✅ Добавлен: import json")
else:
    print("✅ import json уже есть")

# 6. Исправляем обработку ответа Suno API
print("🔧 Исправляем обработку ответа Suno API...")

# Находим блок обработки ответа
suno_response_pattern = r'if response\.status_code == 200:.*?task_id = .*?\.get\([\'"]taskId[\'"]\)'

if re.search(suno_response_pattern, content, re.DOTALL):
    print("✅ Найден блок обработки ответа Suno API")
    
    # Новый блок обработки
    new_response_block = '''if response.status_code == 200:
            result = response.json()
            
            # ПОЛНОЕ ЛОГИРОВАНИЕ ОТВЕТА
            logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
            logger.info(f"[{request_id}]    • Response size: {len(response.text)} bytes")
            logger.info(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)}")
            
            # Проверяем код ответа API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            logger.info(f"[{request_id}]    • API Code: {api_code}")
            logger.info(f"[{request_id}]    • API Message: {api_msg}")
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                logger.error(f"[{request_id}]    • Data: {data_obj}")
                return None
            
            # Проверяем data
            if not data_obj:
                logger.error(f"[{request_id}] ❌ SUNO API: data is null!")
                return None
            
            if not isinstance(data_obj, dict):
                logger.error(f"[{request_id}] ❌ data не словарь: {type(data_obj)}")
                return None
            
            logger.info(f"[{request_id}]    • Data keys: {list(data_obj.keys())}")
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')'''
    
    content = re.sub(suno_response_pattern, new_response_block, content, flags=re.DOTALL)
    print("✅ Обработка ответа Suno API исправлена")
else:
    print("⚠️  Не найден блок обработки ответа (может быть уже исправлен)")

# Сохраняем
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ celery_tasks.py обновлён")
ENDPYTHON

check_syntax "/root/albimusic-bot/celery_tasks.py" || {
    log_error "Ошибка синтаксиса в celery_tasks.py!"
    cp "$BACKUP_DIR/celery_tasks.py" "/root/albimusic-bot/celery_tasks.py"
    exit 1
}

# ========================================
# ШАГ 4: ДОБАВЛЕНИЕ ЛОГИРОВАНИЯ ЗАПРОСОВ
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 4/6: Добавление логирования запросов к Suno API"
echo "================================================================"

python3 << 'ENDPYTHON'
file_path = '/root/albimusic-bot/celery_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку с requests.post для Suno API
for i, line in enumerate(lines):
    if 'response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate/music"' in line:
        indent = ' ' * 12
        
        # Проверяем, не добавлено ли уже логирование
        if i > 0 and 'ОТПРАВКА ЗАПРОСА В SUNO API' in lines[i-1]:
            print("✅ Логирование запросов уже добавлено")
            break
        
        log_lines = [
            f'{indent}# 📤 ЛОГИРОВАНИЕ ЗАПРОСА\n',
            f'{indent}logger.info(f"[{{request_id}}] 📤 ОТПРАВКА ЗАПРОСА В SUNO API:")\n',
            f'{indent}logger.info(f"[{{request_id}}]    • URL: {{config.SUNO_API_URL}}/api/v1/generate/music")\n',
            f'{indent}logger.info(f"[{{request_id}}]    • Custom mode: {{custom_mode}}")\n',
            f'{indent}logger.info(f"[{{request_id}}]    • Is song: {{is_song}}")\n',
            f'{indent}logger.info(f"[{{request_id}}]    • Prompt length: {{len(prompt)}} символов")\n',
            f'{indent}logger.info(f"[{{request_id}}]    • Prompt: {{prompt[:300]}}...")\n',
            f'{indent}logger.info(f"[{{request_id}}]    • Payload: {{json.dumps(payload, ensure_ascii=False)[:500]}}...")\n',
            f'{indent}\n',
        ]
        
        lines = lines[:i] + log_lines + lines[i:]
        print("✅ Добавлено логирование запросов")
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
ENDPYTHON

check_syntax "/root/albimusic-bot/celery_tasks.py"

# ========================================
# ШАГ 5: ПРОВЕРКА REDIS И ОЧИСТКА
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 5/6: Проверка и очистка Redis"
echo "================================================================"

# Проверяем Redis
if redis-cli ping > /dev/null 2>&1; then
    log_info "Redis работает"
    
    # Показываем текущие ключи
    log_info "Текущие ключи в Redis:"
    redis-cli keys "*" | head -20
    
    # Очищаем старые задачи
    log_warn "Очистка старых задач в Redis..."
    redis-cli DEL celery || true
    redis-cli DEL _kombu.binding.celery || true
    redis-cli DEL unacked || true
    
    log_info "Redis очищен"
else
    log_error "Redis не работает!"
    exit 1
fi

# ========================================
# ШАГ 6: ПЕРЕЗАПУСК СЕРВИСОВ
# ========================================
echo ""
echo "================================================================"
log_step "ШАГ 6/6: Перезапуск сервисов"
echo "================================================================"

log_info "Останавливаем сервисы..."
systemctl stop albimusic-celery || true
systemctl stop albimusic-bot || true
systemctl stop albimusic-monitor || true

sleep 2

log_info "Запускаем Celery..."
systemctl start albimusic-celery

sleep 3

log_info "Запускаем бота..."
systemctl start albimusic-bot

sleep 2

log_info "Запускаем монитор..."
systemctl start albimusic-monitor

sleep 2

# ========================================
# ПРОВЕРКА СТАТУСА
# ========================================
echo ""
echo "================================================================"
log_step "ПРОВЕРКА СТАТУСА СЕРВИСОВ"
echo "================================================================"

for service in albimusic-celery albimusic-bot albimusic-monitor; do
    if systemctl is-active --quiet $service; then
        log_info "$service: РАБОТАЕТ"
    else
        log_error "$service: НЕ РАБОТАЕТ"
        systemctl status $service --no-pager -l
    fi
done

# ========================================
# ПРОВЕРКА КОНФИГУРАЦИИ CELERY
# ========================================
echo ""
echo "================================================================"
log_step "ПРОВЕРКА КОНФИГУРАЦИИ CELERY"
echo "================================================================"

log_info "Запускаем проверку конфигурации..."

python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, '/root/albimusic-bot')

try:
    from celery_tasks import celery_app
    
    print("\n📋 КОНФИГУРАЦИЯ CELERY:")
    print(f"   • App name: {celery_app.main}")
    print(f"   • Broker: {celery_app.conf.broker_url}")
    print(f"   • Backend: {celery_app.conf.result_backend}")
    print(f"   • Default queue: {celery_app.conf.task_default_queue}")
    
    if celery_app.conf.task_routes:
        print(f"   • Task routes: {celery_app.conf.task_routes}")
    else:
        print("   ⚠️  Task routes: None (это проблема!)")
    
    print("\n📋 ЗАРЕГИСТРИРОВАННЫЕ ЗАДАЧИ:")
    for task_name in sorted(celery_app.tasks.keys()):
        if not task_name.startswith('celery.'):
            print(f"   • {task_name}")
    
    print("\n✅ Конфигурация загружена успешно")
    
except Exception as e:
    print(f"\n❌ ОШИБКА загрузки конфигурации: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
ENDPYTHON

# ========================================
# ИТОГОВАЯ ИНФОРМАЦИЯ
# ========================================
echo ""
echo "================================================================"
echo -e "${GREEN}✅ КОМПЛЕКСНОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО${NC}"
echo "================================================================"
echo ""
echo "📋 ЧТО БЫЛО СДЕЛАНО:"
echo "   1. ✅ Созданы бэкапы всех файлов"
echo "   2. ✅ Восстановлен/создан celery_config.py"
echo "   3. ✅ Исправлен celery_tasks.py:"
echo "      - Добавлен импорт celery_config"
echo "      - Настроена загрузка конфигурации"
echo "      - Исправлена обработка ответов Suno API"
echo "      - Добавлено полное логирование"
echo "   4. ✅ Очищен Redis"
echo "   5. ✅ Перезапущены все сервисы"
echo ""
echo "📂 Бэкапы: $BACKUP_DIR"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Проверьте логи Celery:"
echo "   tail -f /var/log/albimusic-bot/celery/celery.log"
echo ""
echo "2. Отправьте тестовый запрос из бота"
echo ""
echo "3. Если возникнут ошибки, проверьте:"
echo "   • Логи бота: journalctl -u albimusic-bot -f"
echo "   • Логи монитора: journalctl -u albimusic-monitor -f"
echo "   • Redis: redis-cli monitor"
echo ""
echo "================================================================"

