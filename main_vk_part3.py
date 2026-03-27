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
                if "выбрать 1 вариант" in text_lower or text == "Выбрать 1 вариант":
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
                
                elif "выбрать 2 вариант" in text_lower or text == "Выбрать 2 вариант":
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
        """Запуск бота и прослушивание событий"""
        logger.info("🎧 Начинаю прослушивание событий...")
        
        # Запускаем прослушивание событий
        for event in self.longpoll.listen():
            # Обрабатываем только новые сообщения
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                # Обрабатываем сообщение
                self.handle_message(event)


if __name__ == '__main__':
    # Создаем экземпляр бота
    bot = VKBot()
    
    # Запускаем бота
    try:
        logger.info("🚀 Запуск VK бота...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")