#!/usr/bin/env python3
"""
Непрерывный монитор уведомлений AlBi-music Bot
Логирование через stdout → systemd journald
"""

import sys
import asyncio
import logging
import time
from datetime import datetime

# ========================================
# НАСТРОЙКА ЛОГИРОВАНИЯ ДЛЯ SYSTEMD
# ========================================

# Создаем logger
logger = logging.getLogger('albimusic_monitor')
logger.setLevel(logging.INFO)

# Хендлер для stdout (пойдет в journald)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Форматтер (journald автоматически добавит timestamp)
formatter = logging.Formatter(
    '%(levelname)s - %(name)s - %(message)s'
)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# ========================================
# ИМПОРТЫ
# ========================================

try:
    import config
    from db_utils import execute_query_sync
    from aiogram import Bot
    
    logger.info("✅ Модули импортированы успешно")
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать модули: {e}")
    sys.exit(1)

# ========================================
# ФУНКЦИИ УВЕДОМЛЕНИЙ
# ========================================

async def notify_completed_task(bot, task_id, user_id, audio_url, prompt):
    """Отправляет уведомление пользователю о завершенной задаче"""
    try:
        message_text = f"🎵 Ваша музыка готова!\n\n"
        if prompt:
            message_text += f"📝 Запрос: {prompt}\n\n"
        message_text += f"🎧 Ссылка: {audio_url}\n\n"
        message_text += "Музыка также опубликована в канале @ALBImusic_chart"
        
        await bot.send_message(chat_id=user_id, text=message_text)
        logger.info(f"✅ Уведомление для задачи {task_id} отправлено пользователю {user_id}")
        
        # Помечаем как отправленное
        execute_query_sync(
            "UPDATE generations SET notified = TRUE WHERE task_id = %s",
            (task_id,)
        )
        logger.info(f"✅ Задача {task_id} помечена как отправленная")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления для задачи {task_id}: {str(e)}")
        return False

async def notify_error_task(bot, task_id, user_id, prompt):
    """Отправляет уведомление пользователю о неудачной задаче"""
    try:
        message_text = f"❌ К сожалению, генерация не удалась.\n\n"
        if prompt:
            message_text += f"📝 Запрос: {prompt}\n\n"
        message_text += "Попробуйте снова или обратитесь в поддержку."
        
        await bot.send_message(chat_id=user_id, text=message_text)
        logger.info(f"📨 Уведомление об ошибке для задачи {task_id} отправлено пользователю {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления об ошибке для задачи {task_id}: {str(e)}")
        return False

async def check_completed_tasks():
    """Проверяет завершенные задачи и отправляет уведомления"""
    logger.info("🔄 Проверка завершенных задач...")
    
    try:
        # Инициализируем бота
        bot = Bot(token=config.BOT_TOKEN)
        
        # Получаем завершенные задачи, которые еще не были уведомлены
        query = """
            SELECT task_id, user_id, prompt, audio_url, status 
            FROM generations 
            WHERE notified = FALSE 
              AND (status = 'completed' OR status = 'error')
            ORDER BY created_at ASC
            LIMIT 10
        """
        
        tasks = execute_query_sync(query)
        
        if not tasks:
            logger.info("📭 Нет новых завершенных задач для уведомления")
            await bot.session.close()
            return
        
        logger.info(f"📨 Найдено {len(tasks)} задач для уведомления")
        
        for task in tasks:
            task_id, user_id, prompt, audio_url, status = task
            
            logger.info(f"📨 Найдена задача {task_id} для пользователя {user_id} (статус: {status})")
            
            if status == 'completed':
                await notify_completed_task(bot, task_id, user_id, audio_url, prompt)
            elif status == 'error':
                await notify_error_task(bot, task_id, user_id, prompt)
            
            # Небольшая пауза между отправками
            await asyncio.sleep(0.5)
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке задач: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

# ========================================
# ГЛАВНЫЙ ЦИКЛ
# ========================================

async def main_loop():
    """Главный цикл мониторинга"""
    logger.info("╔═══════════════════════════════════════════════════════════╗")
    logger.info("║       AlBi-music Monitor Started                          ║")
    logger.info("╚═══════════════════════════════════════════════════════════╝")
    
    iteration = 0
    errors_count = 0
    max_consecutive_errors = 10
    
    while True:
        iteration += 1
        
        try:
            logger.info(f"🔄 Итерация #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Вызываем проверку и отправку уведомлений
            await check_completed_tasks()
            
            # Сбрасываем счетчик ошибок
            errors_count = 0
            
            # Пауза перед следующей проверкой
            logger.debug(f"💤 Пауза 30 секунд...")
            await asyncio.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("⚠️  Получен сигнал остановки (Ctrl+C)")
            break
            
        except Exception as e:
            errors_count += 1
            logger.error(f"❌ Ошибка в итерации #{iteration}: {e}", exc_info=True)
            
            if errors_count >= max_consecutive_errors:
                logger.critical(f"🔥 Превышено максимальное количество последовательных ошибок ({max_consecutive_errors})")
                logger.critical("🔥 Монитор завершает работу")
                sys.exit(1)
            
            logger.info(f"⏳ Пауза 60 секунд после ошибки...")
            await asyncio.sleep(60)

async def main():
    try:
        await main_loop()
    finally:
        logger.info("╔═══════════════════════════════════════════════════════════╗")
        logger.info("║       AlBi-music Monitor Stopped                          ║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    asyncio.run(main())
