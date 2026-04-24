# 📖 TG_BOT_REFERENCE — Справочник Telegram-бота ALBI Music

> **Читай этот файл в начале каждой новой сессии**, чтобы сразу знать структуру проекта.
> Файл: `/root/albimusic-bot/TG_BOT_REFERENCE.md`

---

## 🤖 Что за бот

**ALBI Music** — Telegram-бот для генерации музыки через Suno AI.
- Бот: `@AlBimusic_bot`
- Пользователи оплачивают токены, тратят 1 токен на 2 трека (генерация).
- Есть демо-режим (60 сек обрезка с offset=30 сек, чтобы попасть в припев), разблокировка за токен, каверы, минусовки, WAV.

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
| `users` | Пользователи: `user_id`, `username`, `first_name`, `balance`, `active_generations`, `novice_offer_sent`, `novice_offer_pending_at`, `novice_window_started_at`, `novice_gens_bought`, `is_blocked` |
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
| Первая генерация | Монитор выдаёт **60-сек демо** (offset 30 сек — попадает в припев, не полный трек) |
| Хочет полную версию | Кнопка **«🔓 Разблокировать за 39₽»** (активна 24 ч) |
| В течение 24 ч | Пакет «Подарок новичку»: **39₽/генерация**, до **10 штук** |
| По истечении 24 ч | Стандартный магазин: 99₽ за 5 ген, 490₽ за 10 и т.д. |

### Новые поля в таблице `users`
| Поле | Тип | Описание |
|------|-----|---------|
| `novice_window_started_at` | TIMESTAMP | Когда началось 24-ч окно (при первой генерации) |
| `novice_gens_bought` | INT | Сколько новичковых генераций уже куплено (лимит 10) |

### Новые callback_data и payment_type
| callback / payment_type | Что делает |
|------------------------|-----------|
| `pay_unlock_29_TASKID` | Создаёт платёж 39₽ для разблокировки первого трека (название callback историческое, 29 — старая цена) |
| `pay_29_novice` | Создаёт платёж 39₽ за 1 новичковую генерацию (название callback историческое) |
| `payment_type='novice_gen'` | Вебхук: +1 токен, инкремент `novice_gens_bought` |

### Функции
- `get_novice_status(user_id)` → `(is_active, hours_left, gens_bought)` — проверка 24-ч окна
- `get_balance_keyboard(user_id)` — теперь показывает кнопку новичка если окно активно
- `send_no_tokens_message(...)` — теперь показывает кнопку 39₽ вместо стандартного оффера если окно активно

### Добавление колонок в БД (уже выполнено)
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_window_started_at TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_gens_bought INT DEFAULT 0;
```
*(albimusic_user не имеет прав ALTER TABLE — выполнять от postgres)*

---

## 🚫 Система автоматической блокировки (добавлено 16.04.2026)

Пользователи, заблокировавшие бота, помечаются флагом `is_blocked = TRUE` в таблице `users`.
Монитор и бот перестают их обрабатывать. Если пользователь разблокирует бота и напишет `/start` — флаг сбрасывается автоматически.

### Колонка в БД
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_users_is_blocked ON users(is_blocked) WHERE is_blocked = TRUE;
```

### Как работает
| Событие | Действие |
|---------|---------|
| `Forbidden: bot was blocked by the user` в любом хендлере монитора | `UPDATE users SET is_blocked = TRUE WHERE user_id = %s` |
| Пользователь пишет `/start` | `UPDATE users SET is_blocked = FALSE WHERE user_id = %s AND is_blocked = TRUE` |

### Где вызывается `mark_user_blocked(user_id)` (`run_monitor_notify.py`)
- `send_telegram_notification` — outer except (Forbidden при отправке демо/полного трека)
- `send_telegram_notification` — except внутри is_first_generation (Forbidden при кнопке 39₽)
- `send_error_notification` — except (Forbidden при уведомлении об ошибке)
- `send_novice_offer` — except (Forbidden при оффере «Новичок»)
- `check_long_running_generations` — except (Forbidden при «трек ещё создаётся»)

