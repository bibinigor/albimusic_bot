# 🔴 БЛОК 3: Выбор версии v1/v2 для минусовки/кавера/WAV
# Добавить в main_vk.py

# ==================== ЧАСТЬ 1: Функция ask_version() ====================
# Добавить как метод класса VKBot

def ask_version(self, user_id, task_id, action_type):
    """
    Запросить выбор версии у пользователя (v1 или v2)
    
    Args:
        user_id: ID пользователя VK
        task_id: ID трека
        action_type: Тип действия ('karaoke', 'cover', 'wav')
    """
    import json
    from vk_api.keyboard import VkKeyboard, VkKeyboardColor
    
    # Получаем информацию о треке из БД
    try:
        track_info = execute_query_sync(
            "SELECT audio_url FROM generations WHERE task_id = %s AND user_id = %s",
            (task_id, user_id)
        )
        
        if not track_info or not track_info[0][0]:
            self.send_message(
                user_id=user_id,
                message="❌ Трек не найден. Сначала создайте песню.",
                keyboard=self.get_main_keyboard(user_id)
            )
            return
        
        audio_url = track_info[0][0]
        
        # Проверяем, есть ли 2 варианта
        try:
            urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
        except Exception:
            urls = [audio_url]
        
        if len(urls) < 2:
            # Если только 1 вариант, сразу выполняем действие
            logger.info(f"ℹ️ Только 1 вариант для task_id={task_id}, пропускаем выбор версии")
            self._process_action_with_version(user_id, task_id, action_type, version=1)
            return
        
        # Создаем клавиатуру выбора версии
        keyboard = VkKeyboard(inline=True)
        
        # Заголовок зависит от типа действия
        action_names = {
            'karaoke': '🎤 минусовки',
            'cover': '🎸 кавера',
            'wav': '🎵 конвертации в WAV'
        }
        action_name = action_names.get(action_type, 'действия')
        
        # Кнопки выбора версии
        keyboard.add_callback_button(
            '🎵 Вариант 1',
            color=VkKeyboardColor.PRIMARY,
            payload=json.dumps({
                "action": f"{action_type}_version",
                "task_id": str(task_id),
                "version": 1
            })
        )
        keyboard.add_line()
        keyboard.add_callback_button(
            '🎵 Вариант 2',
            color=VkKeyboardColor.PRIMARY,
            payload=json.dumps({
                "action": f"{action_type}_version",
                "task_id": str(task_id),
                "version": 2
            })
        )
        keyboard.add_line()
        keyboard.add_callback_button(
            '❌ Отмена',
            color=VkKeyboardColor.NEGATIVE,
            payload=json.dumps({"action": "cancel"})
        )
        
        # Отправляем сообщение
        message_text = f"Выберите вариант для {action_name}:\n\n"
        message_text += f"🎧 Вариант 1:\n{urls[0]}\n\n"
        message_text += f"🎧 Вариант 2:\n{urls[1]}"
        
        self.send_message(
            user_id=user_id,
            message=message_text,
            keyboard=keyboard
        )
        
        logger.info(f"✅ Отправлен запрос на выбор версии для {action_type}, task_id={task_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка ask_version: {e}")
        import traceback
        traceback.print_exc()
        self.send_message(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )


def _process_action_with_version(self, user_id, task_id, action_type, version):
    """
    Выполнить действие с указанной версией
    
    Args:
        user_id: ID пользователя
        task_id: ID трека
        action_type: Тип действия ('karaoke', 'cover', 'wav')
        version: Номер версии (1 или 2)
    """
    logger.info(f"🎵 Выполнение {action_type} для task_id={task_id}, version={version}")
    
    # В зависимости от действия вызываем соответствующий обработчик
    if action_type == 'karaoke':
        self._process_karaoke_with_version(user_id, task_id, version)
    elif action_type == 'cover':
        # Для кавера нужен еще выбор жанра
        # Сохраняем version в state и показываем выбор жанра
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.update_data(
                user_id,
                cover_task_id=task_id,
                cover_version=version
            )
        )
        from vk_keyboards import get_cover_genre_keyboard
        self.send_message(
            user_id=user_id,
            message="🎸 Выберите жанр для кавера:",
            keyboard=get_cover_genre_keyboard(task_id)
        )
    elif action_type == 'wav':
        self._process_wav_with_version(user_id, task_id, version)


# ==================== ЧАСТЬ 2: Обновление karaoke handler ====================
# Заменить блок обработки action == "karaoke" в handle_callback()

elif action == "karaoke":
    task_id_for_karaoke = payload.get('task_id', '')
    logger.info(f"🎤 Запрос на создание минусовки от пользователя {user_id}, task_id={task_id_for_karaoke}")
    
    # ✅ БЛОК 3: Показываем выбор версии
    self.ask_version(user_id, task_id_for_karaoke, 'karaoke')

