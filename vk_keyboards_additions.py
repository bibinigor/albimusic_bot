"""
Дополнительные клавиатуры для VK-бота
"""
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_lyrics_variants_keyboard():
    """Клавиатура выбора варианта текста песни"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button('✅ Использовать этот текст', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🔄 Сгенерировать другой', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('✍️ Написать свой текст', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard

def get_song_genres_keyboard():
    """Клавиатура выбора жанра песни"""
    keyboard = VkKeyboard(inline=True)
    genres = [
        ("🎤 Поп", VkKeyboardColor.PRIMARY),
        ("🎸 Рок", VkKeyboardColor.PRIMARY),
        ("🎺 Джаз", VkKeyboardColor.PRIMARY),
        ("🎵 Блюз", VkKeyboardColor.PRIMARY),
        ("🎧 Хип-хоп", VkKeyboardColor.PRIMARY),
        ("⚡ Электронная", VkKeyboardColor.PRIMARY),
        ("🎻 Классическая", VkKeyboardColor.PRIMARY),
        ("💿 R&B/Соул", VkKeyboardColor.PRIMARY),
        ("🌴 Регги", VkKeyboardColor.PRIMARY),
        ("🤠 Кантри", VkKeyboardColor.PRIMARY),
        ("🤘 Метал", VkKeyboardColor.PRIMARY),
        ("🪕 Фолк", VkKeyboardColor.PRIMARY),
        ("💃 Латины", VkKeyboardColor.PRIMARY),
        ("🎭 Панк", VkKeyboardColor.PRIMARY),
        ("🕺 Фанк", VkKeyboardColor.PRIMARY),
        ("🎙️ Шансон", VkKeyboardColor.PRIMARY),
        ("✏️ Свой вариант", VkKeyboardColor.POSITIVE)
    ]
    
    # Добавляем жанры в клавиатуру (максимум 2 кнопки в ряду для ВК)
    for i in range(0, len(genres), 2):
        if i > 0:
            keyboard.add_line()
        keyboard.add_button(genres[i][0], color=genres[i][1])
        if i + 1 < len(genres):
            keyboard.add_button(genres[i+1][0], color=genres[i+1][1])
    
    # Добавляем кнопку возврата в главное меню
    keyboard.add_line()
    keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.PRIMARY)
    
    return keyboard

def get_tracks_navigation_keyboard(page, total_pages):
    """Клавиатура навигации по страницам треков"""
    keyboard = VkKeyboard(one_time=False)
    
    # Добавляем кнопки навигации
    if page > 1:
        keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.SECONDARY)
    
    if page < total_pages:
        keyboard.add_button("➡️ Вперед", color=VkKeyboardColor.PRIMARY)
    
    return keyboard

def get_track_actions_keyboard():
    """Клавиатура действий с треком"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button("🎧 Слушать", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📤 Поделиться", color=VkKeyboardColor.SECONDARY)
    
    return keyboard

def get_balance_keyboard():
    """Клавиатура для страницы баланса"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button("💫 1 токен - 50₽", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("💳 10 токенов - 250₽", color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button("🔥 25 токенов - 500₽", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("⭐ 60 токенов - 1000₽", color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button("💎 140 токенов - 2000₽", color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button("🎁 Пригласить друга", color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.SECONDARY)
    
    return keyboard