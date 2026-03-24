#!/usr/bin/env python3
"""
Скрипт очистки загруженных пользователями файлов
Удаляет файлы старше 1 часа из /var/www/albimusic/uploads/
"""

import os
import time
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/albimusic/cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = '/var/www/albimusic/uploads'
MAX_AGE_HOURS = 1  # Удалять файлы старше 1 часа

def cleanup_old_files():
    """Удалить файлы старше MAX_AGE_HOURS часов"""
    try:
        if not os.path.exists(UPLOAD_DIR):
            logger.warning(f"❌ Директория {UPLOAD_DIR} не существует")
            return

        current_time = time.time()
        max_age_seconds = MAX_AGE_HOURS * 3600

        deleted_count = 0
        freed_space = 0
        total_files = 0

        logger.info(f"🔍 Начало очистки директории {UPLOAD_DIR}")
        logger.info(f"⏰ Удаляю файлы старше {MAX_AGE_HOURS} часа(ов)")

        for filename in os.listdir(UPLOAD_DIR):
            filepath = os.path.join(UPLOAD_DIR, filename)

            # Проверяем только файлы
            if not os.path.isfile(filepath):
                continue

            total_files += 1

            # Получаем время последнего изменения файла
            file_age = current_time - os.path.getmtime(filepath)

            # Если файл старше MAX_AGE_HOURS, удаляем
            if file_age > max_age_seconds:
                try:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    freed_space += file_size

                    age_minutes = int(file_age / 60)
                    logger.info(f"🗑️  Удален: {filename} (возраст: {age_minutes} мин, размер: {file_size / 1024:.1f} KB)")
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления {filename}: {e}")

        # Статистика
        logger.info(f"✅ Очистка завершена:")
        logger.info(f"   • Всего файлов: {total_files}")
        logger.info(f"   • Удалено: {deleted_count}")
        logger.info(f"   • Освобождено: {freed_space / 1024 / 1024:.2f} MB")
        logger.info(f"   • Осталось файлов: {total_files - deleted_count}")

        # Проверка свободного места на диске
        stat = os.statvfs(UPLOAD_DIR)
        free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        logger.info(f"💾 Свободно на диске: {free_space_gb:.2f} GB")

        if free_space_gb < 1:
            logger.warning(f"⚠️  ВНИМАНИЕ: Мало места на диске! Осталось {free_space_gb:.2f} GB")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при очистке: {e}")

if __name__ == "__main__":
    cleanup_old_files()
