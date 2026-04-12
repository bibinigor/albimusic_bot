# 📖 TG_BOT_REFERENCE — Справочник Telegram-бота ALBI Music

> **Читай этот файл в начале каждой новой сессии**, чтобы сразу знать структуру проекта.
> Файл: `/root/albimusic-bot/TG_BOT_REFERENCE.md`

---

## 🤖 Что за бот

**ALBI Music** — Telegram-бот для генерации музыки через Suno AI.
- Бот: `@AlBimusic_bot`
- Пользователи оплачивают токены, тратят 1 токен на 2 трека (генерация).
- Есть демо-режим (60 сек обрезка), разблокировка за токен, каверы, минусовки, WAV.

---

## 📁 Ключевые файлы проекта (`/root/albimusic-bot/`)

| Файл | Назначение |
|------|-----------|
| `main_with_payments.py` | **Главный файл бота** — все хендлеры Telegram, FSM, callback-кнопки, оплата |
| `run_monitor_notify.py` | **Монитор** — следит за завершёнными генерациями в БД и отправляет уведомления пользователям |
| `celery_tasks.py` | **Celery-задачи** — вся логика вызова Suno API, polling результата, сохранение в БД |
| `db_utils.py` | Утилиты работы с PostgreSQL (пул соединений, `execute_query_sync`) |
| `config.py` | Конфиг: `BOT_TOKEN`, `SUNO_API_KEY`, `SUNO_API_URL`, `ADMIN_ID`, `DATABASE_URL` |
| `celery_config.py` | Настройки Celery (broker, backend — Redis) |
| `handlers/image_handler.py` | Обработчик генерации обложек (Replicate API) |
| `handlers/photo_video_handler.py` | Обработчик загрузки фото/видео |
| `handlers/monitor_replicate_tasks.py` | Мониторинг задач Replicate |

---

## ⚙️ systemd-сервисы

| Сервис | Файл сервиса | Что делает |
|--------|-------------|-----------|
| `albimusic-bot.service` | `/etc/systemd/system/albimusic-bot.service` | Запускает `main_with_payments.py` — основной Telegram-бот |
| `albimusic-monitor.service` | `/etc/systemd/system/albimusic-monitor.service` | Запускает `run_monitor_notify.py` — монитор уведомлений |
| `albimusic-celery.service` | `/etc/systemd/system/albimusic-celery.service` | Запускает Celery-воркер (`celery_tasks.py`) |
| `albimusic-web.service` | `/etc/systemd/system/albimusic-web.service` | Web API (`web_api.py`, порт 8001) |
| `albimusic-vk-bot.service` | `/etc/systemd/system/albimusic-vk-bot.service` | VK-бот (`main_vk.py`) |
| `nginx.service` | системный | HTTPS-прокси, порты 80/443 |

### Команды управления
```bash
# Перезапуск после правок кода
systemctl restart albimusic-bot
systemctl restart albimusic-monitor
systemctl restart albimusic-celery

# Статус
systemctl status albimusic-bot --no-pager -l
systemctl status albimusic-monitor --no-pager -l

# Логи в реальном времени
journalctl -u albimusic-bot -f
journalctl -u albimusic-monitor -f
journalctl -u albimusic-celery -f

# Логи ошибок монитора
tail -f /var/log/albimusic/monitor-error.log
```

---

## 🌐 Сеть и прокси

> ⚠️ **КРИТИЧНО:** Без прокси бот не может подключиться к `api.telegram.org`.
> Сервер заблокирован по IPv4/IPv6 для Telegram. Всегда используй SOCKS5 через Tor.

### Как устроен прокси

| Параметр | Значение |
|----------|---------|
| **Тип** | SOCKS5 через **Tor** |
| **Адрес** | `socks5://127.0.0.1:9050` |
| **Сервис Tor** | `tor.service` (systemd) |
| **Порт** | `9050` (стандартный Tor SOCKS5) |

### Проверка и управление прокси
```bash
# Проверить, работает ли Tor
systemctl status tor

# Если Tor упал — перезапустить
systemctl restart tor

# Проверить, слушает ли порт 9050
ss -tlnp | grep 9050

# Проверить связь с Telegram через прокси
curl --socks5-hostname 127.0.0.1:9050 https://api.telegram.org
```

### Как использовать прокси в коде

**В aiogram (bot instance):**
```python
from aiogram import Bot
bot = Bot(token=BOT_TOKEN, proxy='socks5://127.0.0.1:9050')
```

