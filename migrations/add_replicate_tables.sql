-- Миграция для добавления таблиц Replicate функций
-- Дата: 18.03.2026

-- Таблица для генерации видео
CREATE TABLE IF NOT EXISTS video_generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    audio_url TEXT,
    duration INT NOT NULL,  -- 5 или 10 секунд
    video_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    cost_tokens INT NOT NULL,  -- 2 или 3 токена
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_video_user ON video_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_video_status ON video_generations(status);
CREATE INDEX IF NOT EXISTS idx_video_task ON video_generations(task_id);

-- Таблица для операций с фото
CREATE TABLE IF NOT EXISTS photo_operations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    operation_type VARCHAR(50) NOT NULL,  -- 'animate', 'dance', 'upscale', 'remove_bg'
    input_url TEXT NOT NULL,
    input_url_2 TEXT,  -- для dance (видео с танцем)
    output_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    cost_tokens INT NOT NULL,  -- 1 или 2 токена
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_photo_user ON photo_operations(user_id);
CREATE INDEX IF NOT EXISTS idx_photo_type ON photo_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_photo_status ON photo_operations(status);
CREATE INDEX IF NOT EXISTS idx_photo_task ON photo_operations(task_id);

-- Таблица для генерации изображений
CREATE TABLE IF NOT EXISTS image_generations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    aspect_ratio VARCHAR(10) NOT NULL,  -- '1:1', '9:16', '16:9', '3:4', '4:3'
    image_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    cost_tokens INT DEFAULT 1,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_image_user ON image_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_image_status ON image_generations(status);
CREATE INDEX IF NOT EXISTS idx_image_task ON image_generations(task_id);

-- Обновление таблицы users - добавляем счетчики
ALTER TABLE users ADD COLUMN IF NOT EXISTS videos_created INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS photos_processed INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS images_generated INT DEFAULT 0;

-- Комментарии к таблицам
COMMENT ON TABLE video_generations IS 'Генерация видео через Runway Gen-3';
COMMENT ON TABLE photo_operations IS 'Операции с фото: анимация, танец, апскейл, удаление фона';
COMMENT ON TABLE image_generations IS 'Генерация изображений через FLUX';

-- Проверка создания таблиц
DO $$
BEGIN
    RAISE NOTICE '✅ Миграция выполнена успешно!';
    RAISE NOTICE 'Создано таблиц: video_generations, photo_operations, image_generations';
END $$;
