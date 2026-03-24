#!/bin/bash
set -e

echo "🎵 ИСПРАВЛЕНИЕ: 2 аудио-ссылки от Suno (с правильными отступами)"
echo "================================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="/root/albimusic-bot/backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# ========================================
# ФУНКЦИИ
# ========================================
backup_file() {
    local file=$1
    cp "$file" "$BACKUP_DIR/$(basename $file)"
    echo -e "${GREEN}✅ Бэкап: $(basename $file)${NC}"
}

check_syntax() {
    local file=$1
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✅ Синтаксис OK: $(basename $file)${NC}"
        return 0
    else
        echo -e "${RED}❌ ОШИБКА синтаксиса: $(basename $file)${NC}"
        python3 -m py_compile "$file"
        return 1
    fi
}

add_json_import() {
    local file=$1
    if ! grep -q "^import json" "$file"; then
        sed -i '1i import json' "$file"
        echo -e "${GREEN}✅ Добавлен import json${NC}"
    fi
}

# ========================================
# 1. ИСПРАВЛЕНИЕ celery_tasks.py
# ========================================
echo ""
echo "================================================================"
echo "📝 1/3: celery_tasks.py (КРИТИЧНО: правильные отступы)"
echo "================================================================"

FILE_CELERY="/root/albimusic-bot/celery_tasks.py"
backup_file "$FILE_CELERY"
add_json_import "$FILE_CELERY"

# Используем Python для точной замены с сохранением отступов
python3 << 'ENDPYTHON'
import sys

file_path = '/root/albimusic-bot/celery_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку 468: audio_url = audio_data[0].get('audioUrl')
target_line_num = None
for i, line in enumerate(lines):
    if "audio_url = audio_data[0].get('audioUrl')" in line:
        target_line_num = i
        break

if target_line_num is None:
    print("❌ Не найдена строка для замены")
    sys.exit(1)

print(f"🔍 Найдена строка {target_line_num + 1}")

# Определяем отступ (должен быть 24 пробела - внутри if audio_data:)
indent = ' ' * 24

# Новый блок кода с правильными отступами
new_block = [
    f"{indent}# Получаем ВСЕ ссылки из массива sunoData\n",
    f"{indent}audio_urls = []\n",
    f"{indent}for item in audio_data:\n",
    f"{indent}    url = item.get('audioUrl')\n",
    f"{indent}    if url:\n",
    f"{indent}        audio_urls.append(url)\n",
    f"{indent}\n",
    f"{indent}if not audio_urls:\n",
    f'{indent}    logger.error(f"[{{request_id}}] ❌ Нет валидных audio URL в ответе")\n',
    f"{indent}    return None\n",
    f"{indent}\n",
    f'{indent}logger.info(f"[{{request_id}}] ✅ SUNO GENERATION COMPLETED:")\n',
    f'{indent}logger.info(f"[{{request_id}}]    • Получено {{len(audio_urls)}} аудио-ссылок")\n',
    f"{indent}\n",
    f"{indent}# Валидация каждой ссылки\n",
    f"{indent}for i, url in enumerate(audio_urls, 1):\n",
    f'{indent}    logger.info(f"[{{request_id}}]    • Версия {{i}}: {{url}}")\n',
    f"{indent}    if not validate_audio_url(url, request_id):\n",
    f'{indent}        logger.error(f"[{{request_id}}] ❌ Версия {{i}} не прошла валидацию")\n',
    f"{indent}        return None\n",
    f"{indent}\n",
    f"{indent}# Возвращаем JSON массив\n",
    f"{indent}audio_url = json.dumps(audio_urls, ensure_ascii=False)\n",
    f'{indent}logger.info(f"[{{request_id}}]    • Сохраняем как JSON: {{audio_url}}")\n',
]

# Находим конец блока для замены (ищем следующий return audio_url)
end_line_num = target_line_num
for i in range(target_line_num + 1, len(lines)):
    if 'return audio_url' in lines[i]:
        end_line_num = i
        break

