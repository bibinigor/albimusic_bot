"""
🔴 БЛОК 2: Модуль демо-системы для VK-бота
Функции для работы с демо-треками и разблокировкой
"""

import logging
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)


def create_demo_track(user_id, task_id, demo_url_1=None, demo_url_2=None, full_url_1=None, full_url_2=None):
    """
    Создать запись демо-трека в БД
    
    Args:
        user_id: ID пользователя VK
        task_id: Уникальный ID задачи
        demo_url_1: URL демо-версии 1 (45 сек)
        demo_url_2: URL демо-версии 2 (45 сек)
        full_url_1: URL полной версии 1
        full_url_2: URL полной версии 2
        
    Returns:
        bool: True если успешно, False при ошибке
    """
    try:
        execute_query_sync(
            '''INSERT INTO demo_tracks 
               (task_id, user_id, demo_url_1, demo_url_2, full_url_1, full_url_2, is_unlocked) 
               VALUES (%s, %s, %s, %s, %s, %s, FALSE)
               ON CONFLICT (task_id) DO NOTHING''',
            (task_id, user_id, demo_url_1, demo_url_2, full_url_1, full_url_2)
        )
        logger.info(f"✅ Создан demo_track для task_id={task_id}, user_id={user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания demo_track: {e}")
        return False


def unlock_demo_track(user_id, task_id):
    """
    Разблокировать демо-трек (после оплаты 1 токена)
    
    Args:
        user_id: ID пользователя VK
        task_id: ID трека для разблокировки
        
    Returns:
        dict: {'success': bool, 'full_url_1': str, 'full_url_2': str, 'message': str}
    """
    try:
        # Проверяем, существует ли трек и принадлежит ли он пользователю
        track = execute_query_sync(
            '''SELECT task_id, user_id, full_url_1, full_url_2, is_unlocked 
               FROM demo_tracks 
               WHERE task_id = %s AND user_id = %s''',
            (task_id, user_id)
        )
        
        if not track or len(track) == 0:
            logger.warning(f"⚠️ Трек task_id={task_id} не найден для user_id={user_id}")
            return {
                'success': False,
                'full_url_1': None,
                'full_url_2': None,
                'message': '❌ Трек не найден. Сначала создайте трек.'
            }
        
        track_data = track[0]
        is_already_unlocked = track_data[4]
        
        # Проверяем, не разблокирован ли уже
        if is_already_unlocked:
            logger.info(f"ℹ️ Трек task_id={task_id} уже разблокирован для user_id={user_id}")
            return {
                'success': False,
                'full_url_1': track_data[2],
                'full_url_2': track_data[3],
                'message': '⚠️ Этот трек уже разблокирован!'
            }
        
        # Проверяем баланс пользователя
        balance_result = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        
        if not balance_result or balance_result[0][0] < 1:
            logger.warning(f"⚠️ Недостаточно токенов для разблокировки: user_id={user_id}")
            return {
                'success': False,
                'full_url_1': None,
                'full_url_2': None,
                'message': '❌ Недостаточно токенов. Для разблокировки нужен 1 токен.'
            }
        
        # Списываем 1 токен
        execute_query_sync(
            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
            (user_id,)
        )
        logger.info(f"💰 Списан 1 токен за разблокировку от user_id={user_id}")
        
        # Разблокируем трек
        execute_query_sync(
            '''UPDATE demo_tracks 
               SET is_unlocked = TRUE, unlocked_at = NOW() 
               WHERE task_id = %s AND user_id = %s''',
            (task_id, user_id)
        )
        logger.info(f"🔓 Разблокирован трек task_id={task_id} для user_id={user_id}")
        
        return {
            'success': True,
            'full_url_1': track_data[2],
            'full_url_2': track_data[3],
            'message': '✅ Трек успешно разблокирован! Полные версии доступны ниже.'
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка разблокировки трека: {e}")
        return {
            'success': False,
            'full_url_1': None,
            'full_url_2': None,
            'message': '❌ Произошла ошибка при разблокировке. Попробуйте позже.'
        }


def get_demo_track_info(task_id, user_id):
    """
    Получить информацию о демо-треке
    
    Args:
        task_id: ID трека
        user_id: ID пользователя
        
    Returns:
        dict или None
    """
    try:
        track = execute_query_sync(
            '''SELECT task_id, user_id, demo_url_1, demo_url_2, 
                      full_url_1, full_url_2, is_unlocked, unlocked_at, created_at 
               FROM demo_tracks 
               WHERE task_id = %s AND user_id = %s''',
            (task_id, user_id)
        )
        
        if not track or len(track) == 0:
            return None
        
        track_data = track[0]
        return {
            'task_id': track_data[0],
            'user_id': track_data[1],
            'demo_url_1': track_data[2],
            'demo_url_2': track_data[3],
            'full_url_1': track_data[4],
            'full_url_2': track_data[5],
            'is_unlocked': track_data[6],
            'unlocked_at': track_data[7],
            'created_at': track_data[8]
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о demo_track: {e}")
        return None


def is_track_unlocked(task_id, user_id):
    """
    Проверить, разблокирован ли трек
    
    Args:
        task_id: ID трека
        user_id: ID пользователя
        
    Returns:
        bool: True если разблокирован, False если нет
    """
    try:
        result = execute_query_sync(
            "SELECT is_unlocked FROM demo_tracks WHERE task_id = %s AND user_id = %s",
            (task_id, user_id)
        )
        
        if not result or len(result) == 0:
            return False
        
        return result[0][0]
    except Exception as e:
        logger.error(f"❌ Ошибка проверки is_unlocked: {e}")
        return False


def get_user_unlocked_tracks_count(user_id):
    """
    Получить количество разблокированных треков пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        int: Количество разблокированных треков
    """
    try:
        result = execute_query_sync(
            "SELECT COUNT(*) FROM demo_tracks WHERE user_id = %s AND is_unlocked = TRUE",
            (user_id,)
        )
        
        if not result:
            return 0
        
        return result[0][0]
    except Exception as e:
        logger.error(f"❌ Ошибка получения количества разблокированных треков: {e}")
        return 0
