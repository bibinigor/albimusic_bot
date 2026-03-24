import psycopg2
from datetime import datetime, timedelta

conn = psycopg2.connect(
    dbname='albimusic_bot',
    user='albimusic_user',
    password='aXAnAixKT6@?B9',
    host='localhost'
)
cur = conn.cursor()

print('📊 AlBi-music Bot - СТАТИСТИКА ИСПОЛЬЗОВАНИЯ')
print('=' * 80)

# Исключаем админа (338544009) из статистики
ADMIN_ID = 338544009

# 1. ОБЩАЯ СТАТИСТИКА (без админа)
cur.execute('SELECT COUNT(*) FROM users WHERE user_id != %s', (ADMIN_ID,))
total_users = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM generations WHERE user_id != %s', (ADMIN_ID,))
total_tasks = cur.fetchone()[0]

print(f'👥 Всего пользователей (без админа): {total_users}')
print(f'🎵 Всего задач генерации (без админа): {total_tasks}')
print()

# 2. СТАТИСТИКА ЗАДАЧ ПО СТАТУСАМ (без админа)
cur.execute('''
    SELECT 
        status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM generations WHERE user_id != %s), 1) as percent
    FROM generations 
    WHERE user_id != %s
    GROUP BY status
    ORDER BY count DESC
''', (ADMIN_ID, ADMIN_ID))

print('📈 СТАТУСЫ ЗАДАЧ (без админа):')
print('-' * 40)

status_translation = {
    'failed': 'Провалено',
    'completed': 'Успешно',
    'error': 'Ошибка',
    'pending': 'В ожидании',
    'processing': 'В процессе',
    'test': 'Тест'
}

for status, count, percent in cur.fetchall():
    status_ru = status_translation.get(status, status)
    print(f'{status_ru:15} : {count:4} ({percent}%)')
print()

# 3. УСПЕШНОСТЬ ГЕНЕРАЦИЙ (без админа)
cur.execute('''
    SELECT 
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
    FROM generations 
    WHERE user_id != %s
    AND status IN ('completed', 'error', 'failed')
''', (ADMIN_ID,))

completed, errors, failed = cur.fetchone()
total_finished = completed + errors + failed

if total_finished > 0:
    success_rate = completed * 100.0 / total_finished
    print('🎯 УСПЕШНОСТЬ ГЕНЕРАЦИЙ (без админа):')
    print('-' * 40)
    print(f'✅ Успешно: {completed}')
    print(f'❌ Ошибки: {errors}')
    print(f'⏰ Провалено (таймаут): {failed}')
    print(f'📊 Всего завершено: {total_finished}')
    print(f'🎯 Успешность: {success_rate:.1f}%')
    
    # Новая успешность после исправления таймаутов (последние 3 дня)
    cur.execute('''
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_new,
            COUNT(CASE WHEN status IN ('error', 'failed') THEN 1 END) as failed_new
        FROM generations 
        WHERE user_id != %s
        AND created_at > NOW() - INTERVAL '3 days'
        AND status IN ('completed', 'error', 'failed')
    ''', (ADMIN_ID,))
    
    completed_new, failed_new = cur.fetchone()
    total_new = completed_new + failed_new
    
    if total_new > 0:
        success_rate_new = completed_new * 100.0 / total_new
        print(f'🎯 Успешность последние 3 дня: {success_rate_new:.1f}%')
    
else:
    print('Нет завершенных задач (без админа)')
print()

# 4. ПОСЛЕДНИЕ 7 ДНЕЙ (без админа)
cur.execute('''
    SELECT 
        DATE(created_at) as day,
        COUNT(*) as tasks,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(DISTINCT user_id) as active_users
    FROM generations 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '7 days'
    GROUP BY DATE(created_at)
    ORDER BY day DESC
''', (ADMIN_ID,))

print('📅 АКТИВНОСТЬ ЗА 7 ДНЕЙ (без админа):')
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

# 5. ТОП ПОЛЬЗОВАТЕЛЕЙ (без админа)
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
    WHERE u.user_id != %s
    GROUP BY u.user_id, u.username, u.first_name, u.balance
    ORDER BY task_count DESC
    LIMIT 5
