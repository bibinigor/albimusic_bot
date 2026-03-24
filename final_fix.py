# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Исправляем process_create_song - удаляем дублирование
import re

# Паттерн для process_create_song
pattern1 = r'''(async def process_create_song\(callback_query: types\.CallbackQuery\):
    await bot\.answer_callback_query\(callback_query\.id\)
    await bot\.send_message\(callback_query\.from_user\.id, "🎤 \*Отлично! Сначала опишите стиль песни:\*\\n\\n• Жанр \(рок, поп, хип-хоп, классика\.\.\.\)\\n• Музыкальные инструменты\\n• Мужской/женский голос\\n• Темп, настроение", parse_mode="Markdown")
        # Удаляем сообщение с inline-клавиатурой.*?await SongStates\.waiting_for_song_style\.set\(\))'''

replacement1 = '''async def process_create_song(callback_query: types.CallbackQuery):
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
    await SongStates.waiting_for_song_style.set()'''

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# Паттерн для process_create_music
pattern2 = r'''(async def process_create_music\(callback_query: types\.CallbackQuery\):
    await bot\.answer_callback_query\(callback_query\.id\)
    await bot\.send_message\(callback_query\.from_user\.id, "🎵 \*Опишите стиль музыки:\*\\n\\n• Жанр и направление\\n• Музыкальные инструменты\\n• Ритм и темп\\n• Настроение и атмосфера", parse_mode="Markdown")
    await MusicStates\.waiting_for_music_style\.set\(\))'''

replacement2 = '''async def process_create_music(callback_query: types.CallbackQuery):
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
    await MusicStates.waiting_for_music_style.set()'''

content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

# Записываем обратно
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Исправлены оба обработчика (удалено дублирование)")
