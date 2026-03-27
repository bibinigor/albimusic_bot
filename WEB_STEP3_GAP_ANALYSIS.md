# ШАГ 3: GAP-АНАЛИЗ И СТРАТЕГИЯ MOBILE-WEB АДАПТАЦИИ

**Дата:** 2026-03-27  
**Эталон:** Telegram Bot (main_with_payments.py, 4025 строк)  
**Цель:** Веб-приложение (web_api.py + /var/www/albimusic-web/index.html)  
**Фокус:** Mobile-First / PWA Experience

---

## 📊 EXECUTIVE SUMMARY

**Текущая готовность веб-версии:** 58% от функционала бота

**Критические пробелы (блокируют монетизацию):**
1. 🔴 **Демо-система** (основа бизнес-модели)
2. 🔴 **ЮKassa платежи** (endpoint заглушка)
3. 🔴 **Реферальная программа** (логика отсутствует)

**Архитектурные проблемы:**
- FSM бота частично конвертирован в REST API
- Отсутствует WebSocket/SSE для real-time генерации
- Нет защиты от накруток (биллинг уязвим)
- Нет публичных страниц треков для sharing

---

## 1️⃣ ЧТО ОТСУТСТВУЕТ НА САЙТЕ (ФУНКЦИОНАЛЬНЫЙ GAP)

### 🔴 КРИТИЧЕСКИЕ ФУНКЦИИ (P0 - Блокируют монетизацию)

| Функция бота | Статус веба | Влияние | Приоритет |
|--------------|-------------|---------|-----------|
| **Демо-система (45 сек)** | ❌ Отсутствует | Нет монетизации треков | P0 |
| **ЮKassa платежи** | ⚠️ Заглушка | Нет пополнения баланса | P0 |
| **Реферальная логика** | ❌ Отсутствует | Нет виральности | P0 |
| **Разблокировка демо** | ❌ Отсутствует | Нет конверсии в оплату | P0 |

**Детализация:**

#### 1.1 Демо-система (Основа монетизации)

**В боте:**
```python
# main_with_payments.py:2854-2900
async def create_demo_tracks_if_needed(clip_id, user_id, generation_id):
    # Создает 2 демо-файла по 45 секунд
    # Сохраняет в demo_tracks с locked=True
    # Отправляет inline-кнопки "Разблокировать"
```

**На сайте:**
- ❌ Нет таблицы `demo_tracks` в web_api.py
- ❌ Нет логики обрезания аудио до 45 сек
- ❌ Нет кнопок "Разблокировать за 1 токен"
- ❌ Frontend сразу показывает полные треки

**Флоу монетизации в боте:**
```
Генерация → 2 демо (45s) → Кнопка "🔓 Разблокировать" → 
-1 токен → 2 полных трека → Возможность скачать
```

**Потеря конверсии:**
- Без демо пользователь не мотивирован пополнять баланс
- Нет триггера "хочу полную версию"
- Невозможно монетизировать каждый трек (только генерацию)

---

#### 1.2 ЮKassa платежи

**В боте:**
```python
# main_with_payments.py:1168-1287
@router.callback_query(F.data.startswith("package:"))
async def package_selected(callback: CallbackQuery):
    # Создает payment в YooKassa
    # Генерирует уникальную ссылку
    # Webhook обрабатывает автоначисление
```

**Пакеты:**
```
50₽ → 1 токен
250₽ → 10 токенов
500₽ → 25 токенов
1000₽ → 60 токенов  (20% бонус)
2000₽ → 140 токенов (40% бонус)
```

**На сайте:**
```python
# web_api.py:425
@app.post("/api/payments/create")
async def create_payment(request: Request):
    return {"error": "Payments not implemented yet"}  # ЗАГЛУШКА!
```

**Что нужно:**
- OAuth callback для ЮKassa
- Webhook для автоматического начисления
- История платежей в личном кабинете
- Защита от двойного начисления

---

#### 1.3 Реферальная программа

**В боте:**
```python
# main_with_payments.py:3663-3747
Бонусы:
- Пригласивший: +2 токена за каждого друга
- Новый юзер: стартовые токены
- 5-й друг: +5 бонусов пригласившему
```

