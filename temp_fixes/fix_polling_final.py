import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Убираем проблемный код с потоками
content = re.sub(r'# Запуск Telegram бота в отдельном потоке.*?bot_thread\.start\(\)', '', content, flags=re.DOTALL)

# Находим правильное место для запуска polling - заменяем запуск Uvicorn на комбинированный
# Находим запуск FastAPI
fastapi_start = content.find("fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)")
if fastapi_start != -1:
    # Заменяем весь блок запуска на комбинированный вариант
    old_code = '''fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Запуск Telegram бота в отдельном потоке
    import threading
    def start_bot():
        from aiogram import executor
        executor.start_polling(dp, skip_updates=True)
    
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    logging.info("🤖 Telegram бот запущен в отдельном потоке")'''
    
    new_code = '''# Запуск FastAPI в отдельном потоке
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Запуск Telegram бота в основном потоке
    logging.info("🤖 Запуск Telegram бота...")
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)'''
    
    content = content.replace(old_code, new_code)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлен запуск бота")