**В aiohttp сессии (если нужен HTTP-запрос через прокси):**
```python
import aiohttp
from aiohttp_socks import ProxyConnector
connector = ProxyConnector.from_url('socks5://127.0.0.1:9050')
async with aiohttp.ClientSession(connector=connector) as session:
    async with session.get('https://api.telegram.org/...') as resp:
        ...
```

**Файлы, где используется прокси:**
- `main_with_payments.py` — основной бот (`Bot(token=..., proxy='socks5://...')`)
- `run_monitor_notify.py` — функция `create_bot_ipv4()` → все Telegram-отправки
- `send_apology_10_04.py`, `send_apology_11_04.py` — скрипты рассылки

### Типичные ошибки прокси
| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Cannot connect to host api.telegram.org` | Tor не запущен или порт 9050 недоступен | `systemctl restart tor` |
| `Connection refused 127.0.0.1:9050` | Tor не запущен | `systemctl start tor` |
| `Unclosed connector` в логах | Aiogram v2 предупреждение (не ошибка) | Игнорировать |

---

## 🗄️ База данных PostgreSQL

Подключение через `DATABASE_URL` в `config.py`. Утилиты в `db_utils.py`.

### Основные таблицы

| Таблица | Описание |
|---------|---------|
| `users` | Пользователи: `user_id`, `username`, `first_name`, `balance`, `active_generations`, `novice_offer_sent`, `novice_offer_pending_at`, `novice_window_started_at`, `novice_gens_bought` |
| `generations` | Задачи генерации: `task_id`, `user_id`, `prompt`, `status`, `audio_url`, `suno_task_id`, `suno_audio_id`, `created_at` |
| `demo_tracks` | Готовые треки с URL: `task_id`, `user_id`, `full_url_1`, `full_url_2`, `is_unlocked` |
| `token_transactions` | История транзакций токенов: `user_id`, `amount`, `transaction_type`, `description` |
| `payments` | Платежи: `user_id`, `status`, `amount` |
| `referrals` | Рефералы: `referrer_id`, `referred_id`, `bonus_applied` |

### Важные статусы `generations.status`
| Статус | Значение |
|--------|---------|
| `processing` | Celery-задача запущена, ожидаем Suno |
| `completed` | Генерация успешна, `audio_url` — реальная ссылка или `ALREADY_SENT_[url]` |
| `error` | Ошибка генерации |

### Важные значения `generations.audio_url`
| Значение | Значение |
|----------|---------|
| `ALREADY_SENT_[url]` | Трек доставлен пользователю, оригинальный URL сохранён после префикса |
| `ALREADY_NOTIFIED_[url]` | Уведомление об ошибке отправлено |
| `ERROR_NOTIFIED` | ⚠️ Старый баг: монитор не смог отправить и перезаписал URL. Трек потерян. |

---

## 🔄 Архитектура потока генерации

```
Пользователь → main_with_payments.py
  └─ Списывает 1 токен
  └─ Создаёт запись generations (status='processing')
  └─ Запускает celery task (generate_music_task / generate_song_task)
       └─ celery_tasks.py → Suno API polling (до 15 мин)
       └─ При успехе: обновляет generations (status='completed', audio_url=URL)
       └─ При ошибке: обновляет generations (status='error')

run_monitor_notify.py (цикл каждые 10 сек)
  └─ Ищет completed генерации с audio_url NOT LIKE 'ALREADY_SENT_%'
  └─ Отправляет демо (60 сек) или полный трек через Telegram
  └─ Помечает: audio_url = 'ALREADY_SENT_' + original_url
  └─ Ищет processing > 3 мин → отправляет "ещё генерируется" (1 раз)
  └─ Проверяет офферы «Новичок» (через 3 мин после 1-й песни)
