import re
import requests
import time

# Читаем текущий файл
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем синхронную функцию Suno API
suno_sync_function = '''
def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None):
    """Синхронная версия генерации музыки через Suno API"""
    import requests
    import time
    import config
    
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if is_song:
        if custom_mode:
            data = {
                "prompt": prompt,
                "customMode": True,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
        else:
            data = {
                "prompt": prompt,
                "customMode": False,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
    else:
        data = {
            "prompt": prompt,
            "customMode": False,
            "instrumental": True,
            "model": "V5",
            "callBackUrl": "https://example.com/callback"
        }
    
    try:
        # Создаем задачу генерации
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            task_id = result['data']['taskId']
            logger.info(f"🎵 Задача создана: {task_id} для пользователя {user_id}")
            
            # Ожидаем завершения генерации
            for i in range(30):  # 30 попыток по 10 секунд = 5 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers)
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    logger.info(f"📊 Статус задачи {task_id}: {status} (попытка {i+1})")
                    
                    if status == 'SUCCESS':
                        audio_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                        if audio_data:
                            audio_url = audio_data[0].get('audioUrl')
                            logger.info(f"✅ Генерация завершена для пользователя {user_id}")
                            return audio_url
                    elif status in ['PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS']:
                        continue
                    else:
                        logger.error(f"❌ Ошибка генерации: {status} для пользователя {user_id}")
                        return None
            
            logger.error(f"⏰ Время ожидания истекло для пользователя {user_id}")
            return None
        else:
            logger.error(f"❌ Ошибка API: {response.text} для пользователя {user_id}")
            return None
    except Exception as e:
        logger.error(f"❌ Ошибка генерации для пользователя {user_id}: {e}")
        return None
'''

# Находим место для вставки функции (после импортов)
imports_end = content.find('@celery_app.task')
if imports_end != -1:
    content = content[:imports_end] + suno_sync_function + '\\n\\n' + content[imports_end:]

# Заменяем асинхронный вызов на синхронный
old_call = '''        # Реальная генерация через Suno API
        import asyncio
        from suno_api import generate_suno_music
        
        # Вызываем реальную Suno API
        audio_url = await generate_suno_music(
            prompt=prompt,
            is_song=False,
            custom_mode=False,
            user_id=user_id
        )'''

new_call = '''        # Реальная генерация через Suno API (синхронная версия)
        audio_url = generate_suno_music_sync(
            prompt=prompt,
            is_song=False,
            custom_mode=False,
            user_id=user_id
        )'''

content = content.replace(old_call, new_call)

# Записываем обратно
with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Добавлена синхронная версия Suno API для Celery задач")
