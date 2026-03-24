import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Новая правильная функция get_admin_stats
new_function = '''async def get_admin_stats():
    """Получить статистику из PostgreSQL"""
    try:
        # Импортируем функции БД
        from postgres_db import fetch_query
        
        # 1. Всего пользователей (из таблицы users)
        users_result = await fetch_query("SELECT COUNT(*) as total FROM users")
        total_users = users_result[0]['total'] if users_result else 0
        
        # 2. Новых пользователей за 7 дней
        new_7days_result = await fetch_query("""
            SELECT COUNT(*) as total 
            FROM users 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        new_7days = new_7days_result[0]['total'] if new_7days_result else 0
        
        # 3. Всего генераций за 7 дней
        gens_7days_result = await fetch_query("""
            SELECT COUNT(*) as total 
            FROM generations 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        total_generations_7days = gens_7days_result[0]['total'] if gens_7days_result else 0
        
        # 4. Успешных генераций за 7 дней
        completed_7days_result = await fetch_query("""
            SELECT COUNT(*) as total 
            FROM generations 
            WHERE status = 'completed' 
            AND created_at >= NOW() - INTERVAL '7 days'
        """)
        completed_generations_7days = completed_7days_result[0]['total'] if completed_7days_result else 0
        
        # 5. Платных генераций за 7 дней (не free)
        paid_7days_result = await fetch_query("""
            SELECT COUNT(*) as total 
            FROM generations 
            WHERE (is_free = false OR is_free IS NULL) 
            AND created_at >= NOW() - INTERVAL '7 days'
        """)
        paid_generations_7days = paid_7days_result[0]['total'] if paid_7days_result else 0
        
        # 6. Общая статистика (для обратной совместимости)
        all_gens_result = await fetch_query("SELECT COUNT(*) as total FROM generations")
        total_generations = all_gens_result[0]['total'] if all_gens_result else 0
        
        completed_result = await fetch_query("SELECT COUNT(*) as total FROM generations WHERE status = 'completed'")
        completed_generations = completed_result[0]['total'] if completed_result else 0
        
        return {
            'total_users': total_users,
            'new_7days': new_7days,
            'total_generations_7days': total_generations_7days,
            'completed_generations_7days': completed_generations_7days,
            'paid_generations_7days': paid_generations_7days,
            # Для обратной совместимости
            'total_generations': total_generations,
            'completed_generations': completed_generations,
            'new_today': new_7days,  # Временно, пока не обновим текст
            'free_generations': 0,
            'active_referrals': 0
        }
    except Exception as e:
        logging.error(f"❌ Ошибка получения статистики: {e}")
        # Возвращаем значения по умолчанию
        return {
            'total_users': 0,
            'new_7days': 0,
            'total_generations_7days': 0,
            'completed_generations_7days': 0,
            'paid_generations_7days': 0,
            'total_generations': 0,
            'completed_generations': 0,
            'new_today': 0,
            'free_generations': 0,
            'active_referrals': 0
        }'''

# Найдем и заменим старую функцию
old_function_pattern = r'async def get_admin_stats\(\):.*?new_today.*?:.*?0.*?active_referrals.*?:.*?0.*?\n\s+\}'

if re.search(old_function_pattern, content, re.DOTALL):
    content = re.sub(old_function_pattern, new_function, content, flags=re.DOTALL)
    print("✅ Функция get_admin_stats обновлена")
else:
    print("❌ Не найдена старая функция get_admin_stats")

# Теперь обновим текст статистики (строка 730)
new_stats_text = '''    text = f"""📊 *Статистика бота:*

👥 Всего пользователей: {stats['total_users']}
🆕 Новых за 7 дней: {stats['new_7days']}
🎵 Всего генераций за 7 дней: {stats['total_generations_7days']}
✅ Успешных за 7 дней: {stats['completed_generations_7days']}
💰 Платных за 7 дней: {stats['paid_generations_7days']}

📈 Общая статистика:
🎵 Всего генераций: {stats['total_generations']}
✅ Завершено: {stats['completed_generations']}"""'''

# Заменяем старый текст статистики
old_stats_pattern = r"text = f\"📊 \*Статистика бота:\*\n\n👥 Всего пользователей: \{stats\['total_users'\]\}\n🆕 Новых сегодня: \{stats\['new_today'\]\}\n🎵 Всего генераций: \{stats\['total_generations'\]\}\n✅ Завершено: \{stats\['completed_generations'\]\}\n🎁 Бесплатных генераций: \{stats\['free_generations'\]\}\n👥 Активных рефералов: \{stats\['active_referrals'\]\}\n💰 Кредитов Suno: \{credits\}\""

if re.search(old_stats_pattern, content):
    content = re.sub(old_stats_pattern, new_stats_text, content)
    print("✅ Текст статистики обновлен")
else:
    print("⚠️ Не найден старый текст статистики, ищем альтернативный...")
    # Попробуем найти по другому паттерну
    old_stats_alt = r'text = f"📊 \*Статистика бота:\*\\n\\n👥 Всего пользователей:.*?💰 Кредитов Suno: \{credits\}"'
    if re.search(old_stats_alt, content):
        content = re.sub(old_stats_alt, new_stats_text, content, flags=re.DOTALL)
        print("✅ Текст статистики обновлен (альтернативный паттерн)")

# Сохраняем изменения
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print()
print("📋 ИЗМЕНЕНИЯ В СТАТИСТИКЕ:")
print("1. Всего пользователей - из таблицы users (правильно)")
print("2. Новых за 7 дней - вместо 'сегодня'")
print("3. Всего генераций за 7 дней")
print("4. Успешных генераций за 7 дней")  
print("5. Платных генераций за 7 дней")
print("6. Добавлена общая статистика (все время)")
print("7. Убраны некорректные 'бесплатные генерации' и 'активные рефералы'")
