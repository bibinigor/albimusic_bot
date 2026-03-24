import psycopg2
from datetime import datetime, timedelta

conn = psycopg2.connect(
    dbname='albimusic_bot',
    user='albimusic_user',
    password='aXAnAixKT6@?B9',
    host='localhost'
)
cur = conn.cursor()

print('📊 AlBi-music Bot - СТАТИСТИКА ЗА ПОСЛЕДНИЕ 3 ДНЯ')
print('(после исправления таймаутов 17.12.2025)')
print('=' * 80)

ADMIN_ID = 338544009
DAYS = 3

# 1. ОБЩАЯ СТАТИСТИКА ЗА 3 ДНЯ (без админа)
cur.execute('''
    SELECT COUNT(DISTINCT user_id) 
    FROM generations 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '%s days'
''', (ADMIN_ID, DAYS))

active_users = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(*) 
    FROM generations 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '%s days'
''', (ADMIN_ID, DAYS))

total_tasks = cur.fetchone()[0]

print(f'👥 Активных пользователей за {DAYS} дня: {active_users}')
print(f'🎵 Всего задач за {DAYS} дня: {total_tasks}')
print()

# 2. СТАТИСТИКА ПО СТАТУСАМ ЗА 3 ДНЯ
cur.execute('''
    SELECT 
        status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM generations 
               WHERE user_id != %s AND created_at > NOW() - INTERVAL '%s days'), 1) as percent
    FROM generations 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '%s days'
    GROUP BY status
    ORDER BY count DESC
''', (ADMIN_ID, DAYS, ADMIN_ID, DAYS))

print(f'📈 СТАТУСЫ ЗАДАЧ ЗА {DAYS} ДНЯ (без админа):')
print('-' * 40)

status_translation = {
    'failed': 'Провалено',
    'completed': 'Успешно',
    'error': 'Ошибка',
    'pending': 'В ожидании',
    'processing': 'В процессе'
}

rows = cur.fetchall()
for status, count, percent in rows:
    status_ru = status_translation.get(status, status)
    print(f'{status_ru:15} : {count:4} ({percent}%)')
print()

# 3. УСПЕШНОСТЬ ЗА 3 ДНЯ
cur.execute('''
    SELECT 
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
    FROM generations 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '%s days'
    AND status IN ('completed', 'error', 'failed')
''', (ADMIN_ID, DAYS))

completed, errors, failed = cur.fetchone()
total_finished = completed + errors + failed

if total_finished > 0:
    success_rate = completed * 100.0 / total_finished
    
    print(f'🎯 УСПЕШНОСТЬ ЗА {DAYS} ДНЯ (без админа):')
    print('-' * 40)
    print(f'✅ Успешно: {completed}')
    print(f'❌ Ошибки: {errors}')
    print(f'⏰ Провалено (таймаут): {failed}')
    print(f'📊 Всего завершено: {total_finished}')
    print(f'🎯 Успешность: {success_rate:.1f}%')
    
    # Для сравнения - успешность за предыдущие 3 дня
    cur.execute('''
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_old,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as errors_old,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_old
        FROM generations 
        WHERE user_id != %s
        AND created_at BETWEEN NOW() - INTERVAL '6 days' AND NOW() - INTERVAL '3 days'
        AND status IN ('completed', 'error', 'failed')
    ''', (ADMIN_ID,))
    
    completed_old, errors_old, failed_old = cur.fetchone()
    total_old = completed_old + errors_old + failed_old
    
    if total_old > 0:
        success_rate_old = completed_old * 100.0 / total_old
        print()
        print('📊 СРАВНЕНИЕ С ПРЕДЫДУЩИМИ 3 ДНЯМИ:')
        print('-' * 40)
        print(f'📅 Предыдущие 3 дня (до исправлений):')
        print(f'   Успешно: {completed_old}, Провалено: {failed_old}')
        print(f'   Успешность: {success_rate_old:.1f}%')
        print()
        print(f'📅 Последние 3 дня (после исправлений):')
        print(f'   Успешно: {completed}, Провалено: {failed}')
        print(f'   Успешность: {success_rate:.1f}%')
        print()
        
        if success_rate > success_rate_old:
            improvement = success_rate - success_rate_old
            print(f'📈 УЛУЧШЕНИЕ: +{improvement:.1f}%')
        else:
            print('⚠️  Улучшений пока не видно (нужно больше времени)')
    
else:
    print(f'Нет завершенных задач за {DAYS} дня')
print()

# 4. РАСПРЕДЕЛЕНИЕ ПО ДНЯМ
cur.execute('''
    SELECT 
        DATE(created_at) as day,
        COUNT(*) as tasks,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
        COUNT(DISTINCT user_id) as active_users
    FROM generations 
    WHERE user_id != %s
    AND created_at > NOW() - INTERVAL '%s days'
    GROUP BY DATE(created_at)
    ORDER BY day DESC
