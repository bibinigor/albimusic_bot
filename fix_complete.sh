#!/bin/bash
set -e

echo "🎵 ПОЛНОЕ ИСПРАВЛЕНИЕ 2 ссылок от Suno"
echo "========================================"

# Бэкап
BACKUP="/root/albimusic-bot/celery_backup_$(date +%Y%m%d_%H%M%S).py"
cp /root/albimusic-bot/celery_tasks.py "$BACKUP"
echo "✅ Бэкап: $BACKUP"

# Исправляем celery_tasks.py с правильными отступами
python3 << 'ENDPYTHON'
with open('/root/albimusic-bot/celery_tasks.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку с audio_url = audio_data[0].get('audioUrl')
for i, line in enumerate(lines):
    if "audio_url = audio_data[0].get('audioUrl')" in line:
        print(f"🔍 Найдена строка {i+1}")
        
        # Определяем отступ (должен быть 24 пробела после if audio_data:)
        # На самом деле: if status == 'SUCCESS': (8 пробелов)
        #                audio_data = ... (12 пробелов)
        #                if audio_data: (12 пробелов)
        #                    наш код (16 пробелов)
        
        indent = ' ' * 16  # 16 пробелов для уровня внутри if audio_data:
        
        # Новый код с ПРАВИЛЬНЫМИ отступами
        new_code = f'''{indent}# Получаем ВСЕ ссылки из массива sunoData
{indent}audio_urls = []
{indent}for item in audio_data:
{indent}    url = item.get('audioUrl')
{indent}    if url:
{indent}        audio_urls.append(url)
{indent}
{indent}if not audio_urls:
{indent}    logger.error(f"[{{request_id}}] ❌ Нет валидных audio URL в ответе")
{indent}    return None
{indent}
{indent}logger.info(f"[{{request_id}}] ✅ SUNO GENERATION COMPLETED:")
{indent}logger.info(f"[{{request_id}}]    • Получено {{len(audio_urls)}} аудио-ссылок")
{indent}
{indent}# Валидация каждой ссылки
{indent}for idx, url in enumerate(audio_urls, 1):
{indent}    logger.info(f"[{{request_id}}]    • Версия {{idx}}: {{url}}")
{indent}    if not validate_audio_url(url, request_id):
{indent}        logger.error(f"[{{request_id}}] ❌ Версия {{idx}} не прошла валидацию")
{indent}        return None
{indent}
{indent}# Возвращаем JSON массив
{indent}audio_url = json.dumps(audio_urls, ensure_ascii=False)
{indent}logger.info(f"[{{request_id}}]    • Сохраняем как JSON: {{audio_url}}")'''
        
        # Заменяем строку
        lines[i] = new_code + '\n'
        
        # Удаляем старые строки после этого (лог о завершении и валидации)
        # Ищем до return audio_url
        j = i + 1
        while j < len(lines) and j < i + 15:
            if 'return audio_url' in lines[j]:
                # Оставляем return audio_url
                j += 1
                continue
            if 'logger.info(f".*SUNO GENERATION COMPLETED"' in lines[j] or \
               'logger.info(f".*Audio URL:"' in lines[j] or \
               'logger.info(f".*Валидация MP3"' in lines[j] or \
               'if not validate_audio_url' in lines[j] or \
               'logger.error(f".*MP3 не прошел валидацию"' in lines[j]:
                # Удаляем старый лог и валидацию
                lines[j] = ''
            j += 1
        
        break

# Сохраняем
with open('/root/albimusic-bot/celery_tasks.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ celery_tasks.py исправлен с правильными отступами")
ENDPYTHON

# Проверяем синтаксис
echo "Проверяем синтаксис..."
if python3 -m py_compile /root/albimusic-bot/celery_tasks.py 2>/dev/null; then
    echo "✅ Синтаксис celery_tasks.py - OK"
    
    # Теперь быстрые фиксы остальных файлов
    echo ""
    echo "Исправляем остальные файлы..."
    
    # 1. run_monitor_notify.py
    echo "1. run_monitor_notify.py..."
    python3 << 'ENDPYTHON'
with open('/root/albimusic-bot/run_monitor_notify.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем импорт json если нет
if 'import json' not in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            lines.insert(i, 'import json')
            break
    content = '\n'.join(lines)

# Заменяем старый код кнопки
import re

# Ищем старый блок
old_pattern = r'keyboard = InlineKeyboardMarkup\(inline_keyboard=\[\s+\[\s+InlineKeyboardButton\(text="🔗 Скачать MP3", url=audio_url\)\s+\],'

new_code = '''        # Парсим audio_url (JSON массив или одна ссылка)
        audio_urls = []
        if audio_url and audio_url.startswith('['):
            try:
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
        
        buttons.append(['''

content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

with open('/root/albimusic-bot/run_monitor_notify.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ run_monitor_notify.py исправлен")
ENDPYTHON

    # 2. main_with_payments.py
    echo "2. main_with_payments.py..."
    python3 << 'ENDPYTHON'
with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем импорт json если нет
if 'import json' not in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            lines.insert(i, 'import json')
            break
    content = '\n'.join(lines)

# Находим функцию send_to_channel и добавляем парсинг
import re

pattern = r'(async def send_to_channel\(audio_url, comment, user_info\):\s+"""[\s\S]*?"""\s+)try:'

def replacer(match):
    return match.group(1) + '''try:
        # Берём первую ссылку (JSON массив или одна ссылка)
        if audio_url and audio_url.startswith('['):
            try:
                audio_urls = json.loads(audio_url)
                first_audio_url = audio_urls[0]
            except:
                first_audio_url = audio_url
        else:
            first_audio_url = audio_url'''

content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open('/root/albimusic-bot/main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ main_with_payments.py исправлен")
ENDPYTHON

    echo ""
    echo "ПРОВЕРКА ВСЕХ ФАЙЛОВ:"
    
    ALL_OK=true
    for file in celery_tasks.py run_monitor_notify.py main_with_payments.py; do
        if python3 -m py_compile "/root/albimusic-bot/$file" 2>/dev/null; then
            echo "✅ $file - синтаксис OK"
        else
            echo "❌ $file - ошибка синтаксиса"
            ALL_OK=false
        fi
    done
    
    if [ "$ALL_OK" = true ]; then
        echo ""
        echo "🎉 ВСЕ ИСПРАВЛЕНИЯ УСПЕШНЫ!"
        echo ""
        echo "🚀 ПЕРЕЗАПУСК СЕРВИСОВ:"
        echo "sudo systemctl restart albimusic-celery"
        echo "sudo systemctl restart albimusic-bot"
        echo "sudo systemctl restart albimusic-monitor"
        echo ""
        echo "📋 После перезапуска протестируйте генерацию - должны приходить 2 ссылки!"
    else
        echo ""
        echo "❌ Есть ошибки. Восстанавливаем оригиналы..."
        cp "$BACKUP" /root/albimusic-bot/celery_tasks.py
    fi
    
else
    echo "❌ Ошибка синтаксиса в celery_tasks.py"
    echo "Восстанавливаем оригинал..."
    cp "$BACKUP" /root/albimusic-bot/celery_tasks.py
fi
