# 📋 Инструкция по настройке Firebase Phone Auth

## Что это?

Firebase Phone Authentication - бесплатный сервис от Google для авторизации по номеру телефона через SMS.

**Бесплатно:** 10,000 SMS в месяц
**Платно:** $0.01 за SMS после превышения лимита

---

## Шаг 1: Создание проекта Firebase

1. **Зайди на Firebase Console:**
   - https://console.firebase.google.com/

2. **Войди через Google аккаунт** (любой личный)

3. **Создай новый проект:**
   - Нажми "Add project" или "Создать проект"
   - Название: **"AlBi Music"**
   - Нажми "Continue"

4. **Google Analytics (опционально):**
   - Можешь отключить (не нужен для SMS)
   - Или оставить включенным
   - Нажми "Create project"

5. **Подожди 1-2 минуты** пока проект создаётся

---

## Шаг 2: Добавление веб-приложения

1. **В консоли проекта:**
   - Нажми на иконку **"</>"** (Web)
   - Или "Add app" → "Web"

2. **Регистрация приложения:**
   - App nickname: **"AlBi Music Web"**
   - ☑️ Also set up Firebase Hosting (можно не ставить галочку)
   - Нажми "Register app"

3. **Скопируй Firebase Config:**

   Ты увидишь код вида:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
     authDomain: "albi-music-xxxxx.firebaseapp.com",
     projectId: "albi-music-xxxxx",
     storageBucket: "albi-music-xxxxx.appspot.com",
     messagingSenderId: "123456789012",
     appId: "1:123456789012:web:xxxxxxxxxxxxx"
   };
   ```

   **СКОПИРУЙ ВСЁ это** и скинь мне!

4. Нажми "Continue to console"

---

## Шаг 3: Включение Phone Authentication

1. **В левом меню выбери:**
   - **"Build"** → **"Authentication"**

2. **Нажми "Get started"**

3. **Вкладка "Sign-in method":**
   - Найди **"Phone"**
   - Нажми на него
   - Переключатель **"Enable"** → ON
   - Нажми "Save"

---

## Шаг 4: Настройка доменов

1. **В той же вкладке "Sign-in method":**
   - Прокрути вниз до раздела **"Authorized domains"**

2. **Добавь свой домен:**
   - Нажми "Add domain"
   - Введи: `albi-music.ru`
   - Нажми "Add"

**Важно:** Firebase автоматически добавляет `localhost` для разработки.

---

## Шаг 5: Настройка reCAPTCHA (обязательно!)

Firebase использует reCAPTCHA для защиты от ботов.

### Вариант A: Invisible reCAPTCHA (рекомендую)
Работает автоматически, пользователь ничего не видит.

### Вариант B: reCAPTCHA v2
Показывает "Я не робот" чекбокс.

**Что делать:**
1. В Authentication → Settings → Phone
2. Выбери "Invisible reCAPTCHA" (по умолчанию)
3. Готово! Firebase сам настроит

---

## Шаг 6: Проверка квот SMS

1. **В Firebase Console:**
   - Левое меню → "Usage and billing"
   - Раздел "Authentication"
   - Увидишь лимит: **10,000 SMS/месяц бесплатно**

2. **Если нужно больше:**
   - Перейди на Blaze план (pay-as-you-go)
   - Платишь только за превышение ($0.01/SMS)

---

## Шаг 7: Что мне передать

Скинь мне **Firebase Config** (из Шага 2, пункт 3):

```javascript
{
  apiKey: "AIzaSy...",
  authDomain: "albi-music-xxxxx.firebaseapp.com",
  projectId: "albi-music-xxxxx",
  storageBucket: "albi-music-xxxxx.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:xxxxxxxxxxxxx"
}
```

**Также скажи:**
- ✅ Phone Authentication включен?
- ✅ Домен `albi-music.ru` добавлен?

---

## 🔐 Безопасность

**Важно:** Firebase config (apiKey и т.д.) можно безопасно использовать в frontend коде - это публичные ключи.

**Секретный ключ** для backend мы получим отдельно (Service Account).

---

## ❓ Возможные проблемы

**Проблема 1:** "SMS не отправляются"
- Проверь что Phone Authentication включен
- Проверь квоты (10k в месяц не превышены)
- Проверь что домен в Authorized domains

**Проблема 2:** "reCAPTCHA не работает"
- Проверь что домен добавлен в Authorized domains
- Попробуй с другого браузера / устройства
- Проверь консоль браузера на ошибки

**Проблема 3:** "Требуют добавить банковскую карту"
- Для бесплатного лимита карта НЕ нужна
- Если спрашивает - выбери "Spark plan" (бесплатный)
- Blaze plan нужен только если хочешь >10k SMS

**Проблема 4:** "SMS не доходят в Россию"
- Firebase использует Twilio для SMS
- В России работает, но могут быть задержки (1-5 минут)
- Альтернатива: SMS.ru (российский сервис)

---

## 📊 Как будет работать для пользователя

```
1. Пользователь вводит номер: +7 900 123-45-67
2. Нажимает "Получить код"
3. Firebase отправляет SMS с кодом: "123456"
4. Пользователь вводит код
5. Firebase проверяет код
6. Если верный → авторизация успешна!
```

---

## 🆚 Firebase vs SMS.ru

| Параметр | Firebase | SMS.ru |
|----------|----------|---------|
| Бесплатно | 10,000/месяц | ~100/месяц |
| Цена после | $0.01/SMS | ~3₽/SMS |
| Интеграция | Простая | Сложнее |
| Доставка в РФ | Медленная (1-5 мин) | Быстрая (<1 мин) |
| Для старта | ✅ Идеально | Потом |

**Вывод:** Начни с Firebase, если увидишь проблемы → переключимся на SMS.ru

---

## ⏱ Время настройки: 10-15 минут

Всё подробно расписал! Если застрянешь - скриншот + скинь мне! 🚀

---

_Создано: 13 февраля 2026_
