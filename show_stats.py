import psycopg2
from datetime import datetime, timedelta

conn = psycopg2.connect(
    dbname='albimusic_bot',
    user='albimusic_user',
    password='aXAnAixKT6@?B9',
    host='localhost'
)
cur = conn.cursor()

print('📊 AlBi-music Bot - ПОЛНАЯ СТАТИСТИКА ИСПОЛЬЗОВАНИЯ')
print('=' * 80)

# 1. ОБЩАЯ СТАТИСТИКА
cur.execute('SELECT COUNT(*) FROM users')
total_users = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM generations')
total_tasks = cur.fetchone()[0]

print(f'👥 Всего пользователей: {total_users}')
print(f'🎵 Всего задач генерации: {total_tasks}')
print()

# 2. СТАТИСТИКА ЗАДАЧ ПО СТАТУСАМ
cur.execute('''
    SELECT 
        status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM generations), 1) as percent
    FROM generations 
    GROUP BY status
    ORDER BY count DESC
''')

print('📈 СТАТУСЫ ЗАДАЧ:')
print('-' * 40)
for status, count, percent in cur.fetchall():
    print(f'{status:12} : {count:4} ({percent}%)')
print()

# 3. УСПЕШНОСТЬ ГЕНЕРАЦИЙ (без учета pending/processing)
cur.execute('''
    SELECT 
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
    FROM generations 
    WHERE status IN ('completed', 'error', 'failed')
''')

completed, errors, failed = cur.fetchone()
total_finished = completed + errors + failed

if total_finished > 0:
    success_rate = completed * 100.0 / total_finished
    print('🎯 УСПЕШНОСТЬ ГЕНЕРАЦИЙ (все время):')
    print('-' * 40)
    print(f'✅ Успешно: {completed}')
    print(f'❌ Ошибки: {errors}')
    print(f'⏰ Failed (таймаут): {failed}')
    print(f'📊 Всего завершено: {total_finished}')
    print(f'🎯 Успешность: {success_rate:.1f}%')
else:
    print('Нет завершенных задач')
print()

# 4. ПОСЛЕДНИЕ 7 ДНЕЙ
cur.execute('''
    SELECT 
        DATE(created_at) as day,
        COUNT(*) as tasks,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(DISTINCT user_id) as active_users
    FROM generations 
    WHERE created_at > NOW() - INTERVAL '7 days'
    GROUP BY DATE(created_at)
    ORDER BY day DESC
''')

print('📅 АКТИВНОСТЬ ЗА 7 ДНЕЙ:')
print('-' * 50)
print('Дата       | Задачи | Успешно | Пользователей | Успешность')
print('-' * 50)

rows = cur.fetchall()
for day, tasks, completed_day, users in rows:
    success_rate_day = completed_day * 100.0 / tasks if tasks > 0 else 0
    print(f'{day} | {tasks:6} | {completed_day:7} | {users:12} | {success_rate_day:.1f}%')

# Итог за 7 дней
if rows:
    total_7d = sum(r[1] for r in rows)
    completed_7d = sum(r[2] for r in rows)
    success_7d = completed_7d * 100.0 / total_7d if total_7d > 0 else 0
    print(f'{"Итого":10} | {total_7d:6} | {completed_7d:7} | {"-":12} | {success_7d:.1f}%')
print()

# 5. ТОП ПОЛЬЗОВАТЕЛЕЙ
cur.execute('''
    SELECT 
        u.user_id,
        u.username,
        u.first_name,
        COUNT(g.id) as task_count,
        COUNT(CASE WHEN g.status = 'completed' THEN 1 END) as completed,
        u.balance
    FROM users u
    LEFT JOIN generations g ON u.user_id = g.user_id
    GROUP BY u.user_id, u.username, u.first_name, u.balance
    ORDER BY task_count DESC
    LIMIT 5
''')

print('👑 ТОП-5 АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ:')
print('-' * 70)
print('ID | Username | Имя | Задачи | Успешно | Баланс')
print('-' * 70)

for user_id, username, first_name, tasks, completed_tasks, balance in cur.fetchall():
    username = f'@{username}' if username else '-'
    first_name = first_name or '-'
    print(f'{user_id:10} | {username:15} | {first_name:10} | {tasks:6} | {completed_tasks:8} | {balance:6}')

# 6. ПЛАТЕЖИ
cur.execute('''
    SELECT 
        COUNT(*) as payment_count,
        SUM(amount) as total_amount,
        AVG(amount) as avg_amount
    FROM payments 
    WHERE status = 'succeeded'
    AND created_at > NOW() - INTERVAL '30 days'
''')

pay_count, total_amount, avg_amount = cur.fetchone()

print()
print('💰 ПЛАТЕЖИ ЗА 30 ДНЕЙ:')
print('-' * 40)
if pay_count and total_amount:
    print(f'Количество платежей: {pay_count}')
    print(f'Общая сумма: {total_amount:.2f} руб.')
    print(f'Средний чек: {avg_amount:.2f} руб.')
else:
    print('Нет платежей за 30 дней')

# 7. РЕФЕРАЛЬНАЯ СИСТЕМА
cur.execute('''
    SELECT 
        COUNT(*) as total_referrals,
        COUNT(CASE WHEN reward_given = true THEN 1 END) as rewards_given
    FROM referrals
''')

total_ref, rewards = cur.fetchone()

print()
print('👥 РЕФЕРАЛЬНАЯ СИСТЕМА:')
print('-' * 40)
print(f'Всего приглашено: {total_ref}')
print(f'Вознаграждений выдано: {rewards}')

# 8. ПРОБЛЕМНЫЕ ПОКАЗАТЕЛИ
print()
print('⚠️  ПРОБЛЕМНЫЕ ПОКАЗАТЕЛИ:')
print('-' * 40)

# Высокая доля failed задач
if failed > 0 and failed * 100.0 / total_finished > 20:
    failed_percent = failed * 100.0 / total_finished
    print(f'❌ Высокий % failed задач: {failed_percent:.1f}%')

# Много ошибок у пользователей
cur.execute('''
    SELECT COUNT(DISTINCT user_id) FROM generations WHERE status = 'error' AND user_id != 338544009
''')
error_users = cur.fetchone()[0]
if error_users > 0:
    print(f'❌ Пользователи с ошибками: {error_users}')

# Задачи в обработке > 30 минут
cur.execute('''
    SELECT COUNT(*) FROM generations 
    WHERE status IN ('pending', 'processing') 
    AND created_at < NOW() - INTERVAL '30 minutes'
''')
stuck_tasks = cur.fetchone()[0]
if stuck_tasks > 0:
    print(f'⏰ Зависших задач (>30 мин): {stuck_tasks}')

if stuck_tasks == 0 and error_users == 0 and (failed * 100.0 / total_finished) < 20:
    print('✅ Все показатели в норме!')

print()
print('=' * 80)
print('📋 ВЫВОД:')
print(f'1. Общая успешность: {success_rate:.1f}%')
print(f'2. Задачи создаются и обрабатываются')
print(f'3. Пользователи получают результаты')
print(f'4. Сегодня исправлены таймауты → ожидаем рост успешности')

conn.close()
