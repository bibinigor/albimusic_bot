import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

print("🔧 ВНОСИМ ИЗМЕНЕНИЯ В ИНТЕРФЕЙС...")

# 1. Убираем "📄 Документы" из главного меню (строка 518)
# Ищем главное меню
main_menu_pattern = r'markup\.add\(KeyboardButton\("💰 Баланс"\), KeyboardButton\("📄 Документы"\)\)'
new_main_menu = 'markup.add(KeyboardButton("💰 Баланс"), KeyboardButton("🎵 Примеры песен"))'

if re.search(main_menu_pattern, content):
    content = re.sub(main_menu_pattern, new_main_menu, content)
    print("✅ Убрали '📄 Документы' из главного меню, добавили '🎵 Примеры песен'")
else:
    print("⚠️ Не найден паттерн главного меню")

# 2. Добавляем "📄 Правовые документы" в клавиатуру баланса (строка 539)
balance_keyboard_pattern = r'def get_balance_keyboard\(user_id\):.*?InlineKeyboardButton\("🔥 Оплатить 400 руб \(10 генераций\)", callback_data="pay_400"\)'
new_balance_keyboard = '''def get_balance_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🌟 Пригласить друга (+2 бесплатно)", callback_data="invite_friend"),
        InlineKeyboardButton("💳 Оплатить 50 руб (1 генерация)", callback_data="pay_50"),
        InlineKeyboardButton("🔥 Оплатить 400 руб (10 генераций)", callback_data="pay_400"),
        InlineKeyboardButton("📄 Правовые документы", callback_data="legal_documents")
    )
    return markup'''

if re.search(balance_keyboard_pattern, content, re.DOTALL):
    content = re.sub(balance_keyboard_pattern, new_balance_keyboard, content, flags=re.DOTALL)
    print("✅ Добавили '📄 Правовые документы' в клавиатуру баланса")
else:
    print("⚠️ Не найден паттерн клавиатуры баланса")

# 3. Создаем новый обработчик для кнопки "legal_documents"
# Найдем место после других callback обработчиков (после show_privacy/show_offer)
legal_docs_handler = '''
@dp.callback_query_handler(lambda c: c.data == "legal_documents")
async def process_legal_documents(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📜 Политика конфиденциальности", callback_data="show_privacy"),
        InlineKeyboardButton("📄 Публичная оферта", callback_data="show_offer")
    )
    await bot.send_message(callback_query.from_user.id, "📄 *Правовые документы:*", reply_markup=markup, parse_mode="Markdown")'''

# Вставляем после обработчика show_offer (находим его)
show_offer_pos = content.find('@dp.callback_query_handler(lambda c: c.data == \'show_offer\')')
if show_offer_pos != -1:
    # Находим конец этой функции
    end_pos = content.find('@dp.callback_query_handler', show_offer_pos + 100)
    if end_pos == -1:
        end_pos = len(content)
    
    # Вставляем новый обработчик
    content = content[:end_pos] + legal_docs_handler + '\n\n' + content[end_pos:]
    print("✅ Добавили обработчик для 'Правовые документы'")
else:
    print("⚠️ Не найден обработчик show_offer")

# 4. Создаем обработчик для кнопки "🎵 Примеры песен" в главном меню
examples_handler = '''
@dp.message_handler(lambda message: message.text == "🎵 Примеры песен")
async def handle_examples(message: types.Message):
    text = "🎵 *Послушайте примеры песен в нашем канале:*\\n\\n👉 @ALBImusic_Chart\\n\\nТам вы найдете лучшие треки, созданные нашими пользователями!"
    await message.answer(text, parse_mode="Markdown")'''

# Вставляем после обработчика документов (который теперь не будет использоваться, но оставим для совместимости)
docs_handler_pos = content.find('@dp.message_handler(lambda message: message.text == "📄 Документы")')
if docs_handler_pos != -1:
    # Находим конец этой функции
    end_pos = content.find('@dp.message_handler', docs_handler_pos + 100)
    if end_pos == -1:
        end_pos = len(content)
    
    # Вставляем новый обработчик
    content = content[:end_pos] + examples_handler + '\n\n' + content[end_pos:]
    print("✅ Добавили обработчик для '🎵 Примеры песен'")
else:
    print("⚠️ Не найден обработчик документов")

# Сохраняем
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print()
print("🎉 ИНТЕРФЕЙС ОБНОВЛЕН!")
print("=" * 60)
print("1. 📄 'Документы' убраны из главного меню")
print("2. 📄 'Правовые документы' добавлены в раздел Баланс")
print("3. 🎵 'Примеры песен' добавлены в главное меню")
print("4. 👉 Ссылка на канал @ALBImusic_Chart")
print()
print("ℹ️  Обработчик для старых 'Документов' остался для обратной совместимости")
print("   (пользователи, которые уже нажали кнопку, смогут ее использовать)")