### SQL-запросы монитора фильтруют заблокированных
Все 3 ключевых запроса применяют условие `AND (u.is_blocked IS NULL OR u.is_blocked = FALSE)`:
- Главный цикл `monitor_generations` → `SELECT ... FROM generations g LEFT JOIN users u`
- `check_long_running_generations` → `SELECT ... FROM generations g LEFT JOIN users u`
- `check_and_send_novice_offers` → `SELECT ... FROM users WHERE ... AND (is_blocked IS NULL OR is_blocked = FALSE)`

### Запрос для просмотра заблокировавших пользователей
```sql
SELECT user_id, username, first_name, balance FROM users WHERE is_blocked = TRUE ORDER BY user_id;
```

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

### Баг «Неизвестный тариф» при оплате 39₽ (14.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователь-новичок нажимает кнопку «🎁 НОВИЧОК: ещё песня — 39₽» (или «🔓 Разблокировать за 39₽») и получает «❌ Неизвестный тариф».
**Причина:** Общий обработчик `process_payment` (декоратор `startswith('pay_')`) перехватывал callback `pay_29_novice` и `pay_unlock_29_TASKID` раньше их собственных хендлеров, так как был зарегистрирован выше по коду. В словаре `payment_data` этих ключей нет → ошибка.
**Исправление (`main_with_payments.py`, строка ~2060):** Декоратор обновлён — явно исключает `pay_29_novice` и `pay_unlock_29_*`:
```python
@dp.callback_query_handler(lambda c: c.data.startswith('pay_') and c.data != 'pay_29_novice' and not c.data.startswith('pay_unlock_29_'))
```
**Рефанды:** Скрипт `refund_apology_14_04.py` — Сашe (@issaevva_s, id=7936045749) +1 токен за ERROR_NOTIFIED + извинения; Ольге (id=8495598008) +1 токен компенсации за недоступность оплаты + извинения.

> ⚠️ **Правило:** При добавлении новых `pay_*` кнопок с отдельными хендлерами — ВСЕГДА добавлять исключение в декоратор `process_payment` ИЛИ переносить их регистрацию ВЫШЕ строки ~2060.

---

## 📞 Поддержка и контакты

- Канал бота: `@ALBImusic_Chart`
- Логи ошибок: `/var/log/albimusic/monitor-error.log`
- Конфиг nginx: `/root/albimusic-bot/nginx_vk_bot.conf`

---

### Баг «Бесконечный цикл монитора для заблокировавших бота» (16.04.2026 — ИСПРАВЛЕН)
**Симптом:** Монитор спамил в логи `Forbidden: bot was blocked by the user` каждые 10 секунд для одних и тех же пользователей. Влиял на производительность мониторинга.
**Причина 1 (первая генерация):** В ветке `is_first_generation` функции `send_telegram_notification` вызов `bot.send_message(... keyboard с кнопкой 39₽)` не был обёрнут в `try/except`. При `Forbidden` исключение уходило выше, `task_id` не добавлялся в `sent_notifications`, монитор пробовал снова через 10 сек.
**Исправление 1 (`run_monitor_notify.py`, строки ~410-430):** Вызов `bot.send_message` с кнопкой разблокировки обёрнут в `try/except` — при ошибке логируется и функция возвращает `True`, т.е. основной цикл помечает `ALREADY_SENT_`.
**Причина 2 (оффер «Новичок»):** Функция `send_novice_offer` при `Forbidden` возвращала `False` без установки `novice_offer_sent = TRUE`. Пользователи с заблокированным ботом повторно обрабатывались каждые 10 секунд.
**Исправление 2 (`run_monitor_notify.py`, строки ~719-733):** В `except`-блоке `send_novice_offer` при `Forbidden`/`ChatNotFound`/`UserDeactivated` устанавливается `novice_offer_sent = TRUE, novice_offer_pending_at = NULL`.
**Дополнительно:** 7 зависших записей `generations` (пользователи заблокировали бота) помечены вручную как `ALREADY_SENT_` напрямую в БД.