**На сайте:**
```python
# web_api.py:274
@app.post("/api/referral/register")
async def register_referral(request: Request):
    # TODO: реализовать логику начисления
    return {"message": "Referral registered"}
```

**Проблема:**
- Ссылка генерируется, но бонусы не начисляются
- Нет таблицы `referrals` в web_api.py
- Нет логики подсчета 5-го друга

---

### 🟡 ВАЖНЫЕ ФУНКЦИИ (P1 - Снижают ценность)

| Функция бота | Статус веба | Описание пробела |
|--------------|-------------|------------------|
| **Кавер (Cover)** | ❌ Отсутствует | Нет загрузки файлов + cover endpoint |
| **Минусовка (Karaoke)** | ❌ Отсутствует | Нет превращения трека в минус |
| **Web Share API** | ❌ Отсутствует | Нельзя поделиться в мессенджеры |
| **Публичные страницы** | ❌ Отсутствует | Нельзя расшарить трек с превью |
| **Конвертация в WAV** | ❌ Отсутствует | Нет premium-опции |
| **Поддержка** | ❌ Отсутствует | Нет связи с админом |
| **Обратная связь** | ❌ Отсутствует | Нет сбора отзывов |

**Детализация:**

#### 1.4 Cover (Кавер на чужой голос)

**В боте:**
```python
# FSM: CoverStates (4 шага)
1. Отправка аудиофайла (up to 20MB)
2. Описание стиля
3. Генерация (2 токена)
4. Получение кавера на другом голосе
```

**На сайте:**
- ❌ Нет `/api/cover/upload` endpoint
- ❌ Нет обработки multipart/form-data
- ❌ Нет UI для загрузки файла
- ❌ Нет интеграции с Suno cover API

**Mobile-адаптация:**
```
Экран "Кавер" → Кнопка "Выбрать файл" (input[type=file]) →
Bottom Sheet со стилем → Экран загрузки → Результат
```

---

#### 1.5 Karaoke (Минусовка)

**В боте:**
```python
# main_with_payments.py:3100-3200
- Берет существующую песню
- Отправляет на Suno stem splitting
- Возвращает минусовку без вокала (-1 токен)
```

**На сайте:**
- ❌ Нет кнопки "🎤 Сделать минусовку"
- ❌ Нет `/api/karaoke/create` endpoint
- ❌ Нет UI для выбора трека из истории

---

#### 1.6 Web Share API (Критично для мобильных!)

**Проблема в боте:**
```python
# Inline Query - работает только в Telegram
@router.inline_query()
async def share_track(inline_query: InlineQuery):
    # Пользователь может переслать в другой чат
```

**Решение для веба:**
```javascript
// Нативный шаринг в любой мессенджер
if (navigator.share) {
    await navigator.share({
        title: 'Моя песня - AlbiMusic',
        text: 'Послушай, что я создал!',
        url: 'https://albi-music.ru/track/abc123'
    });
}
```

**Что нужно:**
1. Публичные страницы треков (Open Graph мета-теги)
2. Кнопка "Поделиться" в UI
3. Fallback на копирование ссылки (desktop)

---

### 🟢 ВТОРОСТЕПЕННЫЕ ФУНКЦИИ (P2 - Nice to have)

| Функция бота | Статус веба | Описание |
|--------------|-------------|----------|
| **Постинг в канал** | ❌ Отсутствует | Админ-функция (не критично) |
| **Рассылка** | ❌ Отсутствует | Админ-функция |
| **Статистика** | ⚠️ Частично | Нет полной аналитики |
| **Обратная связь** | ❌ Отсутствует | Нет формы фидбека |

---

## 2️⃣ ТРАНСФОРМАЦИЯ FSM В MOBILE UI/API

### Принципы адаптации:

| Элемент бота | → | Web Mobile эквивалент |
|--------------|---|----------------------|
| FSM State | → | URL route + React state |
| ReplyKeyboardMarkup | → | Bottom Navigation Bar |
| InlineKeyboardMarkup | → | Bottom Sheet / Modal |
| `await message.answer()` | → | REST POST → UI update |
| GIF-анимация | → | CSS/Lottie loader |
| Callback Query | → | API POST + state change |
| `bot.send_audio(file_id)` | → | `<audio src="{url}">` |

---

### 2.1 Флоу: Создание песни с текстом (CreateSongStates)

