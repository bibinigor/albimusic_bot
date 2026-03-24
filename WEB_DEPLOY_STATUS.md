# 🚀 Статус деплоя веб-версии

**Дата:** 16 февраля 2026, 19:45 МСК
**Статус:** ✅ Веб-версия задеплоена, настраиваем VK авторизацию

---

## ✅ ЧТО СДЕЛАНО

### 1. Веб-приложение задеплоено
- ✅ **Frontend:** `/var/www/albimusic-web/index.html` (webapp версия с нижним меню)
- ✅ **Backend:** `/root/albimusic-bot/web_api.py` (FastAPI на порту 8001)
- ✅ **Сервис работает:** albimusic-web.service - active (running)
- ✅ **Доступно по адресу:** https://albi-music.ru/app

### 2. VK ID авторизация обновлена

**Frontend изменения (webapp/index.html):**
- ✅ Обновлён на VK ID SDK (новый метод)
- ✅ Используется `VKIDSDK` вместо старого `VKID`
- ✅ Добавлен `exchangeCode` метод
- ✅ `redirectUrl: 'https://albi-music.ru/app'`

**Backend изменения (web_api.py):**
- ✅ Обновлён endpoint `/api/auth/vk/token`
- ✅ Принимает `access_token`, `user_id`, `expires_in`
- ✅ Использует VK API для получения данных пользователя

**Настройки VK ID (54451761):**
- ✅ **Redirect URL изменён на:** `https://albi-music.ru/app`
- ✅ **Сохранено** в настройках VK ID

### 3. Credentials VK ID
```
App ID: 54451761
Client Secret: EXsS6C2HrdCS8I5Pddjn
Service Key: 3440b8c23440b8c23440b8c253377e66f3334403440b8c25dce517bbfb4188fd75db900
Redirect URL: https://albi-music.ru/app
```

### 4. Интерфейс веб-версии
**Нижнее меню (как в Telegram боте):**
- 🏠 Главная
- 📂 Треки
- 💰 Баланс
- 🎧 Примеры

**Кнопки авторизации:**
- 🔵 Войти с VK ID
- 🟡 Войти через Яндекс
- 👤 Войти как гость (тест)

---

## ⏳ ТЕКУЩАЯ ПРОБЛЕМА

**VPN блокирует авторизацию VK и Яндекс!**

VK и Яндекс блокируют запросы с VPN IP адресов для безопасности.
VK ID SDK не работает через VPN.

---

## 🎯 ЧТО НУЖНО СДЕЛАТЬ ДАЛЬШЕ

### Шаг 1: Тестирование авторизации БЕЗ VPN

1. **Отключить VPN**
2. **Открыть:** https://albi-music.ru/app
3. **Обновить страницу:** Cmd+Shift+R (жесткая перезагрузка)
4. **Нажать:** "Войти с VK ID"
5. **Проверить консоль браузера:** Cmd+Opt+J (Chrome/Safari)
6. **Ожидаемое поведение:**
   - Появится виджет VK ID (OneTap)
   - После авторизации вернётся на /app
   - Пользователь будет залогинен
   - Отобразится баланс вверху

### Шаг 2: Если VK авторизация работает

1. **Проверить Яндекс:** нажать "Войти через Яндекс"
2. **Проверить создание песни:**
   - Перейти на вкладку "🏠 Главная"
   - Нажать "🎵 Создать песню"
   - Выбрать "✨ ПРИДУМАТЬ ТЕКСТ"
   - Ввести описание
   - Выбрать жанр
   - Запустить генерацию
3. **Проверить мои треки:**
   - Перейти на вкладку "📂 Треки"
   - Убедиться что треки отображаются
   - Проверить кнопку "🔊 Слушать"
4. **Проверить баланс:**
   - Перейти на вкладку "💰 Баланс"
   - Проверить что баланс отображается

### Шаг 3: Если VK авторизация НЕ работает

**Проверить консоль браузера:**
- Открыть DevTools: Cmd+Opt+J
- Перейти на вкладку "Console"
- Найти ошибки (красный текст)
- Сделать скриншот консоли
- Проверить вкладку "Network" - какие запросы падают

**Возможные ошибки:**
- `VKIDSDK is not defined` - SDK не загрузился
- `exchangeCode failed` - проблема с обменом кода
- `401 Unauthorized` - проблема с токеном
- `CORS error` - проблема с CORS

---

## 📝 ЛЕНДИНГ

**На лендинге (albi-music.ru) ПОКА НЕТ кнопки веб-версии!**

Только кнопки Telegram:
- "Открыть в Telegram" → https://t.me/AlBimusic_bot

**Добавить кнопку веб-версии НА ЛЕНДИНГ нужно ТОЛЬКО ПОСЛЕ:**
1. ✅ VK авторизация работает
2. ✅ Яндекс авторизация работает
3. ✅ Создание песни работает
4. ✅ Мои треки работают
5. ✅ Баланс работает
6. ✅ Всё протестировано

---

## 🔧 КОМАНДЫ ДЛЯ ДЕПЛОЯ (на будущее)

### Обновить frontend:
```bash
scp -i ~/.ssh/id_rsa_albi "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/webapp/index.html" root@37.252.23.214:/var/www/albimusic-web/
```

### Обновить backend:
```bash
scp -i ~/.ssh/id_rsa_albi "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/web_api.py" root@37.252.23.214:/root/albimusic-bot/
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "systemctl restart albimusic-web"
```

### Проверить статус:
```bash
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "systemctl status albimusic-web --no-pager | head -15"
```

### Проверить логи:
```bash
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "journalctl -u albimusic-web -f --no-pager"
```

---

## 🗂 ФАЙЛЫ ПРОЕКТА

### Локальные файлы (Mac):
```
/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/
├── webapp/
│   ├── index.html          # Frontend (правильная версия!)
│   ├── README.md
│   └── DEVELOPMENT.md
├── web_api.py              # Backend API
├── config.py               # Конфигурация
├── db_utils.py             # База данных
├── celery_tasks.py         # Celery задачи
└── landing/                # Лендинг (пока без кнопки веб-версии)
    ├── index.html
    ├── style.css
    └── script.js
```

### Серверные файлы:
```
Сервер: root@37.252.23.214
├── /var/www/albimusic-web/
│   └── index.html          # Frontend
├── /root/albimusic-bot/
│   ├── web_api.py          # Backend
│   └── web_venv/           # Virtual environment
└── /etc/systemd/system/
    └── albimusic-web.service
```

---

## 🚀 ВАЖНО ПОМНИТЬ

1. **VPN блокирует VK/Яндекс** - тестировать ТОЛЬКО без VPN!
2. **Redirect URL:** `https://albi-music.ru/app` (без `/callback`)
3. **Кнопку на лендинг добавлять ТОЛЬКО после полного тестирования**
4. **Веб-версия использует ТУ ЖЕ БД что и Telegram бот** - баланс синхронизирован
5. **Все сервисы должны быть запущены:**
   - albimusic-bot (Telegram)
   - albimusic-web (Web API)
   - albimusic-celery (Worker)
   - albimusic-monitor (Демо)

---

## 📊 СЛЕДУЮЩИЙ ЭТАП

**После успешного тестирования веб-версии:**

1. Добавить кнопку на лендинг (albi-music.ru)
2. Написать короткое описание для кнопки
3. Запустить рекламу ($350 бюджет)
4. Отслеживать конверсию (лендинг → веб-версия → генерация)

---

_Статус обновлён: 16.02.2026 19:45 МСК_
_Следующий шаг: Тестирование без VPN_
