with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Находим место перед отправкой запроса к Suno
import re
pattern = r'try:\s*# Создаем задачу генерации'

if pattern in content:
    # Добавляем логирование данных запроса
    debug_code = '''
    # ЛОГИРОВАНИЕ ЗАПРОСА К SUNO
    logger.info("📤 ДАННЫЕ ДЛЯ SUNO API:")
    logger.info(f"   URL: {url}")
    logger.info(f"   Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
    logger.info(f"   Заголовки: {headers}")
    
    try:
        # Создаем задачу генерации'''
    
    content = content.replace(pattern, debug_code)
    print("✅ Добавлено логирование запроса к Suno API")
else:
    print("❌ Не найдено место для добавления логирования")

with open('celery_tasks.py', 'w') as f:
    f.write(content)
