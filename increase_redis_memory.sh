#!/bin/bash
echo "🔄 Увеличиваем Redis память до 1GB..."

# Останавливаем Redis
sudo systemctl stop redis

# Увеличиваем maxmemory в конфигурации
sudo sed -i 's/^maxmemory .*/maxmemory 1024mb/' /etc/redis/redis.conf
sudo sed -i 's/^maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Запускаем Redis
sudo systemctl start redis

# Проверяем настройки
sleep 2
echo "✅ Новые настройки Redis:"
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET maxmemory-policy
redis-cli INFO memory | grep -E "used_memory:|maxmemory:|mem_fragmentation_ratio:"

# Проверяем статус
sudo systemctl status redis --no-pager | head -10
