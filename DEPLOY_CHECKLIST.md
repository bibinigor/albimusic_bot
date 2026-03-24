# 🚀 Чеклист деплоя AlBi Music Bot

## 📋 Перед деплоем

- [ ] Прочитать ARCHITECTURE.md
- [ ] Обновить WORK_LOG.md с описанием изменений
- [ ] Обновить NEW_TEXTS.md если менялись тексты
- [ ] Проверить что все изменения закоммичены локально

---

## 📦 Процесс деплоя

### 1. Создать бэкап на сервере
```bash
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 \
"cd /root/albimusic-bot && mkdir -p backups_deploy_\$(date +%Y%m%d_%H%M%S) && \
cp main_with_payments.py celery_tasks.py backups_deploy_\$(date +%Y%m%d_%H%M%S)/"
```

### 2. Загрузить код на сервер
```bash
cd "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude"

# Основные файлы
scp -i ~/.ssh/id_rsa_albi main_with_payments.py root@37.252.23.214:/root/albimusic-bot/
scp -i ~/.ssh/id_rsa_albi celery_tasks.py root@37.252.23.214:/root/albimusic-bot/
scp -i ~/.ssh/id_rsa_albi run_monitor_notify.py root@37.252.23.214:/root/albimusic-bot/
scp -i ~/.ssh/id_rsa_albi index.html root@37.252.23.214:/root/albimusic-bot/
```

### 3. ⚠️ ОБЯЗАТЕЛЬНО: Загрузить документацию
```bash
scp -i ~/.ssh/id_rsa_albi ARCHITECTURE.md WORK_LOG.md NEW_TEXTS.md root@37.252.23.214:/root/albimusic-bot/
```

### 4. Перезапустить сервисы
```bash
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 \
"systemctl restart albimusic-bot && systemctl restart albimusic-celery"
```

### 5. Проверить статус
```bash
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 \
"systemctl status albimusic-bot albimusic-celery | grep -E 'Active:|albimusic-'"
```

### 6. Создать локальный бэкап
```bash
cd "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude"
mkdir -p "backups_local_\$(date +%Y%m%d_%H%M%S)"
cp main_with_payments.py celery_tasks.py "backups_local_\$(date +%Y%m%d_%H%M%S)/"
```

---

## ✅ После деплоя

- [ ] Проверить что бот отвечает в Telegram
- [ ] Проверить новую функциональность
- [ ] Проверить логи на ошибки
- [ ] Обновить память (MEMORY.md) с датой последнего деплоя

---

## 📊 Информация о сервере

**Сервер:** 37.252.23.214
**Пользователь:** root
**SSH ключ:** ~/.ssh/id_rsa_albi
**Путь к боту:** /root/albimusic-bot

**Сервисы:**
- `albimusic-bot.service` - Telegram бот
- `albimusic-celery.service` - Celery worker
- `albimusic-monitor.service` - Monitor для демо-треков

---

## 🔍 Полезные команды

```bash
# Посмотреть логи бота
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "journalctl -u albimusic-bot -f"

# Посмотреть логи Celery
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "journalctl -u albimusic-celery -f"

# Проверить процессы
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "ps aux | grep -E 'main_with_payments|celery|monitor'"

# Проверить БД
ssh -i ~/.ssh/id_rsa_albi root@37.252.23.214 "psql -U albimusic_user -d albimusic_db -c 'SELECT COUNT(*) FROM generations;'"
```

---

_Создано: 6 февраля 2026_
