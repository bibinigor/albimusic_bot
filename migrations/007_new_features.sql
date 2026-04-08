-- Migration 007: New features (subscription bonus, novice offer, friday broadcast)
-- Date: 2026-04-04

-- Бонус за подписку на канал (одноразовый)
ALTER TABLE users ADD COLUMN IF NOT EXISTS channel_bonus_used BOOLEAN DEFAULT FALSE;

-- Оффер «Новичок» через 3 минуты после первой песни
ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_offer_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_offer_pending_at TIMESTAMP DEFAULT NULL;

-- Пятничная рассылка (одноразовая)
ALTER TABLE users ADD COLUMN IF NOT EXISTS friday_broadcast_sent BOOLEAN DEFAULT FALSE;

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_users_novice_offer_pending ON users (novice_offer_pending_at) WHERE novice_offer_pending_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_friday_not_sent ON users (friday_broadcast_sent) WHERE friday_broadcast_sent = FALSE;
