# ШАГ 2: АУДИТ ТЕКУЩЕГО WEB-ПРИЛОЖЕНИЯ

## 📍 Расположение компонентов на сервере

### 🔧 Backend API (FastAPI)
**Файл:** `/root/albimusic-bot/web_api.py` (749 строк)  
**Процесс:** `PID 3104537` ✅ Запущен (с 19 марта)  
**Порт:** `8001`  
**Виртуальное окружение:** `/root/albimusic-bot/web_venv/`  
**Команда запуска:**
```bash
/root/albimusic-bot/web_venv/bin/python3 /root/albimusic-bot/web_api.py
```

### 🎨 Frontend (Vanilla JS SPA)
**Файл:** `/var/www/albimusic-web/index.html` (1232 строки)  
**Дополнительно:** `/var/www/albimusic-web/style.css` (10KB)  
**Путь в Nginx:** `location ^~ /app → alias /var/www/albimusic-web/`  
**URL доступа:** `https://albi-music.ru/app`

### 🌐 Лендинг (статика)
**Директория:** `/var/www/albimusic-landing/`  
**Файлы:** `index.html`, `style.css`, `script.js`, favicon, images  
**Путь в Nginx:** `root /var/www/albimusic-landing;`  
**URL доступа:** `https://albi-music.ru/` (главная)

### ⚙️ Nginx конфигурация
**Файл:** `/etc/nginx/sites-available/albi-music.ru`  
**Симлинк:** `/etc/nginx/sites-enabled/albi-music.ru`  
**SSL:** Let's Encrypt (fullchain + privkey)  
**Редирект HTTP→HTTPS:** ✅

---

## 🏗 АРХИТЕКТУРА ТЕКУЩЕГО WEB-ПРИЛОЖЕНИЯ

### 📚 Стек технологий

#### Backend (FastAPI)
```python
Framework:    FastAPI (v3.0+)
Server:       Uvicorn (асинхронный ASGI)
Auth:         JWT (HS256, 30 дней expiration)
OAuth:        VK OAuth + Yandex OAuth + VK ID SDK
Database:     PostgreSQL (через db_utils.py)
Task Queue:   Celery (общий с Telegram-ботом)
Port:         8001
```

#### Frontend (SPA без фреймворка)
```javascript
Тип:          Vanilla JavaScript SPA
Библиотеки:   Axios (HTTP), VK ID SDK
Дизайн:       Mobile-First, CSS-in-HTML (встроенный <style>)
Навигация:    Screen-based (showScreen функция)
UI Pattern:   Bottom Navigation Bar (как в мобильных приложениях)
```

#### Infrastructure
```nginx
Reverse Proxy:  Nginx
SSL:            Let's Encrypt (HTTPS)
Тип деплоя:     Прямой запуск Python (не systemd/pm2!)
```

---

## 🔐 СИСТЕМА АВТОРИЗАЦИИ

### JWT Токены
```python
Secret:       Переменная окружения JWT_SECRET
Algorithm:    HS256
Expiration:   30 дней (720 часов)
Payload:      { user_id, provider, exp, iat }
```

### OAuth Providers

#### 1. **VK OAuth** (классический)
- **Auth URL:** `https://oauth.vk.com/authorize`
- **Token URL:** `https://oauth.vk.com/access_token`
- **User Info:** `https://api.vk.com/method/users.get`
- **Callback:** `https://albi-music.ru/auth/vk/callback`
- **Конфиг:** `VK_APP_ID`, `VK_CLIENT_SECRET` из config.py

#### 2. **VK ID SDK** (новый, используется на фронте)
- **SDK:** `@vkid/sdk@<3.0.0` (CDN)
- **Метод:** `exchangeCode()` → `access_token` → отправка на `/api/auth/vk/token`
- **User ID:** Numeric (из VK)

#### 3. **Yandex OAuth**
- **Auth URL:** `https://oauth.yandex.ru/authorize`
- **Token URL:** `https://oauth.yandex.ru/token`
- **User Info:** `https://login.yandex.ru/info`
- **Callback:** `https://albi-music.ru/auth/yandex/callback`
- **User ID:** Хэш строкового ID (SHA256) → numeric

