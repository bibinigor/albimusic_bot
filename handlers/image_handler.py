#!/usr/bin/env python3
"""
Handlers для раздела "Изображения"
"""

import logging
import uuid
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


# ==================== FSM СОСТОЯНИЯ ====================

class ImageStates(StatesGroup):
    """Состояния для генерации изображений"""
    waiting_prompt = State()       # Ожидание промпта
    choosing_aspect = State()      # Выбор соотношения сторон


# ==================== КЛАВИАТУРЫ ====================

def get_image_menu():
    """Главное меню 'Изображения'"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎨 Создать изображение (💎 1 токен)", callback_data="image_create")
    )
    markup.add(InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_main"))
    return markup


def get_aspect_ratio_menu():
    """Меню выбора соотношения сторон"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⬜ 1:1 Квадрат", callback_data="aspect_1:1"),
        InlineKeyboardButton("📱 9:16 Вертикаль", callback_data="aspect_9:16")
    )
    markup.add(
        InlineKeyboardButton("🖥️ 16:9 Горизонталь", callback_data="aspect_16:9"),
        InlineKeyboardButton("📄 3:4 Портрет", callback_data="aspect_3:4")
    )
    markup.add(
        InlineKeyboardButton("🖼️ 4:3 Альбом", callback_data="aspect_4:3")
    )
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="image_menu_back"))
    return markup


# ==================== HANDLERS ====================

