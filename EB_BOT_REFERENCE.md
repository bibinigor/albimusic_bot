# 📖 EB_BOT_REFERENCE — Справочник по веб-боту ALBI Music

> Этот файл описывает архитектуру и ключевые точки веб-бота на сайте albi-music.ru/app.
> Используй его в начале каждой новой сессии.

---

## 🌐 Где находится бот на сайте

| Что | Где |
|-----|-----|
| **URL бота** | `https://albi-music.ru/app` |
| **Фронтенд (HTML)** | `/var/www/albimusic-web/index.html` |
| **Исходник фронтенда** | `/root/albimusic-bot/web_app_index.html` |
| **Backend (Web API)** | `/root/albimusic-bot/web_api.py` |
| **Порт API** | `8001` (на localhost) |

---

## ⚙️ Сервисы и деплой

### Запущенные systemd-сервисы:
```
albimusic-web.service      — Web API (web_api.py, порт 8001)
albimusic-bot.service      — Telegram бот (основной)
albimusic-vk-bot.service   — VK бот (main_vk.py)
albimusic-celery.service   — Celery воркер (генерация музыки)
albimusic-monitor.service  — Мониторинг и уведомления
nginx.service              — Веб-сервер (HTTPS, порты 80/443)
```

### Как задеплоить изменения фронтенда:
```bash
# 1. Отредактировать исходник
nano /root/albimusic-bot/web_app_index.html

# 2. Скопировать в папку nginx
cp /root/albimusic-bot/web_app_index.html /var/www/albimusic-web/index.html

# 3. Перезагрузить nginx (кэш сбрасывается автоматически — Cache-Control: no-cache)
systemctl reload nginx

# Перезапуск Web API (если менялся web_api.py):
systemctl restart albimusic-web.service
```

---

## 🗂️ Архитектура фронтенда

Файл `/var/www/albimusic-web/index.html` — это **SPA** (Single Page Application) на чистом HTML+JS+CSS без фреймворков.

### Экраны (div с id):
| ID экрана | Описание |
|-----------|----------|
| `loginScreen` | Экран авторизации (при входе) |
| `welcomeScreen` | Главная — «Какую песню создадим?» |
| `createSongTypeScreen` | Выбор: свой текст или AI-текст |
| `aiTextScreen` | Ввод идеи для генерации текста AI |
| `ownTextScreen` | Поле ввода своего текста |
| `lyricsReviewScreen` | Просмотр сгенерированного текста |
| `genreSelectionScreen` | Выбор жанра для песни |
| `createMusicScreen` | Выбор жанра для инструментальной музыки |
| `myTracksScreen` | Мои треки (история) |
| `paymentScreen` | Баланс / покупка токенов |
| `referralScreen` | Пригласить друга |
| `examplesScreen` | Примеры треков (ссылка на ВК) |
| `loadingScreen` | Экран ожидания генерации |

### Нижняя навигация (bottom nav):
```
🏠 Главная → welcomeScreen
📂 Треки → myTracksScreen
💳 Баланс → paymentScreen
🎁 Пригласить друга → referralScreen
🎧 Примеры треков → examplesScreen
```

---

## 🔌 API эндпоинты (web_api.py)

`API_BASE = 'https://albi-music.ru/api'` — базовый URL в JS коде

| Эндпоинт API | Описание |
|---|---|
| `GET /api/auth/vk/login` | Начало VK OAuth |
| `GET /api/auth/yandex/login` | Начало Yandex OAuth |
| `POST /api/auth/vk/token` | VK ID токен → JWT |
| `GET /api/user/me` | Профиль пользователя |
| `GET /api/user/balance` | Баланс токенов |
| `POST /api/generate/music` | Генерация музыки без слов — тело: `{ style: "rock" }` |
| `POST /api/generate/song` | Генерация песни с текстом — тело: `{ lyrics, genre }` |
| `POST /api/generate/lyrics` | Генерация текста AI — тело: `{ idea: "..." }` |
| `GET /api/generation/{task_id}/status` | Статус генерации |
| `GET /api/history` | История треков |
| `GET /api/pricing` | Тарифные планы |
| `POST /api/payment/create` | Создать платёж YooKassa — тело: `{ amount: 250 }` |
| `GET /api/referral/link` | Реферальная ссылка → поле `referral_url` |
| `POST /api/referral/register` | Регистрация реферала |

**⚠️ ВАЖНО:** В JS `API_BASE` уже содержит `/api`, поэтому вызовы строятся как:
`axios.post(`${API_BASE}/generate/music`, ...)` → `https://albi-music.ru/api/generate/music`
❌ НЕ ПИСАТЬ: `${API_BASE}/api/generate/music` (это даст двойной `/api/api/...`)

---

## 💰 Тарифы (токены → песни)

| Токены | Песни | Цена |
|--------|-------|------|
| 1 | 2 | 50 ₽ |
| 10 | 20 | 250 ₽ |
| 25 | 50 | 500 ₽ |
| 60 | 120 | 1 000 ₽ |
| 140 | 280 | 2 000 ₽ |

- 1 токен = 2 песни (2 версии по 45 сек демо → разблокировка за токен)
- Реферальная программа: +2 токена за друга, +5 за 5-го друга

---

## 🔐 Авторизация

Поддерживаются два способа входа:
1. **VK ID** — через VK ID SDK (виджет `OneTap`), затем `POST /api/auth/vk/token`
2. **Яндекс** — OAuth redirect → `/auth/yandex/login` → callback → JWT