#### 4. **Гостевой режим**
- **Mock токен:** `guest_token_<timestamp>`
- **Баланс:** 1 генерация
- **Ограничения:** Запрещена реальная генерация (имитация)

---

## 📋 API ENDPOINTS (детальная карта)

### 🔐 Авторизация

| Endpoint | Method | Описание | Требует Auth |
|----------|--------|----------|--------------|
| `/auth/{provider}/login` | GET | Начало OAuth (VK/Yandex), возвращает auth_url | ❌ |
| `/auth/{provider}/callback` | GET | OAuth callback, создаёт JWT, редирект → `/app?token=...` | ❌ |
| `/api/auth/vk/token` | POST | VK ID авторизация (новый метод) | ❌ |

### 👤 Пользователь

| Endpoint | Method | Описание | Требует Auth |
|----------|--------|----------|--------------|
| `/api/user/me` | GET | Информация о пользователе (user_id, username, balance) | ✅ JWT |
| `/api/user/balance` | GET | Текущий баланс генераций | ✅ JWT |

### 🎵 Генерация

| Endpoint | Method | Описание | Требует Auth |
|----------|--------|----------|--------------|
| `/api/generate/music` | POST | Инструментальная музыка (style) | ✅ JWT |
| `/api/generate/lyrics` | POST | AI генерация текста песни (idea) | ✅ JWT |
| `/api/generate/song` | POST | Песня с текстом (lyrics, genre, custom_mode) | ✅ JWT |
| `/api/generation/{task_id}/status` | GET | Polling статуса генерации | ✅ JWT |

### 📂 История

| Endpoint | Method | Описание | Требует Auth |
|----------|--------|----------|--------------|
| `/api/history` | GET | История генераций пользователя (limit=20) | ✅ JWT |

### 💳 Платежи

| Endpoint | Method | Описание | Требует Auth |
|----------|--------|----------|--------------|
| `/api/payment/create` | POST | Создание платежа (TODO: не реализовано!) | ✅ JWT |

### 🏥 Health Check

| Endpoint | Method | Описание | Требует Auth |
|----------|--------|----------|--------------|
| `/health` | GET | Статус API | ❌ |

---

## 🎨 FRONTEND АРХИТЕКТУРА

### Screen-based Navigation (9 экранов)

```javascript
Screens (div.screen):
├── loginScreen          // Авторизация (VK ID SDK + Яндекс кнопки)
├── welcomeScreen        // Главный экран (создать песню/музыку)
├── createSongTypeScreen // Выбор типа текста (AI / свой)
├── aiTextScreen         // Ввод идеи для AI текста
├── ownTextScreen        // Ввод своего текста
├── lyricsReviewScreen   // Просмотр сгенерированного текста
├── genreSelectionScreen // Выбор жанра (16 жанров)
├── createMusicScreen    // Инструментальная музыка (жанры)
├── myTracksScreen       // История треков
├── balanceScreen        // Баланс + пополнение + реферальная ссылка
├── examplesScreen       // Ссылка на Telegram-канал
└── loadingScreen        // Ожидание генерации (3-5 мин)
```

### Bottom Navigation (4 кнопки)

```
🏠 Главная  |  📂 Треки  |  💰 Баланс  |  🎧 Примеры
```

### Жанры музыки (16 штук)

```javascript
pop, rock, jazz, blues, hiphop, electronic, classical, 
rnb, reggae, country, metal, folk, latin, punk, funk, shanson

+ Опция "Свой вариант" (prompt input)
```

### Флоу пользователя (веб)

