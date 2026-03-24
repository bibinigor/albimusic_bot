#!/usr/bin/env python3
import sys
sys.path.append('.')

# Импортируем Celery задачу
from celery_tasks import generate_song_task

# Тестовые данные
user_id = 338544009  # ID администратора
generation_id = 999999
text = "ТЕСТОВЫЙ ТЕКСТ: Солнце светит ярко, небо голубое"
style = "ТЕСТОВЫЙ СТИЛЬ: Поп-рок 80-х годов"

print(f"Отправляем тестовую задачу в Celery...")
print(f"user_id: {user_id}")
print(f"generation_id: {generation_id}")
print(f"text: {text}")
print(f"style: {style}")

# Отправляем задачу
task = generate_song_task.apply_async(
    args=[user_id, generation_id, text, style],
    countdown=1
)

print(f"Задача отправлена с ID: {task.id}")
print("Проверьте логи Celery в течение 30 секунд...")
