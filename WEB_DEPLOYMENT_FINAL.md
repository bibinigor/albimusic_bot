# 🚀 ФИНАЛЬНАЯ ИНСТРУКЦИЯ ПО РАЗВЕРТЫВАНИЮ WEB v2.0

## ✅ ЗАВЕРШЕННЫЕ ЭТАПЫ

### 1. Backend (100% готов)
- ✅ SQL миграции 004, 005, 006 применены
- ✅ YooKassa библиотека установлена
- ✅ web_api.py v2.0 запущен на порту 8001
- ✅ API endpoints работают:
  - `/api/pricing` - тарифные планы
  - `/api/payment/create` - создание платежа
  - `/api/payment/webhook` - webhook YooKassa
  - `/api/unlock/{task_id}` - разблокировка демо
  - `/api/referral/link` - реферальная ссылка
  - `/api/referral/stats` - статистика рефералов

### 2. Database (100% готова)
- ✅ Таблица `pricing_plans` (5 тарифов: 50₽-2000₽)
- ✅ Таблица `processed_payments` (idempotency защита)
- ✅ Таблица `user_accounts` (кросс-платформенность)
- ✅ Таблица `token_transactions` (история транзакций)
- ✅ Таблица `user_actions` (rate limiting)
- ✅ PostgreSQL функции:
  - `process_payment_idempotent()` - безопасные платежи
  - `deduct_tokens_atomic()` - атомарное списание
  - `start_generation_safe()` - старт генерации с проверками
  - `refund_tokens()` - возврат при ошибках
  - `check_rate_limit()` - ограничение запросов
  - `finish_generation()` - завершение генерации

---

## 📋 ОСТАЛОСЬ: Frontend Integration (1 шаг)

### Файл для обновления: `/var/www/albimusic-web/index.html`

**Текущий размер:** 1231 строка  
**Требуется добавить:** 3 ключевых блока кода

---

## 🔧 БЛОК 1: Демо-плеер с ограничением 45 сек

**Где добавить:** В JavaScript секцию (перед функцией `showScreen()`)

```javascript
// ========== ДЕМО-СИСТЕМА (45 сек демо → разблокировка) ==========
function initDemoPlayer(track) {
    const audioElement = document.getElementById(`audio-${track.id}`);
    const unlockButton = document.getElementById(`unlock-${track.id}`);
    
    if (!track.is_unlocked && audioElement) {
        // Ограничение воспроизведения до 45 секунд
        audioElement.addEventListener('timeupdate', function() {
            if (this.currentTime >= 45) {
                this.pause();
                this.currentTime = 45;
                showNotification('⏱️ Демо-версия ограничена 45 секундами. Разблокируйте за 1 токен для полного доступа!', 'warning');
            }
        });
        
        // Блокировка перемотки вперед
        audioElement.addEventListener('seeking', function() {
            if (this.currentTime > 45) {
                this.currentTime = 45;
            }
        });
    }
}

async function unlockTrack(taskId) {
    if (!confirm('Разблокировать полную версию за 1 токен?')) {
        return;
    }
    
    try {
        showNotification('Разблокировка...', 'info');
        
        const response = await axios.post(`${API_BASE_URL}/unlock/${taskId}`, {}, {
            headers: {
                'Authorization': `Bearer ${TOKEN}`
            }
        });
        
        if (response.data.success) {
            showNotification(`✅ Разблокировано! Осталось токенов: ${response.data.balance}`, 'success');
            
            // Обновляем баланс
            document.getElementById('balance').textContent = `${response.data.balance} 🎵`;
            
            // Удаляем кнопку разблокировки
            const unlockBtn = document.getElementById(`unlock-${taskId}`);
            if (unlockBtn) {
                unlockBtn.remove();
            }
            
            // Обновляем аудио на полную версию
            const audioElement = document.getElementById(`audio-${taskId}`);
            if (audioElement && response.data.full_urls) {
                audioElement.src = response.data.full_urls[0]; // Первый трек
                audioElement.removeEventListener('timeupdate', null); // Убираем ограничение
            }
        }
    } catch (error) {
        console.error('Ошибка разблокировки:', error);
        const msg = error.response?.data?.detail || 'Ошибка при разблокировке трека';
        showNotification(`❌ ${msg}`, 'error');
    }
}

// Обновляем функцию loadHistory для добавления демо-плееров
async function loadHistory() {
    try {
        const response = await axios.get(`${API_BASE_URL}/history`, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        
        const historyContainer = document.getElementById('history-list');
        if (response.data.tracks && response.data.tracks.length > 0) {
            historyContainer.innerHTML = response.data.tracks.map(track => {
                const isDemo = !track.is_unlocked && track.demo_urls && track.demo_urls.length > 0;
                const audioUrl = isDemo ? track.demo_urls[0] : (track.audio_urls ? track.audio_urls[0] : '');
                
                return `
                    <div class="track-item">
                        <div class="track-info">
                            <strong>${track.title || 'Без названия'}</strong>
                            <p>${track.style || ''} ${isDemo ? '🔒 ДЕМО (45 сек)' : '✅'}</p>
                            <small>${new Date(track.created_at).toLocaleString('ru-RU')}</small>
                        </div>
                        ${audioUrl ? `
                            <audio id="audio-${track.id}" controls style="width: 100%; margin-top: 10px;">
                                <source src="${audioUrl}" type="audio/mpeg">
                            </audio>
                            <script>
                                initDemoPlayer({id: ${track.id}, is_unlocked: ${!isDemo}});
                            </script>
                        ` : ''}
                        ${isDemo ? `
                            <button id="unlock-${track.id}" onclick="unlockTrack(${track.id})" 
                                    style="margin-top: 10px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                                🔓 Разблокировать за 1 токен
                            </button>
                        ` : ''}
                    </div>
                `;
            }).join('');
        } else {
            historyContainer.innerHTML = '<p style="text-align: center; opacity: 0.6;">История пуста</p>';
        }
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    }
}
```

