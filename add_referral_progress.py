with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''@dp.callback_query_handler(lambda c: c.data == 'invite_friend')
async def process_invite_friend(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    referral_link = f"https://t.me/AlBimusic_bot?start=ref_{user_id}"

    # Отправляем сразу два сообщения подряд
    await bot.send_message(user_id, "Чтобы получить 2 токена бесплатно, скопируйте сообщение ниже и отправьте его другу 👇")'''

new = '''@dp.callback_query_handler(lambda c: c.data == 'invite_friend')
async def process_invite_friend(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    referral_link = f"https://t.me/AlBimusic_bot?start=ref_{user_id}"

    # Считаем рефералов
    from db_utils import execute_query_sync
    count_result = execute_query_sync(
        'SELECT COUNT(*) FROM referrals WHERE referrer_id = %s',
        (user_id,)
    )
    referral_count = count_result[0][0] if count_result else 0
    
    # Прогресс-бар
    progress = "🟢" * referral_count + "⚪" * (5 - referral_count)
    bonus_text = ""
    if referral_count < 5:
        remaining = 5 - referral_count
        bonus_text = f"\\n🎯 До бонуса +5 токенов: осталось {remaining} {'друг' if remaining == 1 else 'друга' if remaining < 5 else 'друзей'}!"
    elif referral_count == 5:
        bonus_text = "\\n🎉 Бонус за 5-го друга получен!"
    
    # Отправляем сообщение с прогрессом
    await bot.send_message(
        user_id, 
        f"🎁 *Приглашено друзей:* {referral_count}/5\\n{progress}{bonus_text}\\n\\nЧтобы получить 2 токена, скопируйте сообщение ниже и отправьте другу 👇",
        parse_mode="Markdown"
    )'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Прогресс-бар рефералов добавлен")
