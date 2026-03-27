"""
БЛОК 5: ИНТЕГРАЦИЯ АДМИН-ПАНЕЛИ В VK-БОТ

Добавляет:
1. UI админ-панели (кнопки в главном меню)
2. Обновление статистики
3. Рассылку (BroadcastStates)
4. Модерацию поддержки
5. Диагностику Suno API

ПРИМЕНЕНИЕ:
1. Добавить в импорты main_vk.py:
   from vk_admin import *
   from vk_states_broadcast import AdminStates

2. Добавить в get_main_keyboard() условие для админа:
   if is_admin:
       keyboard.add_line()
       keyboard.add_callback_button("👨‍💻 Админ-панель", color=VkKeyboardColor.NEGATIVE, payload={"cmd": "admin_panel"})

3. Добавить все handler'ы из этого файла в main_vk.py
"""

import logging
import time
from vk_api import VkUpload
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_admin import (
    get_admin_stats, 
    get_support_messages, 
    send_support_reply,
    close_support_message,
    get_all_user_ids,
    check_suno_api,
    format_broadcast_confirmation,
    format_broadcast_result
)
from vk_states_broadcast import AdminStates
from vk_keyboards import get_admin_keyboard, get_broadcast_confirm_keyboard, get_support_moderation_keyboard
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# АДМИН-ПАНЕЛЬ — ГЛАВНОЕ МЕНЮ
# ════════════════════════════════════════════════════════════════

def handle_admin_panel(self, user_id):
    """
    Показать главное меню админ-панели
    
    Вызывается при нажатии кнопки "👨‍💻 Админ-панель"
    """
    from vk_config import ADMIN_IDS
    
    if user_id not in ADMIN_IDS:
        self.send_message(user_id, "❌ У вас нет доступа к админ-панели")
        return
    
    # Клавиатура админ-панели
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button(
        "📊 Статистика",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "admin_stats"}
    )
    keyboard.add_callback_button(
        "🔄 Обновить",
        color=VkKeyboardColor.SECONDARY,
        payload={"cmd": "refresh_stats"}
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        "📨 Рассылка",
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": "admin_broadcast"}
    )
    keyboard.add_callback_button(
        "📩 Поддержка",
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": "admin_support"}
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        "🔍 Проверить Suno API",
        color=VkKeyboardColor.SECONDARY,
        payload={"cmd": "check_suno_api"}
    )
    
    self.send_message(
        user_id,
        "👨‍💻 **АДМИН-ПАНЕЛЬ ALBI MUSIC**\n\nВыберите действие:",
        keyboard=keyboard.get_keyboard()
    )


# ════════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ════════════════════════════════════════════════════════════════

def handle_admin_stats(self, user_id, is_refresh=False):
    """
    Показать статистику бота
    
    Args:
        user_id: ID администратора
        is_refresh: True если это обновление (не первый показ)
    """
    from vk_config import ADMIN_IDS
    
    if user_id not in ADMIN_IDS:
        return
    
    stats_text = get_admin_stats()
    
    # Клавиатура с кнопками управления
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button(
        "🔄 Обновить",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "refresh_stats"}
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        "📨 Рассылка",
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": "admin_broadcast"}
    )
    keyboard.add_callback_button(
        "📩 Поддержка",
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": "admin_support"}
    )
    
    self.send_message(
        user_id,
        stats_text,
        keyboard=keyboard.get_keyboard()
    )


# ════════════════════════════════════════════════════════════════
# РАССЫЛКА
# ════════════════════════════════════════════════════════════════

def handle_admin_broadcast_start(self, user_id):
    """
    Начать процесс рассылки
    """
    from vk_config import ADMIN_IDS
    import asyncio
    
    if user_id not in ADMIN_IDS:
        return
    
    # Устанавливаем состояние ожидания текста
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.set_state(user_id, AdminStates.WAITING_BROADCAST_TEXT)
    )
    
    self.send_message(
        user_id,
        "📨 **РАССЫЛКА ALBI MUSIC**\n\n"
        "Отправьте текст сообщения для рассылки.\n\n"
        "⚠️ Напишите 'отмена' для отмены."
    )


