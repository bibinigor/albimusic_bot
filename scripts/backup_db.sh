#!/bin/bash

# Конфигурация
BACKUP_DIR="/var/backups/albimusic-bot"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="albimusic_bot"
LOG_FILE="/var/log/albimusic-bot/backup.log"

# Создаем директорию для логов
mkdir -p /var/log/albimusic-bot

# Начало бэкапа
echo "=== Backup started at $(date) ===" >> "$LOG_FILE"

# Проверяем доступность PostgreSQL
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "ERROR: Database '$DB_NAME' not found!" >> "$LOG_FILE"
    exit 1
fi

# Создаем бэкап
echo "Creating backup for database: $DB_NAME" >> "$LOG_FILE"
sudo -u postgres pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"

# Проверяем успешность
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/db_${DATE}.sql.gz" | cut -f1)
    echo "SUCCESS: Backup created: db_${DATE}.sql.gz (Size: $BACKUP_SIZE)" >> "$LOG_FILE"
else
    echo "ERROR: Backup failed!" >> "$LOG_FILE"
    exit 1
fi

# Удаляем старые бэкапы (старше 7 дней)
echo "Cleaning old backups (older than 7 days)..." >> "$LOG_FILE"
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +7 -delete

# Финализация
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "db_*.sql.gz" | wc -l)
echo "Backups in directory: $BACKUP_COUNT" >> "$LOG_FILE"
echo "=== Backup finished at $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
