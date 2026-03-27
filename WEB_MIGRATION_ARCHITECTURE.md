# 🎵 Архитектурная карта бизнес-логики Telegram-бота AlBi Music

**Дата анализа:** 27.03.2026  
**Эталонный файл:** `/root/albimusic-bot/main_with_payments.py` (4025 строк)  
**Цель:** Полный реверс-инжиниринг для переноса на мобильный веб

---

## 📊 1. ДЕРЕВО ПОЛЬЗОВАТЕЛЬСКИХ СЦЕНАРИЕВ (FSM)

### 1.1 Главное меню (Entry Point)
```
/start → Приветствие → Демо-треки (5 шт) → Приглашение в канал
         ↓
    Главное меню:
    ├─ 🎵 Создать песню
    ├─ 🎶 Создать музыку
    ├─ 📂 Мои треки
    ├─ 💰 Баланс
    ├─ 🎧 Примеры песен и промптов
    ├─ 📞 Поддержка
    └─ 👨‍💻 Админ панель (только для админов)
```

### 1.2 Флоу "Создать песню" (CreateSongStates)
```
🎵 Создать песню
    ↓
choosing_text_type → Выбор источника текста:
    ├─ ✨ ПРИДУМАТЬ ТЕКСТ (text_ai)
    │   ↓
    │   waiting_song_idea → Ввод описания (макс 200 символов)
    │   ↓
    │   [AI генерирует 2 варианта текста через Suno Lyrics API]
    │   ↓
    │   choosing_lyrics_variant → Выбор варианта:
    │       ├─ 📝 Выбрать вариант 1
    │       ├─ 📝 Выбрать вариант 2
    │       └─ ✏️ Написать свой текст
    │
    └─ 📝 У МЕНЯ СВОЙ ТЕКСТ (text_own)
        ↓
        waiting_own_lyrics → Ввод текста (макс 3000 символов)
    
    ↓
waiting_genre → Выбор жанра из 17 вариантов:
    ├─ 🎤 Поп
    ├─ 🎸 Рок
    ├─ 🎺 Джаз
    ├─ 🎵 Блюз
    ├─ 🎧 Хип-хоп
    ├─ ⚡ Электронная
    ├─ 🎻 Классическая
    ├─ 💿 R&B/Соул
    ├─ 🌴 Регги
    ├─ 🤠 Кантри
    ├─ 🤘 Метал
    ├─ 🪕 Фолк
    ├─ 💃 Латины
    ├─ 🎭 Панк
    ├─ 🕺 Фанк
    ├─ 🎙️ Шансон
    └─ ✏️ Свой вариант → waiting_custom_genre
    
    ↓
[Генерация через Celery + Suno API]
    ↓
Результат: 2 демо-версии (45 сек каждая)
```

#### 🔍 Детали генерации песни:
- **Auto-detection режима:** `custom_mode = len(lyrics) > 500`
- **Определение пола вокала:** Автоматически из описания жанра (`female`/`male`)
- **Перевод тегов:** `[Куплет]` → `[Verse]`, `[Припев]` → `[Chorus]` для Suno API
- **Время генерации:** 3-5 минут (90 попыток по 10 сек)

### 1.3 Флоу "Создать музыку" (MusicStates)
```
🎶 Создать музыку (инструментальная)
    ↓
waiting_for_music_style → Выбор жанра (те же 17):
    ├─ Предустановленные жанры
    └─ ✏️ Свой вариант
    
    ↓
[Генерация через Celery + Suno API с instrumental=True]
    ↓
Результат: 2 демо-версии (45 сек каждая)
```

### 1.4 Флоу "Мои треки" (History)
```
📂 Мои треки
    ↓
Получение последних 20 треков из БД (status='completed')
    ↓
Для каждого трека:
    ├─ 🎧 Слушать (прямая ссылка)
    ├─ 🔁 Повторить (новая генерация)
    └─ 🔗 Поделиться (inline query)
```