```mermaid
graph TD
    A[Вход на сайт] --> B{Есть токен?}
    B -->|Нет| C[🔐 loginScreen]
    B -->|Да| D[🏠 welcomeScreen]
    
    C -->|VK ID| E[VK SDK exchangeCode]
    C -->|Яндекс| F[OAuth redirect]
    E --> G[/api/auth/vk/token]
    F --> H[/auth/yandex/callback]
    G --> I[JWT токен → localStorage]
    H --> I
    C -->|Гостевой режим| J[Mock токен guest_token_xxx]
    J --> D
    
    D -->|🎵 Создать песню| K[createSongTypeScreen]
    D -->|🎶 Создать музыку| L[createMusicScreen]
    
    K -->|✨ AI текст| M[aiTextScreen: ввод идеи]
    K -->|📝 Свой текст| N[ownTextScreen]
    
    M --> O[/api/generate/lyrics]
    O --> P[lyricsReviewScreen]
    
    N --> Q[genreSelectionScreen]
    P --> Q
    L --> R[Выбор жанра инструментальной]
    
    Q --> S[/api/generate/song]
    R --> T[/api/generate/music]
    
    S --> U[loadingScreen: polling каждые 5 сек]
    T --> U
    
    U --> V[/api/generation/{task_id}/status]
    V -->|completed| W[myTracksScreen: показ треков]
    V -->|pending| U
    V -->|failed| D
```

---

## 🔄 ИНТЕГРАЦИЯ С BACKEND БОТА

### Общие компоненты (переиспользуются)

| Компонент | Источник | Использование |
|-----------|----------|---------------|
| **PostgreSQL БД** | `db_utils.py` | Общая таблица `users`, `generations` |
| **Celery Tasks** | `celery_tasks.py` | `generate_music_task()`, `generate_song_task()`, `generate_suno_lyrics_sync()` |
| **Suno API** | `celery_tasks.py` | Тот же API для генерации |
| **Биллинг логика** | `db_utils.py` | Списание токенов (`balance - 1`) |
| **Жанры** | Хардкод | Дублирование списка жанров (16 шт.) |

### Отличия от Telegram-бота

| Аспект | Telegram Bot | Web App |
|--------|--------------|---------|
| **User ID источник** | `message.from_user.id` (Telegram) | OAuth (VK/Yandex), хэширование для Yandex |
| **Сессия** | FSM State (aiogram) | `sessionData` объект в JS |
| **Авторизация** | Автоматическая (Telegram) | JWT после OAuth |
| **UI** | Inline Keyboard + ReplyKeyboard | Экраны (div.screen) + Bottom Nav |
| **Демо-система** | ✅ Полная (45 сек демо → разблокировка) | ❌ НЕТ разблокировки в web_api.py! |
| **Платежи** | ✅ ЮKassa интегрирована | ❌ TODO (endpoint заглушка) |
| **Поделиться** | Inline Query | ❌ НЕТ (нужен Web Share API!) |
| **Реферальная программа** | ✅ Полная (invited_by, бонусы) | ⚠️ Частично (есть ссылка, но логики нет в API) |
| **Polling генерации** | Celery result polling в Python | Frontend polling каждые 5 сек (JS) |

---

## 🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ (GAP Analysis)

