#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import generate_song_task

print("=== ТЕСТ ИСПРАВЛЕННОГО КОДА ===")
print("Проверка передачи стиля и текста в Suno API")

user_id = 338544009
lyrics = "ТЕСТ_ТЕКСТ_2025: Солнце светит очень ярко"
style = "ТЕСТ_СТИЛЬ_2025: Хард-рок с гитарным соло"

print(f"Стиль: {style}")
print(f"Текст: {lyrics}")
print(f"Будет отправлено в Suno: '{style}. {lyrics}'")

task = generate_song_task.delay(user_id, lyrics, style, custom_mode=False)
print(f"\nЗадача отправлена: {task.id}")
print("Ожидайте 5-7 минут...")
print("Проверьте результат в Telegram.")
print("Текст должен содержать 'ТЕСТ_ТЕКСТ_2025'")
print("Музыка должна соответствовать 'ТЕСТ_СТИЛЬ_2025: Хард-рок с гитарным соло'")
