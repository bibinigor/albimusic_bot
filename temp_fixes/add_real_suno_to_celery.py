import re

# Читаем текущий файл
with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем импорт config если его нет
if 'import config' not in content:
    imports_end = content.find('from celery import')
    if imports_end != -1:
        content = content[:imports_end] + 'import config\\n' + content[imports_end:]

# Добавляем синхронную функцию Suno API после импортов
suno_sync_function = '''
def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None):
    """Синхронная версия генерации музыки через Suno API"""
    import requests
    import time
    
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
            logger.info(f"🎵 Задача Suno создана: {task_id} для пользователя {user_id}")
            
            # Ожидаем завершения генерации
            for i in range(30):  # 30 попыток по 10 секунд = 5 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers)
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    logger.info(f"📊 Статус задачи Suno {task_id}: {status} (попытка {i+1})")
                    
                    if status == 'SUCCESS':
                        audio_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                        if audio_data:
                            audio_url = audio_data[0].get('audioUrl')
                            logger.info(f"✅ Генерация Suno завершена для пользователя {user_id}")
                            return audio_url
                    elif status in ['PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS']:
                        continue
                    else:
                        logger.error(f"❌ Ошибка генерации Suno: {status} для пользователя {user_id}")
                        return None
            
            logger.error(f"⏰ Время ожидания Suno истекло для пользователя {user_id}")
            return None
        else:
            logger.error(f"❌ Ошибка Suno API: {response.text} для пользователя {user_id}")
            return None
    except Exception as e:
        logger.error(f"❌ Ошибка генерации Suno для пользователя {user_id}: {e}")
        return None
'''

# Находим место для вставки функции (после импортов)
imports_end = content.find('@celery_app.task')
if imports_end != -1:
    content = content[:imports_end] + suno_sync_function + '\\n\\n' + content[imports_end:]

# Находим и заменяем заглушку в generate_music_task
old_code = '''        # Имитация работы с Suno API
        import time
        time.sleep(2)
        
        # В реальной системе здесь будет вызов Suno API
        # и возврат реального audio_url
        audio_url = f"https://musicfile.api.box/music_{task_id[:8]}.mp3"'''

new_code = '''        # Реальная генерация через Suno API
        audio_url = generate_suno_music_sync(
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

content = content.replace(old_code, new_code)

# Записываем обратно
with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Добавлена реальная Suno API интеграция в celery_tasks.py")