### Почему нет платежей 39₽ (анализ 16.04.2026)
**Вывод:** Код 39₽-воронки работает корректно. 238 пользователей имеют активное новичковое окно (`novice_window_started_at` установлен). Платежей нет по причине **конверсии**: пользователи видят кнопку 39₽/1 песня и кнопку 99₽/5 песен — и выбирают второе (20₽/песня дешевле 39₽/песня). Это **UX/ценообразование**, не код.

### Баг «Оплатили, но полную версию не получили» (16.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователь нажимает «🔓 Получить ПОЛНУЮ версию — 39₽», оплачивает, `is_unlocked = TRUE` в БД проставляется, но треки в Telegram не приходят. Пользователь может получить «🎉 Оплата прошла! Отправляю...», но треков нет.
**Причина:** `asyncio.create_task(_send_unlocked_first_gen())` создаёт фоновую задачу. Если внутри неё возникает любое исключение (сеть, Tor, Telegram API) — оно **молча поглощается** без логирования и без уведомления пользователя/админа. Пользователь остаётся без треков.
**Исправление (`main_with_payments.py`, строки ~1011–1115):**
1. **Fallback при ошибке `send_audio`** — если аудио-файл не отправляется, URL отправляется текстом.
2. **Fallback при пустом `demo_data`** — если записи нет в `demo_tracks`, ищем URL в таблице `generations`.
3. **Уведомление admin (`ADMIN_ID`)** — при любом сбое доставки треков admin получает сообщение с user_id и task_id для ручной отправки.
4. **Аварийное уведомление пользователю** — при сбое пользователь получает «⚠️ Произошла техническая ошибка...» вместо тишины.
5. **`add_done_callback` на task** — необработанные исключения asyncio-задачи теперь логируются.
**Пострадавшие:** Маша @wuwmuww (user_id=1065246196) — треки отправлены вручную скриптом `send_unlock_16_04_wuwmuww.py`.

> ⚠️ **Правило:** Любой `asyncio.create_task()` с отправкой треков/сообщений ОБЯЗАН:
> 1. Иметь fallback (URL текстом если send_audio упал)
> 2. Уведомлять ADMIN_ID при сбое
> 3. Иметь `add_done_callback` для логирования исключений task

---

### Баг «Автоматический рефанд токенов не работал при ошибках Suno» (16.04.2026 — ИСПРАВЛЕН)
**Симптом:** При ошибке генерации Suno (`GENERATE_AUDIO_FAILED`, errorCode 500) токены не возвращались пользователям автоматически. В логах Celery: `❌ Не удалось вернуть токен user XXX: column "updated_at" of relation "users" does not exist`.
**Причина:** SQL-функция `public.refund_tokens` в БД содержала строку `updated_at = CURRENT_TIMESTAMP` в UPDATE к таблице `users`, но колонки `updated_at` в таблице `users` не существует.
**Исправление:** Пересоздана функция `refund_tokens` в PostgreSQL — убрана строка `updated_at = CURRENT_TIMESTAMP`:
```sql
CREATE OR REPLACE FUNCTION public.refund_tokens(p_user_id bigint, p_amount integer, p_reason text)
 RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    UPDATE users SET balance = balance + p_amount WHERE user_id = p_user_id;
    INSERT INTO token_transactions (user_id, amount, transaction_type, description)
    VALUES (p_user_id, p_amount, 'refund', p_reason);
    PERFORM finish_generation(p_user_id);
END;
$$;
```
**Пострадавшие:** @darkname032 (user_id=8711018526) — возвращён 1 токен вручную.

---

---