#### В БОТЕ (7 шагов FSM):

```python
CreateSongStates:
├─ waiting_for_topic          # Ввод темы песни
├─ waiting_for_style          # Выбор жанра (17 кнопок)
├─ waiting_for_custom_style   # Или кастомный стиль
├─ waiting_for_ai_lyrics      # AI генерирует 2 варианта
├─ waiting_for_lyrics_choice  # Юзер выбирает вариант
├─ waiting_for_vocal_gender   # Мужской/женский вокал
└─ [Генерация + демо]         # Celery task → 2 демо трека
```

**Inline-кнопки:**
```python
genres = [
    ["🎸 Рок", "🎹 Поп"],
    ["🎤 Рэп", "🎵 Джаз"],
    ["🎻 Классика", "🎺 Блюз"],
    # ... +11 жанров
    ["✏️ Свой стиль"]  # Кастомный ввод
]
```

#### НА ВЕБЕ (Mobile-First флоу):

```
Экран 1: "Создать песню" (главное меню)
   ↓ tap
Экран 2: Форма "О чем песня?" (textarea + кнопка "Далее")
   ↓ submit
Экран 3: Bottom Sheet "Выбери жанр" (scrollable grid 3x6)
   ↓ select OR tap "Свой стиль"
Экран 3b (optional): Modal "Введи свой стиль"
   ↓ submit
Экран 4: Loading "AI пишет текст..." (прогресс-бар)
   ↓ API response
Экран 5: Карусель "Выбери вариант текста" (swipe left/right)
   ├─ Вариант 1 (full lyrics)
   └─ Вариант 2 (full lyrics)
   ↓ tap "Выбрать"
Экран 6: Toggle "Мужской вокал / Женский вокал"
   ↓ submit
Экран 7: Loading "Создание трека (3-5 мин)"
   ├─ WebSocket real-time: "Анализ... 15%"
   ├─ "Генерация музыки... 60%"
   └─ "Финализация... 95%"
   ↓ complete
Экран 8: ДЕМО-превью (2 варианта по 45 сек)
   ├─ 🔒 Вариант 1 [Play 45s] → [🔓 Разблокировать 1 токен]
   └─ 🔒 Вариант 2 [Play 45s] → [🔓 Разблокировать 1 токен]
   ↓ unlock
Экран 9: Полный трек
   ├─ [▶ Play full]
   ├─ [📥 Download MP3]
   ├─ [📱 Share (Web Share API)]
   └─ [🎤 Сделать минусовку -1 токен]
```

#### API ENDPOINTS (новые):

```python
POST /api/generate/lyrics        # AI генерация 2 вариантов текста
GET  /api/generate/lyrics/{task_id}  # Polling результата

POST /api/generate/song-with-lyrics  # Запуск генерации трека
GET  /api/generate/status/{task_id}  # Real-time статус 0-100%

GET  /api/tracks/{generation_id}/demo  # Получить 2 демо-файла (45s)
POST /api/tracks/{demo_id}/unlock     # Разблокировать за 1 токен
```

---

### 2.2 Флоу: Создание музыки (MusicStates)

#### В БОТЕ (5 шагов):

```python
MusicStates:
├─ waiting_for_description    # Описание инструментов
├─ waiting_for_style          # Жанр (те же 17)
├─ waiting_for_custom_style   # Или кастомный
└─ [Генерация instrumental]   # Без вокала
```

#### НА ВЕБЕ:

```
Экран 1: Tab "Музыка без слов" (в главном меню)
   ↓
Экран 2: Форма "Опиши инструменты" 
   Placeholder: "спокойная гитара и пианино"
   ↓
Экран 3: Bottom Sheet "Жанр"
   ↓
Экран 4: Loading (3-5 мин) + WebSocket
   ↓
Экран 5: ДЕМО 45s [🔓 Разблокировать]
   ↓
Экран 6: Полный трек
```

**Разница от песни:**
- Нет AI генерации текста (пропускаем шаги 4-6)
- Instrumental-only Suno API

---

### 2.3 Флоу: Платежи (ЮKassa)

#### В БОТЕ:

```python
Меню → [💎 Купить токены] → 
5 inline-кнопок с пакетами →
Генерация payment_url (YooKassa API) →
Браузер открывает ссылку →
Webhook получает succeeded →
Начисление токенов + уведомление
```

