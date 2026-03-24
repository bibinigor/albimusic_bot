import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Находим и исправляем обработчик legal_documents
pattern = r'(@dp\.callback_query_handler\(lambda c: c\.data == "legal_documents"\).*?)(?=@dp\.callback_query_handler|\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_handler = match.group(1)
    print("Найден старый обработчик:")
    print(old_handler[:200] + "..." if len(old_handler) > 200 else old_handler)
    
    # Создаем новый правильный обработчик
    new_handler = '''@dp.callback_query_handler(lambda c: c.data == "legal_documents")
async def process_legal_documents(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📜 Политика конфиденциальности", url="https://albi-music.ru/documents/privacy.html"),
        InlineKeyboardButton("📄 Публичная оферта", url="https://albi-music.ru/documents/offer.html")
    )
    await bot.send_message(callback_query.from_user.id, "📄 *Правовые документы:*", reply_markup=markup, parse_mode="Markdown")'''

    # Заменяем
    content = content.replace(old_handler, new_handler)
    
    with open('main_with_payments.py', 'w') as f:
        f.write(content)
    
    print("✅ Обработчик исправлен")
else:
    print("❌ Обработчик не найден")