def handle_broadcast_text(self, user_id, text):
    """
    Обработать введенный текст рассылки и показать подтверждение
    
    Args:
        user_id: ID администратора
        text: Текст рассылки
    """
    import asyncio
    
    # Проверка на отмену
    if text.lower() in ['отмена', 'cancel']:
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        self.send_message(user_id, "❌ Рассылка отменена")
        return
    
    # Сохраняем текст в состоянии
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.update_data(user_id, broadcast_text=text)
    )
    
    # Получаем количество пользователей
    total_users = len(get_all_user_ids())
    
    # Формируем сообщение с предпросмотром
    confirmation_text = format_broadcast_confirmation(text, total_users)
    
    # Клавиатура подтверждения
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button(
        "✅ Отправить всем",
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": "broadcast_confirm"}
    )
    keyboard.add_callback_button(
        "❌ Отмена",
        color=VkKeyboardColor.NEGATIVE,
        payload={"cmd": "broadcast_cancel"}
    )
    
    # Устанавливаем состояние ожидания подтверждения
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.set_state(user_id, AdminStates.WAITING_BROADCAST_CONFIRM)
    )
    
    self.send_message(
        user_id,
        confirmation_text,
        keyboard=keyboard.get_keyboard()
    )


def handle_broadcast_confirm(self, user_id):
    """
    Выполнить рассылку после подтверждения
    """
    import asyncio
    
    # Получаем текст из состояния
    data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    )
    
    if not data or 'broadcast_text' not in data:
        self.send_message(user_id, "❌ Ошибка: текст рассылки не найден")
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        return
    
    text = data['broadcast_text']
    
    # Сбрасываем состояние
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.finish(user_id)
    )
    
    # Получаем список всех пользователей
    user_ids = get_all_user_ids()
    
    self.send_message(
        user_id,
        f"🚀 **РАССЫЛКА ЗАПУЩЕНА!**\n\n"
        f"📨 Начинаю отправку {len(user_ids)} пользователям...\n"
        f"⏳ Подождите — пришлю итог когда закончу."
    )
    
    # Выполняем рассылку
    sent = 0
    errors = 0
    
    for target_user_id in user_ids:
        try:
            self.send_message(target_user_id, text)
            sent += 1
            # Задержка между сообщениями (антиспам VK)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Ошибка отправки пользователю {target_user_id}: {e}")
            errors += 1
    
    # Отправляем результат админу
    result_text = format_broadcast_result(sent, errors)
    self.send_message(user_id, result_text)


def handle_broadcast_cancel(self, user_id):
    """
    Отменить рассылку
    """
    import asyncio
    
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.finish(user_id)
    )
    
    self.send_message(user_id, "❌ Рассылка отменена")


# ════════════════════════════════════════════════════════════════
# ПОДДЕРЖКА (МОДЕРАЦИЯ)
# ════════════════════════════════════════════════════════════════

def handle_admin_support(self, user_id, offset=0):
    """
    Показать необработанные сообщения поддержки
    
    Args:
        user_id: ID администратора
        offset: Смещение для пагинации
    """
    from vk_config import ADMIN_IDS
    
    if user_id not in ADMIN_IDS:
        return
    
    messages = get_support_messages(offset=offset, limit=5)
    
    if not messages:
        self.send_message(user_id, "📭 Нет необработанных сообщений поддержки")
        return
    
    # Отправляем каждое сообщение отдельным сообщением с кнопками
    for msg in messages:
        msg_id = msg['id']
        target_user_id = msg['user_id']
        username = msg['username']
        first_name = msg['first_name']
        message_text = msg['message']
        created_at = msg['created_at']
        
        # Формируем заголовок
        user_str = f"@{username}" if username else f"id{target_user_id}"
        date_str = created_at.strftime("%d.%m %H:%M") if created_at else ""
        
        header = f"🔴 **{first_name}** ({user_str}) — {date_str}"
        display_text = f"{header}\n\n{message_text}"
        
        # Клавиатура для модерации
        keyboard = VkKeyboard(inline=True)
        keyboard.add_callback_button(
            "💬 Ответить",
            color=VkKeyboardColor.POSITIVE,
            payload={"cmd": "support_reply", "msg_id": msg_id, "target_user_id": target_user_id}
        )
        keyboard.add_callback_button(
            "🗑 Закрыть",
            color=VkKeyboardColor.SECONDARY,
            payload={"cmd": "support_close", "msg_id": msg_id}
        )
        
        self.send_message(
            user_id,
            display_text,
            keyboard=keyboard.get_keyboard()
        )


