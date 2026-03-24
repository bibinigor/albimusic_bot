import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Добавляем отладочное логирование в generate_suno_music_sync
debug_code = '''                    if status == 'SUCCESS':
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
                            return None'''

# Заменяем блок
pattern = r'if status == .SUCCESS.:\s+audio_data = status_result\.get\(.data., \{\}\)\.get\(.response., \{\}\)\.get\(.sunoData., \[\]\)\s+if audio_data:\s+audio_url = audio_data\[0\]\.get\(.audioUrl.\)\s+logger\.info\(f".✅ Генерация Suno завершена для пользователя \{user_id\}."\)\s+return audio_url'
content = re.sub(pattern, debug_code, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Добавлено отладочное логирование в generate_suno_music_sync")
