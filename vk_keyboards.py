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

    # 🔥 СТАРТОВЫЙ ПАКЕТ — самая выгодная первая покупка
    keyboard.add_button("🎁 5 токенов — 99₽ (старт)", color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button("💫 1 токен — 50₽", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("💳 10 токенов — 250₽", color=VkKeyboardColor.POSITIVE)

    keyboard.add_line()
    keyboard.add_button("🔥 25 токенов — 500₽", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("⭐ 60 токенов — 1000₽", color=VkKeyboardColor.POSITIVE)

    keyboard.add_line()
    keyboard.add_button("💎 140 токенов — 2000₽", color=VkKeyboardColor.POSITIVE)

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
        ("🎁 5 токенов — 99₽ (старт)", 99),   # ← стартовый пакет вверху
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


def get_buy_more_keyboard():
    """Inline-клавиатура «Создать ещё» — показывается сразу после результата генерации.
    Цель: предложить следующую генерацию пока эмоции ещё свежи."""
    keyboard = VkKeyboard(inline=True)

    keyboard.add_callback_button(
        label="🎁 5 треков — 99₽ (старт)",
        color=VkKeyboardColor.NEGATIVE,
        payload=json.dumps({"action": "payment", "amount": 99})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        label="💳 10 треков — 250₽",
        color=VkKeyboardColor.POSITIVE,
        payload=json.dumps({"action": "payment", "amount": 250})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        label="🌟 Пригласить друга (+2 бесплатно)",
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
    """Клавиатура с кнопками «Слушать» и «Скачать» для каждого варианта.

    «Слушать» — open_link кнопка: открывает HTML5-плеер albi-music.ru напрямую,
    пользователь сразу переходит по ссылке без дополнительных сообщений.

    «Скачать» — open_link кнопка: прямая CDN-ссылка, скачивает MP3 на устройство.

    Примечание: VK API не поддерживает цвет для openlink-кнопок, поэтому
    обе кнопки белые — различаются иконками (🎵 vs ⬇️).

    Args:
        urls:     str или list — CDN-ссылки на MP3 (может быть JSON-массив)
        task_id:  не используется (оставлен для обратной совместимости)
        suno_ids: не используется (оставлен для обратной совместимости)
    """
    import json as _json
    import urllib.parse as _urlparse

    keyboard = VkKeyboard(inline=True)

    # --- Парсим CDN-ссылки ---
    try:
        url_list = _json.loads(urls) if isinstance(urls, str) and urls.startswith('[') else [urls]
    except Exception:
        url_list = [urls] if isinstance(urls, str) else list(urls)

    # --- Для каждого варианта: «Слушать» (openlink → плеер) + «Скачать» (openlink → MP3) ---
    for i, cdn_url in enumerate(url_list, 1):
        variant_label = f" вариант {i}" if len(url_list) > 1 else ""
        cdn_url_str = str(cdn_url)

        # Формируем URL плеера: https://albi-music.ru/player?url=<encoded>&title=ALBI+Music
        encoded_cdn = _urlparse.quote(cdn_url_str, safe='')
        player_url = f"https://albi-music.ru/player?url={encoded_cdn}&title=ALBI+Music"

        # «Слушать» — open_link, открывает плеер напрямую (пользователь сразу переходит)
        keyboard.add_openlink_button(
            label=f"🎵 Слушать{variant_label}",
            link=player_url
        )

        # «Скачать» — open_link, прямое скачивание MP3
        keyboard.add_openlink_button(
            label=f"⬇️ Скачать{variant_label}",
            link=cdn_url_str
        )

        if i < len(url_list):
            keyboard.add_line()

    return keyboard
