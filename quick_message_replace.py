#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

# Backup
backup = f"{FILE_PATH}.backup_simple_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(FILE_PATH, backup)
print(f"Backup: {backup}")

with open(FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем сообщение для песен
old_song_msg = '''        await callback_query.message.answer(
            f"✅ Выбран: {'Творческий' if mode == 'creative' else 'Точный'} режим\\n\\n"
            "🎵 Генерация песни началась!\\n"
            "⏱ Ожидайте 2-3 минуты..."
        )'''

new_msg = '''        await callback_query.message.answer(
            "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
        )'''

# Заменяем сообщение для музыки  
old_music_msg = '''        await callback_query.message.answer(
            f"✅ Выбран: {'Творческий' if mode == 'creative' else 'Точный'} режим\\n\\n"
            "🎵 Генерация музыки началась!\\n"
            "⏱ Ожидайте 2-3 минуты..."
        )'''

if old_song_msg in content:
    content = content.replace(old_song_msg, new_msg)
    print("✅ Заменено сообщение для песен")

if old_music_msg in content:
    content = content.replace(old_music_msg, new_msg)
    print("✅ Заменено сообщение для музыки")

with open(FILE_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Сообщения заменены")
print("Перезапуск бота: sudo systemctl restart albimusic-bot")
