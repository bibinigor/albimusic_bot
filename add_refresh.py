with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем строку
old = '    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown")'
new = '''    refresh_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"))
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown", reply_markup=refresh_btn)'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Кнопка добавлена")
