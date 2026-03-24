#!/usr/bin/env python3
"""
Сервис для работы с Replicate API
Поддерживает генерацию видео, обработку фото и создание изображений
"""

import os
import logging
import replicate
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ReplicateService:
    """Сервис для работы с Replicate API"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Инициализация сервиса
        
        Args:
            api_token: API токен Replicate (если None, берется из переменной окружения)
        """
        self.api_token = api_token or os.getenv('REPLICATE_API_TOKEN')
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN не найден в переменных окружения")
        
        self.client = replicate.Client(api_token=self.api_token)
        logger.info("✅ ReplicateService инициализирован")
    
    # ==================== ВИДЕО ====================
    
    def generate_video_by_description(self, description: str) -> Dict[str, Any]:
        """
        Генерация видео по текстовому описанию через Runway Gen-3
        
        Args:
            description: Текстовое описание видео
        
        Returns:
            dict: {"status": "success", "video_url": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"🎨 Запуск генерации видео по описанию: {description[:50]}...")
            
            output = self.client.run(
                "runwayml/gen-3-alpha-turbo",
                input={
                    "prompt": description,
                    "duration": 10,  # Фиксированная длительность для лучшего качества
                    "aspect_ratio": "16:9",
                    "mode": "text-to-video"
                }
            )
            
            # Replicate возвращает URL или список URL
            video_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
            
            if video_url:
                logger.info(f"✅ Видео по описанию сгенерировано: {video_url[:50]}...")
                return {
                    "status": "success",
                    "video_url": video_url
                }
            else:
                logger.error("❌ Replicate вернул пустой результат")
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации видео по описанию: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_video(self, audio_url: str, duration: int = 5) -> Dict[str, Any]:
        """
        Генерация видео из аудио через Runway Gen-3 Alpha Turbo
        
        Args:
            audio_url: URL аудио файла
            duration: Длительность видео (5 или 10 секунд)
        
        Returns:
            dict: {"status": "success", "video_url": "...", "task_id": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"🎬 Запуск генерации видео: duration={duration}s, audio={audio_url[:50]}...")
            
            output = self.client.run(
                "runwayml/gen-3-alpha-turbo",
                input={
                    "prompt_image": audio_url,  # Runway использует prompt_image для аудио
                    "duration": duration,
                    "aspect_ratio": "16:9"
                }
            )
            
            # Replicate возвращает URL или список URL
            video_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
            
            if video_url:
                logger.info(f"✅ Видео сгенерировано: {video_url[:50]}...")
                return {
                    "status": "success",
                    "video_url": video_url,
                    "duration": duration
                }
            else:
                logger.error("❌ Replicate вернул пустой результат")
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации видео: {e}")
            return {"status": "error", "error": str(e)}
    
    # ==================== ФОТО ====================
    
    def animate_image(self, image_url: str) -> Dict[str, Any]:
        """
        Оживление фото через Runway Motion Brush
        
        Args:
            image_url: URL изображения
        
        Returns:
            dict: {"status": "success", "video_url": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"🎬 Оживление фото: {image_url[:50]}...")
            
            output = self.client.run(
                "runwayml/motion-brush",
                input={"image": image_url}
            )
            
            video_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
            
            if video_url:
                logger.info(f"✅ Фото оживлено: {video_url[:50]}...")
                return {"status": "success", "video_url": video_url}
            else:
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка оживления фото: {e}")
            return {"status": "error", "error": str(e)}
    
    def animate_person_dance(self, person_image_url: str, dance_video_url: str) -> Dict[str, Any]:
        """
        Танец-персонаж через Animate Anyone
        
        Args:
            person_image_url: URL фото персонажа
            dance_video_url: URL видео с танцем
        
        Returns:
            dict: {"status": "success", "video_url": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"💃 Создание танца: person={person_image_url[:30]}..., dance={dance_video_url[:30]}...")
            
            output = self.client.run(
                "lucataco/animate-anyone",
                input={
                    "image": person_image_url,
                    "video": dance_video_url
                }
            )
            
            video_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
            
            if video_url:
                logger.info(f"✅ Танец создан: {video_url[:50]}...")
                return {"status": "success", "video_url": video_url}
            else:
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания танца: {e}")
            return {"status": "error", "error": str(e)}
    
    def upscale_image(self, image_url: str, scale: int = 4) -> Dict[str, Any]:
        """
        Апскейл изображения через Real-ESRGAN
        
        Args:
            image_url: URL изображения
            scale: Коэффициент увеличения (2 или 4)
        
        Returns:
            dict: {"status": "success", "image_url": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"⬆️ Апскейл {scale}x: {image_url[:50]}...")
            
            output = self.client.run(
                "nightmareai/real-esrgan",
                input={
                    "image": image_url,
                    "scale": scale
                }
            )
            
            upscaled_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
            
            if upscaled_url:
                logger.info(f"✅ Апскейл выполнен: {upscaled_url[:50]}...")
                return {"status": "success", "image_url": upscaled_url}
            else:
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка апскейла: {e}")
            return {"status": "error", "error": str(e)}
    
    def remove_background(self, image_url: str) -> Dict[str, Any]:
        """
        Удаление фона через RMBG-1.4
        
        Args:
            image_url: URL изображения
        
        Returns:
            dict: {"status": "success", "image_url": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"🗑️ Удаление фона: {image_url[:50]}...")
            
            output = self.client.run(
                "lucataco/remove-bg",
                input={"image": image_url}
            )
            
            result_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
            
            if result_url:
                logger.info(f"✅ Фон удален: {result_url[:50]}...")
                return {"status": "success", "image_url": result_url}
            else:
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления фона: {e}")
            return {"status": "error", "error": str(e)}
    
    # ==================== ИЗОБРАЖЕНИЯ ====================
    
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> Dict[str, Any]:
        """
        Генерация изображения через FLUX.1 [dev]
        
        Args:
            prompt: Текстовое описание изображения
            aspect_ratio: Соотношение сторон ('1:1', '9:16', '16:9', '3:4', '4:3')
        
        Returns:
            dict: {"status": "success", "image_url": "...", "prompt": "..."}
                  или {"status": "error", "error": "..."}
        """
        try:
            logger.info(f"🎨 Генерация изображения: aspect={aspect_ratio}, prompt={prompt[:50]}...")
            
            output = self.client.run(
                "black-forest-labs/flux-dev",
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "num_outputs": 1,
                    "output_format": "jpg",
                    "output_quality": 90
                }
            )
            
            # ИСПРАВЛЕНО: Обработка FileOutput object от Replicate
            if output:
                if isinstance(output, list):
                    image_url = str(output[0])
                else:
                    # FileOutput object или строка - конвертируем в str
                    image_url = str(output)
            else:
                image_url = None
            
            if image_url:
                logger.info(f"✅ Изображение создано: {image_url[:50]}...")
                return {
                    "status": "success",
                    "image_url": image_url,
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio
                }
            else:
                return {"status": "error", "error": "Пустой результат от API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    # ==================== УТИЛИТЫ ====================
    
    def check_api_status(self) -> bool:
        """
        Проверка доступности Replicate API
        
        Returns:
            bool: True если API доступен, False если нет
        """
        try:
            # Простой тест - получаем список моделей
            models = self.client.models.list()
            logger.info("✅ Replicate API доступен")
            return True
        except Exception as e:
            logger.error(f"❌ Replicate API недоступен: {e}")
            return False


# Singleton instance
_replicate_service = None


def get_replicate_service() -> ReplicateService:
    """
    Получить singleton instance ReplicateService
    
    Returns:
        ReplicateService: Инстанс сервиса
    """
    global _replicate_service
    if _replicate_service is None:
        _replicate_service = ReplicateService()
    return _replicate_service


if __name__ == "__main__":
    # Тестирование сервиса
    logging.basicConfig(level=logging.INFO)
    
    service = ReplicateService()
    
    # Проверка API
    if service.check_api_status():
        print("✅ Replicate API работает!")
    else:
        print("❌ Replicate API недоступен!")