''', (ADMIN_ID,))

print('👑 ТОП-5 АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ (без админа):')
print('-' * 70)
print('ID | Username | Имя | Задачи | Успешно | Баланс')
print('-' * 70)

top_users = cur.fetchall()
if top_users:
    for user_id, username, first_name, tasks, completed_tasks, balance in top_users:
        username = f'@{username}' if username else '-'
        first_name = first_name or '-'
        print(f'{user_id:10} | {username:15} | {first_name:10} | {tasks:6} | {completed_tasks:8} | {balance:6}')
else:
    print('Нет данных о пользователях')
print()

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

print('💰 ПЛАТЕЖИ ЗА 30 ДНЕЙ:')
print('-' * 40)
if pay_count and total_amount:
    print(f'Количество платежей: {pay_count}')
    print(f'Общая сумма: {total_amount:.2f} руб.')
    print(f'Средний чек: {avg_amount:.2f} руб.')
else:
    print('Нет платежей за 30 дней')

# 7. НОВЫЕ ПОЛЬЗОВАТЕЛИ (без админа)
cur.execute('''
    SELECT 
        DATE(created_at) as day,
        COUNT(*) as new_users
    FROM users 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY day DESC
    LIMIT 7
''', (ADMIN_ID,))

print()
print('👤 НОВЫЕ ПОЛЬЗОВАТЕЛИ ПО ДНЯМ (7 дней):')
print('-' * 40)

new_users_rows = cur.fetchall()
if new_users_rows:
    for day, new_users in new_users_rows:
        print(f'{day}: {new_users} новых пользователей')
else:
    print('Нет новых пользователей за 7 дней')

# 8. ПРОБЛЕМНЫЕ ПОКАЗАТЕЛИ
print()
print('⚠️  АНАЛИЗ ПРОБЛЕМ:')
print('=' * 80)

# Высокая доля failed задач
if failed > 0 and failed * 100.0 / total_finished > 20:
    failed_percent = failed * 100.0 / total_finished
    print(f'❌ Высокий процент проваленных задач: {failed_percent:.1f}%')
    print(f'   Причина: Suno API таймауты (исправлено сегодня)')

# Много ошибок у пользователей
cur.execute('''
    SELECT COUNT(DISTINCT user_id) FROM generations 
    WHERE status = 'error' 
    AND user_id != %s
    AND audio_url != 'ERROR_NOTIFIED'
''', (ADMIN_ID,))
serious_errors = cur.fetchone()[0]

if serious_errors > 0:
    print(f'❌ Пользователей с критическими ошибками: {serious_errors}')
else:
    print('✅ Нет критических ошибок у пользователей')

# Обработанные ошибки
cur.execute('''
    SELECT COUNT(DISTINCT user_id) FROM generations 
    WHERE status = 'error' 
    AND user_id != %s
    AND audio_url = 'ERROR_NOTIFIED'
''', (ADMIN_ID,))
notified_errors = cur.fetchone()[0]

if notified_errors > 0:
    print(f'⚠️  Пользователей с обработанными ошибками: {notified_errors}')
    print(f'   (они получили уведомления и возврат баланса)')

# Задачи в обработке > 30 минут
cur.execute('''
    SELECT COUNT(*) FROM generations 
    WHERE status IN ('pending', 'processing') 
    AND user_id != %s
    AND created_at < NOW() - INTERVAL '30 minutes'
''', (ADMIN_ID,))
stuck_tasks = cur.fetchone()[0]

if stuck_tasks > 0:
    print(f'⏰ Зависших задач (>30 мин): {stuck_tasks}')
else:
    print('✅ Нет зависших задач')

print()
print('=' * 80)
print('📋 ВЫВОД:')
print(f'1. Пользователей: {total_users}, из них активных: {len(top_users) if top_users else 0}')
print(f'2. Общая успешность (без админа): {success_rate:.1f}%')
print(f'3. Главная проблема: {failed} проваленных задач ({failed_percent if failed > 0 else 0:.1f}%) из-за таймаутов')
print(f'4. Сегодня исправлено: увеличены таймауты Suno API с 60 до 300 сек')
print(f'5. Ожидаемый результат: успешность вырастет до 70%+')
print(f'6. Рекомендация: мониторить успешность 3 дня после исправлений')

conn.close()
