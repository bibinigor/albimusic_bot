#!/usr/bin/env python3
import re

print("=== ПРИМЕНЕНИЕ ВСЕХ ИЗМЕНЕНИЙ ===")

# 1. ИЗМЕНЕНИЕ: Реферальный бонус 3 → 2
print("\n1. Меняем реферальный бонус с 3 на 2 генерации...")

with open('main_with_payments.py', 'r') as f:
    content = f.read()

# Все замены для рефералов
changes = [
    ('+3 бесплатно', '+2 бесплатно'),
    ('3 генерации бесплатно', '2 генерации бесплатно'),
    ('Пригласите друга = +3', 'Пригласите друга = +2'),
    ('подарим вам 3 генерации', 'подарим вам 2 генерации'),
    ('balance = balance + 3', 'balance = balance + 2'),
    ('Вам начислено 3 бесплатные', 'Вам начислено 2 бесплатные')
]

for old, new in changes:
    if old in content:
        content = content.replace(old, new)
        print(f"   ✅ {old} → {new}")

# 2. ИЗМЕНЕНИЕ: Новое приветственное сообщение
print("\n2. Обновляем приветственное сообщение...")
new_welcome = '''🎵 *Привет! Я AlBi-music — твой личный композитор с искусственным интеллектом!*

🔥 Попробуй создать песню **БЕСПЛАТНО**! 

• 🎵 Можешь создать любую музыку под настроение (для видеоролика или для тренировки или медитации!
• 🔥 А можешь дать мне стихи и я создам тебе классную песню! 

🚀 Прямо сейчас нажми «Создать песню»!'''

# Находим старое приветствие
old_welcome_pattern = r'welcome_text = ".*?"'
old_welcome_match = re.search(old_welcome_pattern, content, re.DOTALL)

if old_welcome_match:
    content = content.replace(old_welcome_match.group(0), f'welcome_text = """{new_welcome}"""')
    print("   ✅ Приветствие обновлено")
else:
    print("   ⚠️ Старое приветствие не найдено")

# Сохраняем основной файл
with open('main_with_payments.py', 'w') as f:
    f.write(content)

# 3. ИЗМЕНЕНИЕ: Кнопки в мониторинге
print("\n3. Обновляем кнопки в мониторинге...")
with open('run_monitor_notify.py', 'r') as f:
    monitor_content = f.read()

# Заменяем кнопку
monitor_content = monitor_content.replace('Разместить в канале', 'Разместить в канале ALBImusic Chart')

# Добавляем вторую кнопку
button_pattern = r'keyboard\.add\(InlineKeyboardButton\("📢 Разместить в канале ALBImusic Chart".*?\)\)'
if re.search(button_pattern, monitor_content):
    replacement = '''keyboard.add(InlineKeyboardButton("📢 Разместить в канале ALBImusic Chart", callback_data=f"post_{task_id}"))
        keyboard.add(InlineKeyboardButton("✅ Перейти в канал ALBImusic Chart", url="https://t.me/ALBImusic_Chart"))'''
    monitor_content = re.sub(button_pattern, replacement, monitor_content)
    print("   ✅ Кнопки в мониторинге обновлены")

with open('run_monitor_notify.py', 'w') as f:
    f.write(monitor_content)

print("\n=== ВСЕ ИЗМЕНЕНИЯ ПРИМЕНЕНЫ ===")
print("Осталось перезапустить сервисы...")
