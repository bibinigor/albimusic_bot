"""
БЛОК 7: Интеграция платежной системы YooKassa в VK-бота
========================================================

Этот файл содержит код для интеграции в main_vk.py

Инструкции:
1. Добавить import в начале main_vk.py
2. Добавить обработчик кнопки "💰 Баланс"
3. Добавить обработчики callback для тарифов
4. Настроить webhook для YooKassa
"""

# ========================================
# 1. ИМПОРТЫ (добавить в начало main_vk.py)
# ========================================

import vk_payments
from flask import Flask, request, jsonify
import threading

# Инициализация Flask для webhook (если еще нет)
# webhook_app = Flask(__name__)


# ========================================
# 2. ОБРАБОТЧИК КНОПКИ "💰 БАЛАНС"
# ========================================

def handle_balance_button(event, vk_api, state_manager):
    """
    Обработчик кнопки "💰 Баланс" в главном меню.
    
    Показывает:
    - Текущий баланс пользователя
    - Доступные тарифы
    - Кнопки для покупки токенов
    - Кнопку "Пригласить друга"
    """
    user_id = event.obj['message']['from_id']
    
    # Получаем баланс пользователя
    from db_utils import fetch_one_sync
    user = fetch_one_sync(
        "SELECT balance FROM users WHERE user_id = %s",
        (user_id,)
    )
    
    balance = user['balance'] if user else 0
    
    # Форматируем сообщение
    message = vk_payments.format_balance_message(balance)
    
    # Создаем клавиатуру с тарифами
    keyboard = {
        'inline': True,
        'buttons': []
    }
    
    # Кнопки с тарифами (по 2 в ряд)
    tariff_buttons = []
    for amount in [50, 250, 500, 1000, 2000]:
        tariff = vk_payments.TARIFFS[amount]
        tariff_buttons.append({
            'action': {
                'type': 'callback',
                'label': f"{tariff['emoji']} {amount}₽",
                'payload': json.dumps({'cmd': 'pay', 'amount': amount})
            },
            'color': 'positive' if amount == 250 else 'primary'  # Выделяем популярный тариф
        })
    
    # Группируем по 2 кнопки в ряд
    for i in range(0, len(tariff_buttons), 2):
        row = tariff_buttons[i:i+2]
        keyboard['buttons'].append(row)
    
    # Дополнительные кнопки
    keyboard['buttons'].append([
        {
            'action': {
                'type': 'callback',
                'label': '🌟 Пригласить друга',
                'payload': json.dumps({'cmd': 'invite_friend'})
            },
            'color': 'secondary'
        }
    ])
    
    keyboard['buttons'].append([
        {
            'action': {
                'type': 'callback',
                'label': '📜 История платежей',
                'payload': json.dumps({'cmd': 'payment_history'})
            },
            'color': 'secondary'
        }
    ])
    
    # Отправляем сообщение
    vk_api.messages.send(
        peer_id=user_id,
        message=message,
        keyboard=json.dumps(keyboard),
        random_id=0
    )


# ========================================
# 3. ОБРАБОТЧИК CALLBACK ДЛЯ ТАРИФОВ
# ========================================

async def handle_payment_callback(event, vk_api, config):
    """
    Обработчик callback для создания платежа.
    
    Вызывается когда пользователь нажимает кнопку с тарифом.
    """
    user_id = event.obj['user_id']
    payload = json.loads(event.obj['payload'])
    
    cmd = payload.get('cmd')
    amount = payload.get('amount')
    
    if cmd == 'pay' and amount:
        # Создаем платеж через YooKassa
        result = await vk_payments.create_payment(
            shop_id=config.YOOKASSA_SHOP_ID,
            secret_key=config.YOOKASSA_SECRET_KEY,
            user_id=user_id,
            amount=amount,
            vk_group_id=config.VK_GROUP_ID
        )
        
        if result:
            payment_url = result['payment_url']
            payment_id = result['payment_id']
            
            tariff = vk_payments.TARIFFS[amount]
            
            # Создаем кнопку для перехода к оплате
            keyboard = {
                'inline': True,
                'buttons': [[
                    {
                        'action': {
                            'type': 'open_link',
                            'label': '💳 Перейти к оплате',
                            'link': payment_url
                        }
                    }
                ]]
            }
            
            message = (
                f"💳 Оплата: {amount}₽\n"
                f"🎁 Получите: {tariff['tokens']} токенов\n\n"
                f"Нажмите кнопку ниже для перехода к оплате 👇"
            )
            
            vk_api.messages.send(
                peer_id=user_id,
                message=message,
                keyboard=json.dumps(keyboard),
                random_id=0
            )
            
            logger.info(f"✅ Платеж {payment_id} создан для user {user_id}")
        else:
            vk_api.messages.send(
                peer_id=user_id,
                message="❌ Ошибка создания платежа. Попробуйте позже.",
                random_id=0
            )
            logger.error(f"❌ Не удалось создать платеж для user {user_id}")
    
    elif cmd == 'payment_history':
        # Показываем историю платежей
        payments = vk_payments.get_user_payments(user_id, limit=10)
        message = vk_payments.format_payment_history(payments)
        
        vk_api.messages.send(
            peer_id=user_id,
            message=message,
            random_id=0
        )
    
    elif cmd == 'invite_friend':
        # Реферальная программа (БЛОК 4)
        from vk_referral_system import handle_invite_friend_callback
        handle_invite_friend_callback(event, vk_api)


