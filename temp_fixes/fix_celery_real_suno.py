import re

# Читаем текущий файл
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим и заменяем заглушку генерации на реальную Suno API
old_generation_code = '''        # Имитация работы с Suno API
        import asyncio
        await asyncio.sleep(2)
        
        # В реальной системе здесь будет вызов Suno API
        # и возврат реального audio_url
        audio_url = f"https://musicfile.api.box/music_{task_id[:8]}.mp3"'''

new_generation_code = '''        # Реальная генерация через Suno API
        import asyncio
        from suno_api import generate_suno_music
        
        # Вызываем реальную Suno API
        audio_url = await generate_suno_music(
            prompt=prompt,
            is_song=False,
            custom_mode=False,
            user_id=user_id
        )
        
        # Если генерация не удалась, возвращаем ошибку
        if not audio_url:
            logger.error(f"❌ Suno API вернул пустой результат для пользователя {user_id}")
            save_generation_task_sync(
                user_id=user_id,
                task_id=task_id,
                prompt=prompt,
                status='error'
            )
            return {'status': 'error', 'message': 'Генерация не удалась'}'''

content = content.replace(old_generation_code, new_generation_code)

# Записываем обратно
with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Обновлена функция generate_music_task для использования реальной Suno API")
