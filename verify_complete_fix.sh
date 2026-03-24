#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ПРОВЕРКА КОМПЛЕКСНОГО ИСПРАВЛЕНИЯ                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

echo ""
echo "[1] Вариант 1 - Умный обработчик:"
echo "════════════════════════════════════════════════════════════"

if grep -q "Умное определение типа" main_with_payments.py; then
    echo "✅ Умный обработчик установлен"
    grep -A 5 "УМНОЕ ОПРЕДЕЛЕНИЕ" main_with_payments.py
else
    echo "⚠️  Проверьте вручную"
fi

echo ""
echo "[2] Вариант 2 - Установка generation_type:"
echo "════════════════════════════════════════════════════════════"

grep -n "generation_type='song'" main_with_payments.py | head -5

echo ""
echo "[3] Проверка логики определения типа:"
echo "════════════════════════════════════════════════════════════"

grep -A 20 "def process_generation_mode" main_with_payments.py | grep -E "if lyrics:|elif prompt:|generation_type"

echo ""
echo "[4] Синтаксис:"
echo "════════════════════════════════════════════════════════════"

if python3 -m py_compile main_with_payments.py 2>/dev/null; then
    echo "✅ Синтаксис корректен"
else
    echo "❌ Есть ошибки"
    python3 -m py_compile main_with_payments.py
fi

echo ""
echo "[5] Статус бота:"
echo "════════════════════════════════════════════════════════════"

sudo systemctl status albimusic-bot --no-pager -n 5

