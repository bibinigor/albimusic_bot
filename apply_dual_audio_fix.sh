#!/bin/bash
set -e

echo "🎵 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ: JSON для 2 аудио-ссылок"
echo "================================================================"

BACKUP_DIR="/root/albimusic-bot/backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Функция бэкапа
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        echo "✅ Бэкап создан: $(basename $file)"
    else
        echo "❌ Файл не найден: $file"
        exit 1
    fi
}

# Проверка синтаксиса
check_syntax() {
    local file=$1
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✅ Синтаксис корректен: $(basename $file)"
        return 0
    else
        echo "❌ ОШИБКА синтаксиса: $(basename $file)"
        python3 -m py_compile "$file"
        return 1
    fi
}

# Добавление import json
add_json_import() {
    local file=$1
    if ! grep -q "^import json" "$file"; then
        local first_import_line=$(grep -n "^import " "$file" | head -1 | cut -d: -f1)
        if [ -n "$first_import_line" ]; then
            sed -i "${first_import_line}i import json" "$file"
            echo "✅ Добавлен import json в $(basename $file)"
        fi
    else
        echo "⚠️  import json уже есть в $(basename $file)"
    fi
}

# ========================================
# 1. CELERY_TASKS.PY
# ========================================
echo ""
echo "================================================================"
echo "📝 1/3: Исправление celery_tasks.py"
echo "================================================================"

FILE_CELERY="/root/albimusic-bot/celery_tasks.py"
backup_file "$FILE_CELERY"
add_json_import "$FILE_CELERY"

# Находим строку для замены
LINE_NUM=$(grep -n "audio_url = audio_data\[0\]\.get('audioUrl')" "$FILE_CELERY" | cut -d: -f1)

if [ -z "$LINE_NUM" ]; then
    echo "❌ Не найдена строка для замены в celery_tasks.py"
    exit 1
fi

echo "🔍 Найдена строка $LINE_NUM"

# Используем Python для замены
python3 << ENDPYTHON
import json