```

---

## 💰 Логика токенов

- **1 токен = 1 генерация = 2 трека (2 версии)**
- Покупки: 5 ген за 99₽, 10 за 490₽, 25 за 990₽, 60 за 1990₽, 140 за 3990₽
- При ошибке Suno: токен возвращается через `SELECT refund_tokens(user_id, task_id, ...)`
- Реферальный бонус: +2 токена пригласившему при первой генерации друга

---

## 🎁 Воронка монетизации новичка (добавлено 12.04.2026)

| Этап | Что происходит |
|------|---------------|
| `/start` — новый пользователь | Получает 1 токен в подарок |
| Первая генерация | Монитор выдаёт **45-сек демо** (не полный трек) |
| Хочет полную версию | Кнопка **«🔓 Разблокировать за 29₽»** (активна 24 ч) |
| В течение 24 ч | Пакет «Подарок новичку»: **29₽/генерация**, до **10 штук** |
| По истечении 24 ч | Стандартный магазин: 99₽ за 5 ген, 490₽ за 10 и т.д. |

### Новые поля в таблице `users`
| Поле | Тип | Описание |
|------|-----|---------|
| `novice_window_started_at` | TIMESTAMP | Когда началось 24-ч окно (при первой генерации) |
| `novice_gens_bought` | INT | Сколько новичковых генераций уже куплено (лимит 10) |

### Новые callback_data и payment_type
| callback / payment_type | Что делает |
|------------------------|-----------|
| `pay_unlock_29_TASKID` | Создаёт платёж 29₽ для разблокировки первого трека |
| `pay_29_novice` | Создаёт платёж 29₽ за 1 новичковую генерацию |
| `payment_type='novice_gen'` | Вебхук: +1 токен, инкремент `novice_gens_bought` |

### Функции
- `get_novice_status(user_id)` → `(is_active, hours_left, gens_bought)` — проверка 24-ч окна
- `get_balance_keyboard(user_id)` — теперь показывает кнопку новичка если окно активно
- `send_no_tokens_message(...)` — теперь показывает кнопку 29₽ вместо стандартного оффера если окно активно

### Добавление колонок в БД (уже выполнено)
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_window_started_at TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_gens_bought INT DEFAULT 0;
```
*(albimusic_user не имеет прав ALTER TABLE — выполнять от postgres)*

---

## 🛠️ Скрипты обслуживания

| Скрипт | Назначение |
|--------|-----------|
| `refund_tokens_10_04.py` | Рефанд жертвам бага ERROR_NOTIFIED 10.04.2026 |
| `send_apology_10_04.py` | Рассылка извинений жертвам бага 10.04.2026 |
| `refund_tokens_11_04.py` | Рефанд пострадавшим 10–11.04.2026 (Оля, unbrokensociety2280, Fack63827) |
| `send_apology_11_04.py` | Рассылка извинений пострадавшим 10–11.04.2026 |

**Шаблон нового скрипта рефанда:**
```python
# Поиск по username:
execute_query_sync("SELECT user_id, balance FROM users WHERE LOWER(username) = LOWER(%s)", (uname,))
# Начисление:
execute_query_sync("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, uid))
# Транзакция:
execute_query_sync("INSERT INTO token_transactions (user_id, amount, transaction_type, description) VALUES (%s, %s, 'credit', %s)", (uid, amount, desc))
```

**Шаблон отправки сообщения пользователю:**
```python
from aiogram import Bot
bot = Bot(token=BOT_TOKEN, proxy='socks5://127.0.0.1:9050')
await bot.send_message(chat_id=user_id, text="...")
await bot.close()
```

---

## 🐛 История известных багов

### Баг ERROR_NOTIFIED (10.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователи не получают готовые треки, при этом токены списаны.
**Причина:** Монитор не мог подключиться к Telegram (сеть), при ошибке перезаписывал `audio_url = 'ERROR_NOTIFIED'` и `status = 'error'`, уничтожая ссылку на трек.
**Исправление (`run_monitor_notify.py`, строки ~832-840):** При ошибке отправки теперь задача удаляется из `sent_notifications` → монитор повторит попытку. URL и статус не перезаписываются.

### Баг «Нет треков» в «Мои треки» (11.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователь открывает «Мои треки» и видит пустой список, хотя генерации были.
**Причина:** Запрос искал только `status='completed'` в `generations`. Треки, испорченные багом ERROR_NOTIFIED (`status='error'`), не отображались.
**Исправление (`main_with_payments.py`, функция `handle_my_tracks`):** Добавлен `LEFT JOIN demo_tracks` — треки показываются, если запись есть в `demo_tracks`, даже при `status='error'`.

### Баг «Долгая генерация без обратной связи» (10–11.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователь ждёт 6+ минут и не понимает, что происходит.
**Причина:** Не было промежуточных уведомлений при долгой генерации.
**Исправление (`run_monitor_notify.py`, функция `check_long_running_generations`):** Если `status='processing'` > 3 минут — автоматически отправляется уведомление «⏳ трек ещё создаётся» (один раз).

---

## 📞 Поддержка и контакты

- Канал бота: `@ALBImusic_Chart`
- Логи ошибок: `/var/log/albimusic/monitor-error.log`
- Конфиг nginx: `/root/albimusic-bot/nginx_vk_bot.conf`

---

*Последнее обновление: 12.04.2026 — добавлена воронка монетизации новичка: первая песня бесплатно, разблокировка 29₽, пакет «Подарок новичку» 29₽/ген до 10 шт., 24-часовое окно.*
