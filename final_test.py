#!/usr/bin/env python3
import sys
import subprocess
import time
import threading
import redis

sys.path.append('.')

def run_celery():
    """Запускает Celery worker в отдельном процессе"""
    print("=== ЗАПУСК CELERY WORKER ===")
    cmd = [
        '/root/albimusic-bot/venv/bin/celery',
        '-A', 'celery_tasks.celery_app',
        'worker',
        '--pool=solo',
        '--concurrency=1',
        '-l', 'info',
        '--without-heartbeat',
        '--without-mingle',
        '-n', 'test_worker'
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Даем worker время на запуск
    time.sleep(5)
    return process

def send_task():
    """Отправляет тестовую задачу"""
    print("\n=== ОТПРАВКА ТЕСТОВОЙ ЗАДАЧИ ===")
    from celery_tasks import generate_song_task
    
    user_id = 338544009
    lyrics = "ФИНАЛЬНЫЙ ТЕСТ: Текст песни для проверки"
    style = "ФИНАЛЬНЫЙ ТЕСТ: Рок-стиль"
    
    print(f"Текст: {lyrics}")
    print(f"Стиль: {style}")
    
    task = generate_song_task.delay(user_id, lyrics, style, custom_mode=False)
    print(f"Задача отправлена с ID: {task.id}")
    
    # Проверим Redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    print(f"\nПроверка Redis после отправки:")
    print(f"Сообщений в очереди 'celery': {r.llen('celery')}")
    
    # Подождем немного
    for i in range(10):
        status = task.status
        print(f"Статус задачи через {i*2} сек: {status}")
        if status == 'SUCCESS' or status == 'FAILURE':
            break
        time.sleep(2)
    
    return task.id

def main():
    # Запускаем Celery worker в отдельном потоке
    celery_proc = run_celery()
    
    try:
        # Отправляем задачу
        task_id = send_task()
        
        # Ждем немного и читаем вывод Celery
        print("\n=== ВЫВОД CELERY WORKER (последние 20 строк) ===")
        time.sleep(10)
        
        # Попробуем получить вывод из процесса
        try:
            output, _ = celery_proc.communicate(timeout=5)
            lines = output.split('\n')
            print("\n".join(lines[-20:]))
        except subprocess.TimeoutExpired:
            print("Не удалось получить вывод (таймаут)")
            
    finally:
        # Останавливаем Celery worker
        print("\n=== ОСТАНОВКА CELERY WORKER ===")
        celery_proc.terminate()
        celery_proc.wait(timeout=10)
        
        # Запускаем systemd сервис обратно
        print("\n=== ВОССТАНОВЛЕНИЕ SYSTEMD СЕРВИСА ===")
        subprocess.run(['sudo', 'systemctl', 'start', 'albimusic-celery'])
        print("Готово!")

if __name__ == "__main__":
    main()
