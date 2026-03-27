# 🔴 БЛОК 2: ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ
## Демо-система разблокировки

---

## Что реализовано:

### ✅ Новая функциональность:
- **Таблица `demo_tracks`** — хранение демо и полных версий треков
- **Функция `create_demo_track()`** — создание записи при генерации
- **Callback `unlock_{task_id}`** — разблокировка за 1 токен
- **Проверка `is_unlocked`** — перед публикацией требуется разблокировка
- **Модуль `vk_demo_system.py`** — все функции для работы с демо

### ✅ Решенные проблемы из GAP-анализа:
- **Отсутствующая функция #1:** Демо-система полностью реализована
- **Ошибка #2:** Проверка is_unlocked перед публикацией добавлена

---

## 📋 ПОРЯДОК ПРИМЕНЕНИЯ

### ШАГ 1: Применить миграцию БД

```bash
# Подключиться к PostgreSQL
psql -U postgres -d albimusic

# Выполнить миграцию
\i migrations/002_add_demo_tracks_table.sql

# Проверить, что таблица создана
\d demo_tracks
```

**Ожидаемый результат:**
```
                                          Table "public.demo_tracks"
   Column    |            Type             | Nullable |                  Default
-------------+-----------------------------+----------+-------------------------------------------
 id          | integer                     | not null | nextval('demo_tracks_id_seq'::regclass)
 task_id     | character varying(255)      | not null |
 user_id     | bigint                      | not null |
 demo_url_1  | text                        |          |
 demo_url_2  | text                        |          |
 full_url_1  | text                        |          |
 full_url_2  | text                        |          |
 is_unlocked | boolean                     |          | false
 unlocked_at | timestamp without time zone |          |
 created_at  | timestamp without time zone |          | CURRENT_TIMESTAMP
 updated_at  | timestamp without time zone |          | CURRENT_TIMESTAMP
```

---

### ШАГ 2: Убедиться, что vk_demo_system.py на месте

```bash
cd /root/albimusic-bot
ls -lh vk_demo_system.py
```

**Ожидаемый результат:**
```
-rw-r--r-- 1 root root 7.2K Mar 27 15:42 vk_demo_system.py
```

Если файла нет — он уже создан в проекте, просто перезапустите бота.

---

### ШАГ 3: Применить изменения к main_vk.py

#### 3.1. Добавить импорты (в начало файла, после других импортов)

**Найти блок импортов (строки 1-20):**
```python
from vk_keyboards import get_main_keyboard
```

**Добавить после него:**
```python
from vk_demo_system import (
    create_demo_track,
    unlock_demo_track,
    get_demo_track_info,
    is_track_unlocked
)
```

---

#### 3.2. Интегрировать создание demo_track после генерации

**Использовать код из файла:** `main_vk_BLOCK2_INTEGRATION.py` → ЧАСТЬ 2

**Место вставки:** В функции `generate_song_thread()`, сразу после обновления статуса в БД:
```python
execute_query_sync(
    '''UPDATE generations 
       SET audio_url = %s, suno_audio_id = %s, status = %s 
       WHERE task_id = %s''',
    (audio_url, audio_id, 'completed', _task_id)
)

# ← ВСТАВИТЬ КОД СОЗДАНИЯ demo_track СЮДА
```

---

#### 3.3. Добавить callback handler для unlock

**Использовать код из файла:** `main_vk_BLOCK2_INTEGRATION.py` → ЧАСТЬ 3

**Место вставки:** В методе `handle_callback()`, в блоке обработки actions:
```python
elif action == "cover":
    # ... существующий код ...

# ← ВСТАВИТЬ КОД ОБРАБОТКИ unlock СЮДА

elif action == "share":
    # ... существующий код ...
```

---

#### 3.4. Обновить клавиатуру с кнопкой разблокировки

В файле **`vk_keyboards.py`**, функция `get_song_options_keyboard()`:

**Было:**
```python
def get_song_options_keyboard(task_id):
    import json
    keyboard = VkKeyboard(inline=True)

    keyboard.add_callback_button(
        '🎤 Минусовка (1 токен)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "karaoke", "task_id": str(task_id)})
    )
    # ...
```

**Стало:**
```python
def get_song_options_keyboard(task_id):
    import json
    keyboard = VkKeyboard(inline=True)

    # ✅ БЛОК 2: Добавляем кнопку разблокировки
    keyboard.add_callback_button(
        '🔓 Разблокировать (1 токен)',
        color=VkKeyboardColor.POSITIVE,
        payload=json.dumps({"action": "unlock", "task_id": str(task_id)})
    )
    keyboard.add_line()
    
    keyboard.add_callback_button(
        '🎤 Минусовка (1 токен)',
        color=VkKeyboardColor.PRIMARY,
        payload=json.dumps({"action": "karaoke", "task_id": str(task_id)})
    )
    # ... остальные кнопки
```