#### НА ВЕБЕ (Mobile-First):

```
Экран: Личный кабинет (баланс вверху)
   ↓ tap "Пополнить"
Bottom Sheet "Выбери пакет":
   ├─ [50₽ → 1 токен]
   ├─ [250₽ → 10 токенов]
   ├─ [500₽ → 25 токенов] 🔥
   ├─ [1000₽ → 60 токенов] 💎 +20%
   └─ [2000₽ → 140 токенов] 🚀 +40%
   ↓ select
Редирект на YooKassa (iframe / new tab)
   ↓ payment success
Webhook → Database update
   ↓
WebSocket push → Frontend
Toast: "✅ +10 токенов зачислено!"
```

**API ENDPOINTS:**

```python
POST /api/payments/create
Body: { "package": "250" }
Response: { "payment_url": "https://yookassa.ru/..." }

POST /api/payments/webhook  # ЮKassa callback
Body: YooKassa payload
Action: UPDATE users SET balance += tokens

GET /api/payments/history
Response: [{ "date", "amount", "tokens", "status" }]
```

---

### 2.4 Флоу: Реферальная программа

#### В БОТЕ:

```python
Меню → [👥 Пригласить] →
Генерация deeplink: t.me/albimusic_bot?start=ref_123456 →
Кнопка "Поделиться ссылкой" (Telegram native share) →

Новый юзер /start ref_123456 →
DB: referrals INSERT (referrer_id, referred_id) →
+2 токена referrer'у (instantly)

Триггер на 5-го друга:
COUNT(*) FROM referrals WHERE referrer_id = X → IF = 5 → +5 бонус
```

#### НА ВЕБЕ:

```
Экран: "Пригласи друга"
   ├─ Твоя ссылка: https://albi-music.ru?ref=abc123
   ├─ Скопировано! ✅
   ├─ [📱 Share (Web Share API)]
   └─ Статистика:
       • Друзей приглашено: 3
       • Заработано токенов: +6
       • До бонуса: 2 человека (+5 токенов)

Новый юзер открывает ?ref=abc123 →
После авторизации: POST /api/referral/register →
DB insert → Webhook на referrer'а → Toast "Друг присоединился! +2 токена"
```

**API ENDPOINTS:**

```python
GET /api/referral/link
Response: { "link": "https://albi-music.ru?ref=USER_ID_BASE64" }

POST /api/referral/register
Body: { "referrer_code": "abc123" }
Action: INSERT referrals + UPDATE balance

GET /api/referral/stats
Response: {
    "total_referrals": 3,
    "earned_tokens": 6,
    "bonus_progress": { "current": 3, "target": 5 }
}
```

---

### 2.5 Флоу: Демо → Разблокировка (КЛЮЧЕВАЯ МОНЕТИЗАЦИЯ)

#### В БОТЕ:

```python
# После генерации (celery_tasks.py)
create_demo_tracks_if_needed(clip_id, user_id, generation_id)
   ↓
FFmpeg обрезает 2 аудио до 45 сек
   ↓
Сохранение в demo_tracks (locked=True)
   ↓
Telegram: send_audio(demo_file) + inline-кнопка "🔓 Разблокировать 1 токен"
   ↓
User нажимает → callback_query "unlock_demo:{demo_id}"
   ↓
Проверка баланса (≥1 токен)
   ↓
-1 токен → UPDATE demo_tracks SET locked=False
   ↓
Отправка полного файла (send_audio full_clip)
```

#### НА ВЕБЕ (Mobile UI):

