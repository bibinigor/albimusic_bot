import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Обработчики, которые запускают состояния - НЕ должны иметь state="*"
state_starting_handlers = [
    '@dp.message_handler(lambda message: message.text == "🎵 Создать песню", state="*")'
]

for handler in state_starting_handlers:
    # Убираем state="*"
    fixed_handler = handler.replace(', state="*"', '')
    
    if handler in content:
        content = content.replace(handler, fixed_handler)
        print(f"✅ Исправлен: {handler} -> {fixed_handler}")

with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Обработчики запуска состояний исправлены")
