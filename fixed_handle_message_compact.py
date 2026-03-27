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

            # Получаем состояние из нового менеджера состояний
            vk_state = asyncio.get_event_loop().run_until_complete(
                self.state_manager.get_state(user_id)
            )
            
            # Обработка выбора варианта текста
            if vk_state == States.CHOOSING_LYRICS_VARIANT:
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
                    # Обработка запроса на генерацию нового текста
                    # ...
                    command_handled = True
                    return
                
                elif "написать свой текст" in text_lower or "✍️ написать свой текст" in text_lower:
                    # Обработка выбора написать свой текст
                    # ...
                    command_handled = True
                    return
            
            # Обработка выбора жанра музыки
            elif vk_state == States.WAITING_MUSIC_STYLE:
                # Проверяем, выбрал ли пользователь "Свой вариант"
                if "свой вариант" in text_lower or "✏️ свой вариант" in text_lower:
                    # Переходим в состояние ожидания описания своего варианта
                    # ...
                    command_handled = True
                    return
                else:
                    # Пользователь выбрал один из предложенных жанров
                    # ...
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