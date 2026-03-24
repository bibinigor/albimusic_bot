#!/usr/bin/env python3
"""
Handlers для раздела "Фото и Видео"
ИСПРАВЛЕНО: добавлены обработчики загрузки файлов, проверка баланса, валидация
"""

import logging
import os
import uuid
import tempfile
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)


# ==================== FSM СОСТОЯНИЯ ====================

class VideoStates(StatesGroup):
    """Состояния для генерации видео"""
    choosing_source = State()      # Выбор источника (мои треки / загрузить)
    choosing_duration = State()    # Выбор длительности (5 или 10 сек)
    waiting_audio = State()        # Ожидание загрузки аудио
    waiting_description = State()  # Ожидание описания для видео


class PhotoStates(StatesGroup):
    """Состояния для обработки фото"""
    choosing_operation = State()   # Выбор операции
    waiting_photo = State()        # Ожидание фото
    waiting_person_photo = State() # Ожидание фото персонажа (для танца)
    waiting_dance_video = State()  # Ожидание видео с танцем


# ==================== УТИЛИТЫ ====================

async def upload_file_to_server(bot, file_id, filename):
    """Загружает файл на сервер и возвращает публичный URL"""
    try:
        # Скачиваем файл от Telegram
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Создаем временный файл
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, filename)
        
        await bot.download_file(file_path, local_path)
        
        # Загружаем на сервер
        upload_dir = "/var/www/albimusic/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        server_path = os.path.join(upload_dir, unique_filename)
        
        import shutil
        shutil.copy(local_path, server_path)
        
        # Удаляем временный файл
        os.remove(local_path)
        
        # Возвращаем публичный URL
        public_url = f"http://37.252.23.214:8000/uploads/{unique_filename}"
        
        logger.info(f"✅ Файл загружен: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки файла: {e}")
        raise


def validate_audio_file(file_size, duration=None):
    """Валидация аудио файла"""
    MAX_SIZE = 20 * 1024 * 1024  # 20 MB
    MAX_DURATION = 300  # 5 минут
    
    if file_size > MAX_SIZE:
        return False, f"Файл слишком большой ({file_size // 1024 // 1024} MB). Максимум 20 MB."
    
    if duration and duration > MAX_DURATION:
        return False, f"Аудио слишком длинное ({int(duration)} сек). Максимум 5 минут."
    
    return True, "OK"


def validate_photo_file(file_size):
    """Валидация фото файла"""
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    
    if file_size > MAX_SIZE:
        return False, f"Фото слишком большое ({file_size // 1024 // 1024} MB). Максимум 10 MB."
    
    return True, "OK"


def validate_video_file(file_size, duration=None):
    """Валидация видео файла"""
    MAX_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_DURATION = 60  # 1 минута
    
    if file_size > MAX_SIZE:
        return False, f"Видео слишком большое ({file_size // 1024 // 1024} MB). Максимум 50 MB."
    
    if duration and duration > MAX_DURATION:
        return False, f"Видео слишком длинное ({int(duration)} сек). Максимум 1 минута."
    
    return True, "OK"


# ==================== КЛАВИАТУРЫ ====================

def get_photo_video_menu():
    """Главное меню 'Фото и Видео'"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎬 Видео из аудио", callback_data="video_menu"),
        InlineKeyboardButton("🎨 Видео по описанию", callback_data="video_by_description"),
        InlineKeyboardButton("🖼️ Обработка фото", callback_data="photo_menu")
    )
    markup.add(InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_main"))
    return markup


def get_video_menu():
    """Меню выбора длительности видео"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎬 Видео 5 сек (💎 2 токена)", callback_data="video_5sec"),
        InlineKeyboardButton("🎬 Видео 10 сек (💎 3 токена)", callback_data="video_10sec"),
        InlineKeyboardButton("🎨 Видео по описанию (💎 3 токена)", callback_data="video_by_description"),
        InlineKeyboardButton("💃 Танцующий персонаж (💎 2 токена)", callback_data="photo_dance")
    )
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="photo_video_menu"))
    return markup


def get_video_source_menu():
    """Меню выбора источника аудио для видео"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📂 Из моих треков", callback_data="video_source_my"),
        InlineKeyboardButton("📤 Загрузить аудио", callback_data="video_source_upload")
    )
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="video_menu"))
    return markup


def get_photo_menu():
    """Меню операций с фото"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎬 Оживи фото\n💎 1 токен", callback_data="photo_animate"),
        InlineKeyboardButton("⬆️ Апскейл 4x\n💎 1 токен", callback_data="photo_upscale")
    )
    markup.add(
        InlineKeyboardButton("🗑️ Удалить фон\n💎 1 токен", callback_data="photo_remove_bg")
    )
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="photo_video_menu"))
    return markup


