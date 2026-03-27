#!/bin/bash

# Скрипт развертывания VK версии ALBImusic бота

echo "🚀 Начинаем развертывание VK бота..."

# Проверяем наличие необходимых утилит
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 не установлен"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "❌ Pip3 не установлен"; exit 1; }
command -v redis-cli >/dev/null 2>&1 || { echo "❌ Redis не установлен"; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "❌ PostgreSQL не установлен"; exit 1; }

# Создаем виртуальное окружение
echo "🔧 Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден"
    echo "Создайте файл .env с необходимыми переменными окружения"
    exit 1
fi

# Применяем миграции БД
echo "🗄️ Применяем миграции БД..."
source .env
psql $POSTGRES_URI -f migrations/add_vk_id_column.sql

# Создаем systemd сервисы
echo "⚙️ Настраиваем systemd сервисы..."

# Сервис для VK бота
cat > /etc/systemd/system/vk-albimusic-bot.service << EOL
[Unit]
Description=VK ALBImusic Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PYTHONPATH=$(pwd)
ExecStart=$(pwd)/venv/bin/python main_vk.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Сервис для Celery
cat > /etc/systemd/system/vk-albimusic-celery.service << EOL
[Unit]
Description=VK ALBImusic Celery Worker
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PYTHONPATH=$(pwd)
ExecStart=$(pwd)/venv/bin/celery -A celery_tasks worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Перезагружаем systemd и запускаем сервисы
echo "🔄 Запускаем сервисы..."
sudo systemctl daemon-reload
sudo systemctl enable vk-albimusic-bot
sudo systemctl enable vk-albimusic-celery
sudo systemctl start vk-albimusic-bot
sudo systemctl start vk-albimusic-celery

echo "✅ Развертывание завершено!"
echo "📝 Проверьте логи командами:"
echo "sudo journalctl -u vk-albimusic-bot -f"
echo "sudo journalctl -u vk-albimusic-celery -f"