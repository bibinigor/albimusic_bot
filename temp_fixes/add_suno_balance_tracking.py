import fileinput
import sys

# Добавляем функцию отслеживания Suno генераций в final_bot.py
with open('final_bot.py', 'r') as f:
    content = f.read()

# Добавляем функцию после импортов
if 'async def get_suno_balance():' not in content:
    # Находим место после импортов
    imports_end = content.find('async def get_user_balance')
    
    if imports_end != -1:
        suno_balance_function = '''
async def get_suno_balance():
    """Получить статистику использованных генераций Suno"""
    try:
        # Получаем количество завершенных генераций за последние 30 дней
        result = await fetch_query(
            "SELECT COUNT(*) as used FROM generations WHERE status = 'completed' AND created_at >= NOW() - INTERVAL '30 days'"
        )
        used_last_30_days = result[0]['used'] if result else 0
        
        # Предполагаем что у нас изначально было 1000 кредитов (можно изменить)
        initial_credits = 1000
        remaining_credits = max(0, initial_credits - used_last_30_days)
        
        return {
            'success': True,
            'used_last_30_days': used_last_30_days,
            'remaining_credits': remaining_credits,
            'initial_credits': initial_credits
        }
    except Exception as e:
        logging.error(f"❌ Ошибка получения статистики Suno: {e}")
        return {'success': False, 'error': str(e)}
'''
        
        content = content[:imports_end] + suno_balance_function + '\\n\\n' + content[imports_end:]

# Добавляем вызов в админ панель
if 'stats_text += f"• Уникальных пользователей: {users[0][\'total\']}\\n\\n"' in content:
    content = content.replace(
        'stats_text += f"• Уникальных пользователей: {users[0][\'total\']}\\n\\n"',
        'stats_text += f"• Уникальных пользователей: {users[0][\'total\']}\\n\\n"\n            \n            # Добавляем информацию о Suno балансе\n            suno_balance = await get_suno_balance()\n            if suno_balance[\'success\']:\n                stats_text += (\n                    f"🎵 Баланс Suno API:\\n"\n                    f"• Использовано за 30 дней: {suno_balance[\'used_last_30_days\']}\\n"\n                    f"• Осталось кредитов: {suno_balance[\'remaining_credits\']}/{suno_balance[\'initial_credits\']}\\n\\n"\n                )\n            else:\n                stats_text += f"❌ Ошибка баланса Suno: {suno_balance[\'error\']}\\n\\n"'
    )

with open('final_bot.py', 'w') as f:
    f.write(content)

print('✅ Функция отслеживания Suno баланса добавлена в админ панель')
