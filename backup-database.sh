#!/bin/bash
echo "💾 Создание бэкапа базы данных..."

mkdir -p backups
BACKUP_FILE="backups/albimusic_backup_$(date +%Y%m%d_%H%M%S).sql"

# Указываем пароль для pg_dump
PGPASSWORD="aXAnAixKT6@?B9" pg_dump -h localhost -U albimusic_user -d albimusic_bot > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Бэкап создан: $BACKUP_FILE"
    ls -t backups/*.sql | tail -n +11 | xargs rm -f
    echo "🗑️  Удалены старые бэкапы (оставлены последние 10)"
else
    echo "❌ Ошибка создания бэкапа"
    exit 1
fi
