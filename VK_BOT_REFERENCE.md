# 📱 Справочник: Бот ВКонтакте

> Давай этот файл AI в начале каждой сессии по VK-боту.

---

## 📍 Где бот

VK-группа ID: **235442407**
Ссылка на группу: `https://vk.com/club235442407`

---

## 📁 Ключевые файлы

| Что | Путь |
|-----|------|
| **Основной файл** | `/root/albimusic-bot/main_vk.py` |
| **Конфиг VK** | `/root/albimusic-bot/vk_config.py` |
| **Конфиг общий** | `/root/albimusic-bot/config.py` |
| **Клавиатуры** | `/root/albimusic-bot/vk_keyboards.py` |
| **Состояния FSM** | `/root/albimusic-bot/vk_states.py` |
| **Поддержка** | `/root/albimusic-bot/vk_support.py` |
| **Демо-система** | `/root/albimusic-bot/vk_demo_system.py` |
| **Python venv** | `/root/albimusic-bot/venv/` (общий с Telegram) |

---

## ⚙️ Сервис

| Параметр | Значение |
|----------|----------|
| **Systemd сервис** | `albimusic-vk-bot.service` |
| **Запуск через** | Long Polling (NOT webhook) |

```bash
# ✅ ПРАВИЛЬНОЕ управление (только через systemd!)
systemctl status albimusic-vk-bot
systemctl restart albimusic-vk-bot
systemctl stop albimusic-vk-bot
systemctl start albimusic-vk-bot

# Логи live
journalctl -u albimusic-vk-bot -f

# Последние 100 строк логов
journalctl -u albimusic-vk-bot -n 100 --no-pager

# Только ошибки
journalctl -u albimusic-vk-bot -n 100 --no-pager | grep -i error
```

## ⚠️ КРИТИЧЕСКИ ВАЖНО!

> **НИКОГДА** не запускай VK-бота вручную через `python3 main_vk.py` или `nohup python3 ...`!
> Это создаст ВТОРОЙ экземпляр — бот будет отвечать ДВАЖДЫ на каждое сообщение.
> Только через `systemctl restart albimusic-vk-bot`.

**Проверка что запущен только ОДИН экземпляр (должна быть ровно 1 строка):**
```bash
ps aux | grep main_vk.py | grep -v grep | wc -l
```

---

## 🔑 Конфигурация (`vk_config.py`)

| Параметр | Значение |
|----------|----------|
| `VK_TOKEN` | Long-poll токен группы: `vk1.a.pNU9...` |
| `VK_GROUP_ID` | `235442407` |
| `ADMIN_VK_ID` | `57725952` |
| `ADMIN_IDS` | `[57725952]` |
| `YOOKASSA_SHOP_ID` | `<см. vk_config.py>` |

---

## 🔑 Конфигурация (`config.py`, общая)

| Параметр | Значение |
|----------|----------|
| `VK_APP_ID` | `54451761` (для OAuth веб-бота) |
| `DB_NAME` | `albimusic_bot` |
| `DB_USER` | `albimusic_user` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `SUNO_API_URL` | `https://api.sunoapi.org` |

---

## 🏗️ Архитектура

```
VK Long Poll → main_vk.py → Celery Tasks → Suno API
                   │                           │
                   ↓                           ↓
              PostgreSQL               Генерация музыки
              (сохранение)             (фоновые работ.)
                   │
                   ↓
              vk_states.py (FSM состояния пользователя)
              vk_keyboards.py (клавиатуры)
```

**Импортируемые модули:**
- `vk_states.py` — `States`, `VKStateManager` — FSM состояния диалога
- `vk_keyboards.py` — клавиатуры VK
- `vk_support.py` — функции поддержки
- `vk_demo_system.py` — демо-треки (45 сек)
- `db_utils.py` — работа с PostgreSQL
- `celery_tasks.py` — фоновая генерация

---

## 🗄️ База данных

Общая с Telegram-ботом и веб-ботом. PostgreSQL:
- `albimusic_bot` база
- `users` — баланс, реферальная программа
- `generations` — история треков

---

## 🔧 Связанные сервисы (при изменении `celery_tasks.py`)

```bash
# Перезапускать оба Celery worker-а!
systemctl restart celery-worker && systemctl restart albimusic-celery
```

---

## 🔍 Быстрая диагностика

```bash
# Все процессы VK-бота
ps aux | grep main_vk.py | grep -v grep

# Проверить что НЕ задвоен (должна быть 1)
ps aux | grep main_vk.py | grep -v grep | wc -l

# Последние ошибки
journalctl -u albimusic-vk-bot --since "30 minutes ago" --no-pager | grep -iE "error|exception|traceback"

# Статус Redis (нужен для FSM состояний)
systemctl status redis

# Статус Celery (нужен для генерации)
systemctl status celery-worker
systemctl status albimusic-celery
```

---

## 📝 Правило после изменений

| Что изменил | Что сделать |
|-------------|-------------|
| `main_vk.py` | `systemctl restart albimusic-vk-bot` |
| `vk_config.py` | `systemctl restart albimusic-vk-bot` |
| `vk_keyboards.py` | `systemctl restart albimusic-vk-bot` |
| `vk_states.py` | `systemctl restart albimusic-vk-bot` |
| `celery_tasks.py` | `systemctl restart celery-worker && systemctl restart albimusic-celery` |
| `db_utils.py` | `systemctl restart albimusic-vk-bot` |
