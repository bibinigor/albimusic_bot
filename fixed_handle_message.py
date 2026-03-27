def handle_message(self, event):
        """Обработчик входящих сообщений"""
        user_id = event.user_id
        text = event.text if event.text else ""
        text_lower = text.lower()  # Приводим к нижнему регистру сразу
        
        # Логируем все входящие сообщения до любой обработки
        logger.info(f"📩 Получено новое сообщение от {user_id}: '{text}' (в нижнем регистре: '{text_lower}')")
        print(f"Получено сообщение: {text}")
        
        # Проверяем наличие payload в сообщении
        payload = None
        if hasattr(event, 'payload') and event.payload:
            try:
                import json
                payload = json.loads(event.payload)
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

            elif "баланс" in text_lower or text == "💰 Баланс":
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
                        
                        # Получаем количество приглашенных пользователей
                        referrals_result = execute_query_sync(
                            "SELECT COUNT(*) FROM referrals WHERE referrer_id = %s",
                            (user_id,)
                        )
                        referral_count = referrals_result[0][0] if referrals_result else 0
                        
                        # Создаем сообщение с информацией о балансе
                        message = f"""💰 *Ваш баланс:* {balance} токенов

📊 *Ваш профиль:*
 ID: {user_data[0]}
📅 Дата регистрации: {created_at}
👥 Приглашено друзей: {referral_count}

💫 1 токен = 2 песни
🎁 Пригласите друга и получите +2 токена!

*Тарифы:*
💫 1 токен (2 песни) — 50₽
💳 10 токенов (20 песен) — 250₽
🔥 25 токенов (50 песен) — 500₽
⭐ 60 токенов (120 песен) — 1000₽
💎 140 токенов (280 песен) — 2000₽"""
                        
                        # Импортируем клавиатуру для страницы баланса
                        from vk_keyboards import get_balance_actions_keyboard
                        
                        # Создаем клавиатуру с кнопками пополнения баланса
                        keyboard = get_balance_actions_keyboard()
                        
                        logger.info(f"✅ Успешно получен баланс для {user_id}: {balance} генераций")
                    else:
                        message = "❌ Ошибка получения данных профиля"
                        logger.error(f"❌ Пользователь {user_id} не найден в базе данных")
                        keyboard = self.get_main_keyboard(user_id)
                    
                    self.send_message(user_id=user_id, message=message, keyboard=keyboard)
                    command_handled = True
                except Exception as e:
                    logger.error(f"❌ Ошибка при получении баланса для {user_id}: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при получении баланса. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    command_handled = True

            # Обработка кнопок админ-панели
            if user_id == ADMIN_VK_ID:
                # Обработка кнопки "Обновить статистику"
                if "обновить статистику" in text_lower:
                    stats = self.get_admin_stats()
                    
                    # Создаем клавиатуру для админ-панели
                    admin_keyboard = VkKeyboard(one_time=False)
                    
                    # Получаем количество непрочитанных сообщений поддержки
                    try:
                        unread_result = execute_query_sync(
                            "SELECT COUNT(*) FROM support_messages WHERE replied = FALSE"
                        )
                        unread_count = unread_result[0][0] if unread_result else 0
                    except Exception as e:
                        logger.error(f"❌ Ошибка получения количества непрочитанных сообщений: {e}")
                        unread_count = 0
                    
                    # Формируем текст кнопки поддержки
                    support_label = f"📩 Поддержка ({unread_count})" if unread_count > 0 else "📩 Поддержка"
                    
                    # Добавляем кнопки в клавиатуру
                    admin_keyboard.add_button("🔄 Обновить статистику", color=VkKeyboardColor.PRIMARY)
                    admin_keyboard.add_button("🔍 Проверить API", color=VkKeyboardColor.PRIMARY)
                    
                    admin_keyboard.add_line()
                    admin_keyboard.add_button("📨 Рассылка", color=VkKeyboardColor.POSITIVE)
                    admin_keyboard.add_button(support_label, color=VkKeyboardColor.POSITIVE)
                    
                    admin_keyboard.add_line()
                    admin_keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.SECONDARY)
                    
                    # Отправляем статистику с клавиатурой
                    self.send_message(
                        user_id=user_id,
                        message=stats,
                        keyboard=admin_keyboard
                    )
                    command_handled = True
                    return
                
                # Обработка кнопки "Проверить API"
                elif "проверить api" in text_lower:
                    self.send_message(
                        user_id=user_id,
                        message="🔍 Проверка API Suno..."
                    )
                    
                    # Здесь должен быть код проверки API
                    # Пока просто отправляем заглушку
                    api_status = """🔍 *Проверка Suno API*
⏰ 25.03.2026 10:47

✅ /api/v1/generate: 200 OK (1.2 сек)
✅ /api/v1/generate/record-info: 200 OK (0.8 сек)

📢 *Вердикт:* ✅ API отвечает корректно"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=api_status,
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    command_handled = True
                    return
                
                # Обработка кнопки "Рассылка"
                elif "рассылка" in text_lower:
                    # Переводим админа в состояние ожидания текста рассылки
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_BROADCAST_TEXT)
                    )
                    
                    self.send_message(
                        user_id=user_id,
                        message="""📨 *Рассылка сообщений*

Отправьте текст сообщения для рассылки всем пользователям.
Поддерживается *жирный*, _курсив_, `код`, ссылки.