### Инцидент «Массовые ошибки генерации из-за исчерпания токенов Suno» (18.04.2026 — УСТРАНЁН ВРУЧНУЮ)
**Симптом:** Генерации завершались с `status='error'` и `audio_url='ERROR_NOTIFIED'`. Пользователи получали уведомление об ошибке через ~8 минут после запуска (таймаут polling Suno).
**Причина:** Закончились кредиты Suno API на аккаунте. Suno возвращала `GENERATE_AUDIO_FAILED`. Автоматический рефанд через `refund_tokens()` не срабатывал (или не вызывался при данном типе ошибки).
**Пострадавшие:** 20 пользователей, суммарно 29 ошибочных генераций (01:00–10:00 мск 18.04.2026).
**Устранение:**
1. Пополнены кредиты Suno API — генерации начали работать.
2. Массовый рефанд токенов через SQL (по числу ошибочных генераций на пользователя).
3. Рассылка извинений через `send_apology_18_04.py` — 16/20 доставлено, 4 заблокировали бота.
4. Заблокировавшие помечены `is_blocked = TRUE`: Margot_14 (7128441496), salievasss (1392337147), YABOOKY_JO (7955523182), 1314286101.

> ⚠️ **Правило:** При `GENERATE_AUDIO_FAILED` от Suno — проверить баланс Suno API (`get_suno_balance.py`). Добавить мониторинг баланса Suno и алерт администратору при достижении порога (<50 кредитов).

---

### Баг «SENSITIVE_WORD_ERROR — бесконечный polling» (18.04.2026 — ИСПРАВЛЕН)
**Симптом:** Генерация не завершается 8–15 минут, пользователь ждёт до таймаута. Suno сразу возвращает `SENSITIVE_WORD_ERROR` (запрещённые слова в промпте), но polling не прерывается.
**Причина:** В polling loop [`celery_tasks.py`](celery_tasks.py) строка ~649 — список финальных ошибок не включал `SENSITIVE_WORD_ERROR`:
```python
# ДО (баг):
elif status in ('ERROR', 'GENERATE_AUDIO_FAILED', 'GENERATE_FAILED', 'FAILED'):
# ПОСЛЕ (исправлено):
elif status in ('ERROR', 'GENERATE_AUDIO_FAILED', 'GENERATE_FAILED', 'FAILED', 'SENSITIVE_WORD_ERROR'):
```
**Исправление:** Добавлен `SENSITIVE_WORD_ERROR` в список — задача теперь немедленно завершается с ошибкой вместо ожидания 15-минутного таймаута. Celery перезапущен.
**Пострадавший:** Igor_Bibin (338544009) — возвращён 1 токен (баланс 17).

> ⚠️ **Правило:** При получении любого нового статуса от Suno (не SUCCESS/PENDING/TEXT_SUCCESS/FIRST_SUCCESS) — добавлять в список финальных ошибок, чтобы polling немедленно завершался.

*Последнее обновление: 18.04.2026 — исправлен баг SENSITIVE_WORD_ERROR (бесконечный polling), инцидент с исчерпанием токенов Suno (рефанд 20 пользователям).*

---

### Баг «NameError: BOT_TOKEN + Timeout context manager» при разблокировке и оплате (21.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователи оплачивают разблокировку трека (39₽) или покупают novice_gen/пакет токенов — деньги списываются, `is_unlocked = TRUE` в БД, но полный трек и/или уведомление об оплате **не приходят**.
**Ошибки в логах:**
```
🔴 asyncio task _send_unlocked_first_gen завершилась с исключением: name 'BOT_TOKEN' is not defined
  File "main_with_payments.py", line 1053, in _send_unlocked_first_gen
    _local_bot = _Bot(token=BOT_TOKEN, ...)
❌ Ошибка уведомления novice_gen XXXXX: Timeout context manager should be used inside a task
❌ Не удалось отправить уведомление пользователю XXXXX: Timeout context manager should be used inside a task
```
**Причина 1 (`_send_unlocked_first_gen`):** Функция-корутина определена внутри webhook-хендлера. При запуске через `asyncio.create_task()` имя `BOT_TOKEN` не находится — оно является глобальной переменной модуля, но в контексте asyncio-задачи, созданной внутри вложенной функции, поиск по имени нестабилен. Решение: захватить значение через default-аргумент при определении функции.
**Причина 2 (`_notify_novice_gen`, `_notify_payment`):** Использование глобального экземпляра `bot` внутри `asyncio.create_task()` — aiohttp-сессия бота создана вне контекста задачи → `Timeout context manager should be used inside a task`.
**Исправление (`main_with_payments.py`):**
1. `_send_unlocked_first_gen` — добавлен параметр `_token=BOT_TOKEN` (захват при определении), внутри используется `_token` вместо `BOT_TOKEN`.
2. `_notify_novice_gen` — добавлен параметр `_token=BOT_TOKEN`, внутри создаётся локальный `_Bot` и вызывается `await _nb.close()` в `finally`.
3. `_notify_payment` — добавлен параметр `_token=BOT_TOKEN`, внутри создаётся локальный `_Bot` и вызывается `await _pb.close()` в `finally`.

