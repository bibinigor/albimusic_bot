import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим конец функции main или конец файла
if "executor.start_polling" not in content and "dp.start_polling" not in content:
    # Добавляем импорт executor если его нет
    if "from aiogram import executor" not in content:
        # Находим место после других импортов aiogram
        aiogram_imports = re.finditer(r"from aiogram", content)
        last_aiogram_import = None
        for match in aiogram_imports:
            last_aiogram_import = match.end()
        
        if last_aiogram_import:
            content = content[:last_aiogram_import] + "\nfrom aiogram import executor" + content[last_aiogram_import:]
        else:
            # Если не нашли, добавляем в начало импортов
            content = content.replace(
                "from aiogram.dispatcher.filters import Command",
                "from aiogram.dispatcher.filters import Command\nfrom aiogram import executor"
            )
    
    # Находим место где закомментирован запуск бота и добавляем executor
    # Ищем конец файла после запуска FastAPI
    fastapi_thread_pattern = r"fastapi_thread\.start\(\)\s*(.*?)(?=\n\n|\nif|\Z)"
    match = re.search(fastapi_thread_pattern, content, re.DOTALL)
    
    if match:
        after_fastapi = match.end()
        polling_code = '''
    # Запуск Telegram бота
    logging.info("🤖 Запуск Telegram бота...")
    executor.start_polling(dp, skip_updates=True)
'''
        content = content[:after_fastapi] + polling_code + content[after_fastapi:]
    else:
        # Альтернативный вариант - добавляем в конец
        content += "\n\n# Запуск Telegram бота\nexecutor.start_polling(dp, skip_updates=True)\n"

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлен запуск polling для фонового режима")
