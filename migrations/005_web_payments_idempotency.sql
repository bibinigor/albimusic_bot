-- 💳 БЛОК 1 (ВЕБА): Платежная система с Idempotency защитой

-- Описание: Расширяем таблицу payments для защиты от двойного начисления
-- и добавляем поддержку ЮKassa webhook на веб-версии.
--
-- Проблема: При сбое webhook может прийти повторно → риск двойного начисления токенов
-- Решение: Таблица processed_payments + idempotent начисление через CHECK constraint
--
-- Логика работы:
-- 1. Пользователь создает платеж → payments.status = 'pending'
-- 2. ЮKassa webhook подтверждает → проверяем processed_payments
-- 3. Если payment_id уже есть → игнорируем (idempotency)
-- 4. Если нет → начисляем токены + записываем в processed_payments

-- Шаг 1: Расширяем таблицу payments
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS tokens_amount INTEGER,
ADD COLUMN IF NOT EXISTS provider VARCHAR(50) DEFAULT 'yookassa',
ADD COLUMN IF NOT EXISTS metadata JSONB,
ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

-- Шаг 2: Создаем таблицу для защиты от повторной обработки
CREATE TABLE IF NOT EXISTS processed_payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(255) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    tokens_credited INTEGER NOT NULL,
    provider VARCHAR(50) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Индексы для быстрой проверки idempotency
CREATE INDEX IF NOT EXISTS idx_processed_payments_payment_id ON processed_payments(payment_id);
CREATE INDEX IF NOT EXISTS idx_processed_payments_user_id ON processed_payments(user_id);
CREATE INDEX IF NOT EXISTS idx_processed_payments_created ON processed_payments(processed_at);

-- Индексы для payments
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_processed ON payments(processed);
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);

-- Шаг 3: Добавляем constraint для защиты от дублирования
-- (payment_id должен быть уникальным в processed_payments)
ALTER TABLE processed_payments
ADD CONSTRAINT unique_payment_id UNIQUE (payment_id);

-- Комментарии
COMMENT ON TABLE processed_payments IS 'Идемпотентность платежей - защита от повторной обработки webhook';
COMMENT ON COLUMN processed_payments.payment_id IS 'Уникальный ID платежа от ЮKassa/другого провайдера';
COMMENT ON COLUMN processed_payments.tokens_credited IS 'Сколько токенов было начислено за этот платеж';
COMMENT ON COLUMN payments.tokens_amount IS 'Количество токенов, которые должны быть начислены';
COMMENT ON COLUMN payments.provider IS 'Платежный провайдер: yookassa, yoomoney, stripe';
COMMENT ON COLUMN payments.metadata IS 'Дополнительные данные платежа (JSON)';
COMMENT ON COLUMN payments.processed IS 'Обработан ли webhook (начислены ли токены)';

-- Шаг 4: Создаем функцию для атомарного начисления токенов с проверкой idempotency
CREATE OR REPLACE FUNCTION process_payment_idempotent(
    p_payment_id VARCHAR(255),
    p_user_id BIGINT,
    p_amount DECIMAL(10,2),
    p_tokens INTEGER,
    p_provider VARCHAR(50)
) RETURNS BOOLEAN AS $$
DECLARE
    v_already_processed BOOLEAN;
BEGIN
    -- Проверяем, обрабатывался ли уже этот платеж
    SELECT EXISTS(
        SELECT 1 FROM processed_payments WHERE payment_id = p_payment_id
    ) INTO v_already_processed;
    
    -- Если уже обработан, возвращаем FALSE (idempotency)
    IF v_already_processed THEN
        RETURN FALSE;
    END IF;
    
    -- Начинаем транзакцию (атомарно)
    -- 1. Начисляем токены пользователю
    UPDATE users 
    SET balance = balance + p_tokens,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
    
    -- 2. Записываем в processed_payments (для idempotency)
    INSERT INTO processed_payments (payment_id, user_id, amount, tokens_credited, provider)
    VALUES (p_payment_id, p_user_id, p_amount, p_tokens, p_provider);
    
    -- 3. Обновляем статус платежа
    UPDATE payments
    SET status = 'succeeded',
        processed = TRUE,
        confirmed_at = CURRENT_TIMESTAMP,
        tokens_amount = p_tokens
    WHERE payment_id = p_payment_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION process_payment_idempotent IS 'Атомарное начисление токенов с защитой от повторной обработки (idempotency)';

-- Шаг 5: Создаем таблицу для тарифных планов (pricelist)
CREATE TABLE IF NOT EXISTS pricing_plans (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL,
    tokens INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем текущие тарифы из бота
INSERT INTO pricing_plans (amount, tokens, currency) VALUES
    (50.00, 1, 'RUB'),
    (250.00, 10, 'RUB'),
    (500.00, 25, 'RUB'),
    (1000.00, 60, 'RUB'),
    (2000.00, 140, 'RUB')
ON CONFLICT DO NOTHING;

COMMENT ON TABLE pricing_plans IS 'Тарифные планы для покупки токенов';
COMMENT ON COLUMN pricing_plans.amount IS 'Стоимость в рублях';
COMMENT ON COLUMN pricing_plans.tokens IS 'Количество токенов за эту сумму';
