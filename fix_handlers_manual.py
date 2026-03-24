# Создаем временный файл с исправленными обработчиками
with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Находим и исправляем process_create_song
in_process_create_song = False
for i in range(len(lines)):
    if '@dp.callback_query_handler(lambda c: c.data == \'create_song\')' in lines[i]:
        in_process_create_song = True
        start_idx = i
    elif in_process_create_song and 'async def process_create_song' in lines[i]:
        # Нашли начало функции
        func_start = i
    elif in_process_create_song and 'await SongStates.waiting_for_song_style.set()' in lines[i]:
        # Это старый код, нужно заменить все от func_start до i
        old_code = lines[func_start:i+1]
        
        # Новый код
        new_code = '''async def process_create_song(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    # Удаляем сообщение с inline-клавиатурой, чтобы пользователь не путался
    try:
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    except:
        pass
    
    # Создаем клавиатуру с кнопкой отмены
    from aiogram.dispatcher import FSMContext
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Отменить создание", callback_data="cancel_creation"))
    
    await bot.send_message(callback_query.from_user.id, "🎤 *Отлично! Сначала опишите стиль песни:*\\n\\n• Жанр (рок, поп, хип-хоп, классика...)\\n• Музыкальные инструменты\\n• Мужской/женский голос\\n• Темп, настроение", 
                          reply_markup=cancel_markup, parse_mode="Markdown")
    await SongStates.waiting_for_song_style.set()
'''
        
        lines[func_start:i+1] = [new_code]
        in_process_create_song = False
        print("✅ Исправлен process_create_song")

# Теперь process_create_music
in_process_create_music = False
for i in range(len(lines)):
    if '@dp.callback_query_handler(lambda c: c.data == \'create_music\')' in lines[i]:
        in_process_create_music = True
        start_idx = i
    elif in_process_create_music and 'async def process_create_music' in lines[i]:
        # Нашли начало функции
        func_start = i
    elif in_process_create_music and 'await MusicStates.waiting_for_music_style.set()' in lines[i]:
        # Это старый код, нужно заменить
        new_code = '''async def process_create_music(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    # Удаляем сообщение с inline-клавиатурой, чтобы пользователь не путался
    try:
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    except:
        pass
    
    # Создаем клавиатуру с кнопкой отмены
    from aiogram.dispatcher import FSMContext
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Отменить создание", callback_data="cancel_creation"))
    
    await bot.send_message(callback_query.from_user.id, "🎵 *Опишите стиль музыки:*\\n\\n• Жанр и направление\\n• Музыкальные инструменты\\n• Ритм и темп\\n• Настроение и атмосфера", 
                          reply_markup=cancel_markup, parse_mode="Markdown")
    await MusicStates.waiting_for_music_style.set()
'''
        
        lines[func_start:i+1] = [new_code]
        in_process_create_music = False
        print("✅ Исправлен process_create_music")

# Записываем обратно
with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("✅ Обработчики исправлены вручную")
