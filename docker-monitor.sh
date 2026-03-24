#!/bin/bash
# Мониторинг для Docker архитектуры - ТОЛЬКО мониторинг, без автозапуска

echo "🔍 Проверка Docker ботов..."

PRIMARY_STATUS=$(sudo docker inspect -f '{{.State.Status}}' albimusic-bot-primary 2>/dev/null || echo "not_found")

if [ "$PRIMARY_STATUS" != "running" ]; then
    echo "🚨 Primary бот не работает! Статус: $PRIMARY_STATUS"
    echo "ℹ️  Для запуска backup выполните: sudo docker start albimusic-bot-backup"
else
    echo "✅ Primary бот: $PRIMARY_STATUS"
fi
