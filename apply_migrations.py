#!/usr/bin/env python3
"""
Скрипт для применения миграций БЛОКОВ 1-2
"""
import sys
from db_utils import execute_query_sync, init_db_pool_sync

# Инициализируем пул БД
print("🔄 Инициализация подключения к БД...")
try:
    init_db_pool_sync()
    print("✅ Подключение к БД установлено")
except Exception as e:
    print(f"❌ Ошибка подключения к БД: {e}")
    sys.exit(1)

def apply_migration_001():
    """Применить миграцию 001: добавление поля status"""
    print("🔄 Применение миграции 001_add_status_to_generations.sql...")
    
    try:
        # Добавляем поле status
        execute_query_sync("""
            ALTER TABLE generations 
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed'
        """)
        print("✅ Поле status добавлено")
        
        # Создаем индексы
        execute_query_sync("""
            CREATE INDEX IF NOT EXISTS idx_generations_status ON generations(status)
        """)
        print("✅ Индекс idx_generations_status создан")
        
        execute_query_sync("""
            CREATE INDEX IF NOT EXISTS idx_generations_user_status ON generations(user_id, status)
        """)
        print("✅ Индекс idx_generations_user_status создан")
        
        # Обновляем существующие записи
        execute_query_sync("""
            UPDATE generations 
            SET status = 'completed' 
            WHERE status IS NULL AND audio_url IS NOT NULL
        """)
        print("✅ Обновлены записи с status = 'completed'")
        
        execute_query_sync("""
            UPDATE generations 
            SET status = 'failed' 
            WHERE status IS NULL AND audio_url IS NULL
        """)
        print("✅ Обновлены записи с status = 'failed'")
        
        print("✅ Миграция 001 применена успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка применения миграции 001: {e}")
        return False


def apply_migration_002():
    """Применить миграцию 002: создание таблицы demo_tracks"""
    print("\n🔄 Применение миграции 002_add_demo_tracks_table.sql...")
    
    try:
        # Создаем таблицу demo_tracks
        execute_query_sync("""
            CREATE TABLE IF NOT EXISTS demo_tracks (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR(255) UNIQUE NOT NULL,
                user_id BIGINT NOT NULL,
                
                demo_url_1 TEXT,
                demo_url_2 TEXT,
                full_url_1 TEXT,
                full_url_2 TEXT,
                
                is_unlocked BOOLEAN DEFAULT FALSE,
                unlocked_at TIMESTAMP,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        print("✅ Таблица demo_tracks создана")
        
        # Создаем индексы
        execute_query_sync("""
            CREATE INDEX IF NOT EXISTS idx_demo_tracks_task_id ON demo_tracks(task_id)
        """)
        print("✅ Индекс idx_demo_tracks_task_id создан")
        
        execute_query_sync("""
            CREATE INDEX IF NOT EXISTS idx_demo_tracks_user_id ON demo_tracks(user_id)
        """)
        print("✅ Индекс idx_demo_tracks_user_id создан")
        
        execute_query_sync("""
            CREATE INDEX IF NOT EXISTS idx_demo_tracks_unlocked ON demo_tracks(is_unlocked)
        """)
        print("✅ Индекс idx_demo_tracks_unlocked создан")
        
        execute_query_sync("""
            CREATE INDEX IF NOT EXISTS idx_demo_tracks_user_unlocked ON demo_tracks(user_id, is_unlocked)
        """)
        print("✅ Индекс idx_demo_tracks_user_unlocked создан")
        
        # Создаем триггер для updated_at
        execute_query_sync("""
            CREATE OR REPLACE FUNCTION update_demo_tracks_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        print("✅ Функция update_demo_tracks_updated_at() создана")
        
        execute_query_sync("""
            DROP TRIGGER IF EXISTS trigger_update_demo_tracks_updated_at ON demo_tracks
        """)
        
        execute_query_sync("""
            CREATE TRIGGER trigger_update_demo_tracks_updated_at
                BEFORE UPDATE ON demo_tracks
                FOR EACH ROW
                EXECUTE FUNCTION update_demo_tracks_updated_at()
        """)
        print("✅ Триггер trigger_update_demo_tracks_updated_at создан")
        
        print("✅ Миграция 002 применена успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка применения миграции 002: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_migrations():
    """Проверить, какие миграции уже применены"""
    print("\n🔍 Проверка состояния миграций...")
    
    try:
        # Проверяем наличие поля status
        result = execute_query_sync("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'generations' AND column_name = 'status'
        """)
        
        if result and len(result) > 0:
            print("✅ Миграция 001 уже применена (поле status существует)")
            migration_001_applied = True
        else:
            print("⚠️ Миграция 001 не применена")
            migration_001_applied = False
        
        # Проверяем наличие таблицы demo_tracks
        result = execute_query_sync("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'demo_tracks'
        """)
        
        if result and len(result) > 0:
            print("✅ Миграция 002 уже применена (таблица demo_tracks существует)")
            migration_002_applied = True
        else:
            print("⚠️ Миграция 002 не применена")
            migration_002_applied = False
        
        return migration_001_applied, migration_002_applied
    except Exception as e:
        print(f"❌ Ошибка проверки миграций: {e}")
        return False, False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ПРИМЕНЕНИЕ МИГРАЦИЙ БЛОКОВ 1-2")
    print("=" * 60)
    
    # Проверяем текущее состояние
    migration_001_applied, migration_002_applied = check_migrations()
    
    # Применяем миграции
    success = True
    
    if not migration_001_applied:
        if not apply_migration_001():
            success = False
    else:
        print("\n⏭️ Миграция 001 уже применена, пропускаем")
    
    if not migration_002_applied:
        if not apply_migration_002():
            success = False
    else:
        print("\n⏭️ Миграция 002 уже применена, пропускаем")
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ВСЕ МИГРАЦИИ ПРИМЕНЕНЫ УСПЕШНО!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ ОШИБКА ПРИМЕНЕНИЯ МИГРАЦИЙ")
        print("=" * 60)
        sys.exit(1)