### ❌ 1. ОТСУТСТВУЕТ ДЕМО-СИСТЕМА!
**В боте:** После генерации → 2 демо (45 сек) → кнопка "Разблокировать за 1 токен" → 2 полные версии  
**В веб-версии:** Нет endpoint `/api/ для разблокировки! Нет таблицы `demo_tracks`!

**Критичность:** 🔴 ВЫСОКАЯ (основа монетизации!)

### ❌ 2. НЕТ СИСТЕМЫ ПЛАТЕЖЕЙ
**Endpoint:** `/api/payment/create` → `raise HTTPException(status_code=501)`  
**В боте:** Полная интеграция с ЮKassa (webhook, проверка статуса)  

**Критичность:** 🔴 ВЫСОКАЯ

### ❌ 3. РЕФЕРАЛЬНАЯ ПРОГРАММА НЕ РАБОТАЕТ
**Фронт:** Показывает ссылку `?ref={user_id}`  
**Backend:** Нет обработки `ref` параметра при регистрации!  
**В боте:** Логика `invited_by`, начисление +2 токена, проверка 5-го друга

**Критичность:** 🟡 СРЕДНЯЯ

### ❌ 4. НЕТ WEB SHARE API
**В боте:** Inline Query → поделиться в любой чат Telegram  
**В веб-версии:** Нет кнопки "Поделиться" на треке!  
**Нужно:** `navigator.share()` для мобильных устройств

**Критичность:** 🟡 СРЕДНЯЯ

### ❌ 5. ГОСТЕВОЙ РЕЖИМ БЕЗ РЕАЛЬНОЙ ГЕНЕРАЦИИ
**Текущее поведение:** Mock токен → имитация генерации → alert("Авторизуйтесь")  
**Проблема:** В боте есть БЕСПЛАТНАЯ генерация (balance=1 при старте)!  
**Правильно:** Даже гостю дать 1 реальную генерацию

**Критичность:** 🟢 НИЗКАЯ (можно оставить как есть для защиты)

### ❌ 6. НЕТ КАВЕР/МИНУСОВКА ФУНКЦИЙ
**В боте:** Кавер (2 токена), Минусовка (1 токен), Конвертация WAV (1 токен)  
**В веб-версии:** Только песня/музыка  

**Критичность:** 🟡 СРЕДНЯЯ

### ❌ 7. НЕТ ПОДДЕРЖКИ (SUPPORT)
**В боте:** Кнопка "Поддержка" → FSM → отправка сообщения админу → ответ  
**В веб-версии:** Вообще нет раздела поддержки  

**Критичность:** 🟡 СРЕДНЯЯ

### ⚠️ 8. ЖАНРЫ ДУБЛИРОВАНЫ (код запах)
**Проблема:** Одинаковый список жанров в 3 местах:
- `main_with_payments.py` (бот)
- `web_api.py` (бэкенд)
- `index.html` (фронт)

**Решение:** Единый справочник в БД или константы

**Критичность:** 🟢 НИЗКАЯ (технический долг)

---

## 📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА ФУНКЦИЙ

| Функция | Telegram Bot | Web App | Приоритет переноса |
|---------|--------------|---------|-------------------|
| **Авторизация** | ✅ Auto (TG ID) | ✅ OAuth (VK+Yandex) | ✅ ГОТОВО |
| **JWT токены** | ❌ Не нужны | ✅ Есть | ✅ ГОТОВО |
| **Генерация песни** | ✅ FSM | ✅ API `/api/generate/song` | ✅ ГОТОВО |
| **Генерация музыки** | ✅ FSM | ✅ API `/api/generate/music` | ✅ ГОТОВО |
| **AI текст** | ✅ Suno Lyrics | ✅ API `/api/generate/lyrics` | ✅ ГОТОВО |
| **16 жанров** | ✅ | ✅ | ✅ ГОТОВО |
| **Демо 45 сек** | ✅ Полная система | ❌ НЕТ | 🔴 КРИТИЧНО |
| **Разблокировка** | ✅ -1 токен | ❌ НЕТ | 🔴 КРИТИЧНО |
| **Платежи ЮKassa** | ✅ Webhook | ❌ TODO | 🔴 КРИТИЧНО |
| **Реферальная программа** | ✅ +2 токена | ❌ НЕТ логики | 🟡 ВАЖНО |
| **Бонус за 5-го друга** | ✅ +5 токенов | ❌ НЕТ | 🟡 ВАЖНО |
| **Кавер** | ✅ -2 токена | ❌ НЕТ | 🟡 ВАЖНО |
| **Минусовка** | ✅ -1 токен | ❌ НЕТ | 🟡 ВАЖНО |
| **WAV конвертация** | ✅ -1 токен | ❌ НЕТ | 🟢 ОПЦИОНАЛЬНО |
| **Поддержка** | ✅ FSM Support | ❌ НЕТ | 🟡 ВАЖНО |
| **Поделиться** | ✅ Inline Query | ❌ НЕТ | 🟡 ВАЖНО |
| **История треков** | ✅ | ✅ `/api/history` | ✅ ГОТОВО |
| **Web Share API** | ❌ Не нужен | ❌ НЕТ | 🟡 ВАЖНО |
| **Broadcast (рассылка)** | ✅ Админ FSM | ❌ НЕТ | 🟢 ОПЦИОНАЛЬНО |
| **Статистика админа** | ✅ | ❌ НЕТ | 🟢 ОПЦИОНАЛЬНО |

---

## 🎯 ВЫВОД: Текущий статус веб-приложения

### ✅ Что работает хорошо:
1. **Solid Backend:** FastAPI правильно структурирован
2. **Авторизация:** JWT + OAuth (VK, Yandex) работают
3. **Базовая генерация:** Песни и музыка генерируются через общий Celery
4. **Mobile-First UI:** Bottom navigation, экраны, адаптив
5. **Общая БД и таски:** Нет дублирования инфраструктуры

### ❌ Критические пробелы:
1. **НЕТ ДЕМО-СИСТЕМЫ** (основа монетизации!)
2. **НЕТ ПЛАТЕЖЕЙ** (заглушка вместо ЮKassa)
3. **НЕТ РЕФЕРАЛЬНОЙ ЛОГИКИ** (показывается ссылка, но не работает)

### 📈 Уровень готовности: **~60%**
- **Backend:** 70% готовности
- **Frontend:** 80% готовности (UI отличный, но не хватает фич)
- **Интеграция:** 40% готовности (критичная демо-система отсутствует)

---

## 🚀 ЧТО ДАЛЬШЕ? (Подготовка к Шагу 3)

На **Шаге 3** нам предстоит:

1. **GAP-анализ детальный:** Построчное сравнение логики бота и веба
2. **Приоритизация задач:** Что переносить в первую очередь
3. **Мокапы/схемы:** Визуализация отсутствующих экранов (Demo unlock, Share UI)
4. **План миграции:** Пошаговый roadmap внедрения

---

## 📁 СТРУКТУРА ФАЙЛОВ (итоговая карта)

```
/root/albimusic-bot/
├── web_api.py                      # ✅ Backend API (FastAPI, 749 строк)
├── web_venv/                       # ✅ Виртуальное окружение
├── db_utils.py                     # ✅ Общая БД логика
├── celery_tasks.py                 # ✅ Общие таски
├── config.py                       # ✅ Конфиг (OAuth credentials)
└── main_with_payments.py           # ✅ Эталонный Telegram-бот

