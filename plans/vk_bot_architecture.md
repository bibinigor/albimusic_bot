# Архитектура VK-версии ALBImusic бота

## 1. Основные компоненты

### 1.1 Структура проекта
```
albimusic-bot/
├── main_vk.py           # Основной файл VK бота
├── vk_keyboards.py      # Модуль клавиатур VK
├── vk_states.py         # Менеджер состояний для VK
├── vk_handlers/         # Обработчики событий VK
│   ├── music.py         # Обработка музыкальных команд
│   ├── payments.py      # Обработка платежей
│   └── support.py       # Система поддержки
├── celery_tasks.py      # Существующие задачи Celery (переиспользуется)
└── db_utils.py         # Существующие функции БД (переиспользуется)
```

### 1.2 Ключевые зависимости
```python
vk_api==2.0.2  # Библиотека для работы с VK API
vk-botting     # Фреймворк для создания ботов VK
celery         # Для асинхронных задач (переиспользуется)
aiohttp        # Для асинхронных HTTP запросов
```

## 2. Основные различия с Telegram версией

### 2.1 Система состояний
- Вместо FSMContext из aiogram реализуем собственный менеджер состояний
- Хранение состояний в Redis с форматом: `vk:{user_id}:state`
- Сохранение данных состояния в формате JSON

```python
class VKStateManager:
    def __init__(self, redis_connection):
        self.redis = redis_connection
        
    async def set_state(self, user_id: int, state: str, data: dict = None):
        key = f"vk:{user_id}:state"
        await self.redis.hset(key, "state", state)
        if data:
            await self.redis.hset(key, "data", json.dumps(data))
```

### 2.2 Система клавиатур
- Адаптация под VK keyboard API
- Поддержка как inline, так и стандартных клавиатур

```python
def get_music_keyboard():
    keyboard = VKKeyboard(inline=True)
    keyboard.add_button("🎵 Сгенерировать музыку", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🎼 Создать песню", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("💰 Баланс", color=VkKeyboardColor.SECONDARY)
    return keyboard
```

### 2.3 Обработка аудио
- Использование VK Upload API вместо Telegram file_id
- Загрузка аудио через vk_api.upload.audio()
- Сохранение owner_id и audio_id вместо file_id

```python
async def upload_audio_to_vk(audio_path: str, title: str = None):
    upload = vk_api.VkUpload(vk_session)
    audio = upload.audio(
        audio_path,
        artist="ALBImusic",
        title=title
    )
    return f"{audio['owner_id']}_{audio['id']}"
```

## 3. Интеграция с существующими компонентами

### 3.1 Celery задачи
- Переиспользование существующих задач без изменений
- Адаптация только обработки результатов под VK API

### 3.2 База данных
- Использование существующей структуры БД
- Добавление поля vk_id в таблицу users
```sql
ALTER TABLE users ADD COLUMN vk_id BIGINT UNIQUE;
```

### 3.3 Система платежей
- Интеграция с VK Pay API
- Сохранение существующей логики работы с балансом

## 4. Безопасность

### 4.1 Валидация событий
- Проверка подписи запросов от VK
- Валидация прав доступа для групповых токенов

### 4.2 Ограничения доступа
- Проверка подписки на группу
- Ограничение частоты запросов
- Защита от спама

## 5. Масштабирование

### 5.1 Очереди сообщений
- Использование RabbitMQ для обработки сообщений
- Отдельные очереди для разных типов задач

### 5.2 Кэширование
- Кэширование состояний пользователей
- Кэширование результатов генерации
- Кэширование клавиатур

## 6. Мониторинг

### 6.1 Логирование
- Сохранение структуры логирования из Telegram версии
- Добавление специфичных для VK метрик

### 6.2 Метрики
- Количество активных пользователей
- Успешность генераций
- Статистика платежей
- Время отклика бота

## 7. Развертывание

### 7.1 Требования к окружению
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- RabbitMQ 3.8+

### 7.2 Конфигурация
- Переменные окружения для токенов и ключей
- Конфигурационные файлы для разных окружений