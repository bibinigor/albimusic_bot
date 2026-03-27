-- 🔴 БЛОК 4: Таблица для реферальной системы

-- Описание: Таблица referrals хранит информацию о реферальных связях
--
-- Логика работы:
-- 1. Новый пользователь открывает бота по ссылке ?ref=ref_{referrer_id}
-- 2. При регистрации создается запись в referrals
-- 3. Реферер получает 2 токена за приглашение
-- 4. После 5-го приглашенного реферер получает бонус +5 токенов (итого 7 за 5-го)

CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL UNIQUE,
    bonus_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (referred_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Constraint: пользователь не может пригласить сам себя
    CONSTRAINT check_not_self_referral CHECK (referrer_id != referred_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);
CREATE INDEX IF NOT EXISTS idx_referrals_bonus_paid ON referrals(bonus_paid);

-- Комментарии к таблице
COMMENT ON TABLE referrals IS 'Реферальные связи между пользователями';
COMMENT ON COLUMN referrals.referrer_id IS 'ID пользователя, который пригласил (реферер)';
COMMENT ON COLUMN referrals.referred_id IS 'ID приглашенного пользователя (реферал)';
COMMENT ON COLUMN referrals.bonus_paid IS 'Выплачен ли бонус реферу (2 токена при регистрации + 5 за 5-го)';

-- Добавляем поля в таблицу users (если их нет)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS invited_by BIGINT;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS referral_bonus_given BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN users.invited_by IS 'ID пользователя, который пригласил (для обратной совместимости)';
COMMENT ON COLUMN users.referral_bonus_given IS 'Получен ли бонус за 5-го реферала';
