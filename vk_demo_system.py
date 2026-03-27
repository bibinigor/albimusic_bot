"""
Модуль демо-системы для VK бота
"""
import logging
from typing import List, Dict, Optional
from vk_audio import VKAudioUploader

logger = logging.getLogger(__name__)

class VKDemoSystem:
    def __init__(self, vk_session, audio_uploader: VKAudioUploader):
        """
        Инициализация демо-системы
        
        Args:
            vk_session: Сессия VK API
            audio_uploader: Загрузчик аудио
        """
        self.vk = vk_session.get_api()
        self.audio_uploader = audio_uploader
        self.demo_tracks: List[Dict] = []

    async def initialize_demo_tracks(self):
        """Инициализация демо-треков"""
        demo_files = {
            'demo_ya_budu_zhdat.mp3': '💫 Я буду ждать всегда',
            'demo_krasivaya_skripka.mp3': '🎻 Красивая скрипка',
            'demo_audio/lubov.mp3': '🌸 Люба, с 8 марта',
            'demo_audio/bodybuilding.mp3': '💪 Бодибилдинг',
            'demo_audio/cat.mp3': '🐱 Кот'
        }
        
        for file_path, title in demo_files.items():
            try:
                # Загружаем трек в VK
                result = await self.audio_uploader.upload_audio(
                    file_path,
                    title=title,
                    artist="ALBImusic Demo"
                )
                
                if result:
                    owner_id, audio_id = result
                    self.demo_tracks.append({
                        'owner_id': owner_id,
                        'audio_id': audio_id,
                        'title': title
                    })
                    logger.info(f"✅ Загружен демо-трек: {title}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки демо-трека {file_path}: {e}")

    def get_demo_attachments(self) -> List[str]:
        """
        Получить список вложений для демо-треков
        
        Returns:
            Список строк вложений в формате audio{owner_id}_{audio_id}
        """
        return [
            f"audio{track['owner_id']}_{track['audio_id']}"
            for track in self.demo_tracks
        ]

    def get_demo_keyboard_text(self) -> str:
        """
        Получить текст с описанием демо-треков
        
        Returns:
            Форматированный текст с списком демо-треков
        """
        return "\n".join(
            f"{track['title']}"
            for track in self.demo_tracks
        )

async def register_demo_handlers(bot):
    """
    Регистрация обработчиков демо-системы
    
    Args:
        bot: Экземпляр VK бота
    """
    demo_system = VKDemoSystem(bot.vk_session, bot.audio_uploader)
    await demo_system.initialize_demo_tracks()
    
    # Добавляем демо-систему в бота
    bot.demo_system = demo_system
    
    # Расширяем метод send_welcome для отправки демо-треков
    original_send_welcome = bot.send_welcome
    
    async def send_welcome_with_demo(user_id):
        """Отправка приветственного сообщения с демо-треками"""
        await original_send_welcome(user_id)
        
        demo_message = (
            "🎵 Вот примеры треков, которые я могу создавать:\n\n"
            f"{demo_system.get_demo_keyboard_text()}\n\n"
            "💫 Попробуйте создать свой трек!"
        )
        
        # Отправляем сообщение с демо-треками
        try:
            bot.vk.messages.send(
                user_id=user_id,
                message=demo_message,
                attachment=",".join(demo_system.get_demo_attachments()),
                random_id=0
            )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки демо-треков: {e}")
    
    # Заменяем оригинальный метод
    bot.send_welcome = send_welcome_with_demo