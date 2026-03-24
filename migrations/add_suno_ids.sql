-- Migration: Add Suno API IDs to generations table
-- Purpose: Store Suno taskId and audioId for video/karaoke generation
-- Date: 2026-02-06

-- Add columns for Suno identifiers
ALTER TABLE generations ADD COLUMN IF NOT EXISTS suno_task_id TEXT;
ALTER TABLE generations ADD COLUMN IF NOT EXISTS suno_audio_id TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_generations_suno_task_id ON generations(suno_task_id);

-- Comment
COMMENT ON COLUMN generations.suno_task_id IS 'Suno API task ID for this generation';
COMMENT ON COLUMN generations.suno_audio_id IS 'Suno API audio ID (first track) for video/karaoke generation';
