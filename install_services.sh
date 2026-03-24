#!/bin/bash

# Установка и запуск Redis
echo "Installing Redis service..."
cat > redis.service << EOL
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/bin/redis-server /etc/redis/redis.conf
ExecStop=/usr/bin/redis-cli shutdown
Restart=always

[Install]
WantedBy=multi-user.target
EOL

sudo cp redis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable redis
sudo systemctl start redis

# Проверка статуса Redis
echo "Checking Redis status..."
sudo systemctl status redis

# Установка systemd сервиса для монитора
echo "Installing monitor service..."
sudo cp monitor-replicate.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable monitor-replicate
sudo systemctl start monitor-replicate

# Проверка статуса монитора
echo "Checking monitor service status..."
sudo systemctl status monitor-replicate

# Установка systemd сервиса для Celery
echo "Installing Celery worker service..."
cat > celery-worker.service << EOL
[Unit]
Description=Celery Worker Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/albimusic-bot
Environment=PYTHONPATH=/root/albimusic-bot
ExecStart=/usr/local/bin/celery -A celery_tasks worker -Q generation --loglevel=INFO
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

sudo cp celery-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl start celery-worker

# Проверка статуса Celery
echo "Checking Celery worker status..."
sudo systemctl status celery-worker

echo "Done! Both services should now be running."
echo "To check logs:"
echo "  Monitor: journalctl -u monitor-replicate -f"
echo "  Celery: journalctl -u celery-worker -f"