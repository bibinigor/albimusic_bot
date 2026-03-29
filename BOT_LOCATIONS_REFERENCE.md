# 📍 Справочник расположения ботов ALBI Music

## 🤖 Telegram бот
**Основной файл:** `/root/albimusic-bot/bot.py`
**Конфигурация:** `/root/albimusic-bot/config.py`
**Сервис:** `albimusic-bot.service`
```bash
# Управление
systemctl status albimusic-bot
systemctl restart albimusic-bot
systemctl stop albimusic-bot
systemctl start albimusic-bot

# Логи
journalctl -u albimusic-bot -f
```

## 📱 ВКонтакте бот
**Основной файл:** `/root/albimusic-bot/main_vk.py`
**Конфигурация:** `/root/albimusic-bot/vk_config.py`
**Клавиатуры:** `/root/albimusic-bot/vk_keyboards.py`
**Состояния:** `/root/albimusic-bot/vk_states.py`
**Процесс:** Запускается как python процесс (не systemd сервис)
```bash
# Проверка статуса
ps aux | grep main_vk.py | grep -v grep

# Остановка
kill $(ps aux | grep main_vk.py | grep -v grep | awk '{print $2}')

# Запуск
cd /root/albimusic-bot && nohup python3 main_vk.py > /dev/null 2>&1 &
```

## 🌐 Веб-сайт
**HTML:** `/var/www/albimusic-web/index.html`
**CSS:** `/var/www/albimusic-web/style.css`
**Проект HTML:** `/root/albimusic-bot/website/index.html`
**Сервис:** `albimusic-web.service`
```bash
# Управление
systemctl status albimusic-web
systemctl restart albimusic-web
```

## 🔧 Общие компоненты (используются всеми ботами)

### Celery Worker
**Основной файл:** `/root/albimusic-bot/celery_tasks.py`
**Конфигурация:** `/root/albimusic-bot/celery_config.py`
**Сервисы:**
- `celery-worker.service` (основной)
- `albimusic-celery.service` (дополнительный)

```bash
# Управление
systemctl restart celery-worker
systemctl status celery-worker
systemctl restart albimusic-celery

# Логи
journalctl -u celery-worker -f
journalctl -u albimusic-celery -f
```

### База данных
**Утилиты:** `/root/albimusic-bot/db_utils.py`
**Миграции:** `/root/albimusic-bot/migrations/`
**Конфигурация:** В `/root/albimusic-bot/config.py`

### Мониторинг
**Файл:** `/root/albimusic-bot/run_monitor_notify.py`
**Сервис:** `albimusic-monitor.service`
```bash
# Управление
systemctl status albimusic-monitor
systemctl restart albimusic-monitor
```

### Replicate Monitor
**Сервис:** `albimusic-replicate-monitor.service`
```bash
systemctl status albimusic-replicate-monitor
```

## 📋 Быстрый рестарт всех сервисов
```bash
# Перезапуск всех основных компонентов
systemctl restart celery-worker
systemctl restart albimusic-celery
systemctl restart albimusic-monitor
systemctl restart albimusic-bot

# Перезапуск ВК бота
kill $(ps aux | grep main_vk.py | grep -v grep | awk '{print $2}')
sleep 2
cd /root/albimusic-bot && nohup python3 main_vk.py > /dev/null 2>&1 &
```

## 🔍 Полезные команды для диагностики

### Посмотреть все запущенные сервисы проекта
```bash
systemctl list-units --type=service | grep -E "(vk|celery|albi)"
```

### Посмотреть все Python процессы проекта
```bash
ps aux | grep -E "(main_vk|bot.py|celery)" | grep -v grep
```

### Проверить логи Celery за последние 30 минут
```bash
journalctl -u celery-worker --since "30 minutes ago" --no-pager
```

### Найти ошибки в логах
```bash
journalctl -u celery-worker -n 100 --no-pager | grep -i error
journalctl -u albimusic-bot -n 100 --no-pager | grep -i error
```

## 📝 Важные замечания

1. **ВК бот** не работает как systemd сервис - это обычный Python процесс
2. **Telegram бот** работает как systemd сервис `albimusic-bot.service`
3. **Celery** используется обоими ботами для фоновых задач генерации
4. **Веб-версия** использует те же `celery_tasks.py` для генерации музыки
5. При изменении `celery_tasks.py` нужно перезапускать celery-worker
6. При изменении `main_vk.py` нужно перезапускать процесс ВК бота
7. При изменении `bot.py` нужно перезапускать albimusic-bot.service