JWT токен хранится в `localStorage('auth_token')` и передаётся в заголовке:
`Authorization: Bearer <token>`

Если VK авторизация не работает — пользователям показывается сообщение:
`"Ошибка авторизации ВКонтакте. Пожалуйста, войдите через Яндекс."`

---

## 📁 Ключевые файлы проекта

| Файл | Описание |
|------|----------|
| `web_app_index.html` | **Исходник фронтенда** бота на сайте (редактировать здесь) |
| `web_api.py` | **Backend Web API** (FastAPI, порт 8001) |
| `celery_tasks.py` | Celery задачи (генерация через Suno AI) |
| `main_vk.py` | VK-бот (отдельный сервис) |
| `config.py` | Конфигурация (API ключи, настройки) |
| `db_utils.py` | Утилиты для PostgreSQL |
| `/etc/nginx/sites-enabled/albi-music.ru` | Nginx конфиг |
| `/var/log/albimusic/web-api.log` | Логи Web API |
| `/var/log/albimusic/web-api-error.log` | Логи ошибок Web API |

---

## 🐛 Известные особенности и ловушки

1. **Двойной `/api`** — `API_BASE` уже содержит `/api`. Не добавляй его снова в URL эндпоинтов.
2. **Реферальная ссылка** — API возвращает поле `referral_url`, а не `link`.
3. **Тарифы** — данные хранятся в таблице `pricing_plans` в PostgreSQL, но фронтенд использует статичный список.
4. **Генерация** — после запроса `task_id` нужно поллить `GET /api/generation/{task_id}/status` каждые 5 сек.
5. **Кэш HTML** — nginx настроен на `no-cache`, файл обновляется сразу при копировании.
6. **Бэкапы фронтенда** — перед заменой делать бэкап: `cp /var/www/albimusic-web/index.html /var/www/albimusic-web/index.html.backup_ДАТА`

---

## 🔧 Полезные команды

```bash
# Статус сервисов
systemctl status albimusic-web albimusic-celery nginx

# Логи Web API (последние 50 строк)
tail -50 /var/log/albimusic/web-api.log

# Логи ошибок
tail -50 /var/log/albimusic/web-api-error.log

# Перезапуск всего стека
systemctl restart albimusic-web albimusic-celery && systemctl reload nginx

# Проверка что API отвечает
curl -s https://albi-music.ru/api/pricing | python3 -m json.tool
```

---

## 📋 История изменений VK-бота

### 2026-04-10 — Одноразовое предложение новичкам (5 токенов за 99₽)

**Цель:** Монетизация новичков — показать спецпредложение ровно 1 раз в жизни пользователя.

**Изменённые файлы:**
- [`main_vk.py`](./main_vk.py)
- [`vk_keyboards.py`](./vk_keyboards.py)

**Что сделано:**

1. **БД** — добавлен столбец `newcomer_offer_shown BOOLEAN DEFAULT FALSE` в таблицу `users` (через `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` при старте бота)

2. **[`get_newcomer_offer_keyboard()`](./vk_keyboards.py)** в `vk_keyboards.py` — инлайн-клавиатура с кнопками:
   - `🎁 5 треков за 99₽ — ВЗЯТЬ СЕЙЧАС` (callback `newcomer_offer_pay`)
   - `💰 Другие тарифы` (callback `show_balance`)

3. **[`_send_no_tokens_message(self, user_id, context_text)`](./main_vk.py)** — новый метод VKBot:
   - Читает `newcomer_offer_shown` из БД
   - Если `False` → показывает спецпредложение + инлайн-оплата → ставит `True`
   - Если `True` → стандартное "❌ Пополните баланс" без предложения
   - Безопасность: флаг устанавливается **до** отправки сообщения

4. **Обработчик `newcomer_offer_pay`** в `handle_callback()`:
   - Создаёт платёж YooKassa: 99₽ → 5 токенов
   - Записывает в таблицу `payments`
   - Отправляет ссылку оплаты через `get_payment_keyboard(url)`

5. **Исправлен баг**: `tokens_map` не содержал `99: 5`, из-за чего кнопка `5 токенов — 99₽` в `get_balance_actions_keyboard()` не работала

6. **Заменены 10 мест** с `send_message("❌ У вас недостаточно токенов...")` на `_send_no_tokens_message()`

7. **Обновлены 4 upsell-блока** после генерации при нулевом балансе (первый раз — спецпредложение, повторно — стандартный upsell)

**Текст сообщения спецпредложения:**
```
❌ {контекст}

━━━━━━━━━━━━━━━━━━━━━
🎁 РАЗОВОЕ ПРЕДЛОЖЕНИЕ ДЛЯ НОВИЧКОВ
━━━━━━━━━━━━━━━━━━━━━

5 треков всего за 99₽ — специальный стартовый пакет.

⚠️ Это предложение показывается вам ТОЛЬКО ОДИН РАЗ
и больше НИКОГДА не появится.
Это эксклюзив только для новичков — пользуйтесь, пока не исчезло! 🔥

👇 Нажмите кнопку прямо сейчас:
[🎁 5 треков за 99₽ — ВЗЯТЬ СЕЙЧАС]
[💰 Другие тарифы]
```

**Git commit:** `1f98c5d` — `feat: одноразовое предложение новичку 5 токенов за 99₽`

---

*Последнее обновление: 2026-04-10*
