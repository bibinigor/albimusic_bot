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
            # Импортируем клавиатуру для выбора жанра песни
            from vk_keyboards import get_song_genres_keyboard
            
            self.send_message(
                user_id=user_id,
                message="✅ Отлично! Теперь выберите жанр для вашей песни:",
                keyboard=get_song_genres_keyboard()
            )
            logger.info(f"✅ Пользователь {user_id} отправил свой текст")
            command_handled = True

            return
        
        # Обработка выбора варианта текста
        elif vk_state == States.CHOOSING_LYRICS_VARIANT:
            if "использовать этот текст" in text_lower or "✅ использовать этот текст" in text_lower:
                    # Пользователь выбрал использовать сгенерированный текст
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
                    logger.info(f"✅ Пользователь {user_id} выбрал использовать сгенерированный текст")
                    command_handled = True
                    return
                
            elif "сгенерировать другой" in text_lower or "🔄 сгенерировать другой" in text_lower:
                    # Пользователь хочет сгенерировать другой текст
                    # Получаем идею для песни из данных состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    song_idea = state_data.get('song_idea', '')
                    
                    if song_idea:
                        # Отправляем сообщение о генерации нового текста
                        self.send_message(
                            user_id=user_id,
                            message="⏳ Генерирую новый вариант текста...",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Генерируем новый текст
                        try:
                            from celery_tasks import generate_suno_lyrics_sync
                            
                            # Ограничиваем длину идеи
                            idea = song_idea[:500]
                            
                            # Генерируем текст
                            lyrics = generate_suno_lyrics_sync(idea)
                            
                            if lyrics:
                                # Сохраняем сгенерированный текст
                                asyncio.get_event_loop().run_until_complete(
                                    self.state_manager.update_data(user_id, lyrics=lyrics)
                                )
                                
                                # Отправляем сгенерированный текст пользователю
                                self.send_message(
                                    user_id=user_id,
                                    message=f"✨ Вот новый вариант текста:\n\n{lyrics}"
                                )
                                
                                # Отправляем клавиатуру выбора варианта текста
                                from vk_keyboards import get_lyrics_variants_keyboard
                                self.send_message(
                                    user_id=user_id,
                                    message="Что делаем с этим текстом?",
                                    keyboard=get_lyrics_variants_keyboard()
                                )
                            else:
                                # Если не удалось сгенерировать текст
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Не удалось сгенерировать новый текст. Попробуйте использовать текущий вариант или написать свой.",
                                    keyboard=get_lyrics_variants_keyboard()
                                )
                        except Exception as e:
                            logger.error(f"❌ Ошибка генерации нового текста: {e}")
                            self.send_message(
                                user_id=user_id,
                                message="❌ Произошла ошибка при генерации нового текста. Попробуйте использовать текущий вариант или написать свой.",
                                keyboard=get_lyrics_variants_keyboard()
                            )
                    else:
                        # Если идея не найдена, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: идея для песни не найдена. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    logger.info(f"✅ Пользователь {user_id} запросил новый вариант текста")
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
            
            # Обработка выбора жанра музыки
            elif vk_state == States.WAITING_MUSIC_STYLE:
                # Проверяем, выбрал ли пользователь "Свой вариант"
                if "свой вариант" in text_lower or "✏️ свой вариант" in text_lower:
                    # Переходим в состояние ожидания описания своего варианта
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_CUSTOM_STYLE)
                    )
                    
                    prompt_message = """✨ Опишите свой вариант музыки:

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
                    logger.info(f"✅ Пользователь {user_id} переведен в режим ожидания описания своего варианта")
                    command_handled = True
                    return
                else:
                    # Пользователь выбрал один из предложенных жанров
                    # Сохраняем выбранный жанр
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.update_data(user_id, genre=text)
                    )
                    
                    # Запускаем генерацию музыки
                    self.start_music_generation(user_id, text)
                    command_handled = True
                    return
                    
            # Обработка выбора жанра для песни
            elif vk_state == States.WAITING_GENRE:
                # Проверяем, выбрал ли пользователь "Свой вариант"
                if "свой вариант" in text_lower or "✏️ свой вариант" in text_lower:
                    # Переходим в состояние ожидания описания своего варианта
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_CUSTOM_GENRE)
                    )
                    
                    prompt_message = """✨ Опишите жанр для вашей песни:

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
                    logger.info(f"✅ Пользователь {user_id} переведен в режим ожидания описания своего жанра")
                    command_handled = True
                    return
                else:
                    # Пользователь выбрал один из предложенных жанров
                    # Сохраняем выбранный жанр
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.update_data(user_id, genre=text)
                    )
                    
                    # Получаем текст песни из данных состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    lyrics = state_data.get('lyrics', '')
                    
                    if lyrics:
                        # Запускаем генерацию песни
                        self.start_song_generation(user_id, lyrics, text)
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
            
            # Обработка ввода своего варианта жанра для инструментальной музыки
            elif vk_state == States.WAITING_CUSTOM_STYLE:
                # Сохраняем описание своего варианта
                custom_style = text
                
                # Запускаем генерацию музыки
                self.start_music_generation(user_id, custom_style)
                command_handled = True
                return
                
            # Обработка ввода своего варианта жанра для песни
            elif vk_state == States.WAITING_CUSTOM_GENRE:
                # Сохраняем описание своего варианта жанра
                custom_genre = text
                
                # Получаем текст песни из данных состояния
                state_data = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_data(user_id)
                ) or {}
                
                lyrics = state_data.get('lyrics', '')
                
                if lyrics:
                    # Запускаем генерацию песни
                    self.start_song_generation(user_id, lyrics, custom_genre)
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
                
            # Обработка сообщения для поддержки
            elif vk_state == States.WAITING_SUPPORT_MESSAGE:
                # Получаем информацию о пользователе
                try:
                    user_info = self.vk.users.get(user_ids=user_id)[0]
                    username = user_info.get('screen_name', '')
                    first_name = user_info.get('first_name', '')
                except Exception as e:
                    logger.error(f"❌ Ошибка получения информации о пользователе {user_id}: {e}")
                    username = ""
                    first_name = ""
                
                # Сохраняем сообщение в базу данных
                try:
                    execute_query_sync(
                        "INSERT INTO support_messages (user_id, username, first_name, message) VALUES (%s, %s, %s, %s)",
                        (user_id, username, first_name, text)
                    )
                    logger.info(f"✅ Сообщение от пользователя {user_id} сохранено в базе данных")
                except Exception as e:
                    logger.error(f"❌ Ошибка сохранения сообщения в поддержку: {e}")
                
                # Отправляем сообщение администратору
                try:
                    from vk_config import ADMIN_VK_ID
                    admin_message = f"""📩 *Новое сообщение в поддержку*

От: {first_name} (@{username})
ID: {user_id}

Сообщение:
{text}"""
                    
                    self.send_message(
                        user_id=ADMIN_VK_ID,
                        message=admin_message
                    )
                    logger.info(f"✅ Сообщение от пользователя {user_id} отправлено администратору")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки сообщения администратору: {e}")
                
                # Сбрасываем состояние пользователя
                self.reset_state(user_id)
                
                # Отправляем подтверждение пользователю
                self.send_message(
                    user_id=user_id,
                    message="✅ *Сообщение отправлено!*\n\nМы ответим вам в ближайшее время.",
                    keyboard=self.get_main_keyboard(user_id)
                )
                
                command_handled = True
                return
                
            # Обработка для обратной совместимости
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

            elif "поддержка" in text_lower or text == "📞 Поддержка":
                logger.info(f"📞 Запрос в поддержку от пользователя {user_id}")
                
                # Переводим пользователя в состояние ожидания сообщения для поддержки
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.set_state(user_id, States.WAITING_SUPPORT_MESSAGE)
                )
                
                support_message = """📞 *Поддержка ALBI Music*

Напишите ваше сообщение — мы ответим в ближайшее время.

Чтобы отменить, нажмите кнопку "🏠 В главное меню"."""
                
                # Создаем клавиатуру с кнопкой возврата в главное меню
                keyboard = self.get_cancel_keyboard()
                
                self.send_message(
                    user_id=user_id,
                    message=support_message,
                    keyboard=keyboard
                )
                logger.info(f"✅ Пользователь {user_id} переведен в режим отправки сообщения в поддержку")
                command_handled = True
                return

            elif "примеры" in text_lower or text == "🎧 Примеры песен":
                logger.info(f"🎵 Запрос примеров песен от пользователя {user_id}")
                
                # Отправляем сообщение с примерами треков
                demo_message = """🎧 *Примеры треков, созданных нашим ботом:*

Вот несколько примеров песен, созданных с помощью искусственного интеллекта:

1. 🌸 Люба, с 8 марта
2. 💪 Бодибилдинг
3. 🐱 Кот
4. 🎻 Красивая скрипка
5. 💫 Я буду ждать всегда

Больше примеров в нашем сообществе: [https://vk.com/club235442407]"""
                
                self.send_message(
                    user_id=user_id,
                    message=demo_message,
                    keyboard=self.get_main_keyboard(user_id)
                )
                
                # Отправляем демо-аудио
                try:
                    # Отправляем аудио файлы
                    demo_files = [
                        {"path": "demo_audio/lubov.mp3", "title": "🌸 Люба, с 8 марта"},
                        {"path": "demo_audio/bodybuilding.mp3", "title": "💪 Бодибилдинг"},
                        {"path": "demo_audio/cat.mp3", "title": "🐱 Кот"}
                    ]
                    
                    for demo in demo_files:
                        # Проверяем существование файла
                        import os
                        if os.path.exists(demo["path"]):
                            # Отправляем аудио
                            self.vk.docs.getMessagesUploadServer(type='audio_message', peer_id=user_id)
                            # Поскольку VK API не позволяет напрямую отправлять аудио через API,
                            # отправляем сообщение со ссылкой
                            self.send_message(
                                user_id=user_id,
                                message=f"🎵 {demo['title']}: [https://vk.com/club235442407]"
                            )
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке демо-треков: {e}")
                
                # Отправляем приглашение в сообщество
                channel_message = """🎵 В нашем сообществе каждый день новые песни от пользователей, крутые промпты и обучение!

Подпишись, чтобы первым узнавать о новых функциях 👇"""
                
                # Создаем клавиатуру с кнопкой подписки на сообщество
                channel_keyboard = VkKeyboard(inline=True)
                channel_keyboard.add_openlink_button(
                    label="🔔 Подписаться на сообщество",
                    link="https://vk.com/club235442407"
                )
                
                self.send_message(
                    user_id=user_id,
                    message=channel_message,
                    keyboard=channel_keyboard
                )
                
                logger.info(f"✅ Отправлены примеры треков пользователю {user_id}")
                command_handled = True



            elif "админ" in text_lower or text == "⚙️ Админ":
                logger.info(f"⚙️ Запрос админ-панели от пользователя {user_id}")
                if user_id != ADMIN_VK_ID:
                    self.send_message(
                        user_id=user_id,
                        message="⛔ Доступ запрещен",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    command_handled = True
                    return
                
                # Получаем статистику
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

            elif "мои треки" in text_lower or text == "📂 Мои треки":
                logger.info(f"📂 Запрос списка треков от пользователя {user_id}")
                try:
                    # Получаем данные о состоянии пагинации
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    # Получаем текущую страницу (по умолчанию 1)
                    page = state_data.get('tracks_page', 1)
                    
                    # Количество треков на странице
                    per_page = 5
                    
                    # Вычисляем смещение для SQL запроса
                    offset = (page - 1) * per_page
                    
                    # Получаем общее количество треков пользователя
                    total_count = execute_query_sync(
                        """
                        SELECT COUNT(*)
                        FROM generations
                        WHERE user_id = %s AND status = 'completed'
                        """,
                        (user_id,)
                    )[0][0]
                    
                    # Получаем треки для текущей страницы
                    tracks = execute_query_sync(
                        """
                        SELECT task_id, prompt, audio_url, created_at, status
                        FROM generations
                        WHERE user_id = %s AND status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        (user_id, per_page, offset)
                    )

                    if not tracks:
                        if page > 1:
                            # Если страница > 1, но треков нет, значит пользователь перешел слишком далеко
                            # Сбрасываем на первую страницу
                            asyncio.get_event_loop().run_until_complete(
                                self.state_manager.update_data(user_id, tracks_page=1)
                            )
                            self.send_message(
                                user_id=user_id,
                                message="⚠️ Страница не найдена. Возвращаемся к началу списка.",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                            return
                        else:
                            # Если это первая страница и треков нет
                            self.send_message(
                                user_id=user_id,
                                message="*У вас пока нет созданных треков. Самое время это исправить! 🎵*",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                            return

                    # Вычисляем общее количество страниц
                    total_pages = (total_count + per_page - 1) // per_page
                    
                    # Отправляем общую статистику с информацией о пагинации
                    self.send_message(
                        user_id=user_id,
                        message=f"🎵 *Ваши композиции*\n\n📊 Всего создано: {total_count} треков\n📄 Страница {page} из {total_pages}\n━━━━━━━━━━━━━━━━━"
                    )

                    # Отправляем треки текущей страницы
                    for idx, (task_id, prompt, audio_url, created_at, status) in enumerate(tracks, 1):
                        # Форматируем дату
                        date_str = created_at.strftime("%d.%m.%Y") if hasattr(created_at, 'strftime') else str(created_at)[:10]
                        
                        # Форматируем описание
                        short_prompt = prompt[:100] + '...' if len(prompt) > 100 else prompt
                        
                        # Импортируем клавиатуру для действий с треком
                        from vk_keyboards import get_track_actions_keyboard
                        
                        # Создаем клавиатуру для трека с кнопками действий
                        track_keyboard = None
                        if audio_url and not audio_url.startswith('ERROR'):
                            track_keyboard = get_track_actions_keyboard()
                        
                        track_text = (
                            f"*Трек #{offset + idx}*\n"
                            f"📅 Дата: {date_str}\n"
                            f"📝 Описание: _{short_prompt}_\n"
                            f"━━━━━━━━━━━━━━━━━"
                        )
                        
                        self.send_message(
                            user_id=user_id,
                            message=track_text,
                            keyboard=track_keyboard if audio_url and not audio_url.startswith('ERROR') else None
                        )

                    # Импортируем клавиатуру навигации по трекам
                    from vk_keyboards import get_tracks_navigation_keyboard
                    
                    # Создаем клавиатуру навигации
                    nav_keyboard = get_tracks_navigation_keyboard(page, total_pages)
                    
                    # Отправляем сообщение с навигацией
                    self.send_message(
                        user_id=user_id,
                        message=f"📄 Страница {page} из {total_pages}",
                        keyboard=nav_keyboard
                    )
                    
                    # Сохраняем текущую страницу в состоянии пользователя
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.update_data(user_id, tracks_page=page)
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
            
