with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''            if result and result[0][0] == 0:
                # Первое приглашение - добавляем 2 генерации
                execute_query_sync(
                    'INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (%s, %s, NOW())',
                    (invited_by, user.id)
                )
                execute_query_sync(
                    'UPDATE users SET balance = balance + 2 WHERE user_id = %s',
                    (invited_by,)
                )
                try:
                    await bot.send_message(invited_by, f"🎉 По вашей ссылке зарегистрировался новый пользователь!\\n\\n💰 Вам начислено 2 токена бесплатно!")
                except:
                    pass
                logging.info(f"✅ Реферал: {invited_by} получил 2 токена за {user.id}")'''

new = '''            if result and result[0][0] == 0:
                # Добавляем запись о реферале
                execute_query_sync(
                    'INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (%s, %s, NOW())',
                    (invited_by, user.id)
                )
                
                # Считаем сколько всего рефералов
                count_result = execute_query_sync(
                    'SELECT COUNT(*) FROM referrals WHERE referrer_id = %s',
                    (invited_by,)
                )
                referral_count = count_result[0][0] if count_result else 0
                
                # Базовая награда: 2 токена
                tokens_to_add = 2
                message_text = f"🎉 По вашей ссылке зарегистрировался новый пользователь!\\n\\n💰 Вам начислено 2 токена бесплатно!"
                
                # Бонус за 5-го реферала
                if referral_count == 5:
                    tokens_to_add = 7  # 2 базовых + 5 бонус
                    message_text = f"🎉🎉🎉 ПОЗДРАВЛЯЕМ!\\n\\nВы пригласили 5-го друга!\\n\\n💰 Вам начислено 7 токенов (2 + бонус 5)!\\n🎁 Продолжайте приглашать и зарабатывать!"
                
                execute_query_sync(
                    'UPDATE users SET balance = balance + %s WHERE user_id = %s',
                    (tokens_to_add, invited_by)
                )
                
                try:
                    await bot.send_message(invited_by, message_text)
                except:
                    pass
                logging.info(f"✅ Реферал: {invited_by} получил {tokens_to_add} токенов за {user.id} (всего рефералов: {referral_count})")'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Бонус за 5-го реферала добавлен")
