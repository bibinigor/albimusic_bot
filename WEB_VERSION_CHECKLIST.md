# 📋 Чеклист для запуска веб-версии AlBi Music

## ✅ Что уже готово

### Инфраструктура (проверено 13.02.2026):
- ✅ Сервер: root@37.252.23.214
- ✅ SSL сертификат: Let's Encrypt для albi-music.ru
- ✅ Nginx: установлен и настроен (порты 80/443)
- ✅ Лендинг: /var/www/albimusic-landing/ (темная тема)
- ✅ MP3 примеры: 9 файлов в /var/www/albimusic-landing/audio/
- ✅ Favicon: /var/www/albimusic-landing/favicon.ico
- ✅ Backend логика: Celery, Monitor, PostgreSQL, YooKassa

### Дизайн (темная тема):
```css
Фон: #0c0b20 → #1a1a2e (градиент)
Акцент 1: #00e5ff (голубой)
Акцент 2: #00ff95 (зелёный)
Текст: #f0f0f0
```

### Цены (уточнено):
- 490₽ = 10 генераций (20 треков)
- 990₽ = 25 генераций (50 треков)
- 1990₽ = 60 генераций (120 треков)
- 3990₽ = 140 генераций (280 треков)
- 300₽ = разблокировка полных версий
- 🎁 Первая генерация БЕСПЛАТНО (демо 45 сек)

---

## ✅ Что получено от пользователя (13.02.2026)

### 1. VK ID (новое приложение)

**Ключи:**
- App ID: `54451761`
- Client Secret (Защищенный): `EXsS6C2HrdCS8I5Pddjn`
- Service Key (Сервисный): `3440b8c23440b8c23440b8c253377e66f3334403440b8c25dce517bbfb4188fd75db900`
- Redirect URL: `https://albi-music.ru/auth/vk/callback` (уже настроен)

**Frontend код (готов):**
```html
<script src="https://unpkg.com/@vkid/sdk@<3.0.0/dist-sdk/umd/index.js"></script>
<script>
  VKID.Config.init({
    app: 54451761,
    redirectUrl: 'https://albi-music.ru/auth/vk/callback',
    responseMode: VKID.ConfigResponseMode.Callback,
  });

  const oAuth = new VKID.OAuthList();
  oAuth.render({ oauthList: ['vkid'] })
    .on(VKID.OAuthListInternalEvents.LOGIN_SUCCESS, (payload) => {
      VKID.Auth.exchangeCode(payload.code, payload.device_id)
        .then(vkidOnSuccess)
        .catch(vkidOnError);
    });
</script>
```

### 2. Sber ID - ⏳ ожидание

**Статус:** Пользователь будет делать после disconnect

**Что нужно получить:**
- Client ID: `???`
- Client Secret: `???`
- Redirect URI: `https://albi-music.ru/auth/sber/callback`

---

## 🚀 Что я сделаю (после получения ключей)

### 1. Backend API (web_api.py)
```python
FastAPI на порту 8001:
├── /api/auth/vk       ← VK OAuth
├── /api/auth/sber     ← Sber ID
├── /api/generate      ← генерация (Celery)
├── /api/tasks/{id}    ← статус
├── /api/history       ← история
├── /api/balance       ← баланс
├── /api/unlock        ← разблокировка 300₽
└── /api/payment       ← пополнение (YooKassa)
```

### 2. Frontend (React SPA)
- Страницы: лендинг, авторизация, генерация, история, баланс
- Встроенный аудиоплеер для демо (45 сек)
- 16 жанров (как в боте)
- Караоке (100₽), кавер (200₽), WAV (50₽)

### 3. Авторизация
- VK OAuth + Sber ID
- Face ID / Touch ID локально (биометрия после первого входа)

### 4. Изменения на лендинге
Добавлю перед кнопкой:
```
🌐 Создать песню вы можете прямо на этой страничке,
не переходя в телеграмм

[🎵 Создать песню ЗДЕСЬ] ← большая кнопка
```

### 5. Nginx + systemd
- Настрою проксирование /api/ → localhost:8001
- Запущу albimusic-web.service

### 6. БД изменения
- Добавлю поле `source ENUM('telegram', 'web')` в таблицу generations
- Monitor научится отправлять результаты в веб через webhook

---

## ⏱ Время реализации

**~2 часа** после получения:
1. VK Redirect URI (настроен)
2. Sber ID ключи (Client ID + Secret)

---

## 📌 Важно

- Telegram бот продолжит работать без изменений
- Вся backend логика (Celery, Monitor) переиспользуется
- БД та же, балансы пользователей сохранятся
- Демо-система (45 сек + разблокировка 300₽) работает идентично

---

## 📞 Когда будешь готов

Скинь мне:
1. ✅ Статус VK Redirect URI (добавлен или скриншот где искать)
2. ✅ Sber ID ключи (Client ID + Secret)

И я запускаюсь! 🚀

_Документ создан: 13 февраля 2026, 14:35 MSK_