# ========================================
# 4. WEBHOOK ДЛЯ YOOKASSA
# ========================================

@webhook_app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    """
    Webhook для обработки уведомлений от YooKassa.
    
    Настройте этот URL в личном кабинете YooKassa:
    https://your-domain.com/webhook/yookassa
    
    Важно: Webhook должен быть доступен по HTTPS!
    """
    try:
        notification = request.json
        logger.info(f"📩 Webhook от YooKassa: {notification}")
        
        # Обрабатываем платеж
        success = vk_payments.process_webhook(notification)
        
        if success:
            # Извлекаем данные для уведомления пользователя
            payment = notification.get('object', {})
            metadata = payment.get('metadata', {})
            user_id = int(metadata.get('user_id', 0))
            tokens = int(metadata.get('tokens', 0))
            
            if user_id and tokens:
                # Отправляем уведомление пользователю
                try:
                    keyboard = {
                        'inline': True,
                        'buttons': [[
                            {
                                'action': {
                                    'type': 'callback',
                                    'label': '🎵 Создать песню',
                                    'payload': json.dumps({'cmd': 'create_song'})
                                },
                                'color': 'positive'
                            },
                            {
                                'action': {
                                    'type': 'callback',
                                    'label': '🎶 Создать музыку',
                                    'payload': json.dumps({'cmd': 'create_music'})
                                },
                                'color': 'primary'
                            }
                        ]]
                    }
                    
                    message = (
                        f"🎉 Спасибо! Оплата поступила!\n\n"
                        f"💰 Начислено: {tokens} токенов\n\n"
                        f"🎵 Теперь вы можете создавать песни!\n\n"
                        f"Нажмите кнопку ниже чтобы начать 👇"
                    )
                    
                    vk_api.messages.send(
                        peer_id=user_id,
                        message=message,
                        keyboard=json.dumps(keyboard),
                        random_id=0
                    )
                    
                    logger.info(f"✅ Уведомление отправлено user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Не удалось отправить уведомление user {user_id}: {e}")
            
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'ignored'}), 200
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 400


# ========================================
# 5. ЗАПУСК WEBHOOK СЕРВЕРА
# ========================================

def run_webhook_server(port=5001):
    """
    Запустить Flask сервер для webhook в отдельном потоке.
    
    Вызывать при старте бота:
    threading.Thread(target=run_webhook_server, daemon=True).start()
    """
    logger.info(f"🚀 Запуск webhook сервера на порту {port}")
    webhook_app.run(host='0.0.0.0', port=port, debug=False)


# ========================================
# 6. ИНТЕГРАЦИЯ В ОСНОВНОЙ КОД
# ========================================

"""
ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ:

1. В начале main_vk.py добавить:
   
   import vk_payments
   from flask import Flask, request, jsonify
   
   webhook_app = Flask(__name__)

2. В функции main() перед longpoll.listen() добавить:
   
   # Запускаем webhook сервер в фоне
   import threading
   threading.Thread(
       target=run_webhook_server, 
       args=(5001,), 
       daemon=True
   ).start()

3. В обработчике текстовых сообщений добавить:
   
   elif text == '💰 Баланс':
       handle_balance_button(event, vk_api, state_manager)

4. В обработчике event_type == 'message_event' добавить:
   
   payload = json.loads(event.obj.get('payload', '{}'))
   cmd = payload.get('cmd')
   
   if cmd in ['pay', 'payment_history', 'invite_friend']:
       await handle_payment_callback(event, vk_api, config)

5. Настроить webhook в YooKassa:
   - URL: https://your-domain.com/webhook/yookassa
   - Метод: POST
   - Событие: payment.succeeded

6. Проверить переменные в config.py:
   - YOOKASSA_SHOP_ID
   - YOOKASSA_SECRET_KEY
   - VK_GROUP_ID
"""