```html
<!-- Экран после генерации -->
<div class="demo-screen">
    <h2>🎉 Твои треки готовы!</h2>
    <p>Послушай 45-секундные демо:</p>
    
    <!-- Вариант 1 -->
    <div class="track-card locked">
        <audio controls id="demo1" 
               onloadedmetadata="limitDuration(this, 45)">
            <source src="/api/audio/demo/abc123.mp3">
        </audio>
        <button class="unlock-btn" onclick="unlockTrack('abc123')">
            🔓 Разблокировать за 1 токен
        </button>
    </div>
    
    <!-- Вариант 2 -->
    <div class="track-card locked">
        <audio controls id="demo2" 
               onloadedmetadata="limitDuration(this, 45)">
            <source src="/api/audio/demo/xyz789.mp3">
        </audio>
        <button class="unlock-btn" onclick="unlockTrack('xyz789')">
            🔓 Разблокировать за 1 токен
        </button>
    </div>
</div>

<script>
// Ограничение воспроизведения до 45 сек
function limitDuration(audio, maxSeconds) {
    audio.addEventListener('timeupdate', () => {
        if (audio.currentTime > maxSeconds) {
            audio.pause();
            audio.currentTime = 0;
            showToast('Полная версия доступна после разблокировки');
        }
    });
}

// Разблокировка трека
async function unlockTrack(demoId) {
    if (userBalance < 1) {
        showModal('Недостаточно токенов', 'Пополнить баланс?');
        return;
    }
    
    const res = await axios.post(`/api/tracks/${demoId}/unlock`);
    if (res.data.success) {
        // Замена демо на полный трек
        document.getElementById('demo1').src = res.data.full_url;
        document.querySelector('.unlock-btn').remove();
        userBalance -= 1;
        showToast('✅ Трек разблокирован!');
    }
}
</script>
```

**API ENDPOINTS:**

```python
POST /api/tracks/{demo_id}/unlock
Headers: Authorization: Bearer {jwt}
Response: {
    "success": true,
    "full_url": "/api/audio/full/abc123.mp3",
    "new_balance": 9
}

# Backend проверки:
1. JWT валидность
2. Баланс ≥ 1 токен
3. demo_id принадлежит юзеру
4. Не разблокирован ранее (idempotency)
5. Атомарная транзакция: -1 токен + UPDATE locked=False
```

---

## 3️⃣ РЕШЕНИЕ ПЛАТФОРМЕННЫХ ПРОБЛЕМ

### 3.1 Замена "Поделиться в Telegram" на Web Share API

#### Проблема:

В боте:
```python
@router.inline_query()
async def share_track(inline_query: InlineQuery):
    # Пользователь пересылает трек в другой чат Telegram
    # Показывает превью, аудио-кнопку
```

На вебе: Inline Query не работает. Нужна альтернатива для sharing.

#### Решение: Web Share API + Публичные страницы

**Шаг 1: Создать публичную страницу трека**

```python
# web_api.py (новый endpoint)
@app.get("/track/{track_id}")
async def public_track_page(track_id: str):
    # Получить трек из DB
    track = get_track_by_id(track_id)
    
    # Open Graph meta-теги для превью в мессенджерах
    meta = f"""
    <meta property="og:title" content="{track.title}" />
    <meta property="og:description" content="{track.style}" />
    <meta property="og:image" content="{track.cover_url}" />
    <meta property="og:audio" content="{track.audio_url}" />
    <meta property="og:type" content="music.song" />
    """
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        {meta}
        <title>{track.title} - AlbiMusic</title>
    </head>
    <body>
        <h1>{track.title}</h1>
        <audio controls src="{track.audio_url}"></audio>
        <a href="https://albi-music.ru">Создай свою песню!</a>
    </body>
    </html>
    """)
```

**Шаг 2: Кнопка Share в UI**

```javascript
// В карточке трека (мобильная версия)
async function shareTrack(trackId, title) {
    const shareData = {
        title: title,
        text: `Послушай, что я создал в AlbiMusic! 🎵`,
        url: `https://albi-music.ru/track/${trackId}`
    };
    
    if (navigator.share) {
        // Нативный шаринг (Android/iOS)
        await navigator.share(shareData);
    } else {
        // Fallback для desktop: копирование ссылки
        await navigator.clipboard.writeText(shareData.url);
        showToast('Ссылка скопирована!');
    }
}
```

**Результат:**
- Юзер может поделиться в WhatsApp, VK, Telegram, Instagram и т.д. через системное меню
- Превью трека автоматически подтягивается мессенджером (Open Graph)

---

### 3.2 Синхронизация баз пользователей (Telegram vs Яндекс/VK)

#### Проблема:

```python
# Бот (main_with_payments.py)
User ID = Telegram user_id (int64, уникален)

