 %s AND balance > 0",
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