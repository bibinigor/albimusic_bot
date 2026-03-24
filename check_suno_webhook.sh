#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ПРОВЕРКА SUNO WEBHOOK                               ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

echo ""
echo "[1] Поиск webhook обработчика для Suno в FastAPI:"
echo "════════════════════════════════════════════════════════════"

if grep -n "webhook.*suno" main_with_payments.py celery_tasks.py 2>/dev/null; then
    echo "✅ Найдены упоминания webhook suno"
else
    echo "❌ Webhook для Suno не найден"
fi

echo ""
echo "[2] Поиск FastAPI роутов @app.post:"
echo "════════════════════════════════════════════════════════════"

grep -n "@app.post" main_with_payments.py 2>/dev/null | while read line; do
    echo "  $line"
done

WEBHOOK_COUNT=$(grep -c "@app.post" main_with_payments.py 2>/dev/null || echo "0")

if [ $WEBHOOK_COUNT -gt 0 ]; then
    echo ""
    echo "Найдено FastAPI POST роутов: $WEBHOOK_COUNT"
else
    echo "❌ FastAPI POST роуты не найдены"
fi

echo ""
echo "[3] Текущие callBackUrl в коде:"
echo "════════════════════════════════════════════════════════════"

grep -n "callBackUrl" main_with_payments.py celery_tasks.py 2>/dev/null | while read line; do
    echo "  $line"
done

echo ""
echo "[4] Существующие webhook роуты:"
echo "════════════════════════════════════════════════════════════"

if grep -A 5 "@app.post.*webhook" main_with_payments.py 2>/dev/null; then
    echo "✅ Webhook роуты найдены"
else
    echo "ℹ️  Специальных webhook роутов для Suno нет"
fi

echo ""
echo "[5] Анализ метода опроса статуса:"
echo "════════════════════════════════════════════════════════════"

if grep -n "record-info" celery_tasks.py 2>/dev/null; then
    echo "✅ Используется polling через /api/v1/generate/record-info"
    echo ""
    echo "Контекст:"
    grep -B 2 -A 2 "record-info" celery_tasks.py | head -10
else
    echo "⚠️  Метод опроса статуса не найден"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "ВЫВОД:"
echo "════════════════════════════════════════════════════════════"

if grep -q "record-info" celery_tasks.py 2>/dev/null; then
    echo "✅ Бот использует POLLING (опрос статуса)"
    echo "   - Webhook НЕ нужен"
    echo "   - callBackUrl можно оставить как заглушку"
    echo ""
    echo "Рекомендация:"
    echo "  Оставить: \"callBackUrl\": \"https://albi-music.ru/webhook/suno\""
    echo "  Причина: Suno API может использовать его в будущем"
else
    echo "⚠️  Метод получения результатов неясен"
    echo "   Нужна дополнительная проверка кода"
fi

echo "════════════════════════════════════════════════════════════"

