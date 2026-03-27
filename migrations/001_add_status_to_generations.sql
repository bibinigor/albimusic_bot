-- 🔴 БЛОК 1: Миграция базы данных
-- Добавление поля status в таблицу generations

-- Описание: Поле status позволяет отслеживать состояние генерации:
-- - 'pending' - генерация запущена, ожидает результата
-- - 'completed' - генерация завершена успешно
-- - 'failed' - генерация завершилась ошибкой

-- Добавляем поле status
ALTER TABLE generations 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed';

-- Создаем индекс для быстрого поиска по статусу
CREATE INDEX IF NOT EXISTS idx_generations_status ON generations(status);

-- Создаем индекс для поиска pending задач конкретного пользователя
CREATE INDEX IF NOT EXISTS idx_generations_user_status ON generations(user_id, status);

-- Обновляем существующие записи (у которых status = NULL)
UPDATE generations 
SET status = 'completed' 
WHERE status IS NULL AND audio_url IS NOT NULL;

UPDATE generations 
SET status = 'failed' 
WHERE status IS NULL AND audio_url IS NULL;

-- Комментарий к таблице
COMMENT ON COLUMN generations.status IS 'Статус генерации: pending, completed, failed';
