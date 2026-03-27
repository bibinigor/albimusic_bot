"""
БЛОК 6: ИНТЕГРАЦИЯ ЗАГРУЗКИ ФАЙЛОВ ДЛЯ КАВЕРА/МИНУСОВКИ В VK-БОТ

Добавляет:
1. Загрузку аудиофайлов для создания кавера
2. Загрузку аудиофайлов для создания минусовки
3. Валидацию файлов (длительность ≤ 5 мин, размер ≤ 20 МБ)
4. Выбор жанра для загруженного файла (кавер)

ПРИМЕНЕНИЕ:
1. Добавить в импорты main_vk.py:
   from vk_file_upload import process_uploaded_audio, cleanup_temp_file
   from vk_states import States

2. Добавить состояния в vk_states.py:
   WAITING_KARAOKE_UPLOAD = auto()
   WAITING_COVER_UPLOAD = auto()
   WAITING_COVER_UPLOAD_GENRE = auto()

3. Добавить все handler'ы из этого файла в main_vk.py
"""

import logging
import uuid
import asyncio
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_file_upload import process_uploaded_audio, cleanup_temp_file
from vk_states import States
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# МИНУСОВКА ИЗ ЗАГРУЖЕННОГО ФАЙЛА
# ════════════════════════════════════════════════════════════════

def handle_karaoke_upload_request(self, user_id):
    """
    Начать процесс загрузки файла для минусовки
    
    Args:
        user_id: ID пользователя
    """
    import asyncio
    from vk_config import ADMIN_IDS
    
    # Проверка баланса
    balance = execute_query_sync(
        "SELECT balance FROM users WHERE user_id = %s",
        (user_id,)
    )
    
    if balance and balance[0][0] < 1 and user_id not in ADMIN_IDS:
        self.send_message(
            user_id,
            "❌ **Недостаточно токенов!**\n\n"
            "💰 Стоимость минусовки: 1 токен\n\n"
            "Нажмите 💰 Баланс для пополнения"
        )
        return
    
    # Устанавливаем состояние
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.set_state(user_id, States.WAITING_AUDIO_UPLOAD)
    )
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.update_data(user_id, upload_type='karaoke')
    )
    
    self.send_message(
        user_id,
        "🎤 **СОЗДАНИЕ МИНУСОВКИ**\n\n"
        "📤 Отправьте аудиофайл (MP3, WAV и др.)\n\n"
        "⚠️ **Требования:**\n"
        "├ Длительность: до 5 минут\n"
        "└ Размер: до 20 МБ\n\n"
        "💡 Напишите 'отмена' для отмены"
    )


def handle_karaoke_audio_upload(self, user_id, attachment):
    """
    Обработать загруженный audio файл для минусовки
    
    Args:
        user_id: ID пользователя
        attachment: Вложение из сообщения VK
    """
    import asyncio
    from vk_config import ADMIN_IDS
    
    # Получаем данные из состояния
    data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    )
    
    if not data or data.get('upload_type') != 'karaoke':
        self.send_message(user_id, "❌ Ошибка: неверное состояние")
        return
    
    self.send_message(user_id, "⏳ Обрабатываю файл...")
    
    # Обрабатываем файл
    success, server_url, local_path, error = process_uploaded_audio(
        self.vk,
        attachment,
        max_duration=300,
        max_size_mb=20
    )
    
    if not success:
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        self.send_message(
            user_id,
            f"❌ {error}\n\nПопробуйте другой файл или обрежьте текущий."
        )
        return
    
    # Списываем токен (кроме админов)
    if user_id not in ADMIN_IDS:
        execute_query_sync(
            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
            (user_id,)
        )
    
    # Сбрасываем состояние
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.finish(user_id)
    )
    
    self.send_message(
        user_id,
        "✅ Файл загружен!\n\n"
        "🎤 Создаю минусовку...\n"
        "⏰ Подождите 1-2 минуты"
    )
    
    # Создаем Celery задачу
    try:
        from celery_tasks import generate_karaoke_from_upload_task
        
        task_id = str(uuid.uuid4())
        celery_task = generate_karaoke_from_upload_task.apply_async(
            args=[user_id, server_url],
            kwargs={'task_id': task_id},
            queue='generation'
        )
        
        logger.info(f"🎤 Минусовка задача создана: {task_id} для {user_id}, URL: {server_url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания Celery задачи: {e}")
        self.send_message(
            user_id,
            "❌ Ошибка запуска генерации. Попробуйте позже."
        )
    finally:
        # Удаляем временный файл
        cleanup_temp_file(local_path)


