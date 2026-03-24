# AlBi-music Bot Backup
## Дата создания: Mon Dec  1 10:43:07 PM MSK 2025
## Версия системы: Производственная

## Содержимое бэкапа:
1. **База данных:** albimusic_db_*.dump (формат custom pg_dump)
2. **Исходный код:** Все .py файлы проекта
3. **Конфигурации:** config.py, requirements.txt
4. **Systemd сервисы:** albimusic-bot.service, albimusic-celery.service, albimusic-monitor.service
5. **Конфигурации системы:** logrotate, rabbitmq.conf

## Восстановление:
### База данных:
```bash
pg_restore -d albimusic_bot -U albimusic_user -h localhost --clean --if-exists backup_file.dump
```

### Systemd сервисы:
```bash
sudo cp albimusic-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable albimusic-bot albimusic-celery albimusic-monitor
```

## Контакты:
- Сервер: Timeweb, IP: 37.252.23.214
- Домен: https://albi-music.ru
- Телеграм бот: @AlBimusic_bot

## Важные данные:
- Пароль БД: aXAnAixKT6@?B9
- RabbitMQ пользователь: albimusic
- RabbitMQ пароль: StrongPassword123!
- Suno API ключ: 615290cfecdf58e6251835ba7971ab65
