with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Показываем только неотвеченные сообщения
old = '''        messages = execute_query_sync(
            """SELECT id, user_id, username, first_name, message, replied, created_at
               FROM support_messages
               ORDER BY replied ASC, created_at DESC
               LIMIT 5 OFFSET %s""",
            (offset,)
        )'''

new = '''        messages = execute_query_sync(
            """SELECT id, user_id, username, first_name, message, replied, created_at
               FROM support_messages
               WHERE replied = FALSE
               ORDER BY created_at DESC
               LIMIT 5 OFFSET %s""",
            (offset,)
        )'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Поддержка теперь показывает только неотвеченные")
