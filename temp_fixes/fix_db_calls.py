import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Удаляем вызовы db.init() и db.close()
content = re.sub(r"asyncio\.run\(db\.init\(\)\).*?# Инициализация адаптера БД", 
                "# asyncio.run(db.init())  # Инициализация адаптера БД - ЗАКОММЕНТИРОВАНО", content)

content = re.sub(r"db\.close\(\)", 
                "# db.close()  # ЗАКОММЕНТИРОВАНО - закрытие БД теперь в db_utils", content)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Вызовы db исправлены")