### 1.5 Флоу "Баланс" (Billing)
```
💰 Баланс
    ↓
Отображение:
    ├─ Текущий баланс токенов
    ├─ 📄 Документы (оферта, политика)
    ├─ 🌟 Пригласить друга (+2 токена)
    └─ Тарифы оплаты:
        ├─ 💫 1 токен (2 песни) — 50₽
        ├─ 💳 10 токенов (20 песен) — 250₽
        ├─ 🔥 25 токенов (50 песен) — 500₽
        ├─ ⭐ 60 токенов (120 песен) — 1000₽
        └─ 💎 140 токенов (280 песен) — 2000₽
    
    ↓ (при выборе тарифа)
Создание платежа через ЮKassa API
    ↓
Редирект на страницу оплаты
    ↓
Webhook от ЮKassa → Начисление токенов
```

#### 🎁 Реферальная система:
- **Базовая награда:** 2 токена за приглашенного друга
- **Бонус за 5-го:** +5 токенов дополнительно (итого 7)
- **Ссылка:** `https://t.me/AlBimusic_bot?start=ref_{user_id}`

### 1.6 Дополнительные функции для треков

#### 🔓 Разблокировка полных версий (unlock)
```
🔓 Разблокировать полные версии (1 токен)
    ↓
Проверка баланса (-1 токен если не админ)
    ↓
UPDATE demo_tracks SET is_unlocked = TRUE
    ↓
Отправка 2 полных версий (без ограничения по времени)
```

#### 🎤 Минусовка / Karaoke (KaraokeStates)
```
🎤 Минусовка (1 токен)
    ↓
Выбор источника:
    ├─ 📂 Из моих треков → Выбор версии (v1/v2)
    └─ 📤 Загрузить свой файл (MP3/WAV/M4A/OGG, макс 5 мин)
    
    ↓
[Suno API karaoke endpoint: удаление вокала]
    ↓
Результат: Инструментальная версия
```

#### 🎸 Кавер / Cover (CoverStates)
```
🎸 Кавер (2 токена)
    ↓
Выбор источника:
    ├─ 📂 Из моих треков → Выбор версии (v1/v2)
    └─ 📤 Загрузить свой файл
    
    ↓
waiting_for_genre → Выбор нового жанра (17 вариантов)
    ↓
[Suno API cover endpoint: перепой в новом стиле]
    ↓
Результат: Кавер-версия в новом жанре
```

#### 🎵 Конвертация в WAV
```
🎵 В WAV (1 токен)
    ↓
Выбор версии (v1/v2)
    ↓
[Suno API wav endpoint]
    ↓
Результат: Профессиональный WAV файл
```

#### 📢 Публикация в канал (ChannelPostStates)
```
📢 Отправить в канал
    ↓
Проверка: Только для разблокированных треков
    ↓
waiting_for_version (если 2 варианта)
    ↓
waiting_for_comment → Ввод комментария
    ↓
Публикация в @ALBImusic_chart
```

#### 🔗 Поделиться (Inline Query)
```
🔗 Отправить другу
    ↓
Inline query с switch_inline_query
    ↓
Формирование карточки:
    - 🎵 Заголовок трека
    - Описание (промпт)
    - 🎧 Ссылка для прослушивания
    - Призыв попробовать бота
```

### 1.7 Админ-панель (только для ADMIN_ID)
```
👨‍💻 Админ панель
    ↓
    ├─ 📊 Статистика:
    │   ├─ Всего пользователей (+новых сегодня)
    │   ├─ Новых за 7/30 дней
    │   ├─ Воронка (Начали → Дошли до меню)
    │   ├─ Генераций за 24ч
    │   ├─ Успешность генераций (%)
    │   ├─ Платежи (24ч / 7 дней / всего)
    │   └─ Разбивка по тарифам
    │
    ├─ 🔍 Проверить Suno API
    │
    ├─ 📨 Рассылка (BroadcastStates):
    │   └─ waiting_text → waiting_confirm → Отправка всем
    │
    └─ 📩 Поддержка:
        └─ Просмотр тикетов → Ответ (SupportReplyStates)
```

