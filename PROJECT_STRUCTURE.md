# 🎵 AlBi Music Bot - Структура проекта

## 🚀 ОСНОВНЫЕ ФАЙЛЫ:

### 🤖 Основной бот
- `final_bot.py` - Главный Telegram бот с полным функционалом
- `main_with_payments.py` - Резервная версия бота

### 🔧 Системные модули
- `celery_tasks.py` - Фоновые задачи генерации музыки
- `celery_config.py` - Конфигурация Celery
- `config.py` - Настройки приложения

### 💾 Базы данных
- `database_adapter.py` - Адаптер для работы с БД
- `postgres_db.py` - PostgreSQL подключение
- `redis_cache.py` - Redis кеширование
- `create_postgres_tables.sql` - Схема БД

### 💰 Платежи
- `payments.py` - Логика балансов и платежей

### 📊 Мониторинг
- `run_monitor_pro.py` - Автономный мониторинг завершенных задач

### 🛠 Утилиты
- `manage_bot.sh` - Скрипт управления всей системой
- `start_celery_worker.sh` - Запуск Celery воркера

## 📁 ДИРЕКТОРИИ:
- `backups/old_versions/` - Архив старых версий файлов
- `venv/` - Виртуальное окружение Python
- `documents/` - Документация
- `website/` - Веб-сайт

## 🎯 КОМАНДЫ УПРАВЛЕНИЯ:
```bash
./manage_bot.sh start    # Запуск всей системы
./manage_bot.sh stop     # Остановка системы
./manage_bot.sh status   # Статус компонентов
./manage_bot.sh logs     # Просмотр логов
cd ~/albimusic-bot

# 1. Останавливаем старый Celery воркер
pkill -f "celery worker"
sleep 3

# 2. Запускаем новый воркер с исправленным кодом
source venv/bin/activate
nohup celery -A celery_tasks.celery_app worker --queues=generation --loglevel=info --concurrency=1 > celery.log 2>&1 &

echo "✅ Celery перезапущен с исправленным кодом"

# 3. Проверяем что воркер запустился
sleep 5
ps aux | grep "celery worker"

# 4. Тестируем - создаем тестовую задачу
python3 << 'EOF'
from celery_tasks import generate_music_task

result = generate_music_task.delay(338544009, "Тест после перезапуска Celery")
print(f"✅ Тестовая задача запущена: {result.id}")
print("Ждем завершения и уведомления...")
