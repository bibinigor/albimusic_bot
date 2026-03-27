# 🔴 БЛОК 2: Интеграция демо-системы в main_vk.py
# Этот код добавляется в несколько мест main_vk.py

# ==================== ЧАСТЬ 1: Импорты (добавить в начало файла) ====================

from vk_demo_system import (
    create_demo_track,
    unlock_demo_track,
    get_demo_track_info,
    is_track_unlocked
)


# ==================== ЧАСТЬ 2: После успешной генерации ПЕСНИ ====================
# Заменить блок в generate_song_thread() после строки:
# execute_query_sync("UPDATE generations SET audio_url = %s, suno_audio_id = %s, status = %s WHERE task_id = %s")

if result:
    audio_url, suno_task_id, audio_id = result
    
    # Обновляем существующую запись в БД
    execute_query_sync(
        '''UPDATE generations 
           SET audio_url = %s, suno_audio_id = %s, status = %s 
           WHERE task_id = %s''',
        (audio_url, audio_id, 'completed', _task_id)
    )
    logger.info(f"✅ Обновлена запись в БД для task_id={_task_id} со статусом 'completed'")
    
    # ✅ БЛОК 2: Парсим URL и создаем demo_track
    try:
        import json
        audio_urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
        
        # Если есть 2 URL (варианты v1 и v2)
        if len(audio_urls) >= 2:
            # В реальности Suno API возвращает полные версии
            # Для demo нужно либо:
            # 1. Обрезать до 45 сек (требует ffmpeg на сервере)
            # 2. Использовать полные как demo (упрощенный вариант)
            # 3. Хранить только полные, а demo — это preview из Suno
            
            # Упрощенный вариант: храним как demo и full одинаковые URL
            # В production нужно обрезать или использовать preview_url из Suno API
            create_demo_track(
                user_id=_user_id,
                task_id=_task_id,
                demo_url_1=audio_urls[0],  # TODO: заменить на preview или обрезанную версию
                demo_url_2=audio_urls[1] if len(audio_urls) > 1 else None,
                full_url_1=audio_urls[0],
                full_url_2=audio_urls[1] if len(audio_urls) > 1 else None
            )
            logger.info(f"✅ Создан demo_track для task_id={_task_id}")
        else:
            # Если только 1 URL
            create_demo_track(
                user_id=_user_id,
                task_id=_task_id,
                demo_url_1=audio_urls[0],
                demo_url_2=None,
                full_url_1=audio_urls[0],
                full_url_2=None
            )
            logger.info(f"✅ Создан demo_track (1 URL) для task_id={_task_id}")
    except Exception as demo_error:
        logger.error(f"⚠️ Ошибка создания demo_track: {demo_error}")
        # Продолжаем работу, даже если demo_track не создался
    
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
    
    # ✅ БЛОК 2: Добавляем информацию о разблокировке
    message_text += "💎 Что можно сделать с этой песней:\n\n"
    message_text += "🔓 Разблокировать полные версии (1 токен)\n"
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


# ==================== ЧАСТЬ 3: Callback handler для unlock ====================
# Добавить в метод handle_callback() внутри блока обработки callbacks

# Обработка кнопки "Разблокировать"
elif action == "unlock":
    task_id_to_unlock = payload.get('task_id', '')
    logger.info(f"🔓 Запрос на разблокировку трека от пользователя {user_id}, task_id={task_id_to_unlock}")
    
    # Вызываем функцию разблокировки
    result = unlock_demo_track(user_id, task_id_to_unlock)
    
    if result['success']:
        # Формируем сообщение с полными версиями
        message_text = result['message'] + "\n\n"
        
        if result['full_url_1']:
            message_text += f"🎵 Полная версия 1:\n{result['full_url_1']}\n\n"
        
        if result['full_url_2']:
            message_text += f"🎵 Полная версия 2:\n{result['full_url_2']}\n\n"
        
        message_text += "Наслаждайтесь полными версиями! 🎶"
        
        self.send_message(
            user_id=user_id,
            message=message_text,
            keyboard=self.get_main_keyboard(user_id)
        )
    else:
        # Ошибка разблокировки
        self.send_message(
            user_id=user_id,
            message=result['message'],
            keyboard=self.get_main_keyboard(user_id)
        )