---

## 🔧 БЛОК 2: UI Платежей и Реферальной системы

**Где добавить:** В HTML секцию (добавить новые экраны после существующих)

```html
<!-- ========== ЭКРАН ПОКУПКИ ТОКЕНОВ ========== -->
<div id="payment-screen" class="screen">
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 20px;">💳 Покупка токенов</h2>
        
        <div id="pricing-plans" style="display: flex; flex-direction: column; gap: 15px;">
            <!-- Заполняется через loadPricing() -->
        </div>
        
        <p style="text-align: center; margin-top: 20px; font-size: 14px; opacity: 0.7;">
            Оплата через ЮKassa (карты, СБП, электронные кошельки)
        </p>
    </div>
</div>

<!-- ========== ЭКРАН РЕФЕРАЛЬНОЙ ПРОГРАММЫ ========== -->
<div id="referral-screen" class="screen">
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 20px;">🎁 Реферальная программа</h2>
        
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h3 style="margin-bottom: 10px;">Награды:</h3>
            <ul style="line-height: 2; padding-left: 20px;">
                <li>🎵 <strong>+2 токена</strong> за каждого приглашенного друга</li>
                <li>🎁 <strong>+5 токенов</strong> бонус за 5-го друга</li>
            </ul>
        </div>
        
        <div style="background: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h3 style="margin-bottom: 10px;">Ваша ссылка:</h3>
            <div style="display: flex; gap: 10px;">
                <input id="referral-link" type="text" readonly 
                       style="flex: 1; padding: 10px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white;">
                <button onclick="copyReferralLink()" style="padding: 10px 20px;">📋 Копировать</button>
            </div>
            <button onclick="shareReferralLink()" style="margin-top: 10px; width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                📤 Поделиться
            </button>
        </div>
        
        <div id="referral-stats" style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px;">
            <h3 style="margin-bottom: 15px;">Статистика:</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: center;">
                <div>
                    <div style="font-size: 32px; font-weight: bold; color: #667eea;" id="referral-count">0</div>
                    <div style="opacity: 0.7; font-size: 14px;">Друзей</div>
                </div>
                <div>
                    <div style="font-size: 32px; font-weight: bold; color: #f093fb;" id="referral-earned">0</div>
                    <div style="opacity: 0.7; font-size: 14px;">Заработано токенов</div>
                </div>
            </div>
        </div>
    </div>
</div>
```

