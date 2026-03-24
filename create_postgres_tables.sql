-- Создание таблиц для AlBi-music Bot

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    free_generation_used BOOLEAN DEFAULT FALSE,
    invited_by BIGINT DEFAULT NULL,
    balance INTEGER DEFAULT 0
);

-- Таблица генераций
CREATE TABLE IF NOT EXISTS generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    task_id TEXT,
    prompt TEXT,
    audio_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_free BOOLEAN DEFAULT FALSE,
    custom_mode BOOLEAN DEFAULT FALSE
);

-- Таблица рефералов
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT REFERENCES users(user_id),
    referred_id BIGINT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bonus_applied BOOLEAN DEFAULT FALSE
);

-- Таблица платежей
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    amount REAL,
    status TEXT,
    payment_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица токенов пользователей
CREATE TABLE IF NOT EXISTS user_tokens (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
    access_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица публикаций в канал
CREATE TABLE IF NOT EXISTS channel_posts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    audio_url TEXT,
    comment TEXT,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_id INTEGER
);

-- Индексы для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_created_at ON generations(created_at);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);

