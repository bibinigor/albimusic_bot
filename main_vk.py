import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import logging
from datetime import datetime
from enum import Enum, auto
from vk_config import VK_TOKEN, VK_GROUP_ID, DEBUG, ADMIN_VK_ID
from db_utils import execute_query_sync, init_db_pool_sync

# Список базовых команд для сброса состояния
RESET_COMMANDS = ["начать", "start", "меню", "🏠 в главное меню", "❌ отмена", "отмена"]
# Список команд главного меню
MENU_COMMANDS = ["💰 баланс", "📂 мои треки", "🎵 создать песню", "🎶 создать музыку", "🎧 примеры песен", "📞 поддержка", "⚙️ админ"]

# Состояния пользователя (FSM)
class UserState(Enum):
    START = auto()
    WAITING_SONG_DESCRIPTION = auto()
    WAITING_INSTRUMENTAL_DESCRIPTION = auto()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure logger format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize database pool
init_db_pool_sync()
logging.info("✅ Database pool initialized")

# Create users table if not exists
try:
    execute_query_sync("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            invited_by BIGINT,
            free_generation_used BOOLEAN DEFAULT FALSE,
            first_menu_action_at TIMESTAMP
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
        
        # Словарь для хранения состояний пользователей
        self.user_states = {}
        
        logger.info("VK Bot initialized successfully")

    def get_cancel_keyboard(self):
        """Создать клавиатуру с кнопкой возврата в меню"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.PRIMARY)
        return keyboard

    def get_home_keyboard(self):
        """Создать клавиатуру с кнопкой возврата в главное меню"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.SECONDARY)
        return keyboard

    def reset_state(self, user_id):
        """Сбросить состояние пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
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
                params['keyboard'] = keyboard.get_keyboard()
            
            self.vk.messages.send(**params)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False

    def get_main_keyboard(self, user_id=None):
        """Create main menu keyboard"""
        try:
            logger.info("⌨️ Создание главной клавиатуры")
            keyboard = VkKeyboard(one_time=False)
            
            # First row (максимум 2 кнопки в ряду для ВК)
            keyboard.add_button("🎵 Создать песню", color=VkKeyboardColor.POSITIVE)
            keyboard.add_button("🎶 Создать музыку", color=VkKeyboardColor.POSITIVE)
            
            # Second row
            keyboard.add_line()
            keyboard.add_button("📂 Мои треки", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button("💰 Баланс", color=VkKeyboardColor.PRIMARY)
            
            # Third row
            keyboard.add_line()
            keyboard.add_button("🎧 Примеры песен", color=VkKeyboardColor.SECONDARY)
            keyboard.add_button("📞 Поддержка", color=VkKeyboardColor.SECONDARY)

            # Admin button
            if user_id and user_id == ADMIN_VK_ID:
                keyboard.add_line()
                keyboard.add_button("⚙️ Админ", color=VkKeyboardColor.NEGATIVE)
            
            logger.info("✅ Клавиатура успешно создана")
            return keyboard
        except Exception as e:
            logger.error(f"❌ Ошибка создания клавиатуры: {e}")
            return None

    def register_user(self, user_id, username=None, first_name=None):
        """Register new user in database"""
        try:
            execute_query_sync(
                'INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
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
            total_users = execute_query_sync("SELECT COUNT(*) FROM users")[0][0]
            
            # Новые за 24 часа
            users_24h = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours'"
            )[0][0]
            
            # Новые за 7 дней
            users_7d = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )[0][0]
            
            # Новые за 30 дней
            users_30d = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"
            )[0][0]
            
            # Дошли до меню за 24 часа
            menu_24h = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours' AND first_menu_action_at IS NOT NULL"
            )[0][0]
            
            # Генерации за 24 часа
            gens_24h = execute_query_sync(
                "SELECT COUNT(*) FROM generations WHERE created_at >= NOW() - INTERVAL '24 hours'"
            )[0][0]
            
            # Общий успех генераций
            total_gens = execute_query_sync("SELECT COUNT(*) FROM generations")[0][0]
            success_gens = execute_query_sync("SELECT COUNT(*) FROM generations WHERE status = 'completed'")[0][0]
            success_rate = round((success_gens * 100.0) / total_gens, 1) if total_gens > 0 else 0
            
            # Статистика платежей
            try:
                # За 24 часа
                payments_24h = execute_query_sync(
                    "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'"
                )[0]
                payments_count_24h = payments_24h[0]
                payments_sum_24h = int(payments_24h[1])
                
                # За 7 дней
                payments_7d = execute_query_sync(
                    "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded' AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
                )[0]
                payments_count_7d = payments_7d[0]
                payments_sum_7d = int(payments_7d[1])
                
                # Всего
                payments_all = execute_query_sync(
                    "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded'"
                )[0]
                payments_count_all = payments_all[0]
                payments_sum_all = int(payments_all[1])
            except Exception:
                # Если таблица payments не существует
                payments_count_24h = payments_sum_24h = 0
                payments_count_7d = payments_sum_7d = 0
                payments_count_all = payments_sum_all = 0
            
            return f"""📊 Статистика бота:

👥 Всего пользователей: {total_users} (+{users_24h})
📈 Новых за 7 дней: {users_7d}
📅 Новых за 30 дней: {users_30d}

📊 Воронка (НОВЫЕ за 24ч):
▶️ Нажали Начать (новые): {users_24h}
🖱 Дошли до меню: {menu_24h}

🎵 Генераций за 24ч: {gens_24h} шт
✅ Общий успех (все время): {success_rate}%

💳 Оплаты:
⏰ За 24ч: {payments_count_24h} платежей · {payments_sum_24h}₽
📆 За 7 дней: {payments_count_7d} платежей · {payments_sum_7d}₽
📊 Всего: {payments_count_all} платежей · {payments_sum_all}₽"""
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return "❌ Ошибка получения статистики"

    def handle_message(self, event):
        """Обработчик входящих сообщений"""
        user_id = event.user_id
        text = event.text if event.text else ""
        text_lower = text.lower()  # Приводим к нижнему регистру сразу
        
        # Логируем все входящие сообщения до любой обработки
        logger.info(f"📩 Получено новое сообщение от {user_id}: '{text}' (в нижнем регистре: '{text_lower}')")
        
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
            if text in RESET_COMMANDS:
                logger.info(f"🔄 Получена команда сброса состояния от {user_id}: '{text}'")
                self.reset_state(user_id)
                welcome_text = "Вы вернулись в главное меню!"
                
                if text in ["начать", "start"]:
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
            # Проверяем базовые команды до любой другой обработки
            if text_lower in RESET_COMMANDS:
                logger.info(f"🔄 Получена команда сброса состояния от {user_id}: '{text}'")
                self.reset_state(user_id)
                welcome_text = "Вы вернулись в главное меню!"
                
                if text_lower in ["начать", "start"]:
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
            if "создать песню" in text_lower:
                logger.info(f"🎵 Запрос на создание песни от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        self.user_states[user_id] = UserState.WAITING_SONG_DESCRIPTION
                        prompt_message = """✨ Напишите описание для вашей песни:

• Стиль и жанр (рок, поп, рэп и т.д.)
• Настроение и атмосфера (веселая, грустная, энергичная)
• О чем должна быть песня (любовь, дружба, мечты)
• Какой вокал (мужской/женский)

💫 Чем подробнее описание, тем лучше результат!
❌ Чтобы отменить создание, нажмите кнопку "🏠 В главное меню"."""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=self.get_cancel_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} переведен в режим ожидания описания песни")
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

            elif "создать музыку" in text_lower:
                logger.info(f"🎶 Запрос на создание инструментальной музыки от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        self.user_states[user_id] = UserState.WAITING_INSTRUMENTAL_DESCRIPTION
                        prompt_message = """✨ Напишите описание для вашей ИНСТРУМЕНТАЛЬНОЙ музыки (без вокала):

• Стиль и жанр (рок, поп, электронная и т.д.)
• Настроение и атмосфера (веселая, грустная, энергичная)
• Темп (быстрый, медленный, умеренный)
• Основные инструменты (гитара, пианино, синтезатор)

💫 Чем подробнее описание, тем лучше результат!
❌ Чтобы отменить создание, нажмите кнопку "🏠 В главное меню"."""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=self.get_cancel_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} переведен в режим ожидания описания инструментальной музыки")
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

            elif "баланс" in text_lower:
                    logger.info(f"👤 Запрос баланса от пользователя {user_id}")
                    try:
                        result = execute_query_sync(
                            "SELECT user_id, created_at, balance FROM users WHERE user_id = %s",
                            (user_id,)
                        )
                        if result:
                            user_data = result[0]
                            created_at = user_data[1].strftime("%d.%m.%Y")
                            balance = user_data[2]
                            
                            message = f"""📊 Ваш профиль:
                            
👤 ID: {user_data[0]}
📅 Дата регистрации: {created_at}
💰 Баланс: {balance} генераций

💫 1 генерация = 2 песни
🎁 Пригласите друга и получите +2 генерации!"""
                            logger.info(f"✅ Успешно получен баланс для {user_id}: {balance} генераций")
                        else:
                            message = "❌ Ошибка получения данных профиля"
                            logger.error(f"❌ Пользователь {user_id} не найден в базе данных")
                        
                        self.send_message(user_id=user_id, message=message, keyboard=self.get_main_keyboard(user_id))
                        command_handled = True
                    except Exception as e:
                        logger.error(f"❌ Ошибка при получении баланса для {user_id}: {e}")
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка при получении баланса. Попробуйте позже.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        command_handled = True

            # Обработка команды возврата в главное меню
            if text == "🏠 В главное меню":
                self.reset_state(user_id)
                self.send_message(
                    user_id=user_id,
                    message="Вы вернулись в главное меню!",
                    keyboard=self.get_main_keyboard(user_id)
                )
                return

            # Обработка состояний
            current_state = self.user_states.get(user_id, UserState.START)

            if current_state == UserState.WAITING_SONG_DESCRIPTION or current_state == UserState.WAITING_INSTRUMENTAL_DESCRIPTION:
                # Обработка описания песни или инструментальной музыки
                self.send_message(
                    user_id=user_id,
                    message="⏳ Спасибо! Ваш запрос принят в обработку...",
                    keyboard=self.get_main_keyboard()
                )
                self.reset_state(user_id)
                return

            # Обработка кнопок главного меню

            elif "поддержка" in text_lower:
                logger.info(f"📞 Запрос в поддержку от пользователя {user_id}")
                support_message = """Служба поддержки ALBI Music 🛠

По всем вопросам пишите мне в личные сообщения: [https://vk.com/igorbibin]

⏳ Отвечу вам в течение дня."""
                
                self.send_message(
                    user_id=user_id,
                    message=support_message,
                    keyboard=self.get_main_keyboard(user_id)
                )
                logger.info(f"✅ Отправлена информация о поддержке пользователю {user_id}")
                command_handled = True

            elif "примеры" in text_lower:
                logger.info(f"🎵 Запрос примеров песен от пользователя {user_id}")
                demo_message = """Примеры сгенерированных треков можно послушать в нашем сообществе: [https://vk.com/club235442407]"""
                
                self.send_message(
                    user_id=user_id,
                    message=demo_message,
                    keyboard=self.get_main_keyboard(user_id)
                )
                logger.info(f"✅ Отправлены ссылки на примеры пользователю {user_id}")
                command_handled = True


            elif text == "🎶 Создать музыку":
                logger.info(f"🎶 Запрос на создание инструментальной музыки от пользователя {user_id}")
                
                # Проверяем баланс пользователя перед созданием
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        self.user_states[user_id] = UserState.WAITING_INSTRUMENTAL_DESCRIPTION
                        prompt_message = """✨ Напишите описание для вашей ИНСТРУМЕНТАЛЬНОЙ музыки (без вокала):

• Стиль и жанр (рок, поп, электронная и т.д.)
• Настроение и атмосфера (веселая, грустная, энергичная)
• Темп (быстрый, медленный, умеренный)
• Основные инструменты (гитара, пианино, синтезатор)

💫 Чем подробнее описание, тем лучше результат!
❌ Чтобы отменить создание, нажмите кнопку "Отмена"."""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=self.get_home_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} переведен в режим ожидания описания инструментальной музыки")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard()
                        )
                        logger.warning(f"⚠️ Попытка создания музыки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания музыки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard()
                    )

            elif "админ" in text_lower:
                logger.info(f"⚙️ Запрос админ-панели от пользователя {user_id}")
                if user_id != ADMIN_VK_ID:
                    self.send_message(
                        user_id=user_id,
                        message="⛔ Доступ запрещен",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    command_handled = True
                    return
                
                stats = self.get_admin_stats()
                self.send_message(
                    user_id=user_id,
                    message=stats,
                    keyboard=self.get_main_keyboard(user_id)
                )
                command_handled = True
                return

            elif "мои треки" in text_lower:
                logger.info(f"📂 Запрос списка треков от пользователя {user_id}")
                try:
                    # Получаем последние 20 генераций пользователя
                    tracks = execute_query_sync(
                        """
                        SELECT task_id, prompt, audio_url, created_at, status
                        FROM generations
                        WHERE user_id = %s AND status = 'completed'
                        ORDER BY created_at DESC LIMIT 20
                        """,
                        (user_id,)
                    )

                    if not tracks:
                        self.send_message(
                            user_id=user_id,
                            message="*У вас пока нет созданных треков. Самое время это исправить! 🎵*",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        return

                    # Отправляем общую статистику
                    self.send_message(
                        user_id=user_id,
                        message=f"🎵 *Ваши композиции*\n\n📊 Всего создано: {len(tracks)} треков\n━━━━━━━━━━━━━━━━━"
                    )

                    # Отправляем каждый трек отдельным сообщением
                    for idx, (task_id, prompt, audio_url, created_at, status) in enumerate(tracks[:10], 1):
                        # Форматируем дату
                        date_str = created_at.strftime("%d.%m.%Y") if hasattr(created_at, 'strftime') else str(created_at)[:10]
                        
                        # Форматируем описание
                        short_prompt = prompt[:100] + '...' if len(prompt) > 100 else prompt
                        
                        track_text = (
                            f"*Трек #{idx}*\n"
                            f"📅 Дата: {date_str}\n"
                            f"📝 Описание: _{short_prompt}_\n"
                            f"━━━━━━━━━━━━━━━━━"
                        )
                        
                        self.send_message(user_id=user_id, message=track_text)

                    if len(tracks) > 10:
                        self.send_message(
                            user_id=user_id,
                            message=f"_... и еще {len(tracks)-10} треков_\n\nПоказаны последние 10 из {len(tracks)} треков",
                            keyboard=self.get_main_keyboard(user_id)
                        )

                except Exception as e:
                    logger.error(f"❌ Ошибка при получении треков пользователя {user_id}: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при получении списка треков. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
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

    def run(self):
        """Start the bot's event loop"""
        logger.info("Starting VK bot...")
        try:
            # Проверяем подключение к VK API
            try:
                self.vk.groups.getById()
                logger.info("✅ Подключение к VK API успешно установлено")
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к VK API: {e}")
                return

            # Проверяем права группы
            try:
                group_info = self.vk.groups.getById(group_id=VK_GROUP_ID)[0]
                logger.info(f"✅ Подключились к группе: {group_info['name']} (ID: {group_info['id']})")
            except Exception as e:
                logger.error(f"❌ Ошибка получения информации о группе: {e}")
                return

            logger.info("🎯 Бот ВК успешно запущен и слушает сообщения!")
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    logger.debug(f"New message from user {event.user_id}: {event.text}")
                    self.handle_message(event)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise

def main():
    bot = VKBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()