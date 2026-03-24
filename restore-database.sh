#!/bin/bash
echo "🔄 Восстановление базы данных из бэкапа..."

if [ -z "$1" ]; then
    echo "❌ Укажите файл бэкапа: ./restore-database.sh backups/filename.sql"
    echo "📁 Доступные бэкапы:"
    ls -la backups/*.sql 2>/dev/null || echo "   Бэкапы не найдены"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  ВНИМАНИЕ: Это перезапишет текущую базу данных!"
echo "📁 Бэкап: $BACKUP_FILE"
read -p "Продолжить? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ Восстановление отменено"
    exit 0
fi

# Восстанавливаем базу
PGPASSWORD="aXAnAixKT6@?B9" psql -h localhost -U albimusic_user -d albimusic_bot -f "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ База данных восстановлена из: $BACKUP_FILE"
else
    echo "❌ Ошибка восстановления базы данных"
fi
