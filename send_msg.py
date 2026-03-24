import asyncio
from aiogram import Bot
from config import BOT_TOKEN

async def send():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(5665028343, "🎁 Привет! Приносим извинения за техническую ошибку.\n\nМы начислили тебе 2 токена за приглашённых друзей! Спасибо что пользуешься нашим ботом 🎵\n\nТеперь всё работает корректно!")
    await bot.session.close()

asyncio.run(send())
