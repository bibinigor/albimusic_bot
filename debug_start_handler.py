# Добавляем этот код в начало main_with_payments.py для отладки
import logging
logging.basicConfig(level=logging.DEBUG)

# Создадим простейший хэндлер который точно сработает
from aiogram.dispatcher.filters import Command
from aiogram import types

@dp.message_handler(Command('start'))
async def debug_cmd_start(message: types.Message):
    print("=== ДЕБАГ ХЭНДЛЕР START ВЫЗВАН ===")
    print(f"User: {message.from_user.id}, Chat: {message.chat.id}")
    await message.answer("ДЕБАГ: Бот работает! Основной обработчик не сработал.")
