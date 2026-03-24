from db_utils import execute_query_sync, init_db_pool_sync
import asyncio
from aiogram import Bot
import config

async def send_apology_message():
    # Инициализируем бота
    bot = Bot(token=config.BOT_TOKEN)
    
    try:
        # Получаем user_id
        user_info = execute_query_sync(
            "SELECT user_id FROM users WHERE username = 'rasablen'",
            ()
        )
        
        if user_info:
            user_id = user_info[0][0]
            
            # Отправляем сообщение
            message = (
                "🙏 Приносим извинения за технический сбой!\n\n"
                "✅ Мы восстановили ваши 2 токена за приглашенного друга.\n"
                "💰 Ваш текущий баланс: 2 токена\n\n"
                "Теперь вы можете создать свою первую песню! 🎵\n"
                "Жмите «Создать песню» в меню 👇"
            )
            
            await bot.send_message(user_id, message)
            print("✅ Сообщение отправлено успешно")
            
        else:
            print("❌ Пользователь не найден")
            
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
    
    finally:
        await bot.close()

# Инициализируем пул соединений с БД
init_db_pool_sync()

# Запускаем отправку сообщения
asyncio.run(send_apology_message())