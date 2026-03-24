@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора режима генерации"""
    await callback_query.answer()
    
    mode = callback_query.data.replace('mode_', '')
    user_id = str(callback_query.from_user.id)
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    
    # ========== УМНОЕ ОПРЕДЕЛЕНИЕ ТИПА ==========
    lyrics = state_data.get('lyrics', '').strip()
    prompt = state_data.get('prompt', '').strip()
    explicit_type = state_data.get('generation_type', None)
    
    if lyrics:
        generation_type = 'song'
        logging.info(f"🎤 Detected SONG generation (lyrics: {len(lyrics)} chars)")
    elif prompt:
        generation_type = 'music'
        logging.info(f"🎵 Detected MUSIC generation (prompt: {len(prompt)} chars)")
    elif explicit_type:
        generation_type = explicit_type
        logging.info(f"📋 Using explicit type: {explicit_type}")
    else:
        logging.error("❌ Cannot determine generation type")
        await callback_query.message.answer("❌ Ошибка: не удалось определить тип генерации")
        await state.finish()
        return
    
    logging.info(f"User {user_id} selected mode: {mode} for {generation_type}")
    
    # Сохраняем выбор
    await state.update_data(generation_mode=mode)
    
    # Запускаем генерацию
    if generation_type == 'song':
        lyrics = state_data.get('lyrics', '')
        style = state_data.get('style', '')
        
        if not lyrics:
            await callback_query.message.answer("❌ Ошибка: текст песни не найден")
            await state.finish()
            return
        
        from celery_tasks import generate_song_task
        task = generate_song_task.delay(
            user_id=user_id,
            lyrics=lyrics,
            style=style,
            custom_mode=(mode == 'creative')
        )
        
        await callback_query.message.answer(
            "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
        )
        
    else:  # music
        prompt = state_data.get('prompt', '')
        
        if not prompt:
            await callback_query.message.answer("❌ Ошибка: описание музыки не найдено")
            await state.finish()
            return
        
        from celery_tasks import generate_music_task
        task = generate_music_task.delay(
            user_id=user_id,
            prompt=f"{prompt}. {'творческая интерпретация' if mode == 'creative' else 'точное соответствие'}"
        )
        
        await callback_query.message.answer(
            "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
        )
    
    await state.finish()
