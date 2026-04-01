"""
Модуль для работы с клавиатурами VK бота
"""
import json
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

def get_all_genres_keyboard():
    """
    Полная клавиатура выбора жанра — все 17 жанров как обычная reply-клавиатура.
    Заменяет главное меню на период выбора жанра (как в Telegram-боте).
    10 строк × 2 кнопки — укладывается в лимит VK.
    """
    keyboard = VkKeyboard(one_time=False)  # Reply keyboard, не inline — заменяет главное меню

    # 8 рядов по 2 жанра
    genre_rows = [
        [("🎤 Поп", VkKeyboardColor.PRIMARY), ("🎸 Рок", VkKeyboardColor.PRIMARY)],
        [("🎺 Джаз", VkKeyboardColor.PRIMARY), ("🎵 Блюз", VkKeyboardColor.PRIMARY)],
        [("🎧 Хип-хоп", VkKeyboardColor.PRIMARY), ("⚡ Электронная", VkKeyboardColor.PRIMARY)],
        [("🎻 Классическая", VkKeyboardColor.PRIMARY), ("💿 R&B/Соул", VkKeyboardColor.PRIMARY)],
        [("🌴 Регги", VkKeyboardColor.PRIMARY), ("🤠 Кантри", VkKeyboardColor.PRIMARY)],
        [("🤘 Метал", VkKeyboardColor.PRIMARY), ("🪕 Фолк", VkKeyboardColor.PRIMARY)],
        [("💃 Латины", VkKeyboardColor.PRIMARY), ("🎭 Панк", VkKeyboardColor.PRIMARY)],
        [("🕺 Фанк", VkKeyboardColor.PRIMARY), ("🎙️ Шансон", VkKeyboardColor.PRIMARY)],
        # Ряд 9: свой вариант
        [("✏️ Свой вариант", VkKeyboardColor.POSITIVE)],
        # Ряд 10: возврат в главное меню
        [("🏠 В главное меню", VkKeyboardColor.SECONDARY)],
    ]

    for i, row in enumerate(genre_rows):
        if i > 0:
            keyboard.add_line()
        for label, color in row:
            keyboard.add_button(label, color=color)

    return keyboard


def get_music_genres_keyboard():
    """Клавиатура выбора жанра музыки (все 17 жанров — как в Telegram)"""
    return get_all_genres_keyboard()

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
    """Клавиатура выбора жанра песни (все 17 жанров — как в Telegram)"""
    return get_all_genres_keyboard()

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
    """Клавиатура с опциями для готовой песни (callback-кнопки с payload)"""
    import json
    keyboard = VkKeyboard(inline=True)

    keyboard.add_callback_button(
        '🎤 Минусовка (1 токен)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "karaoke", "task_id": str(task_id)})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        '🎸 Кавер (1 токен)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "cover", "task_id": str(task_id)})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        '🎵 В WAV (2 токена)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "wav", "task_id": str(task_id)})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        '🔗 Поделиться',
        color=VkKeyboardColor.POSITIVE,
        payload=json.dumps({"action": "share", "task_id": str(task_id)})
    )

    return keyboard

def get_version_selection_keyboard(task_id, action_type):
    """
    Клавиатура выбора версии для минусовки, кавера или WAV
    Args:
        task_id: ID задачи
        action_type: Тип действия ('karaoke', 'cover', 'wav')
    """
    import json
    keyboard = VkKeyboard(inline=True)
    
    keyboard.add_callback_button(
        '🎵 Версия 1',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": f"{action_type}_v1", "task_id": str(task_id)})
    )
    keyboard.add_callback_button(
        '🎵 Версия 2',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": f"{action_type}_v2", "task_id": str(task_id)})
    )
    
    return keyboard


def get_cover_genre_keyboard(task_id, version=0):
    """
    Клавиатура выбора жанра для кавера (callback-кнопки с payload)
    Args:
        task_id: ID задачи
        version: Версия трека (0 или 1)
    """
    import json
    keyboard = VkKeyboard(inline=False, one_time=True)  # Обычная клавиатура, не inline

    genres = [
        ("🎤 Поп", "Поп"),
        ("🎸 Рок", "Рок"),
        ("🎷 Джаз", "Джаз"),
        ("🎺 Блюз", "Блюз"),
        ("🎧 Хип-хоп", "Хип-хоп"),
        ("🎹 Электронная", "Электронная"),
        ("🎻 Классика", "Классика"),
        ("🎤 R&B", "R&B"),
        ("🥁 Регги", "Регги"),
        ("🎸 Кантри", "Кантри"),
        ("🎸 Метал", "Метал"),
        ("🪕 Фолк", "Фолк"),
        ("🎸 Панк", "Панк"),
        ("🎷 Фанк", "Фанк"),
        ("🎤 Шансон", "Шансон"),
        ("✍️ Другой", "Другой"),
    ]

    for i in range(0, len(genres), 2):
        if i > 0:
            keyboard.add_line()
        label1, genre1 = genres[i]
        keyboard.add_callback_button(
            label1,
            color=VkKeyboardColor.PRIMARY,
            payload=json.dumps({"action": "cover_genre", "task_id": str(task_id), "genre": genre1, "version": version})
        )
        if i + 1 < len(genres):
            label2, genre2 = genres[i + 1]
            keyboard.add_callback_button(
                label2,
                color=VkKeyboardColor.PRIMARY,
                payload=json.dumps({"action": "cover_genre", "task_id": str(task_id), "genre": genre2, "version": version})
            )

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
def get_payment_tariffs_keyboard():
    """Клавиатура с тарифами оплаты (inline-кнопки с callback)"""
    keyboard = VkKeyboard(inline=True)
    
    # Тарифы синхронизированы с Telegram-ботом
    tariffs = [
        ("💫 1 токен — 50₽", 50),
        ("💳 10 токенов — 250₽", 250),
        ("🔥 25 токенов — 500₽", 500),
        ("⭐ 60 токенов — 1000₽", 1000),
        ("💎 140 токенов — 2000₽", 2000)
    ]
    
    for label, amount in tariffs:
        keyboard.add_callback_button(
            label=label,
            color=VkKeyboardColor.POSITIVE,
            payload=json.dumps({"action": "payment", "amount": amount})
        )
        keyboard.add_line()
    
    # Кнопка приглашения друга
    keyboard.add_callback_button(
        label="🌟 Пригласить друга (+2 токена)",
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "invite_friend"})
    )
    
    return keyboard

