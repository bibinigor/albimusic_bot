# 🔴 БЛОК 1: ИСПРАВЛЕННЫЙ КОД ДЛЯ ИНСТРУМЕНТАЛЬНОЙ МУЗЫКИ
# Заменить блок обработки States.WAITING_MUSIC_STYLE (строки 1338-1446)

# Обработка выбора жанра для инструментальной музыки
elif vk_state == States.WAITING_MUSIC_STYLE:
    import uuid
    
    genre = text  # Выбранный жанр
    logger.info(f"🎶 Пользователь {user_id} выбрал жанр для инструментала: {genre}")
    
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
            logger.warning(f"⚠️ Попытка генерации музыки при нулевом балансе: {user_id}")
            command_handled = True
            return
    except Exception as e:
        logger.error(f"❌ Ошибка проверки баlanса: {e}")
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
    
    # ✅ ИСПРАВЛЕНИЕ #4: Создаем запись в БД со статусом 'pending' ДО генерации
    try:
        execute_query_sync(
            '''INSERT INTO generations 
               (user_id, task_id, prompt, audio_url, is_free, custom_mode, status, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())''',
            (user_id, task_id, genre, None, False, False, 'pending')
        )
        logger.info(f"✅ Создана запись в БД для task_id={task_id} (музыка) со статусом 'pending'")
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
    
    # Отправляем сообщение о начале генерации
    self.send_message(
        user_id=user_id,
        message="🎵 Генерация началась! Это займет 3-5 минут. Результат пришлю сюда в чат"
    )
    
    # Пробуем отправить GIF
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        import os
        if os.path.exists(gif_path):
            from vk_api.upload import VkUpload
            upload = VkUpload(self.vk_session)
            doc = upload.document_message(gif_path, peer_id=user_id)
            attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
            try:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    attachment=attachment
                )
            except Exception as gif_err:
                logger.warning(f"⚠️ Не удалось отправить GIF: {gif_err}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка GIF при генерации музыки: {e}")
    
    # Логируем параметры генерации
    logger.info(f"🎶 Запуск генерации инструментальной музыки для пользователя {user_id}")
    logger.info(f"🎶 Task ID: {task_id}")
    logger.info(f"🎶 Жанр: {genre}")
    
    # Запускаем генерацию в отдельном потоке
    import threading
    
    # Копируем переменные для потока
    _genre = genre
    _uid = user_id
    _task_id = task_id
    
    def generate_instrumental_thread():
        try:
            from celery_tasks import generate_suno_music_sync
            
            audio_url = generate_suno_music_sync(_genre)
            
            if audio_url:
                # ✅ ИСПРАВЛЕНИЕ #5: Обновляем существующую запись в БД (НЕ создаем новую)
                try:
                    execute_query_sync(
                        '''UPDATE generations 
                           SET audio_url = %s, status = %s 
                           WHERE task_id = %s''',
                        (audio_url, 'completed', _task_id)
                    )
                    logger.info(f"✅ Обновлена запись в БД для task_id={_task_id} (музыка) со статусом 'completed'")
                except Exception as db_err:
                    logger.error(f"❌ Ошибка обновления музыки в БД: {db_err}")
                
                # Парсим URL: может быть JSON-массив из 2 ссылок
                try:
                    import json as _json
                    urls = _json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                except Exception:
                    urls = [audio_url]
                
                if len(urls) >= 2:
                    result_msg = (
                        f"✅ Ваша инструментальная музыка готова!\n\n"
                        f"🎵 Жанр: {_genre}\n\n"
                        f"🎧 Вариант 1:\n{urls[0]}\n\n"
                        f"🎧 Вариант 2:\n{urls[1]}"
                    )
                else:
                    result_msg = (
                        f"✅ Ваша инструментальная музыка готова!\n\n"
                        f"🎵 Жанр: {_genre}\n\n"
                        f"🔗 Слушать: {urls[0]}"
                    )
                
                self.send_message(
                    user_id=_uid,
                    message=result_msg,
                    keyboard=self.get_main_keyboard(_uid)
                )
                
                logger.info(f"✅ Музыка успешно сгенерирована для пользователя {_uid} (task_id={_task_id})")
            else:
                # Если не удалось сгенерировать музыку
                # ✅ ИСПРАВЛЕНИЕ #6: Возвращаем токен при ошибке
                try:
                    execute_query_sync(
                        "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                        (_uid,)
                    )
                    execute_query_sync(
                        "UPDATE generations SET status = %s WHERE task_id = %s",
                        ('failed', _task_id)
                    )
                    logger.info(f"🔄 Возвращен 1 токен пользователю {_uid} из-за ошибки генерации музыки")
                except Exception as refund_error:
                    logger.error(f"❌ Ошибка возврата токена: {refund_error}")
                
                self.send_message(
                    user_id=_uid,
                    message="❌ Не удалось сгенерировать музыку. Токен возвращен на баланс. Попробуйте другой жанр или позже.",
                    keyboard=self.get_main_keyboard(_uid)
                )
        except Exception as e:
            logger.error(f"❌ Ошибка в потоке генерации музыки: {e}")
            logger.error(traceback.format_exc())
            
            # ✅ ИСПРАВЛЕНИЕ #7: Возвращаем токен при исключении
            try:
                execute_query_sync(
                    "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                    (_uid,)
                )
                execute_query_sync(
                    "UPDATE generations SET status = %s WHERE task_id = %s",
                    ('failed', _task_id)
                )
                logger.info(f"🔄 Возвращен 1 токен пользователю {_uid} из-за исключения")
            except Exception as refund_error:
                logger.error(f"❌ Ошибка возврата токена: {refund_error}")
            
            self.send_message(
                user_id=_uid,
                message="❌ Произошла ошибка при генерации музыки. Токен возвращен на баланс. Попробуйте позже.",
                keyboard=self.get_main_keyboard(_uid)
            )
    
    # Запускаем генерацию в отдельном потоке
    music_thread = threading.Thread(target=generate_instrumental_thread, daemon=True)
    music_thread.start()
    
    # Сбрасываем состояние пользователя
    self.reset_state(user_id)
    
    logger.info(f"✅ Пользователь {user_id} запустил генерацию музыки (жанр: {genre})")
    command_handled = True
    return