# ════════════════════════════════════════════════════════════════
# КАВЕР ИЗ ЗАГРУЖЕННОГО ФАЙЛА
# ════════════════════════════════════════════════════════════════

def handle_cover_upload_request(self, user_id):
    """
    Начать процесс загрузки файла для кавера
    
    Args:
        user_id: ID пользователя
    """
    import asyncio
    from vk_config import ADMIN_IDS
    
    # Проверка баланса
    balance = execute_query_sync(
        "SELECT balance FROM users WHERE user_id = %s",
        (user_id,)
    )
    
    if balance and balance[0][0] < 2 and user_id not in ADMIN_IDS:
        self.send_message(
            user_id,
            "❌ **Недостаточно токенов!**\n\n"
            "💰 Стоимость кавера: 2 токена\n\n"
            "Нажмите 💰 Баланс для пополнения"
        )
        return
    
    # Устанавливаем состояние
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.set_state(user_id, States.WAITING_AUDIO_UPLOAD)
    )
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.update_data(user_id, upload_type='cover')
    )
    
    self.send_message(
        user_id,
        "🎸 **СОЗДАНИЕ КАВЕРА**\n\n"
        "📤 Отправьте аудиофайл (MP3, WAV и др.)\n\n"
        "⚠️ **Требования:**\n"
        "├ Длительность: до 5 минут\n"
        "└ Размер: до 20 МБ\n\n"
        "💡 Напишите 'отмена' для отмены"
    )


def handle_cover_audio_upload(self, user_id, attachment):
    """
    Обработать загруженный audio файл для кавера
    
    Args:
        user_id: ID пользователя
        attachment: Вложение из сообщения VK
    """
    import asyncio
    from vk_config import ADMIN_IDS
    
    # Получаем данные из состояния
    data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    )
    
    if not data or data.get('upload_type') != 'cover':
        self.send_message(user_id, "❌ Ошибка: неверное состояние")
        return
    
    self.send_message(user_id, "⏳ Обрабатываю файл...")
    
    # Обрабатываем файл
    success, server_url, local_path, error = process_uploaded_audio(
        self.vk,
        attachment,
        max_duration=300,
        max_size_mb=20
    )
    
    if not success:
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        self.send_message(
            user_id,
            f"❌ {error}\n\nПопробуйте другой файл или обрежьте текущий."
        )
        return
    
    # Удаляем временный файл
    cleanup_temp_file(local_path)
    
    # Сохраняем URL в состоянии
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.update_data(user_id, cover_audio_url=server_url)
    )
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.set_state(user_id, States.WAITING_COVER_GENRE)
    )
    
    # Показываем выбор жанра
    show_cover_genre_selection(self, user_id)


