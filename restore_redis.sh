#!/bin/bash
echo "🔄 Восстанавливаем Redis..."

# 1. Останавливаем все
sudo systemctl stop redis-server 2>/dev/null || true
sudo pkill redis-server 2>/dev/null || true

# 2. Удаляем проблемную версию
sudo apt-get remove -y redis

# 3. Устанавливаем стабильную версию из официального Ubuntu
sudo apt-get install -y redis-server

# 4. Восстанавливаем нашу конфигурацию
sudo cp /etc/redis/redis.conf.backup* /etc/redis/redis.conf 2>/dev/null || echo "Используем дефолтную конфигурацию"

# 5. Настраиваем память
sudo sed -i 's/^# maxmemory .*/maxmemory 1024mb/' /etc/redis/redis.conf
sudo sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
echo "maxmemory 1024mb" | sudo tee -a /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" | sudo tee -a /etc/redis/redis.conf

# 6. Запускаем
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 7. Проверяем
sleep 3
sudo systemctl status redis-server --no-pager
redis-cli ping
