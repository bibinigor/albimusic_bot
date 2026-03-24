# ТЕКУЩАЯ КОНФИГУРАЦИЯ AlBi-music Bot

## АРХИТЕКТУРА:
- Бот: aiogram + FastAPI
- БД: PostgreSQL (albimusic_bot)
- Очередь: Redis + Celery
- API: Suno API

## ЗАПУЩЕННЫЕ ПРОЦЕССЫ:
1. Основной бот: python3 main_with_payments.py
2. Celery worker: celery -A celery_tasks.celery_app worker
3. Мониторинг: python3 run_monitor_notify.py

## БАЗЫ ДАННЫХ:
- PostgreSQL: albimusic_bot (пользователь: albimusic_user)
- Redis: localhost:6379

## API КЛЮЧИ:
- Telegram: @AlBimusic_bot
- Suno API: 615290cfecdf58e6251835ba7971ab65

## ИЗВЕСТНЫЕ ПРОБЛЕМЫ:
- ❌ Функция add_user использует SQLite вместо PostgreSQL (ИСПРАВЛЕНО)
- ❌ Ошибка статистики из-за проблем с БД

## КОМАНДЫ УПРАВЛЕНИЯ:
pkill -f "python3 main_with_payments.py" - остановить бота
pkill -f "celery.*worker" - остановить Celery