# ==================== ЧАСТЬ 4: Обновить клавиатуру get_song_options_keyboard ====================
# В файле vk_keyboards.py, функция get_song_options_keyboard()

def get_song_options_keyboard(task_id):
    """Клавиатура с опциями для готовой песни (callback-кнопки с payload)"""
    import json
    keyboard = VkKeyboard(inline=True)

    # ✅ БЛОК 2: Добавляем кнопку разблокировки
    keyboard.add_callback_button(
        '🔓 Разблокировать (1 токен)',
        color=VkKeyboardColor.POSITIVE,
        payload=json.dumps({"action": "unlock", "task_id": str(task_id)})
    )
    keyboard.add_line()
    
    keyboard.add_callback_button(
        '🎤 Минусовка (1 токен)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "karaoke", "task_id": str(task_id)})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        '🎸 Кавер (1 токен)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "cover", "task_id": str(task_id)})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        '🎵 В WAV (2 токена)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "wav", "task_id": str(task_id)})
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        '🔗 Поделиться',
        color=VkKeyboardColor.POSITIVE,
        payload=json.dumps({"action": "share", "task_id": str(task_id)})
    )

    return keyboard


# ==================== ЧАСТЬ 5: Проверка is_unlocked перед публикацией ====================
# Добавить в callback handler для "share" (публикация)

elif action == "share":
    task_id_to_share = payload.get('task_id', '')
    logger.info(f"🔗 Запрос на публикацию песни от пользователя {user_id}, task_id={task_id_to_share}")
    
    try:
        # ✅ БЛОК 2: Проверяем, разблокирован ли трек
        if not is_track_unlocked(task_id_to_share, user_id):
            self.send_message(
                user_id=user_id,
                message="❌ Сначала разблокируйте полную версию трека (1 токен), чтобы опубликовать её.",
                keyboard=self.get_main_keyboard(user_id)
            )
            logger.warning(f"⚠️ Попытка публикации неразблокированного трека: user_id={user_id}, task_id={task_id_to_share}")
            return
        
        # Получаем данные о треке (теперь берем из demo_tracks)
        demo_info = get_demo_track_info(task_id_to_share, user_id)
        
        if demo_info and demo_info['is_unlocked']:
            import urllib.parse
            
            # Берем полную версию для публикации
            share_url = demo_info['full_url_1']
            
            if not share_url:
                # Fallback: если не нашли в demo_tracks, берем из generations
                song_info = execute_query_sync(
                    "SELECT audio_url FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                    (task_id_to_share, user_id)
                )
                if song_info and song_info[0][0]:
                    audio_url = song_info[0][0]
                    try:
                        import json as _json
                        urls = _json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                        share_url = urls[0]
                    except Exception:
                        share_url = audio_url
            
            bot_link = "https://vk.com/club235442407"  # Замените на ID вашей группы
            share_text = f"🎵 Послушай мою песню, созданную с помощью ALBI Music!\n\n🤖 Создай свою: {bot_link}"
            vk_share_link = f"https://vk.com/share.php?url={urllib.parse.quote(share_url, safe='')}&title={urllib.parse.quote(share_text, safe='')}"
            
            self.send_message(
                user_id=user_id,
                message=(
                    f"🔗 Поделиться своей песней\n\n"
                    f"Нажмите на ссылку ниже, чтобы опубликовать трек на своей странице ВКонтакте:\n\n"
                    f"{vk_share_link}\n\n"
                    f"или скопируйте прямую ссылку на трек:\n{share_url}"
                ),
                keyboard=self.get_main_keyboard(user_id)
            )
            logger.info(f"✅ Ссылка для публикации отправлена пользователю {user_id}")
        else:
            self.send_message(
                user_id=user_id,
                message="❌ Трек не найден или не разблокирован.",
                keyboard=self.get_main_keyboard(user_id)
            )
    except Exception as e:
        logger.error(f"❌ Ошибка при создании ссылки для публикации: {e}")
        self.send_message(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            keyboard=self.get_main_keyboard(user_id)
        )


# ==================== КОНЕЦ БЛОКА 2 ====================