def show_cover_genre_selection(self, user_id):
    """
    Показать выбор жанра для кавера
    
    Args:
        user_id: ID пользователя
    """
    keyboard = VkKeyboard(inline=True)
    
    genres = [
        ("🎤 Поп", "cover_upload_genre_pop"),
        ("🎸 Рок", "cover_upload_genre_rock"),
        ("🎺 Джаз", "cover_upload_genre_jazz"),
        ("🎵 Блюз", "cover_upload_genre_blues"),
        ("🎧 Хип-хоп", "cover_upload_genre_hiphop"),
        ("🔊 Электроника", "cover_upload_genre_electronic"),
        ("🎻 Классика", "cover_upload_genre_classical"),
        ("🎤 R&B", "cover_upload_genre_rnb"),
        ("🎵 Регги", "cover_upload_genre_reggae"),
        ("🤠 Кантри", "cover_upload_genre_country"),
        ("🤘 Метал", "cover_upload_genre_metal"),
        ("🎸 Фолк", "cover_upload_genre_folk"),
        ("💃 Латино", "cover_upload_genre_latin"),
        ("🎸 Панк", "cover_upload_genre_punk"),
        ("🎺 Фанк", "cover_upload_genre_funk"),
        ("🎤 Шансон", "cover_upload_genre_shanson"),
    ]
    
    # Добавляем по 2 кнопки в ряд
    for i in range(0, len(genres), 2):
        keyboard.add_callback_button(
            genres[i][0],
            color=VkKeyboardColor.PRIMARY,
            payload={"cmd": genres[i][1]}
        )
        if i + 1 < len(genres):
            keyboard.add_callback_button(
                genres[i+1][0],
                color=VkKeyboardColor.PRIMARY,
                payload={"cmd": genres[i+1][1]}
            )
        keyboard.add_line()
    
    keyboard.add_callback_button(
        "✏️ Свой вариант",
        color=VkKeyboardColor.SECONDARY,
        payload={"cmd": "cover_upload_genre_custom"}
    )
    
    self.send_message(
        user_id,
        "🎸 **ВЫБЕРИ В КАКОМ ЖАНРЕ СОЗДАТЬ КАВЕР:**",
        keyboard=keyboard.get_keyboard()
    )


def handle_cover_genre_selection(self, user_id, genre_code):
    """
    Обработать выбор жанра для кавера
    
    Args:
        user_id: ID пользователя
        genre_code: Код жанра (например, 'pop', 'rock')
    """
    import asyncio
    from vk_config import ADMIN_IDS
    
    genre_map = {
        "pop": "Поп",
        "rock": "Рок",
        "jazz": "Джаз",
        "blues": "Блюз",
        "hiphop": "Хип-хоп",
        "electronic": "Электроника",
        "classical": "Классика",
        "rnb": "R&B",
        "reggae": "Регги",
        "country": "Кантри",
        "metal": "Метал",
        "folk": "Фолк",
        "latin": "Латино",
        "punk": "Панк",
        "funk": "Фанк",
        "shanson": "Шансон",
    }
    
    if genre_code == "custom":
        # Ожидаем ввод своего жанра
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.set_state(user_id, States.WAITING_CUSTOM_COVER_GENRE)
        )
        self.send_message(
            user_id,
            "✏️ **Опиши свой жанр:**\n\n"
            "Например: синти-поп 80-х, акустический инди, тяжелый метал"
        )
        return
    
    genre_name = genre_map.get(genre_code, "Поп")
    
    # Получаем сохраненный URL из состояния
    data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    )
    
    if not data or 'cover_audio_url' not in data:
        self.send_message(user_id, "❌ Ошибка: файл не найден")
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        return
    
    server_url = data['cover_audio_url']
    
    # Списываем токены (кроме админов)
    if user_id not in ADMIN_IDS:
        execute_query_sync(
            "UPDATE users SET balance = balance - 2 WHERE user_id = %s",
            (user_id,)
        )
    
    # Сбрасываем состояние
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.finish(user_id)
    )
    
    self.send_message(
        user_id,
        f"🎸 Создаю кавер в стиле **{genre_name}**...\n\n"
        f"⏰ Подождите 3-5 минут"
    )
    
    # Создаем Celery задачу
    try:
        from celery_tasks import generate_cover_from_upload_task
        
        task_id = str(uuid.uuid4())
        celery_task = generate_cover_from_upload_task.apply_async(
            args=[user_id, server_url, genre_name],
            kwargs={'task_id': task_id},
            queue='generation'
        )
        
        logger.info(f"🎸 Кавер задача создана: {task_id} для {user_id}, жанр: {genre_name}, URL: {server_url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания Celery задачи: {e}")
        self.send_message(
            user_id,
            "❌ Ошибка запуска генерации. Попробуйте позже."
        )