def handle_support_reply_start(self, user_id, msg_id, target_user_id):
    """
    Начать процесс ответа на сообщение поддержки
    
    Args:
        user_id: ID администратора
        msg_id: ID сообщения в БД
        target_user_id: ID пользователя VK
    """
    import asyncio
    
    # Сохраняем данные в состоянии
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.set_state(user_id, AdminStates.WAITING_SUPPORT_REPLY)
    )
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.update_data(
            user_id,
            support_msg_id=msg_id,
            support_target_user_id=target_user_id
        )
    )
    
    self.send_message(
        user_id,
        "💬 Напишите ответ пользователю.\n\n"
        "⚠️ Напишите 'отмена' для отмены."
    )


def handle_support_reply_text(self, user_id, reply_text):
    """
    Отправить ответ пользователю
    
    Args:
        user_id: ID администратора
        reply_text: Текст ответа
    """
    import asyncio
    
    # Проверка на отмену
    if reply_text.lower() in ['отмена', 'cancel']:
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        self.send_message(user_id, "❌ Ответ отменен")
        return
    
    # Получаем данные из состояния
    data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    )
    
    if not data or 'support_msg_id' not in data:
        self.send_message(user_id, "❌ Ошибка: данные не найдены")
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        return
    
    msg_id = data['support_msg_id']
    target_user_id = data['support_target_user_id']
    
    # Отправляем ответ пользователю
    try:
        self.send_message(
            target_user_id,
            f"📩 **Ответ поддержки AlBi Music:**\n\n{reply_text}"
        )
        
        # Удаляем сообщение из БД
        success, message = send_support_reply(msg_id, target_user_id, reply_text)
        
        # Сбрасываем состояние
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )
        
        self.send_message(user_id, f"✅ {message}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}")
        self.send_message(user_id, f"❌ Ошибка отправки: {e}")
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.finish(user_id)
        )


def handle_support_close(self, user_id, msg_id):
    """
    Закрыть (пометить как обработанное) сообщение поддержки
    
    Args:
        user_id: ID администратора
        msg_id: ID сообщения в БД
    """
    success = close_support_message(msg_id)
    
    if success:
        self.send_message(user_id, "✅ Сообщение закрыто")
    else:
        self.send_message(user_id, "❌ Ошибка закрытия сообщения")


# ════════════════════════════════════════════════════════════════
# ПРОВЕРКА SUNO API
# ════════════════════════════════════════════════════════════════

def handle_check_suno_api(self, user_id):
    """
    Проверить работоспособность Suno API
    """
    from vk_config import ADMIN_IDS
    
    if user_id not in ADMIN_IDS:
        return
    
    self.send_message(user_id, "🔍 Проверяю Suno API...")
    
    result = check_suno_api()
    
    self.send_message(user_id, result)


# ════════════════════════════════════════════════════════════════
# ИНТЕГРАЦИЯ В ГЛАВНЫЙ ОБРАБОТЧИК
# ════════════════════════════════════════════════════════════════

"""
ДОБАВИТЬ В handle_message() main_vk.py:

    # Обработка callback-кнопок (payload)
    if payload:
        cmd = payload.get('cmd')
        
        # АДМИН-ПАНЕЛЬ
        if cmd == 'admin_panel':
            self.handle_admin_panel(user_id)
            return
        
        elif cmd == 'admin_stats':
            self.handle_admin_stats(user_id)
            return
        
        elif cmd == 'refresh_stats':
            self.handle_admin_stats(user_id, is_refresh=True)
            return
        
        elif cmd == 'admin_broadcast':
            self.handle_admin_broadcast_start(user_id)
            return
        
        elif cmd == 'broadcast_confirm':
            self.handle_broadcast_confirm(user_id)
            return
        
        elif cmd == 'broadcast_cancel':
            self.handle_broadcast_cancel(user_id)
            return
        
        elif cmd == 'admin_support':
            self.handle_admin_support(user_id)
            return
        
        elif cmd == 'support_reply':
            msg_id = payload.get('msg_id')
            target_user_id = payload.get('target_user_id')
            self.handle_support_reply_start(user_id, msg_id, target_user_id)
            return
        
        elif cmd == 'support_close':
            msg_id = payload.get('msg_id')
            self.handle_support_close(user_id, msg_id)
            return
        
        elif cmd == 'check_suno_api':
            self.handle_check_suno_api(user_id)
            return
    
    # Обработка текстовых ответов в состояниях
    current_state = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_state(user_id)
    )
    
    # РАССЫЛКА
    if current_state == AdminStates.WAITING_BROADCAST_TEXT:
        self.handle_broadcast_text(user_id, text)
        return
    
    # ОТВЕТ НА ПОДДЕРЖКУ
    if current_state == AdminStates.WAITING_SUPPORT_REPLY:
        self.handle_support_reply_text(user_id, text)
        return
"""
