-- Таблица для генерации изображений через Replicate
CREATE TABLE IF NOT EXISTS image_generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id UUID UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    aspect_ratio VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    cost_tokens INTEGER NOT NULL DEFAULT 1,
    image_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_image_generations_user_id ON image_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_image_generations_status ON image_generations(status);
CREATE INDEX IF NOT EXISTS idx_image_generations_task_id ON image_generations(task_id);

-- Права для пользователя
GRANT ALL PRIVILEGES ON TABLE image_generations TO albimusic_user;
GRANT USAGE, SELECT ON SEQUENCE image_generations_id_seq TO albimusic_user;
