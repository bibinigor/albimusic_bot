import re

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Находим обработчик /start
pattern = r'(@dp\.message_handler\(Command\(\'start\'\)\).*?async def cmd_start\(message: types\.Message\):)'

def add_state_reset(match):
    handler_def = match.group(0)
    # Добавляем сброс состояния после определения функции
    return handler_def + "\n    # Сброс состояния FSM при команде /start\n    from aiogram.dispatcher import FSMContext\n    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)\n    await state.finish()\n"

# Заменяем
new_content = re.sub(pattern, add_state_reset, content, flags=re.DOTALL)

with open('main_with_payments.py', 'w') as f:
    f.write(new_content)

print("✅ Добавлен сброс состояния FSM в обработчик /start")
