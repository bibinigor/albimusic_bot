import os
import sys
import json
import time
import random
import asyncio
import logging
import traceback
from datetime import datetime, timedelta

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import aioredis

# Импортируем модули проекта
from vk_config import VK_TOKEN, VK_GROUP_ID, ADMIN_IDS
from vk_states import States, VKStateManager
from db_utils import execute_query_sync

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Команды для сброса состояния
RESET_COMMANDS = ["начать", "start", "меню", "menu", "отмена", "cancel", "🏠 в главное меню", "в главное меню", "главное меню"]

# Перечисление состояний пользователя (для обратной совместимости)
class UserState:
    START = 0
    WAITING_SONG_DESCRIPTION = 1
    WAITING_INSTRUMENTAL_DESCRIPTION = 2
    WAITING_GENRE = 3
    WAITING_VOCAL_GENDER = 4
    WAITING_MUSIC_STYLE = 5

# Инициализация пула подключений к базе данных
try:
    from db_utils import init_db_pool
    init_db_pool()
    logger.info("✅ Database pool initialized")
except Exception as e:
    logger.error(f"❌ Error initializing database pool: {e}")
    sys.exit(1)

# Create users table if not exists
try:
    execute_query_sync("""
    CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT FALSE,
            referrer_id BIGINT,
            is_free_used BOOLEAN DEFAULT FALSE
    )
    """)
    logging.info("✅ Users table ready")
except Exception as e:
    logger.error(f"❌ Error creating users table: {e}")