### 1.8 Поддержка (SupportStates)
```
📞 Поддержка
    ↓
waiting_message → Ввод сообщения
    ↓
Сохранение в support_messages (replied=FALSE)
    ↓
[Админ видит в админ-панели]
    ↓
Админ отвечает → Отправка пользователю → DELETE из БД
```

---

## 💰 2. БИЛЛИНГ И СПИСАНИЕ ТОКЕНОВ

### 2.1 Система токенов
```python
# 1 токен = 1 генерация = 2 версии песни (по 45 сек демо)
# Новый пользователь: 1 токен в подарок
```

### 2.2 Точки списания токенов

#### ✅ Обязательное списание (перед генерацией):
```python
# Местоположение в коде:
# 1. start_song_generation() - строка 2813
# 2. start_music_generation() - строка 2763
# 3. process_custom_music_genre() - строка 2763

if not is_admin(user_id):
    balance = get_balance_number(user_id)
    if balance <= 0:
        return ERROR
    execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))
```

#### ✅ Дополнительные функции:
```python
# Разблокировка полных версий: -1 токен (строка 3277)
# Минусовка: -1 токен (строка 3128)
# Кавер: -2 токена (строка 3549)
# WAV: -1 токен (строка 3211)
```

### 2.3 Начисление токенов

#### 💳 Через ЮKassa (webhook):
```python
# /webhook/yookassa - строка 733
amount_to_tokens = {
    50.00: 1,      # 50₽ → 1 токен
    250.00: 10,    # 250₽ → 10 токенов
    500.00: 25,    # 500₽ → 25 токенов
    1000.00: 60,   # 1000₽ → 60 токенов
    2000.00: 140,  # 2000₽ → 140 токенов
}

add_balance(user_id, tokens)
add_payment(user_id, amount, 'succeeded', payment_id)
```

#### 🎁 Реферальная система:
```python
# /start с ref_param - строка 815-856
# Базовая награда:
execute_query_sync('UPDATE users SET balance = balance + 2 WHERE user_id = %s', (invited_by,))

# Бонус за 5-го реферала:
if referral_count == 5:
    tokens_to_add = 7  # 2 + 5 бонус
```

### 2.4 Защита от ошибок

#### ❌ Возврат токенов при ошибке:
```python
# В celery_tasks.py - все генерационные таски
# При ошибке Suno API (SENSITIVE_WORD_ERROR, таймаут):
execute_query_sync(
    "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
    (user_id,)
)
```

---

## 🔧 3. CELERY + SUNO API (Асинхронная генерация)

### 3.1 Архитектура таск-воркеров
```
Telegram Bot (main_with_payments.py)
    ↓
[Создание task с UUID]
    ↓
RabbitMQ (amqp://localhost:5672)
    ↓
Celery Worker (celery_tasks.py)
    ↓
Suno API (api.sunoapi.org)
    ↓
[Polling статуса каждые 10 сек, макс 90 попыток = 15 минут]
    ↓
Telegram Bot получает результат
    ↓
Отправка пользователю + сохранение в demo_tracks
```

### 3.2 Celery Tasks (celery_tasks.py)

#### 📝 Основные таски:
```python
@celery_app.task(name='generate_music_task')
def generate_music_task(user_id, style, task_id=None):
    # Инструментальная музыка (instrumental=True)
    
@celery_app.task(name='generate_song_task')
def generate_song_task(user_id, lyrics, style, custom_mode, task_id=None, is_song=True):
    # Песня с текстом (instrumental=False)
    
@celery_app.task(name='generate_karaoke_task')
def generate_karaoke_task(user_id, original_task_id, version):
    # Минусовка (удаление вокала)
    
@celery_app.task(name='generate_cover_task')
def generate_cover_task(user_id, original_task_id, genre, version):
    # Кавер в новом жанре
    
@celery_app.task(name='generate_wav_task')
def generate_wav_task(user_id, original_task_id, version):
    # Конвертация в WAV
```

