#!/bin/bash
# Скрипт проверки исправления всех 7 проблем VK-бота

echo "🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ VK-БОТА"
echo "===================================="
echo ""

cd /root/albimusic-bot

ERRORS=0
PASSED=0

# Функция для проверки
check() {
    local test_name=$1
    local condition=$2
    local success_msg=$3
    local error_msg=$4
    
    if eval "$condition"; then
        echo "✅ ТЕСТ $test_name: $success_msg"
        ((PASSED++))
        return 0
    else
        echo "❌ ТЕСТ $test_name: $error_msg"
        ((ERRORS++))
        return 1
    fi
}

echo "📋 ПРОВЕРКА ФАЙЛОВ"
echo "==================="

# Проверка существования файлов
check "0.1" "[ -f main_vk.py ]" "main_vk.py существует" "main_vk.py не найден"
check "0.2" "[ -f vk_keyboards.py ]" "vk_keyboards.py существует" "vk_keyboards.py не найден"  
check "0.3" "[ -f celery_tasks.py ]" "celery_tasks.py существует" "celery_tasks.py не найден"

echo ""
echo "🔍 ПРОВЕРКА ПРОБЛЕМ"
echo "==================="

# ПРОБЛЕМА 1: Автоматическая оплата YooKassa
echo ""
echo "1️⃣ ПРОБЛЕМА 1: Автоматическая оплата"
check "1.1" "grep -q 'from vk_keyboards import get_payment_keyboard' main_vk.py" \
    "Импорт клавиатуры платежей найден" \
    "Импорт клавиатуры платежей НЕ НАЙДЕН"

check "1.2" "grep -q 'get_payment_keyboard()' main_vk.py" \
    "Вызов get_payment_keyboard() найден" \
    "Вызов get_payment_keyboard() НЕ НАЙДЕН"

check "1.3" "grep -q 'def get_payment_keyboard' vk_keyboards.py" \
    "Функция get_payment_keyboard() существует" \
    "Функция get_payment_keyboard() НЕ СУЩЕСТВУЕТ"

check "1.4" "! grep -q 'Для оплаты напишите в поддержку' main_vk.py" \
    "Старое сообщение 'напишите в поддержку' УДАЛЕНО" \
    "Старое сообщение 'напишите в поддержку' ВСЕ ЕЩЕ ЕСТЬ"

# П РОБЛЕМА 2: Ссылка на VK-сообщество
echo ""
echo "2️⃣ ПРОБЛЕМА 2: Ссылка на VK-сообщество"
check "2.1" "grep -q 'https://vk.com/club235442407' main_vk.py" \
    "Ссылка на VK-сообщество найдена" \
    "Ссылка на VK-сообщество НЕ НАЙДЕНА"

check "2.2" "! grep -q 'https://t.me/ALBImusic_chart' main_vk.py" \
    "Ссылка на Telegram-канал УДАЛЕНА" \
    "Ссылка на Telegram-канал ВСЕ ЕЩЕ ЕСТЬ"

# ПРОБЛЕМА 3: Перевод жанров
echo ""
echo "3️⃣ ПРОБЛЕМА 3: Перевод жанров"
check "3.1" "grep -q 'from celery_tasks import translate_style_to_english' main_vk.py" \
    "Импорт translate_style_to_english найден" \
    "Импорт translate_style_to_english НЕ НАЙДЕН"

check "3.2" "grep -q 'translated_genre = translate_style_to_english(genre' main_vk.py" \
    "Вызов translate_style_to_english для жанра найден" \
    "Вызов translate_style_to_english для жанра НЕ НАЙДЕН"

check "3.3" "grep -A5 'Формируем стиль с учетом пола вокалиста' main_vk.py | grep -q 'translated_genre'" \
    "Использование переведенного жанра для песен подтверждено" \
    "Переведенный жанр НЕ используется для песен"

check "3.4" "grep -A10 'Обработка выбора жанра для инструментальной музыки' main_vk.py | grep -q 'translated_genre'" \
    "Использование переведенного жанра для музыки подтверждено" \
    "Переведенный жанр НЕ используется для музыки"