class VKBot:
    def __init__(self):
        # Инициализация базовых компонентов
        self.vk_session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkLongPoll(self.vk_session, group_id=VK_GROUP_ID)
        
        # Словарь для хранения состояний пользователей (для обратной совместимости)
        self.user_states = {}
        
        # Инициализация Redis и менеджера состояний
        self.redis = asyncio.get_event_loop().run_until_complete(
            aioredis.from_url("redis://localhost")
        )
        self.state_manager = VKStateManager(self.redis)
        
        logger.info("VK Bot initialized successfully")

    def get_cancel_keyboard(self):
        """Создать клавиатуру с кнопкой возврата в меню"""
        # Используем клавиатуру из модуля vk_keyboards
        from vk_keyboards import get_cancel_keyboard
        return get_cancel_keyboard()

    def get_home_keyboard(self):
        """Создать клавиатуру с кнопкой возврата в главное меню"""
        # Используем клавиатуру из модуля vk_keyboards
        from vk_keyboards import get_home_keyboard
        return get_home_keyboard()
        
    def get_music_style_keyboard(self):
        """Создать клавиатуру выбора стиля музыки"""
        # Используем клавиатуру из модуля vk_keyboards
        from vk_keyboards import get_music_style_keyboard
        return get_music_style_keyboard()

    def reset_state(self, user_id):
        """Сбросить состояние пользователя"""
        # Сброс состояния в старом хранилище (для обратной совместимости)
        if user_id in self.user_states:
            del self.user_states[user_id]
            
        # Сброс состояния в новом менеджере состояний
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.set_state(user_id, States.START)
        )
        
        # Реинициализация компонентов VK API
        self.vk_session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkLongPoll(self.vk_session, group_id=VK_GROUP_ID)
        logger.info("VK Bot initialized successfully")

    def send_message(self, user_id, message, keyboard=None):
        """Send message to user with optional keyboard"""
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': get_random_id()
            }
            
            if keyboard:
                params['keyboard'] = keyboard
                
            self.vk.messages.send(**params)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False

    def get_main_keyboard(self, user_id):
        """Create main menu keyboard"""
        try:
            logger.info("⌨️ Создание главной клавиатуры")
            
            # Используем клавиатуру из модуля vk_keyboards
            from vk_keyboards import get_main_keyboard
            
            keyboard = get_main_keyboard(user_id in ADMIN_IDS)
            logger.info("✅ Клавиатура успешно создана")
            return keyboard
        except Exception as e:
            logger.error(f"❌ Ошибка создания клавиатуры: {e}")
            return None

    def register_user(self, user_id, username, first_name):
        """Register new user in database"""
        try:
            execute_query_sync(
                "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
                (user_id, username, first_name)
            )
            logger.info(f"✅ Пользователь {user_id} успешно зарегистрирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации пользователя {user_id}: {e}")
            return False

    def get_admin_stats(self):
        """Получить статистику для админ-панели"""
        try:
            # Всего пользователей
            users_count = execute_query_sync(
                "SELECT COUNT(*) FROM users"
            )[0][0]
            
            # Новые пользователи за 24 часа
            users_24h = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours'"
            )[0][0]
            
            # Новые пользователи за 7 дней
            users_7d = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '7 days'"
            )[0][0]
            
            # Количество генераций
            generations_count = execute_query_sync(
                "SELECT COUNT(*) FROM generations"
            )[0][0] if execute_query_sync("SELECT to_regclass('public.generations')") and execute_query_sync("SELECT to_regclass('public.generations')")[0][0] else 0
            
            # Генерации за 24 часа
            generations_24h = execute_query_sync(
                "SELECT COUNT(*) FROM generations WHERE created_at > NOW() - INTERVAL '24 hours'"
            )[0][0] if execute_query_sync("SELECT to_regclass('public.generations')") and execute_query_sync("SELECT to_regclass('public.generations')")[0][0] else 0
            
            # Генерации за 7 дней
            generations_7d = execute_query_sync(
                "SELECT COUNT(*) FROM generations WHERE created_at > NOW() - INTERVAL '7 days'"
            )[0][0] if execute_query_sync("SELECT to_regclass('public.generations')") and execute_query_sync("SELECT to_regclass('public.generations')")[0][0] else 0
            
            # Статистика платежей
            try:
                # За 24 часа
                payments_24h = execute_query_sync(
                    """
                    SELECT COUNT(*), SUM(amount)
                    FROM payments
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    """
                )
                payments_count_24h = payments_24h[0][0] if payments_24h and payments_24h[0][0] else 0
                payments_sum_24h = int(payments_24h[0][1]) if payments_24h and payments_24h[0][1] else 0
                
                # За 7 дней
                payments_7d = execute_query_sync(
                    """
                    SELECT COUNT(*), SUM(amount)
                    FROM payments
                    WHERE created_at > NOW() - INTERVAL '7 days'
                    """
                )
                payments_count_7d = payments_7d[0][0] if payments_7d and payments_7d[0][0] else 0
                payments_sum_7d = int(payments_7d[0][1]) if payments_7d and payments_7d[0][1] else 0
                
                # Всего
                payments_all = execute_query_sync(
                    """
                    SELECT COUNT(*), SUM(amount)
                    FROM payments
                    """
                )
                payments_count_all = payments_all[0][0] if payments_all and payments_all[0][0] else 0
                payments_sum_all = int(payments_all[1]) if payments_all else 0
            except Exception:
                # Если таблица payments не существует
                payments_count_24h = 0
                payments_sum_24h = 0
                payments_count_7d = 0
                payments_sum_7d = 0
                payments_count_all = 0
                payments_sum_all = 0
            
            return f"""📊 **Статистика бота**

👥 Пользователи:
📆 За 24 часа: {users_24h} новых
📆 За 7 дней: {users_7d} новых
📊 Всего: {users_count} пользователей

🎵 Генерации:
📆 За 24 часа: {generations_24h} генераций
📆 За 7 дней: {generations_7d} генераций
📊 Всего: {generations_count} генераций

💰 Платежи:
📆 За 24 часа: {payments_count_24h} платежей · {payments_sum_24h}₽
📆 За 7 дней: {payments_count_7d} платежей · {payments_sum_7d}₽
📊 Всего: {payments_count_all} платежей · {payments_sum_all}₽"""
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return "❌ Ошибка получения статистики"