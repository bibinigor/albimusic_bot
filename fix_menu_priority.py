import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Список обработчиков главного меню, которые должны работать в любом состоянии
menu_handlers = [
    '@dp.message_handler(lambda message: message.text == "💰 Баланс")',
    '@dp.message_handler(lambda message: message.text == "🎵 Примеры песен")', 
    '@dp.message_handler(lambda message: message.text == "👨‍💻 Админ панель")',
    '@dp.message_handler(lambda message: message.text == "🎵 Создать песню")',
    '@dp.message_handler(lambda message: message.text == "🎵 Создать музыку")'
]

for handler in menu_handlers:
    # Ищем и добавляем state="*"
    pattern = handler.replace('(', '\(').replace(')', '\)').replace('[', '\[').replace(']', '\]')
    new_handler = handler.replace(')', ', state="*")')
    
    if handler in content:
        content = content.replace(handler, new_handler)
        print(f"✅ Обновлен: {handler}")

with open('main_with_payments.py', 'w') as f:
    f.write(content)

print("✅ Обработчики главного меню теперь имеют приоритет над состояниями FSM")
