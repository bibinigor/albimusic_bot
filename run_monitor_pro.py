#!/usr/bin/env python3
"""
Улучшенный мониторинг с правильными импортами
"""

import asyncio
import logging
import aiohttp
import hashlib
import sys
import os

# Добавляем путь к проекту
sys.path.append('/app')

from postgres_db import Database
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/monitor_pro.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Инициализация БД и бота
db = Database()
bot = Bot(token=config.BOT_TOKEN)

async def check_suno_task_status(suno_task_id):
    """Проверяет статус задачи в SunoAPI"""
    try:
        headers = {
            "Authorization": f"Bearer {config.SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={suno_task_id}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    status = result.get("data", {}).get("status")
                    
                    if status == "SUCCESS":
                        # Задача завершена успешно
                        audio_data = result.get("data", {}).get("response", {}).get("sunoData", [])
                        if audio_data:
                            audio_url = audio_data[0].get("audioUrl")
                            return {"status": "completed", "audio_url": audio_url}
                    elif status in ["PENDING", "PROCESSING"]:
                        return {"status": "processing"}
                    else:
                        return {"status": "failed"}
                        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки статуса Suno задачи {suno_task_id}: {e}")
        return {"status": "error"}

async def check_completed_tasks():
    """Проверяет завершенные задачи без уведомлений"""
    try:
        # Задачи со статусом completed но без уведомления
        completed_tasks = await db.fetch_query(
            'SELECT task_id, user_id, audio_url, prompt FROM generations WHERE status = $1 AND notified = $2',
            'completed', False
        )
        
        for task in completed_tasks:
            if task['audio_url'] and task['audio_url'].startswith('http'):
                # Отправляем уведомление
                is_song = "Текст песни:" in task['prompt']
                message = f"🎵 **{'Песня' if is_song else 'Музыка'} готова!**\n\n📥 Скачать: {task['audio_url']}"
                
                keyboard = InlineKeyboardMarkup()
                url_hash = hashlib.md5(task['audio_url'].encode()).hexdigest()[:10]
                keyboard.add(InlineKeyboardButton("📢 Разместить в канале ALBImusic Chart", callback_data=f"post_{url_hash}"))
                
                await bot.send_message(task['user_id'], message, reply_markup=keyboard, parse_mode="Markdown")
                
                # Помечаем как уведомленное
                await db.execute_query(
                    'UPDATE generations SET notified = TRUE WHERE task_id = $1',
                    task['task_id']
                )
                logger.info(f"✅ Уведомление отправлено пользователю {task['user_id']}")

    except Exception as e:
        logger.error(f"❌ Ошибка в проверке завершенных задач: {e}")

async def check_suno_processing_tasks():
    """Проверяет задачи в статусе suno_processing"""
    try:
        # Задачи в статусе suno_processing
        processing_tasks = await db.fetch_query(
            'SELECT task_id, user_id, audio_url as suno_task_id FROM generations WHERE status = $1',
            'suno_processing'
        )
        
        for task in processing_tasks:
            suno_task_id = task['suno_task_id']
            if suno_task_id and len(suno_task_id) == 32:  # Проверяем что это suno_task_id
                logger.info(f"🔍 Проверяем статус Suno задачи: {suno_task_id}")
                
                # Проверяем статус в SunoAPI
                status_result = await check_suno_task_status(suno_task_id)
                
                if status_result["status"] == "completed":
                    # Обновляем задачу в БД
                    await db.execute_query(
                        'UPDATE generations SET status = $1, audio_url = $2, notified = $3 WHERE task_id = $4',
                        'completed', status_result["audio_url"], False, task['task_id']
                    )
                    logger.info(f"✅ Задача {task['task_id']} завершена, audio_url обновлен")
                    
                elif status_result["status"] == "failed":
                    await db.execute_query(
                        'UPDATE generations SET status = $1 WHERE task_id = $2',
                        'failed', task['task_id']
                    )
                    logger.warning(f"⚠️ Задача {task['task_id']} завершилась с ошибкой")

    except Exception as e:
        logger.error(f"❌ Ошибка в проверке suno_processing задач: {e}")

async def start_pro_monitor():
    """Запускает улучшенный мониторинг"""
    logger.info("🚀 Запуск улучшенного мониторинга...")
    
    while True:
        try:
            await check_completed_tasks()
            await check_suno_processing_tasks()
            await asyncio.sleep(30)  # Проверяем каждые 30 секунд
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в мониторинге: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(start_pro_monitor())