---

#### 3.5. Добавить проверку is_unlocked перед публикацией

**Использовать код из файла:** `main_vk_BLOCK2_INTEGRATION.py` → ЧАСТЬ 5

**Место:** В callback handler для `action == "share"`, в начале функции.

**Заменить:**
```python
elif action == "share":
    logger.info(f"🔗 Запрос на публикацию...")
    try:
        # Получаем данные о треке
        song_info = execute_query_sync(...)
```

**На:**
```python
elif action == "share":
    task_id_to_share = payload.get('task_id', '')
    logger.info(f"🔗 Запрос на публикацию...")
    
    try:
        # ✅ БЛОК 2: Проверяем, разблокирован ли трек
        if not is_track_unlocked(task_id_to_share, user_id):
            self.send_message(
                user_id=user_id,
                message="❌ Сначала разблокируйте полную версию трека (1 токен).",
                keyboard=self.get_main_keyboard(user_id)
            )
            return
        
        # Получаем данные о треке...
```

---

### ШАГ 4: Перезапустить VK-бота

```bash
# Остановить текущий процесс
pkill -f main_vk.py

# Запустить заново
cd /root/albimusic-bot
nohup python3 main_vk.py > vk_bot.log 2>&1 &

# Проверить логи
tail -f vk_bot.log
```

**Ожидаемое в логах:**
```
✅ Подключение к VK API успешно установлено
✅ Database pool initialized
✅ Подключение к Redis успешно установлено
🎯 Бот ВК успешно запущен и слушает сообщения!
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Тест 1: Создание demo_track при генерации

**Входные данные:**
1. Пользователь создает песню
2. Генерация завершается успешно

**Ожидаемый результат:**
- ✅ В БД создается запись в таблице `demo_tracks` с `is_unlocked = FALSE`
- ✅ В сообщении пользователю добавлена кнопка "🔓 Разблокировать (1 токен)"

**Проверка в БД:**
```sql
SELECT task_id, user_id, is_unlocked, demo_url_1, full_url_1 
FROM demo_tracks 
ORDER BY created_at DESC 
LIMIT 5;
```

**Ожидаемый результат:**
```
              task_id              | user_id | is_unlocked |    demo_url_1    |    full_url_1
-----------------------------------+---------+-------------+------------------+------------------
 a1b2c3d4-e5f6-7890-abcd-ef1234567890 | 123456  | f           | https://suno... | https://suno...
```

---

### Тест 2: Разблокировка трека (успешная)

**Входные данные:**
1. Пользователь с balance >= 1
2. Нажимает кнопку "🔓 Разблокировать"

**Ожидаемый результат:**
- ✅ Токен списывается (balance -= 1)
- ✅ В БД: `is_unlocked = TRUE`, `unlocked_at = NOW()`
- ✅ Пользователь получает сообщение с полными версиями:
  ```
  ✅ Трек успешно разблокирован! Полные версии доступны ниже.
  
  🎵 Полная версия 1:
  https://cdn1.suno.ai/...
  
  🎵 Полная версия 2:
  https://cdn1.suno.ai/...
  ```

**Проверка в БД:**
```sql
SELECT task_id, is_unlocked, unlocked_at 
FROM demo_tracks 
WHERE task_id = '<ID из теста>';
```

**Ожидаемый результат:**
```
              task_id              | is_unlocked |      unlocked_at
-----------------------------------+-------------+------------------------
 a1b2c3d4-e5f6-7890-abcd-ef1234567890 | t           | 2026-03-27 15:43:25
```

---

### Тест 3: Повторная разблокировка (должна быть отклонена)

**Входные данные:**
1. Трек уже разблокирован
2. Пользователь снова нажимает "🔓 Разблокировать"

**Ожидаемый результат:**
- ✅ Токен НЕ списывается
- ✅ Сообщение: "⚠️ Этот трек уже разблокирован!"

---

### Тест 4: Разблокировка с недостаточным балансом

**Входные данные:**
1. Пользователь с balance = 0
2. Пытается разблокировать трек

**Ожидаемый результат:**
- ✅ Сообщение: "❌ Недостаточно токенов. Для разблокировки нужен 1 токен."
- ✅ is_unlocked остается FALSE

---

### Тест 5: Публикация неразблокированного трека

**Входные данные:**
1. Трек создан, но НЕ разблокирован (is_unlocked = FALSE)
2. Пользователь нажимает "🔗 Поделиться"

**Ожидаемый результат:**
- ✅ Сообщение: "❌ Сначала разблокируйте полную версию трека (1 токен), чтобы опубликовать её."
- ✅ Публикация НЕ происходит

---

### Тест 6: Публикация разблокированного трека

**Входные данные:**
1. Трек разблокирован (is_unlocked = TRUE)
2. Пользователь нажимает "🔗 Поделиться"

**Ожидаемый результат:**
- ✅ Пользователь получает ссылку для публикации с полной версией трека

---

## 📊 МОНИТОРИНГ

### Статистика разблокировок

```sql
-- Количество разблокированных треков
SELECT COUNT(*) as unlocked_count
FROM demo_tracks
WHERE is_unlocked = TRUE;

