#!/bin/bash
# Скрипт автоматического тестирования интеграции VK-бота
# Проверяет все критические компоненты перед запуском

set -e  # Прерывать при ошибках

echo "=========================================="
echo "🧪 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ VK-БОТА"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Счетчики
PASSED=0
FAILED=0

# Функция для вывода результата теста
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        FAILED=$((FAILED + 1))
    fi
}

# 1. Проверка Python и зависимостей
echo "1️⃣ Проверка Python и зависимостей..."
python3 --version > /dev/null 2>&1
test_result $? "Python 3 установлен"

python3 -c "import vk_api" > /dev/null 2>&1
test_result $? "Модуль vk_api"

python3 -c "import psycopg2" > /dev/null 2>&1
test_result $? "Модуль psycopg2"

python3 -c "import redis" > /dev/null 2>&1
test_result $? "Модуль redis"

python3 -c "import flask" > /dev/null 2>&1
test_result $? "Модуль flask"

python3 -c "import yookassa" > /dev/null 2>&1
test_result $? "Модуль yookassa"

echo ""

# 2. Проверка файлов проекта
echo "2️⃣ Проверка файлов проекта..."

FILES=(
    "main_vk.py"
    "vk_demo_system.py"
    "vk_referral_system.py"
    "vk_admin.py"
    "vk_file_upload.py"
    "vk_payments.py"
    "vk_states_broadcast.py"
    "config.py"
    "webhook_server.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        test_result 0 "Файл $file существует"
    else
        test_result 1 "Файл $file НЕ НАЙДЕН"
    fi
done

echo ""

# 3. Проверка синтаксиса Python
echo "3️⃣ Проверка синтаксиса Python..."

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        python3 -m py_compile "$file" > /dev/null 2>&1
        test_result $? "Синтаксис $file"
    fi
done

echo ""

# 4. Проверка импортов модулей
echo "4️⃣ Проверка импортов модулей..."

python3 -c "from vk_demo_system import create_demo_track, unlock_demo_track" > /dev/null 2>&1
test_result $? "Импорт vk_demo_system"

python3 -c "from vk_referral_system import add_referral, get_referral_progress" > /dev/null 2>&1
test_result $? "Импорт vk_referral_system"

python3 -c "from vk_admin import get_admin_stats, send_broadcast" > /dev/null 2>&1
test_result $? "Импорт vk_admin"

python3 -c "from vk_file_upload import handle_audio_upload, validate_audio_file" > /dev/null 2>&1
test_result $? "Импорт vk_file_upload"

python3 -c "from vk_payments import create_payment, process_payment_callback" > /dev/null 2>&1
test_result $? "Импорт vk_payments"

python3 -c "from vk_states_broadcast import BroadcastStates" > /dev/null 2>&1
test_result $? "Импорт vk_states_broadcast"

echo ""

# 5. Проверка БД
echo "5️⃣ Проверка базы данных..."

python3 -c "
from config import DB_CONFIG
import psycopg2

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Проверка таблиц
    tables = ['users', 'generations', 'demo_tracks', 'referrals', 'payments']
    for table in tables:
        cur.execute(f\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')\")
        exists = cur.fetchone()[0]
        if not exists:
            raise Exception(f'Таблица {table} не существует')
    
    # Проверка поля status в generations
    cur.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name='generations' AND column_name='status'\")
    if not cur.fetchone():
        raise Exception('Поле status в generations не существует')
    
    cur.close()
    conn.close()
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
" > /dev/null 2>&1

test_result $? "Подключение к БД и проверка таблиц"

echo ""

# 6. Проверка Redis
echo "6️⃣ Проверка Redis..."

redis-cli ping > /dev/null 2>&1
test_result $? "Redis доступен"

echo ""

# 7. Проверка конфигурации
echo "7️⃣ Проверка конфигурации..."

python3 -c "
from config import *

required_vars = [
    ('VK_TOKEN', VK_TOKEN),
    ('VK_GROUP_ID', VK_GROUP_ID),
    ('YOOKASSA_SHOP_ID', YOOKASSA_SHOP_ID),
    ('YOOKASSA_SECRET_KEY', YOOKASSA_SECRET_KEY),
    ('SUNO_API_KEY', SUNO_API_KEY),
]

for var_name, var_value in required_vars:
    if not var_value or var_value.startswith('YOUR_'):
        print(f'ERROR: {var_name} не настроен')
        exit(1)

print('OK')
" > /dev/null 2>&1

test_result $? "Все критические переменные настроены"

echo ""

# 8. Проверка миграций
echo "8️⃣ Проверка миграций БД..."

python3 -c "
from config import DB_CONFIG
import psycopg2

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Проверка поля status
cur.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name='generations' AND column_name='status'\")
if not cur.fetchone():
    print('ERROR: Миграция 001 не применена')
    exit(1)

# Проверка таблицы demo_tracks
cur.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'demo_tracks')\")
if not cur.fetchone()[0]:
    print('ERROR: Миграция 002 не применена')
    exit(1)

# Проверка таблицы referrals
cur.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'referrals')\")
if not cur.fetchone()[0]:
    print('ERROR: Миграция 003 не применена')
    exit(1)

cur.close()
conn.close()
print('OK')
" > /dev/null 2>&1

test_result $? "Все миграции применены (001, 002, 003)"

echo ""

# 9. Проверка webhook сервера (опционально)
echo "9️⃣ Проверка webhook сервера..."

if pgrep -f "webhook_server.py" > /dev/null; then
    test_result 0 "Webhook сервер запущен"
    
    # Проверка health endpoint
    curl -s http://localhost:8080/health > /dev/null 2>&1
    test_result $? "Health endpoint доступен"
else
    echo -e "${YELLOW}⚠️  SKIP${NC}: Webhook сервер не запущен (опционально)"
fi

echo ""

# 10. Проверка процесса бота
echo "🔟 Проверка процесса VK-бота..."

if pgrep -f "main_vk.py" > /dev/null; then
    test_result 0 "VK-бот запущен"
else
    echo -e "${YELLOW}⚠️  INFO${NC}: VK-бот не запущен (будет запущен позже)"
fi

echo ""

# Итоговый результат
echo "=========================================="
echo "📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ"
echo "=========================================="
echo -e "Пройдено: ${GREEN}$PASSED${NC}"
echo -e "Провалено: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!${NC}"
    echo ""
    echo "🚀 Готов к запуску:"
    echo "   nohup python3 main_vk.py > vk_bot.log 2>&1 &"
    echo "   nohup python3 webhook_server.py > webhook.log 2>&1 &"
    exit 0
else
    echo -e "${RED}❌ ЕСТЬ ОШИБКИ! Исправьте перед запуском.${NC}"
    exit 1
fi
