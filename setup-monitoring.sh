#!/bin/bash
echo "📊 Настройка системы мониторинга..."

# Создаем директорию для логов
mkdir -p logs

# Создаем скрипт мониторинга состояния ботов
cat > monitor-bots.sh << 'MONEOF'
#!/bin/bash
while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    PRIMARY_STATUS=$(docker inspect -f '{{.State.Status}}' albimusic-bot-primary 2>/dev/null || echo "not_found")
    BACKUP_STATUS=$(docker inspect -f '{{.State.Status}}' albimusic-bot-backup 2>/dev/null || echo "not_found")
    
    echo "[$TIMESTAMP] Primary: $PRIMARY_STATUS, Backup: $BACKUP_STATUS" >> logs/bot-status.log
    
    # Если primary не работает, а backup не запущен - запускаем backup
    if [ "$PRIMARY_STATUS" != "running" ] && [ "$BACKUP_STATUS" != "running" ]; then
        echo "[$TIMESTAMP] 🔄 Primary не работает, запускаем Backup..." >> logs/bot-status.log
        docker start albimusic-bot-backup 2>/dev/null || true
    fi
    
    sleep 30
done
MONEOF

chmod +x monitor-bots.sh

echo "✅ Система мониторинга настроена"
echo "🚀 Запуск мониторинга: ./monitor-bots.sh"
