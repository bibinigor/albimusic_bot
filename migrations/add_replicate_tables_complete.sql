-- 1. Таблица для видео
CREATE TABLE IF NOT EXISTS video_generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id UUID UNIQUE NOT NULL,
    audio_url TEXT NOT NULL,
    duration INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    cost_tokens INTEGER NOT NULL,
    video_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 2. Таблица для фото операций
CREATE TABLE IF NOT EXISTS photo_operations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id UUID UNIQUE NOT NULL,
    operation_type VARCHAR(20) NOT NULL,
    input_url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    cost_tokens INTEGER NOT NULL,
    output_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Права для пользователя на все таблицы
GRANT ALL PRIVILEGES ON TABLE video_generations TO albimusic_user;
GRANT ALL PRIVILEGES ON TABLE photo_operations TO albimusic_user;
GRANT ALL PRIVILEGES ON TABLE image_generations TO albimusic_user;

-- Права на sequences
GRANT USAGE, SELECT ON SEQUENCE video_generations_id_seq TO albimusic_user;
GRANT USAGE, SELECT ON SEQUENCE photo_operations_id_seq TO albimusic_user;
GRANT USAGE, SELECT ON SEQUENCE image_generations_id_seq TO albimusic_user;

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_video_generations_user_id ON video_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_video_generations_status ON video_generations(status);
CREATE INDEX IF NOT EXISTS idx_photo_operations_user_id ON photo_operations(user_id);
CREATE INDEX IF NOT EXISTS idx_photo_operations_status ON photo_operations(status);
