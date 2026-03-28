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
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
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
    from db_utils import init_db_pool_sync
    init_db_pool_sync()
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
        # Инициализация базовых компонентов с обработкой ошибок
        try:
            self.vk_session = vk_api.VkApi(token=VK_TOKEN)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
            logger.info("✅ Подключение к VK API успешно установлено (BotLongPoll)")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации VK API: {e}")
            # Повторная попытка инициализации с задержкой
            time.sleep(5)
            self.vk_session = vk_api.VkApi(token=VK_TOKEN)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
            logger.info("✅ Подключение к VK API успешно установлено со второй попытки (BotLongPoll)")
        
        # Словарь для хранения состояний пользователей (для обратной совместимости)
        self.user_states = {}
        
        # Инициализация Redis и менеджера состояний с обработкой ошибок
        max_redis_retries = 3
        redis_retry_count = 0
        
        while redis_retry_count < max_redis_retries:
            try:
                self.redis = asyncio.get_event_loop().run_until_complete(
                    aioredis.from_url("redis://localhost", socket_timeout=10.0, socket_connect_timeout=10.0)
                )
                self.state_manager = VKStateManager(self.redis)
                logger.info("✅ Подключение к Redis успешно установлено")
                break
            except Exception as e:
                redis_retry_count += 1
                logger.error(f"❌ Ошибка при подключении к Redis (попытка {redis_retry_count}/{max_redis_retries}): {e}")
                if redis_retry_count >= max_redis_retries:
                    logger.critical("❌ Не удалось подключиться к Redis после нескольких попыток")
                    # Создаем заглушку для Redis, чтобы бот мог работать без сохранения состояний
                    from unittest.mock import MagicMock
                    self.redis = MagicMock()
                    self.state_manager = VKStateManager(self.redis)
                    logger.warning("⚠️ Используется заглушка для Redis. Состояния пользователей не будут сохраняться.")
                else:
                    time.sleep(3 * redis_retry_count)
        
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
        try:
            # Принудительно удаляем все данные состояния из Redis
            try:
                asyncio.get_event_loop().run_until_complete(
                    self.redis.delete(f"vk:state:{user_id}")
                )
                asyncio.get_event_loop().run_until_complete(
                    self.redis.delete(f"vk:data:{user_id}")
                )
                logger.info(f"✅ Данные состояния пользователя {user_id} удалены из Redis")
            except Exception as e:
                logger.error(f"❌ Ошибка при удалении данных из Redis: {e}")
            
            # Сначала очищаем все данные состояния
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.update_data(user_id, {})
            )
            
            # Затем устанавливаем состояние START
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.set_state(user_id, States.START)
            )
            
            logger.info(f"✅ Состояние пользователя {user_id} успешно сброшено")
        except Exception as e:
            logger.error(f"❌ Ошибка при сбросе состояния пользователя {user_id}: {e}")
        
        # Реинициализация компонентов VK API
        self.vk_session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
        logger.info("VK Bot initialized successfully")

    def send_message(self, user_id, message, keyboard=None, max_retries=3):
        """Send message to user with optional keyboard"""
        retries = 0
        while retries < max_retries:
            try:
                params = {
                    'user_id': user_id,
                    'message': message,
                    'random_id': get_random_id()
                }
                
                if keyboard:
                    # Преобразуем клавиатуру в JSON строку с помощью метода get_keyboard()
                    params['keyboard'] = keyboard.get_keyboard()
                    
                self.vk.messages.send(**params)
                return True
            except Exception as e:
                retries += 1
                error_msg = str(e)
                
                # Проверяем тип ошибки
                if "Connection reset by peer" in error_msg or "Read timed out" in error_msg:
                    # Сетевая ошибка, пробуем еще раз после паузы
                    logger.warning(f"⚠️ Сетевая ошибка при отправке сообщения (попытка {retries}/{max_retries}): {e}")
                    time.sleep(2 * retries)  # Увеличиваем время ожидания с каждой попыткой
                    continue
                elif "flood control" in error_msg.lower():
                    # Ограничение на частоту отправки сообщений
                    logger.warning(f"⚠️ Сработало ограничение на отправку сообщений (попытка {retries}/{max_retries}): {e}")
                    time.sleep(3 * retries)  # Более длительная пауза при флуд-контроле
                    continue
                else:
                    # Другая ошибка, логируем и пробуем еще раз
                    logger.error(f"❌ Ошибка отправки сообщения (попытка {retries}/{max_retries}): {e}")
                    if retries < max_retries:
                        time.sleep(1)
                        continue
                    else:
                        # Исчерпаны все попытки
                        logger.error(f"❌ Не удалось отправить сообщение после {max_retries} попыток")
                        return False
        
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
    def handle_message(self, event):
        """Обработчик входящих сообщений (VkBotLongPoll)"""
        # Поддержка VkBotLongPoll (event.obj['message']) и VkLongPoll (event.user_id) как fallback
        if hasattr(event, 'obj') and isinstance(event.obj, dict) and 'message' in event.obj:
            msg = event.obj['message']
            user_id = msg.get('from_id') or msg.get('user_id', 0)
            text = msg.get('text', '') or ''
        else:
            user_id = getattr(event, 'user_id', 0)
            text = getattr(event, 'text', '') or ''
        text_lower = text.lower()  # Приводим к нижнему регистру сразу
        
        # Логируем все входящие сообщения до любой обработки
        logger.info(f"📩 Получено новое сообщение от {user_id}: '{text}' (в нижнем регистре: '{text_lower}')")
        print(f"Получено сообщение: {text}")
        
        # Специальная обработка команды "Начать" до всего остального
        if text_lower in ["начать", "start"]:
            logger.info(f"🔄 Получена команда начала работы от {user_id}: '{text}'")
            # Принудительно сбрасываем состояние
            self.reset_state(user_id)
            
            welcome_text = """🎵 Привет! Я — бот для создания музыки с помощью ИИ.

🎼 Что я умею:
• Создавать песни с вашим текстом
• Генерировать инструментальную музыку
• Сочинять тексты для песен

💫 Первая генерация — бесплатно!
🎁 Выберите действие в меню 👇"""
            
            keyboard = self.get_main_keyboard(user_id)
            if keyboard:
                result = self.send_message(
                    user_id=user_id,
                    message=welcome_text,
                    keyboard=keyboard
                )
                logger.info(f"📨 Отправка приветственного сообщения: {'успешно' if result else 'ошибка'}")
            return
        
        # Проверяем наличие payload в сообщении (VkBotLongPoll и VkLongPoll)
        payload = None
        try:
            payload_raw = None
            if hasattr(event, 'obj') and isinstance(event.obj, dict) and 'message' in event.obj:
                # VkBotLongPoll: payload хранится в event.obj['message']['payload'] как строка
                payload_raw = event.obj['message'].get('payload', '')
            elif hasattr(event, 'payload') and event.payload:
                # VkLongPoll fallback
                payload_raw = event.payload
            if payload_raw:
                payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                print(f"Получен payload: {payload}")
                logger.info(f"📩 Получен payload от {user_id}: {payload}")
        except Exception as e:
            logger.error(f"❌ Ошибка при разборе payload: {e}")
        
        try:
            # Флаг для отслеживания обработки команды
            command_handled = False
            
            # Регистрация пользователя при первом сообщении
            try:
                user_info = self.vk.users.get(user_ids=user_id)[0]
                logger.info(f"👤 Получена информация о пользователе: {user_info}")
                
                registered = self.register_user(
                    user_id=user_id,
                    username=user_info.get('screen_name'),
                    first_name=user_info.get('first_name')
                )
                logger.info(f"📝 Регистрация пользователя: {'успешно' if registered else 'уже был в базе'}")
            except Exception as e:
                logger.error(f"❌ Ошибка при работе с пользователем: {e}")
                return

            # Проверяем базовые команды до любой другой обработки
            if text.lower() in [cmd.lower() for cmd in RESET_COMMANDS]:
                logger.info(f"🔄 Получена команда сброса состояния от {user_id}: '{text}'")
                self.reset_state(user_id)
                welcome_text = "Вы вернулись в главное меню!"
                
                if text.lower() in ["начать", "start"]:
                    welcome_text = """🎵 Привет! Я — бот для создания музыки с помощью ИИ.

🎼 Что я умею:
• Создавать песни с вашим текстом
• Генерировать инструментальную музыку
• Сочинять тексты для песен

💫 Первая генерация — бесплатно!
🎁 Выберите действие в меню 👇"""
                
                keyboard = self.get_main_keyboard(user_id)
                if keyboard:
                    result = self.send_message(
                        user_id=user_id,
                        message=welcome_text,
                        keyboard=keyboard
                    )
                    logger.info(f"📨 Отправка сообщения: {'успешно' if result else 'ошибка'}")
                command_handled = True
                return

            # Обработка команд меню
            
            # Проверяем, есть ли payload и обрабатываем его
            if payload and isinstance(payload, dict):
                # Обработка payload от кнопок
                action = payload.get('action')
                if action:
                    logger.info(f"🔘 Обработка действия из payload: {action}")
                    
                    # Обработка различных действий из payload
                    if action == "create_song":
                        text = "🎵 Создать песню"
                        text_lower = text.lower()
                    elif action == "create_music":
                        text = "🎶 Создать музыку"
                        text_lower = text.lower()
                    elif action == "balance":
                        text = "💰 Баланс"
                        text_lower = text.lower()
                    elif action == "my_tracks":
                        text = "📂 Мои треки"
                        text_lower = text.lower()
                    elif action == "examples":
                        text = "🎧 Примеры песен"
                        text_lower = text.lower()
                    elif action == "support":
                        text = "📞 Поддержка"
                        text_lower = text.lower()
                    elif action == "admin":
                        text = "⚙️ Админ"
                        text_lower = text.lower()
                    elif action == "home":
                        text = "🏠 В главное меню"
                        text_lower = text.lower()
                    elif action == "select_variant_1":
                        text = "Выбрать вариант 1"
                        text_lower = text.lower()
                    elif action == "select_variant_2":
                        text = "Выбрать вариант 2"
                        text_lower = text.lower()
                    elif action == "write_own_text":
                        text = "Написать свой текст"
                        text_lower = text.lower()
            
            # Обработка команд меню по тексту
            if "создать песню" in text_lower or text == "🎵 Создать песню":
                logger.info(f"🎵 Запрос на создание песни от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Устанавливаем состояние выбора типа текста
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.CHOOSING_TEXT_TYPE)
                        )
                        # Для обратной совместимости
                        self.user_states[user_id] = UserState.WAITING_SONG_DESCRIPTION
                        
                        # Сообщение с выбором типа текста
                        prompt_message = """✨ Отлично! Придумать за тебя текст или у тебя свой?

Чтобы вернуться в главное меню, нажмите кнопку ниже."""
                        
                        # Импортируем клавиатуру для выбора типа текста
                        from vk_keyboards import get_song_type_keyboard
                        
                        # Создаем клавиатуру для выбора типа текста (inline=True для отображения под сообщением)
                        keyboard = get_song_type_keyboard()
                        
                        # Отправляем сообщение с клавиатурой выбора типа текста
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=keyboard
                        )
                        
                        logger.info(f"✅ Пользователь {user_id} переведен в режим выбора типа текста")
                        command_handled = True
                        return  # Прерываем обработку текущего сообщения
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания песни при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания песни: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True

            elif "создать музыку" in text_lower or text == "🎶 Создать музыку":
                logger.info(f"🎶 Запрос на создание инструментальной музыки от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Устанавливаем состояние выбора жанра музыки
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_MUSIC_STYLE)
                        )
                        # Для обратной совместимости
                        self.user_states[user_id] = UserState.WAITING_INSTRUMENTAL_DESCRIPTION
                        
                        # Импортируем клавиатуру для выбора жанра музыки
                        from vk_keyboards import get_music_genres_keyboard
                        
                        # Создаем клавиатуру с жанрами
                        keyboard = get_music_genres_keyboard()
                        
                        # Сообщение с выбором жанра
                        prompt_message = """🎶 **СОЗДАЕМ ИНСТРУМЕНТАЛЬНУЮ МУЗЫКУ**

🎹 Музыка БЕЗ слов - только мелодия и ритм!

Выбери жанр для твоей композиции 👇"""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=keyboard
                        )
                        
                        logger.info(f"✅ Пользователь {user_id} переведен в режим выбора жанра инструментальной музыки")
                        command_handled = True
                        return  # Прерываем обработку текущего сообщения
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания музыки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания музыки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True

            # ──── БАЛАНС ────
            elif "баланс" in text_lower or text == "💰 Баланс":
                logger.info(f"💰 Запрос баланса от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    balance_num = result[0][0] if result else 0
                    balance_str = f"💰 {balance_num} токенов" if balance_num > 0 else "❌ 0 токенов"
                    balance_msg = (
                        f"💰 Ваш баланс: {balance_str}\n\n"
                        f"💳 Пополнить баланс:\n\n"
                        f"💫 1 токен (2 песни) — 50₽\n"
                        f"💳 10 токенов (20 песен) — 250₽\n"
                        f"🔥 25 токенов (50 песен) — 500₽\n"
                        f"⭐ 60 токенов (120 песен) — 1000₽\n"
                        f"💎 140 токенов (280 песен) — 2000₽\n\n"
                        f"🌟 Пригласи друга — получи 2 токена бесплатно!\n"
                        f"🎁 Первый токен в подарок — для новых пользователей!\n\n"
                        f"📩 Для оплаты напишите в поддержку: https://vk.com/igorbibin"
                    )
                    self.send_message(
                        user_id=user_id,
                        message=balance_msg,
                        keyboard=self.get_main_keyboard(user_id)
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка при получении баланса: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Ошибка при получении баланса. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True
                return

            # ──── МОИ ТРЕКИ ────
            elif "мои треки" in text_lower or text == "📂 Мои треки":
                logger.info(f"📂 Запрос треков от пользователя {user_id}")
                try:
                    tracks = execute_query_sync(
                        """SELECT task_id, prompt, audio_url, created_at
                           FROM generations
                           WHERE user_id = %s
                           ORDER BY id DESC LIMIT 10""",
                        (user_id,)
                    )
                    if not tracks:
                        self.send_message(
                            user_id=user_id,
                            message="🎵 У вас пока нет созданных треков. Самое время это исправить!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                    else:
                        self.send_message(
                            user_id=user_id,
                            message=f"🎵 Ваши последние треки ({len(tracks)} шт.):\n━━━━━━━━━━━━━━━━━",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        for idx, (task_id, prompt, audio_url, created_at) in enumerate(tracks, 1):
                            try:
                                date_str = created_at.strftime("%d.%m.%Y") if hasattr(created_at, 'strftime') else str(created_at)[:10]
                            except Exception:
                                date_str = "—"
                            short_prompt = (prompt[:80] + '...') if prompt and len(prompt) > 80 else (prompt or '—')
                            urls_text = ""
                            if audio_url:
                                try:
                                    import json as _json
                                    urls = _json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                                    for i, url in enumerate(urls, 1):
                                        label = f"Вариант {i}" if len(urls) > 1 else "Слушать"
                                        urls_text += f"\n🔗 {label}: {url}"
                                except Exception:
                                    urls_text = f"\n🔗 Слушать: {audio_url}"
                            track_msg = (
                                f"🎼 Трек #{idx} ({date_str})\n"
                                f"📝 {short_prompt}"
                                f"{urls_text}"
                            )
                            self.send_message(user_id=user_id, message=track_msg)
                except Exception as e:
                    logger.error(f"❌ Ошибка при получении треков: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Ошибка при получении треков. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True
                return

            # ──── ПРИМЕРЫ ПЕСЕН ────
            elif "примеры" in text_lower or text == "🎧 Примеры песен":
                logger.info(f"🎧 Запрос примеров от пользователя {user_id}")
                self.send_message(
                    user_id=user_id,
                    message=(
                        "🔐 Это портал для перехода в наш секретный канал\n\n"
                        "«ALBImusic/ Музыка/ Промпты/ Новости/ Обучение»\n\n"
                        "Там твоё вдохновение! Там твоё секретное оружие — идеи! "
                        "И там же обучение и новости!\n\n"
                        "👉 Переходи в канал: https://t.me/ALBImusic_chart"
                    ),
                    keyboard=self.get_main_keyboard(user_id)
                )
                command_handled = True
                return

            # ──── ПОДДЕРЖКА ────
            elif "поддержка" in text_lower or text == "📞 Поддержка":
                logger.info(f"📞 Запрос поддержки от пользователя {user_id}")
                self.send_message(
                    user_id=user_id,
                    message=(
                        "Служба поддержки ALBI Music 🛠\n\n"
                        "По всем вопросам пишите мне в личные сообщения:\n"
                        "👉 https://vk.com/igorbibin\n\n"
                        "⏳ Отвечу вам в течение дня."
                    ),
                    keyboard=self.get_main_keyboard(user_id)
                )
                command_handled = True
                return

            # Получаем состояние из нового менеджера состояний
            try:
                vk_state = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_state(user_id)
                )
            except Exception as e:
                logger.error(f"❌ Ошибка получения состояния пользователя {user_id}: {e}")
                # Сбрасываем состояние при ошибке
                self.reset_state(user_id)
                vk_state = States.START
            
            # Обработка выбора типа текста
            if vk_state == States.CHOOSING_TEXT_TYPE:
                if "ai-текст" in text_lower or "придумать текст" in text_lower or "🤖 ai-текст" in text_lower:
                    # Обработка выбора AI-текста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_SONG_IDEA)
                    )
                    
                    prompt_message = """✨ **СЕЙЧАС МЫ ТЕБЕ СОЧИНИМ САМЫЙ ЛУЧШИЙ ТЕКСТ!**

Про что и для кого ты хочешь песню? Напиши мне.

▪️ для кого / о ком
▪️ какие интересные моменты упомянуть
▪️ идея которую хочется передать песней

📩 Всё в ОДНОМ сообщении — и я создам текст!

💡 Совет: опиши кратко самое главное (до 200 символов) ✨"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=prompt_message,
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал генерацию AI-текста")
                    command_handled = True
                    return
                
                elif "свой текст" in text_lower or "✍️ свой текст" in text_lower:
                    # Обработка выбора своего текста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_OWN_LYRICS)
                    )
                    
                    prompt_message = """📝 **ОТЛИЧНО!**

Отправь мне текст своей песни, и мы перейдем к выбору жанра 🎵"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=prompt_message,
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал использование своего текста")
                    command_handled = True
                    return
            
            # Обработка ввода идеи для AI-текста
            elif vk_state == States.WAITING_SONG_IDEA:
                # Сохраняем идею для генерации текста
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, song_idea=text)
                )
                
                # Отправляем сообщение о начале генерации
                self.send_message(
                    user_id=user_id,
                    message="⏳ Генерирую текст песни, подождите 1-2 минуты...",
                    keyboard=self.get_cancel_keyboard()
                )
                
                print(f"Запуск генерации текста для пользователя {user_id}, идея: {text}")
                logger.info(f"📝 Запуск генерации текста для пользователя {user_id}, идея: {text}")
                
                # Генерируем два варианта текста песни на основе идеи
                try:
                    from celery_tasks import generate_suno_lyrics_sync
                    
                    # Ограничиваем длину идеи
                    idea = text[:500]
                    
                    # Генерируем первый вариант текста
                    lyrics_variant1 = generate_suno_lyrics_sync(idea)
                    
                    # Генерируем второй вариант текста с небольшим изменением запроса
                    lyrics_variant2 = generate_suno_lyrics_sync(idea + " (альтернативный вариант)")
                    
                    if lyrics_variant1 and lyrics_variant2:
                        # Сохраняем сгенерированные тексты
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(
                                user_id, 
                                lyrics_variant1=lyrics_variant1,
                                lyrics_variant2=lyrics_variant2
                            )
                        )
                        
                        # Отправляем первый вариант текста пользователю
                        self.send_message(
                            user_id=user_id,
                            message=f"✨ Вариант 1:\n\n{lyrics_variant1}"
                        )
                        
                        # Отправляем второй вариант текста пользователю
                        self.send_message(
                            user_id=user_id,
                            message=f"✨ Вариант 2:\n\n{lyrics_variant2}"
                        )
                        
                        # Импортируем клавиатуру для выбора варианта текста
                        from vk_keyboards import get_lyrics_variants_selection_keyboard
                        
                        # Отправляем клавиатуру выбора варианта текста
                        self.send_message(
                            user_id=user_id,
                            message="Выберите вариант текста или напишите свой:",
                            keyboard=get_lyrics_variants_selection_keyboard()
                        )
                        
                        # Переводим в состояние выбора варианта текста
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.CHOOSING_LYRICS_VARIANT)
                        )
                    else:
                        # Если не удалось сгенерировать текст
                        self.send_message(
                            user_id=user_id,
                            message="❌ Не удалось сгенерировать тексты. Попробуйте другую идею или свой текст.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации текста: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при генерации текста. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    self.reset_state(user_id)
                
                logger.info(f"✅ Пользователь {user_id} отправил идею для AI-текста")
                command_handled = True
                return
                            # Обработка ввода своего текста
            elif vk_state == States.WAITING_OWN_LYRICS:
                # Сохраняем текст песни
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, lyrics=text)
                )
                
                # Переводим в состояние выбора жанра
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.set_state(user_id, States.WAITING_GENRE)
                )
                
                # Импортируем клавиатуру для выбора жанра песни
                from vk_keyboards import get_song_genres_keyboard
                
                # Отправляем клавиатуру выбора жанра
                self.send_message(
                    user_id=user_id,
                    message="Выберите жанр для вашей песни:",
                    keyboard=get_song_genres_keyboard()
                )
                
                logger.info(f"✅ Пользователь {user_id} отправил свой текст")
                command_handled = True
                return
            
            # Обработка выбора варианта текста
            elif vk_state == States.CHOOSING_LYRICS_VARIANT:
                if "выбрать вариант 1" in text_lower or text == "Выбрать вариант 1" or "выбрать 1 вариант" in text_lower:
                    # Пользователь выбрал первый вариант текста
                    # Получаем данные состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    # Получаем первый вариант текста
                    lyrics = state_data.get('lyrics_variant1', '')
                    
                    if lyrics:
                        # Сохраняем выбранный текст
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(user_id, lyrics=lyrics)
                        )
                        
                        # Переводим в состояние выбора жанра
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_GENRE)
                        )
                        
                        # Импортируем клавиатуру для выбора жанра песни
                        from vk_keyboards import get_song_genres_keyboard
                        
                        # Отправляем клавиатуру выбора жанра
                        self.send_message(
                            user_id=user_id,
                            message="Выберите жанр для вашей песни:",
                            keyboard=get_song_genres_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} выбрал первый вариант текста")
                    else:
                        # Если текст не найден, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: текст песни не найден. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    command_handled = True
                    return
                
                elif "выбрать вариант 2" in text_lower or text == "Выбрать вариант 2" or "выбрать 2 вариант" in text_lower:
                    # Пользователь выбрал второй вариант текста
                    # Получаем данные состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    # Получаем второй вариант текста
                    lyrics = state_data.get('lyrics_variant2', '')
                    
                    if lyrics:
                        # Сохраняем выбранный текст
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(user_id, lyrics=lyrics)
                        )
                        
                        # Переводим в состояние выбора жанра
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_GENRE)
                        )
                        
                        # Импортируем клавиатуру для выбора жанра песни
                        from vk_keyboards import get_song_genres_keyboard
                        
                        # Отправляем клавиатуру выбора жанра
                        self.send_message(
                            user_id=user_id,
                            message="Выберите жанр для вашей песни:",
                            keyboard=get_song_genres_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} выбрал второй вариант текста")
                    else:
                        # Если текст не найден, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: текст песни не найден. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    command_handled = True
                    return
                
                elif "написать свой текст" in text_lower or "✍️ написать свой текст" in text_lower:
                    # Пользователь хочет написать свой текст
                    # Переводим в состояние ожидания своего текста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_OWN_LYRICS)
                    )
                    
                    prompt_message = """📝 **ОТЛИЧНО!**

Отправь мне текст своей песни, и мы перейдем к выбору жанра 🎵"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=prompt_message,
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал написать свой текст")
                    command_handled = True
                    return
                
                elif "сгенерировать другие" in text_lower or "🔄 сгенерировать другие" in text_lower:
                    # Пользователь хочет сгенерировать другие варианты текста
                    # Получаем идею для песни из данных состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    song_idea = state_data.get('song_idea', '')
                    
                    if song_idea:
                        # Отправляем сообщение о генерации новых текстов
                        self.send_message(
                            user_id=user_id,
                            message="⏳ Генерирую новые варианты текста...",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Генерируем новые варианты текста
                        try:
                            from celery_tasks import generate_suno_lyrics_sync
                            
                            # Ограничиваем длину идеи
                            idea = song_idea[:500]
                            
                            # Генерируем первый вариант текста с небольшим изменением запроса
                            lyrics_variant1 = generate_suno_lyrics_sync(idea + " (новый вариант)")
                            
                            # Генерируем второй вариант текста с другим изменением запроса
                            lyrics_variant2 = generate_suno_lyrics_sync(idea + " (другой стиль)")
                            
                            if lyrics_variant1 and lyrics_variant2:
                                # Сохраняем сгенерированные тексты
                                asyncio.get_event_loop().run_until_complete(
                                    self.state_manager.update_data(
                                        user_id, 
                                        lyrics_variant1=lyrics_variant1,
                                        lyrics_variant2=lyrics_variant2
                                    )
                                )
                                
                                # Отправляем первый вариант текста пользователю
                                self.send_message(
                                    user_id=user_id,
                                    message=f"✨ Новый вариант 1:\n\n{lyrics_variant1}"
                                )
                                
                                # Отправляем второй вариант текста пользователю
                                self.send_message(
                                    user_id=user_id,
                                    message=f"✨ Новый вариант 2:\n\n{lyrics_variant2}"
                                )
                                
                                # Импортируем клавиатуру для выбора варианта текста
                                from vk_keyboards import get_lyrics_variants_keyboard_with_two_options
                                
                                # Отправляем клавиатуру выбора варианта текста
                                self.send_message(
                                    user_id=user_id,
                                    message="Выберите вариант текста или напишите свой:",
                                    keyboard=get_lyrics_variants_keyboard_with_two_options()
                                )
                            else:
                                # Если не удалось сгенерировать текст
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Не удалось сгенерировать новые тексты. Попробуйте использовать текущие варианты или написать свой.",
                                    keyboard=get_lyrics_variants_keyboard_with_two_options()
                                )
                        except Exception as e:
                            logger.error(f"❌ Ошибка генерации новых текстов: {e}")
                            self.send_message(
                                user_id=user_id,
                                message="❌ Произошла ошибка при генерации новых текстов. Попробуйте использовать текущие варианты или написать свой.",
                                keyboard=get_lyrics_variants_keyboard_with_two_options()
                            )
                    else:
                        # Если идея не найдена, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: идея для песни не найдена. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    logger.info(f"✅ Пользователь {user_id} запросил новые варианты текста")
                    command_handled = True
                    return
            
            # Обработка выбора жанра
            elif vk_state == States.WAITING_GENRE:
                # Проверяем, выбрал ли пользователь "Свой вариант"
                if "свой вариант" in text_lower or text == "✏️ Свой вариант":
                    # Переводим в состояние ввода своего жанра
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_CUSTOM_GENRE)
                    )
                    
                    # Отправляем сообщение с просьбой ввести свой жанр
                    self.send_message(
                        user_id=user_id,
                        message="Опишите жанр и стиль песни своими словами:",
                        keyboard=self.get_cancel_keyboard()
                    )
                    
                    logger.info(f"✅ Пользователь {user_id} выбрал ввод своего жанра")
                    command_handled = True
                    return
                else:
                    # Сохраняем выбранный жанр
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.update_data(user_id, genre=text)
                    )
                    
                    # Переводим в состояние выбора пола вокалиста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_VOCAL_GENDER)
                    )
                    
                    # Импортируем клавиатуру для выбора пола вокалиста
                    from vk_keyboards import get_vocal_gender_keyboard
                    
                    # Отправляем клавиатуру выбора пола вокалиста
                    self.send_message(
                        user_id=user_id,
                        message="Выберите пол вокалиста:",
                        keyboard=get_vocal_gender_keyboard()
                    )
                    
                    logger.info(f"✅ Пользователь {user_id} выбрал жанр: {text}")
                    command_handled = True
                    return
                    
            # Обработка ввода своего жанра
            elif vk_state == States.WAITING_CUSTOM_GENRE:
                # Сохраняем введенный пользователем жанр
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, genre=text)
                )
                
                # Переводим в состояние выбора пола вокалиста
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.set_state(user_id, States.WAITING_VOCAL_GENDER)
                )
                
                # Импортируем клавиатуру для выбора пола вокалиста
                from vk_keyboards import get_vocal_gender_keyboard
                
                # Отправляем клавиатуру выбора пола вокалиста
                self.send_message(
                    user_id=user_id,
                    message="Выберите пол вокалиста:",
                    keyboard=get_vocal_gender_keyboard()
                )
                
                logger.info(f"✅ Пользователь {user_id} ввел свой жанр: {text}")
                command_handled = True
                return
                
            # Обработка выбора пола вокалиста
            elif vk_state == States.WAITING_VOCAL_GENDER:
                # Сохраняем выбранный пол вокалиста
                vocal_gender = "male"
                if "женский" in text_lower or text == "👩 Женский":
                    vocal_gender = "female"
                
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, vocal_gender=vocal_gender)
                )
                
                # Получаем данные пользователя
                state_data = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_data(user_id)
                ) or {}
                
                # Получаем текст песни и жанр
                lyrics = state_data.get('lyrics', '')
                genre = state_data.get('genre', '')
                
                # Отправляем GIF-анимацию и сообщение о начале генерации
                gif_path = '/root/albimusic-bot/robot_music.gif'
                try:
                    # Проверяем, существует ли файл
                    import os
                    if os.path.exists(gif_path):
                        # Отправляем GIF
                        from vk_api.upload import VkUpload
                        upload = VkUpload(self.vk_session)
                        doc = upload.document_message(gif_path, peer_id=user_id)
                        attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
                        
                        self.send_message(
                            user_id=user_id,
                            message="🎵 **Генерация началась!**\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Отправляем GIF как документ с обработкой ошибок
                        try:
                            self.vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                attachment=attachment
                            )
                        except Exception as gif_error:
                            logger.warning(f"⚠️ Не удалось отправить GIF: {gif_error}")
                    else:
                        # Если GIF не найден, просто отправляем сообщение
                        self.send_message(
                            user_id=user_id,
                            message="🎵 **Генерация началась!**\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                            keyboard=self.get_cancel_keyboard()
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке GIF: {e}")
                    # Если произошла ошибка, просто отправляем сообщение
                    self.send_message(
                        user_id=user_id,
                        message="🎵 **Генерация началась!**\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                        keyboard=self.get_cancel_keyboard()
                    )
                
                # Запускаем генерацию песни
                try:
                    # Импортируем функцию для генерации песни
                    from celery_tasks import generate_suno_song_sync
                    
                    # Формируем стиль с учетом пола вокалиста
                    style = f"{genre}, {vocal_gender} vocals"
                    
                    # Проверяем длину текста песни и автоматически включаем customMode для длинных текстов
                    use_custom_mode = len(lyrics) > 500
                    if use_custom_mode:
                        logger.info(f"ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")
                    
                    # Запускаем генерацию песни
                    logger.info(f"🎵 Запуск генерации песни для пользователя {user_id}")
                    logger.info(f"🎵 Текст: {lyrics[:100]}...")
                    logger.info(f"🎵 Стиль: {style}")
                    logger.info(f"🎵 Custom Mode: {use_custom_mode}")
                    
                    # Запускаем генерацию в отдельном потоке, чтобы не блокировать бота
                    import threading
                    def generate_song_thread():
                        try:
                            # Генерируем песню
                            result = generate_suno_song_sync(lyrics, style)
                            
                            if result:
                                audio_url, task_id, audio_id = result
                                
                                # Сохраняем результат в базу данных
                                execute_query_sync(
                                    'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_audio_id) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                                    (user_id, task_id, style, audio_url, False, use_custom_mode, audio_id)
                                )
                                
                                # Импортируем клавиатуру с опциями
                                from vk_keyboards import get_song_options_keyboard
                                
                                # Подготовка сообщения с результатом
                                message_text = f"✅ Ваша песня готова!\n\nЖанр: {genre}\n\n"
                                
                                # Проверяем, содержит ли audio_url несколько ссылок (JSON массив)
                                try:
                                    import json
                                    audio_urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                                    
                                    # Если есть несколько ссылок, добавляем их все в сообщение
                                    if len(audio_urls) > 1:
                                        message_text += "🎵 **Варианты песни:**\n\n"
                                        for i, url in enumerate(audio_urls, 1):
                                            message_text += f"Вариант {i}: {url}\n\n"
                                    else:
                                        message_text += f"Ссылка: {audio_url}\n\n"
                                except Exception as json_error:
                                    # Если не удалось распарсить JSON, логируем ошибку и используем строку как есть
                                    logger.error(f"❌ Ошибка при парсинге JSON аудио URL: {json_error}")
                                    message_text += f"Ссылка: {audio_url}\n\n"
                                
                                # Добавляем информацию о возможных действиях
                                message_text += "💎 **Что можно сделать с этой песней:**\n\n"
                                message_text += "🎤 **Минусовка** (1 токен) — версия без вокала для исполнения\n"
                                message_text += "🎸 **Кавер** (1 токен) — перепой в другом стиле/жанре\n"
                                message_text += "🎵 **В WAV** (2 токена) — конвертируй в WAV формат для профи\n"
                                message_text += "🔗 **Поделиться** — опубликуй трек на своей странице ВКонтакте"
                                
                                # Отправляем результат пользователю с клавиатурой опций
                                self.send_message(
                                    user_id=user_id,
                                    message=message_text,
                                    keyboard=get_song_options_keyboard(task_id)
                                )
                                
                                # Списываем баланс
                                execute_query_sync(
                                    "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                    (user_id,)
                                )
                                logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")
                            else:
                                # Если не удалось сгенерировать песню
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Не удалось сгенерировать песню. Попробуйте другой жанр или позже.",
                                    keyboard=self.get_main_keyboard(user_id)
                                )
                        except Exception as e:
                            logger.error(f"❌ Ошибка генерации песни: {e}")
                            self.send_message(
                                user_id=user_id,
                                message="❌ Произошла ошибка при генерации песни. Попробуйте позже.",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                    
                    # Запускаем генерацию в отдельном потоке
                    thread = threading.Thread(target=generate_song_thread)
                    thread.start()
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка запуска генерации песни: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при запуске генерации песни. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                
                # Сбрасываем состояние пользователя
                self.reset_state(user_id)
                
                logger.info(f"✅ Пользователь {user_id} выбрал пол вокалиста: {vocal_gender}")
                command_handled = True
                return

            # Обработка выбора жанра для инструментальной музыки
            elif vk_state == States.WAITING_MUSIC_STYLE:
                genre = text  # Выбранный жанр
                logger.info(f"🎶 Пользователь {user_id} выбрал жанр для инструментала: {genre}")

                # Сбрасываем состояние ДО запуска потока
                self.reset_state(user_id)

                # Отправляем сообщение о начале генерации
                self.send_message(
                    user_id=user_id,
                    message="🎵 Генерация началась. Это займет 3-5 минут. Результат пришлю сюда в чат"
                )

                # Пробуем отправить GIF
                gif_path = '/root/albimusic-bot/robot_music.gif'
                try:
                    import os
                    if os.path.exists(gif_path):
                        from vk_api.upload import VkUpload
                        upload = VkUpload(self.vk_session)
                        doc = upload.document_message(gif_path, peer_id=user_id)
                        attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
                        try:
                            self.vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                attachment=attachment
                            )
                        except Exception as gif_err:
                            logger.warning(f"⚠️ Не удалось отправить GIF: {gif_err}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка GIF при генерации музыки: {e}")

                # Запускаем генерацию в отдельном потоке
                import threading
                _genre = genre
                _uid = user_id

                def generate_instrumental_thread():
                    try:
                        from celery_tasks import generate_suno_music_sync

                        audio_url = generate_suno_music_sync(_genre)

                        if audio_url:
                            # Сохраняем в БД
                            try:
                                execute_query_sync(
                                    'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                                    (_uid, _genre, audio_url, False, False)
                                )
                            except Exception as db_err:
                                logger.error(f"❌ Ошибка сохранения музыки в БД: {db_err}")

                            # Парсим URL: может быть JSON-массив из 2 ссылок
                            try:
                                import json as _json
                                urls = _json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                            except Exception:
                                urls = [audio_url]

                            if len(urls) >= 2:
                                result_msg = (
                                    f"✅ Ваша инструментальная музыка готова!\n\n"
                                    f"🎵 Жанр: {_genre}\n\n"
                                    f"🎧 Вариант 1:\n{urls[0]}\n\n"
                                    f"🎧 Вариант 2:\n{urls[1]}"
                                )
                            else:
                                result_msg = (
                                    f"✅ Ваша инструментальная музыка готова!\n\n"
                                    f"🎵 Жанр: {_genre}\n\n"
                                    f"🔗 Слушать: {urls[0]}"
                                )

                            self.send_message(
                                user_id=_uid,
                                message=result_msg,
                                keyboard=self.get_main_keyboard(_uid)
                            )

                            # Списываем 1 токен
                            try:
                                execute_query_sync(
                                    "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                    (_uid,)
                                )
                                logger.info(f"💰 Списан 1 токен за инструментальную музыку: пользователь {_uid}")
                            except Exception as bal_err:
                                logger.error(f"❌ Ошибка списания баланса за музыку: {bal_err}")
                        else:
                            self.send_message(
                                user_id=_uid,
                                message="❌ Не удалось сгенерировать музыку. Попробуйте другой жанр или позже.",
                                keyboard=self.get_main_keyboard(_uid)
                            )
                    except Exception as e:
                        logger.error(f"❌ Ошибка в потоке генерации музыки: {e}")
                        self.send_message(
                            user_id=_uid,
                            message="❌ Произошла ошибка при генерации музыки. Попробуйте позже.",
                            keyboard=self.get_main_keyboard(_uid)
                        )

                music_thread = threading.Thread(target=generate_instrumental_thread, daemon=True)
                music_thread.start()

                command_handled = True
                return

            # Если команда не была обработана выше
            if not command_handled:
                # Проверяем, находится ли пользователь в каком-то состоянии
                current_state = self.user_states.get(user_id)
                if current_state:
                    # Обработка состояний (FSM)
                    if current_state in [UserState.WAITING_SONG_DESCRIPTION, UserState.WAITING_INSTRUMENTAL_DESCRIPTION]:
                        self.send_message(
                            user_id=user_id,
                            message="⏳ Спасибо! Ваш запрос принят в обработку...",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                        command_handled = True
                        return
                
                # Если команда всё ещё не обработана - отправляем сообщение о неизвестной команде
                if not command_handled:
                    logger.warning(f"❓ Неизвестная команда от {user_id}: '{text}' (в нижнем регистре: '{text_lower}')")
                    keyboard = self.get_main_keyboard(user_id)
                    if keyboard:
                        result = self.send_message(
                            user_id=user_id,
                            message="Я не понимаю эту команду. Воспользуйтесь меню 👇",
                            keyboard=keyboard
                        )
                        logger.info(f"📨 Отправка сообщения с меню: {'успешно' if result else 'ошибка'}")
                    else:
                        logger.error("❌ Не удалось создать клавиатуру для обычного сообщения")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.error(traceback.format_exc())
            
            # Пытаемся сбросить состояние пользователя и отправить сообщение об ошибке
            try:
                self.reset_state(user_id)
                self.send_message(
                    user_id=user_id,
                    message="Произошла ошибка при обработке сообщения. Попробуйте начать сначала.",
                    keyboard=self.get_main_keyboard(user_id)
                )
                logger.info(f"✅ Состояние пользователя {user_id} сброшено после ошибки")
            except Exception as inner_e:
                logger.error(f"❌ Ошибка при восстановлении после ошибки: {inner_e}")
            
    def start_music_generation(self, user_id, genre):
        """Запуск генерации инструментальной музыки"""
        try:
            # Отправляем сообщение о начале генерации
            self.send_message(
                user_id=user_id,
                message="⏳ Генерирую музыку, подождите 1-2 минуты...",
                keyboard=self.get_cancel_keyboard()
            )
            
            print(f"Запуск генерации музыки для пользователя {user_id}, жанр: {genre}")
            logger.info(f"🎵 Запуск генерации музыки для пользователя {user_id}, жанр: {genre}")
            
            # Запускаем генерацию музыки через Celery
            try:
                from celery_tasks import generate_suno_music_sync
                
                # Генерируем музыку
                audio_url = generate_suno_music_sync(genre)
                
                if audio_url:
                    # Сохраняем результат в базу данных
                    try:
                        execute_query_sync(
                            'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                            (user_id, genre, audio_url, False, False)
                        )
                        logger.info(f"✅ Результат генерации музыки сохранен в базе данных для пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения результата генерации музыки в базе данных: {e}")
                    
                    # Отправляем результат пользователю
                    self.send_message(
                        user_id=user_id,
                        message=f"✅ Ваша музыка готова!\n\nЖанр: {genre}\n\nСсылка: {audio_url}",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    
                    # Списываем баланс
                    try:
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка списания баланса: {e}")
                else:
                    # Если не удалось сгенерировать музыку
                    self.send_message(
                        user_id=user_id,
                        message="❌ Не удалось сгенерировать музыку. Попробуйте другой жанр или позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка генерации музыки: {e}")
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при генерации музыки. Попробуйте позже.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            
            # Сбрасываем состояние пользователя
            self.reset_state(user_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска генерации музыки: {e}")
            self.send_message(
                user_id=user_id,
                message="❌ Произошла ошибка. Попробуйте позже.",
                keyboard=self.get_main_keyboard(user_id)
            )
            self.reset_state(user_id)
    
    def start_song_generation(self, user_id, lyrics, genre):
        """Запуск генерации песни с текстом"""
        try:
            # Отправляем сообщение о начале генерации
            self.send_message(
                user_id=user_id,
                message="⏳ Генерирую песню, подождите 1-2 минуты...",
                keyboard=self.get_cancel_keyboard()
            )
            
            print(f"Запуск генерации песни для пользователя {user_id}, жанр: {genre}")
            logger.info(f"🎵 Запуск генерации песни для пользователя {user_id}, жанр: {genre}")
            
            # Запускаем генерацию песни через Celery
            try:
                from celery_tasks import generate_suno_song_sync
                
                # Проверяем длину текста песни и автоматически включаем customMode для длинных текстов
                use_custom_mode = len(lyrics) > 500
                if use_custom_mode:
                    logger.info(f"ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")
                
                # Генерируем песню
                result = generate_suno_song_sync(lyrics, genre)
                
                if result:
                    audio_url, task_id, audio_id = result
                    
                    # Сохраняем результат в базу данных
                    try:
                        execute_query_sync(
                            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_audio_id) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (user_id, task_id, genre, audio_url, False, use_custom_mode, audio_id)
                        )
                        logger.info(f"✅ Результат генерации песни сохранен в базе данных для пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения результата генерации песни в базе данных: {e}")
                    
                    # Импортируем клавиатуру с опциями
                    from vk_keyboards import get_song_options_keyboard
                    
                    # Подготовка сообщения с результатом
                    message_text = f"✅ Ваша песня готова!\n\nЖанр: {genre}\n\n"
                    
                    # Проверяем, содержит ли audio_url несколько ссылок (JSON массив)
                    try:
                        import json
                        audio_urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                        
                        # Если есть несколько ссылок, добавляем их все в сообщение
                        if len(audio_urls) > 1:
                            message_text += "🎵 **Варианты песни:**\n\n"
                            for i, url in enumerate(audio_urls, 1):
                                message_text += f"Вариант {i}: {url}\n\n"
                        else:
                            message_text += f"Ссылка: {audio_url}\n\n"
                    except Exception as json_error:
                        # Если не удалось распарсить JSON, логируем ошибку и используем строку как есть
                        logger.error(f"❌ Ошибка при парсинге JSON аудио URL: {json_error}")
                        message_text += f"Ссылка: {audio_url}\n\n"
                    
                    # Добавляем информацию о возможных действиях
                    message_text += "💎 **Что можно сделать с этой песней:**\n\n"
                    message_text += "🎤 **Минусовка** (1 токен) — версия без вокала для исполнения\n"
                    message_text += "🎸 **Кавер** (1 токен) — перепой в другом стиле/жанре\n"
                    message_text += "🎵 **В WAV** (2 токена) — конвертируй в WAV формат для профи\n"
                    message_text += "🔗 **Поделиться** — опубликуй трек на своей странице ВКонтакте"
                    
                    # Отправляем результат пользователю с клавиатурой опций
                    self.send_message(
                        user_id=user_id,
                        message=message_text,
                        keyboard=get_song_options_keyboard(task_id)
                    )
                    
                    # Списываем баланс
                    try:
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка списания баланса: {e}")
                else:
                    # Если не удалось сгенерировать песню
                    self.send_message(
                        user_id=user_id,
                        message="❌ Не удалось сгенерировать песню. Попробуйте другой жанр или позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка генерации песни: {e}")
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при генерации песни. Попробуйте позже.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            
            # Сбрасываем состояние пользователя
            self.reset_state(user_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска генерации песни: {e}")
            self.send_message(
                user_id=user_id,
                message="❌ Произошла ошибка. Попробуйте позже.",
                keyboard=self.get_main_keyboard(user_id)
            )
            self.reset_state(user_id)
    
    def handle_callback(self, event):
        """Обработчик событий от кнопок (callback)"""
        try:
            # Получаем данные из события
            user_id = event.obj.get('user_id')
            payload = event.obj.get('payload', {})
            
            logger.info(f"📩 Получено событие от кнопки от {user_id}: {payload}")
            print(f"Получен callback: {payload}")
            
            # Проверяем наличие payload
            if not payload:
                logger.error("❌ Пустой payload в событии от кнопки")
                return
            
            # Преобразуем payload в словарь, если он строка
            if isinstance(payload, str):
                try:
                    import json
                    payload = json.loads(payload)
                except Exception as e:
                    logger.error(f"❌ Ошибка при разборе payload: {e}")
                    return
            
            # Обработка различных действий из payload
            action = payload.get('action')
            task_id_from_payload = payload.get('task_id', '')
            if action == "create_music":
                print("Обработка кнопки 'Создать музыку'")
                logger.info(f"🎶 Запрос на создание инструментальной музыки от пользователя {user_id}")
                
                # Проверяем баланс пользователя
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Устанавливаем состояние выбора жанра музыки
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_MUSIC_STYLE)
                        )
                        # Для обратной совместимости
                        self.user_states[user_id] = UserState.WAITING_INSTRUMENTAL_DESCRIPTION
                        
                        # Импортируем клавиатуру для выбора жанра музыки
                        from vk_keyboards import get_music_genres_keyboard
                        
                        # Создаем клавиатуру с жанрами
                        keyboard = get_music_genres_keyboard()
                        
                        # Сообщение с выбором жанра
                        prompt_message = """🎶 **СОЗДАЕМ ИНСТРУМЕНТАЛЬНУЮ МУЗЫКУ**

