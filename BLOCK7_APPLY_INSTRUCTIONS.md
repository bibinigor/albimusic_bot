# 🔴 БЛОК 7: Платежная система YooKassa

## 📋 Решаемая проблема

**Из GAP-анализа:** Критическая проблема #2 — отсутствует автоматическая платежная система.

**Текущее состояние:** При нажатии "💰 Баланс" бот говорит "Напишите в поддержку" (ручное начисление).

**Новое состояние:** Полностью автоматическая оплата через YooKassa с мгновенным начислением токенов.

---

## 🎯 Что реализовано

### ✅ Функциональность:
1. **Интеграция YooKassa** — создание платежей через API
2. **Webhook обработка** — автоматическое начисление токенов после оплаты
3. **История платежей** — просмотр всех транзакций
4. **Тарифы** — синхронизированы с Telegram-ботом (50₽, 250₽, 500₽, 1000₽, 2000₽)
5. **Уведомления** — пользователь получает сообщение сразу после оплаты

### 🔧 Технические детали:
- Асинхронные запросы к YooKassa (aiohttp)
- Basic Auth для безопасности
- Идемпотентность (защита от дублей)
- Webhook с проверкой дубликатов
- Транзакции в БД (статусы: pending → succeeded)

---

## 📁 Созданные файлы

1. **`vk_payments.py`** — модуль платежной системы (394 строки, 10 функций)
2. **`main_vk_BLOCK7_PAYMENTS_INTEGRATION.py`** — интеграционный код (280 строк)

---

## 🗄️ Изменения в БД

**Таблица `payments` уже существует!** Проверьте её структуру:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'payments';
```

Должны быть поля:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (BIGINT)
- `amount` (NUMERIC или INT)
- `status` (VARCHAR) — 'pending', 'succeeded', 'failed', 'cancelled'
- `payment_id` (VARCHAR) — ID платежа в YooKassa
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

Если таблицы нет, создайте:

```sql
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_payment_id ON payments(payment_id);
CREATE INDEX idx_payments_status ON payments(status);
```

---

## 🔧 Шаг 1: Подготовка

### 1.1. Проверьте config.py

Убедитесь, что в `config.py` есть:

```python
# YooKassa
YOOKASSA_SHOP_ID = "your_shop_id"  # ID магазина
YOOKASSA_SECRET_KEY = "live_XXXXXX"  # Секретный ключ

# VK
VK_GROUP_ID = 123456789  # ID вашей группы VK
```

Если переменных нет, добавьте их!

### 1.2. Проверьте зависимости

```bash
pip install flask aiohttp
```

Если уже установлены, ничего не делайте.

---

## 🔧 Шаг 2: Интеграция кода

### 2.1. Добавьте импорты в начало main_vk.py

Найдите блок импортов (примерно строки 1-30) и добавьте:

```python
import vk_payments
from flask import Flask, request, jsonify
import threading
```

### 2.2. Создайте Flask приложение

После импортов (примерно строка 50), добавьте:

```python
# Flask для webhook YooKassa
webhook_app = Flask(__name__)
```

### 2.3. Добавьте обработчик кнопки "💰 Баланс"

Найдите функцию обработки текстовых сообщений (примерно строка 800-1000).

Ищите блок:
```python
elif text == '💰 Баланс':
    # Текущий код (возможно "Напишите в поддержку")
```

**ЗАМЕНИТЕ** на:

```python
elif text == '💰 Баланс':
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
            'color': 'positive' if amount == 250 else 'primary'
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
```

### 2.4. Добавьте обработчик callback для платежей

Найдите обработчик `event_type == 'message_event'` (примерно строка 1500-1700).

Внутри этого блока добавьте:

```python
elif event_type == 'message_event':
    user_id = event.obj['user_id']
    payload_str = event.obj.get('payload', '{}')
    
    try:
        payload = json.loads(payload_str)
        cmd = payload.get('cmd')
        
        # ОБРАБОТКА ПЛАТЕЖЕЙ
        if cmd == 'pay':
            amount = payload.get('amount')
            
            # Создаем платеж через YooKassa
            result = asyncio.run(vk_payments.create_payment(
                shop_id=config.YOOKASSA_SHOP_ID,
                secret_key=config.YOOKASSA_SECRET_KEY,
                user_id=user_id,
                amount=amount,
                vk_group_id=config.VK_GROUP_ID
            ))
            
            if result:
                payment_url = result['payment_url']
                tariff = vk_payments.TARIFFS[amount]
                
                # Кнопка для оплаты
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
            else:
                vk_api.messages.send(
                    peer_id=user_id,
                    message="❌ Ошибка создания платежа. Попробуйте позже.",
                    random_id=0
                )
        
        elif cmd == 'payment_history':
            # История платежей
            payments = vk_payments.get_user_payments(user_id, limit=10)
            message = vk_payments.format_payment_history(payments)
            
            vk_api.messages.send(
                peer_id=user_id,
                message=message,
                random_id=0
            )
        
        # Остальные callback...
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}", exc_info=True)
```

### 2.5. Добавьте webhook обработчик

**В КОНЕЦ ФАЙЛА** (перед `if __name__ == "__main__":`), добавьте:

```python
# ========================================
# WEBHOOK ДЛЯ YOOKASSA
# ========================================