def get_track_actions_keyboard(task_id, has_two_variants=False):
    """Клавиатура действий с треком (inline-кнопки)"""
    keyboard = VkKeyboard(inline=True)
    
    if has_two_variants:
        # Если 2 варианта - кнопки для прослушивания
        keyboard.add_callback_button(
            label="🎧 Вариант 1",
            color=VkKeyboardColor.PRIMARY,
            payload=json.dumps({"action": "play", "task_id": str(task_id), "variant": 1})
        )
        keyboard.add_callback_button(
            label="🎧 Вариант 2",
            color=VkKeyboardColor.PRIMARY,
            payload=json.dumps({"action": "play", "task_id": str(task_id), "variant": 2})
        )
        keyboard.add_line()
    
    # Доп. функции
    keyboard.add_callback_button(
        label="🎤 Минусовка (1 токен)",
        color=VkKeyboardColor.SECONDARY,
        payload=json.dumps({"action": "karaoke", "task_id": str(task_id)})
    )
    keyboard.add_callback_button(
        label="🎸 Кавер (1 токен)",
        color=VkKeyboardColor.SECONDARY,
        payload=json.dumps({"action": "cover", "task_id": str(task_id)})
    )
    keyboard.add_line()
    
    keyboard.add_callback_button(
        label="🎵 В WAV (2 токена)",
        color=VkKeyboardColor.SECONDARY,
        payload=json.dumps({"action": "wav", "task_id": str(task_id)})
    )
    
    return keyboard

def get_music_result_keyboard(urls, task_id=None, suno_ids=None):
    """Клавиатура с ссылками на варианты музыки.
    
    Для каждого трека показывает две кнопки в одной строке:
      🎧 Слушать  — открывает Suno веб-плеер (без скачивания, удобно на телефоне)
      ⬇️ Скачать  — прямая CDN-ссылка для сохранения MP3
    
    Args:
        urls:      str или list — CDN-ссылки на MP3 (может быть JSON-массив)
        task_id:   опционально, не используется в этой функции
        suno_ids:  str или list — ID треков Suno (может быть JSON-массив или строка)
    """
    import json as _json

    keyboard = VkKeyboard(inline=True)

    # --- Парсим CDN-ссылки ---
    try:
        url_list = _json.loads(urls) if isinstance(urls, str) and urls.startswith('[') else [urls]
    except Exception:
        url_list = [urls] if isinstance(urls, str) else list(urls)

    # --- Парсим Suno ID-шники ---
    sid_list = []
    if suno_ids:
        try:
            if isinstance(suno_ids, str) and suno_ids.startswith('['):
                sid_list = _json.loads(suno_ids)
            elif isinstance(suno_ids, str):
                sid_list = [suno_ids]
            elif isinstance(suno_ids, list):
                sid_list = suno_ids
        except Exception:
            sid_list = [str(suno_ids)] if suno_ids else []

    # --- Добавляем кнопки для каждого варианта ---
    for i, cdn_url in enumerate(url_list, 1):
        variant_label = f" вариант {i}" if len(url_list) > 1 else ""

        # Ссылка для прослушивания: Suno веб-плеер (если есть ID) или CDN
        suno_id = sid_list[i - 1] if i - 1 < len(sid_list) else None
        listen_url = f"https://suno.com/song/{suno_id}" if suno_id else cdn_url

        # Кнопка "Слушать" — открывает плеер, НЕ скачивает
        keyboard.add_openlink_button(
            label=f"🎧 Слушать{variant_label}",
            link=listen_url
        )

        # Кнопка "Скачать" — прямой MP3 для сохранения
        keyboard.add_openlink_button(
            label=f"⬇️ Скачать{variant_label}",
            link=cdn_url
        )

        if i < len(url_list):
            keyboard.add_line()

    return keyboard