🎹 Музыка БЕЗ слов - только мелодия и ритм!

Выбери жанр для твоей композиции 👇"""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=keyboard
                        )
                        
                        logger.info(f"✅ Пользователь {user_id} переведен в режим выбора жанра инструментальной музыки")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания музыки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания музыки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка кнопки "Минусовка"
            elif action == "karaoke":
                logger.info(f"🎤 Запрос на создание минусовки от пользователя {user_id}")
                
                # Проверяем баланс пользователя
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Отправляем сообщение о начале генерации минусовки
                        self.send_message(
                            user_id=user_id,
                            message="⏳ Генерирую минусовку, подождите 1-2 минуты...",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Запускаем генерацию минусовки в отдельном потоке
                        import threading
                        def generate_karaoke_thread():
                            try:
                                # Импортируем функцию для генерации минусовки
                                from celery_tasks import generate_suno_karaoke_sync
                                
                                # Получаем информацию о песне из базы данных
                                if task_id_from_payload:
                                    song_info = execute_query_sync(
                                        "SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                                        (task_id_from_payload, user_id)
                                    )
                                else:
                                    song_info = execute_query_sync(
                                        "SELECT audio_url, suno_audio_id FROM generations WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                                        (user_id,)
                                    )

                                if song_info and song_info[0][0] and song_info[0][1]:
                                    audio_url = song_info[0][0]
                                    suno_id = song_info[0][1]
                                    
                                    # Генерируем минусовку
                                    karaoke_url = generate_suno_karaoke_sync(suno_id)
                                    
                                    if karaoke_url:
                                        # Сохраняем результат в базу данных
                                        execute_query_sync(
                                            'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                                            (user_id, f"Минусовка для {suno_id}", karaoke_url, False, False)
                                        )
                                        
                                        # Отправляем результат пользователю
                                        self.send_message(
                                            user_id=user_id,
                                            message=f"✅ Минусовка готова!\n\nСсылка: {karaoke_url}",
                                            keyboard=self.get_main_keyboard(user_id)
                                        )
                                        
                                        # Списываем баланс
                                        execute_query_sync(
                                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                            (user_id,)
                                        )
                                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")
                                    else:
                                        # Если не удалось сгенерировать минусовку
                                        self.send_message(
                                            user_id=user_id,
                                            message="❌ Не удалось сгенерировать минусовку. Попробуйте позже.",
                                            keyboard=self.get_main_keyboard(user_id)
                                        )
                                else:
                                    # Если не найдена информация о песне
                                    self.send_message(
                                        user_id=user_id,
                                        message="❌ Не найдена информация о песне. Сначала создайте песню.",
                                        keyboard=self.get_main_keyboard(user_id)
                                    )
                            except Exception as e:
                                logger.error(f"❌ Ошибка генерации минусовки: {e}")
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Произошла ошибка при генерации минусовки. Попробуйте позже.",
                                    keyboard=self.get_main_keyboard(user_id)
                                )
                        
                        # Запускаем генерацию в отдельном потоке
                        thread = threading.Thread(target=generate_karaoke_thread)
                        thread.start()
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания минусовки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания минусовки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка кнопки "WAV"
            elif action == "wav":
                logger.info(f"🎵 Запрос на конвертацию в WAV от пользователя {user_id}")
                
                # Проверяем баланс пользователя
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 2:  # WAV стоит 2 токена
                        # Отправляем сообщение о начале конвертации
                        self.send_message(
                            user_id=user_id,
                            message="⏳ Конвертирую в WAV, подождите 1-2 минуты...",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Запускаем конвертацию в отдельном потоке
                        import threading
                        def convert_to_wav_thread():
                            try:
                                # Импортируем функцию для конвертации в WAV
                                from celery_tasks import generate_suno_wav_sync
                                
                                # Получаем информацию о песне из базы данных
                                if task_id_from_payload:
                                    song_info = execute_query_sync(
                                        "SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                                        (task_id_from_payload, user_id)
                                    )
                                else:
                                    song_info = execute_query_sync(
                                        "SELECT audio_url, suno_audio_id FROM generations WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                                        (user_id,)
                                    )

                                if song_info and song_info[0][0] and song_info[0][1]:
                                    audio_url = song_info[0][0]
                                    suno_id = song_info[0][1]
                                    
                                    # Конвертируем в WAV
                                    wav_url = generate_suno_wav_sync(suno_id)
                                    
                                    if wav_url:
                                        # Сохраняем результат в базу данных
                                        execute_query_sync(
                                            'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                                            (user_id, f"WAV для {suno_id}", wav_url, False, False)
                                        )
                                        
                                        # Отправляем результат пользователю
                                        self.send_message(
                                            user_id=user_id,
                                            message=f"✅ WAV файл готов!\n\nСсылка: {wav_url}\n\n⚠️ Файл доступен 24 часа",
                                            keyboard=self.get_main_keyboard(user_id)
                                        )
                                        
                                        # Списываем баланс
                                        execute_query_sync(
                                            "UPDATE users SET balance = balance - 2 WHERE user_id = %s",
                                            (user_id,)
                                        )
                                        logger.info(f"💰 Списано 2 токена с баланса пользователя {user_id}")
                                    else:
                                        # Если не удалось сконвертировать в WAV
                                        self.send_message(
                                            user_id=user_id,
                                            message="❌ Не удалось сконвертировать в WAV. Попробуйте позже.",
                                            keyboard=self.get_main_keyboard(user_id)
                                        )
                                else:
                                    # Если не найдена информация о песне
                                    self.send_message(
                                        user_id=user_id,
                                        message="❌ Не найдена информация о песне. Сначала создайте песню.",
                                        keyboard=self.get_main_keyboard(user_id)
                                    )
                            except Exception as e:
                                logger.error(f"❌ Ошибка конвертации в WAV: {e}")
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Произошла ошибка при конвертации в WAV. Попробуйте позже.",
                                    keyboard=self.get_main_keyboard(user_id)
                                )
                        
                        # Запускаем конвертацию в отдельном потоке
                        thread = threading.Thread(target=convert_to_wav_thread)
                        thread.start()
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для конвертации в WAV нужно 2 токена. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка конвертации в WAV при недостаточном балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для конвертации в WAV: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка кнопки "Кавер"
            elif action == "cover":
                logger.info(f"🎸 Запрос на создание кавера от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 1:  # Кавер стоит 1 токен
                        # Отправляем клавиатуру выбора жанра
                        from vk_keyboards import get_cover_genre_keyboard
                        self.send_message(
                            user_id=user_id,
                            message="🎸 **КАВЕР В НОВОМ ЖАНРЕ**\n\nВыбери жанр для создания кавера:",
                            keyboard=get_cover_genre_keyboard(task_id_from_payload)
                        )
                        logger.info(f"✅ Пользователь {user_id} получил клавиатуру выбора жанра для кавера (task_id={task_id_from_payload})")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для создания кавера нужен 1 токен. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания кавера при недостаточном балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для кавера: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )

            # Обработка выбора жанра для кавера
            elif action == "cover_genre":
                genre = payload.get('genre', '')
                cover_task_id = task_id_from_payload
                logger.info(f"🎸 Пользователь {user_id} выбрал жанр '{genre}' для кавера (task_id={cover_task_id})")

                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 1:
                        self.send_message(
                            user_id=user_id,
                            message=f"⏳ Создаю кавер в жанре «{genre}», подождите 2-3 минуты...",
                            keyboard=self.get_cancel_keyboard()
                        )

                        import threading
                        def generate_cover_thread():
                            try:
                                from celery_tasks import generate_suno_cover_sync

                                # Получаем suno_audio_id по task_id
                                if cover_task_id:
                                    song_info = execute_query_sync(
                                        "SELECT audio_url, suno_audio_id, prompt FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                                        (cover_task_id, user_id)
                                    )
                                else:
                                    song_info = execute_query_sync(
                                        "SELECT audio_url, suno_audio_id, prompt FROM generations WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                                        (user_id,)
                                    )

                                if song_info and song_info[0][1]:
                                    suno_id = song_info[0][1]
                                    original_prompt = song_info[0][2] or ''

                                    cover_url = generate_suno_cover_sync(suno_id, genre)

                                    if cover_url:
                                        # Сохраняем результат в базу данных
                                        execute_query_sync(
                                            'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                                            (user_id, f"Кавер [{genre}] для {suno_id}", cover_url, False, False)
                                        )
                                        self.send_message(
                                            user_id=user_id,
                                            message=f"✅ Кавер в жанре «{genre}» готов!\n\nСсылка: {cover_url}",
                                            keyboard=self.get_main_keyboard(user_id)
                                        )
                                        # Списываем 1 токен
                                        execute_query_sync(
                                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                            (user_id,)
                                        )
                                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id} за кавер")
                                    else:
                                        self.send_message(
                                            user_id=user_id,
                                            message="❌ Не удалось создать кавер. Попробуйте позже.",
                                            keyboard=self.get_main_keyboard(user_id)
                                        )
                                else:
                                    self.send_message(
                                        user_id=user_id,
                                        message="❌ Не найдена информация о песне. Сначала создайте песню.",
                                        keyboard=self.get_main_keyboard(user_id)
                                    )
                            except Exception as e:
                                logger.error(f"❌ Ошибка генерации кавера: {e}")
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Произошла ошибка при создании кавера. Попробуйте позже.",
                                    keyboard=self.get_main_keyboard(user_id)
                                )

                        thread = threading.Thread(target=generate_cover_thread)
                        thread.start()
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для создания кавера нужен 1 токен. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания кавера при недостаточном балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для кавера: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )

            # Обработка кнопки "Поделиться"
            elif action == "share":
                logger.info(f"🔗 Запрос на публикацию песни от пользователя {user_id}")
                try:
                    # Получаем данные о треке
                    if task_id_from_payload:
                        song_info = execute_query_sync(
                            "SELECT audio_url, prompt FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                            (task_id_from_payload, user_id)
                        )
                    else:
                        song_info = execute_query_sync(
                            "SELECT audio_url, prompt FROM generations WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                            (user_id,)
                        )

                    if song_info and song_info[0][0]:
                        import urllib.parse
                        audio_url = song_info[0][0]
                        # Если несколько URL — берём первый
                        try:
                            import json as _json
                            urls = _json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                            share_url = urls[0]
                        except Exception:
                            share_url = audio_url

                        bot_link = "https://vk.com/club235442407"
                        share_text = f"🎵 Послушай мою песню, созданную с помощью ALBI Music!\n\n🤖 Создай свою: {bot_link}"
                        vk_share_link = f"https://vk.com/share.php?url={urllib.parse.quote(share_url, safe='')}&title={urllib.parse.quote(share_text, safe='')}"

                        self.send_message(
                            user_id=user_id,
                            message=(
                                f"🔗 **Поделиться своей песней**\n\n"
                                f"Нажмите на ссылку ниже, чтобы опубликовать трек на своей странице ВКонтакте:\n\n"
                                f"{vk_share_link}\n\n"
                                f"или скопируйте прямую ссылку на трек:\n{share_url}"
                            ),
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.info(f"✅ Ссылка для публикации отправлена пользователю {user_id}")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ Не найдена информация о песне. Сначала создайте песню.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка при создании ссылки для публикации: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )

            # Отправляем ответ на событие (обязательно для callback-кнопок)
            try:
                self.vk.messages.sendMessageEventAnswer(
                    event_id=event.obj.get('event_id'),
                    user_id=user_id,
                    peer_id=event.obj.get('peer_id'),
                    event_data=json.dumps({"type": "show_snackbar", "text": "Команда получена"})
                )
            except Exception as callback_error:
                logger.error(f"❌ Ошибка при отправке ответа на callback: {callback_error}")
                # Пытаемся отправить обычное сообщение вместо callback-ответа
                try:
                    self.send_message(
                        user_id=user_id,
                        message="✅ Команда получена и обрабатывается",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                except Exception as msg_error:
                    logger.error(f"❌ Не удалось отправить альтернативное сообщение: {msg_error}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке события от кнопки: {e}")
            logger.error(traceback.format_exc())
            # Пытаемся отправить сообщение об ошибке пользователю
            try:
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при обработке команды. Попробуйте еще раз.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            except Exception as msg_error:
                logger.error(f"❌ Не удалось отправить сообщение об ошибке: {msg_error}")
    
    def run(self):
        """Запуск бота и прослушивание событий"""
        logger.info("🎧 Начинаю прослушивание событий...")
        
        # Увеличиваем таймаут для longpoll
        self.longpoll.wait = 60  # Увеличиваем время ожидания до 60 секунд
        
        # Запускаем прослушивание событий с обработкой ошибок соединения
        while True:
            try:
                # Переинициализируем longpoll при каждой итерации для избежания проблем с соединением
                self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
                logger.info("✅ Подключение к VK API успешно установлено (BotLongPoll)")
                
                # Запускаем прослушивание событий
                for event in self.longpoll.listen():
                    try:
                        # Обрабатываем новые входящие сообщения
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            # Обрабатываем сообщение
                            self.handle_message(event)
                        # Обрабатываем события от callback-кнопок (Минусовка, WAV, Кавер, Поделиться)
                        elif event.type == VkBotEventType.MESSAGE_EVENT:
                            # Обрабатываем событие от кнопки и отвечаем sendMessageEventAnswer
                            self.handle_callback(event)
                    except Exception as e:
                        logger.error(f"❌ Ошибка при обработке события: {e}")
                        logger.error(traceback.format_exc())
                        # Продолжаем работу после ошибки обработки события
            except requests.exceptions.ReadTimeout:
                logger.warning("⚠️ Таймаут соединения с VK API. Переподключение...")
                time.sleep(5)  # Ждем 5 секунд перед переподключением
                continue
            except requests.exceptions.ConnectionError:
                logger.warning("⚠️ Ошибка соединения с VK API. Переподключение...")
                time.sleep(10)  # Ждем 10 секунд перед переподключением
                continue
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле бота: {e}")
                logger.error(traceback.format_exc())
                logger.info("🔄 Перезапуск основного цикла через 15 секунд...")
                time.sleep(15)  # Ждем 15 секунд перед перезапуском

if __name__ == '__main__':
    # Создаем экземпляр бота с обработкой ошибок
    max_restart_attempts = 3
    restart_count = 0
    
    while restart_count < max_restart_attempts:
        try:
            # Создаем экземпляр бота
            bot = VKBot()
            
            # Запускаем бота
            try:
                logger.info("🚀 Запуск VK бота...")
                logger.info("🎯 Бот ВК успешно запущен и слушает сообщения!")
                bot.run()
            except KeyboardInterrupt:
                logger.info("👋 Бот остановлен пользователем")
                break  # Выходим из цикла перезапуска при ручной остановке
            except Exception as e:
                restart_count += 1
                logger.error(f"❌ Ошибка при запуске бота (попытка {restart_count}/{max_restart_attempts}): {e}")
                logger.error(f"❌ Трассировка ошибки: {traceback.format_exc()}")
                
                if restart_count < max_restart_attempts:
                    wait_time = 15 * restart_count  # Увеличиваем время ожидания с каждой попыткой
                    logger.info(f"🔄 Перезапуск бота через {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    logger.critical("❌ Достигнуто максимальное количество попыток перезапуска")
        except Exception as init_error:
            restart_count += 1
            logger.critical(f"❌ Критическая ошибка при инициализации бота (попытка {restart_count}/{max_restart_attempts}): {init_error}")
            logger.critical(f"❌ Трассировка ошибки: {traceback.format_exc()}")
            
            if restart_count < max_restart_attempts:
                wait_time = 20 * restart_count  # Более длительное ожидание при ошибке инициализации
                logger.info(f"🔄 Повторная попытка через {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                logger.critical("❌ Не удалось запустить бота после нескольких попыток")