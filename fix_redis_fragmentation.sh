#!/bin/bash
echo "🧹 Исправляем фрагментацию Redis..."

# 1. Сохраняем дамп если нужно (опционально)
# redis-cli SAVE

# 2. Останавливаем Redis
sudo systemctl stop redis

# 3. Удаляем файл дампа чтобы запустить с чистой памятью
sudo rm -f /var/lib/redis/dump.rdb 2>/dev/null

# 4. Запускаем Redis
sudo systemctl start redis

# 5. Ждем и проверяем
sleep 3
echo "✅ Redis перезапущен. Новая фрагментация:"
redis-cli INFO memory | grep -E "used_memory:|mem_fragmentation_ratio:"

# 6. Перезапускаем Celery workers чтобы они переподключились
echo "🔄 Перезапускаем Celery workers..."
pkill -f "celery.*worker"
source venv/bin/activate
nohup celery -A celery_tasks.celery_app worker --pool=prefork --concurrency=2 > celery.log 2>&1 &

sleep 2
echo "✅ Celery workers запущены"
ps aux | grep "celery.*worker" | grep -v grep | wc -l
