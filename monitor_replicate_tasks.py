#!/usr/bin/env python3
"""
Мониторинг и отправка результатов для Replicate задач
Добавить в cron: */1 * * * * cd /root/albimusic-bot && python3 monitor_replicate_tasks.py >> monitor_replicate.log 2>&1
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot
from db_utils import execute_query_sync, init_db_pool_sync
from config import BOT_TOKEN

# ИСПРАВЛЕНО: Инициализация пула БД
init_db_pool_sync()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_video_results(bot: Bot):
    """Отправка готовых видео пользователям"""
    try:
        # Получаем завершенные видео, которые еще не отправлены
        results = execute_query_sync(
            """SELECT task_id, user_id, video_url, duration, cost_tokens
               FROM video_generations
               WHERE status = 'completed' AND video_url IS NOT NULL 
               AND (video_url NOT LIKE 'SENT_%')
               ORDER BY completed_at ASC
               LIMIT 10"""
        )
        
        if not results:
            return
        
        logger.info(f"📤 Найдено {len(results)} готовых видео для отправки")
        
        for task_id, user_id, video_url, duration, cost_tokens in results:
            try:
                # Отправляем видео
                await bot.send_video(
                    user_id,
                    video_url,
                    caption=f"🎬 **Ваше видео готово!**\n\n⏱️ Длительность: {duration} сек\n💎 Потрачено: {cost_tokens} токенов",
                    parse_mode="Markdown"
                )
                
                # Помечаем как отправленное
                execute_query_sync(
                    "UPDATE video_generations SET video_url = %s WHERE task_id = %s",
                    (f"SENT_{video_url}", task_id)
                )
                
                logger.info(f"✅ Видео отправлено: user={user_id}, task={task_id}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки видео user={user_id}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка в send_video_results: {e}")


async def send_photo_results(bot: Bot):
    """Отправка готовых фото операций пользователям"""
    try:
        # Получаем завершенные операции, которые еще не отправлены
        results = execute_query_sync(
            """SELECT task_id, user_id, operation_type, output_url, cost_tokens
               FROM photo_operations
               WHERE status = 'completed' AND output_url IS NOT NULL 
               AND (output_url NOT LIKE 'SENT_%')
               ORDER BY completed_at ASC
               LIMIT 10"""
        )
        
        if not results:
            return
        
        logger.info(f"📤 Найдено {len(results)} готовых фото операций для отправки")
        
        for task_id, user_id, operation_type, output_url, cost_tokens in results:
            try:
                # Определяем тип контента и текст
                operation_names = {
                    'animate': ('видео', '🎬 Ваше оживленное фото готово!'),
                    'dance': ('видео', '💃 Ваш танец готов!'),
                    'upscale': ('фото', '⬆️ Ваше улучшенное фото готово!'),
                    'remove_bg': ('фото', '🗑️ Фон удален!')
                }
                
                content_type, caption_text = operation_names.get(operation_type, ('фото', 'Готово!'))
                
                # Отправляем результат
                if content_type == 'видео':
                    await bot.send_video(
                        user_id,
                        output_url,
                        caption=f"{caption_text}\n\n💎 Потрачено: {cost_tokens} токенов",
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_photo(
                        user_id,
                        output_url,
                        caption=f"{caption_text}\n\n💎 Потрачено: {cost_tokens} токенов",
                        parse_mode="Markdown"
                    )
                
                # Помечаем как отправленное
                execute_query_sync(
                    "UPDATE photo_operations SET output_url = %s WHERE task_id = %s",
                    (f"SENT_{output_url}", task_id)
                )
                
                logger.info(f"✅ Фото операция отправлена: user={user_id}, task={task_id}, type={operation_type}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки фото операции user={user_id}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка в send_photo_results: {e}")


async def send_image_results(bot: Bot):
    """Отправка готовых изображений пользователям"""
    try:
        # Получаем завершенные изображения, которые еще не отправлены
        results = execute_query_sync(
            """SELECT task_id, user_id, prompt, image_url, aspect_ratio, cost_tokens
               FROM image_generations
               WHERE status = 'completed' AND image_url IS NOT NULL
               AND (image_url NOT LIKE 'SENT_%')
               ORDER BY completed_at ASC
               LIMIT 10"""
        )
        
        if not results:
            return
        
        logger.info(f"📤 Найдено {len(results)} готовых изображений для отправки")
        
        # ИСПРАВЛЕНО: Двухуровневая система качества (превью + HD)
        import requests
        from PIL import Image
        from io import BytesIO
        
        for task_id, user_id, prompt, image_url, aspect_ratio, cost_tokens in results:
            try:
                short_prompt = (prompt[:50] + '...') if len(prompt) > 50 else prompt
                
                # Скачиваем HD-изображение
                logger.info(f"⬇️ Скачиваю HD-изображение: {image_url[:50]}...")
                response = requests.get(image_url, timeout=30)
                hd_image = Image.open(BytesIO(response.content))
                
                # Создаём превью (сжимаем до 700px по длинной стороне)
                preview = hd_image.copy()
                preview.thumbnail((700, 700), Image.LANCZOS)
                
                # Сохраняем превью во временную директорию
                preview_dir = "/tmp/albimusic_image_previews"
                os.makedirs(preview_dir, exist_ok=True)
                preview_path = os.path.join(preview_dir, f"preview_{task_id}.jpg")
                preview.save(preview_path, "JPEG", quality=75, optimize=True)
                
                logger.info(f"✅ Превью создано: {os.path.getsize(preview_path) // 1024} KB")
                
                # Создаём inline кнопки
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
                    InlineKeyboardButton("🎨 Новое изображение", callback_data="image_create"),
                    InlineKeyboardButton("🔄 Перегенерировать", callback_data=f"image_regen_{task_id}")
                )
                
                # Отправляем превью в чат
                with open(preview_path, 'rb') as photo:
                    await bot.send_photo(
                        user_id,
                        photo,
                        caption=(
                            f"🎨 **Ваше изображение готово!**\n\n"
                            f"📝 _{short_prompt}_\n"
                            f"📐 Формат: {aspect_ratio}\n"
                            f"💎 Потрачено: {cost_tokens} токен\n\n"
                            f"⬇️ **HD-версия для скачивания:**\n"
                            f"{image_url}\n\n"
                            f"💡 Нажмите правой кнопкой → \"Сохранить изображение\""
                        ),
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                
                # Удаляем превью сразу после отправки
                os.remove(preview_path)
                logger.info(f"🗑️ Превью удалено: {preview_path}")
                
                # Помечаем как отправленное
                execute_query_sync(
                    "UPDATE image_generations SET image_url = %s WHERE task_id = %s",
                    (f"SENT_{image_url}", task_id)
                )
                
                logger.info(f"✅ Изображение отправлено: user={user_id}, task={task_id}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки изображения user={user_id}: {e}")
                # Удаляем превью в случае ошибки
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                
    except Exception as e:
        logger.error(f"❌ Ошибка в send_image_results: {e}")


async def notify_failed_tasks(bot: Bot):
    """Уведомление пользователей об ошибках"""
    try:
        # Видео ошибки
        video_errors = execute_query_sync(
            """SELECT task_id, user_id, error_message, cost_tokens
               FROM video_generations
               WHERE status = 'failed' AND error_message IS NOT NULL
               AND (error_message NOT LIKE 'NOTIFIED_%')
               LIMIT 5"""
        )
        
        for task_id, user_id, error_message, cost_tokens in video_errors:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ **Ошибка генерации видео**\n\n"
                    f"К сожалению, не удалось создать видео.\n\n"
                    f"💰 Токены возвращены: {cost_tokens}\n\n"
                    f"Попробуйте еще раз или обратитесь в поддержку.",
                    parse_mode="Markdown"
                )
                
                execute_query_sync(
                    "UPDATE video_generations SET error_message = %s WHERE task_id = %s",
                    (f"NOTIFIED_{error_message}", task_id)
                )
                
                logger.info(f"📧 Уведомление об ошибке видео отправлено: user={user_id}")
            except:
                pass
        
        # Фото ошибки
        photo_errors = execute_query_sync(
            """SELECT task_id, user_id, operation_type, error_message, cost_tokens
               FROM photo_operations
               WHERE status = 'failed' AND error_message IS NOT NULL
               AND (error_message NOT LIKE 'NOTIFIED_%')
               LIMIT 5"""
        )
        
        for task_id, user_id, operation_type, error_message, cost_tokens in photo_errors:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ **Ошибка обработки фото**\n\n"
                    f"Операция: {operation_type}\n\n"
                    f"💰 Токены возвращены: {cost_tokens}\n\n"
                    f"Попробуйте еще раз или обратитесь в поддержку.",
                    parse_mode="Markdown"
                )
                
                execute_query_sync(
                    "UPDATE photo_operations SET error_message = %s WHERE task_id = %s",
                    (f"NOTIFIED_{error_message}", task_id)
                )
                
                logger.info(f"📧 Уведомление об ошибке фото отправлено: user={user_id}")
            except:
                pass
        
        # Изображения ошибки
        image_errors = execute_query_sync(
            """SELECT task_id, user_id, error_message, cost_tokens
               FROM image_generations
               WHERE status = 'failed' AND error_message IS NOT NULL
               AND (error_message NOT LIKE 'NOTIFIED_%')
               LIMIT 5"""
        )
        
        for task_id, user_id, error_message, cost_tokens in image_errors:
            try:
                await bot.send_message(
                    user_id,
                    f"❌ **Ошибка генерации изображения**\n\n"
                    f"К сожалению, не удалось создать изображение.\n\n"
                    f"💰 Токены возвращены: {cost_tokens}\n\n"
                    f"Попробуйте еще раз или обратитесь в поддержку.",
                    parse_mode="Markdown"
                )
                
                execute_query_sync(
                    "UPDATE image_generations SET error_message = %s WHERE task_id = %s",
                    (f"NOTIFIED_{error_message}", task_id)
                )
                
                logger.info(f"📧 Уведомление об ошибке изображения отправлено: user={user_id}")
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Ошибка в notify_failed_tasks: {e}")


async def main():
    """Главная функция мониторинга"""
    logger.info("🔍 Запуск мониторинга Replicate задач...")
    
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Отправляем результаты
        await send_video_results(bot)
        await send_photo_results(bot)
        await send_image_results(bot)
        
        # Уведомляем об ошибках
        await notify_failed_tasks(bot)
        
        logger.info("✅ Мониторинг завершен")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в мониторинге: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
