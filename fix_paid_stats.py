import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Найдем и заменим неправильный SQL запрос для paid_generations_7days
wrong_sql = '''        # 5. Платных генераций за 7 дней (не free)
        paid_7days_result = await fetch_query("""
            SELECT COUNT(*) as total 
            FROM generations 
            WHERE (is_free = false OR is_free IS NULL) 
            AND created_at >= NOW() - INTERVAL '7 days'
        """)'''

correct_sql = '''        # 5. Платежей за 7 дней (из таблицы payments)
        paid_7days_result = await fetch_query("""
            SELECT COUNT(*) as total 
            FROM payments 
            WHERE status = 'succeeded' 
            AND created_at >= NOW() - INTERVAL '7 days'
        """)'''

if wrong_sql in content:
    content = content.replace(wrong_sql, correct_sql)
    print("✅ SQL запрос для платных генераций исправлен (теперь считает платежи)")
    
    # Также нужно обновить комментарий в return
    content = content.replace(
        "'paid_generations_7days': paid_generations_7days,",
        "'paid_generations_7days': paid_generations_7days,  # На самом деле: платежи за 7 дней"
    )
else:
    print("⚠️ Не найден старый SQL запрос")

# Также исправим текст в статистике для ясности
content = content.replace(
    '💰 Платных за 7 дней: {stats[\'paid_generations_7days\']}',
    '💰 Платежей за 7 дней: {stats[\'paid_generations_7days\']}'
)

# Сохраняем
with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Статистика платежей исправлена")
print("Теперь считаются УСПЕШНЫЕ платежи (status = 'succeeded') из таблицы payments")