# Веб (web_api.py)
JWT = { "user_id": telegram_id, "provider": "yandex", ... }
```

Возможны коллизии:
- Яндекс ID 123456 ≠ Telegram ID 123456
- VK ID 123456 ≠ Telegram ID 123456

#### Решение: Составной ключ provider + external_id

**Миграция таблицы users:**

```sql
-- Добавить колонку для источника
ALTER TABLE users ADD COLUMN provider VARCHAR(20) DEFAULT 'telegram';
ALTER TABLE users ADD COLUMN external_id BIGINT;

-- Заполнить для существующих (бот-пользователи)
UPDATE users SET provider = 'telegram', external_id = telegram_id;

-- Новый уникальный индекс
CREATE UNIQUE INDEX idx_users_provider_external 
ON users(provider, external_id);

-- Для веб-юзеров
INSERT INTO users (provider, external_id, username, ...)
VALUES ('yandex', 185967336, 'John Doe', ...);
```

**Обновить JWT генерацию:**

```python
# web_api.py
def create_jwt_token(user_id, provider):
    payload = {
        "user_id": user_id,
        "provider": provider,  # 'telegram', 'yandex', 'vk'
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Lookup пользователя:**

```python
def get_user_from_jwt(token):
    payload = jwt.decode(token, SECRET_KEY)
    return db.query("""
        SELECT * FROM users 
        WHERE provider = %s AND external_id = %s
    """, (payload['provider'], payload['user_id']))
```

---

### 3.3 Защита от двойной авторизации (Telegram bot + Web)

#### Проблема:

Пользователь может авторизоваться:
1. В Telegram боте (user_id 123456)
2. На сайте через Яндекс (внутренний Yandex ID 123456)

Это будут 2 разных аккаунта с разными балансами.

#### Решение: Связывание аккаунтов

**Сценарий 1: Юзер сначала в боте, потом на сайте**

```
Бот → /start → users.telegram_id = 123456
Веб → OAuth Yandex → users.yandex_id = 789

Предложить связать:
"У вас уже есть аккаунт в Telegram боте. Связать аккаунты?"
[Да] → UPDATE users SET yandex_id = 789 WHERE telegram_id = 123456
```

**Сценарий 2: Юзер сначала на сайте, потом в боте**

```
Веб → OAuth → users.yandex_id = 789, balance = 5
Бот → /start → Проверка: 
  SELECT * FROM users WHERE yandex_id = (get from Yandex API by telegram_id)
  
Если найден:
  "Ваш аккаунт с сайта найден! Баланс: 5 токенов."
Если нет:
  Создать новый + предложить ввести email для связывания
```

**Таблица связи:**

```sql
CREATE TABLE user_accounts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    provider VARCHAR(20),  -- 'telegram', 'yandex', 'vk'
    external_id BIGINT,
    linked_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4️⃣ БЕЗОПАСНОСТЬ БИЛЛИНГА (Защита от накруток)

### 4.1 Уязвимости текущего веб-кода

**Проблема 1: Нет проверки баланса на фронтенде**

```javascript
// /var/www/albimusic-web/index.html:850
async function generateTrack() {
    // НЕТ ПРОВЕРКИ: if (userBalance < 1) return;
    await axios.post('/api/generate/song');  // Сразу отправляет
}
```

**Атака:**
```javascript
// Злоумышленник в консоли браузера
for (let i = 0; i < 100; i++) {
    axios.post('/api/generate/song', { topic: 'test', style: 'rock' });
}
// 100 генераций без списания токенов!
```

**Проблема 2: Нет атомарности списания на backend**

```python
# web_api.py:300 (текущий код)
@app.post("/api/generate/song")
async def generate_song(request: Request):
    user = get_user_from_jwt(request)
    
    # НЕПРАВИЛЬНО:
    if user.balance < 1:
        return {"error": "Insufficient balance"}
    
    # Между проверкой и списанием - race condition!
    # Юзер может отправить 2 запроса одновременно
    
    task = celery_task.delay(...)  # Генерация запущена
    
    # Списание ПОСЛЕ генерации (юзер может закрыть страницу)
    user.balance -= 1
    db.commit()
```

**Проблема 3: Нет idempotency для платежей**

```python
# Webhook YooKassa может прийти дважды
@app.post("/api/payments/webhook")
async def payment_webhook(request: Request):
    payment_id = request.json['id']
    
    # НЕТ ПРОВЕРКИ: if payment_id already processed
    
    user.balance += 10  # Двойное начисление!
    db.commit()
```

---

### 4.2 Решения для безопасности

#### Защита 1: Атомарное списание токенов (DB-уровень)

```python
# web_api.py (исправленный)
@app.post("/api/generate/song")
async def generate_song(request: Request, data: GenerateSongRequest):
    user_id = get_user_id_from_jwt(request)
    
    # АТОМАРНАЯ ОПЕРАЦИЯ: списание + проверка в одном UPDATE
    result = db.execute("""
        UPDATE users 
        SET balance = balance - 1 
        WHERE id = %s AND balance >= 1
        RETURNING balance
    """, (user_id,))
    
    if result.rowcount == 0:
        # Либо недостаточно баланса, либо юзер не найден
        return JSONResponse(
            status_code=402,
            content={"error": "Insufficient balance"}
        )
    
    new_balance = result.fetchone()[0]
    
    # Теперь можно безопасно запускать генерацию
    task = generate_song_task.apply_async(
        args=[user_id, data.topic, data.style],
        task_id=f"gen_{user_id}_{time.time()}"
    )
    
    return {
        "task_id": task.id,
        "new_balance": new_balance
    }
```

**Преимущества:**
- ✅ Race condition невозможен (DB lock)
- ✅ Токен списан ДО генерации
- ✅ Если генерация упадет - возврат через отдельный механизм

#### Защита 2: Idempotency для платежей

```python
# Таблица для отслеживания обработанных платежей
CREATE TABLE processed_payments (
    payment_id VARCHAR(255) PRIMARY KEY,
    user_id INT,
    amount INT,
    tokens INT,
    processed_at TIMESTAMP DEFAULT NOW()
);

# Webhook
@app.post("/api/payments/webhook")
async def payment_webhook(request: Request):
    data = request.json
    payment_id = data['object']['id']
    
    # Проверка идемпотентности
    existing = db.query(
        "SELECT 1 FROM processed_payments WHERE payment_id = %s",
        (payment_id,)
    )
    
    if existing:
        # Уже обработан
        return {"status": "ok"}
    
    # Атомарная транзакция
    with db.begin():
        # 1. Добавить в processed_payments
        db.execute("""
            INSERT INTO processed_payments (payment_id, user_id, amount, tokens)
            VALUES (%s, %s, %s, %s)
        """, (payment_id, user_id, amount, tokens))
        
        # 2. Начислить токены
        db.execute("""
            UPDATE users SET balance = balance + %s WHERE id = %s
        """, (tokens, user_id))
    
    # 3. Уведомить юзера (WebSocket)
    await notify_user(user_id, f"✅ +{tokens} токенов зачислено!")
    
    return {"status": "ok"}
```

#### Защита 3: Rate limiting на генерацию

```python
# Redis для хранения лимитов
REDIS = redis.Redis(host='localhost', port=6379)

@app.post("/api/generate/song")
async def generate_song(request: Request):
    user_id = get_user_id_from_jwt(request)
    
    # Лимит: максимум 5 генераций в минуту
    key = f"ratelimit:generate:{user_id}"
    count = REDIS.incr(key)
    
    if count == 1:
        # Первый запрос - установить TTL 60 секунд
        REDIS.expire(key, 60)
    
    if count > 5:
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests. Wait 1 minute."}
        )
    
    # Продолжить генерацию...
