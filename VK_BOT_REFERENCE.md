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
| **Сервис systemd** | `/etc/systemd/system/albimusic-vk-bot.service` |

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
| `OPENROUTER_API_KEY` | задаётся в systemd-сервисе как `Environment=` |
| `OPENROUTER_MODEL` | `google/gemini-2.0-flash-001` (Gemini 2.0 Flash) |

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
| `/etc/systemd/system/albimusic-vk-bot.service` | `systemctl daemon-reload && systemctl restart albimusic-vk-bot` |

---

## 🤖 Gemini-пайплайн генерации текстов (v2, апрель 2026)

### Что изменилось

Раньше тексты песен генерировал Suno через `/api/v1/lyrics` — качество на русском было плохим (глагольные рифмы, несуществующие слова, нет ритма). Теперь тексты пишет **Gemini 2.0 Flash** через OpenRouter API.

### Новый флоу для пользователя

```
Создать песню → 🤖 AI-текст
       ↓
Бот: "Напишите о чём песня и в каком жанре одним сообщением"
       ↓
Пользователь: "про кота Василия в стиле панк-рок"
       ↓
Бот: "✍️ Пишу стихи..." (мгновенно, не блокирует бота)
       ↓ (5-15 секунд в отдельном потоке)
Gemini генерирует: текст песни + стиль для Suno
       ↓
Бот показывает текст + кнопки:
  [🎵 Создать песню]  [🔄 Переписать текст (бесплатно: 3 из 3)]
  [📋 Вариант 1] [📋 Вариант 2]  ← после переписываний
       ↓ при нажатии "Создать песню"
Suno делает музыку (3-5 мин) → готовый трек
```

### Лимиты переписываний

- **3 бесплатных** переписывания на одну идею
- Далее **1 токен** за каждое
- История хранит до 3 предыдущих вариантов — кнопки «📋 Вариант N»

### Автофолбэк при проблемах с OpenRouter

Если OpenRouter недоступен (нет денег, сбой):
1. Бот **автоматически** переключается на старый Suno Lyrics API
2. Пользователь не видит ошибки — текст приходит (чуть хуже)
3. Если оба недоступны — вежливое сообщение об ошибке

**Мониторинг баланса OpenRouter:**
```bash
# Смотреть в реальном времени — появится CRITICAL при нехватке средств
journalctl -u albimusic-vk-bot -f | grep -iE "OPENROUTER|FALLBACK|CRITICAL|💳"
```

### Где находится код

| Что | Файл | Место |
|-----|------|-------|
| Функция генерации текста через Gemini | `celery_tasks.py` | `generate_lyrics_via_gemini()` |
| Поток генерации (threading) | `main_vk.py` | обработчик `States.WAITING_SONG_IDEA` |
| Обработчик кнопок просмотра текста | `main_vk.py` | обработчик `States.REVIEWING_LYRICS` |
| Клавиатура с кнопками и историей | `vk_keyboards.py` | `get_lyrics_review_keyboard()` |
| Ключ API OpenRouter | `/etc/systemd/system/albimusic-vk-bot.service` | `Environment=OPENROUTER_API_KEY=...` |

### Как сменить модель

В `/etc/systemd/system/albimusic-vk-bot.service` изменить строку:
```
Environment="OPENROUTER_MODEL=google/gemini-2.0-flash-001"
```
Доступные варианты (через openrouter.ai):
- `google/gemini-2.0-flash-001` — текущая (рекомендуется)
- `anthropic/claude-3.5-haiku` — дороже, ещё лучше русский
- `openai/gpt-4o` — дорогой, хорошее качество

После смены: `systemctl daemon-reload && systemctl restart albimusic-vk-bot`

### Как откатить на старую логику (экстренно)

В `main_vk.py` найти строку:
```python
elif False and vk_state == States.CHOOSING_LYRICS_VARIANT:  # DISABLED
```
Убрать `False and` → старый код снова работает. Перезапустить бота.

---

## 🆕 Новые состояния FSM (добавлены в v2)

| Состояние | Когда используется |
|-----------|-------------------|
| `States.REVIEWING_LYRICS` | Пользователь видит готовый текст и выбирает: создать / переписать / выбрать вариант из истории |

**Состояние `CHOOSING_LYRICS_VARIANT` отключено** (заменено на `REVIEWING_LYRICS`). Код оставлен закомментированным в `main_vk.py` для возможного отката.
