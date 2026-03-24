import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем импорт executor если его нет
if "from aiogram import executor" not in content:
    # Находим место после других импортов aiogram
    import re
    aiogram_imports = list(re.finditer(r"from aiogram", content))
    if aiogram_imports:
        last_import = aiogram_imports[-1]
        insert_pos = content.find("\n", last_import.end())
        if insert_pos != -1:
            content = content[:insert_pos] + "\nfrom aiogram import executor" + content[insert_pos:]

# Добавляем запуск polling если его нет
if "executor.start_polling" not in content:
    # Находим место после запуска FastAPI
    fastapi_pos = content.find("fastapi_thread.start()")
    if fastapi_pos != -1:
        line_end = content.find("\n", fastapi_pos)
        if line_end != -1:
            polling_code = '''\n    \n    # Запуск Telegram бота\n    logging.info("🤖 Запуск polling для Telegram бота...")\n    executor.start_polling(dp, skip_updates=True)'''
            content = content[:line_end] + polling_code + content[line_end:]

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Polling добавлен безопасно")
