"""
🔴 БЛОК 4: Модуль реферальной системы для VK-бота
Функции для работы с рефералами и начислением бонусов
"""

import logging
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)


def add_referral(referrer_id, referred_id):
    """
    Добавить реферальную связь и начислить бонус
    
    Args:
        referrer_id: ID пользователя, который пригласил
        referred_id: ID приглашенного пользователя
        
    Returns:
        dict: {'success': bool, 'tokens_awarded': int, 'message': str}
    """
    try:
        # Проверяем, что пользователь не приглашает сам себя
        if referrer_id == referred_id:
            logger.warning(f"⚠️ Попытка самореферала: user_id={referrer_id}")
            return {
                'success': False,
                'tokens_awarded': 0,
                'message': '❌ Нельзя пригласить самого себя'
            }
        
        # Проверяем, не был ли уже приглашен этот пользователь
        existing = execute_query_sync(
            "SELECT id FROM referrals WHERE referred_id = %s",
            (referred_id,)
        )
        
        if existing and len(existing) > 0:
            logger.info(f"ℹ️ Пользователь {referred_id} уже был приглашен ранее")
            return {
                'success': False,
                'tokens_awarded': 0,
                'message': 'ℹ️ Пользователь уже зарегистрирован по реферальной ссылке'
            }
        
        # Создаем запись в referrals
        execute_query_sync(
            "INSERT INTO referrals (referrer_id, referred_id, bonus_paid) VALUES (%s, %s, TRUE)",
            (referrer_id, referred_id)
        )
        logger.info(f"✅ Создана реферальная связь: {referrer_id} → {referred_id}")
        
        # Обновляем invited_by в таблице users
        execute_query_sync(
            "UPDATE users SET invited_by = %s WHERE user_id = %s",
            (referrer_id, referred_id)
        )
        
        # Начисляем 2 токена рефереру
        execute_query_sync(
            "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
            (referrer_id,)
        )
        logger.info(f"💰 Начислено 2 токена пользователю {referrer_id} за приглашение {referred_id}")
        
        # Проверяем, не 5-й ли это реферал
        referral_count = get_referral_count(referrer_id)
        
        tokens_awarded = 2
        bonus_message = ""
        
        if referral_count == 5:
            # Проверяем, не выдали ли уже бонус
            bonus_given = execute_query_sync(
                "SELECT referral_bonus_given FROM users WHERE user_id = %s",
                (referrer_id,)
            )
            
            if bonus_given and bonus_given[0][0] is False:
                # Начисляем дополнительные 5 токенов
                execute_query_sync(
                    "UPDATE users SET balance = balance + 5, referral_bonus_given = TRUE WHERE user_id = %s",
                    (referrer_id,)
                )
                tokens_awarded = 7  # 2 + 5
                bonus_message = "\n\n🎁 БОНУС! Это ваш 5-й друг! Дополнительно +5 токенов!"
                logger.info(f"🎁 Начислен бонус 5 токенов пользователю {referrer_id} за 5-го реферала")
            else:
                logger.info(f"ℹ️ Бонус за 5-го реферала уже был выдан пользователю {referrer_id}")
        
        return {
            'success': True,
            'tokens_awarded': tokens_awarded,
            'message': f'✅ Реферал добавлен! +{tokens_awarded} токенов{bonus_message}'
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления реферала: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'tokens_awarded': 0,
            'message': '❌ Ошибка при обработке реферальной ссылки'
        }


def get_referral_count(user_id):
    """
    Получить количество приглашенных пользователей
    
    Args:
        user_id: ID пользователя
        
    Returns:
        int: Количество рефералов
    """
    try:
        result = execute_query_sync(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = %s",
            (user_id,)
        )
        
        if not result:
            return 0
        
        return result[0][0]
    except Exception as e:
        logger.error(f"❌ Ошибка получения количества рефералов: {e}")
        return 0


def get_referral_progress(user_id):
    """
    Получить прогресс по рефералам (X/5)
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: {'count': int, 'progress': str, 'bonus_available': bool}
    """
    try:
        count = get_referral_count(user_id)
        progress = f"{count}/5"
        bonus_available = count >= 5
        
        # Проверяем, был ли получен бонус
        bonus_received = execute_query_sync(
            "SELECT referral_bonus_given FROM users WHERE user_id = %s",
            (user_id,)
        )
        
        bonus_given = bonus_received[0][0] if bonus_received and bonus_received[0][0] is not None else False
        
        return {
            'count': count,
            'progress': progress,
            'bonus_available': bonus_available,
            'bonus_received': bonus_given
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения прогресса рефералов: {e}")
        return {
            'count': 0,
            'progress': '0/5',
            'bonus_available': False,
            'bonus_received': False
        }


def get_referral_link(user_id, bot_username="club235442407"):
    """
    Сгенерировать реферальную ссылку для пользователя
    
    Args:
        user_id: ID пользователя VK
        bot_username: Username группы ВК (без @)
        
    Returns:
        str: Реферальная ссылка
    """
    # Для ВК реферальные ссылки работают через payload кнопки "Начать"
    # Формат: https://vk.com/{bot_username}?ref=ref_{user_id}
    return f"https://vk.com/{bot_username}?ref=ref_{user_id}"


def parse_referral_code(ref_string):
    """
    Извлечь ID реферера из строки ref_XXX
    
    Args:
        ref_string: Строка вида "ref_123456"
        
    Returns:
        int или None: ID реферера
    """
    try:
        if not ref_string or not isinstance(ref_string, str):
            return None
        
        # Убираем префикс "ref_"
        if ref_string.startswith("ref_"):
            referrer_id_str = ref_string[4:]  # Убираем "ref_"
            return int(referrer_id_str)
        
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга реферального кода: {e}")
        return None


def get_referral_stats(user_id):
    """
    Получить подробную статистику по рефералам
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Статистика
    """
    try:
        # Количество рефералов
        count = get_referral_count(user_id)
        
        # Заработано токенов
        tokens_earned = count * 2  # По 2 токена за каждого
        
        # Проверяем бонус за 5-го
        bonus_received = execute_query_sync(
            "SELECT referral_bonus_given FROM users WHERE user_id = %s",
            (user_id,)
        )
        
        if bonus_received and bonus_received[0][0]:
            tokens_earned += 5
        
        # Получаем список рефералов
        referrals = execute_query_sync(
            """SELECT r.referred_id, u.first_name, r.created_at 
               FROM referrals r
               LEFT JOIN users u ON r.referred_id = u.user_id
               WHERE r.referrer_id = %s
               ORDER BY r.created_at DESC""",
            (user_id,)
        )
        
        referral_list = []
        if referrals:
            for ref in referrals:
                referral_list.append({
                    'id': ref[0],
                    'name': ref[1] or 'Пользователь',
                    'date': ref[2]
                })
        
        return {
            'count': count,
            'tokens_earned': tokens_earned,
            'bonus_received': bonus_received[0][0] if bonus_received else False,
            'referrals': referral_list
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики рефералов: {e}")
        return {
            'count': 0,
            'tokens_earned': 0,
            'bonus_received': False,
            'referrals': []
        }