#### 🔍 Особенности Suno API:
```python
# 1. Генерация текста (lyrics)
POST /api/v1/lyrics
    → taskId
    → Polling: GET /api/v1/lyrics/record-info?taskId={taskId}
    → Response: { "data": { "status": "complete", "text": "..." } }

# 2. Генерация музыки/песни
POST /api/v1/generate
    Body: {
        "prompt": "текст песни или описание",
        "style": "жанр + инструменты + настроение",
        "customMode": true/false,
        "instrumental": true/false,
        "model": "V5",
        "vocalsGender": "m"/"f",
        "styleWeight": 0.8-0.9
    }
    → taskId
    → Polling: GET /api/v1/generate/record-info?taskId={taskId}
    → Response: { 
        "data": { 
            "status": "SUCCESS", 
            "response": { 
                "sunoData": [
                    { "audioUrl": "...", "id": "audio_id_1" },
                    { "audioUrl": "...", "id": "audio_id_2" }
                ]
            }
        }
    }

# 3. Минусовка
POST /api/v1/karaoke
    Body: { "songId": "audio_id" }

# 4. Кавер
POST /api/v1/cover
    Body: { "songId": "audio_id", "genre": "новый жанр" }

# 5. WAV
POST /api/v1/wav
    Body: { "songId": "audio_id" }
```

#### ⚙️ Логика автоопределения:
```python
# 1. Custom Mode (для длинных текстов)
use_custom_mode = len(lyrics) > 500

# 2. Пол вокала
vocal_gender = "m"  # по умолчанию
if "female" in style.lower() or "женск" in style.lower():
    vocal_gender = "f"
    style += ", female vocals, female voice"  # усиление

# 3. Перевод стиля с русского на английский
style = translate_style_to_english(style, add_improvements=True)
# Добавляет: "high quality, professional, studio quality"
# И инструменты по жанру (guitar, drums, bass для рока и т.д.)
```

### 3.3 Обработка результатов

#### 📊 Структура БД:
```sql
-- Таблица demo_tracks (для разблокировки)
CREATE TABLE demo_tracks (
    id SERIAL PRIMARY KEY,
    task_id UUID NOT NULL,
    user_id BIGINT NOT NULL,
    demo_url_1 TEXT,  -- 45 сек демо
    demo_url_2 TEXT,  -- 45 сек демо
    full_url_1 TEXT,  -- Полная версия
    full_url_2 TEXT,  -- Полная версия
    is_unlocked BOOLEAN DEFAULT FALSE,  -- Статус разблокировки
    unlocked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица generations (история)
CREATE TABLE generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id UUID NOT NULL,
    prompt TEXT,
    audio_url TEXT,  -- JSON массив или строка
    status VARCHAR(20) DEFAULT 'pending',  -- pending/completed/failed
    is_free BOOLEAN DEFAULT FALSE,
    custom_mode BOOLEAN DEFAULT FALSE,
    suno_task_id TEXT,  -- ID задачи в Suno
    suno_audio_id TEXT,  -- ID аудио для karaoke/cover/wav
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 🎵 Отправка результатов пользователю:
```python
# В celery_tasks.py - финальная часть каждого таска
# После успешной генерации отправляется Telegram-сообщение:

# 1. Для обычной генерации (песня/музыка):
await bot.send_message(
    user_id,
    "🎉 Твоя композиция готова!\n\n"
    "🎧 Слушай 2 демо-версии (по 45 сек):\n"
    "Для полных версий — нажми кнопку разблокировки!"
)
await bot.send_audio(user_id, demo_url_1, caption="🎵 Демо 1")
await bot.send_audio(user_id, demo_url_2, caption="🎵 Демо 2")

# Кнопки:
markup = InlineKeyboardMarkup()
markup.add(
    InlineKeyboardButton("🔓 Разблокировать (1 токен)", callback_data=f"unlock_{task_id}"),
    InlineKeyboardButton("🎤 Минусовка (1 токен)", callback_data=f"karaoke_{task_id}"),
    InlineKeyboardButton("🎸 Кавер (2 токена)", callback_data=f"cover_{task_id}"),
    InlineKeyboardButton("🔗 Отправить другу", switch_inline_query=task_id)
)
```

---

## 📱 4. ПЛАТФОРМОЗАВИСИМЫЕ ФУНКЦИИ TELEGRAM

### 4.1 ❌ Функции БЕЗ прямого веб-аналога:

#### 1️⃣ **Inline Query (Поделиться треком)**
```python
# Код бота: @dp.inline_handler() - строка 1302
# Функция: Пользователь вызывает бота в любом чате (@AlBimusic_bot)
# → Показывает список своих треков
# → Отправляет карточку с аудио другу