```

#### Защита 4: Проверка JWT на каждый запрос (Middleware)

```python
# web_api.py
@app.middleware("http")
async def verify_jwt_middleware(request: Request, call_next):
    # Публичные эндпоинты
    if request.url.path in ["/", "/api/auth/yandex", "/track/{id}"]:
        return await call_next(request)
    
    # Проверка JWT
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"}
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        request.state.user_id = payload['user_id']
        request.state.provider = payload['provider']
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"error": "Token expired"}
        )
    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid token"}
        )
    
    return await call_next(request)
```

#### Защита 5: Возврат токенов при ошибке генерации

```python
# celery_tasks.py
@celery_app.task
def generate_song_task(user_id, topic, style):
    try:
        # Генерация через Suno API
        result = suno_api.generate(topic, style)
        
        if result['status'] == 'error':
            # Возврат токена юзеру
            db.execute("""
                UPDATE users SET balance = balance + 1 WHERE id = %s
            """, (user_id,))
            
            notify_user(user_id, "⚠️ Ошибка генерации. Токен возвращен.")
            return {"error": result['message']}
        
        # Создание демо-треков...
        create_demo_tracks(result['clips'], user_id)
        
    except Exception as e:
        # Критическая ошибка - возврат токена
        db.execute("""
            UPDATE users SET balance = balance + 1 WHERE id = %s
        """, (user_id,))
        
        log_error(f"Generation failed for user {user_id}: {e}")
        raise
