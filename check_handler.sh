#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ПРОВЕРКА ОБРАБОТЧИКА                                ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

echo ""
echo "[1] Обработчик в коде:"
echo "════════════════════════════════════════════════════════════"

if grep -q "def process_generation_mode" main_with_payments.py; then
    echo "✅ Найден"
    echo ""
    grep -B 1 -A 10 "def process_generation_mode" main_with_payments.py
else
    echo "❌ НЕ найден"
fi

echo ""
echo "[2] Декоратор callback_query_handler:"
echo "════════════════════════════════════════════════════════════"

grep -B 1 "def process_generation_mode" main_with_payments.py | head -2

echo ""
echo "[3] Callback_data в клавиатуре:"
echo "════════════════════════════════════════════════════════════"

grep -n "mode_exact\|mode_creative" main_with_payments.py

echo ""
echo "[4] Статус бота:"
echo "════════════════════════════════════════════════════════════"

if sudo systemctl is-active --quiet albimusic-bot; then
    echo "✅ Бот работает"
    
    echo ""
    echo "Последние логи:"
    sudo journalctl -u albimusic-bot -n 5 --no-pager
else
    echo "❌ Бот не работает"
fi

