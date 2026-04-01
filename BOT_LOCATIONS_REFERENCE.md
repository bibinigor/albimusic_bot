# 📍 Справочник расположения ботов ALBI Music

> **Используй этот файл при любой отладке** — здесь актуальные пути, сервисы и команды.

---

## 🤖 Telegram бот

| Параметр | Значение |
|---|---|
| **Основной файл** | `/root/albimusic-bot/main_with_payments.py` |
| **Конфигурация** | `/root/albimusic-bot/config.py` |
| **venv** | `/root/albimusic-bot/venv/` |
| **Сервис** | `albimusic-bot.service` |

```bash
# Управление
systemctl status albimusic-bot
systemctl restart albimusic-bot
systemctl stop albimusic-bot

# Логи (live)
journalctl -u albimusic-bot -f

# Найти ошибки
journalctl -u albimusic-bot -n 100 --no-pager | grep -i error
```

---

## 📱 ВКонтакте бот

| Параметр | Значение |
|---|---|
| **Основной файл** | `/root/albimusic-bot/main_vk.py` |
| **Клавиатуры** | `/root/albimusic-bot/vk_keyboards.py` |
| **Состояния** | `/root/albimusic-bot/vk_states.py` |
| **Конфигурация** | `/root/albimusic-bot/config.py` |
| **venv** | `/root/albimusic-bot/venv/` |
| **Сервис** | `albimusic-vk-bot.service` |

> ⚠️ **ВАЖНО:** VK-бот управляется через **systemd** (`albimusic-vk-bot.service`).
> **НЕ** запускай его вручную через `nohup python3 main_vk.py &` — это создаст второй экземпляр и бот будет отвечать дважды на каждое сообщение!

```bash
# Управление (ПРАВИЛЬНЫЙ способ)
systemctl status albimusic-vk-bot
systemctl restart albimusic-vk-bot
systemctl stop albimusic-vk-bot

# Логи (live)
journalctl -u albimusic-vk-bot -f

# Найти ошибки
journalctl -u albimusic-vk-bot -n 100 --no-pager | grep -i error

# Проверить что только ОДИН процесс запущен (должна быть 1 строка)
ps aux | grep main_vk.py | grep -v grep
```

---

## 🌐 Веб API (сайт albi-music.ru)

| Параметр | Значение |
|---|---|
| **Основной файл** | `/root/albimusic-bot/web_api.py` |
| **venv** | `/root/albimusic-bot/web_venv/` (отдельный!) |
| **Сервис** | `albimusic-web.service` |
| **Лог** | `/var/log/albimusic/web-api.log` |
| **Лог ошибок** | `/var/log/albimusic/web-api-error.log` |

```bash
# Управление
systemctl status albimusic-web
systemctl restart albimusic-web

# Логи
tail -f /var/log/albimusic/web-api.log
tail -f /var/log/albimusic/web-api-error.log
```

---

## ⚙️ Celery Workers (фоновая генерация музыки)

> Запущены **ДВА** celery-сервиса (оба работают параллельно):

### 1. `celery-worker.service`
```
celery -A celery_tasks worker -Q generation
```

### 2. `albimusic-celery.service`
```
celery -A celery_tasks.celery_app worker --pool=prefork --concurrency=8 -E -l info --task-events -Q generation
```

```bash
# Управление
systemctl status celery-worker
systemctl restart celery-worker

systemctl status albimusic-celery
systemctl restart albimusic-celery

# Логи
journalctl -u celery-worker -f
journalctl -u albimusic-celery -f

# Найти ошибки в celery
journalctl -u celery-worker --since "30 minutes ago" --no-pager | grep -iE "error|exception"
```

> ⚠️ При изменении `celery_tasks.py` — **перезапускать оба** celery-сервиса!

---

## 📡 Мониторинг

### Основной монитор уведомлений
| Параметр | Значение |
|---|---|
| **Файл** | `/root/albimusic-bot/run_monitor_notify.py` |
| **Сервис** | `albimusic-monitor.service` |

### Replicate монитор (изображения/видео)
| Параметр | Значение |
|---|---|
| **Файл** | `/root/albimusic-bot/monitor_replicate_tasks.py` |
| **Сервис** | `albimusic-replicate-monitor.service` |

```bash
systemctl status albimusic-monitor
systemctl restart albimusic-monitor

systemctl status albimusic-replicate-monitor
systemctl restart albimusic-replicate-monitor
```

---

## 🗄️ Инфраструктура

| Компонент | Сервис | Команда |
|---|---|---|
| PostgreSQL 14 | `postgresql@14-main.service` | `systemctl status postgresql@14-main` |
| Redis | `redis.service` | `systemctl status redis` |
| Nginx | `nginx.service` | `systemctl status nginx` |

---

## 🔍 Быстрая диагностика (скопируй и запусти)

```bash
# 1. Проверить все сервисы проекта
systemctl list-units --type=service | grep -E "(albi|celery|vk)"

# 2. Все Python-процессы проекта
ps aux | grep -E "(main_vk|main_with_payments|web_api|run_monitor|monitor_replicate|celery)" | grep -v grep

# 3. Проверить что VK-бот не задвоен (должна быть 1 строка)
ps aux | grep main_vk.py | grep -v grep | wc -l

# 4. Хвост логов всех сервисов
journalctl -u albimusic-vk-bot -u albimusic-bot -u albimusic-celery -u celery-worker -n 50 --no-pager
```

---

## ⚡ Быстрый перезапуск всего

```bash
# Telegram бот
systemctl restart albimusic-bot

# VK бот (ТОЛЬКО через systemd!)
systemctl restart albimusic-vk-bot

# Оба Celery worker-а
systemctl restart celery-worker && systemctl restart albimusic-celery

# Веб API
systemctl restart albimusic-web

# Мониторинг
systemctl restart albimusic-monitor && systemctl restart albimusic-replicate-monitor
```

---

## 📝 Важные замечания

1. **Telegram бот** (`albimusic-bot.service`) запускает `main_with_payments.py` — **не** `bot.py`!
2. **VK бот** (`albimusic-vk-bot.service`) запускает `main_vk.py` через systemd — **НЕ** запускать вручную!
3. **Веб API** использует **отдельный** venv: `/root/albimusic-bot/web_venv/` (не путать с `/root/albimusic-bot/venv/`)
4. **Celery** работает двумя сервисами одновременно (`celery-worker` + `albimusic-celery`) — оба нужны
5. При изменении `main_vk.py` → `systemctl restart albimusic-vk-bot`
6. При изменении `main_with_payments.py` → `systemctl restart albimusic-bot`
7. При изменении `celery_tasks.py` → `systemctl restart celery-worker && systemctl restart albimusic-celery`
8. При изменении `web_api.py` → `systemctl restart albimusic-web`
