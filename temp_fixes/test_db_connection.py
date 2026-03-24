import sys
import os
sys.path.append(os.path.dirname(__file__))

from db_utils import DatabaseManager

def test_db_connection():
    print("🔧 Тестируем подключение к БД...")
    try:
        db = DatabaseManager()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем таблицу users
                cur.execute("SELECT COUNT(*) FROM users")
                users_count = cur.fetchone()
                print(f"✅ Таблица users: {users_count[0]} записей")
                
                # Проверяем таблицу generations
                cur.execute("SELECT COUNT(*) FROM generations")
                generations_count = cur.fetchone()
                print(f"✅ Таблица generations: {generations_count[0]} записей")
                
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()
