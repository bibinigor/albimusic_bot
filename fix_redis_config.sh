#!/bin/bash
# Исправляем конфигурацию Redis

# 1. Останавливаем Redis
sudo systemctl stop redis

# 2. Резервное копирование текущей конфигурации
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup.$(date +%Y%m%d)

# 3. Находим и заменяем настройки памяти в конфигурации
sudo sed -i 's/^maxmemory .*/maxmemory 256mb/' /etc/redis/redis.conf
sudo sed -i 's/^maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
sudo sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# 4. Добавляем настройки если их нет
grep -q "^maxmemory " /etc/redis/redis.conf || echo "maxmemory 256mb" | sudo tee -a /etc/redis/redis.conf
grep -q "^maxmemory-policy " /etc/redis/redis.conf || echo "maxmemory-policy allkeys-lru" | sudo tee -a /etc/redis/redis.conf

# 5. Запускаем Redis
sudo systemctl start redis
sudo systemctl status redis --no-pager

echo "✅ Конфигурация Redis исправлена:"
echo "   maxmemory: 256mb"
echo "   maxmemory-policy: allkeys-lru"
