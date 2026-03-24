-- Добавление недостающих индексов для оптимизации PostgreSQL
-- 1. Индекс на task_id для быстрого поиска задач
CREATE INDEX IF NOT EXISTS idx_generations_task_id ON generations(task_id);

-- 2. Композитный индекс на user_id и created_at для истории пользователя
CREATE INDEX IF NOT EXISTS idx_generations_user_created ON generations(user_id, created_at DESC);

-- 3. Композитный индекс на status и created_at для очистки старых записей
CREATE INDEX IF NOT EXISTS idx_generations_status_created ON generations(status, created_at);

-- 4. Также добавим индекс на audio_url для быстрого поиска завершенных задач
CREATE INDEX IF NOT EXISTS idx_generations_audio_url ON generations(audio_url) WHERE audio_url IS NOT NULL;

-- Показать созданные индексы
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'generations' 
ORDER BY indexname;
