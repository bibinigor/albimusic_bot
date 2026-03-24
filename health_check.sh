#!/bin/bash
# Health check для AlBi-music бота

LOG_FILE="/var/log/albimusic/health_check.log"
MAX_RESTARTS=3
RESTART_FILE="/tmp/albimusic_restart_count"

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Инициализация счетчика перезапусков
if [ ! -f "$RESTART_FILE" ]; then
    echo "0" > "$RESTART_FILE"
fi
RESTART_COUNT=$(cat "$RESTART_FILE")

# Проверяем, запущен ли бот через systemd
if ! systemctl is-active --quiet albimusic-bot.service; then
    log "❌ Бот не активен (systemd)"
    
    if [ "$RESTART_COUNT" -lt "$MAX_RESTARTS" ]; then
        log "🔄 Попытка перезапуска ($((RESTART_COUNT + 1))/$MAX_RESTARTS)..."
        systemctl restart albimusic-bot.service
        sleep 10
        
        if systemctl is-active --quiet albimusic-bot.service; then
            log "✅ Бот успешно перезапущен"
            echo "0" > "$RESTART_FILE"
        else
            NEW_COUNT=$((RESTART_COUNT + 1))
            echo "$NEW_COUNT" > "$RESTART_FILE"
            log "⚠️  Не удалось перезапустить бот (попытка $NEW_COUNT/$MAX_RESTARTS)"
        fi
    else
        log "🚨 Достигнут лимит перезапусков ($MAX_RESTARTS). Требуется ручное вмешательство!"
        # Можно добавить уведомление в Telegram
    fi
    exit 1
fi

# Бот активен, проверяем PID
BOT_PID=$(systemctl show albimusic-bot.service --property=MainPID | cut -d= -f2)

if [ "$BOT_PID" -eq 0 ]; then
    log "⚠️  Бот активен, но PID=0 (странно)"
    exit 0
fi

# Проверяем, отвечает ли процесс
if ! kill -0 "$BOT_PID" 2>/dev/null; then
    log "⚠️  Процесс бота ($BOT_PID) не отвечает, но systemd считает его активным"
    # Перезапускаем
    systemctl restart albimusic-bot.service
    echo "1" > "$RESTART_FILE"
    exit 1
fi

# Проверяем логи на наличие критических ошибок (за последние 10 минут)
ERROR_COUNT=$(tail -200 /var/log/albimusic/bot-error.log 2>/dev/null | grep -c "ERROR\|CRITICAL\|Traceback\|Exception")

if [ "$ERROR_COUNT" -gt 10 ]; then
    log "⚠️  Много ошибок в логах ($ERROR_COUNT). Возможна проблема."
    # Если много ошибок - мягкий перезапуск
    if [ "$RESTART_COUNT" -lt "$MAX_RESTARTS" ]; then
        log "🔄 Мягкий перезапуск из-за ошибок в логах..."
        systemctl restart albimusic-bot.service
        NEW_COUNT=$((RESTART_COUNT + 1))
        echo "$NEW_COUNT" > "$RESTART_FILE"
    fi
fi

# Все в порядке
log "✅ Бот работает нормально (PID: $BOT_PID, ошибок: $ERROR_COUNT)"
echo "0" > "$RESTART_FILE"  # Сбрасываем счетчик при успешной проверке
exit 0
