with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Заменяем старую функцию get_admin_stats на новую для PostgreSQL
old_stats_function = '''def get_admin_stats():
    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE("now")')
        new_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM generations')
        total_generations = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM generations WHERE is_free = TRUE')
        free_generations = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE bonus_applied = TRUE')
        active_referrals = cursor.fetchone()[0]
        conn.close()
        return {
            'total_users': total_users,
            'new_today': new_today,
            'total_generations': total_generations,
            'free_generations': free_generations,
            'active_referrals': active_referrals
        }
    except sqlite3.Error as e:
        logging.error(f"❌ Ошибка получения статистики: {e}")
        return {}'''

new_stats_function = '''async def get_admin_stats():
    """Получить статистику из PostgreSQL"""
    try:
        # Импортируем функции БД
        from postgres_db import fetch_query
        
        # Получаем статистику пользователей
        users_result = await fetch_query("SELECT COUNT(*) as total FROM generations WHERE user_id IS NOT NULL")
        total_users = users_result[0]['total'] if users_result else 0
        
        # Новые пользователи сегодня (приблизительно)
        today_result = await fetch_query("SELECT COUNT(DISTINCT user_id) as total FROM generations WHERE created_at >= CURRENT_DATE")
        new_today = today_result[0]['total'] if today_result else 0
        
        # Общее количество генераций
        generations_result = await fetch_query("SELECT COUNT(*) as total FROM generations")
        total_generations = generations_result[0]['total'] if generations_result else 0
        
        # Бесплатные генерации (приглашения)
        free_result = await fetch_query("SELECT COUNT(*) as total FROM generations WHERE prompt LIKE '%приглаш%' OR prompt LIKE '%invite%'")
        free_generations = free_result[0]['total'] if free_result else 0
        
        # Активные рефералы (пользователи с приглашениями)
        referrals_result = await fetch_query("SELECT COUNT(DISTINCT user_id) as total FROM generations WHERE prompt LIKE '%приглаш%' OR prompt LIKE '%invite%'")
        active_referrals = referrals_result[0]['total'] if referrals_result else 0
        
        return {
            'total_users': total_users,
            'new_today': new_today,
            'total_generations': total_generations,
            'free_generations': free_generations,
            'active_referrals': active_referrals
        }
    except Exception as e:
        logging.error(f"❌ Ошибка получения статистики: {e}")
        return {}'''

content = content.replace(old_stats_function, new_stats_function)

with open('main_with_payments.py', 'w') as f:
    f.write(content)

print('✅ Функция статистики обновлена для PostgreSQL')
