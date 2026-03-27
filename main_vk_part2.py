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
                    elif action == "select_variant_1":
                        text = "Выбрать 1 вариант"
                        text_lower = text.lower()
                    elif action == "select_variant_2":
                        text = "Выбрать 2 вариант"
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
                        from vk_keyboards import get_lyrics_variants_keyboard_with_two_options
                        
                        # Отправляем клавиатуру выбора варианта текста
                        self.send_message(
                            user_id=user_id,
                            message="Выберите вариант текста или напишите свой:",
                            keyboard=get_lyrics_variants_keyboard_with_two_options()
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