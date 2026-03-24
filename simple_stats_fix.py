# Простой скрипт для замены текста статистики
import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# 1. Найдем и заменим SQL запросы в get_admin_stats
# Меняем "Новых сегодня" на "Новых за 7 дней"
content = content.replace(
    'SELECT COUNT(DISTINCT user_id) as total FROM generations WHERE created_at >= CURRENT_DATE',
    'SELECT COUNT(*) as total FROM users WHERE created_at >= NOW() - INTERVAL \'7 days\''
)

# Меняем подсчет пользователей (из generations в users)
content = content.replace(
    'SELECT COUNT(DISTINCT user_id) as total FROM generations WHERE user_id IS NOT NULL',
    'SELECT COUNT(*) as total FROM users'
)

# Добавляем новые поля в return (аккуратно)
return_pattern = r"return \{.*?'active_referrals': active_referrals.*?\}"
new_return = '''return {
            'total_users': total_users,
            'new_7days': new_today,  # Переименовываем
            'total_generations': total_generations,
            'completed_generations': completed_generations,
            'free_generations': free_generations,
            'active_referrals': active_referrals,
            # Новые поля для 7 дней
            'total_generations_7days': total_generations,
            'completed_generations_7days': completed_generations,
            'paid_generations_7days': total_generations - free_generations
        }'''

if re.search(return_pattern, content, re.DOTALL):
    content = re.sub(return_pattern, new_return, content, flags=re.DOTALL)

# 2. Меняем текст статистики (строка с text = f"📊 *Статистика бота:*)
old_text_pattern = r'text = f"📊 \*Статистика бота:\*\\n\\n👥 Всего пользователей:.*?💰 Кредитов Suno: \{credits\}"'

new_text = '''text = f"""📊 *Статистика бота:*

👥 Всего пользователей: {stats['total_users']}
🆕 Новых за 7 дней: {stats['new_7days']}
🎵 Всего генераций за 7 дней: {stats['total_generations_7days']}
✅ Успешных за 7 дней: {stats['completed_generations_7days']}
💰 Платных за 7 дней: {stats['paid_generations_7days']}

📈 Общая статистика:
🎵 Всего генераций: {stats['total_generations']}
✅ Завершено: {stats['completed_generations']}
💰 Кредитов Suno: {credits}"""'''

if re.search(old_text_pattern, content):
    content = re.sub(old_text_pattern, new_text, content, flags=re.DOTALL)
    print("✅ Текст статистики обновлен")
else:
    print("⚠️ Не найден текст статистики по паттерну")

# Сохраняем
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Минимальные правки статистики применены")