Чтобы отменить, нажмите кнопку "🏠 В главное меню".""",
                        keyboard=self.get_cancel_keyboard()
                    )
                    command_handled = True
                    return
                
                # Обработка кнопки "Поддержка"
                elif "поддержка" in text_lower:
                    # Получаем непрочитанные сообщения поддержки
                    try:
                        messages = execute_query_sync(
                            """SELECT id, user_id, username, first_name, message, created_at
                            FROM support_messages
                            WHERE replied = FALSE
                            ORDER BY created_at DESC
                            LIMIT 10"""
                        )
                        
                        if not messages:
                            self.send_message(
                                user_id=user_id,
                                message="📭 Нет непрочитанных сообщений в поддержке.",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                            command_handled = True
                            return
                        
                        # Отправляем каждое сообщение отдельно
                        for msg_id, msg_user_id, username, first_name, text, created_at in messages:
                            # Форматируем дату
                            date_str = created_at.strftime("%d.%m.%Y %H:%M") if hasattr(created_at, 'strftime') else str(created_at)[:16]
                            
                            # Создаем клавиатуру для ответа
                            reply_keyboard = VkKeyboard(inline=True)
                            reply_keyboard.add_button(f"💬 Ответить {msg_id}", color=VkKeyboardColor.PRIMARY)
                            reply_keyboard.add_button(f"🗑 Закрыть {msg_id}", color=VkKeyboardColor.NEGATIVE)
                            
                            # Формируем сообщение
                            user_str = f"@{username}" if username else f"id{msg_user_id}"
                            header = f"🔴 *{first_name}* ({user_str}) — {date_str}"
                            message = f"{header}\n\n{text}"
                            
                            self.send_message(
                                user_id=user_id,
                                message=message,
                                keyboard=reply_keyboard
                            )
                        
                        command_handled = True
                        return
                    except Exception as e:
                        logger.error(f"❌ Ошибка получения сообщений поддержки: {e}")
                        self.send_message(
                            user_id=user_id,
                            message=f"❌ Ошибка: {e}",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        command_handled = True
                        return
            
            # Обработка кнопки "Пригласить друга"
            if "пригласить друга" in text_lower:
                # Создаем реферальную ссылку
                referral_link = f"https://vk.com/app{VK_GROUP_ID}#ref_{user_id}"
                
                # Отправляем сообщение с реферальной ссылкой
                message = f"""🎁 *Приглашайте друзей и получайте бонусы!*

За каждого приглашенного друга вы получите +2 токена на баланс.
Друг тоже получит +1 токен при регистрации по вашей ссылке.

👇 *Ваша реферальная ссылка:*
{referral_link}

📋 Скопируйте ссылку и отправьте друзьям или поделитесь в соцсетях.

💡 Бонус начисляется автоматически, когда друг перейдет по ссылке и начнет использовать бота."""
                
                self.send_message(
                    user_id=user_id,
                    message=message,
                    keyboard=self.get_main_keyboard(user_id)
                )
                command_handled = True
                return
                
            # Обработка команды возврата в главное меню
            if "в главное меню" in text_lower or text == "🏠 В главное меню":
                self.reset_state(user_id)
                self.send_message(
                    user_id=user_id,
                    message="Вы вернулись в главное меню!",
                    keyboard=self.get_main_keyboard(user_id)
                )
                return
                
            # Обработка навигации по страницам треков
            if text == "⬅️ Назад" or text == "➡️ Вперед":
                # Получаем текущую страницу из состояния
                state_data = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_data(user_id)
                ) or {}
                
                current_page = state_data.get('tracks_page', 1)
                
                # Изменяем страницу в зависимости от нажатой кнопки
                if text == "⬅️ Назад" and current_page > 1:
                    new_page = current_page - 1
                elif text == "➡️ Вперед":
                    new_page = current_page + 1
                else:
                    new_page = current_page
                
                # Сохраняем новую страницу
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, tracks_page=new_page)
                )
                
                # Имитируем нажатие на кнопку "Мои треки" для отображения новой страницы
                self.handle_message(types.SimpleNamespace(
                    user_id=user_id,
                    text="📂 Мои треки",
                    to_me=True
                ))
                return

            # Обработка состояний
            current_state = self.user_states.get(user_id, UserState.START)

            # Получаем состояние из нового менеджера состояний
            vk_state = asyncio.get_event_loop().run_until_complete(
                self.state_manager.get_state(user_id)
            )
            
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
                
                # Генерируем текст песни на основе идеи
                try:
                    from celery_tasks import generate_suno_lyrics_sync
                    
                    # Ограничиваем длину идеи
                    idea = text[:500]
                    
                    # Генерируем текст
                    lyrics = generate_suno_lyrics_sync(idea)
                    
                    if lyrics:
                        # Сохраняем сгенерированный текст
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(user_id, lyrics=lyrics)
                        )
                        
                        # Импортируем клавиатуру для выбора варианта текста
                        from vk_keyboards import get_lyrics_variants_keyboard
                        
                        # Отправляем сгенерированный текст пользователю с клавиатурой выбора варианта
                        self.send_message(
                            user_id=user_id,
                            message=f"✨ Вот текст, который я сочинил для вас:\n\n{lyrics}",
                            keyboard=get_lyrics_variants_keyboard()
                        )
                        
                        # Переводим в состояние выбора варианта текста
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.CHOOSING_LYRICS_VARIANT)
                        )
                    else:
                        # Если не удалось сгенерировать текст
                        self.send_message(
                            user_id=user_id,
                            message="❌ Не удалось сгенерировать текст. Попробуйте другую идею или свой текст.",
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
                
                # Сообщение о том, что текст принят
                # Импортируем клавиатуру для выб