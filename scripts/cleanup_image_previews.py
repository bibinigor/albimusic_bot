#!/usr/bin/env python3
"""
Скрипт очистки старых превью изображений
Удаляет файлы старше 24 часов из /tmp/albimusic_image_previews/
"""

import os
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PREVIEW_DIR = "/tmp/albimusic_image_previews"
MAX_AGE_HOURS = 24

def cleanup_old_previews():
    """Удаляет превью старше 24 часов"""
    try:
        if not os.path.exists(PREVIEW_DIR):
            logger.info(f"📁 Директория {PREVIEW_DIR} не существует")
            return
        
        now = time.time()
        cutoff_time = now - (MAX_AGE_HOURS * 3600)
        
        deleted_count = 0
        deleted_size = 0
        
        for filename in os.listdir(PREVIEW_DIR):
            filepath = os.path.join(PREVIEW_DIR, filename)
            
            # Пропускаем директории
            if not os.path.isfile(filepath):
                continue
            
            # Проверяем возраст файла
            file_mtime = os.path.getmtime(filepath)
            
            if file_mtime < cutoff_time:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted_count += 1
                deleted_size += file_size
                
                file_age = (now - file_mtime) / 3600
                logger.info(f"🗑️ Удалён: {filename} (возраст: {file_age:.1f}ч, {file_size // 1024}KB)")
        
        if deleted_count > 0:
            logger.info(f"✅ Очистка завершена: удалено {deleted_count} файлов, освобождено {deleted_size // 1024} KB")
        else:
            logger.info("✅ Нет файлов старше 24 часов")
        
        # Показываем текущее состояние
        remaining_files = len([f for f in os.listdir(PREVIEW_DIR) if os.path.isfile(os.path.join(PREVIEW_DIR, f))])
        if remaining_files > 0:
            total_size = sum(os.path.getsize(os.path.join(PREVIEW_DIR, f)) 
                           for f in os.listdir(PREVIEW_DIR) 
                           if os.path.isfile(os.path.join(PREVIEW_DIR, f)))
            logger.info(f"📊 Осталось файлов: {remaining_files}, размер: {total_size // 1024} KB")
        
    except Exception as e:
        logger.error(f"❌ Ошибка очистки: {e}")


if __name__ == "__main__":
    logger.info("🧹 Запуск очистки превью изображений...")
    cleanup_old_previews()
    logger.info("✅ Скрипт завершён")