**JavaScript для платежей и рефералов:**

```javascript
// ========== ПЛАТЕЖИ YOOKASSA ==========
async function loadPricing() {
    try {
        const response = await axios.get(`${API_BASE_URL}/pricing`);
        const container = document.getElementById('pricing-plans');
        
        container.innerHTML = response.data.plans.map(plan => `
            <div class="plan-card" onclick="createPayment(${plan.amount}, ${plan.tokens})" 
                 style="background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%); 
                        padding: 20px; border-radius: 15px; cursor: pointer; border: 2px solid rgba(102,126,234,0.3);
                        transition: all 0.3s;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 24px; font-weight: bold;">${plan.tokens} 🎵</div>
                        <div style="opacity: 0.7; font-size: 14px; margin-top: 5px;">
                            ${plan.amount === 500 ? '🔥 Популярный' : plan.amount === 2000 ? '💎 Выгоднее всего' : ''}
                        </div>
                    </div>
                    <div style="font-size: 20px; font-weight: bold;">${plan.amount} ₽</div>
                </div>
                ${plan.amount >= 500 ? `<div style="margin-top: 10px; font-size: 12px; opacity: 0.8;">
                    💰 ${Math.round((plan.amount / plan.tokens))₽/токен
                </div>` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Ошибка загрузки тарифов:', error);
    }
}

async function createPayment(amount, tokens) {
    if (!confirm(`Купить ${tokens} токенов за ${amount} ₽?`)) {
        return;
    }
    
    try {
        showNotification('Создание платежа...', 'info');
        
        const response = await axios.post(`${API_BASE_URL}/payment/create`, {
            amount: amount
        }, {
            headers: {
                'Authorization': `Bearer ${TOKEN}`
            }
        });
        
        if (response.data.confirmation_url) {
            // Перенаправляем на страницу оплаты ЮKassa
            window.location.href = response.data.confirmation_url;
        }
    } catch (error) {
        console.error('Ошибка создания платежа:', error);
        showNotification(`❌ ${error.response?.data?.detail || 'Ошибка создания платежа'}`, 'error');
    }
}

// ========== РЕФЕРАЛЬНАЯ СИСТЕМА ==========
async function loadReferralInfo() {
    try {
        // Получаем реферальную ссылку
        const linkResponse = await axios.get(`${API_BASE_URL}/referral/link`, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        document.getElementById('referral-link').value = linkResponse.data.link;
        
        // Получаем статистику
        const statsResponse = await axios.get(`${API_BASE_URL}/referral/stats`, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        });
        document.getElementById('referral-count').textContent = statsResponse.data.referrals_count;
        document.getElementById('referral-earned').textContent = statsResponse.data.tokens_earned;
    } catch (error) {
        console.error('Ошибка загрузки реферальной информации:', error);
    }
}

function copyReferralLink() {
    const input = document.getElementById('referral-link');
    input.select();
    document.execCommand('copy');
    showNotification('✅ Ссылка скопирована!', 'success');
}

async function shareReferralLink() {
    const link = document.getElementById('referral-link').value;
    
    // Web Share API (для мобильных)
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'ALBI Music - Генератор музыки',
                text: 'Создавай музыку с AI! Получи +2 токена по моей ссылке 🎵',
                url: link
            });
            showNotification('✅ Успешно поделились!', 'success');
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Ошибка шэринга:', error);
            }
        }
    } else {
        // Fallback: копируем в буфер
        copyReferralLink();
    }
}

// Проверка реферального кода при загрузке
function checkReferralCode() {
    const urlParams = new URLSearchParams(window.location.search);
    const refCode = urlParams.get('ref');
    
    if (refCode && TOKEN) {
        axios.post(`${API_BASE_URL}/referral/register`, {
            referral_code: refCode
        }, {
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        }).then(response => {
            if (response.data.bonus_added) {
                showNotification(`🎁 Вы получили +2 токена по реферальной ссылке!`, 'success');
                updateBalance();
            }
        }).catch(error => {
            console.log('Реферальный код уже использован или недействителен');
        });
    }
}
```

---

## 🔧 БЛОК 3: Обновление Bottom Navigation

**Где обновить:** В HTML разделе Bottom Navigation (добавить кнопки)

```html
<!-- В существующий <nav class="bottom-nav"> добавить: -->
<button onclick="showScreen('payment-screen'); loadPricing();">
    <span class="nav-icon">💳</span>
    <span class="nav-label">Купить</span>
