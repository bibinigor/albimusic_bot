#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ПРОВЕРКА generation_type                            ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

echo ""
echo "[1] process_song_lyrics:"
echo "════════════════════════════════════════════════════════════"

grep -A 5 "async def process_song_lyrics" main_with_payments.py | grep "update_data"

if grep -A 5 "async def process_song_lyrics" main_with_payments.py | grep -q "generation_type='song'"; then
    echo "✅ generation_type установлен"
else
    echo "⚠️  generation_type НЕ установлен"
fi

echo ""
echo "[2] process_song_style:"
echo "════════════════════════════════════════════════════════════"

grep -A 10 "async def process_song_style" main_with_payments.py | grep "update_data"

if grep -A 10 "async def process_song_style" main_with_payments.py | grep -q "generation_type='song'"; then
    echo "✅ generation_type установлен"
else
    echo "⚠️  generation_type НЕ установлен"
fi

echo ""
echo "[3] Все установки generation_type='song':"
echo "════════════════════════════════════════════════════════════"

grep -n "generation_type='song'" main_with_payments.py

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

if sudo systemctl is-active --quiet albimusic-bot; then
    echo "✅ Бот работает"
    sudo journalctl -u albimusic-bot -n 5 --no-pager
else
    echo "❌ Бот не работает"
    sudo systemctl status albimusic-bot --no-pager
fi