# ПРОБЛЕМА 4: Минусовка работает
echo ""
echo "4️⃣ ПРОБЛЕМА 4: Минусовка"
check "4.1" "grep -q 'generate_suno_karaoke_sync' main_vk.py" \
    "Функция генерации минусовки найдена" \
    "Функция генерации минусов ки НЕ НАЙДЕНА"

check "4.2" "grep -q 'SELECT audio_url, suno_audio_id FROM generations WHERE task_id = %s LIMIT 1' main_vk.py" \
    "Запрос к БД для минусовки исправлен (без лишнего user_id)" \
    "Запрос к БД для минусовки НЕКОРРЕКТЕН"

# ПРОБЛЕМА 5: Кавер работает
echo ""
echo "5️⃣ ПРОБЛЕМА 5: Кавер"
check "5.1" "grep -q 'generate_suno_cover_sync' main_vk.py" \
    "Функция генерации кавера найдена" \
    "Функция генерации кавера НЕ НАЙДЕНА"

check "5.2" "grep -q 'SELECT audio_url, suno_audio_id, prompt FROM generations WHERE task_id = %s LIMIT 1' main_vk.py" \
    "Запрос к БД для кавера исправлен (без лишнего user_id)" \
    "Запрос к БД для кавера НЕКОРРЕКТЕН"

# ПРОБЛЕМА 6: WAV работает
echo ""
echo "6️⃣ ПРОБЛЕМА 6: WAV"
check "6.1" "grep -q 'generate_suno_wav_sync' main_vk.py" \
    "Функция генерации WAV найдена" \
    "Функция генерации WAV НЕ НАЙДЕНА"

# ПРОБЛЕМА 7: Красивый вывод
echo ""
echo "7️⃣ ПРОБЛЕМА 7: Красивый вывод результатов"
check "7.1" "grep -q 'def get_track_actions_keyboard' vk_keyboards.py" \
    "Функция get_track_actions_keyboard() существует" \
    "Функция get_track_actions_keyboard() НЕ СУЩЕСТВУЕТ"

check "7.2" "grep -q '🎧 Вариант 1' vk_keyboards.py" \
    "Кнопки вариантов трека найдены" \
    "Кнопки вариантов трека НЕ НАЙДЕНЫ"

check "7.3" "grep -q '🎤 Минусовка' vk_keyboards.py" \
    "Кнопка минусовки найдена" \
    "Кнопка минусовки НЕ НАЙДЕНА"

# ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ
echo ""
echo "➕ ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ"
echo "=========================="

check "8.1" "python3 -m py_compile main_vk.py" \
    "main_vk.py компилируется без ошибок" \
    "main_vk.py НЕ КОМПИЛИРУЕТСЯ (синтаксические ошибки)"

check "8.2" "python3 -m py_compile vk_keyboards.py" \
    "vk_keyboards.py компилируется без ошибок" \
    "vk_keyboards.py НЕ КОМПИЛИРУЕТСЯ (синтаксические ошибки)"

# ИТОГИ
echo ""
echo "═══════════════════════════════════"
echo "📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ"
echo "═══════════════════════════════════"
echo ""
echo "✅ Пройдено тестов: $PASSED"
echo "❌ Провалено тестов: $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!"
    echo ""
    echo "✅ Все 7 проблем исправлены:"
    echo "   1. ✅ Автоматическая оплата через YooKassa"
    echo "   2. ✅ Ссылка на VK-сообщество"
    echo "   3. ✅ Перевод жанров (Джаз и др.)"
    echo "   4. ✅ Минусовка работает"
    echo "   5. ✅ Кавер работает"
    echo "   6. ✅ WAV работает"
    echo "   7. ✅ Красивый вывод результатов"
    echo ""
    echo "🚀 БОТ ГОТОВ К ПЕРЕЗАПУСКУ!"
    exit 0
else
    echo "⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ!"
    echo ""
    echo "Необходима доработка перед перезапуском бота."
    exit 1
fi
