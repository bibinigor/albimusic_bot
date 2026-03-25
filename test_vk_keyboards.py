"""
Тестовый скрипт для проверки клавиатур VK-бота
"""
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import logging
import json
from vk_config import VK_TOKEN, VK_GROUP_ID, ADMIN_VK_ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_keyboard(keyboard_name, keyboard):
    """Выводит информацию о клавиатуре в консоль"""
    if isinstance(keyboard, VkKeyboard):
        keyboard_json = keyboard.get_keyboard()
        keyboard_dict = json.loads(keyboard_json)
        
        logger.info(f"Клавиатура: {keyboard_name}")
        logger.info(f"Тип: {'inline' if keyboard.inline else 'обычная'}")
        
        for i, row in enumerate(keyboard_dict.get('buttons', [])):
            logger.info(f"Ряд {i+1}:")
            for j, button in enumerate(row):
                action = button.get('action', {})
                logger.info(f"  Кнопка {j+1}: {action.get('label', 'Без текста')} (тип: {action.get('type', 'неизвестно')})")
        
        logger.info("=" * 40)
    else:
        logger.error(f"Объект {keyboard_name} не является клавиатурой VK")

def test_keyboards():
    """Тестирует все клавиатуры VK-бота"""
    from vk_keyboards import (
        get_main_keyboard,
        get_music_style_keyboard,
        get_song_type_keyboard,
        get_confirm_keyboard,
        get_cancel_keyboard,
        get_home_keyboard,
        get_music_genres_keyboard,
        get_tokens_keyboard,
        get_payment_keyboard,
        get_lyrics_variants_keyboard,
        get_song_genres_keyboard,
        get_tracks_navigation_keyboard,
        get_track_actions_keyboard,
        get_balance_actions_keyboard
    )
    
    # Тестируем основные клавиатуры
    print_keyboard("Главная клавиатура", get_main_keyboard())
    print_keyboard("Клавиатура выбора стиля музыки", get_music_style_keyboard())
    print_keyboard("Клавиатура выбора типа песни", get_song_type_keyboard())
    print_keyboard("Клавиатура подтверждения", get_confirm_keyboard())
    print_keyboard("Клавиатура отмены", get_cancel_keyboard())
    print_keyboard("Клавиатура возврата в главное меню", get_home_keyboard())
    
    # Тестируем клавиатуры для создания музыки
    print_keyboard("Клавиатура выбора жанра музыки", get_music_genres_keyboard())
    
    # Тестируем клавиатуры для создания песни
    print_keyboard("Клавиатура выбора варианта текста", get_lyrics_variants_keyboard())
    print_keyboard("Клавиатура выбора жанра песни", get_song_genres_keyboard())
    
    # Тестируем клавиатуры для треков
    print_keyboard("Клавиатура навигации по трекам (стр. 1 из 3)", get_tracks_navigation_keyboard(1, 3))
    print_keyboard("Клавиатура навигации по трекам (стр. 2 из 3)", get_tracks_navigation_keyboard(2, 3))
    print_keyboard("Клавиатура действий с треком", get_track_actions_keyboard())
    
    # Тестируем клавиатуры для баланса и платежей
    print_keyboard("Клавиатура выбора токенов", get_tokens_keyboard())
    print_keyboard("Клавиатура оплаты", get_payment_keyboard("https://example.com/payment"))
    print_keyboard("Клавиатура действий с балансом", get_balance_actions_keyboard())

if __name__ == "__main__":
    logger.info("Начинаем тестирование клавиатур VK-бота")
    test_keyboards()
    logger.info("Тестирование клавиатур завершено")