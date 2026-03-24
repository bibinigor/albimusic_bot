#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import generate_song_task
import time

print("=== СОЗДАНИЕ ТЕСТОВОЙ ПЕСНИ С ОТСЛЕЖИВАНИЕМ ===")

# Ваш ID пользователя
user_id = 338544009

# ОЧЕНЬ четкие параметры для теста
lyrics = "ТЕКСТ_ДЛЯ_ПРОВЕРКИ_12345: Солнце светит, птицы поют, трава зеленая"
style = "СТИЛЬ_ДЛЯ_ПРОВЕРКИ_67890: Хеви-метал с оркестром"

print(f"Ваш user_id: {user_id}")
print(f"Текст песни (должен быть в результате): {lyrics}")
print(f"Стиль музыки (должен быть в результате): {style}")

print("\nОтправляю задачу в Celery...")
task = generate_song_task.delay(user_id, lyrics, style, custom_mode=False)

print(f"ID задачи: {task.id}")
print(f"Начальный статус: {task.status}")

print("\nОжидайте 5-7 минут...")
print("Вы должны получить уведомление в Telegram с результатом.")
print("Проверьте, поет ли результат текст 'ТЕКСТ_ДЛЯ_ПРОВЕРКИ_12345'")
print("и соответствует ли музыка 'СТИЛЬ_ДЛЯ_ПРОВЕРКИ_67890: Хеви-метал с оркестром'")

# Сохраним ID для проверки
with open('/tmp/last_task_id.txt', 'w') as f:
    f.write(task.id)
    
print(f"\nID задачи сохранен в /tmp/last_task_id.txt")