> ⚠️ **Правило:** Любая async-функция, запускаемая через `asyncio.create_task()` внутри webhook/Starlette-хендлера, **не должна** обращаться к глобальным переменным по имени и **не должна** использовать глобальный `bot`. Всегда:
> 1. Захватывать нужные значения через default-аргументы (`_token=BOT_TOKEN`, `uid=user_id` и т.д.)
> 2. Создавать локальный `_Bot(token=_token, proxy=...)` внутри задачи
> 3. Закрывать его в `finally: await _local_bot.close()`

**Пострадавшие 21.04.2026:** Юля (@Julia_Denisovnaa, id=1629183873) и Sheba (@Sheba232012, id=5810528205) — треки отправлены вручную скриптом `fix_complaints_21_04.py`. Aaaassa (id=8492512614) и кудряш (@chekniidaaam) — рефанд токенов + извинения. Вика (@viking180474, id=1224845726) — оплатила unlock_first 39₽ в 13:18, треки не пришли; отправлены вручную скриптом `fix_viking180474_21_04.py` + начислен 1 токен компенсации.

*Последнее обновление: 21.04.2026 — исправлен баг NameError BOT_TOKEN + Timeout context при разблокировке треков после оплаты; добавлена Вика (@viking180474) в список пострадавших.*

---

### Баг «Двойная оплата 39₽ при повторных нажатиях кнопки (double-tap)» (22.04.2026 — ИСПРАВЛЕН)
**Симптом:** Пользователь нажимает кнопку «🎁 НОВИЧОК: ещё песня — 39₽» или «🔓 Разблокировать за 39₽» несколько раз подряд (пока ждёт генерацию). Каждое нажатие создаёт НОВЫЙ платёж в ЮKassa. Если пользователь успевает подтвердить все — с него списывается сумма в несколько раз больше задуманного.
**Причина:** В обработчиках `process_pay_29_novice` и `process_pay_unlock_first_gen_29` не было защиты от повторных нажатий. Отсутствовала проверка существующего `pending`-платежа перед созданием нового.
**Пострадавшая:** Юля (@Julia_Denisovnaa, id=1629183873) — 9 успешных платежей по 39₽ = 261₽. Треки были доставлены монитором в 03:10 и 03:35 MSK. Все 9 токенов зачислены на баланс (6 остаток + 3 использовано). Отправлено извинение + 1 токен компенсации скриптом `apology_julia_22_04.py`.
**Исправление (`main_with_payments.py`):**
1. `process_pay_29_novice` — добавлена проверка `pending`-платежей за последние 10 минут перед созданием нового:
```python
recent_pending_np = execute_query_sync(
    "SELECT id FROM payments WHERE user_id = %s AND status = 'pending' "
    "AND created_at > NOW() - INTERVAL '10 minutes'", (user_id,)
)
if recent_pending_np:
    await callback_query.answer("⏳ Платёж уже создан! Проверьте предыдущее сообщение с кнопкой оплаты.", show_alert=True)
    return
```
2. `process_pay_unlock_first_gen_29` — аналогичная проверка, но с фильтром по `metadata->>'task_id'`:
```python
recent_pending_ul = execute_query_sync(
    "SELECT id FROM payments WHERE user_id = %s AND status = 'pending' "
    "AND metadata->>'task_id' = %s "
    "AND created_at > NOW() - INTERVAL '10 minutes'", (user_id, task_id)
)
if recent_pending_ul:
    await callback_query.answer("⏳ Платёж уже создан! ...", show_alert=True)
    return
```

