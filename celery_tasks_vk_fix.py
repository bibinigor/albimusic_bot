#!/usr/bin/env python3
"""
CRITICAL FIX: Исправление send_vk_result для отправки аудио файлов

Проблема: функция send_vk_result() отправляет только текст, игнорирует аудио
Решение: добавляем загрузку и отправку аудио через VK API
"""

def send_vk_result_fixed(user_id, message, audio_url=None):
    """Отправляет результат генерации пользователю ВК с аудио файлом"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        import vk_api
        from vk_config import VK_TOKEN
        from vk_api.utils import get_random_id
        from vk_api.upload import VkUpload
        import requests
        import tempfile
        import os
        
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
        upload = VkUpload(vk_session)
        
        # Если есть audio_url, загружаем и отправляем аудио
        if audio_url:
            try:
                # Парсим URL (может быть JSON массив)
                import json
                if isinstance(audio_url, str) and audio_url.startswith('['):
                    urls = json.loads(audio_url)
                    # Берем первый URL из массива
                    audio_url = urls[0] if urls else audio_url
                
                logger.info(f"🎵 Скачиваю аудио для отправки в ВК: {audio_url}")
                
                # Скачиваем аудио файл
                response = requests.get(audio_url, timeout=60)
                response.raise_for_status()
                
                # Сохраняем во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                logger.info(f"📥 Файл скачан: {tmp_path}")
                
                # Загружаем аудио в ВК
                audio = upload.audio(tmp_path, artist="ALBI Music", title="AI Generated Track")
                attachment = f"audio{audio['owner_id']}_{audio['id']}"
                
                logger.info(f"✅ Аудио загружено в ВК: {attachment}")
                
                # Отправляем сообщение с аудио
                vk.messages.send(
                    user_id=user_id,
                    message=message,
                    attachment=attachment,
                    random_id=get_random_id()
                )
                
                # Удаляем временный файл
                os.unlink(tmp_path)
                logger.info(f"✅ Результат с аудио отправлен пользователю ВК {user_id}")
                return True
                
            except Exception as audio_error:
                logger.error(f"❌ Ошибка отправки аудио в ВК: {audio_error}")
                # Если не удалось отправить аудио, отправляем хотя бы текст с URL
                message_with_url = f"{message}\n\n🔗 Слушать: {audio_url}"
                vk.messages.send(
                    user_id=user_id,
                    message=message_with_url,
                    random_id=get_random_id()
                )
                logger.info(f"✅ Текст с URL отправлен пользователю ВК {user_id}")
                return True
        else:
            # Если нет аудио, просто отправляем текст
            vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=get_random_id()
            )
            logger.info(f"✅ Текстовое сообщение отправлено пользователю ВК {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки результата в ВК для пользователя {user_id}: {e}")
        return False


# Код для замены в celery_tasks.py
REPLACEMENT_CODE = """
# Функция для отправки результатов в ВК
def send_vk_result(user_id, message, audio_url=None):
    '''Отправляет результат генерации пользователю ВК с аудио файлом'''
    try:
        import vk_api
        from vk_config import VK_TOKEN
        from vk_api.utils import get_random_id
        from vk_api.upload import VkUpload
        import requests
        import tempfile
        import os
        import json
        
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
        upload = VkUpload(vk_session)
        
        # Если есть audio_url, загружаем и отправляем аудио
        if audio_url:
            try:
                # Парсим URL (может быть JSON массив)
                if isinstance(audio_url, str) and audio_url.startswith('['):
                    urls = json.loads(audio_url)
                    # Берем первый URL из массива
                    audio_url = urls[0] if urls else audio_url
                
                logger.info(f"🎵 Скачиваю аудио для отправки в ВК: {audio_url}")
                
                # Скачиваем аудио файл
                response = requests.get(audio_url, timeout=60)
                response.raise_for_status()
                
                # Сохраняем во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                logger.info(f"📥 Файл скачан: {tmp_path}")
                
                # Загружаем аудио в ВК
                audio = upload.audio(tmp_path, artist="ALBI Music", title="AI Generated Track")
                attachment = f"audio{audio['owner_id']}_{audio['id']}"
                
                logger.info(f"✅ Аудио загружено в ВК: {attachment}")
                
                # Отправляем сообщение с аудио
                vk.messages.send(
                    user_id=user_id,
                    message=message,
                    attachment=attachment,
                    random_id=get_random_id()
                )
                
                # Удаляем временный файл
                os.unlink(tmp_path)
                logger.info(f"✅ Результат с аудио отправлен пользователю ВК {user_id}")
                return True
                
            except Exception as audio_error:
                logger.error(f"❌ Ошибка отправки аудио в ВК: {audio_error}")
                # Если не удалось отправить аудио, отправляем хотя бы текст с URL
                message_with_url = f"{message}\\n\\n🔗 Слушать: {audio_url}"
                vk.messages.send(
                    user_id=user_id,
                    message=message_with_url,
                    random_id=get_random_id()
                )
                logger.info(f"✅ Текст с URL отправлен пользователю ВК {user_id}")
                return True
        else:
            # Если нет аудио, просто отправляем текст
            vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=get_random_id()
            )
            logger.info(f"✅ Текстовое сообщение отправлено пользователю ВК {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки результата в ВК для пользователя {user_id}: {e}")
        return False
"""

if __name__ == "__main__":
    print("🔧 Скрипт для исправления send_vk_result в celery_tasks.py")
    print("\n📋 Инструкции:")
    print("1. Создайте резервную копию celery_tasks.py")
    print("2. Замените функцию send_vk_result (строки 24-45) на код из REPLACEMENT_CODE")
    print("3. Перезапустите Celery Worker")
    print("\nКод для замены сохранен в переменной REPLACEMENT_CODE")
