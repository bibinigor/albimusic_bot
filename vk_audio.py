"""
Модуль для работы с аудио в VK боте
"""
import os
import logging
import aiohttp
import asyncio
from typing import Optional, Tuple
from vk_api import VkUpload
import tempfile

logger = logging.getLogger(__name__)

class VKAudioUploader:
    def __init__(self, vk_session):
        """
        Инициализация загрузчика аудио
        
        Args:
            vk_session: Сессия VK API
        """
        self.vk = vk_session
        self.upload = VkUpload(vk_session)

    async def download_audio(self, url: str) -> Optional[str]:
        """
        Скачать аудио файл по URL
        
        Args:
            url: URL аудио файла
            
        Returns:
            Путь к скачанному файлу или None в случае ошибки
        """
        try:
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_path = temp_file.name
            temp_file.close()

            # Скачиваем файл
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка скачивания аудио: {response.status}")
                        return None
                    
                    with open(temp_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка при скачивании аудио: {e}")
            return None

    async def upload_audio(self, file_path: str, title: str = None, artist: str = "ALBImusic") -> Optional[Tuple[int, int]]:
        """
        Загрузить аудио в VK
        
        Args:
            file_path: Путь к аудио файлу
            title: Название трека
            artist: Исполнитель
            
        Returns:
            Кортеж (owner_id, audio_id) или None в случае ошибки
        """
        try:
            # Загружаем аудио через vk_api
            try:
                audio = self.upload.audio(
                    file_path,
                    artist=artist,
                    title=title or "Generated Music"
                )
                
                # Удаляем временный файл
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить временный файл {file_path}: {e}")
                
                return audio['owner_id'], audio['id']
            except Exception as upload_error:
                # Проверяем, является ли ошибка связанной с авторизацией группы
                if "Group authorization failed" in str(upload_error) or "method is unavailable with group auth" in str(upload_error):
                    logger.warning(f"⚠️ Ошибка авторизации группы при загрузке аудио: {upload_error}")
                    # Возвращаем None, чтобы использовать альтернативный метод отправки аудио
                    return None
                else:
                    # Пробрасываем другие ошибки
                    raise upload_error
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке аудио в VK: {e}")
            return None

    async def process_audio(self, url: str, title: str = None) -> Optional[str]:
        """
        Обработать аудио: скачать и загрузить в VK
        
        Args:
            url: URL аудио файла
            title: Название трека
            
        Returns:
            Строка для прикрепления аудио к сообщению (owner_id_audio_id)
            или None в случае ошибки
        """
        try:
            # Скачиваем аудио
            temp_path = await self.download_audio(url)
            if not temp_path:
                return None
            
            # Загружаем в VK
            result = await self.upload_audio(temp_path, title)
            if not result:
                return None
                
            owner_id, audio_id = result
            return f"{owner_id}_{audio_id}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке аудио: {e}")
            return None

    @staticmethod
    def get_audio_attachment(owner_id: int, audio_id: int) -> str:
        """
        Получить строку прикрепления аудио для сообщения
        
        Args:
            owner_id: ID владельца аудио
            audio_id: ID аудио записи
            
        Returns:
            Строка прикрепления в формате audio{owner_id}_{audio_id}
        """
        return f"audio{owner_id}_{audio_id}"