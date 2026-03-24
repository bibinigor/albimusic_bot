#!/bin/bash
echo "🔍 Мониторинг состояния ботов..."

while true; do
    PRIMARY_STATUS=$(sudo docker inspect -f '{{.State.Status}}' albimusic-bot-primary 2>/dev/null)
    BACKUP_STATUS=$(sudo docker inspect -f '{{.State.Status}}' albimusic-bot-backup 2>/dev/null)
    
    # Если основной бот не работает, а резервный работает но в ошибке
    if [ "$PRIMARY_STATUS" != "running" ] && [ "$BACKUP_STATUS" = "running" ]; then
        echo "🔄 Основной бот не работает, перезапускаем резервный..."
        sudo docker restart albimusic-bot-backup
    fi
    
    sleep 30
done
