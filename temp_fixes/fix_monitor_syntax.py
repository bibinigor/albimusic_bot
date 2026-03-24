with open('run_monitor_pro.py', 'r') as f:
    content = f.read()

# Исправляем проблемную строку
content = content.replace(
    "            tasks = result = execute_query_sync(\\n                'SELECT task_id, user_id, audio_url, prompt FROM generations WHERE status = $1 AND notified = $2',\\n                'completed', False)\\n            )",
    "            result = execute_query_sync(\\n                'SELECT task_id, user_id, audio_url, prompt FROM generations WHERE status = %s AND notified = %s',\\n                ('completed', False)\\n            )\\n            tasks = result if result else []"
)

with open('run_monitor_pro.py', 'w') as f:
    f.write(content)

print('✅ Синтаксическая ошибка исправлена')
