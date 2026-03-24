#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ ПЕСЕН                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"

echo ""
echo "Запуск мониторинга логов..."
echo "Откройте бот и выполните:"
echo "  1. /song"
echo "  2. Введите стиль: pop"
echo "  3. Введите текст песни"
echo "  4. Выберите режим"
echo ""
echo "Ожидаемые логи:"
echo "  ✅ Detected SONG generation (lyrics present: XXX chars)"
echo "  ✅ Starting SONG generation"
echo "  ✅ Song generation task started: [task_id]"
echo ""
echo "Нажмите Ctrl+C для выхода"
echo "════════════════════════════════════════════════════════════"

sudo journalctl -u albimusic-bot -f | grep --color=always -E "generation_type|Detected|SONG|lyrics present|Song generation task"

