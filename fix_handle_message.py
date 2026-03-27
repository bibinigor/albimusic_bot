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
        
        # Обработка payload от кнопок
        if payload and isinstance(payload, dict):
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
        
        # 1. Сначала проверяем системные команды
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
        
        # 2. Затем проверяем СОСТОЯНИЯ пользователя
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
                return
            else:
                # Пользователь выбрал один из предложенных жанров
                # Сохраняем выбранный жанр
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, genre=text)
                )
                
                # Запускаем генерацию музыки
                self.start_music_generation(user_id, text)
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
                
                return
        
        # Обработка ввода своего варианта жанра для инструментальной музыки
        elif vk_state == States.WAITING_CUSTOM_STYLE:
            # Сохраняем описание своего варианта
            custom_style = text
            
            # Запускаем генерацию музыки
            self.start_music_generation(user_id, custom_style)
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
            
            return
            
        # Обработка для обратной совместимости
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
        
        # 3. Затем проверяем нажатия на кнопки главного меню
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
                    return
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
            return

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
                        self.state_manager.set_state(user_id, States.