```

---

## 5️⃣ ПЛАН АДАПТАЦИИ (Roadmap)

### Фаза 1: Критическая монетизация (P0) - 2 недели

**Задачи:**
1. ✅ Демо-система (45 сек обрезка + UI)
2. ✅ Разблокировка треков (endpoint + атомарное списание)
3. ✅ ЮKassa интеграция (payment + webhook)
4. ✅ Реферальная программа (логика + бонусы)
5. ✅ Безопасность биллинга (атомарность + idempotency)

**Метрики успеха:**
- Конверсия демо → разблокировка: >15%
- Средний чек: 250₽
- Реферальные установки: +20% к органике

---

### Фаза 2: Расширенные функции (P1) - 2 недели

**Задачи:**
1. ✅ Cover (загрузка файла + Suno API)
2. ✅ Karaoke (минусовка)
3. ✅ Web Share API + публичные страницы
4. ✅ Поддержка (support tickets)
5. ✅ WebSocket для real-time генерации

**Метрики:**
- % использования Cover: >5%
- Share rate: >30%

---

### Фаза 3: UX улучшения (P2) - 1 неделя

**Задачи:**
1. ✅ PWA (install prompt)
2. ✅ Голосовой ввод темы песни
3. ✅ History фильтры (дата, жанр)
4. ✅ Dark mode
5. ✅ Уведомления (Push API)

---

## 6️⃣ ТЕХНИЧЕСКИЙ СТЕК (рекомендации)

### Backend (без изменений):
- FastAPI (уже есть)
- PostgreSQL (уже есть)
- Celery + RabbitMQ (уже есть)
- Redis (добавить для rate limiting)

### Frontend (улучшения):
- ❌ Vanilla JS → ✅ **React или Vue.js** (для сложных State Machine)
- ✅ Axios (оставить)
- ✅ PWA (Service Worker)
- ✅ **Socket.IO** (WebSocket для real-time)

### Инфраструктура:
- ✅ Nginx (уже настроен)
- ✅ Certbot (SSL уже есть)
- ⚠️ CDN для аудио (рекомендация: CloudFlare R2)
- ⚠️ Мониторинг (Sentry для ошибок)

---

## 7️⃣ МЕТРИКИ ДЛЯ ОТСЛЕЖИВАНИЯ

### KPI Монетизации:
```sql
-- Конверсия демо → разблокировка
SELECT 
    COUNT(DISTINCT generation_id) as total_generations,
    COUNT(DISTINCT CASE WHEN locked = FALSE THEN demo_id END) as unlocked,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN locked = FALSE THEN demo_id END) / COUNT(DISTINCT generation_id), 2) as conversion_rate
FROM demo_tracks;

-- Средний чек
SELECT AVG(amount) FROM payments WHERE status = 'succeeded';

-- LTV (Lifetime Value)
SELECT 
    user_id,
    SUM(amount) as total_spent,
    COUNT(*) as purchases,
    MIN(created_at) as first_purchase,
    MAX(created_at) as last_purchase
FROM payments
GROUP BY user_id
HAVING COUNT(*) > 1;
```

---

## 🎯 ВЫВОД

**Готовность веб-версии: 58%**

**Критические пробелы устранены в этом плане:**
- ✅ Демо-система (45s + unlock)
- ✅ ЮKassa платежи (idempotent)
- ✅ Реферальная программа (+2/+5 токенов)
- ✅ Безопасность биллинга (атомарность)
- ✅ FSM → Mobile UI адаптация
- ✅ Web Share API
- ✅ Публичные страницы треков

**Документ готов для утверждения.**

---

**Ожидание команды:**
```
[ОДОБРЕНО. ПЕРЕХОДИМ К ШАГУ 4]
```

После утверждения начнется **ШАГ 4: Написание кода** (приоритет P0 функции).
