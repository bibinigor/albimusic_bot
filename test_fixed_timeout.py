#!/usr/bin/env python3
import sys
sys.path.append('.')
from celery_tasks import generate_song_task
import time

print("=== ТЕСТ С УВЕЛИЧЕННЫМИ ТАЙМАУТАМИ ===")
task = generate_song_task.delay(999888, 'ТЕСТ новых таймаутов', 'СТИЛЬ тест', False)
print(f"Задача: {task.id}")

# Мониторим 10 минут с прогрессом
for i in range(60):  # 60 * 10 секунд = 10 минут
    time.sleep(10)
    status = task.status
    print(f"{i+1}. Через {(i+1)*10} сек: Статус = {status}")
    
    if status != 'PENDING':
        print(f"✅ Задача завершена со статусом: {status}")
        if status == 'SUCCESS':
            print(f"Результат: {task.result}")
        break
        
    if i >= 30:  # После 5 минут
        print(f"⚠️  Долгое выполнение: уже {((i+1)*10)/60:.1f} минут")

if task.status == 'PENDING':
    print(f"❌ Задача все еще PENDING после 10 минут")
    print("Возможно Suno API перегружен или требуется еще больше времени")
