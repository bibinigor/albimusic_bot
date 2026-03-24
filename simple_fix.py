#!/usr/bin/env python3
"""
Простое исправление: добавляем определение generation_type
"""

import os
import shutil
from datetime import datetime

FILE_PATH = "/root/albimusic-bot/main_with_payments.py"

# Backup
backup = f"{FILE_PATH}.backup_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(FILE_PATH, backup)
print(f"Backup: {backup}")

with open(FILE_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим функцию
for i, line in enumerate(lines):
    if 'async def process_generation_mode' in line:
        print(f"Функция на строке {i+1}")
        
        # Находим state_data = await state.get_data()
        for j in range(i, min(i+20, len(lines))):
            if 'state_data = await state.get_data()' in lines[j]:
                print(f"state_data на строке {j+1}")
                
                # Вставляем умную логику после state_data
                smart_logic = [
                    '\n',
                    '        # ========== УМНОЕ ОПРЕДЕЛЕНИЕ ТИПА ==========\n',
                    '        lyrics = state_data.get("lyrics", "").strip()\n',
                    '        prompt = state_data.get("prompt", "").strip()\n',
                    '        explicit_type = state_data.get("generation_type", None)\n',
                    '\n',
                    '        if lyrics:\n',
                    '            generation_type = "song"\n',
                    '            logging.info(f"🎤 Detected SONG generation (lyrics: {len(lyrics)} chars)")\n',
                    '        elif prompt:\n',
                    '            generation_type = "music"\n',
                    '            logging.info(f"🎵 Detected MUSIC generation (prompt: {len(prompt)} chars)")\n',
                    '        elif explicit_type:\n',
                    '            generation_type = explicit_type\n',
                    '            logging.info(f"📋 Using explicit type: {explicit_type}")\n',
                    '        else:\n',
                    '            logging.error("❌ Cannot determine generation type!")\n',
                    '            await callback_query.message.answer(\n',
                    '                "❌ Ошибка: не удалось определить тип генерации\\n"\n',
                    '                "Попробуйте начать заново с 🎵 Создать песню"\n',
                    '            )\n',
                    '            await state.finish()\n',
                    '            return\n',
                    '\n',
                    '        style = state_data.get("style", "").strip()\n',
                ]
                
                # Вставляем после строки j
                lines[j+1:j+1] = smart_logic
                print(f"Добавлено {len(smart_logic)} строк после строки {j+1}")
                break
        break

with open(FILE_PATH, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Умная логика добавлена")

# Проверка синтаксиса
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', FILE_PATH],
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Синтаксис корректен")
    print("\nПерезапусти бота: sudo systemctl restart albimusic-bot")
else:
    print("❌ Ошибка синтаксиса:")
    print(result.stderr)
    print("\nВосстанавливаю из backup...")
    shutil.copy2(backup, FILE_PATH)
