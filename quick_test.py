from celery import Celery
import time

# Создаем новое приложение Celery в этом же окружении
app = Celery(
    'quick_test',
    broker='amqp://albimusic:StrongPassword123!@localhost:5672//',
    backend='redis://localhost:6379/0',
)

@app.task
def quick_ping(x):
    print(f"QUICK PING: {x}")
    return x

if __name__ == '__main__':
    # Запустим воркер в фоне
    import subprocess, os
    from pathlib import Path
    
    # Запустим простой воркер
    worker_cmd = ['celery', '-A', 'quick_test', 'worker', '--loglevel=INFO', '--concurrency=1']
    proc = subprocess.Popen(worker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Воркер запущен с PID: {proc.pid}")
    time.sleep(3)
    
    # Отправим задачу
    r = quick_ping.delay(7777)
    print(f"Task ID: {r.id}")
    
    for i in range(5):
        if r.ready():
            print(f"Готово через {i+1} секунд")
            break
        time.sleep(1)
    
    print(f"State: {r.state}")
    print(f"Result: {r.result}")
    
    # Остановим воркер
    proc.terminate()
    proc.wait()
