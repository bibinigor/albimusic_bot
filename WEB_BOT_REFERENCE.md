# 🌐 Справочник: Бот на сайте (albi-music.ru)

> Давай этот файл AI в начале каждой сессии по веб-боту.

---

## 📍 Ссылка на бот

**https://albi-music.ru/app**

---

## 📁 Ключевые файлы

| Что | Путь |
|-----|------|
| **Фронтенд (HTML + JS)** | `/var/www/albimusic-web/index.html` |
| **Бэкенд (FastAPI)** | `/root/albimusic-bot/web_api.py` |
| **Конфигурация** | `/root/albimusic-bot/config.py` |
| **Python venv бэкенда** | `/root/albimusic-bot/web_venv/` (отдельный от Telegram/VK!) |
| **Nginx конфиг сайта** | `/etc/nginx/sites-available/albi-music.ru` |
| **Стили** | `/var/www/albimusic-web/style.css` |

---

## ⚙️ Сервисы

| Сервис | Описание |
|--------|----------|
| `albimusic-web.service` | FastAPI бэкенд (порт 8001) |
| `nginx.service` | Раздаёт фронтенд и проксирует API |

```bash
# Управление бэкендом
systemctl status albimusic-web
systemctl restart albimusic-web
systemctl stop albimusic-web

# Логи бэкенда
tail -f /var/log/albimusic/web-api.log
tail -f /var/log/albimusic/web-api-error.log
journalctl -u albimusic-web -f

# Nginx
systemctl reload nginx
systemctl status nginx
```

> ⚠️ **ВАЖНО:** Фронтенд (index.html) — статический файл. Nginx раздаёт его напрямую.
> После правки `index.html` перезапуск **не нужен**.
> После правки `web_api.py` — `systemctl restart albimusic-web`.

---

## 🔌 Как устроена маршрутизация

```
Браузер → HTTPS → nginx (albi-music.ru)
  ├── /app         → /var/www/albimusic-web/index.html  (статика)
  ├── /api/*       → http://127.0.0.1:8001/api/*        (FastAPI)
  ├── /auth/*      → http://127.0.0.1:8001/auth/*       (OAuth callbacks)
  └── /            → /var/www/albimusic-landing/        (лендинг)
```

---

## 🔑 API Endpoints (FastAPI, порт 8001)

### ⚠️ КРИТИЧЕСКИ ВАЖНО: разница в URL-префиксах!
- Auth endpoints (`/auth/...`) — **БЕЗ** префикса `/api`
- Все остальные (`/api/...`) — **С** префиксом `/api`

```
# Auth (без /api)
GET  /auth/vk/login              → Начало VK OAuth (возвращает auth_url)
GET  /auth/vk/callback           → Callback от VK (редирект → /app?token=JWT)
GET  /auth/yandex/login          → Начало Яндекс OAuth (возвращает auth_url)
GET  /auth/yandex/callback       → Callback от Яндекс (редирект → /app?token=JWT)

# API (с /api)
POST /api/auth/vk/token          → VK ID SDK: принимает access_token + user_id
GET  /api/user/me                → Инфо о пользователе (JWT required)
GET  /api/user/balance           → Баланс токенов (JWT required)
POST /api/generate/music         → Генерация музыки
POST /api/generate/lyrics        → Генерация текста
POST /api/generate/song          → Генерация песни с текстом
GET  /api/generation/{id}/status → Статус генерации
GET  /api/history                → История треков пользователя
POST /api/unlock/{task_id}       → Разблокировать полный трек (списывает 1 токен)
GET  /api/pricing                → Тарифные планы
POST /api/payment/create         → Создать платёж YooKassa
POST /api/payment/webhook        → Webhook от YooKassa
GET  /api/referral/link          → Реферальная ссылка
GET  /api/referral/stats         → Статистика рефералов
POST /api/referral/register      → Зарегистрировать реферальный код
GET  /health                     → Health check
```

---

## 🔐 Авторизация

Три способа:
1. **VK ID Widget** (VKID SDK) — рендерится автоматически. При ошибке виджета — это нормально (пользователь не в VK), ошибку пользователю не показывать.
2. **ВКонтакте (fallback)** — кнопка → `GET /auth/vk/login` → редирект на VK → callback → `/app?token=JWT`
3. **Яндекс** — кнопка → `GET https://albi-music.ru/auth/yandex/login` → редирект на Яндекс → callback → `/app?token=JWT`
4. **Гость** — локальный тестовый режим, без реального бэкенда

**Как обрабатывается токен после OAuth:**
- Backend редиректит на `https://albi-music.ru/app?token=JWT_TOKEN`
- Фронтенд при `DOMContentLoaded` проверяет `?token=` в URL
- Сохраняет в `localStorage('auth_token')`
- Очищает URL через `history.replaceState`

---

## 🔧 OAuth конфигурация

| Параметр | Значение |
|----------|----------|
| `VK_APP_ID` | `54451761` (env: `VK_APP_ID`) |
| `VK_CLIENT_SECRET` | env: `VK_CLIENT_SECRET` |
| `YANDEX_CLIENT_ID` | env: `YANDEX_CLIENT_ID` |
| `YANDEX_CLIENT_SECRET` | env: `YANDEX_CLIENT_SECRET` |
| VK redirect_uri | `https://albi-music.ru/auth/vk/callback` |
| Yandex redirect_uri | `https://albi-music.ru/auth/yandex/callback` |
| JWT expires | 30 дней |

---

## 🐛 Известные баги, которые уже исправлены

1. VK widget ERROR при загрузке → **не показывать** `showError()`, только `console.warn`
2. VK exchangeCode падал → **fallback** на серверный OAuth через `loginVKFallback()`
3. Яндекс URL был неверный `/api/auth/yandex/login` → исправлено на `/auth/yandex/login`
4. `loadUserInfo` вызывал `/user/info` (не существовал) → `/user/me`
5. `loadMyTracks` double `/api` + неверный ключ → `/history` + ключ `history`
6. `loadBalance` double `/api` → `/user/me`

---

## 🗄️ База данных

Общая PostgreSQL со всеми ботами. Таблицы:
- `users` — пользователи (user_id, username, first_name, balance, invited_by)
- `generations` — история генераций (task_id, user_id, prompt, audio_url, status)
- `payments` — платежи YooKassa
- `referrals` — реферальная программа

---

## 🔗 Связанные сервисы

Веб-бот использует те же Celery workers что и Telegram/VK боты:
- `celery-worker.service`
- `albimusic-celery.service`

При изменении `celery_tasks.py` перезапускать оба worker'а.