> ⚠️ **Правило:** При добавлении любой новой кнопки оплаты — ВСЕГДА добавлять проверку `pending`-платежа за последние 10 минут перед созданием нового (`create_yookassa_payment`). Иначе повторные нажатия приведут к двойной оплате.

*Последнее обновление: 22.04.2026 — исправлен баг двойной оплаты (double-tap) в кнопках 39₽; Юля (@Julia_Denisovnaa) +1 токен компенсации.*

---

### Баг «Дублирование платежей в статистике из-за повторных вебхуков ЮKassa» (23.04.2026 — ИСПРАВЛЕН)

**Симптом:** Статистика в админ-панели бота показывала выручку в 3–12 раз больше реальной. Сравнение с кабинетом ЮKassa показало расхождение:
- 21.04: бот 2930₽, ЮKassa 831₽
- 22.04: бот 3530₽, ЮKassa 203₽
- 23.04: бот 3822₽, ЮKassa 459₽

**Причина:** ЮKassa повторно отправляет вебхук (`payment.succeeded`) пока не получит ответ 200 OK. Каждый повторный вызов вебхука создавал **новую строку** в таблице `payments` с тем же `payment_id`. Один реальный платёж записывался до 12 раз. Кроме того, `add_balance()` вызывалась при каждом повторе → пользователи получали токены в несколько раз больше оплаченного.

**Диагностика через SQL:**
```sql
SELECT payment_id, COUNT(*) as dup_count
FROM payments WHERE status = 'succeeded'
GROUP BY payment_id HAVING COUNT(*) > 1
ORDER BY dup_count DESC LIMIT 10;
-- Результат: payment_id появлялся до 12 раз!
```

**Исправление (`main_with_payments.py`):**

1. **Идемпотентность вебхука** — в `yookassa_webhook` добавлена проверка перед любой обработкой:
```python
if payment_id:
    _dup = execute_query_sync(
        "SELECT id FROM payments WHERE payment_id = %s LIMIT 1", (payment_id,)
    )
    if _dup:
        logging.info(f"⚡ Дубль вебхука пропущен: {payment_id}")
        return JSONResponse({"status": "ok"})
```

2. **`add_payment()` — защита на уровне INSERT** — заменён простой `INSERT` на `INSERT ... WHERE NOT EXISTS`:
```python
execute_query_sync(
    'INSERT INTO payments (user_id, amount, status, payment_id, platform) '
    'SELECT %s, %s, %s, %s, %s WHERE NOT EXISTS '
    '(SELECT 1 FROM payments WHERE payment_id = %s)',
    (user_id, amount, status, payment_id, 'tg', payment_id)
)
```

3. **Статистика — DISTINCT ON (payment_id)** — все запросы `SUM(amount)` и `COUNT(*)` переписаны через подзапрос с `DISTINCT ON`:
```sql
-- Вместо SUM(amount) FROM payments WHERE ...
SELECT COALESCE(SUM(amount), 0)
FROM (SELECT DISTINCT ON (payment_id) payment_id, amount
      FROM payments WHERE status = 'succeeded' AND ...
      ORDER BY payment_id, created_at) _s

-- Вместо COUNT(*):
SELECT COUNT(DISTINCT payment_id) FROM payments WHERE status = 'succeeded' AND ...
```
Исправлены: `sum_24h`, `sum_7days`, `sum_total`, `count_24h`, `count_7days`, `count_total`, `tariffs_24h`, `platform_total`, `platform_7d` в `get_admin_stats()`, а также подзапрос revenue в `process_admin_unit7()`.