@webhook_app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    """Webhook для обработки уведомлений от YooKassa"""
    try:
        notification = request.json
        logger.info(f"📩 Webhook от YooKassa: {notification}")
        
        # Обрабатываем платеж
        success = vk_payments.process_webhook(notification)
        
        if success:
            # Извлекаем данные для уведомления
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
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки уведомления: {e}")
            
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'ignored'}), 200
            
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}", exc_info=True)
        return jsonify({'status': 'error'}), 400


def run_webhook_server(port=5001):
    """Запустить Flask сервер для webhook"""
    logger.info(f"🚀 Запуск webhook сервера на порту {port}")
    webhook_app.run(host='0.0.0.0', port=port, debug=False)
```

### 2.6. Запустите webhook сервер

В функции `main()`, **ПЕРЕД** `longpoll.listen()`, добавьте:

```python
def main():
    # ... существующий код ...
    
    # Запускаем webhook сервер в фоне
    webhook_thread = threading.Thread(
        target=run_webhook_server,
        args=(5001,),
        daemon=True
    )
    webhook_thread.start()
    logger.info("✅ Webhook сервер запущен")
    
    # Начинаем слушать события
    longpoll.listen()
```

---

## 🌐 Шаг 3: Настройка webhook в YooKassa

### 3.1. Откройте настройки YooKassa

1. Войдите в личный кабинет: https://yookassa.ru/my
2. Выберите ваш магазин
3. Перейдите в "Настройки" → "Уведомления"

### 3.2. Настройте HTTP-уведомления

- **URL для уведомлений:** `https://your-domain.com/webhook/yookassa`
- **События:** Выберите `payment.succeeded`
- **Формат:** JSON
- **HTTP метод:** POST

**⚠️ ВАЖНО:** Webhook должен быть доступен по HTTPS!

Если у вас нет домена, используйте ngrok для тестирования:

```bash
# Установите ngrok (если нет)
npm install -g ngrok

# Запустите туннель на порт 5001
ngrok http 5001

# Используйте URL вида: https://xxxx.ngrok.io/webhook/yookassa
```

### 3.3. Проверьте webhook

YooKassa сразу отправит тестовое уведомление. Проверьте логи бота:

```bash
tail -f vk_bot.log | grep webhook
```

Должно быть:
```
✅ Webhook сервер запущен
📩 Webhook от YooKassa: {...}
```

---

## 🧪 Шаг 4: Тестирование

### 4.1. Тест кнопки "💰 Баланс"

1. Откройте бота в VK
2. Нажмите "💰 Баланс"
3. Должны увидеть:
   - Текущий баланс
   - 5 кнопок с тарифами
   - Кнопку "Пригласить друга"
   - Кнопку "История платежей"

### 4.2. Тест создания платежа

1. Нажмите любую кнопку с тарифом (например, "💳 250₽")
2. Должно прийти сообщение с кнопкой "Перейти к оплате"
3. Нажмите кнопку — откроется страница YooKassa

### 4.3. Тест оплаты (тестовый режим)

1. На странице YooKassa выберите "Тестовая карта"
2. Введите данные:
   - Номер: `5555 5555 5555 4444`
   - Срок: любой будущий
   - CVC: любой
   - Имя: любое
3. Нажмите "Оплатить"

### 4.4. Проверка начисления

1. В логах должно быть:
   ```
   📩 Webhook от YooKassa: {...}
   ✅ Платеж XXX обработан: user 12345 получил 10 токенов за 250₽
   ```

2. Пользователю должно прийти уведомление:
   ```
   🎉 Спасибо! Оплата поступила!
   💰 Начислено: 10 токенов
   ```