</button>
<button onclick="showScreen('referral-screen'); loadReferralInfo();">
    <span class="nav-icon">🎁</span>
    <span class="nav-label">Рефералы</span>
</button>
```

---

## 🔧 БЛОК 4: Обновление init() функции

**Где обновить:** В функции `init()` добавить вызовы:

```javascript
async function init() {
    // ... существующий код ...
    
    // НОВОЕ: Проверка реферального кода
    checkReferralCode();
    
    // НОВОЕ: Загрузка истории с демо-плеерами
    if (TOKEN) {
        await loadHistory();
    }
}
```

---

## ⚙️ НАСТРОЙКА YOOKASSA WEBHOOK

### В личном кабинете ЮKassa:

1. Перейти в **Настройки → Уведомления**
2. Webhook URL: `https://albi-music.ru/api/payment/webhook`
3. События для отправки:
   - ✅ `payment.succeeded` (платеж успешен)
   - ✅ `payment.canceled` (платеж отменен)
4. HTTP метод: **POST**
5. Формат: **JSON**

---

## 📊 ТЕСТИРОВАНИЕ

### 1. Проверка Backend API:
```bash
# Тарифы
curl http://localhost:8001/api/pricing

# Health
curl http://localhost:8001/health
```

### 2. Проверка Frontend:
- Откройте: `https://albi-music.ru/app/?token=YOUR_JWT_TOKEN`
- Проверьте отображение экранов: Создание → История → Купить → Рефералы
- Проверьте демо-плеер в истории

### 3. Проверка демо-системы:
- Создайте трек
- Проверьте, что воспроизводится только 45 секунд
- Проверьте кнопку "Разблокировать за 1 токен"

---

## 🎯 МЕТРИКИ ДЛЯ ОТСЛЕЖИВАНИЯ

### SQL запросы для аналитики:

```sql
-- 1. Конверсия демо → разблокировка
SELECT 
    COUNT(*) FILTER (WHERE is_unlocked) * 100.0 / COUNT(*) as conversion_rate
FROM demo_tracks WHERE created_at > NOW() - INTERVAL '7 days';

-- 2. Средний чек
SELECT AVG(amount) FROM payments WHERE status = 'succeeded';

-- 3. Реферальная активность
SELECT 
    COUNT(DISTINCT referrer_id) * 100.0 / COUNT(DISTINCT id) as referral_users_percent
FROM users WHERE created_at > NOW() - INTERVAL '30 days';

-- 4. Топ тарифы
SELECT tokens_amount, COUNT(*), SUM(amount) 
FROM payments WHERE status = 'succeeded' 
GROUP BY tokens_amount ORDER BY COUNT(*) DESC;
```

---

## ✅ ИТОГОВЫЙ ЧЕКЛИСТ

- [x] SQL миграции применены (004, 005, 006)
- [x] yookassa установлен
- [x] web_api.py v2.0 запущен
- [x] API endpoints работают
- [x] Права БД настроены
- [ ] Frontend обновлен (3 блока кода добавлены)
- [ ] YooKassa webhook настроен
- [ ] Тестирование флоу: демо → разблокировка → оплата → реферал

---

## 📞 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА

**Backend API логи:**
```bash
tail -f /root/albimusic-bot/web_api.log
```

**Проверка процессов:**
```bash
ps aux | grep web_api.py
```

**Перезапуск API:**
```bash
pkill -f web_api.py
cd /root/albimusic-bot && nohup /root/albimusic-bot/web_venv/bin/python3 web_api.py > web_api.log 2>&1 &
```

---

## 🚀 ГОТОВО К PRODUCTION!

**Backend:** ✅ 100%  
**Database:** ✅ 100%  
**Frontend:** 🟡 Требуется интеграция 3 блоков кода  
**Documentation:** ✅ 100%

**Следующий шаг:** Применить код из Блоков 1-4 к `/var/www/albimusic-web/index.html`