''', (ADMIN_ID, DAYS))

print(f'📅 РАСПРЕДЕЛЕНИЕ ПО ДНЯМ (за {DAYS} дня):')
print('-' * 60)
print('Дата       | Задачи | Успешно | Провалено | Пользователей | Успешность')
print('-' * 60)

days_data = cur.fetchall()
for day, tasks, completed_day, failed_day, users in days_data:
    success_rate_day = completed_day * 100.0 / tasks if tasks > 0 else 0
    failed_percent_day = failed_day * 100.0 / tasks if tasks > 0 else 0
    print(f'{day} | {tasks:6} | {completed_day:7} | {failed_day:8} | {users:12} | {success_rate_day:.1f}%')

print()

# 5. ТИПЫ ОШИБОК
print('🔍 АНАЛИЗ ОШИБОК ЗА 3 ДНЯ:')
print('-' * 40)

# Failed с timeout_auto_cleanup
cur.execute('''
    SELECT COUNT(*) FROM generations 
    WHERE user_id != %s
    AND status = 'failed'
    AND audio_url = 'timeout_auto_cleanup'
    AND created_at > NOW() - INTERVAL '%s days'
''', (ADMIN_ID, DAYS))

timeout_fails = cur.fetchone()[0]

# Errors с ERROR_NOTIFIED
cur.execute('''
    SELECT COUNT(*) FROM generations 
    WHERE user_id != %s
    AND status = 'error'
    AND audio_url = 'ERROR_NOTIFIED'
    AND created_at > NOW() - INTERVAL '%s days'
''', (ADMIN_ID, DAYS))

notified_errors = cur.fetchone()[0]

# Другие ошибки
cur.execute('''
    SELECT COUNT(*) FROM generations 
    WHERE user_id != %s
    AND status = 'error'
    AND audio_url != 'ERROR_NOTIFIED'
    AND audio_url IS NOT NULL
    AND created_at > NOW() - INTERVAL '%s days'
''', (ADMIN_ID, DAYS))

other_errors = cur.fetchone()[0]

print(f'⏰ Таймауты (failed): {timeout_fails}')
print(f'⚠️  Обработанные ошибки (error): {notified_errors}')
print(f'❌ Другие ошибки: {other_errors}')

if timeout_fails > 0:
    timeout_percent = timeout_fails * 100.0 / failed if failed > 0 else 0
    print(f'   ({timeout_percent:.1f}% от всех проваленных задач)')

print()

# 6. ВЫВОД И РЕКОМЕНДАЦИИ
print('=' * 80)
print('📋 ВЫВОД ПО ИСПРАВЛЕНИЯМ ТАЙМАУТОВ:')
print('-' * 80)

if total_finished > 0:
    failed_percent = failed * 100.0 / total_finished
    
    if failed_percent > 50:
        print('❌ КРИТИЧЕСКАЯ СИТУАЦИЯ:')
        print(f'   {failed_percent:.1f}% задач проваливаются!')
        print('   Исправления таймаутов НЕ помогли')
        print('   Нужно: увеличить таймауты еще больше или проверить Suno API')
    
    elif failed_percent > 20:
        print('⚠️  ПРОБЛЕМА ЕСТЬ:')
        print(f'   {failed_percent:.1f}% задач проваливаются')
        print('   Исправления помогли частично')
        print('   Нужно: мониторить еще 2-3 дня')
    
    elif failed_percent > 0:
        print('✅ УЛУЧШЕНИЯ ЕСТЬ:')
        print(f'   Только {failed_percent:.1f}% задач проваливаются')
        print('   Исправления таймаутов работают!')
    
    else:
        print('🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ!')
        print('   0% проваленных задач за 3 дня!')
        print('   Исправления таймаутов полностью решили проблему!')
    
    print()
    print('📊 РЕКОМЕНДАЦИИ:')
    print('1. Мониторить успешность еще 3 дня')
    print('2. Если failed > 20% - увеличить таймаут до 600 секунд')
    print('3. Проверить логи Celery на предмет ошибок Suno API')
    print('4. Убедиться, что скрипт cleanup_stuck_tasks.py работает с 45 минутами')

else:
    print('ℹ️  Нет данных для анализа за последние 3 дня')
    print('   Дождитесь активности пользователей')

conn.close()
