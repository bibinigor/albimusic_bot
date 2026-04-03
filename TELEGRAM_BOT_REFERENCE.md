# 📲 Справочник: Telegram-бот

> Давай этот файл AI в начале каждой сессии по Telegram-боту.

---

## 📍 Где бот

Telegram: **@AlBimusic_bot**
Ссылка: `https://t.me/AlBimusic_bot`
Канал с примерами: `@ALBImusic_Chart` (`https://t.me/ALBImusic_Chart`)

---

## 📁 Ключевые файлы

| Что | Путь |
|-----|------|
| **Основной файл** | `/root/albimusic-bot/main_with_payments.py` |
| **Конфиг** | `/root/albimusic-bot/config.py` |
| **Celery задачи** | `/root/albimusic-bot/celery_tasks.py` |
| **БД утилиты** | `/root/albimusic-bot/db_utils.py` |
| **Демо-система** | `/root/albimusic-bot/demo_system.py` |
| **Мониторинг** | `/root/albimusic-bot/run_monitor_notify.py` |
| **Replicate монитор** | `/root/albimusic-bot/handlers/monitor_replicate_tasks.py` |
| **Image handler** | `/root/albimusic-bot/handlers/image_handler.py` |
| **Photo/Video handler** | `/root/albimusic-bot/handlers/photo_video_handler.py` |
| **Python venv** | `/root/albimusic-bot/venv/` (общий с VK-ботом) |

> ⚠️ **НЕ** `bot.py` — основной файл именно `main_with_payments.py`!

---

## ⚙️ Сервисы

| Сервис | Файл | Описание |
|--------|------|----------|
| `albimusic-bot.service` | `main_with_payments.py` | Основной Telegram-бот |
| `albimusic-monitor.service` | `run_monitor_notify.py` | Монитор уведомлений |
| `albimusic-replicate-monitor.service` | `monitor_replicate_tasks.py` | Монитор Replicate (изображения/видео) |
| `celery-worker.service` | `celery_tasks.py` | Celery worker #1 |
| `albimusic-celery.service` | `celery_tasks.py` | Celery worker #2 |

```bash
# Основной бот
systemctl status albimusic-bot
systemctl restart albimusic-bot
systemctl stop albimusic-bot

# Логи
journalctl -u albimusic-bot -f
journalctl -u albimusic-bot -n 100 --no-pager
journalctl -u albimusic-bot -n 100 --no-pager | grep -i error

# Мониторинг
systemctl status albimusic-monitor
systemctl restart albimusic-monitor

systemctl status albimusic-replicate-monitor
systemctl restart albimusic-replicate-monitor
```

---

## 🔑 Конфигурация (`config.py`)

| Параметр | Значение |
|----------|----------|
| `BOT_TOKEN` | `<см. config.py>` |
| `SUNO_API_KEY` | `<см. config.py>` |
| `SUNO_API_URL` | `https://api.sunoapi.org` |
| `DB_NAME` | `albimusic_bot` |
| `DB_USER` | `albimusic_user` |
| `DB_PASSWORD` | `<см. config.py>` |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `YOOKASSA_SHOP_ID` | `<см. config.py>` |
| `YOOKASSA_RETURN_URL` | `https://albi-music.ru/payment_success` |
| `REPLICATE_API_TOKEN` | `<см. config.py>` |

---

## 🏗️ Архитектура

```
Telegram → main_with_payments.py → Celery Tasks → Suno API
                   │                      │            │
                   ↓                      ↓            ↓
              PostgreSQL           Фоновая работа   Музыка
              (users, gen.)        (celery_tasks.py)
                   │
                   ↓
            run_monitor_notify.py  ← следит за готовностью треков
            monitor_replicate_tasks.py ← следит за изображениями
```

---

## ⚙️ Celery Workers

> Запущены **ДВА** celery-сервиса одновременно — оба нужны!

```bash
# Управление
systemctl status celery-worker
systemctl restart celery-worker

systemctl status albimusic-celery
systemctl restart albimusic-celery

# Логи Celery
journalctl -u celery-worker -f
journalctl -u albimusic-celery -f

# Ошибки в Celery
journalctl -u celery-worker --since "30 minutes ago" --no-pager | grep -iE "error|exception"
```

> ⚠️ При изменении `celery_tasks.py` **перезапускать ОБА** worker-а!

---

## 🗄️ База данных (PostgreSQL 14)

```bash
# Статус
systemctl status postgresql@14-main

# Подключение
psql -U albimusic_user -d albimusic_bot

# Полезные запросы
SELECT count(*) FROM users;
SELECT count(*) FROM generations WHERE status = 'pending';
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
```

Таблицы:
- `users` — пользователи (user_id, username, first_name, balance, invited_by, created_at)
- `generations` — история генераций (task_id, user_id, prompt, audio_url, status, created_at)
- `payments` — платежи YooKassa
- `referrals` — реферальная программа
- `demo_tracks` — демо-треки

---

## 🔧 Инфраструктура

| Компонент | Сервис | Команда проверки |
|-----------|--------|------------------|
| PostgreSQL 14 | `postgresql@14-main.service` | `systemctl status postgresql@14-main` |
| Redis | `redis.service` | `systemctl status redis` |
| Nginx | `nginx.service` | `systemctl status nginx` |
| RabbitMQ | `rabbitmq-server.service` | `systemctl status rabbitmq-server` |

---

## 🔍 Быстрая диагностика

```bash
# Все сервисы проекта
systemctl list-units --type=service | grep -E "(albi|celery)"

# Все Python-процессы проекта
ps aux | grep -E "(main_with_payments|web_api|run_monitor|monitor_replicate|celery)" | grep -v grep

# Проверка Redis
redis-cli ping

# Проверка PostgreSQL
pg_isready -U albimusic_user -d albimusic_bot

# Хвост всех логов вместе
journalctl -u albimusic-bot -u albimusic-celery -u celery-worker -n 50 --no-pager
```

---

## ⚡ Быстрый перезапуск всего

```bash
# Telegram бот
systemctl restart albimusic-bot

# Оба Celery worker-а
systemctl restart celery-worker && systemctl restart albimusic-celery

# Мониторинг
systemctl restart albimusic-monitor && systemctl restart albimusic-replicate-monitor
```

---

## 📝 Правило после изменений

| Что изменил | Что сделать |
|-------------|-------------|
| `main_with_payments.py` | `systemctl restart albimusic-bot` |
| `config.py` | `systemctl restart albimusic-bot` + все остальные сервисы |
| `celery_tasks.py` | `systemctl restart celery-worker && systemctl restart albimusic-celery` |
| `db_utils.py` | `systemctl restart albimusic-bot` |
| `run_monitor_notify.py` | `systemctl restart albimusic-monitor` |
| `handlers/monitor_replicate_tasks.py` | `systemctl restart albimusic-replicate-monitor` |
