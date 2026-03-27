"""
Модуль для работы с клавиатурами VK бота
"""
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard(user_id=None):
    """
    Основная клавиатура бота
    Args:
        user_id: ID пользователя VK для проверки прав администратора
    """
    from vk_config import ADMIN_VK_ID
    
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🎵 Создать песню', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎶 Создать музыку', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('📂 Мои треки', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('💰 Баланс', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('🎧 Примеры песен', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('📞 Поддержка', color=VkKeyboardColor.SECONDARY)
    
    # Добавляем кнопку админ-панели только для администратора
    if user_id and user_id == ADMIN_VK_ID:
        keyboard.add_line()
        keyboard.add_button('⚙️ Админ', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard

def get_music_style_keyboard():
    """Клавиатура выбора стиля музыки"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button('🎸 Рок', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎹 Поп', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎷 Джаз', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('🎼 Классика', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎵 Электронная', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('✍️ Свой стиль', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard

def get_song_type_keyboard():
    """Клавиатура выбора типа создания песни"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button('Придумать текст', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('✍️ Свой текст', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard

def get_confirm_keyboard():
    """Клавиатура подтверждения действия"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button('✅ Да', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('❌ Нет', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены/возврата в меню"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🏠 В главное меню', color=VkKeyboardColor.PRIMARY)
    return keyboard

def get_home_keyboard():
    """Клавиатура с кнопкой возврата в главное меню"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('🏠 В главное меню', color=VkKeyboardColor.SECONDARY)
    return keyboard

def get_music_genres_keyboard():
    """Клавиатура выбора жанра музыки"""
    keyboard = VkKeyboard(inline=True)
    
    # Основные популярные жанры (сокращенный список)
    genres = [
        ("🎤 Поп", VkKeyboardColor.PRIMARY),
        ("🎸 Рок", VkKeyboardColor.PRIMARY),
        ("🎺 Джаз", VkKeyboardColor.PRIMARY),
        ("⚡ Электронная", VkKeyboardColor.PRIMARY),
        ("🎻 Классика", VkKeyboardColor.PRIMARY),
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

def get_tokens_keyboard():
    """Клавиатура выбора количества токенов для покупки"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button('5 токенов - 149₽', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('10 токенов - 249₽', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('20 токенов - 449₽', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('50 токенов - 999₽', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard

def get_payment_keyboard(payment_url: str):
    """Клавиатура с кнопкой оплаты"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_openlink_button(
        label='💳 Оплатить',
        link=payment_url
    )
    
    return keyboard

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
    
    # Основные популярные жанры (сокращенный список)
    genres = [
        ("🎤 Поп", VkKeyboardColor.PRIMARY),
        ("🎸 Рок", VkKeyboardColor.PRIMARY),
        ("🎺 Джаз", VkKeyboardColor.PRIMARY),
        ("⚡ Электронная", VkKeyboardColor.PRIMARY),
        ("🎻 Классика", VkKeyboardColor.PRIMARY),
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

def get_balance_actions_keyboard():
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

def get_lyrics_variants_selection_keyboard():
    """Клавиатура выбора варианта текста после генерации"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button('Выбрать вариант 1', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Выбрать вариант 2', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Написать свой текст', color=VkKeyboardColor.SECONDARY)
    
    return keyboard

def get_song_options_keyboard(task_id):
    """Клавиатура с опциями для готовой песни"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button('🎤 Минусовка (1 токен)', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🎸 Кавер (1 токен)', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🎵 В WAV (2 токена)', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('📢 Отправить в канал', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('🔗 Поделиться', color=VkKeyboardColor.POSITIVE)
    
    return keyboard

def get_vocal_gender_keyboard():
    """Клавиатура выбора пола вокалиста"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button('👨 Мужской', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('👩 Женский', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('🏠 В главное меню', color=VkKeyboardColor.SECONDARY)
    
    return keyboard

def get_lyrics_variants_keyboard_with_two_options():
    """Клавиатура выбора между двумя вариантами текста после генерации"""
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_button('Выбрать вариант 1', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Выбрать вариант 2', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Написать свой текст', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('🔄 Сгенерировать другие', color=VkKeyboardColor.POSITIVE)
    
    return keyboard