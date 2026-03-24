#!/bin/bash
echo "🔄 Исправление для получения 2 ссылок от Suno"

# Создаем бэкапы
BACKUP="/root/albimusic-bot/backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"
cp /root/albimusic-bot/celery_tasks.py "$BACKUP/"
cp /root/albimusic-bot/run_monitor_notify.py "$BACKUP/"
cp /root/albimusic-bot/main_with_payments.py "$BACKUP/"
echo "✅ Бэкапы: $BACKUP"

# ================= 1. celery_tasks.py =================
echo ""
echo "1. Исправляем celery_tasks.py..."

# Находим точный блок для замены
python3 << 'ENDPYTHON'
import re

with open('/root/albimusic-bot/celery_tasks.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем блок с audio_data[0]
for i, line in enumerate(lines):
    if 'audio_url = audio_data[0].get(' in line and "'audioUrl'" in line:
        print(f"Найдена строка {i+1}: {line.strip()}")
        
        # Нужно заменить от строки i до строки с return audio_url
        new_block = '''                        # Получаем ВСЕ ссылки из массива sunoData
                        audio_urls = []
                        for item in audio_data:
                            url = item.get('audioUrl')
                            if url:
                                audio_urls.append(url)
                        
                        if not audio_urls:
                            logger.error(f"[{request_id}] ❌ Нет валидных audio URL в ответе")
                            return None
                        
                        logger.info(f"[{request_id}] ✅ SUNO GENERATION COMPLETED:")
                        logger.info(f"[{request_id}]    • Получено {len(audio_urls)} аудио-ссылок")
                        
                        # Валидация каждой ссылки
                        for i, url in enumerate(audio_urls, 1):
                            logger.info(f"[{request_id}]    • Версия {i}: {url}")
                            if not validate_audio_url(url, request_id):
                                logger.error(f"[{request_id}] ❌ Версия {i} не прошла валидацию")
                                return None
                        
                        # Возвращаем JSON массив
                        audio_url = json.dumps(audio_urls, ensure_ascii=False)
                        logger.info(f"[{request_id}]    • Сохраняем как JSON: {audio_url}")'''
        
        # Заменяем строку i на новый блок
        lines[i] = new_block + '\n'
        
        # Удаляем старые строки после этого (до return audio_url)
        j = i + 1
        while j < len(lines):
            if 'return audio_url' in lines[j]:
                lines[j] = '                        return audio_url\n'
                break
            j += 1
        
        break

with open('/root/albimusic-bot/celery_tasks.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ celery_tasks.py исправлен")
ENDPYTHON

# Проверяем синтаксис
if python3 -m py_compile /root/albimusic-bot/celery_tasks.py 2>/dev/null; then
    echo "✅ Синтаксис celery_tasks.py OK"
else
    echo "❌ Ошибка в celery_tasks.py"
    echo "Восстанавливаем..."
    cp "$BACKUP/celery_tasks.py" /root/albimusic-bot/celery_tasks.py
    exit 1
fi

# ================= 2. run_monitor_notify.py =================
echo ""
echo "2. Исправляем run_monitor_notify.py..."

# Находим и заменяем функцию send_telegram_notification
python3 << 'ENDPYTHON'
import re

with open('/root/albimusic-bot/run_monitor_notify.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем импорт json
if 'import json' not in content:
    # Добавляем импорт после других импортов
    content = content.replace('import logging', 'import logging\nimport json')

# Заменяем весь блок кнопок для скачивания
# Ищем старый блок
old_button_block = '''keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Скачать MP3", url=audio_url)],
                [InlineKeyboardButton(text="📢 Разместить в канале ALBI Music Chart", callback_data=f"post_{task_id}")],
                [InlineKeyboardButton(text="🎵 Создать новую композицию", callback_data="create_new")]
            ])'''

new_button_block = '''        # Парсим audio_url (JSON или обычная строка)
        audio_urls = []
        
        if audio_url and audio_url.startswith('['):
            try:
                import json
                audio_urls = json.loads(audio_url)
            except:
                audio_urls = [audio_url]
        else:
            audio_urls = [audio_url] if audio_url else []
        
        # Создаём кнопки для каждой версии
        buttons = []
        
        for i, url in enumerate(audio_urls, 1):
            button_text = f"🔗 Скачать Версию {i}" if len(audio_urls) > 1 else "🔗 Скачать MP3"
            buttons.append([InlineKeyboardButton(text=button_text, url=url)])
        
        buttons.append([InlineKeyboardButton(text="📢 Разместить в канале ALBI Music Chart", callback_data=f"post_{task_id}")])
        buttons.append([InlineKeyboardButton(text="🎵 Создать новую композицию", callback_data="create_new")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)'''

content = content.replace(old_button_block, new_button_block)

with open('/root/albimusic-bot/run_monitor_notify.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ run_monitor_notify.py исправлен")
ENDPYTHON

if python3 -m py_compile /root/albimusic-bot/run_monitor_notify.py 2>/dev/null; then
    echo "✅ Синтаксис run_monitor_notify.py OK"
else
    echo "❌ Ошибка в run_monitor_notify.py"
    cp "$BACKUP/run_monitor_notify.py" /root/albimusic-bot/run_monitor_notify.py
    exit 1
fi

# ================= 3. main_with_payments.py =================
echo ""
echo "3. Исправляем main_with_payments.py..."

python3 << 'ENDPYTHON'
with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем функцию send_to_channel и заменяем первую строку
# Заменяем блок получения первой ссылки
old_code = '''async def send_to_channel(audio_url, comment, user_info):
    """Отправка трека в канал ALBI Music Chart"""
    try:'''

new_code = '''async def send_to_channel(audio_url, comment, user_info):
    """Отправка трека в канал ALBI Music Chart"""
    try:
        # Берём первую ссылку (поддержка JSON и старого формата)
        if audio_url and audio_url.startswith('['):
            try:
                import json
                audio_urls = json.loads(audio_url)
                first_audio_url = audio_urls[0]
            except:
                first_audio_url = audio_url
        else:
            first_audio_url = audio_url'''

# Простая замена первой части
content = content.replace(old_code, new_code)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ main_with_payments.py исправлен")
ENDPYTHON

if python3 -m py_compile /root/albimusic-bot/main_with_payments.py 2>/dev/null; then
    echo "✅ Синтаксис main_with_payments.py OK"
else
    echo "❌ Ошибка в main_with_payments.py"
    cp "$BACKUP/main_with_payments.py" /root/albimusic-bot/main_with_payments.py
    exit 1
fi

echo ""
echo "========================================="
echo "✅ ВСЕ ИСПРАВЛЕНИЯ УСПЕШНО ПРИМЕНЕНЫ!"
echo "========================================="
echo ""
echo "Перезапустите сервисы:"
echo "sudo systemctl restart albimusic-celery"
echo "sudo systemctl restart albimusic-bot"
echo "sudo systemctl restart albimusic-monitor"
