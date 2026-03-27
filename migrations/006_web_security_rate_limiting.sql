-- 🔒 БЛОК 1 (ВЕБА): Безопасность биллинга и Rate Limiting

-- Описание: Защита от накруток генераций и спама через БД-уровень
-- Веб-версия более уязвима к атакам через API, чем Telegram-бот.
--
-- Проблемы:
-- 1. Race condition при списании токенов (два запроса одновременно)
-- 2. Спам генераций (можно создать 100 запросов за секунду)
-- 3. Обход оплаты (генерация без списания токенов)
--
-- Решения:
-- 1. Атомарное списание через UPDATE ... WHERE balance >= cost
-- 2. Таблица user_actions для rate limiting
-- 3. CHECK constraint на баланс (не может быть отрицательным)

-- Шаг 1: Добавляем CHECK constraint для баланса (не может быть < 0)
ALTER TABLE users
DROP CONSTRAINT IF EXISTS check_balance_non_negative;

ALTER TABLE users
ADD CONSTRAINT check_balance_non_negative CHECK (balance >= 0);

COMMENT ON CONSTRAINT check_balance_non_negative ON users 
IS 'Баланс не может быть отрицательным (защита от race condition)';

-- Шаг 2: Создаем функцию для атомарного списания токенов
CREATE OR REPLACE FUNCTION deduct_tokens_atomic(
    p_user_id BIGINT,
    p_cost INTEGER,
    p_action_type VARCHAR(50)
) RETURNS BOOLEAN AS $$
DECLARE
    v_rows_affected INTEGER;
BEGIN
    -- Атомарное списание: обновляем только если баланс достаточный
    UPDATE users
    SET balance = balance - p_cost,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id 
      AND balance >= p_cost;
    
    GET DIAGNOSTICS v_rows_affected = ROW_COUNT;
    
    -- Если обновление прошло успешно (баланс был достаточный)
    IF v_rows_affected > 0 THEN
        -- Логируем транзакцию
        INSERT INTO token_transactions (user_id, amount, transaction_type, description)
        VALUES (p_user_id, -p_cost, 'debit', p_action_type);
        
        RETURN TRUE;
    ELSE
        -- Недостаточно токенов
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION deduct_tokens_atomic IS 'Атомарное списание токенов с защитой от race condition';

-- Шаг 3: Создаем таблицу для логирования транзакций токенов
CREATE TABLE IF NOT EXISTS token_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- 'debit', 'credit', 'refund'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_token_transactions_user_id ON token_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_token_transactions_type ON token_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_token_transactions_created ON token_transactions(created_at);

COMMENT ON TABLE token_transactions IS 'История транзакций токенов (для аудита баланса)';
COMMENT ON COLUMN token_transactions.transaction_type IS 'Тип: debit (списание), credit (пополнение), refund (возврат)';

-- Шаг 4: Создаем таблицу для rate limiting
CREATE TABLE IF NOT EXISTS user_actions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'generate_song', 'generate_music', 'generate_cover', etc.
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_type ON user_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_user_actions_created ON user_actions(created_at);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_time ON user_actions(user_id, created_at);

COMMENT ON TABLE user_actions IS 'Логирование действий пользователя (для rate limiting и аналитики)';
COMMENT ON COLUMN user_actions.action_type IS 'Тип действия: generate_song, unlock_track, create_payment';

-- Шаг 5: Создаем функцию для проверки rate limit
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_user_id BIGINT,
    p_action_type VARCHAR(50),
    p_max_requests INTEGER DEFAULT 5,
    p_time_window_minutes INTEGER DEFAULT 1
) RETURNS BOOLEAN AS $$
DECLARE
    v_action_count INTEGER;
BEGIN
    -- Считаем количество действий за последний time_window
    SELECT COUNT(*)
    INTO v_action_count
    FROM user_actions
    WHERE user_id = p_user_id
      AND action_type = p_action_type
      AND created_at > CURRENT_TIMESTAMP - (p_time_window_minutes || ' minutes')::INTERVAL;
    
    -- Если превышен лимит
    IF v_action_count >= p_max_requests THEN
        RETURN FALSE;
    END IF;
    
    -- Логируем действие
    INSERT INTO user_actions (user_id, action_type)
    VALUES (p_user_id, p_action_type);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_rate_limit IS 'Проверка rate limit: max N запросов за M минут';

-- Шаг 6: Создаем задачу для очистки старых логов (опционально, через cron)
-- Удаляем записи user_actions старше 7 дней
CREATE OR REPLACE FUNCTION cleanup_old_user_actions() RETURNS void AS $$
BEGIN
    DELETE FROM user_actions
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_user_actions IS 'Очистка старых записей user_actions (запускать через cron)';

-- Шаг 7: Добавляем поле для отслеживания генераций в процессе (защита от спама)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS active_generations INTEGER DEFAULT 0;

COMMENT ON COLUMN users.active_generations IS 'Количество генераций в процессе (для защиты от спама)';

-- Шаг 8: Создаем функцию для начала генерации (с проверкой лимита)
CREATE OR REPLACE FUNCTION start_generation_safe(
    p_user_id BIGINT,
    p_cost INTEGER,
    p_max_concurrent INTEGER DEFAULT 3
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_active INTEGER;
    v_deducted BOOLEAN;
BEGIN
    -- Проверяем текущее количество активных генераций
    SELECT active_generations INTO v_current_active
    FROM users
    WHERE user_id = p_user_id;
    
    -- Если превышен лимит одновременных генераций
    IF v_current_active >= p_max_concurrent THEN
        RETURN FALSE;
    END IF;
    
    -- Списываем токены атомарно
    SELECT deduct_tokens_atomic(p_user_id, p_cost, 'generation_start') INTO v_deducted;
    
    IF NOT v_deducted THEN
        RETURN FALSE;
    END IF;
    
    -- Увеличиваем счетчик активных генераций
    UPDATE users
    SET active_generations = active_generations + 1
    WHERE user_id = p_user_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION start_generation_safe IS 'Безопасное начало генерации: списание токенов + проверка concurrent limit';

-- Шаг 9: Создаем функцию для завершения генерации
CREATE OR REPLACE FUNCTION finish_generation(
    p_user_id BIGINT
) RETURNS void AS $$
BEGIN
    -- Уменьшаем счетчик активных генераций
    UPDATE users
    SET active_generations = GREATEST(0, active_generations - 1)
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION finish_generation IS 'Завершение генерации: уменьшаем счетчик active_generations';

-- Шаг 10: Создаем функцию для возврата токенов при ошибке
CREATE OR REPLACE FUNCTION refund_tokens(
    p_user_id BIGINT,
    p_amount INTEGER,
    p_reason TEXT
) RETURNS void AS $$
BEGIN
    -- Возвращаем токены
    UPDATE users
    SET balance = balance + p_amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
    
    -- Логируем транзакцию
    INSERT INTO token_transactions (user_id, amount, transaction_type, description)
    VALUES (p_user_id, p_amount, 'refund', p_reason);
    
    -- Уменьшаем счетчик активных генераций
    PERFORM finish_generation(p_user_id);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refund_tokens IS 'Возврат токенов при ошибке генерации';