# ❗ Веб-замена: navigator.share() (Web Share API)
navigator.share({
    title: 'Зацени мою песню!',
    text: 'Создано в AlBi Music AI',
    url: 'https://albi-music.ru/track/{track_id}'
})
```

#### 2️⃣ **Отправка аудио-файлов через file_id**
```python
# Telegram хранит загруженные файлы, можно пересылать по file_id
await bot.send_audio(user_id, file_id="CQACAgIAAxkDAAIocWm...")

# ❗ Веб-замена: 
# - <audio> элемент с src="{audio_url}"
# - Download кнопка с blob/URL.createObjectURL()
```

#### 3️⃣ **ReplyKeyboardMarkup (Кнопки-меню)**
```python
# Стационарная клавиатура внизу экрана
markup = ReplyKeyboardMarkup(resize_keyboard=True)
markup.add(
    KeyboardButton("🎵 Создать песню"),
    KeyboardButton("💰 Баланс")
)

# ❗ Веб-замена: 
# - Нижняя навигационная панель (Bottom Navigation)
# - Плавающая кнопка действия (FAB)
```

#### 4️⃣ **InlineKeyboardMarkup (Кнопки в сообщении)**
```python
# Кнопки прикреплены к конкретному сообщению
markup = InlineKeyboardMarkup()
markup.add(
    InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
    InlineKeyboardButton("❌ Отмена", callback_data="cancel")
)

# ❗ Веб-замена:
# - Modal Dialog (снизу, как Bottom Sheet)
# - Кнопки внутри карточки трека
```

#### 5️⃣ **FSM через aiogram.dispatcher.FSMContext**
```python
# Бот запоминает состояние пользователя между сообщениями
await CreateSongStates.waiting_genre.set()
# → Следующее сообщение обрабатывается как выбор жанра

# ❗ Веб-замена:
# - React Context / Redux для состояния
# - Маршрутизация по URL (/create-song/select-genre)
# - localStorage для сохранения прогресса
```

#### 6️⃣ **Публикация в Telegram-канал**
```python
await bot.send_audio(
    chat_id="@ALBImusic_chart",
    audio=audio_url,
    caption="🎵 Новая AI-песня!"
)

# ❗ Веб-замена:
# - Интеграция с VK/OK API
# - Или просто navigator.share() для любого мессенджера
```

#### 7️⃣ **GIF-анимация при загрузке**
```python
gif_path = '/root/albimusic-bot/robot_music.gif'
await bot.send_animation(
    user_id, gif,
    caption="🎵 Генерация началась! Подождите 3-5 минут..."
)

# ❗ Веб-замена:
# - <img src="robot_music.gif"> в модальном окне
# - Lottie-анимация
# - CSS-анимация загрузки
```

### 4.2 ✅ Функции С веб-аналогом:

#### 1️⃣ **Текстовые сообщения** → Карточки/алерты
#### 2️⃣ **Callback queries** → onClick events
#### 3️⃣ **File uploads** → `<input type="file">`
#### 4️⃣ **Авторизация (user_id)** → JWT + Yandex OAuth
#### 5️⃣ **База данных** → Та же PostgreSQL
#### 6️⃣ **Платежи (ЮKassa)** → Та же интеграция
#### 7️⃣ **Celery + Suno API** → Без изменений (backend)

---

## 🗄️ 5. СХЕМА БАЗЫ ДАННЫХ (PostgreSQL)

### 5.1 Основные таблицы:

```sql
-- Пользователи
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    balance INTEGER DEFAULT 1,  -- Токены
    free_generation_used BOOLEAN DEFAULT FALSE,
    invited_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    first_menu_action_at TIMESTAMP  -- Для воронки
);

