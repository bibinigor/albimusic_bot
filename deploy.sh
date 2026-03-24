#!/bin/bash
echo "🚀 ЗАПУСК АВТОМАТИЧЕСКОГО ДЕПЛОЯ AlBi-music Bot"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции для красивого вывода
log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Проверяем что мы в правильной директории
if [ ! -f "main_with_payments.py" ]; then
    log_error "Не найден main_with_payments.py. Запускайте из папки проекта."
    exit 1
fi

log_info "1. Останавливаем текущую систему..."
sudo docker-compose down

log_info "2. Обновляем код из Git (если используется)..."
# git pull origin main  # Раскомментировать если используете Git

log_info "3. Собираем новый Docker образ..."
sudo docker build -t albimusic-bot:latest .

if [ $? -ne 0 ]; then
    log_error "Ошибка сборки Docker образа"
    exit 1
fi

log_info "4. Запускаем систему..."
sudo docker-compose up -d

log_info "5. Проверяем статус сервисов..."
sleep 5
sudo docker-compose ps

log_info "6. Проверяем логи основного бота..."
sudo docker logs albimusic-bot-primary --tail 3

log_info "7. Останавливаем backup бот (чтобы избежать конфликта)..."
sudo docker stop albimusic-bot-backup

log_info "8. Проверяем что primary бот работает..."
sudo docker logs albimusic-bot-primary --tail 2

log_info "🎉 ДЕПЛОЙ ЗАВЕРШЕН!"
echo ""
echo "📊 Статус системы:"
echo "   - Primary бот: $(sudo docker inspect -f '{{.State.Status}}' albimusic-bot-primary)"
echo "   - Backup бот:  $(sudo docker inspect -f '{{.State.Status}}' albimusic-bot-backup)" 
echo "   - Nginx:       $(sudo docker inspect -f '{{.State.Status}}' albimusic-nginx)"
echo ""
echo "🌐 Health check: curl http://localhost:8080/health"
