"""
VK Payments Module - YooKassa Integration
==========================================
Платежная система для VK-бота через YooKassa.
Полная синхронизация с Telegram-ботом (эталон).

Архитектура:
1. Пользователь нажимает кнопку с тарифом
2. create_payment() создает платеж в YooKassa
3. Пользователь переходит по URL оплаты
4. После оплаты YooKassa отправляет webhook
5. process_webhook() начисляет токены автоматически
6. Отправляется уведомление пользователю

Тарифы (синхронизированы с ТГ-ботом):
- 50₽ → 1 токен (2 песни)
- 250₽ → 10 токенов (20 песен)
- 500₽ → 25 токенов (50 песен)
- 1000₽ → 60 токенов (120 песен)
- 2000₽ → 140 токенов (280 песен)
"""

import logging
import uuid
import base64
import aiohttp
from typing import Dict, Optional
from db_utils import execute_query_sync, fetch_one_sync, fetch_all_sync

logger = logging.getLogger(__name__)

# Тарифы (синхронизированы с Telegram-ботом)
TARIFFS = {
    50: {
        'tokens': 1,
        'description': '1 токен (2 песни)',
        'emoji': '💫'
    },
    250: {
        'tokens': 10,
        'description': '10 токенов (20 песен)',
        'emoji': '💳'
    },
    500: {
        'tokens': 25,
        'description': '25 токенов (50 песен)',
        'emoji': '🔥'
    },
    1000: {
        'tokens': 60,
        'description': '60 токенов (120 песен)',
        'emoji': '⭐'
    },
    2000: {
        'tokens': 140,
        'description': '140 токенов (280 песен)',
        'emoji': '💎'
    }
}


async def create_payment(
    shop_id: str,
    secret_key: str,
    user_id: int,
    amount: int,
    vk_group_id: int
) -> Optional[Dict]:
    """
    Создать платеж через YooKassa (асинхронно).
    
    Args:
        shop_id: ID магазина в YooKassa
        secret_key: Секретный ключ YooKassa
        user_id: VK ID пользователя
        amount: Сумма в рублях (50, 250, 500, 1000, 2000)
        vk_group_id: ID группы VK (для return_url)
        
    Returns:
        Dict: {
            'payment_url': str,  # URL для оплаты
            'payment_id': str    # ID платежа в YooKassa
        } или None при ошибке
        
    Пример:
        result = await create_payment(
            shop_id="123456",
            secret_key="live_XXX",
            user_id=12345,
            amount=250,
            vk_group_id=123456789
        )
        # {'payment_url': 'https://yookassa.ru/...', 'payment_id': 'uuid'}
    """
    try:
        if amount not in TARIFFS:
            logger.error(f"❌ Неверная сумма: {amount}₽ (доступны: {list(TARIFFS.keys())})")
            return None
            
        tariff = TARIFFS[amount]
        
        # Генерируем уникальный ключ идемпотентности
        idempotence_key = str(uuid.uuid4())
        
        # Формируем данные платежа
        payment_data = {
            'amount': {
                'value': f"{amount:.2f}",
                'currency': 'RUB'
            },
            'capture': True,
            'confirmation': {
                'type': 'redirect',
                'return_url': f'https://vk.com/club{vk_group_id}?success=true'
            },
            'description': f'ALBImusic: {tariff["description"]}',
            'metadata': {
                'user_id': str(user_id),
                'tokens': tariff['tokens'],
                'platform': 'vk'
            }
        }
        
        # Заголовки для запроса
        headers = {
            'Idempotence-Key': idempotence_key,
            'Content-Type': 'application/json'
        }
        
        # Basic Auth для YooKassa
        auth_string = f"{shop_id}:{secret_key}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        headers['Authorization'] = f'Basic {auth_header}'
        
        # Отправляем запрос в YooKassa
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.yookassa.ru/v3/payments',
                json=payment_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    payment_id = result.get('id')
                    payment_url = result.get('confirmation', {}).get('confirmation_url')
                    
                    if not payment_id or not payment_url:
                        logger.error(f"❌ Некорректный ответ от YooKassa: {result}")
                        return None
                    
                    # Сохраняем платеж в БД
                    _create_payment_record(user_id, amount, tariff['tokens'], payment_id)
                    
                    logger.info(
                        f"✅ Создан платеж {payment_id}: "
                        f"user {user_id}, {amount}₽, {tariff['tokens']} токенов"
                    )
                    
                    return {
                        'payment_url': payment_url,
                        'payment_id': payment_id
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка YooKassa API: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}", exc_info=True)
        return None


