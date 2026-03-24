from celery_tasks import generate_music_task
import redis

print("=== ТЕСТ ОТПРАВКИ ЗАДАЧИ CELERY ===")

# 1. Проверяем Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    print(f"✅ Redis: {r.ping()}, очередь: {r.llen('celery')} задач")
except Exception as e:
    print(f"❌ Redis ошибка: {e}")

# 2. Проверяем Celery app
from celery_tasks import celery_app
print(f"✅ Celery app broker: {celery_app.conf.broker_url}")

# 3. Пробуем отправить задачу
try:
    result = generate_music_task.delay(338544009, "test music style")
    print(f"✅ Задача отправлена: {result.id}")
    print(f"✅ Статус: {result.status}")
except Exception as e:
    print(f"❌ Ошибка отправки: {e}")

# 4. Проверяем очередь после отправки
print(f"✅ Очередь после отправки: {r.llen('celery')} задач")
