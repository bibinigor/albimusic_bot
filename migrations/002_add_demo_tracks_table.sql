-- 🔴 БЛОК 2: Таблица для демо-системы разблокировки

-- Описание: Таблица demo_tracks хранит информацию о демо-версиях треков
-- и статусе их разблокировки пользователями.
--
-- Логика работы:
-- 1. При генерации трека создается demo_track с is_unlocked = FALSE
-- 2. Пользователю отправляются 2 URL (демо 45 сек)
-- 3. Пользователь может разблокировать за 1 токен → is_unlocked = TRUE
-- 4. После разблокировки доступны полные версии (full_url_1, full_url_2)

CREATE TABLE IF NOT EXISTS demo_tracks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    
    -- Демо-версии (45 секунд) - отправляются сразу
    demo_url_1 TEXT,
    demo_url_2 TEXT,
    
    -- Полные версии (разблокируются за 1 токен)
    full_url_1 TEXT,
    full_url_2 TEXT,
    
    -- Статус разблокировки
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_demo_tracks_task_id ON demo_tracks(task_id);
CREATE INDEX IF NOT EXISTS idx_demo_tracks_user_id ON demo_tracks(user_id);
CREATE INDEX IF NOT EXISTS idx_demo_tracks_unlocked ON demo_tracks(is_unlocked);
CREATE INDEX IF NOT EXISTS idx_demo_tracks_user_unlocked ON demo_tracks(user_id, is_unlocked);

-- Комментарии к таблице
COMMENT ON TABLE demo_tracks IS 'Демо-версии треков с системой разблокировки';
COMMENT ON COLUMN demo_tracks.demo_url_1 IS 'Демо-версия 1 (45 сек) - бесплатно';
COMMENT ON COLUMN demo_tracks.demo_url_2 IS 'Демо-версия 2 (45 сек) - бесплатно';
COMMENT ON COLUMN demo_tracks.full_url_1 IS 'Полная версия 1 - доступна после разблокировки';
COMMENT ON COLUMN demo_tracks.full_url_2 IS 'Полная версия 2 - доступна после разблокировки';
COMMENT ON COLUMN demo_tracks.is_unlocked IS 'Разблокирован ли трек (TRUE = пользователь заплатил 1 токен)';
COMMENT ON COLUMN demo_tracks.unlocked_at IS 'Дата и время разблокировки';

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_demo_tracks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_demo_tracks_updated_at
    BEFORE UPDATE ON demo_tracks
    FOR EACH ROW
    EXECUTE FUNCTION update_demo_tracks_updated_at();
