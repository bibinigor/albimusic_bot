#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import celery_app

# Тестовые данные
user_id = 999888777
lyrics = "ПРЯМАЯ ОТПРАВКА: Текст песни для теста"
style = "ПРЯМАЯ ОТПРАВКА: Рок-стиль"

print("=== ПРЯМАЯ ОТПРАВКА ЧЕРЕЗ CELERY_APP ===")

# Отправляем задачу напрямую
result = celery_app.send_task(
    'celery_tasks.generate_song_task',
    args=[user_id, lyrics, style],
    kwargs={'custom_mode': False}
)

print(f"Задача отправлена: {result.id}")

# Проверим через inspect
i = celery_app.control.inspect()
active = i.active()
scheduled = i.scheduled()
reserved = i.reserved()

print(f"\nСтатус через inspect:")
print(f"  Активные задачи: {active}")
print(f"  Запланированные: {scheduled}")
print(f"  Зарезервированные: {reserved}")

# Подождем немного и проверим статус
import time
time.sleep(2)
print(f"\nСтатус задачи через 2 секунды: {result.status}")
