#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app

# Тестовые данные
user_id = 338544009
lyrics = "ФИНАЛЬНЫЙ ТЕСТ ТЕКСТА: Солнце светит ярко"
style = "ФИНАЛЬНЫЙ ТЕСТ СТИЛЯ: Рок-баллада"

print("=== ТЕСТ ОТПРАВКИ ЗАДАЧИ ===")
print(f"user_id: {user_id}")
print(f"lyrics: {lyrics}")
print(f"style: {style}")

# Отправляем задачу как это делает бот
from celery_tasks import generate_song_task
result = generate_song_task.delay(user_id, lyrics, style)

print(f"\nЗадача отправлена!")
print(f"ID задачи: {result.id}")
print(f"Статус: {result.status}")
print("\nПроверьте логи Celery в течение 30 секунд...")