# ==================== HANDLERS ====================

async def handle_photo_video_menu(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Фото и Видео' в главном меню"""
    await state.finish()
    
    text = (
        "🎬 **ФОТО И ВИДЕО**\n\n"
        "Создавайте видео и обрабатывайте фото с помощью AI!\n\n"
        "**Доступные функции:**\n"
        "🎬 **Видео из аудио** - визуализация для треков\n"
        "🎨 **Видео по описанию** - AI создаст видео из текста\n"
        "🖼️ **Обработка фото** - анимация, танцы, улучшение\n\n"
        "Выберите действие 👇"
    )
    
    await message.answer(text, reply_markup=get_photo_video_menu(), parse_mode="Markdown")


async def handle_video_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Меню видео"""
    await callback_query.answer()
    
    text = (
        "🎬 **ВИДЕО ИЗ АУДИО**\n\n"
        "Создайте видео-визуализацию для вашего трека!\n\n"
        "**Runway Gen-3 Alpha Turbo** - лучшее качество на рынке\n\n"
        "**Выберите вариант:**\n"
        "• 5 сек - 2 токена (быстрая визуализация)\n"
        "• 10 сек - 3 токена (премиум качество)\n"
        "• По описанию - 3 токена (AI создаст видео по тексту)\n"
        "• Танцующий персонаж - 2 токена (загрузите фото и видео танца)\n\n"
        "Выберите вариант 👇"
    )
    
    await callback_query.message.edit_text(text, reply_markup=get_video_menu(), parse_mode="Markdown")


async def handle_video_duration_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Выбор длительности видео"""
    await callback_query.answer()
    
    duration = 5 if callback_query.data == "video_5sec" else 10
    cost = 2 if duration == 5 else 3
    
    # ИСПРАВЛЕНО: Добавлена проверка баланса
    from main_with_payments import is_admin, get_balance_number, get_balance_keyboard
    
    user_id = callback_query.from_user.id
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await callback_query.message.answer(
                f"❌ **Недостаточно токенов!**\n\n"
                f"💰 Стоимость: {cost} токена\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown",
                reply_markup=get_balance_keyboard(user_id)
            )
            await state.finish()
            return
    
    # Сохраняем выбор в FSM
    await state.update_data(video_duration=duration, video_cost=cost)
    
    text = (
        f"🎬 **ВИДЕО {duration} СЕК**\n\n"
        f"💰 Стоимость: {cost} токена\n\n"
        "Выберите источник аудио:"
    )
    
    await VideoStates.choosing_source.set()
    await callback_query.message.edit_text(text, reply_markup=get_video_source_menu(), parse_mode="Markdown")


# ИСПРАВЛЕНО: Добавлен обработчик "Из моих треков"
async def handle_video_source_my_callback(callback_query: types.CallbackQuery, state: FSMContext, bot):
    """Выбор трека из своих для видео"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    # Получаем последние 10 треков пользователя
    tracks = execute_query_sync(
        """SELECT task_id, prompt, created_at, audio_url 
           FROM generations 
           WHERE user_id = %s AND status = 'completed' AND audio_url IS NOT NULL
           ORDER BY created_at DESC 
           LIMIT 10""",
        (user_id,)
    )
    
    if not tracks:
        await bot.send_message(
            user_id,
            "📂 У вас пока нет треков.\n\n"
            "Создайте песню или загрузите свой файл!",
            parse_mode="Markdown"
        )
        await state.finish()
        return
    
    await bot.send_message(user_id, "🎵 **ВЫБЕРИТЕ ТРЕК ДЛЯ ВИДЕО:**", parse_mode="Markdown")
    
    for idx, (task_id, prompt, created_at, audio_url) in enumerate(tracks, 1):
        date_str = created_at.strftime("%d %b") if hasattr(created_at, 'strftime') else str(created_at)[:10]
        short_prompt = (prompt[:40] + '...') if len(prompt) > 40 else prompt
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            "🎬 Создать видео",
            callback_data=f"video_from_track_{task_id}"
        ))
        
        await bot.send_message(
            user_id,
            f"🎼 #{idx} • {date_str}\n{short_prompt}",
            reply_markup=markup
        )


# ИСПРАВЛЕНО: Добавлен обработчик выбора трека для видео
async def handle_video_from_track_callback(callback_query: types.CallbackQuery, state: FSMContext, bot):
    """Создание видео из выбранного трека"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace("video_from_track_", "")
    
    # Получаем URL трека
    result = execute_query_sync(
        "SELECT audio_url FROM generations WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )
    
    if not result or not result[0][0]:
        await bot.send_message(user_id, "❌ Трек не найден")
        await state.finish()
        return
    
    audio_url_raw = result[0][0]
    
    # Парсим JSON если массив
    import json
    if audio_url_raw.startswith('['):
        try:
            urls = json.loads(audio_url_raw)
            audio_url = urls[0] if urls else audio_url_raw
        except:
            audio_url = audio_url_raw
    else:
        audio_url = audio_url_raw
    
    # Убираем префиксы
    for prefix in ('ALREADY_SENT_', 'ALREADY_NOTIFIED_'):
        if audio_url.startswith(prefix):
            audio_url = audio_url.replace(prefix, '', 1)
            break
    
    # Получаем параметры из FSM
    data = await state.get_data()
    duration = data.get('video_duration', 5)
    cost = data.get('video_cost', 2)
    
    # Проверка баланса и списание
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_main_menu_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await bot.send_message(
                user_id,
                f"❌ Недостаточно токенов! Нужно: {cost}, у вас: {balance}",
                parse_mode="Markdown"
            )
            await state.finish()
            return
        
        update_user_balance(user_id, -cost)
    
    # Создаем задачу Celery
    new_task_id = str(uuid.uuid4())
    
    from tasks.replicate_tasks import generate_video_task
    
    celery_task = generate_video_task.apply_async(
        args=[user_id, audio_url, duration],
        kwargs={'task_id': new_task_id},
        task_id=new_task_id,
        queue='generation'
    )
    
    await bot.send_message(
        user_id,
        f"🎬 **Создаю видео {duration} сек!**\n\n"
        f"⏰ Генерация займет 2-3 минуты.\n\n"
        f"Результат пришлю сюда в чат!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    
    await state.finish()
    logger.info(f"🎬 Видео задача создана: {new_task_id} для user {user_id}")


# ИСПРАВЛЕНО: Добавлен обработчик "Загрузить аудио"
async def handle_video_source_upload_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Загрузка своего аудио для видео"""
    await callback_query.answer()
    
    text = (
        "📤 **ЗАГРУЗИТЕ АУДИО**\n\n"
        "Отправьте аудио файл (MP3, WAV, M4A, OGG)\n\n"
        "⚠️ Ограничения:\n"
        "• Максимум 5 минут\n"
        "• Размер до 20 МБ\n\n"
        "Я создам видео-визуализацию для вашего трека!"
    )
    
    await VideoStates.waiting_audio.set()
    
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Отмена", callback_data="video_menu"))
    
    await callback_query.message.edit_text(text, reply_markup=cancel_markup, parse_mode="Markdown")


# ИСПРАВЛЕНО: Добавлен обработчик загрузки аудио
async def handle_audio_upload(message: types.Message, state: FSMContext, bot):
    """Обработка загруженного аудио для видео"""
    user_id = message.from_user.id
    
    # Получаем параметры из FSM
    data = await state.get_data()
    duration = data.get('video_duration', 5)
    cost = data.get('video_cost', 2)
    
    # Получаем файл
    file_id = None
    file_size = 0
    
    if message.audio:
        file_id = message.audio.file_id
        file_size = message.audio.file_size
    elif message.voice:
        file_id = message.voice.file_id
        file_size = message.voice.file_size
    elif message.document:
        file_id = message.document.file_id
        file_size = message.document.file_size
    
    if not file_id:
        await message.answer("❌ Не удалось получить аудио файл. Попробуйте еще раз.")
        return
    
    # Валидация
    is_valid, error_msg = validate_audio_file(file_size)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Проверка баланса и списание
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_balance_keyboard, get_main_menu_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await message.answer(
                f"❌ **Недостаточно токенов!**\n\n"
                f"💰 Стоимость: {cost} токена\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown",
                reply_markup=get_balance_keyboard(user_id)
            )
            await state.finish()
            return
        
        update_user_balance(user_id, -cost)
    
    try:
        await message.answer("📤 Загружаю файл на сервер...")
        
        # Загружаем файл на сервер
        audio_url = await upload_file_to_server(bot, file_id, f"audio_{user_id}.mp3")
        
        # Создаем задачу Celery
        new_task_id = str(uuid.uuid4())
        
        from tasks.replicate_tasks import generate_video_task
        
        celery_task = generate_video_task.apply_async(
            args=[user_id, audio_url, duration],
            kwargs={'task_id': new_task_id},
            task_id=new_task_id,
            queue='generation'
        )
        
        # Отправляем прогресс-сообщение
        progress_msg = await message.answer(
            f"🎬 **Создаю видео {duration} сек!**\n\n"
            f"⏰ Генерация займет 2-3 минуты.\n"
            f"📊 Прогресс: ▰▰▰▱▱▱▱▱▱▱ 30%\n\n"
            f"Результат пришлю сюда в чат!",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        await state.finish()
        logger.info(f"🎬 Видео задача создана: {new_task_id} для user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки аудио: {e}")
        await message.answer("❌ Ошибка загрузки файла. Попробуйте другой файл.")
        await state.finish()


async def handle_photo_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Меню обработки фото"""
    await callback_query.answer()
    
    text = (
        "🖼️ **ОБРАБОТКА ФОТО**\n\n"
        "Выберите операцию:\n\n"
        "🎬 **Оживи фото** (1 токен) - превратите фото в короткое видео\n"
        "⬆️ **Апскейл 4x** (1 токен) - увеличение разрешения в 4 раза\n"
        "🗑️ **Удалить фон** (1 токен) - прозрачный фон\n\n"
        "Выберите действие 👇"
    )
    
    await callback_query.message.edit_text(text, reply_markup=get_photo_menu(), parse_mode="Markdown")


async def handle_photo_operation_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Выбор операции с фото"""
    await callback_query.answer()
    
    operation = callback_query.data.replace("photo_", "")
    cost = 2 if operation == "dance" else 1
    
    # ИСПРАВЛЕНО: Добавлена проверка баланса для всех операций
    from main_with_payments import is_admin, get_balance_number, get_balance_keyboard
    
    user_id = callback_query.from_user.id
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await callback_query.message.answer(
                f"❌ **Недостаточно токенов!**\n\n"
                f"💰 Стоимость: {cost} токен(а)\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown",
                reply_markup=get_balance_keyboard(user_id)
            )
            await state.finish()
            return
    
    # Сохраняем выбор
    await state.update_data(photo_operation=operation, photo_cost=cost)
    
    # Тексты для разных операций
    operation_texts = {
        "animate": ("🎬 **ОЖИВИ ФОТО**\n\n💰 Стоимость: 1 токен\n\nОтправьте фото, которое хотите оживить:", "Фото превратится в короткое видео (2-4 сек)"),
        "dance": ("💃 **ТАНЕЦ-ПЕРСОНАЖ**\n\n💰 Стоимость: 2 токена\n\nСначала отправьте фото персонажа:", "Затем загрузите видео с танцем"),
        "upscale": ("⬆️ **АПСКЕЙЛ 4X**\n\n💰 Стоимость: 1 токен\n\nОтправьте фото для улучшения:", "Разрешение увеличится в 4 раза"),
        "remove_bg": ("🗑️ **УДАЛИТЬ ФОН**\n\n💰 Стоимость: 1 токен\n\nОтправьте фото:", "Фон станет прозрачным")
    }
    
    text, description = operation_texts.get(operation, ("Отправьте фото:", ""))
    
    if operation == "dance":
        await PhotoStates.waiting_person_photo.set()
    else:
        await PhotoStates.waiting_photo.set()
    
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Отмена", callback_data="photo_menu"))
    
    await callback_query.message.edit_text(
        f"{text}\n\n💡 {description}",
        reply_markup=cancel_markup,
        parse_mode="Markdown"
    )


# ИСПРАВЛЕНО: Добавлен обработчик загрузки фото
async def handle_photo_upload(message: types.Message, state: FSMContext, bot):
    """Обработка загруженного фото"""
    user_id = message.from_user.id
    
    # Получаем параметры из FSM
    data = await state.get_data()
    operation = data.get('photo_operation')
    cost = data.get('photo_cost', 1)
    
    if not operation:
        await message.answer("❌ Ошибка: операция не выбрана")
        await state.finish()
        return
    
    # Получаем фото
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото (не файл)")
        return
    
    photo = message.photo[-1]  # Берем самое большое разрешение
    file_id = photo.file_id
    file_size = photo.file_size
    
    # Валидация
    is_valid, error_msg = validate_photo_file(file_size)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Проверка баланса и списание
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_main_menu_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await message.answer(f"❌ Недостаточно токенов! Нужно: {cost}, у вас: {balance}")
            await state.finish()
            return
        
        update_user_balance(user_id, -cost)
    
    try:
        await message.answer("📤 Загружаю фото на сервер...")
        
        # Загружаем файл на сервер
        image_url = await upload_file_to_server(bot, file_id, f"photo_{user_id}.jpg")
        
        # Создаем задачу Celery в зависимости от операции
        new_task_id = str(uuid.uuid4())
        
        from tasks.replicate_tasks import animate_photo_task, upscale_photo_task, remove_bg_task
        
        if operation == "animate":
            celery_task = animate_photo_task.apply_async(
                args=[user_id, image_url],
                kwargs={'task_id': new_task_id},
                task_id=new_task_id,
                queue='generation'
            )
            operation_name = "оживление фото"
        elif operation == "upscale":
            celery_task = upscale_photo_task.apply_async(
                args=[user_id, image_url],
                kwargs={'task_id': new_task_id},
                task_id=new_task_id,
                queue='generation'
            )
            operation_name = "апскейл 4x"
        elif operation == "remove_bg":
            celery_task = remove_bg_task.apply_async(
                args=[user_id, image_url],
                kwargs={'task_id': new_task_id},
                task_id=new_task_id,
                queue='generation'
            )
            operation_name = "удаление фона"
        else:
            await message.answer("❌ Неизвестная операция")
            await state.finish()
            return
        
        await message.answer(
            f"🖼️ **Запустил {operation_name}!**\n\n"
            f"⏰ Обработка займет 1-2 минуты.\n\n"
            f"Результат пришлю сюда в чат!",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        await state.finish()
        logger.info(f"🖼️ Фото задача создана: {new_task_id} для user {user_id}, операция: {operation}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки фото: {e}")
        await message.answer("❌ Ошибка загрузки файла. Попробуйте другой файл.")
        await state.finish()


# ИСПРАВЛЕНО: Добавлен обработчик загрузки фото персонажа для танца
async def handle_person_photo_upload(message: types.Message, state: FSMContext, bot):
    """Обработка загруженного фото персонажа для танца"""
    user_id = message.from_user.id
    
    # Получаем фото
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото (не файл)")
        return
    
    photo = message.photo[-1]
    file_id = photo.file_id
    file_size = photo.file_size
    
    # Валидация
    is_valid, error_msg = validate_photo_file(file_size)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    try:
        await message.answer("📤 Загружаю фото персонажа...")
        
        # Загружаем файл на сервер
        person_image_url = await upload_file_to_server(bot, file_id, f"person_{user_id}.jpg")
        
        # Сохраняем URL в FSM
        await state.update_data(person_image_url=person_image_url)
        
        # Переходим к загрузке видео с танцем
        await PhotoStates.waiting_dance_video.set()
        
        cancel_markup = InlineKeyboardMarkup()
        cancel_markup.add(InlineKeyboardButton("❌ Отмена", callback_data="photo_menu"))
        
        await message.answer(
            "✅ Фото персонажа получено!\n\n"
            "💃 Теперь отправьте видео с танцем:",
            reply_markup=cancel_markup
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки фото персонажа: {e}")
        await message.answer("❌ Ошибка загрузки файла. Попробуйте другой файл.")
        await state.finish()


# ИСПРАВЛЕНО: Добавлен обработчик загрузки видео для танца
async def handle_dance_video_upload(message: types.Message, state: FSMContext, bot):
    """Обработка загруженного видео с танцем"""
    user_id = message.from_user.id
    
    # Получаем видео
    if not message.video and not message.animation:
        await message.answer("❌ Пожалуйста, отправьте видео")
        return
    
    video = message.video if message.video else message.animation
    file_id = video.file_id
    file_size = video.file_size
    
    # Валидация
    is_valid, error_msg = validate_video_file(file_size)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Получаем параметры из FSM
    data = await state.get_data()
    person_image_url = data.get('person_image_url')
    cost = data.get('photo_cost', 2)
    
    if not person_image_url:
        await message.answer("❌ Ошибка: фото персонажа не найдено")
        await state.finish()
        return
    
    # Проверка баланса и списание
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_main_menu_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await message.answer(f"❌ Недостаточно токенов! Нужно: {cost}, у вас: {balance}")
            await state.finish()
            return
        
        update_user_balance(user_id, -cost)
    
    try:
        await message.answer("📤 Загружаю видео на сервер...")
        
        # Загружаем файл на сервер
        dance_video_url = await upload_file_to_server(bot, file_id, f"dance_{user_id}.mp4")
        
        # Создаем задачу Celery
        new_task_id = str(uuid.uuid4())
        
        from tasks.replicate_tasks import dance_person_task
        
        celery_task = dance_person_task.apply_async(
            args=[user_id, person_image_url, dance_video_url],
            kwargs={'task_id': new_task_id},
            task_id=new_task_id,
            queue='generation'
        )
        
        await message.answer(
            f"💃 **Создаю танец!**\n\n"
            f"⏰ Генерация займет 3-5 минут.\n\n"
            f"Результат пришлю сюда в чат!",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        await state.finish()
        logger.info(f"💃 Танец задача создана: {new_task_id} для user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки видео: {e}")
        await message.answer("❌ Ошибка загрузки файла. Попробуйте другой файл.")
        await state.finish()


async def handle_video_by_description_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Видео по описанию'"""
    await callback_query.answer()
    
    # Проверка баланса
    from main_with_payments import is_admin, get_balance_number, get_balance_keyboard
    
    user_id = callback_query.from_user.id
    cost = 3  # Стоимость видео по описанию
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await callback_query.message.answer(
                f"❌ **Недостаточно токенов!**\n\n"
                f"💰 Стоимость: {cost} токена\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown",
                reply_markup=get_balance_keyboard(user_id)
            )
            await state.finish()
            return
    
    # Сохраняем стоимость в FSM
    await state.update_data(video_cost=cost)
    
    text = (
        "🎨 **ВИДЕО ПО ОПИСАНИЮ**\n\n"
        "Опишите подробно, что должно происходить в видео.\n\n"
        "**Примеры:**\n"
        "• _Космический корабль летит сквозь туманность_\n"
        "• _Цветок распускается на рассвете в саду_\n"
        "• _Футуристический город с летающими машинами_\n\n"
        "💡 Чем детальнее описание, тем лучше результат!\n\n"
        "📝 Отправьте описание:"
    )
    
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Отмена", callback_data="video_menu"))
    
    await VideoStates.waiting_description.set()
    await callback_query.message.edit_text(text, reply_markup=cancel_markup, parse_mode="Markdown")


async def handle_video_description(message: types.Message, state: FSMContext, bot):
    """Обработка описания для видео"""
    user_id = message.from_user.id
    description = message.text.strip()
    
    if len(description) < 10:
        await message.answer("❌ Описание слишком короткое. Опишите подробнее, что должно происходить в видео.")
        return
    
    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return
    
    # Получаем стоимость из FSM
    data = await state.get_data()
    cost = data.get('video_cost', 3)
    
    # Проверка баланса и списание
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_main_menu_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < cost:
            await message.answer(
                f"❌ **Недостаточно токенов!**\n\n"
                f"💰 Стоимость: {cost} токена\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown"
            )
            await state.finish()
            return
        
        update_user_balance(user_id, -cost)
    
    # Создаем задачу Celery
    new_task_id = str(uuid.uuid4())
    
    from tasks.replicate_tasks import generate_video_by_description_task
    
    celery_task = generate_video_by_description_task.apply_async(
        args=[user_id, description],
        kwargs={'task_id': new_task_id},
        task_id=new_task_id,
        queue='generation'
    )
    
    await message.answer(
        f"🎨 **Создаю видео по описанию!**\n\n"
        f"📝 _{description[:100]}{'...' if len(description) > 100 else ''}_\n\n"
        f"⏰ Генерация займет 3-5 минут.\n\n"
        f"Результат пришлю сюда в чат!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    
    await state.finish()
    logger.info(f"🎨 Видео по описанию задача создана: {new_task_id} для user {user_id}")


async def handle_back_to_main_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await callback_query.answer()
    await state.finish()
    
    from main_with_payments import get_main_menu_keyboard
    
    await callback_query.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard(callback_query.from_user.id)
    )


async def handle_photo_video_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Callback для возврата в меню Фото и Видео"""
    await callback_query.answer()
    await state.finish()
    
    text = (
        "🎬 **ФОТО И ВИДЕО**\n\n"
        "Создавайте видео и обрабатывайте фото с помощью AI!\n\n"
        "**Доступные функции:**\n"
        "🎬 **Видео из аудио** - визуализация для треков\n"
        "🖼️ **Обработка фото** - анимация, танцы, улучшение\n\n"
        "Выберите действие 👇"
    )
    
    await callback_query.message.edit_text(text, reply_markup=get_photo_video_menu(), parse_mode="Markdown")


# ==================== РЕГИСТРАЦИЯ HANDLERS ====================

def register_photo_video_handlers(dp, bot):
    """
    Регистрация всех handlers для раздела 'Фото и Видео'
    
    Args:
        dp: Dispatcher
        bot: Bot instance
    """
    from aiogram.dispatcher.filters import Text
    
    # Главное меню "Фото и Видео"
    dp.register_message_handler(
        handle_photo_video_menu,
        Text(equals="🎬 Фото и Видео"),
        state='*'
    )
    
    # Callback handlers
    dp.register_callback_query_handler(
        handle_photo_video_menu_callback,
        lambda c: c.data == "photo_video_menu",
        state='*'
    )
    
    dp.register_callback_query_handler(
        handle_video_menu_callback,
        lambda c: c.data == "video_menu",
        state='*'
    )
    
    dp.register_callback_query_handler(
        handle_video_duration_callback,
        lambda c: c.data in ["video_5sec", "video_10sec"],
        state='*'
    )
    
    # ИСПРАВЛЕНО: Добавлены обработчики источников видео
    dp.register_callback_query_handler(
        lambda c, s, b=bot: handle_video_source_my_callback(c, s, b),
        lambda c: c.data == "video_source_my",
        state=VideoStates.choosing_source
    )
    
    dp.register_callback_query_handler(
        handle_video_source_upload_callback,
        lambda c: c.data == "video_source_upload",
        state=VideoStates.choosing_source
    )
    
    # ИСПРАВЛЕНО: Добавлен обработчик выбора трека для видео
    dp.register_callback_query_handler(
        lambda c, s, b=bot: handle_video_from_track_callback(c, s, b),
        lambda c: c.data.startswith("video_from_track_"),
        state='*'
    )
    
    # ИСПРАВЛЕНО: Добавлен обработчик загрузки аудио
    dp.register_message_handler(
        lambda m, s, b=bot: handle_audio_upload(m, s, b),
        state=VideoStates.waiting_audio,
        content_types=['audio', 'voice', 'document']
    )
    
    dp.register_callback_query_handler(
        handle_photo_menu_callback,
        lambda c: c.data == "photo_menu",
        state='*'
    )
    
    dp.register_callback_query_handler(
        handle_photo_operation_callback,
        lambda c: c.data.startswith("photo_") and c.data != "photo_menu" and c.data != "photo_video_menu",
        state='*'
    )
    
    # ИСПРАВЛЕНО: Добавлен обработчик загрузки фото
    dp.register_message_handler(
        lambda m, s, b=bot: handle_photo_upload(m, s, b),
        state=PhotoStates.waiting_photo,
        content_types=['photo']
    )
    
    # ИСПРАВЛЕНО: Добавлен обработчик загрузки фото персонажа
    dp.register_message_handler(
        lambda m, s, b=bot: handle_person_photo_upload(m, s, b),
        state=PhotoStates.waiting_person_photo,
        content_types=['photo']
    )
    
    # ИСПРАВЛЕНО: Добавлен обработчик загрузки видео для танца
    dp.register_message_handler(
        lambda m, s, b=bot: handle_dance_video_upload(m, s, b),
        state=PhotoStates.waiting_dance_video,
        content_types=['video', 'animation']
    )
    
    dp.register_callback_query_handler(
        handle_back_to_main_callback,
        lambda c: c.data == "back_to_main",
        state='*'
    )

    # Обработчики для видео по описанию
    dp.register_callback_query_handler(
        handle_video_by_description_callback,
        lambda c: c.data == "video_by_description",
        state='*'
    )
    
    dp.register_message_handler(
        lambda m, s, b=bot: handle_video_description(m, s, b),
        state=VideoStates.waiting_description,
        content_types=['text']
    )
    
    logger.info("✅ Photo/Video handlers зарегистрированы")
