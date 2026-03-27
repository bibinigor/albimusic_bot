#!/usr/bin/env python3
"""
Скрипт для применения миграций веб-версии AlBi Music
Применяет SQL миграции для поддержки кросс-платформенной авторизации,
платежей и безопасности.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging

# Добавляем родительскую директорию в путь для импорта config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Миграции для веб-версии (порядок важен!)
WEB_MIGRATIONS = [
    '004_web_platform_support.sql',
    '005_web_payments_idempotency.sql',
    '006_web_security_rate_limiting.sql',
]


def get_db_connection():
    """Создает подключение к БД"""
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        sys.exit(1)


def create_migrations_table(conn):
    """Создает таблицу для отслеживания примененных миграций"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("✅ Таблица schema_migrations готова")
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы миграций: {e}")
        conn.rollback()
        raise


def is_migration_applied(conn, filename):
    """Проверяет, применена ли миграция"""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE filename = %s",
                (filename,)
            )
            count = cur.fetchone()[0]
            return count > 0
    except Exception as e:
        logger.error(f"❌ Ошибка проверки миграции {filename}: {e}")
        return False


def apply_migration(conn, filepath, filename):
    """Применяет одну миграцию"""
    try:
        logger.info(f"📦 Применяем миграцию: {filename}")
        
        # Читаем SQL файл
        with open(filepath, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Применяем миграцию
        with conn.cursor() as cur:
            cur.execute(migration_sql)
            
            # Записываем в schema_migrations
            cur.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (filename,)
            )
        
        conn.commit()
        logger.info(f"✅ Миграция {filename} успешно применена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка применения миграции {filename}: {e}")
        conn.rollback()
        return False


def main():
    """Основная функция"""
    logger.info("🚀 Начинаем применение миграций для веб-версии...")
    
    # Подключаемся к БД
    conn = get_db_connection()
    logger.info("✅ Подключение к БД установлено")
    
    try:
        # Создаем таблицу для отслеживания миграций
        create_migrations_table(conn)
        
        # Путь к директории с миграциями
        migrations_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Применяем миграции по порядку
        applied_count = 0
        skipped_count = 0
        
        for filename in WEB_MIGRATIONS:
            filepath = os.path.join(migrations_dir, filename)
            
            # Проверяем существование файла
            if not os.path.exists(filepath):
                logger.warning(f"⚠️ Файл миграции не найден: {filepath}")
                continue
            
            # Проверяем, применена ли миграция
            if is_migration_applied(conn, filename):
                logger.info(f"⏭️ Миграция {filename} уже применена, пропускаем")
                skipped_count += 1
                continue
            
            # Применяем миграцию
            if apply_migration(conn, filepath, filename):
                applied_count += 1
            else:
                logger.error(f"❌ Не удалось применить миграцию {filename}")
                break
        
        # Итоговый отчет
        logger.info("\n" + "="*60)
        logger.info("📊 ИТОГИ ПРИМЕНЕНИЯ МИГРАЦИЙ:")
        logger.info(f"   ✅ Применено: {applied_count}")
        logger.info(f"   ⏭️ Пропущено (уже применены): {skipped_count}")
        logger.info(f"   📦 Всего миграций: {len(WEB_MIGRATIONS)}")
        logger.info("="*60 + "\n")
        
        if applied_count > 0:
            logger.info("🎉 Веб-миграции успешно применены!")
            logger.info("\n📋 Что было добавлено:")
            logger.info("   1. Кросс-платформенная авторизация (Telegram/Yandex/VK)")
            logger.info("   2. Платежная система с idempotency защитой")
            logger.info("   3. Rate limiting и безопасность биллинга")
            logger.info("   4. Атомарные функции для списания токенов")
            logger.info("   5. История транзакций для аудита")
        else:
            logger.info("ℹ️ Новых миграций для применения не найдено")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        conn.close()
        logger.info("🔌 Подключение к БД закрыто")


if __name__ == "__main__":
    main()
