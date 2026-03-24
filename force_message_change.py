#!/usr/bin/env python3
"""
Сильно меняем сообщение чтобы обойти кэш
"""

with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Полностью меняем блок сообщения
old_block = '''        await message.answer(
            "✅ *Ваша песня опубликована в канале!*\\n\\n" +
            f"📝 Ваш комментарий: *{comment}*\\n\\n" +
            "📢 *Посмотреть в канале:* @ALBImusic_chart\\n\\n" +
            "Спасибо за участие в нашем музыкальном сообществе! 🎶", 
            parse_mode="Markdown"
        )'''

new_block = '''        await message.answer(
            f"🎉 *Отлично! Песня размещена в нашем канале!*\\n\\n" +
            f"💬 *Ваш комментарий:* {comment}\\n\\n" +
            f"📢 *Смотреть в канале:* @ALBImusic_chart\\n\\n" +
            f"Спасибо что делитесь творчеством с сообществом! 🎵", 
            parse_mode="Markdown"
        )'''

content = content.replace(old_block, new_block)

with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Сообщение полностью изменено!")