def handle_custom_cover_genre(self, user_id, custom_genre):
    """
    Обработать ввод своего жанра для кавера
    
    Args:
        user_id: ID пользователя
        custom_genre: Описание жанра от пользователя
    """
    import asyncio
    from vk_config import ADMIN_IDS
    
    # Проверка длины
    if len(custom_genre) > 500:
        self.send_message(
            user_id,
            "❌ Описание слишком длинное (максимум 500 символов)\n\n"
            "Попробуйте короче"
        )
        return
    
    # Получаем сохраненный URL из состояния
    data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    )
    
    if not data or 'cover_audio_url' not in data:
        self.send_message(user_id, "❌ Ошибка: файл не найден")
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        return
    
    server_url = data['cover_audio_url']
    
    # Списываем токены (кроме админов)
    if user_id not in ADMIN_IDS:
        execute_query_sync(
            "UPDATE users SET balance = balance - 2 WHERE user_id = %s",
            (user_id,)
        )
    
    # Сбрасываем состояние
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.finish(user_id)
    )
    
    self.send_message(
        user_id,
        f"🎸 Создаю кавер в стиле **{custom_genre}**...\n\n"
        f"⏰ Подождите 3-5 минут"
    )
    
    # Создаем Celery задачу
    try:
        from celery_tasks import generate_cover_from_upload_task
        
        task_id = str(uuid.uuid4())
        celery_task = generate_cover_from_upload_task.apply_async(
            args=[user_id, server_url, custom_genre],
            kwargs={'task_id': task_id},
            queue='generation'
        )
        
        logger.info(f"🎸 Кавер задача создана: {task_id} для {user_id}, жанр: {custom_genre}, URL: {server_url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания Celery задачи: {e}")
        self.send_message(
            user_id,
            "❌ Ошибка запуска генерации. Попробуйте позже."
        )


# ════════════════════════════════════════════════════════════════
# ИНТЕГРАЦИЯ В ГЛАВНЫЙ ОБРАБОТЧИК
# ════════════════════════════════════════════════════════════════

"""
ДОБАВИТЬ В handle_message() main_vk.py:

    # Обработка состояния загрузки аудио
    current_state = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_state(user_id)
    )
    
    if current_state == States.WAITING_AUDIO_UPLOAD:
        # Проверяем отмену
        if text and text.lower() in ['отмена', 'cancel']:
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.finish(user_id)
            )
            self.send_message(user_id, "❌ Загрузка отменена")
            return
        
        # Проверяем наличие аудио-вложения
        if 'attachments' in msg and msg['attachments']:
            for attachment in msg['attachments']:
                if attachment['type'] in ['audio', 'doc']:
                    doc_info = attachment.get('audio') or attachment.get('doc')
                    
                    # Получаем тип загрузки из состояния
                    data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    )
                    
                    if data and data.get('upload_type') == 'karaoke':
                        self.handle_karaoke_audio_upload(user_id, doc_info)
                    elif data and data.get('upload_type') == 'cover':
                        self.handle_cover_audio_upload(user_id, doc_info)
                    return
        
        self.send_message(
            user_id,
            "❌ Не обнаружен аудиофайл\n\n"
            "Отправьте аудиофайл или напишите 'отмена'"
        )
        return
    
    # Обработка ввода своего жанра для кавера
    if current_state == States.WAITING_CUSTOM_COVER_GENRE:
        if text and text.lower() in ['отмена', 'cancel']:
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.finish(user_id)
            )
            self.send_message(user_id, "❌ Отменено")
            return
        
        self.handle_custom_cover_genre(user_id, text)
        return
    
    # Обработка выбора жанра кавера через callback
    if payload:
        cmd = payload.get('cmd')
        
        if cmd and cmd.startswith('cover_upload_genre_'):
            genre_code = cmd.replace('cover_upload_genre_', '')
            self.handle_cover_genre_selection(user_id, genre_code)
            return
"""
