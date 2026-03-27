# ALBImusic VK Bot

## Описание
VK версия бота ALBImusic для генерации музыки с помощью искусственного интеллекта. Бот использует те же модели и системы генерации, что и Telegram версия, но адаптирован для работы в социальной сети ВКонтакте.

## Основные функции
- 🎵 Генерация музыки в различных стилях
- 🎼 Создание песен с текстом
- 🎸 Создание каверов на существующие треки
- 🎤 Создание караоке-версий
- 💰 Система токенов и оплаты через ЮKassa
- 🎁 Демо-система с примерами треков
- 🛟 Система поддержки пользователей

## Установка и настройка

### Предварительные требования
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- RabbitMQ 3.8+

### Переменные окружения
Создайте файл `.env` в корневой директории проекта:
```env
# VK API
VK_GROUP_TOKEN=your_vk_group_token
VK_GROUP_ID=your_group_id
ADMIN_ID=your_vk_admin_id

# ЮKassa
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# База данных
POSTGRES_URI=postgresql://user:password@host:port/dbname

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Suno API
SUNO_API_KEY=your_suno_api_key
```

### Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка базы данных
```bash
# Применение миграций
psql -U your_user -d your_database -f migrations/add_vk_id_column.sql
```

### Запуск компонентов

1. Запуск Celery worker:
```bash
celery -A celery_tasks worker --loglevel=info
```

2. Запуск бота:
```bash
python main_vk.py
```

## Основные различия с Telegram версией

### 1. Система состояний
- В Telegram: Использует FSMContext из aiogram
- В VK: Собственная реализация на Redis (vk_states.py)

### 2. Клавиатуры
- В Telegram: InlineKeyboardMarkup и ReplyKeyboardMarkup
- В VK: VkKeyboard с другой структурой и ограничениями

### 3. Обработка аудио
- В Telegram: Прямая отправка файла и получение file_id
- В VK: Двухэтапная загрузка через vk_api.upload

### 4. Платежи
- В обеих версиях используется ЮKassa
- Разные URL для возврата после оплаты
- В VK используется другой формат уведомлений

### 5. Демо-система
- В Telegram: Использует предварительно загруженные file_id
- В VK: Загружает демо-треки при старте бота

### 6. Структура проекта
```
albimusic-bot/
├── main_vk.py           # Основной файл VK бота
├── vk_config.py         # Конфигурация VK бота
├── vk_states.py         # Менеджер состояний
├── vk_keyboards.py      # Клавиатуры VK
├── vk_audio.py          # Работа с аудио
├── vk_demo_system.py    # Демо-система
├── vk_support.py        # Система поддержки
├── yookassa_vk.py       # Интеграция с ЮKassa
└── celery_tasks.py      # Общие задачи Celery
```

## Мониторинг и обслуживание

### Логирование
- Все логи сохраняются в формате:
```
%(asctime)s - %(levelname)s - %(message)s
```
- Основные логи: стандартный вывод
- Логи Celery: celery.log

### Мониторинг состояния
1. Проверка статуса бота:
```bash
systemctl status vk-albimusic-bot
```

2. Проверка Celery:
```bash
systemctl status celery-worker
```

### Резервное копирование
```bash
# Бэкап базы данных
./backup-database.sh

# Бэкап Redis
./backup-redis.sh
```

## Известные ограничения
1. VK API имеет лимиты на загрузку аудио:
   - До 200 аудиозаписей в сутки
   - Максимальный размер файла: 200 MB
   - Максимальная длительность: 60 минут

2. Ограничения клавиатур VK:
   - Максимум 40 кнопок
   - Максимум 10 кнопок в строке
   - Максимум 6 строк

## Устранение неполадок

### Частые проблемы и решения

1. Ошибка загрузки аудио:
```python
# Проверьте права доступа группы
vk.groups.getTokenPermissions()
```

2. Проблемы с Redis:
```bash
# Очистка состояний
redis-cli -n 1 KEYS "vk:*" | xargs redis-cli -n 1 DEL
```

3. Ошибки платежей:
```bash
# Проверка статуса платежа
curl -X GET https://api.yookassa.ru/v3/payments/{payment_id} \
     -u <shop_id>:<secret_key>
```

## Поддержка
При возникновении проблем:
1. Проверьте логи
2. Убедитесь в актуальности всех токенов
3. Проверьте подключение к Redis и PostgreSQL
4. Обратитесь к администратору системы