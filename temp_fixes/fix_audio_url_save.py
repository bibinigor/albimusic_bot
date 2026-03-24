# Читаем текущий файл
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим место где нужно добавить сохранение audio_url в БД
# Ищем блок после создания audio_url
old_code = '''        audio_url = f"https://musicfile.api.box/music_{task_id[:8]}.mp3"
        logger.info(f"✅ Генерация завершена для {user_id}")
        
        return {'''

new_code = '''        audio_url = f"https://musicfile.api.box/music_{task_id[:8]}.mp3"
        
        # Сохраняем audio_url в БД
        save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            status='completed',
            audio_url=audio_url
        )
        
        logger.info(f"✅ Генерация завершена для {user_id}")
        
        return {'''

content = content.replace(old_code, new_code)

# Записываем обратно
with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлена функция generate_music_task - добавлено сохранение audio_url в БД")
