#!/bin/bash
echo "🔄 Восстановление из бэкапа..."

if [ -z "$1" ]; then
    echo "❌ Укажите папку бэкапа: ./restore_from_backup.sh project_backup_YYYYMMDD_HHMMSS"
    echo "📁 Доступные бэкапы:"
    ls -d project_backup_* 2>/dev/null || echo "   Бэкапы не найдены"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Папка бэкапа не найдена: $BACKUP_DIR"
    exit 1
fi

echo "📦 Восстанавливаем файлы из: $BACKUP_DIR"
cp -r "$BACKUP_DIR"/* . 2>/dev/null || true

echo "✅ Файлы восстановлены!"
echo "🚀 Для применения изменений выполните:"
echo "   sudo docker build -t albimusic-bot:latest ."
echo "   sudo docker restart albimusic-bot-primary"
