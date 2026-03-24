import psycopg2
from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)

# ... остальной код ...

def execute_query_sync(query, params=None, fetch_one=False):
    """Выполняет SQL запрос синхронно"""
    conn = None
    try:
        pool = get_db_pool_sync()
        conn = pool.getconn()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                if fetch_one:
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
            else:
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

# ... остальной код ...
