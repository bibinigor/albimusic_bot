with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем UPDATE на DELETE после отправки ответа
old = '''        execute_query_sync(
            "UPDATE support_messages SET replied = TRUE, reply_text = %s WHERE id = %s",
            (reply_text, msg_id)
        )'''

new = '''        # Удаляем сообщение после ответа (не копим отвеченные)
        execute_query_sync(
            "DELETE FROM support_messages WHERE id = %s",
            (msg_id,)
        )'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Автоудаление отвеченных сообщений добавлено")
