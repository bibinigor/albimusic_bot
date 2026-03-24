#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       АНАЛИЗ СТРУКТУРЫ ФАЙЛА                              ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

echo ""
echo "[1] Поиск блоков if __name__:"
echo "════════════════════════════════════════════════════════════"

grep -n "if __name__" main_with_payments.py

echo ""
echo "[2] Количество блоков:"
echo "════════════════════════════════════════════════════════════"

COUNT=$(grep -c "if __name__" main_with_payments.py)
echo "Найдено блоков: $COUNT"

if [ "$COUNT" -gt 1 ]; then
    echo "⚠️  ПРОБЛЕМА: Найдено $COUNT дубликатов!"
else
    echo "✅ Нормально: один блок"
fi

echo ""
echo "[3] Поиск обработчика process_generation_mode:"
echo "════════════════════════════════════════════════════════════"

if grep -q "def process_generation_mode" main_with_payments.py; then
    echo "✅ Обработчик найден"
    grep -n "def process_generation_mode" main_with_payments.py
else
    echo "❌ Обработчик НЕ найден"
fi

echo ""
echo "[4] Контекст дубликатов (если есть):"
echo "════════════════════════════════════════════════════════════"

grep -B 2 -A 5 "if __name__" main_with_payments.py

