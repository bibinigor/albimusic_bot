import logging
from database_adapter import db

logger = logging.getLogger(__name__)

async def get_user_balance(user_id):
    """Получить баланс пользователя"""
    try:
        result = await db.fetch_query(
            'SELECT balance FROM users WHERE user_id = $1',
            user_id
        )
        if result:
            return result[0]['balance']
        else:
            # Создаем пользователя если не существует
            await db.execute_query(
                'INSERT INTO users (user_id, balance) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING',
                user_id, 3  # 3 бесплатные генерации
            )
            return 3
    except Exception as e:
        logger.error(f"❌ Ошибка получения баланса: {e}")
        return 3

async def update_user_balance(user_id, amount):
    """Обновить баланс пользователя"""
    try:
        await db.execute_query(
            'INSERT INTO users (user_id, balance) VALUES ($1, $2) '
            'ON CONFLICT (user_id) DO UPDATE SET balance = users.balance + $2',
            user_id, amount
        )
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления баланса: {e}")
        return False

async def create_payment(user_id, amount, description=""):
    """Создать платеж"""
    try:
        # Здесь будет интеграция с ЮКассой
        # Пока просто обновляем баланс
        await update_user_balance(user_id, amount)
        return {"status": "success", "balance_change": amount}
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {"status": "error"}
