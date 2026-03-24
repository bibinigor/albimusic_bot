#!/usr/bin/env python3
"""Очистка старых записей из БД (запускать раз в неделю)"""
import psycopg2
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_records():
    try:
        conn = psycopg2.connect(
            "dbname=albimusic_bot user=albimusic_user "
            "password='aXAnAixKT6@?B9' host=localhost"
        )
        cur = conn.cursor()
        
        # 1. Удаляем задачи старше 30 дней
        cur.execute("""
            DELETE FROM generations 
            WHERE created_at < NOW() - INTERVAL '30 days'
            RETURNING COUNT(*)
        """)
        deleted_tasks = cur.fetchone()[0]
        logger.info(f"🗑️ Удалено {deleted_tasks} старых задач (>30 дней)")
        
        # 2. Удаляем платежи старше 90 дней (для финансового учета)
        cur.execute("""
            DELETE FROM payments 
            WHERE created_at < NOW() - INTERVAL '90 days'
            AND status = 'succeeded'
            RETURNING COUNT(*)
        """)
        deleted_payments = cur.fetchone()[0]
        logger.info(f"💰 Удалено {deleted_payments} старых платежей (>90 дней)")
        
        # 3. Удаляем логи админа старше 7 дней (если таблица существует)
        try:
            cur.execute("""
                DELETE FROM admin_logs 
                WHERE created_at < NOW() - INTERVAL '7 days'
                RETURNING COUNT(*)
            """)
            deleted_logs = cur.fetchone()[0]
            logger.info(f"📋 Удалено {deleted_logs} старых логов (>7 дней)")
        except Exception as e:
            logger.info(f"ℹ️ Таблица admin_logs не существует или ошибка: {e}")
        
        # 4. VACUUM для освобождения места
        cur.execute("VACUUM ANALYZE")
        logger.info("🧹 Выполнен VACUUM ANALYZE для оптимизации БД")
        
        conn.commit()
        conn.close()
        
        # Итоговый отчет
        logger.info(f"✅ Очистка завершена. Удалено: {deleted_tasks} задач, {deleted_payments} платежей")
        
    except Exception as e:
        logger.error(f"❌ Ошибка очистки БД: {e}")

if __name__ == "__main__":
    cleanup_old_records()
