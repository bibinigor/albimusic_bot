import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command

logging.basicConfig(level=logging.DEBUG)

API_TOKEN = '8078747945:AAELaCEzbPUdwwilFBy_TJi9LsBb5scyzVU'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(Command('start'))
async def cmd_start(message: types.Message):
    print("=== ХЭНДЛЕР START ВЫЗВАН ===")
    await message.answer("Тестовый ответ от бота!")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=False)
