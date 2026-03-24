with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Исправляем строки 746-763
# Удаляем дублирование и исправляем отступы
new_handler = '''async def process_create_music(callback_query: types.CallbackQuery):
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

# Находим начало и конец функции
start_idx = -1
end_idx = -1
for i in range(746, 780):
    if 'async def process_create_music' in lines[i]:
        start_idx = i
    elif start_idx != -1 and 'await MusicStates.waiting_for_music_style.set()' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    lines[start_idx:end_idx+1] = [new_handler]
    print(f"✅ Обработчик process_create_music исправлен (строки {start_idx+1}-{end_idx+1})")
else:
    print("❌ Не удалось найти обработчик")

with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)