-- Генерации (история)
CREATE TABLE generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id UUID NOT NULL UNIQUE,
    prompt TEXT,
    audio_url TEXT,  -- JSON массив ["url1", "url2"]
    status VARCHAR(20) DEFAULT 'pending',
    is_free BOOLEAN DEFAULT FALSE,
    custom_mode BOOLEAN DEFAULT FALSE,
    suno_task_id TEXT,
    suno_audio_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Демо-треки (разблокировка)
CREATE TABLE demo_tracks (
    id SERIAL PRIMARY KEY,
    task_id UUID NOT NULL,
    user_id BIGINT NOT NULL,
    demo_url_1 TEXT,
    demo_url_2 TEXT,
    full_url_1 TEXT,
    full_url_2 TEXT,
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Платежи
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2),
    status VARCHAR(20),  -- pending/succeeded/failed
    payment_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Рефералы
CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,  -- Кто пригласил
    referred_id BIGINT NOT NULL,  -- Кто зарегистрировался
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(referrer_id, referred_id)
);

-- Поддержка
CREATE TABLE support_messages (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    message TEXT NOT NULL,
    replied BOOLEAN DEFAULT FALSE,
    reply_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Публикации в канал
CREATE TABLE channel_posts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    audio_url TEXT,
    comment TEXT,
    message_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## ⚡ 6. КРИТИЧЕСКИЕ ОСОБЕННОСТИ ДЛЯ АДАПТАЦИИ

### 6.1 🔥 Демо-система (ключевая фича!)
```python
# Логика разблокировки (строка 3236-3316):
# 1. Пользователь генерирует песню → Получает 2 демо (45 сек)
# 2. Чтобы получить полные версии → Платит 1 токен
# 3. После разблокировки → Доступны обе полные версии

# ❗ На вебе:
# - Демо: <audio> с ограничением currentTime <= 45
# - Или: Отдельные демо-файлы (45 сек) от Suno
# - Разблокировка: AJAX запрос → Обновление UI
```

### 6.2 📊 Воронка конверсии
```python
# Метрика: track_first_menu_action(user_id)
# Цель: Понять сколько пользователей дошло от /start до создания песни

# ❗ На вебе:
# - Аналитика через Google Analytics / Яндекс.Метрика
# - События: pageview /start → click "Создать песню" → generation_started
```

### 6.3 🎨 Локализация тегов песни
```python
# Suno API использует английские теги: [Verse], [Chorus]
# Бот показывает пользователю русские: [Куплет], [Припев]

# Перевод туда-обратно:
delocalize_lyrics_tags(lyrics)  # Куплет → Verse перед отправкой в Suno
localize_lyrics_tags(lyrics)    # Verse → Куплет при показе пользователю

# ❗ На вебе: Та же логика в frontend/backend
```

### 6.4 ⏱️ Долгий процесс генерации (3-5 минут)
```python
# В боте: Пользователь ждет, бот пришлет результат в тот же чат
# Polling через Celery каждые 10 сек

# ❗ На вебе:
# - WebSocket / Server-Sent Events для real-time обновлений
# - Прогресс-бар: "Генерация: 30%... 60%... Готово!"
# - Уведомление через browser Push Notification
# - Email/SMS уведомление (опционально)
```

### 6.5 🔐 Авторизация
```python
# В боте: user_id из Telegram (гарантированно уникален)
# Админ: ADMIN_ID = 338544009

# ❗ На вебе:
# - JWT токены после Yandex OAuth
# - Сессии в localStorage/cookie
# - Админ: Проверка роли в БД (users.is_admin)
```

---

## 📈 7. СТАТИСТИКА И АНАЛИТИКА

### 7.1 Метрики (get_admin_stats):
```python
{
    'total_users': int,           # Всего пользователей
    'new_today': int,             # Новых сегодня
    'new_7days': int,             # Новых за неделю
    'new_30days': int,            # Новых за месяц
    'generations_24h': int,       # Генераций за сутки
    'total_generations': int,     # Всего генераций
    'completed_generations': int, # Успешных
    'success_rate': float,        # % успешных
    'paid_7days': int,            # Оплаченных генераций (неделя)
    'paid_24h': int,              # Оплаченных генераций (сутки)
    'invited_today': int,         # Приглашенных сегодня
    'started_24h': int,           # Нажали /start
    'menu_24h': int,              # Дошли до меню
    'sum_24h': int,               # Сумма платежей за сутки (₽)
    'sum_7days': int,             # Сумма за неделю
    'sum_total': int,             # Сумма всего
    'count_24h': int,             # Количество платежей (сутки)
    'count_7days': int,           # Количество платежей (неделя)
    'tariffs_24h': dict           # Разбивка по тарифам
}
```

### 7.2 Запросы к БД:
```sql
-- Пример: Воронка конверсии
SELECT 
    COUNT(*) as started,
    COUNT(first_menu_action_at) as reached_menu
FROM users
WHERE created_at >= NOW() - INTERVAL '24 hours';

-- Конверсия: (reached_menu / started) * 100%
```

---

## 🎯 8. ВЫВОДЫ ДЛЯ ВЕБА

### 8.1 ЧТО ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ:
✅ **Backend:**
- PostgreSQL база данных (та же)
- Celery + RabbitMQ (та же)
- Suno API интеграция (та же)
- ЮKassa платежи (та же)
- Бизнес-логика (та же)

### 8.2 ЧТО ТРЕБУЕТ АДАПТАЦИИ:

#### 🔄 Замены Telegram-функций:
| Telegram | Веб (Mobile-First) |
|----------|-------------------|
| ReplyKeyboardMarkup | Bottom Navigation Bar |
| InlineKeyboardMarkup | Modal / Bottom Sheet |
| send_audio(file_id) | `<audio src="{url}">` |
| Inline Query | Web Share API |
| send_animation (GIF) | Loading animation |
| FSM States | React State / URL routing |
| В канал Telegram | Share в VK/OK/любой мессенджер |

#### 📱 Mobile-First UI:
- **Шаги вместо сообщений:** Каждый шаг FSM = отдельный экран
- **Bottom Sheet:** Вместо inline-кнопок
- **Swipe жесты:** Между вариантами треков
- **Карточки треков:** Вместо списка сообщений
- **Прогресс-бар:** Для генерации (3-5 минут)

#### 🔐 Авторизация:
- **Telegram user_id** → **JWT + Yandex OAuth**
- **Сессии:** localStorage + httpOnly cookies
- **Реферальная ссылка:** `?ref={user_id}` в URL

#### ⚡ Real-time updates:
- **Polling (Telegram)** → **WebSocket / SSE**
- **Push notifications** для готовности трека

---

## 📋 9. РЕЗЮМЕ ПО ШАГУ 1

### ✅ Выполнено:
1. ✅ Полный реверс-инжиниринг бота (4025 строк)
2. ✅ Дерево пользовательских сценариев (9 FSM States)
3. ✅ Карта биллинга (5 точек списания, 2 источника начисления)
4. ✅ Документация Celery + Suno API (6 endpoints)
5. ✅ Список платформозависимых функций (7 критичных)
6. ✅ Схема БД (7 таблиц)
7. ✅ Критические особенности для адаптации

### 🎯 Ключевые находки:
- **Демо-система** — главная монетизация (45 сек → 1 токен → полные версии)
- **Двухэтапная генерация текста** — AI предлагает 2 варианта
- **Автоопределение custom_mode** — по длине текста (>500 символов)
- **Перевод стиля** — с русского на английский + улучшения
- **Возврат токенов** — при ошибках генерации
- **Воронка конверсии** — отслеживание от /start до меню

---

## 🚦 ГОТОВНОСТЬ К ШАГУ 2

**Статус:** ✅ Архитектурная карта завершена  
**Ожидание:** Команда `[ОДОБРЕНО. ПЕРЕХОДИМ К ШАГУ 2]` от пользователя

**Шаг 2 будет включать:**
- GAP-анализ (что есть в боте, чего нет на вебе)
- Детальные мокапы мобильных экранов
- Карта адаптации каждой функции
- Приоритизация функций (MVP vs Full)
