import re

with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Найдем функцию get_admin_stats (примерно строка 268)
for i, line in enumerate(lines):
    if 'async def get_admin_stats():' in line:
        start_line = i
        break

# Найдем конец функции (до следующей def или return)
for i in range(start_line, len(lines)):
    if i > start_line + 50:  # Не ищем слишком далеко
        break
    if lines[i].strip().startswith('async def') and i != start_line:
        end_line = i
        break
    elif 'return {' in lines[i]:
        # Ищем закрывающую скобку
        for j in range(i, min(i+20, len(lines))):
            if lines[j].strip() == '}':
                end_line = j + 1
                break

# Заменяем функцию
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
            'new_today': new_7days,
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
        }
'''

# Заменяем строки
lines[start_line:end_line] = [new_function]

# Теперь найдем и исправим текст статистики
for i, line in enumerate(lines):
    if 'text = f"📊 *Статистика бота:*' in line:
        # Удаляем старую строку и возможно следующие
        old_indent = len(line) - len(line.lstrip())
        
        # Создаем новый текст с правильными отступами
        new_text = f'''{' ' * old_indent}text = f"""📊 *Статистика бота:*

{' ' * old_indent}👥 Всего пользователей: {{stats[\'total_users\']}}
{' ' * old_indent}🆕 Новых за 7 дней: {{stats[\'new_7days\']}}
{' ' * old_indent}🎵 Всего генераций за 7 дней: {{stats[\'total_generations_7days\']}}
{' ' * old_indent}✅ Успешных за 7 дней: {{stats[\'completed_generations_7days\']}}
{' ' * old_indent}💰 Платных за 7 дней: {{stats[\'paid_generations_7days\']}}

{' ' * old_indent}📈 Общая статистика:
{' ' * old_indent}🎵 Всего генераций: {{stats[\'total_generations\']}}
{' ' * old_indent}✅ Завершено: {{stats[\'completed_generations\']}}"""'''
        
        lines[i] = new_text + '\n'
        
        # Удаляем старые строки (если они занимают несколько строк)
        j = i + 1
        while j < len(lines) and ('Новых сегодня:' in lines[j] or '💰 Кредитов Suno:' in lines[j]):
            lines[j] = ''
            j += 1
        break

# Сохраняем
with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("✅ Функция статистики исправлена с правильными отступами")
print("📋 Изменения:")
print("1. Исправлены отступы в get_admin_stats")
print("2. Исправлены отступы в тексте статистики")
print("3. Статистика теперь показывает данные за 7 дней")
