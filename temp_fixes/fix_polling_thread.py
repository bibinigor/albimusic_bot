import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Убираем наш предыдущий код из конца файла
content = re.sub(r'# Запуск Telegram бота.*?executor\.start_polling.*?skip_updates=True\)', '', content, flags=re.DOTALL)

# Находим место после запуска FastAPI и добавляем запуск polling в отдельном потоке
fastapi_pos = content.find("fastapi_thread.start()")
if fastapi_pos != -1:
    line_end = content.find("\n", fastapi_pos)
    if line_end != -1:
        polling_code = '''\n    \n    # Запуск Telegram бота в отдельном потоке\n    import threading\n    def start_bot():\n        from aiogram import executor\n        executor.start_polling(dp, skip_updates=True)\n    \n    bot_thread = threading.Thread(target=start_bot, daemon=True)\n    bot_thread.start()\n    logging.info("🤖 Telegram бот запущен в отдельном потоке")'''
        content = content[:line_end] + polling_code + content[line_end:]

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Polling добавлен в отдельном потоке")