# Заменяем блок
lines = lines[:target_line_num] + new_block + lines[end_line_num + 1:]

# Сохраняем
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Блок заменён с правильными отступами (24 пробела)")
ENDPYTHON

check_syntax "$FILE_CELERY" || {
    echo -e "${RED}❌ Ошибка синтаксиса! Восстанавливаем бэкап...${NC}"
    cp "$BACKUP_DIR/celery_tasks.py" "$FILE_CELERY"
    exit 1
}

# ========================================
# 2. ИСПРАВЛЕНИЕ run_monitor_notify.py
# ========================================
echo ""
echo "================================================================"
echo "📝 2/3: run_monitor_notify.py"
echo "================================================================"

FILE_MONITOR="/root/albimusic-bot/run_monitor_notify.py"
backup_file "$FILE_MONITOR"
add_json_import "$FILE_MONITOR"

# Проверяем import config
if ! grep -q "from config import BOT_TOKEN" "$FILE_MONITOR"; then
    sed -i '1i from config import BOT_TOKEN' "$FILE_MONITOR"
    echo -e "${GREEN}✅ Добавлен import BOT_TOKEN${NC}"
fi

python3 << 'ENDPYTHON'
import re

file_path = '/root/albimusic-bot/run_monitor_notify.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Новая функция send_telegram_notification
new_function = '''async def send_telegram_notification(user_id, task_id, audio_url, is_song=False):
    """Отправка уведомления в Telegram о готовности генерации"""
    try:
        import aiohttp
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        bot = Bot(token=BOT_TOKEN)
        
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
        return False
'''

# Ищем и заменяем функцию
pattern = r'async def send_telegram_notification\(.*?\):.*?(?=\nasync def |\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content.replace(match.group(0), new_function)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Функция send_telegram_notification заменена")
else:
    print("❌ Не удалось найти функцию send_telegram_notification")
    exit(1)
ENDPYTHON

check_syntax "$FILE_MONITOR" || {
    echo -e "${RED}❌ Ошибка синтаксиса! Восстанавливаем бэкап...${NC}"
    cp "$BACKUP_DIR/run_monitor_notify.py" "$FILE_MONITOR"
    exit 1
}

# ========================================
# 3. ИСПРАВЛЕНИЕ main_with_payments.py
# ========================================
echo ""
echo "================================================================"
echo "📝 3/3: main_with_payments.py"
echo "================================================================"

FILE_MAIN="/root/albimusic-bot/main_with_payments.py"
backup_file "$FILE_MAIN"
add_json_import "$FILE_MAIN"

python3 << 'ENDPYTHON'
import re

file_path = '/root/albimusic-bot/main_with_payments.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Новая функция send_to_channel
new_function = '''async def send_to_channel(audio_url, comment, user_info):
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
        return False
'''

# Ищем и заменяем функцию
pattern = r'async def send_to_channel\(.*?\):.*?(?=\nasync def |\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content.replace(match.group(0), new_function)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Функция send_to_channel заменена")
else:
    print("❌ Не удалось найти функцию send_to_channel")
    exit(1)
ENDPYTHON

check_syntax "$FILE_MAIN" || {
    echo -e "${RED}❌ Ошибка синтаксиса! Восстанавливаем бэкап...${NC}"
    cp "$BACKUP_DIR/main_with_payments.py" "$FILE_MAIN"
    exit 1
}

# ========================================
# ИТОГ
# ========================================
echo ""
echo "================================================================"
echo -e "${GREEN}✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!${NC}"
echo "================================================================"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "systemctl restart albimusic-celery"
echo "systemctl restart albimusic-bot"
echo "systemctl restart albimusic-monitor"
echo ""
echo "# Проверка логов:"
echo "tail -f /var/log/albimusic-bot/celery/celery.log"
echo ""
echo "🔙 Бэкапы: $BACKUP_DIR"
echo "================================================================"

