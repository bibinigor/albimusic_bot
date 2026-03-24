import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем есть ли уже executor
if "executor.start_polling" not in content and "dp.start_polling" not in content:
    # Добавляем импорт если его нет
    if "from aiogram import executor" not in content:
        import_match = re.search(r"from aiogram\.\w+ import", content)
        if import_match:
            import_pos = import_match.end()
            content = content[:import_pos] + "\nfrom aiogram import executor" + content[import_pos:]
    
    # Добавляем запуск polling в конец файла перед if __name__
    if "__name__ == '__main__':" in content:
        main_start = content.find("if __name__ == '__main__':")
        # Находим отступ для добавления кода перед if __name__
        content = content[:main_start] + "\n\n# Запуск бота\nif __name__ == '__main__':\n    import asyncio\n    asyncio.run(main())\n\n" + content[main_start:]
    
    # Или добавляем простой запуск если не нашли подходящее место
    content += "\n\n# Запуск бота\nif __name__ == '__main__':\n    from aiogram import executor\n    executor.start_polling(dp, skip_updates=True)\n"

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Добавлен запуск polling для бота")