/var/www/albimusic-web/
├── index.html                      # ✅ SPA (1232 строки, Vanilla JS)
└── style.css                       # ✅ Дополнительные стили

/var/www/albimusic-landing/
└── index.html                      # ✅ Лендинг (статика)

/etc/nginx/sites-available/
└── albi-music.ru                   # ✅ Nginx конфигурация
```

---

**Процесс запущен:** ✅ `/root/albimusic-bot/web_venv/bin/python3 /root/albimusic-bot/web_api.py` (PID 3104537, с 19 марта)

---

## 🔍 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Версии зависимостей (web_api.py)
```python
FastAPI      (latest)
Uvicorn      (ASGI server)
httpx        (async HTTP client)
PyJWT        (JWT tokens)
Pydantic     (validation)
python-multipart (для form data)
```

### Nginx routing
```nginx
/          → /var/www/albimusic-landing/   (static)
/app       → /var/www/albimusic-web/       (SPA)
/api       → http://127.0.0.1:8001/api     (proxy)
/auth      → http://127.0.0.1:8001/auth    (proxy)
/health    → http://127.0.0.1:8001/health  (proxy)
/payment/  → http://127.0.0.1:8000         (Telegram webhook)
/webhook/  → http://127.0.0.1:8000         (Telegram webhook)
```

### База данных (общая)
```sql
users          # Пользователи (TG + Web объединены!)
generations    # История генераций
demo_tracks    # ❌ НЕТ В ВЕБ-ВЕРСИИ!
payments       # Платежи (используется ботом)
referrals      # Рефералы (используется ботом)
support_messages   # Поддержка (только бот)
channel_posts      # Публикации (только бот)
```

---

**Статус Шага 2:** ✅ ЗАВЕРШЕН  
**Дата аудита:** 27 марта 2026  
**Следующий шаг:** GAP-анализ + мокапы (ожидание команды "[ОДОБРЕНО. ПЕРЕХОДИМ К ШАГУ 3]")
