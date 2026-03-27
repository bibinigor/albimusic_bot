#!/bin/bash

# Скрипт резервного копирования данных VK бота

# Загружаем переменные окружения
source ../.env

# Создаем директорию для бэкапов
BACKUP_DIR="../backups/vk_bot"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

echo "📦 Создание резервной копии..."
mkdir -p "$BACKUP_PATH"

# Функция для логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Бэкап PostgreSQL
backup_postgres() {
    log_message "🗄️ Создание бэкапа PostgreSQL..."
    pg_dump "$POSTGRES_URI" > "$BACKUP_PATH/database.sql"
    if [ $? -eq 0 ]; then
        log_message "✅ Бэкап PostgreSQL создан успешно"
    else
        log_message "❌ Ошибка создания бэкапа PostgreSQL"
        exit 1
    fi
}

# Бэкап Redis
backup_redis() {
    log_message "📊 Создание бэкапа Redis..."
    redis-cli save
    cp /var/lib/redis/dump.rdb "$BACKUP_PATH/redis_dump.rdb"
    if [ $? -eq 0 ]; then
        log_message "✅ Бэкап Redis создан успешно"
    else
        log_message "❌ Ошибка создания бэкапа Redis"
        exit 1
    fi
}

# Бэкап конфигурации
backup_config() {
    log_message "⚙️ Создание бэкапа конфигурации..."
    cp ../.env "$BACKUP_PATH/env.backup"
    cp ../vk_config.py "$BACKUP_PATH/vk_config.py.backup"
    if [ $? -eq 0 ]; then
        log_message "✅ Бэкап конфигурации создан успешно"
    else
        log_message "❌ Ошибка создания бэкапа конфигурации"
        exit 1
    fi
}

# Архивация бэкапа
create_archive() {
    log_message "📦 Создание архива..."
    cd "$BACKUP_DIR"
    tar -czf "backup_$TIMESTAMP.tar.gz" "$TIMESTAMP"
    if [ $? -eq 0 ]; then
        log_message "✅ Архив создан успешно"
        rm -rf "$TIMESTAMP"
    else
        log_message "❌ Ошибка создания архива"
        exit 1
    fi
}

# Очистка старых бэкапов (оставляем последние 5)
cleanup_old_backups() {
    log_message "🧹 Очистка старых бэкапов..."
    cd "$BACKUP_DIR"
    ls -t backup_*.tar.gz | tail -n +6 | xargs -r rm
    log_message "✅ Очистка завершена"
}

# Функция восстановления из бэкапа
restore_backup() {
    local backup_file=$1
    if [ ! -f "$backup_file" ]; then
        log_message "❌ Файл бэкапа не найден: $backup_file"
        exit 1
    fi

    log_message "🔄 Начало восстановления из бэкапа..."
    
    # Создаем временную директорию для распаковки
    local temp_dir="/tmp/vk_bot_restore_$TIMESTAMP"
    mkdir -p "$temp_dir"
    
    # Распаковываем архив
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Останавливаем сервисы
    sudo systemctl stop vk-albimusic-bot
    sudo systemctl stop vk-albimusic-celery
    
    # Восстанавливаем PostgreSQL
    log_message "🗄️ Восстановление базы данных..."
    psql "$POSTGRES_URI" < "$temp_dir"/**/database.sql
    
    # Восстанавливаем Redis
    log_message "📊 Восстановление Redis..."
    sudo systemctl stop redis
    cp "$temp_dir"/**/redis_dump.rdb /var/lib/redis/dump.rdb
    sudo chown redis:redis /var/lib/redis/dump.rdb
    sudo systemctl start redis
    
    # Восстанавливаем конфигурацию
    log_message "⚙️ Восстановление конфигурации..."
    cp "$temp_dir"/**/env.backup ../.env
    cp "$temp_dir"/**/vk_config.py.backup ../vk_config.py
    
    # Запускаем сервисы
    sudo systemctl start vk-albimusic-bot
    sudo systemctl start vk-albimusic-celery
    
    # Очистка
    rm -rf "$temp_dir"
    
    log_message "✅ Восстановление завершено успешно"
}

# Основной блок
case "$1" in
    "backup")
        log_message "🚀 Начало резервного копирования..."
        backup_postgres
        backup_redis
        backup_config
        create_archive
        cleanup_old_backups
        log_message "✅ Резервное копирование завершено успешно"
        ;;
    "restore")
        if [ -z "$2" ]; then
            log_message "❌ Укажите файл для восстановления"
            echo "Использование: $0 restore <путь к файлу бэкапа>"
            exit 1
        fi
        restore_backup "$2"
        ;;
    *)
        echo "Использование: $0 {backup|restore <файл>}"
        exit 1
        ;;
esac