> ⚠️ **Правило:** ЮKassa ВСЕГДА повторяет вебхук если не получает 200 немедленно. Любой обработчик вебхука ОБЯЗАН быть **идемпотентным** — проверять существование `payment_id` в БД перед записью и начислением токенов. Баг затронул все дни с 21.04 по 23.04 включительно (старые дублирующие записи остаются в БД, но статистика теперь читает их корректно через DISTINCT).

*Последнее обновление: 23.04.2026 — исправлен баг дублирования платежей из-за повторных вебхуков ЮKassa; добавлена идемпотентность вебхука и DISTINCT в запросах статистики.*

---

### Инцидент «Жалобы пользователей 23–24.04.2026» (24.04.2026 — УСТРАНЁН)

**Пострадавшие:**

1. **@sony_a_nis (id=1788955713)** — заплатила 29₽, платёж завис в `pending` (вебхук ЮKassa не дошёл), токен не зачислился, баланс = 0. Вручную зачислен 1 токен + отправлено извинение. Сообщение доставлено.

2. **@lidaignatenko16 (id=6136613619)** — генерация упала с `ERROR_NOTIFIED` (старый баг Suno), автоматический рефанд не сработал, баланс = 0. Вручную зачислен 1 токен. **Сообщение не доставлено** — пользователь заблокировал бота, помечен `is_blocked = TRUE`.

**Скрипт устранения:** `fix_complaints_24_04.py`

*Последнее обновление: 24.04.2026 — рефанд +1 токен @sony_a_nis и @lidaignatenko16 за технические сбои.*

---

### Исправление «Платежи по 29₽ проходили вместо 39₽» (24.04.2026 — ИСПРАВЛЕНО)

**Симптом:** В ЮKassa приходили платежи на 29₽, хотя код создаёт платёж на 39₽.

**Причины (две):**
1. **`main_with_payments.py`, словарь `amount_to_tokens`** содержал строку `29.00: 1` — «совместимость со старыми ценами». Это позволяло ЮKassa-вебхуку принимать старые pending-платежи на 29₽ (созданные до смены цены) и начислять токены.
2. **`run_monitor_notify.py`** — кнопка разблокировки и сообщение монитора по-прежнему показывали «29₽» в тексте (хотя реальный платёж создавался на 39₽). Пользователи, получившие сообщение до перезапуска монитора, видели старый текст.

**Исправление:**
- `main_with_payments.py` — удалена строка `29.00: 1` из `amount_to_tokens`. Теперь платёж 29₽ не даёт токенов.
- `run_monitor_notify.py` — исправлены все тексты: «29₽» → «39₽» во всех кнопках и сообщениях первой генерации.

---

### Изменение «Демо-версия 45 сек → 60 сек + смещение для попадания в припев» (24.04.2026)

**Изменение:** Демо при первой генерации изменено с 45 секунд на 60 секунд. Добавлен `start_offset=30` — демо начинается с 30-й секунды трека, пропуская вступление и попадая в первый припев.

**Как работает:**
- Функция [`download_and_cut_audio(url, duration=60, start_offset=0)`](run_monitor_notify.py) получила новый параметр `start_offset`.
- ffmpeg-команда: `-ss {start_offset} -i full.mp3 -t {duration} -c copy demo.mp3` — быстрый seek к нужной позиции.
- При первой генерации вызывается: `download_and_cut_audio(url, duration=60, start_offset=30)`.
- Результат: пользователь слышит секунды **30–90** оригинального трека (типичное место первого припева в Suno-треках).
- Обычные (не первые) демо отправляются с `start_offset=0` (с начала), длина 60 сек — без изменений.

> ⚠️ Если у трека нестандартная структура (очень длинное вступление), припев может начинаться позже 30 сек. При необходимости можно увеличить `start_offset` до 40–45 сек.

*Последнее обновление: 24.04.2026 — исправлены платежи 29₽/39₽, демо первой генерации: 45→60 сек с offset=30 (попадание в припев).*
