#!/bin/bash
# Скрипт автоматического бэкапа AlBi-music Bot
BACKUP_DIR="/root/albimusic-backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="$BACKUP_DIR/albimusic_db_$DATE.dump"
ARCHIVE_FILE="/root/albimusic-backup-$DATE.tar.gz"

# Создаем директорию
mkdir -p $BACKUP_DIR

# Бэкап базы данных
PGPASSWORD="aXAnAixKT6@?B9" pg_dump -d albimusic_bot -U albimusic_user -h localhost -F c -f $DB_FILE

# Копируем файлы
cp -r /root/albimusic-bot/*.py /root/albimusic-bot/*.txt /root/albimusic-bot/*.md /root/albimusic-bot/config.py $BACKUP_DIR/
cp /etc/systemd/system/albimusic-*.service $BACKUP_DIR/ 2>/dev/null
cp /etc/logrotate.d/albimusic $BACKUP_DIR/ 2>/dev/null

# Архивируем
cd /root
tar -czf $ARCHIVE_FILE "$(basename $BACKUP_DIR)"

# Удаляем старые архивы (храним 7 последних)
ls -t /root/albimusic-backup-*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true

# Удаляем временную папку
rm -rf $BACKUP_DIR

echo "Бэкап создан: $ARCHIVE_FILE"
