"""
Реальная интеграция с Suno API
"""

import aiohttp
import logging
import asyncio
import config

logger = logging.getLogger(__name__)

async def generate_suno_music(prompt, is_song=False, custom_mode=False, user_id=None):
    """Реальная генерация музыки через Suno API"""
    async with aiohttp.ClientSession() as session:
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
            async with session.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result[data][taskId]
                    logger.info(f"🎵 Задача создана: {task_id} для пользователя {user_id}")
                    
                    # Ожидаем завершения генерации
                    for i in range(30):  # 30 попыток по 10 секунд = 5 минут
                        await asyncio.sleep(10)
                        async with session.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers) as status_response:
                            if status_response.status == 200:
                                status_result = await status_response.json()
                                status = status_result.get(data, {}).get(status)
                                logger.info(f"📊 Статус задачи {task_id}: {status} (попытка {i+1})")
                                
                                if status == SUCCESS:
                                    audio_data = status_result.get(data, {}).get(response, {}).get(sunoData, [])
                                    if audio_data:
                                        audio_url = audio_data[0].get(audioUrl)
                                        logger.info(f"✅ Генерация завершена для пользователя {user_id}")
                                        return audio_url
                                elif status in [PENDING, TEXT_SUCCESS, FIRST_SUCCESS]:
                                    continue
                                else:
                                    logger.error(f"❌ Ошибка генерации: {status} для пользователя {user_id}")
                                    return None
                    
                    logger.error(f"⏰ Время ожидания истекло для пользователя {user_id}")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка API: {error_text} для пользователя {user_id}")
                    return None
        except Exception as e:
            logger.error(f"❌ Ошибка генерации для пользователя {user_id}: {e}")
            return None

# Алиасы для совместимости
async def generate_music(prompt, style=None):
    """Генерация инструментальной музыки"""
    full_prompt = f"{prompt}. {style}" if style else prompt
    return await generate_suno_music(full_prompt, is_song=False, user_id=None)

async def generate_song(lyrics, style=None):
    """Генерация песни с текстом"""
    full_prompt = f"Стиль: {style}. Текст песни: {lyrics}" if style else lyrics
    return await generate_suno_music(full_prompt, is_song=True, user_id=None)
