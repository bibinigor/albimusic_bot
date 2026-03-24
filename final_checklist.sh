#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ФИНАЛЬНЫЙ CHECKLIST                                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"

cd /root/albimusic-bot

SUCCESS=0
TOTAL=0

# Проверка 1
TOTAL=$((TOTAL + 1))
echo -n "[1/7] process_song_lyrics имеет generation_type: "
if grep -A 5 "async def process_song_lyrics" main_with_payments.py | grep -q "generation_type='song'"; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "❌"
fi

# Проверка 2
TOTAL=$((TOTAL + 1))
echo -n "[2/7] process_song_style имеет generation_type: "
if grep -A 10 "async def process_song_style" main_with_payments.py | grep -q "generation_type='song'"; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "❌"
fi

# Проверка 3
TOTAL=$((TOTAL + 1))
echo -n "[3/7] Обработчик process_generation_mode существует: "
if grep -q "def process_generation_mode" main_with_payments.py; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "❌"
fi

# Проверка 4
TOTAL=$((TOTAL + 1))
echo -n "[4/7] Умная логика определения типа: "
if grep -A 20 "def process_generation_mode" main_with_payments.py | grep -q "if lyrics:"; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "❌"
fi

# Проверка 5
TOTAL=$((TOTAL + 1))
echo -n "[5/7] Синтаксис корректен: "
if python3 -m py_compile main_with_payments.py 2>/dev/null; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "❌"
fi

# Проверка 6
TOTAL=$((TOTAL + 1))
echo -n "[6/7] Бот запущен: "
if sudo systemctl is-active --quiet albimusic-bot; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "❌"
fi

# Проверка 7
TOTAL=$((TOTAL + 1))
echo -n "[7/7] Нет ошибок в логах: "
if ! sudo journalctl -u albimusic-bot -n 20 --no-pager | grep -q "Error\|Traceback"; then
    echo "✅"
    SUCCESS=$((SUCCESS + 1))
else
    echo "⚠️"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Результат: $SUCCESS/$TOTAL проверок пройдено"

if [ $SUCCESS -eq $TOTAL ]; then
    echo "✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!"
    echo ""
    echo "Теперь протестируйте в боте:"
    echo "  1. /song"
    echo "  2. Введите стиль и текст"
    echo "  3. Выберите режим"
    echo "  4. Проверьте генерацию"
else
    echo "⚠️  Есть проблемы, проверьте детали выше"
fi

