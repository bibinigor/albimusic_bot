CREATE TABLE IF NOT EXISTS channel_posts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    audio_url TEXT NOT NULL,
    comment TEXT,
    message_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
