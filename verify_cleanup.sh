#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ПРОВЕРКА ОЧИСТКИ                                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

echo ""
echo "[1] Количество блоков с generation_type в функции:"
echo "════════════════════════════════════════════════════════════"

COUNT=$(grep -A 100 "async def process_generation_mode" main_with_payments.py | grep -c "generation_type = ")

if [ $COUNT -eq 1 ]; then
    echo "✅ Только один блок (правильно)"
elif [ $COUNT -gt 1 ]; then
    echo "⚠️  Найдено $COUNT блоков (возможно дубликаты)"
else
    echo "❌ Не найдено блоков"
fi

echo ""
echo "[2] Наличие умной логики:"
echo "════════════════════════════════════════════════════════════"

if grep -A 100 "async def process_generation_mode" main_with_payments.py | grep -q "if lyrics:"; then
    echo "✅ Умная логика присутствует"
else
    echo "❌ Умная логика не найдена"
fi

echo ""
echo "[3] Определение logger:"
echo "════════════════════════════════════════════════════════════"

grep -A 20 "async def process_generation_mode" main_with_payments.py | grep -E "logger = |import logging"

echo ""
echo "[4] Синтаксис:"
echo "════════════════════════════════════════════════════════════"

if python3 -m py_compile main_with_payments.py 2>/dev/null; then
    echo "✅ Синтаксис корректен"
else
    echo "❌ Есть ошибки:"
    python3 -m py_compile main_with_payments.py
fi

echo ""
echo "[5] Статус бота:"
echo "════════════════════════════════════════════════════════════"

sudo systemctl status albimusic-bot --no-pager -n 5

