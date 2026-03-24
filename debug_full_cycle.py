#!/usr/bin/env python3
import sys
sys.path.append('.')

from celery_tasks import generate_song_task
import redis
import time

print("=== ПОЛНЫЙ ЦИКЛ ДИАГНОСТИКИ ===")
print("Время начала: ", time.strftime("%H:%M:%S"))

user_id = 338544009
lyrics = "ДИАГНОСТИКА_ЦИКЛА: Текст для проверки полного цикла"
style = "ДИАГНОСТИКА_ЦИКЛА: Хеви-метал"

print(f"User ID: {user_id}")
print(f"Lyrics: {lyrics}")
print(f"Style: {style}")
print(f"Prompt для Suno: '{style}. {lyrics}'")

# Отправляем задачу
task = generate_song_task.delay(user_id, lyrics, style, custom_mode=False)
task_id = task.id
print(f"\n✅ Задача отправлена в Celery")
print(f"Task ID: {task_id}")
print(f"Статус: {task.status}")

# Проверяем Redis
r = redis.Redis(host='localhost', port=6379, db=0)
print(f"\n📊 Redis проверка:")
print(f"Очередь 'celery': {r.llen('celery')}")
print(f"Ключ задачи существует: {r.exists(f'celery-task-meta-{task_id}')}")

# Мониторим 10 минут
print(f"\n⏱️  Мониторинг выполнения (каждые 30 секунд):")
for i in range(20):  # 20 * 30 сек = 10 минут
    time.sleep(30)
    status = task.status
    print(f"{i+1}. {time.strftime('%H:%M:%S')} - Статус: {status}")
    
    if status == 'SUCCESS':
        print("🎉 Задача завершена успешно!")
        result = task.result
        print(f"Результат: {result}")
        break
    elif status == 'FAILURE':
        print("❌ Задача завершилась с ошибкой!")
        try:
            result = task.result
            print(f"Ошибка: {result}")
        except:
            print("Не удалось получить детали ошибки")
        break

if task.status == 'PENDING':
    print(f"\n⚠️  ВНИМАНИЕ: Задача все еще PENDING после 10 минут!")
    print("Возможные проблемы:")
    print("1. Celery Worker не обрабатывает задачи")
    print("2. Suno API не отвечает")
    print("3. Ошибка в функции generate_song_task")
    print("4. Проблемы с подключением к БД")

print(f"\n📋 Итог в {time.strftime('%H:%M:%S')}:")
print(f"Финальный статус: {task.status}")