async def handle_image_menu(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Изображения' в главном меню"""
    await state.finish()
    
    text = (
        "🎨 **ИЗОБРАЖЕНИЯ**\n\n"
        "Создавайте любые изображения с помощью AI!\n\n"
        "**FLUX.1 [dev]** - лучшая модель 2024-2026:\n"
        "✅ Фотореалистичность\n"
        "✅ Отличное понимание промптов\n"
        "✅ Высокая детализация\n\n"
        "**Стоимость:** 1 токен за изображение\n\n"
        "**Доступные форматы:**\n"
        "• Квадрат 1:1 (для постов)\n"
        "• Вертикаль 9:16 (для stories)\n"
        "• Горизонталь 16:9 (для обложек)\n"
        "• Портрет 3:4 и Альбом 4:3\n\n"
        "Нажмите кнопку ниже чтобы начать 👇"
    )
    
    await message.answer(text, reply_markup=get_image_menu(), parse_mode="Markdown")


async def handle_image_create_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало создания изображения"""
    await callback_query.answer()
    
    text = (
        "🎨 **СОЗДАНИЕ ИЗОБРАЖЕНИЯ**\n\n"
        "Опишите что вы хотите увидеть на изображении.\n\n"
        "**Примеры промптов:**\n"
        "• _Обложка альбома в стиле киберпанк, неоновые цвета_\n"
        "• _Портрет девушки с голубыми глазами, реалистично_\n"
        "• _Футуристический город на закате, детализация_\n"
        "• _Абстрактная композиция, яркие цвета, минимализм_\n\n"
        "💡 **Совет:** Чем подробнее описание, тем лучше результат!\n\n"
        "📝 Отправьте описание изображения:"
    )
    
    await ImageStates.waiting_prompt.set()
    
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Отмена", callback_data="image_menu_back"))
    
    await callback_query.message.edit_text(text, reply_markup=cancel_markup, parse_mode="Markdown")


async def handle_image_prompt(message: types.Message, state: FSMContext):
    """Получен промпт для изображения"""
    prompt = message.text.strip()
    
    if len(prompt) < 3:
        await message.answer("❌ Описание слишком короткое. Опишите подробнее что вы хотите увидеть.")
        return
    
    if len(prompt) > 1000:
        await message.answer("❌ Описание слишком длинное. Максимум 1000 символов.")
        return
    
    # Сохраняем промпт
    await state.update_data(image_prompt=prompt)
    
    text = (
        "📐 **ВЫБЕРИТЕ ФОРМАТ ИЗОБРАЖЕНИЯ**\n\n"
        "⬜ **1:1 Квадрат** - для постов в соцсетях\n"
        "📱 **9:16 Вертикаль** - для stories, Reels\n"
        "🖥️ **16:9 Горизонталь** - для обложек, баннеров\n"
        "📄 **3:4 Портрет** - классический портрет\n"
        "🖼️ **4:3 Альбом** - классический альбом\n\n"
        "Выберите формат 👇"
    )
    
    await ImageStates.choosing_aspect.set()
    await message.answer(text, reply_markup=get_aspect_ratio_menu(), parse_mode="Markdown")


async def handle_aspect_ratio_callback(callback_query: types.CallbackQuery, state: FSMContext, bot):
    """Выбор соотношения сторон и запуск генерации"""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    aspect_ratio = callback_query.data.replace("aspect_", "")
    
    # Получаем промпт из FSM
    data = await state.get_data()
    prompt = data.get('image_prompt', '')
    
    if not prompt:
        await callback_query.message.answer("❌ Ошибка: промпт не найден. Попробуйте снова.")
        await state.finish()
        return
    
    # ИСПРАВЛЕНО: Проверка баланса ПЕРЕД списанием
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_balance_keyboard, get_main_menu_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 1:
            await callback_query.message.answer(
                "❌ **Недостаточно токенов!**\n\n"
                "💰 Стоимость: 1 токен\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown",
                reply_markup=get_balance_keyboard(user_id)
            )
            await state.finish()
            return
        
        # Списываем 1 токен ТОЛЬКО после проверки
        update_user_balance(user_id, -1)
    
    # Создаем задачу Celery
    task_id = str(uuid.uuid4())
    
    from tasks.replicate_tasks import generate_image_task
    
    celery_task = generate_image_task.apply_async(
        args=[user_id, prompt, aspect_ratio],
        kwargs={'task_id': task_id},
        task_id=task_id,
        queue='generation'
    )
    
    # Форматируем название формата
    aspect_names = {
        "1:1": "Квадрат 1:1",
        "9:16": "Вертикаль 9:16",
        "16:9": "Горизонталь 16:9",
        "3:4": "Портрет 3:4",
        "4:3": "Альбом 4:3"
    }
    aspect_name = aspect_names.get(aspect_ratio, aspect_ratio)
    
    await callback_query.message.answer(
        f"🎨 **Создаю изображение!**\n\n"
        f"📐 Формат: {aspect_name}\n"
        f"📝 Промпт: _{prompt[:100]}..._\n\n"
        f"⏰ Для генерации требуется некоторое время... давайте подождём?\n\n"
        f"Результат пришлю сюда в чат!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    
    await state.finish()
    logger.info(f"🎨 Изображение задача создана: {task_id} для user {user_id}, aspect={aspect_ratio}")


async def handle_image_menu_back_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат в меню изображений"""
    await callback_query.answer()
    await state.finish()
    
    text = (
        "🎨 **ИЗОБРАЖЕНИЯ**\n\n"
        "Создавайте любые изображения с помощью AI!\n\n"
        "**FLUX.1 [dev]** - лучшая модель 2024-2026:\n"
        "✅ Фотореалистичность\n"
        "✅ Отличное понимание промптов\n"
        "✅ Высокая детализация\n\n"
        "**Стоимость:** 1 токен за изображение\n\n"
        "Нажмите кнопку ниже чтобы начать 👇"
    )
    
    await callback_query.message.edit_text(text, reply_markup=get_image_menu(), parse_mode="Markdown")


async def handle_image_regenerate_callback(callback_query: types.CallbackQuery, state: FSMContext, bot):
    """Перегенерация изображения с теми же параметрами"""
    await callback_query.answer()
    
    # Извлекаем task_id из callback_data
    original_task_id = callback_query.data.replace("image_regen_", "")
    user_id = callback_query.from_user.id
    
    # Получаем оригинальные параметры из БД
    from db_utils import execute_query_sync
    result = execute_query_sync(
        "SELECT prompt, aspect_ratio FROM image_generations WHERE task_id = %s",
        (original_task_id,)
    )
    
    if not result:
        await callback_query.message.answer("❌ Ошибка: оригинальное изображение не найдено.")
        return
    
    prompt, aspect_ratio = result[0]
    
    # ИСПРАВЛЕНО: Проверка баланса ПЕРЕД списанием
    from main_with_payments import is_admin, get_balance_number, update_user_balance, get_balance_keyboard
    
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 1:
            await callback_query.message.answer(
                "❌ **Недостаточно токенов!**\n\n"
                "💰 Стоимость: 1 токен\n"
                f"💳 Ваш баланс: {balance} токенов",
                parse_mode="Markdown",
                reply_markup=get_balance_keyboard(user_id)
            )
            return
        
        # Списываем 1 токен
        update_user_balance(user_id, -1)
    
    # Создаем новую задачу
    task_id = str(uuid.uuid4())
    
    from tasks.replicate_tasks import generate_image_task
    
    celery_task = generate_image_task.apply_async(
        args=[user_id, prompt, aspect_ratio],
        kwargs={'task_id': task_id},
        task_id=task_id,
        queue='generation'
    )
    
    # Форматируем название формата
    aspect_names = {
        "1:1": "Квадрат 1:1",
        "9:16": "Вертикаль 9:16",
        "16:9": "Горизонталь 16:9",
        "3:4": "Портрет 3:4",
        "4:3": "Альбом 4:3"
    }
    aspect_name = aspect_names.get(aspect_ratio, aspect_ratio)
    
    from main_with_payments import get_main_menu_keyboard
    
    await callback_query.message.answer(
        f"🔄 **Перегенерирую изображение!**\n\n"
        f"📐 Формат: {aspect_name}\n"
        f"📝 Промпт: _{prompt[:100]}{'...' if len(prompt) > 100 else ''}_\n\n"
        f"⏰ Для генерации требуется некоторое время... давайте подождём?\n\n"
        f"Результат пришлю сюда в чат!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    
    logger.info(f"🔄 Перегенерация изображения: task={task_id}, user={user_id}, prompt={prompt[:50]}")


# ==================== РЕГИСТРАЦИЯ HANDLERS ====================

def register_image_handlers(dp, bot):
    """
    Регистрация всех handlers для раздела 'Изображения'
    
    Args:
        dp: Dispatcher
        bot: Bot instance
    """
    from aiogram.dispatcher.filters import Text
    
    # Главное меню "Изображения"
    dp.register_message_handler(
        handle_image_menu,
        Text(equals="🎨 Изображения"),
        state='*'
    )
    
    # Callback handlers
    dp.register_callback_query_handler(
        handle_image_create_callback,
        lambda c: c.data == "image_create",
        state='*'
    )
    
    dp.register_callback_query_handler(
        handle_image_menu_back_callback,
        lambda c: c.data == "image_menu_back",
        state='*'
    )
    
    # Обработка промпта
    dp.register_message_handler(
        handle_image_prompt,
        state=ImageStates.waiting_prompt,
        content_types=['text']
    )
    
    # Выбор соотношения сторон
    # Создаем wrapper функцию для передачи bot instance
    async def _handle_aspect_with_bot(callback_query: types.CallbackQuery, state: FSMContext):
        await handle_aspect_ratio_callback(callback_query, state, bot)
    
    dp.register_callback_query_handler(
        _handle_aspect_with_bot,
        lambda c: c.data.startswith("aspect_"),
        state=ImageStates.choosing_aspect
    )
    
    # Перегенерация изображения
    async def _handle_regen_with_bot(callback_query: types.CallbackQuery, state: FSMContext):
        await handle_image_regenerate_callback(callback_query, state, bot)
    
    dp.register_callback_query_handler(
        _handle_regen_with_bot,
        lambda c: c.data.startswith("image_regen_"),
        state='*'
    )
    
    logger.info("✅ Image handlers зарегистрированы")