def process_webhook(notification: Dict) -> bool:
    """
    Обработать webhook от YooKassa о статусе платежа (синхронно).
    
    Args:
        notification: Данные webhook от YooKassa
        
    Returns:
        bool: True если обработка успешна, иначе False
        
    Структура notification:
    {
        'event': 'payment.succeeded',
        'object': {
            'id': 'payment_id',
            'amount': {'value': '250.00'},
            'metadata': {'user_id': '12345', 'tokens': 10}
        }
    }
    
    Важно: Эта функция вызывается из веб-сервера (Flask/aiohttp)!
    """
    try:
        if notification.get('event') != 'payment.succeeded':
            logger.info(f"Webhook пропущен: event={notification.get('event')}")
            return False
        
        payment = notification.get('object', {})
        payment_id = payment.get('id')
        
        if not payment_id:
            logger.error("❌ Отсутствует payment_id в webhook")
            return False
        
        # Извлекаем данные
        metadata = payment.get('metadata', {})
        user_id = int(metadata.get('user_id', 0))
        tokens = int(metadata.get('tokens', 0))
        amount = float(payment.get('amount', {}).get('value', 0))
        
        if not user_id or not tokens:
            logger.error(f"❌ Некорректные данные в webhook: user_id={user_id}, tokens={tokens}")
            return False
        
        # Проверяем, не обработан ли уже этот платеж
        existing = fetch_one_sync(
            "SELECT status FROM payments WHERE payment_id = %s",
            (payment_id,)
        )
        
        if existing and existing['status'] == 'succeeded':
            logger.warning(f"⚠️ Платеж {payment_id} уже обработан (дубликат webhook)")
            return True  # Не ошибка, просто дубликат
        
        # Начисляем токены
        execute_query_sync(
            "UPDATE users SET balance = balance + %s WHERE user_id = %s",
            (tokens, user_id)
        )
        
        # Обновляем статус платежа в БД
        execute_query_sync(
            """
            UPDATE payments 
            SET status = 'succeeded', 
                payment_id = %s,
                updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s AND amount = %s AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (payment_id, user_id, amount)
        )
        
        logger.info(
            f"✅ Платеж {payment_id} обработан: "
            f"user {user_id} получил {tokens} токенов за {amount}₽"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}", exc_info=True)
        return False


def _create_payment_record(
    user_id: int, 
    amount: int, 
    tokens: int, 
    payment_id: str
) -> bool:
    """
    Создать запись о платеже в БД (синхронно).
    
    Args:
        user_id: VK ID пользователя
        amount: Сумма в рублях
        tokens: Количество токенов
        payment_id: ID платежа в YooKassa
        
    Returns:
        bool: True если успешно, иначе False
    """
    try:
        execute_query_sync(
            """
            INSERT INTO payments (user_id, amount, status, payment_id, created_at, updated_at)
            VALUES (%s, %s, 'pending', %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (user_id, amount, payment_id)
        )
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания записи платежа: {e}", exc_info=True)
        return False


def get_user_payments(user_id: int, limit: int = 10) -> list:
    """
    Получить историю платежей пользователя (синхронно).
    
    Args:
        user_id: VK ID пользователя
        limit: Максимальное количество записей
        
    Returns:
        List[Dict]: История платежей
        
    Пример:
        payments = get_user_payments(12345, limit=5)
        for p in payments:
            print(f"{p['amount']}₽ - {p['status']} - {p['created_at']}")
    """
    try:
        payments = fetch_all_sync(
            """
            SELECT 
                id, 
                amount, 
                status, 
                payment_id,
                created_at,
                updated_at
            FROM payments 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """,
            (user_id, limit)
        )
        
        return [
            {
                'id': p['id'],
                'amount': float(p['amount']),
                'status': p['status'],
                'tokens': TARIFFS.get(int(p['amount']), {}).get('tokens', 0),
                'payment_id': p['payment_id'],
                'created_at': p['created_at'],
                'updated_at': p['updated_at']
            }
            for p in payments
        ]
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории платежей: {e}", exc_info=True)
        return []


def format_balance_message(user_balance: int) -> str:
    """
    Форматировать сообщение с балансом и тарифами.
    
    Args:
        user_balance: Текущий баланс пользователя
        
    Returns:
        str: Отформатированное сообщение
    """
    message = f"💰 Ваш баланс: {user_balance} токенов\n\n"
    message += "📋 Доступные тарифы:\n\n"
    
    for amount in sorted(TARIFFS.keys()):
        tariff = TARIFFS[amount]
        message += (
            f"{tariff['emoji']} {tariff['description']} — {amount}₽\n"
        )
    
    message += "\n💡 1 токен = 2 песни (с текстом или без)\n"
    message += "🎁 Пригласи друга — получи 2 токена в подарок!\n"
    message += "🎉 За 5 друзей — бонус 5 токенов!"
    
    return message


# Эмодзи для статусов платежей (для UI)
PAYMENT_STATUS_EMOJI = {
    'pending': '⏳',
    'succeeded': '✅',
    'failed': '❌',
    'cancelled': '🚫'
}


def format_payment_status(status: str) -> str:
    """
    Форматировать статус платежа с эмодзи.
    
    Args:
        status: Статус платежа
        
    Returns:
        str: Статус с эмодзи
    """
    emoji = PAYMENT_STATUS_EMOJI.get(status, '❓')
    status_text = {
        'pending': 'Ожидает оплаты',
        'succeeded': 'Успешно',
        'failed': 'Ошибка',
        'cancelled': 'Отменен'
    }.get(status, status)
    
    return f"{emoji} {status_text}"


def format_payment_history(payments: list) -> str:
    """
    Форматировать историю платежей для вывода пользователю.
    
    Args:
        payments: Список платежей из get_user_payments()
        
    Returns:
        str: Отформатированная история
    """
    if not payments:
        return "📜 История платежей пуста"
    
    message = "📜 История ваших платежей:\n\n"
    
    for p in payments:
        date = p['created_at'].strftime('%d.%m.%Y %H:%M')
        status = format_payment_status(p['status'])
        message += (
            f"{status} {p['amount']}₽ ({p['tokens']} токенов)\n"
            f"   {date}\n\n"
        )
    
    return message
