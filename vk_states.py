"""
Модуль для управления состояниями (FSM) VK бота
"""
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)

class States(Enum):
    """Все возможные состояния бота"""
    START = auto()
    
    # Состояния генерации музыки
    WAITING_MUSIC_STYLE = auto()
    WAITING_CUSTOM_STYLE = auto()
    
    # Состояния создания песни
    CHOOSING_TEXT_TYPE = auto()
    WAITING_SONG_IDEA = auto()
    CHOOSING_LYRICS_VARIANT = auto()
    WAITING_OWN_LYRICS = auto()
    REVIEWING_LYRICS = auto()
    WAITING_GENRE = auto()
    WAITING_CUSTOM_GENRE = auto()
    WAITING_VOCAL_GENDER = auto()  # Добавлено состояние выбора пола вокалиста
    WAITING_CUSTOM_VOCAL = auto()  # Добавлено состояние для ввода своего варианта пола вокалиста
    
    # Состояния каверов и караоке
    WAITING_COVER_GENRE = auto()
    WAITING_CUSTOM_COVER_GENRE = auto()
    WAITING_AUDIO_UPLOAD = auto()
    
    # Состояния поддержки
    WAITING_SUPPORT_MESSAGE = auto()
    WAITING_SUPPORT_REPLY = auto()

    # Состояния администрирования (рассылка)
    WAITING_BROADCAST_TEXT = auto()
    WAITING_BROADCAST_CONFIRM = auto()

@dataclass
class StateData:
    """Данные состояния пользователя"""
    state: States
    data: Dict[str, Any]

class VKStateManager:
    """Менеджер состояний для VK бота"""
    
    def __init__(self, redis_client):
        """
        Инициализация менеджера состояний
        
        Args:
            redis_client: Клиент Redis для хранения состояний
        """
        self.redis = redis_client
    
    def _get_state_key(self, user_id: int) -> str:
        """Получить ключ Redis для состояния пользователя"""
        return f"vk:{user_id}:state"
    
    def _get_data_key(self, user_id: int) -> str:
        """Получить ключ Redis для данных состояния"""
        return f"vk:{user_id}:state_data"
    
    async def set_state(self, user_id: int, state: States) -> None:
        """
        Установить состояние для пользователя
        
        Args:
            user_id: ID пользователя VK
            state: Новое состояние
        """
        try:
            await self.redis.set(
                self._get_state_key(user_id),
                state.name
            )
            logger.debug(f"Установлено состояние {state.name} для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка установки состояния для {user_id}: {e}")
    
    async def get_state(self, user_id: int) -> Optional[States]:
        """
        Получить текущее состояние пользователя
        
        Args:
            user_id: ID пользователя VK
            
        Returns:
            Текущее состояние или None
        """
        try:
            state_name = await self.redis.get(self._get_state_key(user_id))
            if state_name:
                # Декодируем байты в строку, если это байты
                if isinstance(state_name, bytes):
                    state_name = state_name.decode('utf-8')
                return States[state_name]
            return None
        except Exception as e:
            logger.error(f"Ошибка получения состояния для {user_id}: {e}")
            return None
    
    async def update_data(self, user_id: int, data=None, **kwargs) -> None:
        """
        Обновить данные состояния пользователя
        
        Args:
            user_id: ID пользователя VK
            data: Словарь с данными (опционально)
            **kwargs: Данные для обновления
        """
        try:
            # Получаем текущие данные
            current_data = await self.get_data(user_id) or {}
            
            # Если передан словарь data, используем его
            if isinstance(data, dict):
                current_data.update(data)
            
            # Обновляем данные из kwargs
            current_data.update(kwargs)
            
            # Сохраняем обновленные данные
            await self.redis.set(
                self._get_data_key(user_id),
                json.dumps(current_data)
            )
            logger.debug(f"Обновлены данные состояния для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка обновления данных для {user_id}: {e}")
    
    async def get_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить данные состояния пользователя
        
        Args:
            user_id: ID пользователя VK
            
        Returns:
            Словарь с данными или None
        """
        try:
            data = await self.redis.get(self._get_data_key(user_id))
            if data:
                # Декодируем байты в строку, если это байты
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения данных для {user_id}: {e}")
            return None
    
    async def finish(self, user_id: int) -> None:
        """
        Очистить состояние и данные пользователя
        
        Args:
            user_id: ID пользователя VK
        """
        try:
            await self.redis.delete(
                self._get_state_key(user_id),
                self._get_data_key(user_id)
            )
            logger.debug(f"Очищено состояние для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка очистки состояния для {user_id}: {e}")
    
    async def reset_state(self, user_id: int) -> None:
        """
        Сбросить состояние пользователя в начальное
        
        Args:
            user_id: ID пользователя VK
        """
        await self.set_state(user_id, States.START)