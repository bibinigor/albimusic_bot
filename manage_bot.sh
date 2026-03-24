#!/bin/bash

case "$1" in
    start)
        echo "🚀 Запуск AlBi Music Bot системы..."
        # Основной бот
        cd /root/albimusic-bot
        source venv/bin/activate
        nohup python3 main_with_payments.py > bot.log 2>&1 &
        # Мониторинг через systemd
        systemctl start albimusic-monitor.service
        echo "✅ Система запущена"
        ;;
    stop)
        echo "🛑 Остановка AlBi Music Bot системы..."
        pkill -f "python3 main_with_payments.py"
        systemctl stop albimusic-monitor.service
        echo "✅ Система остановлена"
        ;;
    status)
        echo "📊 Статус AlBi Music Bot системы:"
        echo "Основной бот:"
        pgrep -f "python3 main_with_payments.py" > /dev/null && echo "✅ Запущен" || echo "❌ Остановлен"
        echo "Мониторинг:"
        systemctl is-active albimusic-monitor.service > /dev/null && echo "✅ Запущен" || echo "❌ Остановлен"
        echo "Логи мониторинга:"
        journalctl -u albimusic-monitor.service -n 5 --no-pager
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    logs)
        echo "📋 Логи:"
        echo "1 - Основной бот"
        echo "2 - Мониторинг" 
        echo "3 - Celery"
        read -p "Выберите вариант: " choice
        case $choice in
            1) tail -f /root/albimusic-bot/bot.log ;;
            2) journalctl -u albimusic-monitor.service -f ;;
            3) tail -f /root/albimusic-bot/celery.log ;;
            *) echo "Неверный выбор" ;;
        esac
        ;;
    *)
        echo "Использование: $0 {start|stop|status|restart|logs}"
        echo "  start  - запуск всей системы"
        echo "  stop   - остановка всей системы" 
        echo "  status - статус системы"
        echo "  restart - перезапуск системы"
        echo "  logs   - просмотр логов"
        exit 1
        ;;
esac
