import asyncio
from aiogram import Bot
from config import BOT_TOKEN

async def send():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(8564538095, "🎁 Привет! Приносим извинения за техническую ошибку.\n\nМы вернули тебе 2 токена за неудачные генерации. Ошибка исправлена, теперь всё работает! 🎵\n\nПопробуй создать песню снова!")
    await bot.session.close()

asyncio.run(send())
