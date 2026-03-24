import os
import logging
import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)

_db_pool = None

def init_db_pool_sync():
    """Синхронная инициализация пула соединений psycopg2"""
    global _db_pool
    if _db_pool is not None:
        logger.warning("DB pool already initialized. Closing existing pool before re-initialization.")
        close_db_pool_sync()

    try:
        _db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            user=os.getenv('DB_USER', 'albimusic_user'),
            password=os.getenv('DB_PASSWORD', 'aXAnAixKT6@?B9'),
            database=os.getenv('DB_NAME', 'albimusic_bot'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        logger.info("✅ psycopg2 DB pool initialized successfully for worker.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize psycopg2 DB pool: {e}", exc_info=True)
        _db_pool = None
        raise

def close_db_pool_sync():
    """Синхронное закрытие пула"""
    global _db_pool
    if _db_pool:
        logger.info("🔒 Closing psycopg2 DB pool...")
        try:
            _db_pool.closeall()
            logger.info("✅ psycopg2 DB pool closed successfully.")
        except Exception as e:
            logger.error(f"❌ Error closing psycopg2 DB pool: {e}", exc_info=True)
        finally:
            _db_pool = None

def get_db_pool_sync():
    """Возвращает глобальный пул соединений"""
    if _db_pool is None:
        logger.error("❌ DB pool is not initialized. Call init_db_pool_sync first.")
        raise RuntimeError("Database pool is not initialized.")
    return _db_pool

def execute_query_sync(query, params=None, fetch_one=False):
    """Выполняет SQL запрос синхронно"""
    import logging
    logger = logging.getLogger(__name__)
    """Выполняет SQL запрос синхронно"""
    conn = None
    try:
        pool = get_db_pool_sync()
        conn = pool.getconn()
        with conn.cursor() as cursor:
            # Логируем запрос (без паролей)
            safe_query = query.replace("\n", " ").strip()[:200]
            logger.info(f"🔧 execute_query_sync: {safe_query}")
            if params:
                logger.info(f"🔧 Параметры: {params}")
            
            cursor.execute(query, params)
            
            # СРОЧНОЕ ИСПРАВЛЕНИЕ: добавляем COMMIT для UPDATE/INSERT/DELETE
            query_upper = query.strip().upper()
            if query_upper.startswith(('UPDATE', 'INSERT', 'DELETE')):
                conn.commit()
                logger.info(f"🔥 COMMIT ВЫПОЛНЕН для {query_upper.split()[0]} (rowcount: {cursor.rowcount})")
            
            # Логируем результат
            query_upper = query.strip().upper()
            if query_upper.startswith('UPDATE'):
                logger.info(f"🔧 UPDATE rowcount: {cursor.rowcount}")
            elif query_upper.startswith('INSERT'):
                logger.info(f"🔧 INSERT rowcount: {cursor.rowcount}")
            elif query_upper.startswith('SELECT'):
                logger.info(f"🔧 SELECT выполнен")
            
            # Проверяем есть ли RETURNING в запросе
            query_upper = query.strip().upper()
            has_returning = 'RETURNING' in query_upper
            
            if query_upper.startswith('SELECT') or has_returning:
                # Для SELECT и запросов с RETURNING возвращаем данные
                # ВНИМАНИЕ: fetchone() вернет None если нет строк!
                if fetch_one or has_returning:
                    result = cursor.fetchone()
                    return result  # Может быть None если нет строк
                else:
                    return cursor.fetchall()
                # Для SELECT и запросов с RETURNING возвращаем данные
                if fetch_one or has_returning:
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
            else:
                # Для обычных UPDATE/INSERT/DELETE возвращаем rowcount
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        logger.error(f"❌ Error executing query: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            pool.putconn(conn)
def initialize_pool_for_worker():
    """Инициализирует пул соединений для воркера"""
    logger.info("🚀 Worker process: Initializing DB pool...")
    try:
        init_db_pool_sync()
        logger.info("✅ Worker process: DB pool initialization complete.")
    except Exception as e:
        logger.critical(f"❌ Worker process: Failed to initialize DB pool. Error: {e}")
        raise

def shutdown_pool_for_worker():
    """Закрывает пул соединений при остановке воркера"""
    logger.info("🔒 Worker process: Shutting down. Closing DB pool...")
    try:
        close_db_pool_sync()
    except Exception as e:
        logger.error(f"❌ Worker process: Error closing DB pool: {e}")
