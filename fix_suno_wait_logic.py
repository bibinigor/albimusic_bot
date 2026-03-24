import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Исправляем логику ожидания в generate_suno_music_sync
# Находим блок for i in range(90) и исправляем логику проверки статусов

new_wait_logic = '''            # Ожидаем завершения генерации
            for i in range(120):  # 120 попыток по 10 секунд = 20 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers, timeout=30)
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    logger.info(f"📊 Статус задачи Suno {task_id}: {status} (попытка {i+1}/120)")
                    
                    # Если Suno слишком долго думает, возможно проблема
                    if i > 50 and status in ["PENDING", "TEXT_SUCCESS", "FIRST_SUCCESS"]:
                        logger.warning(f"⚠️ Suno API очень медленный: задача {task_id} все еще {status} после {i*10} секунд")
                    
                    if status == 'SUCCESS':
                        audio_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                        # ОТЛАДКА: Логируем полный ответ
                        logger.info(f"🔍 ОТЛАДКА: Полный ответ Suno для задачи {task_id}:")
                        logger.info(f"   Статус результат: {status_result}")
                        logger.info(f"   Audio data: {audio_data}")
                        if audio_data:
                            audio_url = audio_data[0].get('audioUrl')
                            logger.info(f"✅ Генерация Suno завершена для пользователя {user_id}, URL: {audio_url}")
                            return audio_url
                        else:
                            logger.error(f"❌ Audio data пустой для задачи {task_id}")
                            logger.error(f"   Полный ответ: {status_result}")
                            return None
                    elif status in ['PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS', 'AUDIO_SUCCESS']:
                        # Продолжаем ждать - это промежуточные статусы
                        continue
                    else:
                        logger.error(f"❌ Ошибка генерации Suno: {status} для пользователя {user_id}")
                        return None
                
                else:
                    logger.warning(f"⚠️ Не удалось получить статус задачи {task_id}: {status_response.status_code}")
            
            logger.error(f"❌ Превышено время ожидания генерации Suno для пользователя {user_id}")
            return None'''

# Заменяем старую логику ожидания
pattern = r'# Ожидаем завершения генерации.*?logger.error\(f".❌ Превышено время ожидания генерации Suno для пользователя \{user_id\}"\)\s+return None'
content = re.sub(pattern, new_wait_logic, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Логика ожидания в generate_suno_music_sync исправлена!")
print("Теперь функция правильно обрабатывает промежуточные статусы:")
print("- TEXT_SUCCESS, FIRST_SUCCESS, AUDIO_SUCCESS - продолжаем ждать")
print("- SUCCESS - аудио готово, возвращаем URL")
print("- Ожидание увеличено до 20 минут")
