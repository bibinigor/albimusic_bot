import sys
import os
sys.path.append(os.path.dirname(__file__))

from celery_tasks import generate_music_task, generate_song_task, test_task
from db_utils import DatabaseManager

def test_celery_connection():
    print("🔧 Тестируем подключение Celery...")
    try:
        result = test_task.delay()
        print(f"✅ Тестовая задача отправлена: {result.id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Celery: {e}")
        return False

def test_db_connection():
    print("🔧 Тестируем подключение к БД...")
    try:
        db = DatabaseManager()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                print(f"✅ Подключение к БД: {result}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

def test_music_generation():
    print("🔧 Тестируем генерацию музыки...")
    try:
        result = generate_music_task.delay(
            user_id=338544009,
            description="Тестовая музыка - инструментальная композиция",
            style="classical"
        )
        print(f"✅ Задача генерации музыки отправлена: {result.id}")
        return result.id
    except Exception as e:
        print(f"❌ Ошибка генерации музыки: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Запуск тестов интеграции...")
    
    # Тест подключения к Celery
    if not test_celery_connection():
        print("❌ Celery не подключен")
        sys.exit(1)
    
    # Тест подключения к БД
    if not test_db_connection():
        print("❌ БД не подключена")
        sys.exit(1)
    
    # Тест генерации
    task_id = test_music_generation()
    if task_id:
        print(f"🎵 Тестовая задача создана: {task_id}")
    else:
        print("❌ Не удалось создать задачу генерации")