-- Конверсия (% разблокировок от всех созданных)
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN is_unlocked THEN 1 ELSE 0 END) as unlocked,
    ROUND(100.0 * SUM(CASE WHEN is_unlocked THEN 1 ELSE 0 END) / COUNT(*), 2) as conversion_rate
FROM demo_tracks;
```

**Ожидаемый результат:**
```
 total | unlocked | conversion_rate
-------+----------+-----------------
   150 |       45 |           30.00
```

### Топ-5 пользователей по разблок овкам

```sql
SELECT user_id, COUNT(*) as unlocked_count
FROM demo_tracks
WHERE is_unlocked = TRUE
GROUP BY user_id
ORDER BY unlocked_count DESC
LIMIT 5;
```

---

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ

### 🚨 TODO: Демо-версии (45 сек)

В текущей реализации `demo_url_1` и `demo_url_2` = `full_url_1` и `full_url_2` (одинаковые).

**Для production нужно:**
1. Использовать `preview_url` из Suno API (если доступно)
2. Или обрезать аудио до 45 сек с помощью ffmpeg:

```python
import subprocess

def create_demo_from_full(full_url, output_path):
    """Обрезать аудио до 45 секунд"""
    subprocess.run([
        'ffmpeg', '-i', full_url,
        '-t', '45',  # Первые 45 секунд
        '-acodec', 'copy',
        output_path
    ])
    return output_path
```

### 💡 Рекомендация:
На первом этапе можно использовать полные версии как демо, затем добавить обрезку.

---

## ✅ КРИТЕРИИ УСПЕХА

БЛОК 2 считается успешно примененным, если:

1. ✅ Таблица `demo_tracks` создана в БД
2. ✅ При генерации трека создается запись в `demo_tracks`
3. ✅ Кнопка "🔓 Разблокировать" отображается после генерации
4. ✅ Разблокировка списывает 1 токен и обновляет `is_unlocked = TRUE`
5. ✅ Повторная разблокировка отклоняется
6. ✅ Публикация требует разблокировки
7. ✅ Все тесты 1-6 прошли успешно
8. ✅ Логи показывают:
   - "✅ Создан demo_track для task_id={uuid}"
   - "💰 Списан 1 токен за разблокировку от user_id={id}"
   - "🔓 Разблокирован трек task_id={uuid}"

---

## 📝 КОМИТ В GIT

После успешного тестирования:

```bash
cd /root/albimusic-bot

git add main_vk.py
git add vk_keyboards.py
git add vk_demo_system.py
git add migrations/002_add_demo_tracks_table.sql
git add main_vk_BLOCK2_INTEGRATION.py
git add BLOCK2_APPLY_INSTRUCTIONS.md

git commit -m "[BLOCK2] Демо-система разблокировки: unlock за 1 токен, проверка перед публикацией

✅ Реализовано:
- Таблица demo_tracks (демо и полные версии)
- Модуль vk_demo_system.py с функциями разблокировки
- Callback unlock_{task_id} для разблокировки за 1 токен
- Проверка is_unlocked перед публикацией
- Кнопка '🔓 Разблокировать' в клавиатуре треков

🔧 Изменено:
- main_vk.py: интеграция демо-системы
- vk_keyboards.py: добавлена кнопка разблокировки
- Добавлена миграция: 002_add_demo_tracks_table.sql

🧪 Протестировано:
- Создание demo_track при генерации ✅
- Разблокировка за 1 токен ✅
- Отклонение повторной разблокировки ✅
- Блокировка публикации без unlock ✅"

git push origin main
```

---

## 🎯 СЛЕДУЮЩИЙ ШАГ

После успешного применения БЛОКА 2 переходим к **БЛОКУ 3: Выбор версии v1/v2** для минусовки голоса/кавера/WAV.

---

**Применил:** [Ваше имя]  
**Дата:** [Дата применения]  
**Результат:** ✅ Успешно / ❌ Откачено
