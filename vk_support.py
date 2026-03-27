"""
Модуль системы поддержки для VK бота
"""
import logging
from typing import Optional
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from db_utils import execute_query_sync
from datetime import datetime

logger = logging.getLogger(__name__)

def get_support_keyboard():
    """Клавиатура для меню поддержки"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('✍️ Написать в поддержку', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_cancel_keyboard():
    """Клавиатура для отмены сообщения"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('❌ Отменить', color=VkKeyboardColor.NEGATIVE)
    return keyboard

class VKSupportSystem:
    def __init__(self, bot):
        """
        Инициализация системы поддержки
        
        Args:
            bot: Экземпляр VK бота
        """
        self.bot = bot
        self.admin_ids = [self.bot.admin_id]  # ID администраторов

    async def show_support_menu(self, user_id: int):
        """
        Показать меню поддержки
        
        Args:
            user_id: VK ID пользователя
        """
        message = (
            "🛟 Поддержка ALBImusic\n\n"
            "Если у вас возникли вопросы или проблемы, "
            "напишите нам, и мы поможем!\n\n"
            "✍️ Нажмите кнопку ниже, чтобы отправить сообщение"
        )
        await self.bot.send_message(user_id, message, get_support_keyboard())

    async def start_support_message(self, user_id: int):
        """
        Начать процесс отправки сообщения в поддержку
        
        Args:
            user_id: VK ID пользователя
        """
        message = (
            "✍️ Опишите ваш вопрос или проблему.\n"
            "❌ Для отмены нажмите кнопку ниже"
        )
        await self.bot.state_manager.set_state(user_id, self.bot.states.WAITING_SUPPORT_MESSAGE)
        await self.bot.send_message(user_id, message, get_cancel_keyboard())

    async def handle_support_message(self, user_id: int, message: str):
        """
        Обработать сообщение в поддержку
        
        Args:
            user_id: VK ID пользователя
            message: Текст сообщения
        """
        try:
            # Получаем информацию о пользователе
            user_info = self.bot.vk.users.get(user_ids=user_id)[0]
            
            # Сохраняем сообщение в БД
            execute_query_sync(
                """
                INSERT INTO support_messages 
                (user_id, vk_id, username, first_name, message, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    user_id,
                    user_info.get('screen_name', ''),
                    user_info.get('first_name', ''),
                    message,
                    datetime.now()
                )
            )
            
            # Уведомляем пользователя
            await self.bot.send_message(
                user_id,
                "✅ Ваше сообщение отправлено! Мы ответим в ближайшее время.",
                self.bot.keyboards.get_main_keyboard()
            )
            
            # Уведомляем администраторов
            admin_message = (
                f"📨 Новое сообщение в поддержку\n\n"
                f"От: {user_info.get('first_name')} (vk.com/id{user_id})\n"
                f"Сообщение: {message}"
            )
            
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(admin_id, admin_message)
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки уведомления админу {admin_id}: {e}")
            
            # Сбрасываем состояние
            await self.bot.state_manager.finish(user_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения поддержки: {e}")
            await self.bot.send_message(
                user_id,
                "❌ Произошла ошибка. Попробуйте позже.",
                self.bot.keyboards.get_main_keyboard()
            )
            await self.bot.state_manager.finish(user_id)

    async def reply_to_support(self, admin_id: int, user_id: int, reply_text: str):
        """
        Ответить на сообщение поддержки
        
        Args:
            admin_id: VK ID администратора
            user_id: VK ID пользователя
            reply_text: Текст ответа
        """
        if admin_id not in self.admin_ids:
            logger.warning(f"⚠️ Попытка ответа от неадмина: {admin_id}")
            return
            
        try:
            # Отправляем ответ пользователю
            await self.bot.send_message(
                user_id,
                f"📨 Ответ поддержки:\n\n{reply_text}"
            )
            
            # Обновляем статус в БД
            execute_query_sync(
                """
                UPDATE support_messages 
                SET replied = true, reply_text = %s 
                WHERE vk_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
                """,
                (reply_text, user_id)
            )
            
            # Уведомляем админа
            await self.bot.send_message(
                admin_id,
                f"✅ Ответ отправлен пользователю vk.com/id{user_id}"
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки ответа поддержки: {e}")
            await self.bot.send_message(
                admin_id,
                f"❌ Ошибка отправки ответа пользователю vk.com/id{user_id}"
            )

async def register_support_handlers(bot):
    """
    Регистрация обработчиков системы поддержки
    
    Args:
        bot: Экземпляр VK бота
    """
    support_system = VKSupportSystem(bot)
    bot.support_system = support_system
    
    # Добавляем обработчики команд в основной хендлер сообщений
    original_handle_message = bot.handle_message
    
    async def handle_message_with_support(event):
        """Расширенный обработчик с поддержкой"""
        user_id = event.obj.message['from_id']
        text = event.obj.message['text'].lower()
        
        current_state = await bot.state_manager.get_state(user_id)
        
        if text == "поддержка" or text == "❓ помощь":
            await support_system.show_support_menu(user_id)
            
        elif text == "✍️ написать в поддержку":
            await support_system.start_support_message(user_id)
            
        elif current_state == bot.states.WAITING_SUPPORT_MESSAGE:
            if text == "❌ отменить":
                await bot.state_manager.finish(user_id)
                await bot.send_message(
                    user_id,
                    "Отправка сообщения отменена",
                    bot.keyboards.get_main_keyboard()
                )
            else:
                await support_system.handle_support_message(user_id, event.obj.message['text'])
                
        else:
            # Передаем управление оригинальному обработчику
            await original_handle_message(event)
    
    # Заменяем оригинальный обработчик
    bot.handle_message = handle_message_with_support