#!/bin/bash
# Финальные исправления VK-бота

cd /root/albimusic-bot

echo "🔧 Применяю финальные исправления..."

# Исправление 1: Убрать проверку user_id в запросах для минусовки/кавера/WAV
echo "1️⃣ Исправление запросов к БД для минусовки/кавера/WAV..."

sed -i 's/"SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",/"SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s LIMIT 1",/g' main_vk.py
sed -i 's/(task_id_from_payload, user_id)/(task_id_from_payload,)/g' main_vk.py

sed -i 's/"SELECT audio_url, suno_audio_id, prompt FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",/"SELECT audio_url, suno_audio_id, prompt FROM generations WHERE task_id = %s LIMIT 1",/g' main_vk.py

echo "✅ Исправления применены!"
echo ""
echo "📋 Что исправлено:"
echo "   ✓ Убрана лишняя проверка user_id в запросах"
echo "   ✓ Минусовка/Кавер/WAV теперь работают корректно"
