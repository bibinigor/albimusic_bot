# Читаем файл
with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Находим обработчик process_generation_mode и добавляем дополнительную проверку
old_handler = '''@dp.callback_query_handler(lambda c: c.data.startswith('mode_'), state=SongStates.waiting_for_mode)
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_data = await state.get_data()
    style = user_data.get('style')
    lyrics = user_data.get('lyrics')'''

new_handler = '''@dp.callback_query_handler(lambda c: c.data.startswith('mode_'), state=SongStates.waiting_for_mode)
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    # Дополнительная проверка что это действительно mode_ кнопка
    if callback_query.data not in ['mode_exact', 'mode_creative']:
        await bot.send_message(callback_query.from_user.id, "❌ Неверный запрос. Начните заново.")
        await state.finish()
        return
    
    user_data = await state.get_data()
    style = user_data.get('style')
    lyrics = user_data.get('lyrics')'''

content = content.replace(old_handler, new_handler)

# Записываем обратно
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Обработчик process_generation_mode исправлен - добавлена проверка callback данных")
