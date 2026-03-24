#!/usr/bin/env python3
import sys
sys.path.append('.')

# Импортируем Celery задачу
from celery_tasks import generate_song_task

# Тестовые данные с ПРАВИЛЬНЫМИ параметрами
user_id = 338544009  # ID администратора
lyrics = "ТЕСТОВЫЙ ТЕКСТ ПЕСНИ: Солнце светит ярко, небо голубое"
style = "ТЕСТОВЫЙ СТИЛЬ: Поп-рок 80-х годов"

print(f"Отправляем тестовую задачу в Celery с правильными параметрами...")
print(f"user_id: {user_id}")
print(f"lyrics: {lyrics}")
print(f"style: {style}")

# Отправляем задачу с правильными параметрами
task = generate_song_task.apply_async(
    args=[user_id, lyrics, style],
    countdown=1
)

print(f"Задача отправлена с ID: {task.id}")
print("Проверьте логи Celery в течение 30 секунд...")
