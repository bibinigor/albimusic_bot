with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Заменяем существующее логирование на более подробное
old_log = '''    # Логируем данные ДО отправки в Suno
    logger.info(f"📤 SUNO DEBUG Данные для отправки:")
    logger.info(f"   Данные: {data}")'''

new_log = '''    # Логируем данные ДО отправки в Suno
    import json
    logger.info("=" * 60)
    logger.info("📤 SUNO DEBUG ПОЛНЫЕ ДАННЫЕ ДЛЯ ОТПРАВКИ:")
    logger.info(f"   prompt: {data.get('prompt', 'НЕТ ПРОМПТА!')}")
    logger.info(f"   style: {data.get('style', 'НЕТ СТИЛЯ!')}")
    logger.info(f"   customMode: {data.get('customMode', 'НЕТ')}")
    logger.info(f"   styleWeight: {data.get('styleWeight', 'НЕТ')}")
    logger.info(f"   vocalGender: {data.get('vocalGender', 'НЕТ')}")
    logger.info(f"   Полный JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")
    logger.info("=" * 60)'''

if old_log in content:
    content = content.replace(old_log, new_log)
    print("✅ Улучшено логирование данных для Suno API")
else:
    print("❌ Не найдено старое логирование")

with open('celery_tasks.py', 'w') as f:
    f.write(content)
