#!/usr/bin/env python3
import sys
sys.path.append('.')

# Импортируем Celery приложение
from celery_tasks import celery_app

# Тестовые данные
user_id = 338544009
lyrics = "ТЕСТОВЫЙ ТЕКСТ ПЕСНИ: Солнце светит ярко, небо голубое"
style = "ТЕСТОВЫЙ СТИЛЬ: Поп-рок 80-х годов"

print(f"Отправляем тестовую задачу через celery_app...")
print(f"user_id: {user_id}")
print(f"lyrics: {lyrics}")
print(f"style: {style}")

# Отправляем задачу через celery_app
task = celery_app.send_task(
    'celery_tasks.generate_song_task',
    args=[user_id, lyrics, style],
    kwargs={},
    countdown=1
)

print(f"Задача отправлена с ID: {task.id}")
print("Проверьте логи Celery в течение 30 секунд...")
