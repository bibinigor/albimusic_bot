with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем асинхронный postgres_db на синхронный db_utils
old = '''        try:
            # Используем PostgreSQL для реферальной системы
            from postgres_db import fetch_query, execute_query
            result = await fetch_query(
                'SELECT COUNT(*) FROM referrals WHERE referrer_id = $1 AND referred_id = $2',
                invited_by, user.id
            )
            if result and result[0][0] == 0:
                # Первое приглашение - добавляем 2 генерации
                await execute_query(
                    'INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES ($1, $2, NOW())',
                    invited_by, user.id
                )
                await execute_query(
                    'UPDATE users SET balance = balance + 2 WHERE user_id = $1',
                    invited_by
                )
                try:
                    await bot.send_message(invited_by, f"🎉 По вашей ссылке зарегистрировался новый пользователь!\\n\\n💰 Вам начислено 2 токена бесплатно!")
                except:
                    pass
        except Exception as e:
            logging.error(f"❌ Ошибка обработки реферала: {e}")'''

new = '''        try:
            # Используем db_utils для реферальной системы
            from db_utils import execute_query_sync
            result = execute_query_sync(
                'SELECT COUNT(*) FROM referrals WHERE referrer_id = %s AND referred_id = %s',
                (invited_by, user.id)
            )
            if result and result[0][0] == 0:
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
                logging.info(f"✅ Реферал: {invited_by} получил 2 токена за {user.id}")
        except Exception as e:
            logging.error(f"❌ Ошибка обработки реферала: {e}")'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Реферальная система исправлена")
