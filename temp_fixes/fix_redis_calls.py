import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Закомментируем вызов init_redis()
content = re.sub(r"init_redis\(\)\s*# Инициализация Redis", 
                "# init_redis()  # Инициализация Redis - ЗАКОММЕНТИРОВАНО", content)

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Вызов init_redis исправлен")
