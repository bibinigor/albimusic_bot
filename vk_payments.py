"""
Модуль для работы с платежами через VK Pay
"""
import logging
import hashlib
import json
from typing import Optional, Dict
import hmac
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class VKPayments:
    def __init__(self, merchant_id: str, secret_key: str):
        """
        Инициализация обработчика платежей
        
        Args:
            merchant_id: ID продавца VK Pay
            secret_key: Секретный ключ для подписи запросов
        """
        self.merchant_id = merchant_id
        self.secret_key = secret_key.encode('utf-8')
        
        # Стоимость токенов
        self.TOKEN_PRICES = {
            '5': 149,    # 5 токенов за 149 руб
            '10': 249,   # 10 токенов за 249 руб
            '20': 449,   # 20 токенов за 449 руб
            '50': 999    # 50 токенов за 999 руб
        }

    def create_payment_url(self, amount: str, user_id: int) -> Optional[str]:
        """
        Создать URL для оплаты через VK Pay
        
        Args:
            amount: Количество токенов для покупки ('5', '10', '20' или '50')
            user_id: VK ID пользователя
            
        Returns:
            URL для оплаты или None в случае ошибки
        """
        try:
            if amount not in self.TOKEN_PRICES:
                logger.error(f"❌ Неверная сумма токенов: {amount}")
                return None

            price = self.TOKEN_PRICES[amount]
            order_id = f"tokens_{amount}_{user_id}_{int(datetime.now().timestamp())}"
            
            # Формируем параметры платежа
            payment_params = {
                "amount": price,
                "currency": "RUB",
                "order_id": order_id,
                "merchant_id": self.merchant_id,
                "ts": int(datetime.now().timestamp()),
                "description": f"Покупка {amount} токенов в боте ALBImusic",
                "success_url": f"https://vk.com/app51787269#success_{order_id}",
                "fail_url": f"https://vk.com/app51787269#fail_{order_id}",
            }
            
            # Создаем подпись
            params_to_sign = [
                str(payment_params[key]) 
                for key in sorted(payment_params.keys())
            ]
            params_str = ":".join(params_to_sign)
            
            signature = hmac.new(
                self.secret_key,
                params_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Добавляем подпись
            payment_params['sign'] = signature
            
            # Кодируем параметры в base64
            params_json = json.dumps(payment_params)
            params_b64 = base64.b64encode(params_json.encode('utf-8')).decode('utf-8')
            
            # Формируем URL
            return f"https://vk.com/vkpay#action=pay-to-service&params={params_b64}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            return None

    def verify_callback(self, data: Dict, signature: str) -> bool:
        """
        Проверить подпись callback от VK Pay
        
        Args:
            data: Данные callback
            signature: Подпись от VK Pay
            
        Returns:
            True если подпись верна, иначе False
        """
        try:
            # Сортируем ключи
            sorted_data = dict(sorted(data.items()))
            
            # Формируем строку для подписи
            params_str = ":".join(str(v) for v in sorted_data.values())
            
            # Создаем подпись
            expected_signature = hmac.new(
                self.secret_key,
                params_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки подписи: {e}")
            return False

    def parse_order_id(self, order_id: str) -> Optional[Dict]:
        """
        Распарсить order_id для получения информации о платеже
        
        Args:
            order_id: ID заказа в формате tokens_amount_user_id_timestamp
            
        Returns:
            Словарь с информацией о платеже или None
        """
        try:
            parts = order_id.split('_')
            if len(parts) != 4 or parts[0] != 'tokens':
                return None
                
            return {
                'amount': parts[1],
                'user_id': int(parts[2]),
                'timestamp': int(parts[3])
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга order_id: {e}")
            return None

    def get_token_amount(self, price: int) -> Optional[int]:
        """
        Получить количество токенов по цене
        
        Args:
            price: Сумма платежа
            
        Returns:
            Количество токенов или None если цена не найдена
        """
        for tokens, token_price in self.TOKEN_PRICES.items():
            if token_price == price:
                return int(tokens)
        return None