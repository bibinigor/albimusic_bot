# 🔴 БЛОК 1: ИСПРАВЛЕННЫЙ КОД ДЛЯ main_vk.py
# Заменить блок обработки States.WAITING_VOCAL_GENDER (строки 1163-1335)

# Обработка выбора пола вокалиста
elif vk_state == States.WAITING_VOCAL_GENDER:
    import uuid
    
    # Сохраняем выбранный пол вокалиста
    vocal_gender = "male"
    if "женский" in text_lower or text == "👩 Женский":
        vocal_gender = "female"
    
    asyncio.get_event_loop().run_until_complete(
        self.state_manager.update_data(user_id, vocal_gender=vocal_gender)
    )
    
    # Получаем данные пользователя
    state_data = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_data(user_id)
    ) or {}
    
    # Получаем текст песни и жанр
    lyrics = state_data.get('lyrics', '')
    genre = state_data.get('genre', '')
    
    # ✅ ИСПРАВЛЕНИЕ #1: Проверяем баланс ДО всех операций
    try:
        balance_result = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        current_balance = balance_result[0][0] if balance_result else 0
        
        if current_balance <= 0:
            self.send_message(
                user_id=user_id,
                message="❌ Недостаточно токенов для генерации. Пополните баланс!",
                keyboard=self.get_main_keyboard(user_id)
            )
            self.reset_state(user_id)
            logger.warning(f"⚠️ Попытка генерации при нулевом балансе: {user_id}")
            command_handled = True
            return
    except Exception as e:
        logger.error(f"❌ Ошибка проверки баланса: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Ошибка при проверке баланса. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )
        self.reset_state(user_id)
        command_handled = True
        return
    
    # ✅ ИСПРАВЛЕНИЕ #2: Создаем task_id ДО генерации
    task_id = str(uuid.uuid4())
    
    # ✅ ИСПРАВЛЕНИЕ #3: Списываем баланс ДО генерации
    try:
        execute_query_sync(
            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
            (user_id,)
        )
        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id} (task_id={task_id})")
    except Exception as e:
        logger.error(f"❌ Ошибка списания баланса: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Ошибка при списании баланса. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )
        self.reset_state(user_id)
        command_handled = True
        return
    
    # Формируем стиль с учетом пола вокалиста
    style = f"{genre}, {vocal_gender} vocals"
    
    # Проверяем длину текста песни и автоматически включаем customMode для длинных текстов
    use_custom_mode = len(lyrics) > 500
    if use_custom_mode:
        logger.info(f"ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")
    
    # ✅ ИСПРАВЛЕНИЕ #4: Создаем запись в БД со статусом 'pending' ДО генерации
    try:
        execute_query_sync(
            '''INSERT INTO generations 
               (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_audio_id, status, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())''',
            (user_id, task_id, style, None, False, use_custom_mode, None, 'pending')
        )
        logger.info(f"✅ Создана запись в БД для task_id={task_id} со статусом 'pending'")
    except Exception as e:
        logger.error(f"❌ Ошибка создания записи в БД: {e}")
        # Возвращаем токен обратно
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
            logger.info(f"🔄 Возвращен 1 токен пользователю {user_id} из-за ошибки")
        except Exception:
            pass
        self.send_message(
            user_id=user_id,
            message="❌ Ошибка при создании задачи. Токен возвращен на баланс.",
            keyboard=self.get_main_keyboard(user_id)
        )
        self.reset_state(user_id)
        command_handled = True
        return
    
    # Отправляем GIF-анимацию и сообщение о начале генерации
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        # Проверяем, существует ли файл
        import os
        if os.path.exists(gif_path):
            # Отправляем GIF
            from vk_api.upload import VkUpload
            upload = VkUpload(self.vk_session)
            doc = upload.document_message(gif_path, peer_id=user_id)
            attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
            
            self.send_message(
                user_id=user_id,
                message="🎵 Генерация началась!\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                keyboard=self.get_cancel_keyboard()
            )
            
            # Отправляем GIF как документ с обработкой ошибок
            try:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    attachment=attachment
                )
            except Exception as gif_error:
                logger.warning(f"⚠️ Не удалось отправить GIF: {gif_error}")
        else:
            # Если GIF не найден, просто отправляем сообщение
            self.send_message(
                user_id=user_id,
                message="🎵 Генерация началась!\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                keyboard=self.get_cancel_keyboard()
            )
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке GIF: {e}")
        # Если произошла ошибка, просто отправляем сообщение
        self.send_message(
            user_id=user_id,
            message="🎵 Генерация началась!\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
            keyboard=self.get_cancel_keyboard()
        )
    
    # Логируем параметры генерации
    logger.info(f"🎵 Запуск генерации песни для пользователя {user_id}")
    logger.info(f"🎵 Task ID: {task_id}")
    logger.info(f"🎵 Текст: {lyrics[:100]}...")
    logger.info(f"🎵 Стиль: {style}")
    logger.info(f"🎵 Custom Mode: {use_custom_mode}")
    
    # Запускаем генерацию в отдельном потоке, чтобы не блокировать бота
    import threading
    
    # Копируем переменные для потока
    _user_id = user_id
    _task_id = task_id
    _lyrics = lyrics
    _style = style
    _use_custom_mode = use_custom_mode
    _genre = genre
    
    def generate_song_thread():
        try:
            # Импортируем функцию для генерации песни
            from celery_tasks import generate_suno_song_sync
            
            # Генерируем песню
            result = generate_suno_song_sync(_lyrics, _style)
            
            if result:
                audio_url, suno_task_id, audio_id = result
                
                # ✅ ИСПРАВЛЕНИЕ #5: Обновляем существующую запись в БД (НЕ создаем новую)
                execute_query_sync(
                    '''UPDATE generations 
                       SET audio_url = %s, suno_audio_id = %s, status = %s 
                       WHERE task_id = %s''',
                    (audio_url, audio_id, 'completed', _task_id)
                )
                logger.info(f"✅ Обновлена запись в БД для task_id={_task_id} со статусом 'completed'")
                
                # Импортируем клавиатуру с опциями
                from vk_keyboards import get_song_options_keyboard
                
                # Подготовка сообщения с результатом
                message_text = f"✅ Ваша песня готова!\n\nЖанр: {_genre}\n\n"
                
                # Проверяем, содержит ли audio_url несколько ссылок (JSON массив)
                try:
                    import json
                    audio_urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                    
                    # Если есть несколько ссылок, добавляем их все в сообщение
                    if len(audio_urls) > 1:
                        message_text += "🎵 Варианты песни:\n\n"
                        for i, url in enumerate(audio_urls, 1):
                            message_text += f"Вариант {i}: {url}\n\n"
                    else:
                        message_text += f"Ссылка: {audio_url}\n\n"
                except Exception as json_error:
                    # Если не удалось распарсить JSON, логируем ошибку и используем строку как есть
                    logger.error(f"❌ Ошибка при парсинге JSON аудио URL: {json_error}")
                    message_text += f"Ссылка: {audio_url}\n\n"
                
                # Добавляем информацию о возможных действиях
                message_text += "💎 Что можно сделать с этой песней:\n\n"
                message_text += "🎤 Минусовка (1 токен) — версия без вокала\n"
                message_text += "🎸 Кавер (1 токен) — перепой в другом жанре\n"
                message_text += "🎵 В WAV (2 токена) — формат для профи\n"
                message_text += "🔗 Поделиться — опубликуй на своей странице"
                
                # Отправляем результат пользователю с клавиатурой опций
                self.send_message(
                    user_id=_user_id,
                    message=message_text,
                    keyboard=get_song_options_keyboard(_task_id)
                )
                
                logger.info(f"✅ Песня успешно сгенерирована для пользователя {_user_id} (task_id={_task_id})")
            else:
                # Если не удалось сгенерировать песню
                # ✅ ИСПРАВЛЕНИЕ #6: Возвращаем токен при ошибке
                try:
                    execute_query_sync(
                        "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                        (_user_id,)
                    )
                    execute_query_sync(
                        "UPDATE generations SET status = %s WHERE task_id = %s",
                        ('failed', _task_id)
                    )
                    logger.info(f"🔄 Возвращен 1 токен пользователю {_user_id} из-за ошибки генерации")
                except Exception as refund_error:
                    logger.error(f"❌ Ошибка возврата токена: {refund_error}")
                
                self.send_message(
                    user_id=_user_id,
                    message="❌ Не удалось сгенерировать песню. Токен возвращен на баланс. Попробуйте другой жанр или позже.",
                    keyboard=self.get_main_keyboard(_user_id)
                )
        except Exception as e:
            logger.error(f"❌ Ошибка генерации песни: {e}")
            logger.error(traceback.format_exc())
            
            # ✅ ИСПРАВЛЕНИЕ #7: Возвращаем токен при исключении
            try:
                execute_query_sync(
                    "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                    (_user_id,)
                )
                execute_query_sync(
                    "UPDATE generations SET status = %s WHERE task_id = %s",
                    ('failed', _task_id)
                )
                logger.info(f"🔄 Возвращен 1 токен пользователю {_user_id} из-за исключения")
            except Exception as refund_error:
                logger.error(f"❌ Ошибка возврата токена: {refund_error}")
            
            self.send_message(
                user_id=_user_id,
                message="❌ Произошла ошибка при генерации песни. Токен возвращен на баланс. Попробуйте позже.",
                keyboard=self.get_main_keyboard(_user_id)
            )
    
    # Запускаем генерацию в отдельном потоке
    thread = threading.Thread(target=generate_song_thread, daemon=True)
    thread.start()
    
    # Сбрасываем состояние пользователя
    self.reset_state(user_id)
    
    logger.info(f"✅ Пользователь {user_id} выбрал пол вокалиста: {vocal_gender}. Генерация запущена.")
    command_handled = True
    return
