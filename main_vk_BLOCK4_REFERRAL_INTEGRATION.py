# 🔴 БЛОК 4: Интеграция реферальной системы в main_vk.py

# ==================== ЧАСТЬ 1: Импорты (добавить в начало файла) ====================

from vk_referral_system import (
    add_referral,
    get_referral_count,
    get_referral_progress,
    get_referral_link,
    parse_referral_code,
    get_referral_stats
)


# ==================== ЧАСТЬ 2: Парсинг реферального кода при /start ====================
# Обновить обработку команды "начать" в handle_message()

# Найти блок:
if text_lower in ["начать", "start"]:
    logger.info(f"🔄 Получена команда начала работы от {user_id}: '{text}'")
    # Принудительно сбрасываем состояние
    self.reset_state(user_id)
    
    # ✅ БЛОК 4: Парсинг реферального кода из payload
    # В VK реферальные параметры НЕ передаются через /start как в Telegram
    # Вместо этого нужно использовать payload кнопки "Начать" или utm-метки
    # Для упрощения будем сохранять ref в session через callback кнопки
    
    # Пример: при первом запуске бота через реферальную ссылку
    # пользователь видит кнопку "Начать" с payload {"action": "start", "ref": "ref_123456"}
    
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


# ==================== ЧАСТЬ 3: Обработка реферального кода из payload ====================
# Добавить в handle_message() после парсинга payload

# Если в payload есть ref, обрабатываем его
if payload and isinstance(payload, dict):
    ref_code = payload.get('ref')
    if ref_code:
        logger.info(f"🔗 Получен реферальный код: {ref_code} от пользователя {user_id}")
        
        # Парсим ID реферера
        referrer_id = parse_referral_code(ref_code)
        
        if referrer_id:
            # Проверяем, не новый ли это пользователь
            try:
                user_exists = execute_query_sync(
                    "SELECT invited_by FROM users WHERE user_id = %s",
                    (user_id,)
                )
                
                # Если пользователь новый (только что зарегистрировался)
                if not user_exists or user_exists[0][0] is None:
                    # Добавляем реферальную связь
                    result = add_referral(referrer_id, user_id)
                    
                    if result['success']:
                        # Уведомляем реферера
                        try:
                            self.send_message(
                                user_id=referrer_id,
                                message=result['message'],
                                keyboard=self.get_main_keyboard(referrer_id)
                            )
                        except Exception as notify_error:
                            logger.error(f"❌ Не удалось уведомить реферера {referrer_id}: {notify_error}")
                    
                    logger.info(f"✅ Реферальная связь обработана: {referrer_id} → {user_id}")
                else:
                    logger.info(f"ℹ️ Пользователь {user_id} уже зарегистрирован, реферал не засчитан")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки реферального кода: {e}")


# ==================== ЧАСТЬ 4: Обновление сообщения "💰 Баланс" ====================
# Заменить блок обработки "баланс" в handle_message()

elif "баланс" in text_lower or text == "💰 Баланс":
    logger.info(f"💰 Запрос баланса от пользователя {user_id}")
    try:
        result = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        balance_num = result[0][0] if result else 0
        balance_str = f"💰 {balance_num} токенов" if balance_num > 0 else "❌ 0 токенов"
        
        # ✅ БЛОК 4: Добавляем информацию о рефералах
        referral_progress = get_referral_progress(user_id)
        referral_count = referral_progress['count']
        referral_progress_str = referral_progress['progress']
        
        # Формируем прогресс-бар
        filled = min(referral_count, 5)
        empty = 5 - filled
        progress_bar = "🟢" * filled + "⚪" * empty
        
        balance_msg = f"""💰 Ваш баланс: {balance_str}

🌟 РЕФЕРАЛЬНАЯ ПРОГРАММА
{progress_bar} {referral_progress_str}

Пригласи друзей и получи бонусы:
• За каждого друга: +2 токена
• За 5-го друга: +5 токенов (бонус)

💳 Тарифы:

💫 1 токен (2 песни) — 50₽
💳 10 токенов (20 песен) — 250₽
🔥 25 токенов (50 песен) — 500₽
⭐ 60 токенов (120 песен) — 1000₽
💎 140 токенов (280 песен) — 2000₽

🎁 Первый токен в подарок — для новых пользователей!

📩 Для оплаты напишите в поддержку: https://vk.com/igorbibin"""
        
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


