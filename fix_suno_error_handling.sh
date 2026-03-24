#!/bin/bash
set -e

echo "🔧 ИСПРАВЛЕНИЕ: Обработка ошибок Suno API"
echo "================================================================"

BACKUP_DIR="/root/albimusic-bot/backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

FILE="/root/albimusic-bot/celery_tasks.py"
cp "$FILE" "$BACKUP_DIR/celery_tasks.py"

echo "✅ Бэкап создан: $BACKUP_DIR"

# Исправляем обработку ответа Suno API
python3 << 'ENDPYTHON'
import re

file_path = '/root/albimusic-bot/celery_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем блок с обработкой ответа Suno API
pattern = r'(if response\.status_code == 200:.*?task_id = result\[.data.\]\[.taskId.\])'

match = re.search(pattern, content, re.DOTALL)

if match:
    old_block = match.group(1)
    
    # Новый блок с правильной обработкой
    new_block = '''if response.status_code == 200:
            result = response.json()
            
            logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
            logger.info(f"[{request_id}]    • Response size: {len(response.text)} bytes")
            logger.info(f"[{request_id}]    • Response keys: {list(result.keys())}")
            logger.info(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)[:500]}...")
            
            # Проверяем код ответа Suno API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                logger.error(f"[{request_id}]    • Data: {data_obj}")
                return None
            
            # Проверяем что data не null
            if not data_obj:
                logger.error(f"[{request_id}] ❌ SUNO API: data is null!")
                logger.error(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)}")
                return None
            
            # Проверяем что data - это словарь
            if not isinstance(data_obj, dict):
                logger.error(f"[{request_id}] ❌ ОШИБКА: result[\'data\'] не является словарем!")
                logger.error(f"[{request_id}]    • Тип: {type(data_obj)}")
                logger.error(f"[{request_id}]    • Значение: {data_obj}")
                return None
            
            logger.info(f"[{request_id}]    • Data keys: {list(data_obj.keys())}")
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')'''
    
    content = content.replace(old_block, new_block)
    print("✅ Найден и заменён блок обработки Suno API")
else:
    print("❌ Не удалось найти блок для замены!")
    print("⚠️  Будем искать альтернативный способ...")
    
    # Простая замена по более простому паттерну
    content = content.replace(
        "if response.status_code == 200:",
        '''if response.status_code == 200:
            result = response.json()
            
            logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
            logger.info(f"[{request_id}]    • Response size: {len(response.text)} bytes")
            logger.info(f"[{request_id}]    • Response keys: {list(result.keys())}")
            logger.info(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)[:500]}...")
            
            # Проверяем код ответа Suno API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                logger.error(f"[{request_id}]    • Data: {data_obj}")
                return None
            
            # Проверяем что data не null
            if not data_obj:
                logger.error(f"[{request_id}] ❌ SUNO API: data is null!")
                logger.error(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)}")
                return None
            
            # Проверяем что data - это словарь
            if not isinstance(data_obj, dict):
                logger.error(f"[{request_id}] ❌ ОШИБКА: result['data'] не является словарем!")
                logger.error(f"[{request_id}]    • Тип: {type(data_obj)}")
                logger.error(f"[{request_id}]    • Значение: {data_obj}")
                return None
            
            logger.info(f"[{request_id}]    • Data keys: {list(data_obj.keys())}")
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')'''
    )
    print("✅ Произведена простая замена")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл обновлён")
ENDPYTHON

# Проверка синтаксиса
if python3 -m py_compile "$FILE" 2>/dev/null; then
    echo "✅ Синтаксис Python корректен"
else
    echo "❌ ОШИБКА синтаксиса!"
    python3 -m py_compile "$FILE"
    echo "🔙 Восстанавливаем бэкап..."
    cp "$BACKUP_DIR/celery_tasks.py" "$FILE"
    exit 1
fi

echo ""
echo "================================================================"
echo "✅ ИСПРАВЛЕНИЕ ПРИМЕНЕНО"
echo "================================================================"
echo ""
echo "Перезапустите Celery:"
echo "  systemctl restart albimusic-celery"
echo ""
echo "Проверьте логи:"
echo "  sudo journalctl -u albimusic-celery -f"
echo ""
echo "Бэкап: $BACKUP_DIR"
echo "================================================================"
