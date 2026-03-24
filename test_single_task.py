#!/usr/bin/env python3
import sys
sys.path.append('.')
from celery_tasks import generate_song_task
task = generate_song_task.delay(999888, 'ДИАГНОСТИКА Воркера', 'ТЕСТ стиль', False)
print(f"Задача отправлена: {task.id}")