# Добавить новый handler для karaoke_version
elif action == "karaoke_version":
    task_id_for_karaoke = payload.get('task_id', '')
    version = payload.get('version', 1)
    logger.info(f"🎤 Выбрана версия {version} для минусовки, task_id={task_id_for_karaoke}")
    
    # Проверяем баланс
    try:
        result = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        if result and result[0][0] > 0:
            # Отправляем сообщение о начале генерации минусовки
            self.send_message(
                user_id=user_id,
                message=f"⏳ Генерирую минусовку (вариант {version}), подождите 1-2 минуты...",
                keyboard=self.get_cancel_keyboard()
            )
            
            # Запускаем генерацию минусовки в отдельном потоке
            import threading
            def generate_karaoke_thread():
                try:
                    from celery_tasks import generate_suno_karaoke_sync
                    
                    # Получаем информацию о песне из базы данных
                    song_info = execute_query_sync(
                        "SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                        (task_id_for_karaoke, user_id)
                    )
                    
                    if song_info and song_info[0][0] and song_info[0][1]:
                        audio_url = song_info[0][0]
                        suno_id = song_info[0][1]
                        
                        # ✅ БЛОК 3: Выбираем нужную версию
                        try:
                            import json
                            urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                            # Берем нужную версию (индекс = version - 1)
                            selected_url = urls[version - 1] if version <= len(urls) else urls[0]
                        except Exception:
                            selected_url = audio_url
                        
                        # Генерируем минусовку
                        karaoke_url = generate_suno_karaoke_sync(suno_id)
                        
                        if karaoke_url:
                            # Сохраняем результат в базу данных
                            execute_query_sync(
                                'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                                (user_id, f"Минусовка v{version} для {suno_id}", karaoke_url, False, False)
                            )
                            
                            # Отправляем результат пользователю
                            self.send_message(
                                user_id=user_id,
                                message=f"✅ Минусовка (вариант {version}) готова!\n\nСсылка: {karaoke_url}",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                            
                            # Списываем баланс
                            execute_query_sync(
                                "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                (user_id,)
                            )
                            logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")
                        else:
                            # Если не удалось сгенерировать минусовку
                            self.send_message(
                                user_id=user_id,
                                message="❌ Не удалось сгенерировать минусовку. Попробуйте позже.",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                    else:
                        # Если не найдена информация о песне
                        self.send_message(
                            user_id=user_id,
                            message="❌ Не найдена информация о песне. Сначала создайте песню.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации минусовки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при генерации минусовки. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Запускаем генерацию в отдельном потоке
            thread = threading.Thread(target=generate_karaoke_thread)
            thread.start()
        else:
            self.send_message(
                user_id=user_id,
                message="❌ У вас недостаточно токенов. Пополните баланс!",
                keyboard=self.get_main_keyboard(user_id)
            )
            logger.warning(f"⚠️ Попытка создания минусовки при нулевом балансе: {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке баланса для создания минусовки: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )


# ==================== ЧАСТЬ 3: Обновление WAV handler ====================
# Заменить блок обработки action == "wav" в handle_callback()

elif action == "wav":
    task_id_for_wav = payload.get('task_id', '')
    logger.info(f"🎵 Запрос на конвертацию в WAV от пользователя {user_id}, task_id={task_id_for_wav}")
    
    # ✅ БЛОК 3: Показываем выбор версии
    self.ask_version(user_id, task_id_for_wav, 'wav')

# Добавить новый handler для wav_version
elif action == "wav_version":
    task_id_for_wav = payload.get('task_id', '')
    version = payload.get('version', 1)
    logger.info(f"🎵 Выбрана версия {version} для WAV, task_id={task_id_for_wav}")
    
    # Проверяем баланс (WAV стоит 2 токена)
    try:
        result = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        if result and result[0][0] >= 2:
            # Отправляем сообщение о начале конвертации
            self.send_message(
                user_id=user_id,
                message=f"⏳ Конвертирую в WAV (вариант {version}), подождите 1-2 минуты...",
                keyboard=self.get_cancel_keyboard()
            )
            
            # Запускаем конвертацию в отдельном потоке
            import threading
            def convert_to_wav_thread():
                try:
                    from celery_tasks import generate_suno_wav_sync
                    
                    # Получаем информацию о песне из базы данных
                    song_info = execute_query_sync(
                        "SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                        (task_id_for_wav, user_id)
                    )
                    
                    if song_info and song_info[0][0] and song_info[0][1]:
                        suno_id = song_info[0][1]
                        
                        # Конвертируем в WAV
                        wav_url = generate_suno_wav_sync(suno_id)
                        
                        if wav_url:
                            # Сохраняем результат в базу данных
                            execute_query_sync(
                                'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                                (user_id, f"WAV v{version} для {suno_id}", wav_url, False, False)
                            )
                            
                            # Отправляем результат пользователю
                            self.send_message(
                                user_id=user_id,
                                message=f"✅ WAV файл (вариант {version}) готов!\n\nСсылка: {wav_url}\n\n⚠️ Файл доступен 24 часа",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                            
                            # Списываем баланс (2 токена)
                            execute_query_sync(
                                "UPDATE users SET balance = balance - 2 WHERE user_id = %s",
                                (user_id,)
                            )
                            logger.info(f"💰 Списано 2 токена с баланса пользователя {user_id}")
                        else:
                            # Если не удалось сконвертировать в WAV
                            self.send_message(
                                user_id=user_id,
                                message="❌ Не удалось сконвертировать в WAV. Попробуйте позже.",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                    else:
                        # Если не найдена информация о песне
                        self.send_message(
                            user_id=user_id,
                            message="❌ Не найдена информация о песне. Сначала создайте песню.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка конвертации в WAV: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при конвертации в WAV. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Запускаем конвертацию в отдельном потоке
            thread = threading.Thread(target=convert_to_wav_thread)
            thread.start()
        else:
            self.send_message(
                user_id=user_id,
                message="❌ Для конвертации в WAV нужно 2 токена. Пополните баланс!",
                keyboard=self.get_main_keyboard(user_id)
            )
            logger.warning(f"⚠️ Попытка конвертации в WAV при недостаточном балансе: {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке баланса для конвертации в WAV: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )


# ==================== ЧАСТЬ 4: Обновление cover handler (уже есть выбор жанра) ====================
# Для кавера выбор версии уже реализован через ask_version() → сохранение в state → выбор жанра
# Код выше в _process_action_with_version() уже обрабатывает этот случай

# ==================== КОНЕЦ БЛОКА 3 ====================