3. Проверьте баланс в БД:
   ```sql
   SELECT balance FROM users WHERE user_id = 12345;
   ```

### 4.5. Тест истории платежей

1. Нажмите "📜 История платежей"
2. Должен показаться список всех платежей с датами и статусами

---

## 🔧 Шаг 5: Дополнительные настройки

### 5.1. Настройте Nginx (если используете)

Добавьте в конфигурацию:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    # ... SSL сертификаты ...
    
    location /webhook/yookassa {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Перезапустите Nginx:

```bash
sudo systemctl reload nginx
```

### 5.2. Настройте firewall

Откройте порт 5001 (если webhook внутри сети):

```bash
sudo ufw allow 5001/tcp
```

---

## 📊 Критерии успеха

### ✅ Все работает правильно, если:

1. При нажатии "💰 Баланс" показываются тарифы
2. При нажатии на тариф создается платеж
3. Webhook успешно принимает уведомления от YooKassa
4. Токены начисляются автоматически после оплаты
5. Пользователь получает уведомление сразу после оплаты
6. История платежей отображается корректно

---

## 🐛 Troubleshooting

### Проблема: "Ошибка создания платежа"

**Решение:**
1. Проверьте config.py (YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
2. Проверьте логи: `tail -f vk_bot.log | grep YooKassa`
3. Убедитесь, что секретный ключ валиден (не истек)

### Проблема: Webhook не работает

**Решение:**
1. Проверьте, запущен ли Flask: `netstat -tuln | grep 5001`
2. Проверьте URL в YooKassa (должен быть HTTPS)
3. Проверьте логи webhook: `tail -f vk_bot.log | grep webhook`
4. Отправьте тестовый webhook из личного кабинета YooKassa

### Проблема: Токены не начисляются

**Решение:**
1. Проверьте логи webhook
2. Проверьте таблицу payments:
   ```sql
   SELECT * FROM payments ORDER BY created_at DESC LIMIT 5;
   ```
3. Проверьте metadata в платеже (должны быть user_id и tokens)

### Проблема: Дублирующиеся начисления

**Решение:** Код защищен от дублей через проверку `payment_id`. Если всё равно происходит:

```sql
-- Найдите дубли
SELECT payment_id, COUNT(*) 
FROM payments 
WHERE status = 'succeeded' 
GROUP BY payment_id 
HAVING COUNT(*) > 1;

-- Удалите дубли (оставив первый)
DELETE FROM payments 
WHERE id NOT IN (
    SELECT MIN(id) 
    FROM payments 
    GROUP BY payment_id
);
```

---

## 📈 Мониторинг

### Проверка статуса платежей

```sql
-- Статистика по статусам
SELECT status, COUNT(*), SUM(amount) 
FROM payments 
GROUP BY status;

-- Последние 10 платежей
SELECT 
    p.created_at,
    u.user_id,
    u.first_name,
    p.amount,
    p.status
FROM payments p
JOIN users u ON p.user_id = u.user_id
ORDER BY p.created_at DESC
LIMIT 10;

-- Незавершенные платежи (старше 1 часа)
SELECT * FROM payments 
WHERE status = 'pending' 
AND created_at < NOW() - INTERVAL '1 hour';
```

### Проверка webhook

```bash
# Логи webhook за последний час
grep "webhook" vk_bot.log | tail -20

# Ошибки webhook
grep "webhook.*ERROR" vk_bot.log
```

---

## ✅ Готово!

БЛОК 7 полностью интегрирован. Теперь VK-бот имеет:
- ✅ Автоматическую платежную систему через YooKassa
- ✅ 5 тарифов (синхронизированы с ТГ-ботом)
- ✅ Мгновенное начисление токенов
- ✅ Историю платежей
- ✅ Уведомления пользователям

**Процент синхронизации:** 35% → 90% (после применения всех блоков)

---

## 📚 Связанные файлы

- [`vk_payments.py`](vk_payments.py) — модуль платежей
- [`main_vk_BLOCK7_PAYMENTS_INTEGRATION.py`](main_vk_BLOCK7_PAYMENTS_INTEGRATION.py) — интеграция
- [`FINAL_SUMMARY_BLOCKS_1-7.md`](FINAL_SUMMARY_BLOCKS_1-7.md) — итоговая сводка

---

⏱️ **Время на применение:** 30-40 минут  
🔧 **Сложность:** Средняя (требуется настройка webhook)  
🎯 **Приоритет:** 🔥🔥🔥 КРИТИЧНО (монетизация!)
