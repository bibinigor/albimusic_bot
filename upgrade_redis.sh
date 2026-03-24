#!/bin/bash
echo "🚀 Обновляем Redis до последней версии..."

# 1. Останавливаем Redis и удаляем старый
sudo systemctl stop redis
sudo apt-get remove -y redis-server

# 2. Устанавливаем репозиторий Redis официальный
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# 3. Обновляем и устанавливаем Redis 7+
sudo apt-get update
sudo apt-get install -y redis

# 4. Копируем нашу конфигурацию
sudo cp /etc/redis/redis.conf.backup* /etc/redis/redis.conf 2>/dev/null || true
sudo sed -i 's/^maxmemory .*/maxmemory 1024mb/' /etc/redis/redis.conf
sudo sed -i 's/^maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# 5. Запускаем
sudo systemctl start redis
sudo systemctl enable redis

# 6. Проверяем
sleep 3
echo "✅ Redis обновлен:"
redis-cli INFO server | grep "redis_version:"
redis-cli INFO memory | grep -E "used_memory:|mem_fragmentation_ratio:"
