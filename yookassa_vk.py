"""
Модуль для работы с ЮKassa в VK боте
"""
import logging
import uuid
import json
import hmac
import hashlib
import base64
from typing import Optional, Dict
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class YooKassaVK:
    def __init__(self, shop_id: str, secret_key: str):
        """
        Инициализация обработчика платежей ЮKassa
        
        Args:
            shop_id: ID магазина в ЮKassa
            secret_key: Секретный ключ
        """
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.api_url = 'https://api.yookassa.ru/v3'
        
        # Стоимость токенов
        self.TOKEN_PRICES = {
            '5': 149,    # 5 токенов за 149 руб
            '10': 249,   # 10 токенов за 249 руб
            '20': 449,   # 20 токенов за 449 руб
            '50': 999    # 50 токенов за 999 руб
        }

    def create_payment(self, amount: str, user_id: int) -> Optional[Dict]:
        """
        Создать платеж в ЮKassa
        
        Args:
            amount: Количество токенов для покупки ('5', '10', '20' или '50')
            user_id: VK ID пользователя
            
        Returns:
            Словарь с данными платежа или None в случае ошибки
        """
        try:
            if amount not in self.TOKEN_PRICES:
                logger.error(f"❌ Неверная сумма токенов: {amount}")
                return None

            price = self.TOKEN_PRICES[amount]
            idempotence_key = str(uuid.uuid4())
            
            headers = {
                'Idempotence-Key': idempotence_key,
                'Content-Type': 'application/json'
            }
            
            auth_string = f"{self.shop_id}:{self.secret_key}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            headers['Authorization'] = f'Basic {auth_header}'
            
            payment_data = {
                'amount': {
                    'value': str(price),
                    'currency': 'RUB'
                },
                'capture': True,
                'confirmation': {
                    'type': 'redirect',
                    'return_url': f'https://vk.com/app51787269#success_{amount}_{user_id}'
                },
                'description': f'Покупка {amount} токенов в боте ALBImusic',
                'metadata': {
                    'user_id': user_id,
                    'tokens': amount,
                    'source': 'vk'  # Маркер: платеж из VK-бота
                }
            }
            
            response = requests.post(
                f'{self.api_url}/payments',
                json=payment_data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка создания платежа: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            return None

    def verify_notification(self, data: Dict, signature: str) -> bool:
        """
        Проверить подпись уведомления от ЮKassa
        
        Args:
            data: Данные уведомления
            signature: Подпись от ЮKassa
            
        Returns:
            True если подпись верна, иначе False
        """
        try:
            # Формируем строку для подписи
            notification_data = json.dumps(data, separators=(',', ':'))
            
            # Создаем подпись
            secret_key_bytes = self.secret_key.encode()
            notification_bytes = notification_data.encode()
            calculated_signature = hmac.new(
                secret_key_bytes,
                notification_bytes,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(calculated_signature, signature)
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки подписи: {e}")
            return False

    def get_payment_status(self, payment_id: str) -> Optional[Dict]:
        """
        Получить статус платежа
        
        Args:
            payment_id: ID платежа в ЮKassa
            
        Returns:
            Словарь с данными платежа или None в случае ошибки
        """
        try:
            auth_string = f"{self.shop_id}:{self.secret_key}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.api_url}/payments/{payment_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка получения статуса платежа: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса платежа: {e}")
            return None