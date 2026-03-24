import psycopg2
import logging
import config

logger = logging.getLogger(__name__)

class DatabaseAdapterSync:
    def __init__(self):
        self.conn_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT, 
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
        self.connection = None
    
    def get_connection(self):
        """Получить синхронное соединение с PostgreSQL"""
        try:
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(**self.conn_params)
            return self.connection
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def execute_query(self, query, *params):
        """Выполнить SQL запрос (синхронно)"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise

# Глобальный экземпляр для Celery
db_sync = DatabaseAdapterSync()
