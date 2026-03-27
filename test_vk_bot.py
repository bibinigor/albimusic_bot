#!/usr/bin/env python3
"""
Скрипт для тестирования функциональности VK бота
"""
import logging
import sys
from main_vk import VKBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_bot_initialization():
    """Тестирование инициализации бота"""
    try:
        bot = VKBot()
        logger.info("✅ Бот успешно инициализирован")
        return bot
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        return None

def test_keyboards(bot):
    """Тестирование клавиатур"""
    try:
        # Тестирование главной клавиатуры
        main_keyboard = bot.get_main_keyboard()
        logger.info("✅ Главная клавиатура успешно создана")
        
        # Тестирование клавиатуры выбора стиля музыки
        music_style_keyboard = bot.get_music_style_keyboard()
        logger.info("✅ Клавиатура выбора стиля музыки успешно создана")
        
        # Тестирование клавиатуры с кнопкой возврата в главное меню
        home_keyboard = bot.get_home_keyboard()
        logger.info("✅ Клавиатура с кнопкой возврата в главное меню успешно создана")
        
        # Тестирование клавиатуры с кнопкой отмены
        cancel_keyboard = bot.get_cancel_keyboard()
        logger.info("✅ Клавиатура с кнопкой отмены успешно создана")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания клавиатур: {e}")
        return False

def test_state_management(bot):
    """Тестирование управления состояниями"""
    try:
        # Тестирование сброса состояния
        bot.reset_state(123456789)  # Тестовый ID пользователя
        logger.info("✅ Сброс состояния успешно выполнен")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка управления состояниями: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("🧪 Начало тестирования VK бота")
    
    # Тестирование инициализации бота
    bot = test_bot_initialization()
    if not bot:
        logger.error("❌ Тестирование прервано из-за ошибки инициализации")
        return
    
    # Тестирование клавиатур
    if not test_keyboards(bot):
        logger.error("❌ Тестирование прервано из-за ошибки создания клавиатур")
        return
    
    # Тестирование управления состояниями
    if not test_state_management(bot):
        logger.error("❌ Тестирование прервано из-за ошибки управления состояниями")
        return
    
    logger.info("✅ Все тесты успешно пройдены")
    logger.info("🚀 Бот готов к запуску")

if __name__ == "__main__":
    main()