# ==================== ЧАСТЬ 5: Callback для кнопки "Пригласить друга" ====================
# Добавить в handle_callback() или создать отдельную кнопку в главном меню

# Вариант А: Callback из inline-кнопки в сообщении "Баланс"
elif action == "invite_friend":
    logger.info(f"🌟 Запрос реферальной ссылки от пользователя {user_id}")
    
    try:
        # Получаем статистику
        progress = get_referral_progress(user_id)
        stats = get_referral_stats(user_id)
        
        # Генерируем реферальную ссылку
        ref_link = get_referral_link(user_id, "club235442407")  # Замените на ID вашей группы
        
        # Формируем сообщение
        message_text = f"""🌟 ПРИГЛАСИ ДРУЗЕЙ — ПОЛУЧИ ТОКЕНЫ!

Твой прогресс: {progress['progress']}
Заработано токенов: {stats['tokens_earned']}

📱 Твоя реферальная ссылка:
{ref_link}

🎁 За каждого друга ты получишь 2 токена!
🔥 За 5-го друга — бонус +5 токенов!

Скопируй ссылку и отправь друзьям в ВКонтакте!"""
        
        self.send_message(
            user_id=user_id,
            message=message_text,
            keyboard=self.get_main_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации реферальной ссылки: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )


# Вариант Б: Отдельная команда в главном меню (если добавить кнопку)
elif "пригласить" in text_lower or text == "🌟 Пригласить друга":
    logger.info(f"🌟 Запрос реферальной ссылки от пользователя {user_id}")
    
    try:
        # Получаем статистику
        progress = get_referral_progress(user_id)
        stats = get_referral_stats(user_id)
        
        # Генерируем реферальную ссылку
        ref_link = get_referral_link(user_id, "club235442407")  # Замените на ID вашей группы
        
        # Формируем сообщение
        message_text = f"""🌟 ПРИГЛАСИ ДРУЗЕЙ — ПОЛУЧИ ТОКЕНЫ!

Твой прогресс: {progress['progress']}
Заработано токенов: {stats['tokens_earned']}

📱 Твоя реферальная ссылка:
{ref_link}

🎁 За каждого друга ты получишь 2 токена!
🔥 За 5-го друга — бонус +5 токенов!

Скопируй ссылку и отправь друзьям в ВКонтакте!"""
        
        self.send_message(
            user_id=user_id,
            message=message_text,
            keyboard=self.get_main_keyboard(user_id)
        )
        
        command_handled = True
        return
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации реферальной ссылки: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )
        command_handled = True
        return


# ====================ЧАСТЬ 6: Добавить кнопку в главное меню (опционально) ====================
# В файле vk_keyboards.py, функция get_main_keyboard()

def get_main_keyboard(user_id=None):
    """Основная клавиатура бота"""
    from vk_config import ADMIN_VK_ID
    
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🎵 Создать песню', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎶 Создать музыку', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('📂 Мои треки', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('💰 Баланс', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('🎧 Примеры песен', color=VkKeyboardColor.SECONDARY)
    
    # ✅ БЛОК 4: Добавляем кнопку "Пригласить друга"
    keyboard.add_button('🌟 Пригласить друга', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('📞 Поддержка', color=VkKeyboardColor.SECONDARY)
    
    # Добавляем кнопку админ-панели только для администратора
    if user_id and user_id == ADMIN_VK_ID:
        keyboard.add_line()
        keyboard.add_button('⚙️ Админ', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard


# ==================== КОНЕЦ БЛОКА 4 ====================

# ВАЖНАЯ ЗАМЕТКА: 
# В ВКонтакте реферальные параметры НЕ передаются автоматически при открытии бота.
# Есть 2 способа реализации:
#
# Способ 1 (рекомендуется): Callback-кнопка "Начать" с payload
# - Создать пост с кнопкой, у которой payload={"action": "start", "ref": "ref_123456"}
# - При нажатии кнопки payload передается в событие MESSAGE_EVENT
# - Обрабатываем ref и создаем реферальную связь
#
# Способ 2: VK Mini Apps (требует разработки)
# - Создать VK Mini App с параметрами vk_ref
# - Обрабатывать параметры при запуске приложения
#
# Для максимальной простоты рекомендую Способ 1.
