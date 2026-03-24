import asyncio
import logging
import sys
import os
import time

# Добавляем путь к проекту
sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync
from config import BOT_TOKEN as TELEGRAM_BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/albimusic/monitor-error.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_telegram_notification(user_id, task_id, audio_url, is_song=False):
    """Отправка аудио файлов напрямую в Telegram"""
    try:
        import json
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Парсим JSON массив ссылок
        audio_urls = []
        try:
            if isinstance(audio_url, str) and audio_url.startswith("["):
                parsed_urls = json.loads(audio_url)
                if isinstance(parsed_urls, list):
                    audio_urls = parsed_urls
                    logger.info(f"📊 JSON массив: {len(audio_urls)} ссылок для {task_id}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга JSON: {e}")
        
        if not audio_urls:
            audio_urls = [audio_url]
        
        # Отправляем заголовок
        header = "🎤 Ваша песня готова!" if is_song else "🎵 Ваша музыка готова!"
        if len(audio_urls) > 1:
            header += f"\n\nСоздано {len(audio_urls)} варианта:"
        
        await bot.send_message(chat_id=user_id, text=header)
        
        # Отправляем каждый трек как аудио файл
        for idx, url in enumerate(audio_urls, 1):
            try:
                # Создаем кнопки
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📢 Разместить в канале",
                        callback_data=f"post_{task_id}"
                    )],
                    [InlineKeyboardButton(
                        text="🔔 Перейти в канал",
                        url="https://t.me/ALBImusic_Chart"
                    )]
                ])
                
                caption = f"🎼 Версия {idx}" if len(audio_urls) > 1 else "🎼 Ваш трек"
                
                # Отправляем аудио по URL - Telegram скачает сам
                await bot.send_audio(
                    chat_id=user_id,
                    audio=url,
                    caption=caption,
                    reply_markup=keyboard,
                    title=f"AI Music v{idx}",
                    performer="ALBI Music"
                )
                
                logger.info(f"✅ Версия {idx}/{len(audio_urls)} отправлена user {user_id}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки аудио {idx}: {e}")
                # Fallback - отправляем ссылку
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"🔗 Скачать v{idx}", url=url)]
                ])
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🎵 Версия {idx} (ссылка)",
                    reply_markup=kb
                )
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки user {user_id}: {e}")
        return False


# ========================================
# ПРОВЕРКА ДУБЛИКАТОВ В БД
# ========================================

async def check_and_clean_duplicates():
    """
    Проверяет и очищает дублирующиеся записи в таблице generations.
    Оставляет только последнюю запись для каждой пары (user_id, task_id).
    """
    logger.info("🔍 Проверка дубликатов в БД...")
    
    try:
        # Находим дубликаты
        duplicates = await execute_query("""
            SELECT 
                user_id,
                task_id,
                COUNT(*) as duplicate_count,
                MAX(created_at) as latest_created,
                MIN(created_at) as earliest_created
            FROM generations
            GROUP BY user_id, task_id
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 20
        """)
        
        if duplicates:
            logger.warning(f"⚠️  Найдено {len(duplicates)} групп дубликатов")
            
            for dup in duplicates:
                user_id, task_id, count, latest, earliest = dup
                logger.warning(f"   • user_id={user_id}, task_id={task_id}: {count} дубликатов")
                
                # Удаляем старые дубликаты, оставляя только последний
                deleted = await execute_query("""
                    DELETE FROM generations
                    WHERE user_id = %s 
                      AND task_id = %s 
                      AND id NOT IN (
                          SELECT id 
                          FROM generations 
                          WHERE user_id = %s 
                            AND task_id = %s 
                          ORDER BY created_at DESC 
                          LIMIT 1
                      )
                    RETURNING COUNT(*)
                """, (user_id, task_id, user_id, task_id))
                
                if deleted and deleted[0]:
                    logger.info(f"     ✅ Удалено {deleted[0]} старых дубликатов")
        else:
            logger.info("✅ Дубликатов не найдено")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке дубликатов: {e}")

async def monitor_generations():
    # Инициализируем пул подключений к БД
    from db_utils import init_db_pool_sync
    init_db_pool_sync()
    # Инициализируем пул подключений к БД
    from db_utils import init_db_pool_sync
    init_db_pool_sync()
    """Основная функция мониторинга"""
    logger.info("🚀 Запуск мониторинга завершенных задач...")
    
    # Словарь для отслеживания уже отправленных уведомлений
    sent_notifications = set()
    
    while True:
        try:
            # Ищем завершенные задачи в БД (и ошибки)
            results = execute_query_sync(
                "SELECT task_id, user_id, prompt, audio_url, status FROM generations WHERE ((status = 'completed' AND audio_url IS NOT NULL) OR (status = 'error' AND audio_url IS NOT NULL)) AND audio_url NOT LIKE 'ALREADY_NOTIFIED_%' AND audio_url != 'ERROR_NOTIFIED' ORDER BY created_at DESC LIMIT 10"
            )
            
            if results:
                for task_id, user_id, prompt, audio_url, status in results:
                    # Проверяем, не отправляли ли уже уведомление для этой задачи
                    if task_id not in sent_notifications:
                        logger.info(f"📨 Найдена задача {task_id} для пользователя {user_id} (статус: {status})")
                        
                        # Для ошибок отправляем особое уведомление
                        if status == 'error' or "ERROR:" in str(audio_url):
                            await send_error_notification(user_id, task_id, prompt)
                            sent_notifications.add(task_id)
                            continue
                        
                        # Определяем тип задачи (песня или музыка)
                        is_song = "текст" in prompt.lower() if prompt else False
                        
                        # Отправляем уведомление об успехе
                        success = await send_telegram_notification(user_id, task_id, audio_url, is_song)
                        
                        if success:
                            # Помечаем задачу как уведомленную
                            sent_notifications.add(task_id)
                            logger.info(f"✅ Уведомление для задачи {task_id} отправлено и запомнено")
                        else:
                            logger.error(f"❌ Не удалось отправить уведомление для задачи {task_id}")
            
            # Очищаем старые уведомления (чтобы не накапливать память)
            if len(sent_notifications) > 100:
                # Оставляем только последние 50 уведомлений
                sent_notifications = set(list(sent_notifications)[-50:])
                logger.info(f"🧹 Очищены старые уведомления, осталось: {len(sent_notifications)}")
            
            # Пауза между проверками
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в мониторинге: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_generations())
    except KeyboardInterrupt:
        logger.info("👋 Мониторинг остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
