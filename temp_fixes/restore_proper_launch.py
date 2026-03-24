import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим и заменяем неправильный запуск на правильный из бэкапа
# Находим блок с threading и запуском
threading_block_start = content.find("fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)")
if threading_block_start != -1:
    # Находим конец этого блока
    threading_block_end = content.find("executor.start_polling", threading_block_start)
    if threading_block_end != -1:
        # Находим конец строки с executor.start_polling
        block_end = content.find("\n", threading_block_end)
        
        # Заменяем весь блок на правильный запуск из бэкапа
        old_block = content[threading_block_start:block_end]
        
        new_block = '''# Запуск FastAPI в отдельном потоке
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Запуск Telegram бота (правильный способ из бэкапа)
    logging.info("🚀 Запуск AlBi-music Bot + Payments...")
    executor.start_polling(dp, skip_updates=True)'''
        
        content = content.replace(old_block, new_block)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Восстановлен правильный запуск из бэкапа")
