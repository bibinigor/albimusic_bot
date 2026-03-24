#!/bin/bash
echo "🔧 Настраиваем аллокатор Redis..."

# 1. Останавливаем Redis
sudo systemctl stop redis

# 2. Меняем настройки аллокатора в конфигурации
sudo sed -i 's/^# maxmemory-samples .*/maxmemory-samples 10/' /etc/redis/redis.conf
sudo sed -i 's/^# hash-max-ziplist-entries .*/hash-max-ziplist-entries 512/' /etc/redis/redis.conf
sudo sed -i 's/^# hash-max-ziplist-value .*/hash-max-ziplist-value 64/' /etc/redis/redis.conf

# 3. Включаем активную дефрагментацию (аккуратно)
sudo sed -i 's/^activedefrag .*/activedefrag yes/' /etc/redis/redis.conf
echo "active-defrag-ignore-bytes 100mb" | sudo tee -a /etc/redis/redis.conf
echo "active-defrag-threshold-lower 10" | sudo tee -a /etc/redis/redis.conf
echo "active-defrag-threshold-upper 100" | sudo tee -a /etc/redis/redis.conf

# 4. Запускаем Redis
sudo systemctl start redis

# 5. Ждем и проверяем
sleep 5
echo "✅ Redis перезапущен с новыми настройками:"
redis-cli INFO memory | grep -E "used_memory:|mem_fragmentation_ratio:|active_defrag"

# 6. Запускаем дефрагментацию вручную
redis-cli MEMORY PURGE 2>/dev/null && echo "🧹 Ручная дефрагментация выполнена"

sleep 2
echo "📊 Финальная статистика:"
redis-cli INFO memory | grep -E "used_memory:|mem_fragmentation_ratio:"
