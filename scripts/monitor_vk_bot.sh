#!/bin/bash

# Скрипт мониторинга и обслуживания VK бота

# Функция для проверки статуса сервиса
check_service() {
    local service_name=$1
    echo "🔍 Проверка статуса $service_name..."
    if systemctl is-active --quiet $service_name; then
        echo "✅ Сервис $service_name активен"
        return 0
    else
        echo "❌ Сервис $service_name не активен"
        return 1
    fi
}

# Функция для проверки использования диска
check_disk_usage() {
    echo "💾 Проверка использования диска..."
    usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $usage -gt 90 ]; then
        echo "⚠️ Внимание! Диск заполнен на $usage%"
        echo "Очистка старых логов..."
        find /var/log -name "*.gz" -mtime +7 -delete
    else
        echo "✅ Использование диска: $usage%"
    fi
}

# Функция для проверки Redis
check_redis() {
    echo "📊 Проверка Redis..."
    if redis-cli ping > /dev/null; then
        echo "✅ Redis работает"
        # Очистка устаревших ключей состояний (старше 24 часов)
        redis-cli --scan --pattern "vk:*:state" | while read key; do
            ttl=$(redis-cli ttl "$key")
            if [ $ttl -eq -1 ]; then
                redis-cli expire "$key" 86400
            fi
        done
    else
        echo "❌ Redis не отвечает"
    fi
}

# Функция для проверки логов на ошибки
check_logs() {
    echo "📝 Проверка логов на ошибки..."
    errors=$(journalctl -u vk-albimusic-bot -n 100 | grep -i "error" | wc -l)
    if [ $errors -gt 0 ]; then
        echo "⚠️ Найдено $errors ошибок в логах"
        echo "Последние ошибки:"
        journalctl -u vk-albimusic-bot -n 100 | grep -i "error" | tail -5
    else
        echo "✅ Ошибок не найдено"
    fi
}

# Функция для проверки нагрузки на CPU
check_cpu_load() {
    echo "🔄 Проверка нагрузки на CPU..."
    load=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1)
    load=${load//./}
    if [ $load -gt 400 ]; then
        echo "⚠️ Высокая нагрузка на CPU: $load"
    else
        echo "✅ Нагрузка на CPU в норме: $load"
    fi
}

# Основной блок мониторинга
echo "🔍 Начало проверки системы..."
echo "Время: $(date)"
echo "-------------------"

check_service "vk-albimusic-bot"
bot_status=$?

check_service "vk-albimusic-celery"
celery_status=$?

check_redis
check_disk_usage
check_logs
check_cpu_load

echo "-------------------"

# Если есть проблемы, предлагаем перезапуск
if [ $bot_status -eq 1 ] || [ $celery_status -eq 1 ]; then
    echo "⚠️ Обнаружены проблемы с сервисами. Перезапустить? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        echo "🔄 Перезапуск сервисов..."
        sudo systemctl restart vk-albimusic-bot
        sudo systemctl restart vk-albimusic-celery
        echo "✅ Сервисы перезапущены"
    fi
fi

echo "✅ Проверка завершена"