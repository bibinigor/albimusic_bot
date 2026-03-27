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
        
        # Обработка выбора жанра для песни
        elif vk_state == States.WAITING_GENRE:
            # Получаем текст песни из данных состояния
            state_data = asyncio.get_event_loop().run_until_complete(
                self.state_manager.get_data(user_id)
            ) or {}
            
            lyrics = state_data.get('lyrics', '')
            
            if not lyrics:
                # Если текст не найден, сообщаем об ошибке
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка: текст песни не найден. Попробуйте начать сначала.",
                    keyboard=self.get_main_keyboard(user_id)
                )
                self.reset_state(user_id)
                command_handled = True
                return
            
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
        
        # Обработка выбора пола вокалиста
        elif vk_state == States.WAITING_VOCAL_GENDER:
            # Получаем данные состояния
            state_data = asyncio.get_event_loop().run_until_complete(
                self.state_manager.get_data(user_id)
            ) or {}
            
            lyrics = state_data.get('lyrics', '')
            genre = state_data.get('genre', '')
            
            if not lyrics or not genre:
                # Если данные не найдены, сообщаем об ошибке
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка: данные для генерации песни не найдены. Попробуйте начать сначала.",
                    keyboard=self.get_main_keyboard(user_id)
                )
                self.reset_state(user_id)
                command_handled = True
                return
            
            # Определяем пол вокалиста
            vocal_gender = "male"
            if "женский" in text_lower or "female" in text_lower:
                vocal_gender = "female"
            
            # Сохраняем выбранный пол вокалиста
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.update_data(user_id, vocal_gender=vocal_gender)
            )
            
            # Отправляем сообщение о начале генерации
            self.send_message(
                user_id=user_id,
                message=f"""🎵 **НАЧИНАЕМ СОЗДАНИЕ ПЕСНИ!**

📝 Текст: {len(lyrics)} символов
🎸 Жанр: {genre}
🎤 Вокал: {text}

⏳ Генерация займет 1-2 минуты...
Я пришлю вам песню, как только она будет готова!""",
                keyboard=self.get_main_keyboard(user_id)
            )
            
            # Запускаем генерацию песни
            try:
                # Списываем генерацию (кроме админа)
                from vk_config import ADMIN_VK_ID
                if user_id != ADMIN_VK_ID:
                    execute_query_sync(
                        "UPDATE users SET balance = balance - 1 WHERE user_id = %s AND balance > 0",
                        (user_id,)
                    )
                
                # Запускаем задачу генерации песни
                from celery_tasks import generate_suno_song
                
                # Создаем задачу генерации песни
                task = generate_suno_song.delay(
                    user_id=user_id,
                    lyrics=lyrics,
                    genre=genre,
                    vocal_gender=vocal_gender
                )
                
                # Сохраняем ID задачи
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, task_id=task.id)
                )
                
                logger.info(f"✅ Запущена генерация песни для {user_id}: task_id={task.id}")
            except Exception as e:
                logger.error(f"❌ Ошибка запуска генерации песни: {e}")
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при запуске генерации песни. Попробуйте позже.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            
            # Сбрасываем состояние
            self.reset_state(user_id)
            
            logger.info(f"✅ Пользователь {user_id} выбрал пол вокалиста: {text}")
            command_handled = True
            return
        
        # Обработка выбора жанра для инструментальной музыки
        elif vk_state == States.WAITING_MUSIC_STYLE:
            # Запускаем генерацию инструментальной музыки
            self.start_music_generation(user_id, text)
            
            # Сбрасываем состояние
            self.reset_state(user_id)
            
            logger.info(f"✅ Пользователь {user_id} выбрал жанр инструментальной музыки: {text}")
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