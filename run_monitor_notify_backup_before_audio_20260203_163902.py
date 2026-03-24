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
    """Отправка уведомления в Telegram о готовности генерации"""
    try:
        import aiohttp
        import json
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Определяем язык пользователя
        language = "ru"  # По умолчанию русский
        
        # Проверяем, является ли audio_url JSON массивом ссылок
        audio_urls = []
        try:
            # Пробуем распарсить как JSON
            if isinstance(audio_url, str) and audio_url.startswith("["):
                parsed_urls = json.loads(audio_url)
                if isinstance(parsed_urls, list):
                    audio_urls = parsed_urls
                    logger.info(f"📊 Обнаружен JSON массив с {len(audio_urls)} ссылками для задачи {task_id}")
        except Exception as json_error:
            logger.warning(f"⚠️ Не удалось распарсить JSON для задачи {task_id}: {json_error}")
        
        # Если не JSON или пустой массив, используем как обычную ссылку
        if not audio_urls:
            audio_urls = [audio_url]
        
        if language == "ru":
            message_text = "🎵 Ваша музыка готова!"
            if is_song:
                message_text = "🎤 Ваша песня готова!"
            
            # Создаем кнопки для каждой ссылки
            keyboard_buttons = []
            
            if len(audio_urls) == 1:
                # Одна ссылка - одна кнопка
                keyboard_buttons.append([
                    InlineKeyboardButton(text="🔗 Скачать MP3", url=audio_urls[0])
                ])
            else:
                # Несколько ссылок - кнопки "Версия 1", "Версия 2", etc.
                for i, url in enumerate(audio_urls):
                    keyboard_buttons.append([
                        InlineKeyboardButton(text=f"🔗 Скачать Версию {i+1}", url=url)
                    ])
            
            # Добавляем остальные кнопки
            keyboard_buttons.append([
                InlineKeyboardButton(text="📢 Разместить в канале ALBI Music Chart", callback_data=f"post_{task_id}")
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔔 Перейти в канал ALBI Music Chart", url="https://t.me/ALBImusic_Chart")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        else:
            message_text = "🎵 Your music is ready!"
            if is_song:
                message_text = "🎤 Your song is ready!"
            
            keyboard_buttons = []
            
            if len(audio_urls) == 1:
                keyboard_buttons.append([
                    InlineKeyboardButton(text="🔗 Download MP3", url=audio_urls[0])
                ])
            else:
                for i, url in enumerate(audio_urls):
                    keyboard_buttons.append([
                        InlineKeyboardButton(text=f"🔗 Download Version {i+1}", url=url)
                    ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="📢 Publish in ALBI Music Chart", callback_data=f"post_{task_id}")
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔔 Go to ALBI Music Chart", url="https://t.me/ALBImusic_Chart")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await bot.send_message(
            chat_id=user_id,
            text=message_text,
            reply_markup=keyboard
        )
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False
        
        message_text = f"❌ К сожалению, генерация не удалась.\n\n"
        message_text += f"Запрос: {prompt[:200]}...\n\n"
        message_text += "Мы вернули 1 генерацию на ваш баланс. Попробуйте снова с другим описанием."
        
        await bot.send_message(
            chat_id=user_id,
            text=message_text
        )
        
        await bot.session.close()
        
        # Обновляем задачу, чтобы не обрабатывать ее снова
        execute_query_sync(
            "UPDATE generations SET audio_url = 'ERROR_NOTIFIED' WHERE task_id = %s",
            (task_id,)
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления об ошибке пользователю {user_id}: {e}")
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
