import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Находим функцию generate_suno_music_sync и заменяем ее полностью
new_function = '''def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None, style=None):
    """Синхронная версия генерации музыки через Suno API"""
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if is_song:
        if custom_mode:
            # В custom_mode: true требуется style и title
            data = {
                "prompt": prompt,
                "style": style if style else "pop",
                "title": f"Song for user {user_id}" if user_id else "Generated Song",
                "customMode": True,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
        else:
            # В non-custom_mode стиль не передается
            data = {
                "prompt": prompt,
                "customMode": False,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
    else:
        # Инструментальная музыка
        data = {
            "prompt": prompt,
            "customMode": False,
            "instrumental": True,
            "model": "V5",
            "callBackUrl": "https://example.com/callback"
        }
    
    try:
        # Создаем задачу генерации
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            result = response.json()
            task_id = result['data']['taskId']
            logger.info(f"🎵 Задача Suno создана: {task_id} для пользователя {user_id}")
            
            # Ожидаем завершения генерации (увеличено для медленного Suno API)
            for i in range(90):  # 90 попыток по 10 секунд = 15 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers, timeout=30)
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    logger.info(f"📊 Статус задачи Suno {task_id}: {status} (попытка {i+1}/90)")
                    # Если Suno слишком долго думает, возможно проблема
                    if i > 30 and status == "PENDING":
                        logger.warning(f"⚠️ Suno API очень медленный: задача {task_id} все еще PENDING после {i*10} секунд")
                    
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
                
                else:
                    logger.warning(f"⚠️ Не удалось получить статус задачи {task_id}: {status_response.status_code}")
            
            logger.error(f"❌ Превышено время ожидания генерации Suno для пользователя {user_id}")
            return None
        else:
            logger.error(f"❌ Ошибка создания задачи Suno: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Исключение в generate_suno_music_sync: {e}")
        return None'''

# Заменяем старую функцию
pattern = r'def generate_suno_music_sync\(prompt, is_song=False, custom_mode=False, user_id=None, style=None\):.*?return None\n'
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Функция generate_suno_music_sync полностью переписана")