with open('$FILE_CELERY', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем точный блок для замены
start_line = $LINE_NUM - 1
new_code = '''                        # Получаем ВСЕ ссылки из массива sunoData
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

# Заменяем от start_line до следующей строки с отступом
lines[start_line] = new_code + '\\n'
# Удаляем следующие 6 строк (старый блок)
del lines[start_line+1:start_line+7]

with open('$FILE_CELERY', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Блок заменён в celery_tasks.py")
ENDPYTHON

check_syntax "$FILE_CELERY" || exit 1

# ========================================
# 2. RUN_MONITOR_NOTIFY.PY
# ========================================
echo ""
echo "================================================================"
echo "📝 2/3: Исправление run_monitor_notify.py"
echo "================================================================"

FILE_MONITOR="/root/albimusic-bot/run_monitor_notify.py"
backup_file "$FILE_MONITOR"
add_json_import "$FILE_MONITOR"

# Находим функцию send_telegram_notification
FUNC_START=$(grep -n "async def send_telegram_notification" "$FILE_MONITOR" | cut -d: -f1)

if [ -z "$FUNC_START" ]; then
    echo "❌ Не найдена функция send_telegram_notification"
    exit 1
fi

echo "🔍 Найдена функция на строке $FUNC_START"

# Заменяем функцию через Python
python3 << ENDPYTHON
with open('$FILE_MONITOR', 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем начало функции до следующей функции
import re

# Паттерн для поиска функции
pattern = r'(async def send_telegram_notification\(.*?\):.*?)(?=\n(?:async def |def |\Z))'
match = re.search(pattern, content, re.DOTALL)

if match:
    new_func = '''async def send_telegram_notification(user_id, task_id, audio_url, is_song=False):
    """Отправка уведомления в Telegram о готовности генерации"""
    try:
        import aiohttp
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        bot = Bot(token=config.BOT_TOKEN)
        
        language = 'ru'
        
        if language == 'ru':
            message_text = "🎵 Ваша музыка готова!"
            if is_song:
                message_text = "🎤 Ваша песня готова!"
        else:
            message_text = "🎵 Your music is ready!"
            if is_song:
                message_text = "🎤 Your song is ready!"
        
        # Парсим audio_url (JSON или обычная строка)
        audio_urls = []
        
        if audio_url and audio_url.startswith('['):
            try:
                audio_urls = json.loads(audio_url)
            except json.JSONDecodeError:
                logger.error(f"❌ Ошибка парсинга JSON: {audio_url}")
                audio_urls = [audio_url]
        else:
            # Обратная совместимость: старая одиночная ссылка
            audio_urls = [audio_url] if audio_url else []
        
        if not audio_urls:
            logger.error(f"❌ Нет audio_urls для пользователя {user_id}")
            return False
        
        # Создаём кнопки для каждой версии
        buttons = []
        
        for i, url in enumerate(audio_urls, 1):
            button_text = f"🔗 Скачать Версию {i}" if len(audio_urls) > 1 else "🔗 Скачать MP3"
            buttons.append([
                InlineKeyboardButton(text=button_text, url=url)
            ])
        
        buttons.append([
            InlineKeyboardButton(
                text="📢 Разместить в канале ALBI Music Chart",
                callback_data=f"post_{task_id}"
            )
        ])
        
        buttons.append([
            InlineKeyboardButton(
                text="🎵 Создать новую композицию",
                callback_data="create_new"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await bot.send_message(
            chat_id=user_id,
            text=message_text,
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Уведомление отправлено пользователю {user_id} ({len(audio_urls)} ссылок)")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False'''
    
    content = content.replace(match.group(1), new_func)
    
    with open('$FILE_MONITOR', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Функция заменена в run_monitor_notify.py")
else:
    print("❌ Не удалось найти функцию")
    exit(1)
ENDPYTHON

check_syntax "$FILE_MONITOR" || exit 1

# ========================================
# 3. MAIN_WITH_PAYMENTS.PY
# ========================================
echo ""
echo "================================================================"
echo "📝 3/3: Исправление main_with_payments.py"
echo "================================================================"

FILE_MAIN="/root/albimusic-bot/main_with_payments.py"
backup_file "$FILE_MAIN"
add_json_import "$FILE_MAIN"

# Находим функцию send_to_channel
FUNC_START=$(grep -n "async def send_to_channel" "$FILE_MAIN" | cut -d: -f1)

if [ -z "$FUNC_START" ]; then
    echo "❌ Не найдена функция send_to_channel"
    exit 1
fi

echo "🔍 Найдена функция на строке $FUNC_START"

# Заменяем функцию
python3 << ENDPYTHON
with open('$FILE_MAIN', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Ищем функцию send_to_channel
pattern = r'(async def send_to_channel\(.*?\):.*?)(?=\n(?:async def |def |\Z))'
match = re.search(pattern, content, re.DOTALL)

if match:
    new_func = '''async def send_to_channel(audio_url, comment, user_info):
    """Отправка трека в канал ALBI Music Chart"""
    try:
        # Парсим audio_url (JSON или обычная строка)
        if audio_url and audio_url.startswith('['):
            try:
                audio_urls = json.loads(audio_url)
                first_audio_url = audio_urls[0]
            except json.JSONDecodeError:
                logger.error(f"❌ Ошибка парсинга JSON: {audio_url}")
                first_audio_url = audio_url
        else:
            # Обратная совместимость
            first_audio_url = audio_url
        
        caption = (f"🎵 Новая композиция от пользователя!\\n\\n"
                   f"👤 Автор: {user_info}\\n"
                   f"💬 Комментарий: {comment}\\n\\n"
                   f"🔗 Скачать: {first_audio_url}\\n\\n"
                   f"🤖 Создано с помощью @albimusic_bot")
        
        message = await bot.send_audio(
            chat_id=config.CHANNEL_ID,
            audio=first_audio_url,
            caption=caption
        )
        
        logger.info(f"✅ Трек отправлен в канал")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки в канал: {e}")
        return False'''
    
    content = content.replace(match.group(1), new_func)
    
    with open('$FILE_MAIN', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Функция заменена в main_with_payments.py")
else:
    print("❌ Не удалось найти функцию")
    exit(1)
ENDPYTHON

check_syntax "$FILE_MAIN" || exit 1

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo "✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!"
echo "================================================================"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "1. systemctl restart albimusic-celery"
echo "2. systemctl restart albimusic-bot"
echo "3. systemctl restart albimusic-monitor"
echo ""
echo "🔙 Бэкапы сохранены в: $BACKUP_DIR"
echo ""
