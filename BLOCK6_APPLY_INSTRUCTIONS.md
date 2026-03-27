# 📋 ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ БЛОКА 6: ЗАГРУЗКА ФАЙЛОВ

## 🎯 ЧТО РЕШАЕТ ЭТОТ БЛОК

**Из GAP-анализа (проблема #8):** Отсутствует возможность загрузки своих аудиофайлов для кавера/минусовки

**Реализовано:**
- ✅ Загрузка аудиофайлов из VK
- ✅ Валидация файлов (длительность ≤ 5 мин, размер ≤ 20 МБ)
- ✅ Создание минусовки из загруженного файла
- ✅ Создание кавера из загруженного файла + выбор жанра
- ✅ Проверка через ffprobe (опционально)

---

## 📁 СОЗДАННЫЕ ФАЙЛЫ

1. **`vk_file_upload.py`** — Модуль загрузки и валидации файлов (280 строк)
   - download_vk_audio() — скачивание из VK
   - check_audio_duration() — проверка длительности через ffprobe
   - check_audio_size() — проверка размера файла
   - process_uploaded_audio() — полная обработка
   - cleanup_temp_file() — очистка временных файлов

2. **`main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py`** — Код интеграции (500 строк)
   - Handler'ы для минусовки из файла
   - Handler'ы для кавера из файла
   - Выбор жанра для кавера

3. **`BLOCK6_APPLY_INSTRUCTIONS.md`** — Эта инструкция

---

## 🔧 ПОШАГОВАЯ ИНТЕГРАЦИЯ

### ШАГ 1: Обновление vk_states.py

**Добавить новые состояния в класс States:**

```python
class States(Enum):
    """Все возможные состояния бота"""
    START = auto()
    
    # ... существующие состояния ...
    
    # Состояния загрузки файлов (БЛОК 6)
    WAITING_AUDIO_UPLOAD = auto()  # Ожидание загрузки audio
    WAITING_COVER_GENRE = auto()  # Выбор жанра для кавера
    WAITING_CUSTOM_COVER_GENRE = auto()  # Ввод своего жанра
```

**Место вставки:** После существующих состояний, перед концом класса.

---

### ШАГ 2: Добавление импортов в main_vk.py

**Добавить в начало файла (после существующих импортов):**

```python
# БЛОК 6: Загрузка файлов
from vk_file_upload import process_uploaded_audio, cleanup_temp_file
```

**Место вставки:** После импорта `from vk_states import States, VKStateManager`

---

### ШАГ 3: Добавление методов в класс VKBot

**Найти класс `VKBot` в main_vk.py.**

**Добавить методы из `main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py`:**

```python
class VKBot:
    # ... существующие методы ...
    
    # ═══════════════════════════════════════════════════
    # БЛОК 6: ЗАГРУЗКА ФАЙЛОВ
    # ═══════════════════════════════════════════════════
    
    def handle_karaoke_upload_request(self, user_id):
        """Начать процесс загрузки файла для минусовки"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
    
    def handle_karaoke_audio_upload(self, user_id, attachment):
        """Обработать загруженный audio файл для минусовки"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
    
    def handle_cover_upload_request(self, user_id):
        """Начать процесс загрузки файла для кавера"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
    
    def handle_cover_audio_upload(self, user_id, attachment):
        """Обработать загруженный audio файл для кавера"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
    
    def show_cover_genre_selection(self, user_id):
        """Показать выбор жанра для кавера"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
    
    def handle_cover_genre_selection(self, user_id, genre_code):
        """Обработать выбор жанра для кавера"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
    
    def handle_custom_cover_genre(self, user_id, custom_genre):
        """Обработать ввод своего жанра для кавера"""
        # ... код из main_vk_BLOCK6_FILE_UPLOAD_INTEGRATION.py ...
```

**⚠️ ВАЖНО:** Скопировать ВСЕ методы целиком из файла интеграции.

---

### ШАГ 4: Интеграция в handle_message()

**Найти метод `handle_message(self, event)` в классе VKBot.**

**Добавить обработку ПЕРЕД обработкой текстовых команд:**

```python
def handle_message(self, event):
    # ... существующий код получения user_id, text, payload, msg ...
    
    # ════════════════════════════════════════════════════
    # БЛОК 6: ОБРАБОТКА ЗАГРУЗКИ ФАЙЛОВ
    # ════════════════════════════════════════════════════
    
    current_state = asyncio.get_event_loop().run_until_complete(
        self.state_manager.get_state(user_id)
    )
    
    # Обработка загрузки аудиофайла
    if current_state == States.WAITING_AUDIO_UPLOAD:
        # Проверяем отмену
        if text and text.lower() in ['отмена', 'cancel']:
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.finish(user_id)
            )
            self.send_message(user_id, "❌ Загрузка отменена")
            return
        
        # Проверяем наличие аудио-вложения
        if 'attachments' in msg and msg['attachments']:
            for attachment in msg['attachments']:
                if attachment['type'] in ['audio', 'doc']:
                    doc_info = attachment.get('audio') or attachment.get('doc')
                    
                    # Получаем тип загрузки из состояния
                    data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    )
                    
                    if data and data.get('upload_type') == 'karaoke':
                        self.handle_karaoke_audio_upload(user_id, doc_info)
                    elif data and data.get('upload_type') == 'cover':
                        self.handle_cover_audio_upload(user_id, doc_info)
                    return
        
        self.send_message(
            user_id,
            "❌ Не обнаружен аудиофайл\n\n"
            "Отправьте аудиофайл или напишите 'отмена'"
        )
        return
    
    # Обработка ввода своего жанра для кавера
    if current_state == States.WAITING_CUSTOM_COVER_GENRE:
        if text and text.lower() in ['отмена', 'cancel']:
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.finish(user_id)
            )
            self.send_message(user_id, "❌ Отменено")
            return
        
        self.handle_custom_cover_genre(user_id, text)
        return
    
    # Обработка выбора жанра кавера через callback
    if payload:
        cmd = payload.get('cmd')
        
        if cmd and cmd.startswith('cover_upload_genre_'):
            genre_code = cmd.replace('cover_upload_genre_', '')
            self.handle_cover_genre_selection(user_id, genre_code)
            return
    
    # ... остальной существующий код обработки ...
```

**Место вставки:** В начале метода `handle_message()`, после получения основных переменных.

---

### ШАГ 5: Добавление кнопок в UI

**В месте, где создаются кнопки кавера/минусовки, добавить вариант загрузки:**

Например, при обработке callback'а `karaoke` или `cover`:

```python
# Было:
# Только кнопка "📂 Из моих треков"

# Стало:
keyboard = VkKeyboard(inline=True)
keyboard.add_callback_button(
    "📂 Из моих треков",
    color=VkKeyboardColor.PRIMARY,
    payload={"cmd": "karaoke_from_my"}
)
keyboard.add_callback_button(
    "📤 Загрузить файл",
    color=VkKeyboardColor.POSITIVE,
    payload={"cmd": "karaoke_upload"}
)

# Обработчик для karaoke_upload:
if cmd == 'karaoke_upload':
    self.handle_karaoke_upload_request(user_id)
    return

# Аналогично для кавера:
if cmd == 'cover_upload':
    self.handle_cover_upload_request(user_id)
    return
```

---

### ШАГ 6: Установка зависимостей

**Убедиться, что установлен `requests` (для скачивания файлов):**

```bash
pip3 install requests
```

**Опционально: установка ffprobe (для проверки длительности):**

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

**⚠️ ВАЖНО:** ffprobe не обязателен — код работает без него (просто пропускает проверку длительности).

---

### ШАГ 7: Настройка upload_audio_to_server()

**В файле `vk_file_upload.py` функция `upload_audio_to_server()` — это заглушка!**

**Нужно реализовать реальную загрузку на ваш сервер:**

```python
def upload_audio_to_server(file_path: str, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Загрузить аудиофайл на сервер
    """
    try:
        # ВАРИАНТ 1: Загрузка на свой HTTP-сервер
        import requests
        files = {'file': open(file_path, 'rb')}
        response = requests.post('https://your-server.com/upload', files=files)
        return True, response.json()['url'], None
        
        # ВАРИАНТ 2: Загрузка в S3
        # import boto3
        # s3 = boto3.client('s3')
        # s3.upload_file(file_path, 'bucket-name', filename)
        # url = f"https://bucket-name.s3.amazonaws.com/{filename}"
        # return True, url, None
        
        # ВАРИАНТ 3: Загрузка по FTP
        # from ftplib import FTP
        # ftp = FTP('ftp.server.com')
        # ftp.login('user', 'password')
        # with open(file_path, 'rb') as f:
        #     ftp.storbinary(f'STOR {filename}', f)
        # return True, f"https://server.com/files/{filename}", None
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки на сервер: {e}")
        return False, None, str(e)
```

**Или использовать существующий upload_file_to_server из Telegram-бота (если есть).**

---

### ШАГ 8: Перезапуск бота

```bash
# Остановка бота
pkill -f main_vk.py

# Проверка синтаксиса
python3 -m py_compile main_vk.py
python3 -m py_compile vk_file_upload.py
python3 -m py_compile vk_states.py

# Запуск бота
nohup python3 main_vk.py > vk_bot.log 2>&1 &

# Проверка логов
tail -f vk_bot.log
```

---

## ✅ КРИТЕРИИ УСПЕШНОГО ПРИМЕНЕНИЯ

### Тест 1: Минусовка из файла
1. Нажать кнопку **"🎤 Минусовка"**
2. Выбрать **"📤 Загрузить файл"**
3. ✅ Показывается сообщение с требованиями
4. Отправить MP3 файл (до 5 мин, до 20 МБ)
5. ✅ Файл обрабатывается
6. ✅ Токен списывается
7. ✅ Минусовка создается через Celery

### Тест 2: Кавер из файла
1. Нажать кнопку **"🎸 Кавер"**
2. Выбрать **"📤 Загрузить файл"**
3. ✅ Показывается сообщение с требованиями
4. Отправить MP3 файл (до 5 мин, до 20 МБ)
5. ✅ Файл обрабатывается
6. ✅ Показывается выбор жанра (16 кнопок + "Свой вариант")
7. Выбрать жанр или написать свой
8. ✅ Токены списываются (2 шт)
9. ✅ Кавер создается через Celery

### Тест 3: Валидация файлов
1. Попробовать загрузить файл > 5 минут
2. ✅ Показывается ошибка "Файл слишком длинный"
3. Попробовать загрузить файл > 20 МБ
4. ✅ Показывается ошибка "Файл слишком большой"

### Тест 4: Отмена загрузки
1. Начать загрузку файла
2. Написать "отмена"
3. ✅ Процесс отменяется
4. ✅ Состояние сбрасывается

---

## 🐛 ВОЗМОЖНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема 1: "Ошибка скачивания файла"

**Причина:** VK не возвращает URL файла или файл недоступен

**Решение:**
- Проверить права доступа к документам в настройках сообщества
- Убедиться, что пользователь отправил именно аудиофайл
- Проверить логи: `tail -f vk_bot.log | grep "Ошибка скачивания"`

---

### Проблема 2: "ffprobe не найден"

**Причина:** ffmpeg не установлен в системе

**Решение:**
```bash
# Установка ffmpeg (включает ffprobe)
sudo apt-get install ffmpeg -y
```

**Или:** Код работает без ffprobe — проверка длительности просто пропускается.

---

### Проблема 3: "Ошибка загрузки на сервер"

**Причина:** Функция `upload_audio_to_server()` — заглушка

**Решение:** Реализовать реальную загрузку (см. ШАГ 7).

**Временное решение:** Использовать прямой URL из VK (без загрузки на свой сервер):
```python
def upload_audio_to_server(file_path: str, filename: str):
    # Возвращаем локальный путь как URL (только для тестирования!)
    return True, f"file://{file_path}", None
```

---

### Проблема 4: "Не обнаружен аудиофайл"

**Причина:** VK не отправляет attachment нужного типа

**Решение:**
- Убедиться, что пользователь отправляет именно аудиофайл (не голосовое сообщение)
- Проверить структуру attachment в логах
- Добавить поддержку других типов:
  ```python
  if attachment['type'] in ['audio', 'doc', 'audio_message']:
      # ...
  ```

---

### Проблема 5: Временные файлы не удаляются

**Причина:** Ошибка при удалении или код не доходит до cleanup

**Решение:**
```bash
# Периодическая очистка временных файлов
find /tmp -name "vk_audio_*.mp3" -mtime +1 -delete
```

---

## 📊 СТАТИСТИКА БЛОКА 6

| Метрика | Значение |
|---------|----------|
| Создано файлов | 3 |
| Строк кода | ~780 |
| Функций | 8 |
| Новых состояний | 3 |
| Callbacks | 17 (жанры кавера) |

---

## 🎯 АРХИТЕКТУРА ЗАГРУЗКИ ФАЙЛОВ

```
┌─────────────────────────────────────────────────────────┐
│           ЗАГРУЗКА ФАЙЛОВ ДЛЯ КАВЕРА/МИНУСОВКИ          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🎤 МИНУСОВКА                                           │
│  ├─ Запрос загрузки → WAITING_AUDIO_UPLOAD             │
│  ├─ Получение файла из VK (download_vk_audio)          │
│  ├─ Валидация (размер ≤ 20 МБ)                         │
│  ├─ Валидация (длительность ≤ 5 мин) [ffprobe]        │
│  ├─ Загрузка на сервер                                 │
│  ├─ Списание 1 токена                                  │
│  └─ Создание Celery задачи (generate_karaoke)         │
│                                                          │
│  🎸 КАВЕР                                               │
│  ├─ Запрос загрузки → WAITING_AUDIO_UPLOAD             │
│  ├─ Получение файла из VK (download_vk_audio)          │
│  ├─ Валидация (размер ≤ 20 МБ)                         │
│  ├─ Валидация (длительность ≤ 5 мин) [ffprobe]        │
│  ├─ Загрузка на сервер                                 │
│  ├─ Выбор жанра → WAITING_COVER_GENRE                  │
│  │   ├─ 16 стандартных жанров                          │
│  │   └─ Свой вариант → WAITING_CUSTOM_COVER_GENRE     │
│  ├─ Списание 2 токенов                                 │
│  └─ Создание Celery задачи (generate_cover)           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ ВОЗМОЖНОСТИ

### Расширение функционала:

1. **Поддержка голосовых сообщений:**
   ```python
   if attachment['type'] == 'audio_message':
       # Обработка голосовых сообщений
   ```

2. **Пакетная загрузка:**
   ```python
   def handle_multiple_files(user_id, attachments):
       # Обработка нескольких файлов сразу
   ```

3. **Предпросмотр перед обработкой:**
   ```python
   def show_file_preview(user_id, file_info):
       # Показать информацию о файле перед обработкой
   ```

4. **История загрузок:**
   ```python
   def get_upload_history(user_id):
       # Показать список загруженных файлов
   ```

---

## ✨ ЗАВЕРШЕНИЕ

**БЛОК 6 полностью готов к применению!**

После применения:
- ✅ Загрузка своих файлов для минусовки
- ✅ Загрузка своих файлов для кавера
- ✅ Валидация файлов (размер, длительность)
- ✅ Выбор жанра для кавера (17 вариантов)

**Процент синхронизации:** 70% → **~85%** (после применения)

---

**⚠️ ВАЖНО:** Обязательно реализуйте `upload_audio_to_server()` для продакшена!

**Готово к применению или переходить к финальной сводке БЛОКОВ 1-6?**
