"""
Дополнительные состояния для администрирования VK-бота
Рассылка, модерация поддержки
"""
from vk_states import States
from enum import Enum, auto

class AdminStates(Enum):
    """Состояния админ-панели"""
    # Рассылка
    WAITING_BROADCAST_TEXT = auto()
    WAITING_BROADCAST_CONFIRM = auto()
    
    # Модерация поддержки
    WAITING_SUPPORT_REPLY = auto()
