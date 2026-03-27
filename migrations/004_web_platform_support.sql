-- 🌐 БЛОК 1 (ВЕБА): Кросс-платформенная поддержка (Telegram + Yandex + VK)

-- Описание: Расширяем таблицу users для поддержки веб-авторизации
-- через Яндекс и VK ID SDK, сохраняя совместимость с Telegram-ботом.
--
-- Логика:
-- 1. user_id остается основным идентификатором (для Telegram это telegram_id)
-- 2. Для веб-пользователей user_id генерируется как hash от oauth_id
-- 3. provider указывает на источник: 'telegram', 'yandex', 'vk'
-- 4. oauth_id хранит внешний ID от провайдера
-- 5. Возможна связка аккаунтов (один user_id + несколько провайдеров)

-- Шаг 1: Добавляем колонки для мульти-провайдерной авторизации
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS provider VARCHAR(20) DEFAULT 'telegram',
ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS email VARCHAR(255),
ADD COLUMN IF NOT EXISTS full_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_web_user BOOLEAN DEFAULT FALSE;

-- Шаг 2: Создаем индекс для быстрого поиска по провайдеру
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider);
CREATE INDEX IF NOT EXISTS idx_users_oauth_id ON users(oauth_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_web ON users(is_web_user);

-- Шаг 3: Создаем уникальный индекс для комбинации provider+oauth_id
-- (один и тот же пользователь VK не может зарегистрироваться дважды)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_provider_oauth 
ON users(provider, oauth_id) 
WHERE oauth_id IS NOT NULL;

-- Шаг 4: Обновляем существующих пользователей (Telegram)
UPDATE users 
SET provider = 'telegram', 
    oauth_id = user_id::VARCHAR,
    is_web_user = FALSE
WHERE provider IS NULL OR provider = 'telegram';

-- Комментарии к колонкам
COMMENT ON COLUMN users.provider IS 'Источник авторизации: telegram, yandex, vk';
COMMENT ON COLUMN users.oauth_id IS 'Внешний ID от OAuth провайдера (для связки аккаунтов)';
COMMENT ON COLUMN users.email IS 'Email пользователя (для Yandex/VK)';
COMMENT ON COLUMN users.full_name IS 'Полное имя пользователя';
COMMENT ON COLUMN users.avatar_url IS 'URL аватара пользователя';
COMMENT ON COLUMN users.last_login_at IS 'Время последнего входа';
COMMENT ON COLUMN users.is_web_user IS 'Пользователь зарегистрировался через веб (TRUE) или бота (FALSE)';

-- Шаг 5: Создаем таблицу для связки аккаунтов (опционально, для будущего)
CREATE TABLE IF NOT EXISTS user_accounts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    provider VARCHAR(20) NOT NULL,
    oauth_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(provider, oauth_id)
);

CREATE INDEX IF NOT EXISTS idx_user_accounts_user_id ON user_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_provider ON user_accounts(provider);

COMMENT ON TABLE user_accounts IS 'Связанные аккаунты пользователя (для кросс-платформенной идентификации)';
COMMENT ON COLUMN user_accounts.user_id IS 'Основной ID пользователя в системе';
COMMENT ON COLUMN user_accounts.provider IS 'Провайдер: telegram, yandex, vk';
COMMENT ON COLUMN user_accounts.oauth_id IS 'ID от внешнего провайдера';
