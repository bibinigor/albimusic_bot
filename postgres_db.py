import asyncpg
import logging
from config import *

# Настройки подключения к PostgreSQL
POSTGRES_DSN = f"postgresql://albimusic_user:aXAnAixKT6%40%3FB9@localhost/albimusic_bot"

# Пул подключений
connection_pool = None

async def init_postgres():
    """Инициализация пула подключений к PostgreSQL"""
    global connection_pool
    try:
        connection_pool = await asyncpg.create_pool(POSTGRES_DSN)
        logging.info("✅ PostgreSQL пул подключений инициализирован")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False

async def close_postgres():
    """Закрытие пула подключений"""
    global connection_pool
    if connection_pool:
        await connection_pool.close()
        logging.info("✅ PostgreSQL пул подключений закрыт")

# Базовые функции для работы с БД
async def execute_query(query, *args):
    """Выполнение SQL запроса"""
    async with connection_pool.acquire() as conn:
        return await conn.execute(query, *args)

async def fetch_query(query, *args):
    """Выполнение SELECT запроса с возвратом результатов"""
    async with connection_pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def fetchrow_query(query, *args):
    """Выполнение SELECT запроса с возвратом одной строки"""
    async with connection_pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
