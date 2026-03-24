import re

with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим строку 1445 и добавляем очистку после неё
old = '''    lyrics = message.text

    if len(lyrics) > 3000:'''

new = '''    lyrics = message.text
    
    # Убираем "Текст:" если пользователь добавил его в начале
    lyrics = re.sub(r'^Текст:\s*', '', lyrics, flags=re.IGNORECASE).strip()

    if len(lyrics) > 3000:'''

content = content.replace(old, new)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Очистка 'Текст:' добавлена")

