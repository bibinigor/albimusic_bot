import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Модифицируем process_create_song
process_create_song_pattern = r'(@dp\.callback_query_handler\(lambda c: c\.data == \'create_song\'\)\s+async def process_create_song\(callback_query: types\.CallbackQuery\):.*?)await SongStates\.waiting_for_song_style\.set\(\)'

def fix_create_song(match):
    handler = match.group(1)
    # Добавляем удаление сообщения с клавиатурой и кнопку отмены
    fixed_handler = handler + '''    # Удаляем сообщение с inline-клавиатурой, чтобы пользователь не путался
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
    return fixed_handler

content = re.sub(process_create_song_pattern, fix_create_song, content, flags=re.DOTALL)

# Модифицируем process_create_music
process_create_music_pattern = r'(@dp\.callback_query_handler\(lambda c: c\.data == \'create_music\'\)\s+async def process_create_music\(callback_query: types\.CallbackQuery\):.*?)await MusicStates\.waiting_for_music_style\.set\(\)'

def fix_create_music(match):
    handler = match.group(1)
    fixed_handler = handler + '''    # Удаляем сообщение с inline-клавиатурой, чтобы пользователь не путался
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
    return fixed_handler

content = re.sub(process_create_music_pattern, fix_create_music, content, flags=re.DOTALL)

# Добавляем обработчик для кнопки отмены
cancel_handler = '''
# Обработчик отмены создания (из состояния)
@dp.callback_query_handler(lambda c: c.data == 'cancel_creation', state="*")
async def process_cancel_creation(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.finish()
    
    # Удаляем текущее сообщение
    try:
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    except:
        pass
    
    await bot.send_message(callback_query.from_user.id, "✅ Создание отменено. Вы вернулись в главное меню.", 
                          reply_markup=get_main_menu_keyboard(callback_query.from_user.id))
'''

# Находим место, где заканчиваются callback обработчики (перед states)
if 'class SongStates(StatesGroup):' in content:
    pos = content.find('class SongStates(StatesGroup):')
    content = content[:pos] + cancel_handler + '\n\n' + content[pos:]
elif 'from aiogram.dispatcher.filters.state import State, StatesGroup' in content:
    pos = content.find('from aiogram.dispatcher.filters.state import State, StatesGroup')
    # Ищем ближайший class StatesGroup после импорта
    lines = content.split('\n')
    for i in range(len(lines)):
        if i > content.find('from aiogram.dispatcher.filters.state import State, StatesGroup') and 'class' in lines[i] and 'StatesGroup' in lines[i]:
            pos = content.find(lines[i])
            content = content[:pos] + cancel_handler + '\n\n' + content[pos:]
            break

with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Обработчики модифицированы:")
print("1. Сообщения с inline-клавиатурой теперь удаляются")
print("2. Добавлены кнопки '❌ Отменить создание'")
print("3. Добавлен обработчик отмены из любого состояния")
