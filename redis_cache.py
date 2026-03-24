import redis
import json
import logging
from datetime import timedelta

# Настройки Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Глобальный клиент Redis
redis_client = None

def init_redis():
    """Инициализация подключения к Redis"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        # Проверяем подключение
        redis_client.ping()
        logging.info("✅ Redis подключен успешно")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к Redis: {e}")
        return False

# Функции кеширования
def cache_user_balance(user_id, balance_data, expire_minutes=5):
    """Кеширование баланса пользователя"""
    if not redis_client:
        return
    try:
        key = f"user_balance:{user_id}"
        redis_client.setex(key, timedelta(minutes=expire_minutes), balance_data)
    except Exception as e:
        logging.error(f"❌ Ошибка кеширования баланса {user_id}: {e}")

def get_cached_user_balance(user_id):
    """Получение кешированного баланса пользователя"""
    if not redis_client:
        return None
    try:
        key = f"user_balance:{user_id}"
        return redis_client.get(key)
    except Exception as e:
        logging.error(f"❌ Ошибка получения кешированного баланса {user_id}: {e}")
        return None

def cache_generation_status(task_id, status_data, expire_minutes=10):
    """Кеширование статуса генерации"""
    if not redis_client:
        return
    try:
        key = f"generation_status:{task_id}"
        redis_client.setex(key, timedelta(minutes=expire_minutes), json.dumps(status_data))
    except Exception as e:
        logging.error(f"❌ Ошибка кеширования статуса {task_id}: {e}")

def get_cached_generation_status(task_id):
    """Получение кешированного статуса генерации"""
    if not redis_client:
        return None
    try:
        key = f"generation_status:{task_id}"
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logging.error(f"❌ Ошибка получения кешированного статуса {task_id}: {e}")
        return None

# Функции для сессий
def set_user_session(user_id, session_data, expire_minutes=30):
    """Сохранение сессии пользователя"""
    if not redis_client:
        return
    try:
        key = f"user_session:{user_id}"
        redis_client.setex(key, timedelta(minutes=expire_minutes), json.dumps(session_data))
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения сессии {user_id}: {e}")

def get_user_session(user_id):
    """Получение сессии пользователя"""
    if not redis_client:
        return None
    try:
        key = f"user_session:{user_id}"
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logging.error(f"❌ Ошибка получения сессии {user_id}: {e}")
        return None

def delete_user_session(user_id):
    """Удаление сессии пользователя"""
    if not redis_client:
        return
    try:
        key = f"user_session:{user_id}"
        redis_client.delete(key)
    except Exception as e:
        logging.error(f"❌ Ошибка удаления сессии {user_id}: {e}")
