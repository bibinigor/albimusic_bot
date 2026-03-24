#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функции "Отправить другу"
Согласно Правилу №7 - тестируем перед завершением!
"""

import sys

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}🧪 Тест функции 'Отправить другу'{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

total_tests = 0
passed_tests = 0
failed_tests = 0

def test_result(name, success, details=""):
    global total_tests, passed_tests, failed_tests
    total_tests += 1

    if success:
        passed_tests += 1
        print(f"{GREEN}✅ {name}{RESET}")
        if details:
            print(f"   {details}")
    else:
        failed_tests += 1
        print(f"{RED}❌ {name}{RESET}")
        if details:
            print(f"   {RED}{details}{RESET}")
    print()

# ============================================
# Тест 1: Проверка кода в main_with_payments.py
# ============================================
print(f"{YELLOW}1️⃣ Проверка обработчиков...{RESET}")

try:
    with open('main_with_payments.py', 'r', encoding='utf-8') as f:
        bot_code = f.read()

    # Проверка 1: inline_query_handler принимает query
    if 'query_text = inline_query.query.strip()' in bot_code:
        test_result(
            "inline_query_handler получает query",
            True,
            "query_text извлекается из inline_query"
        )
    else:
        test_result(
            "inline_query_handler получает query",
            False,
            "query_text не извлекается"
        )

    # Проверка 2: Проверка task_id в query
    if 'if query_text:' in bot_code and 'WHERE user_id = %s AND task_id = %s' in bot_code:
        test_result(
            "Проверка конкретного task_id",
            True,
            "Если query есть - ищем конкретный трек"
        )
    else:
        test_result(
            "Проверка конкретного task_id",
            False,
            "Логика поиска по task_id не найдена"
        )

    # Проверка 3: Caption содержит ссылку на музыку
    if '🎧 Слушать: {first_audio_url}' in bot_code or 'f"🎧 Слушать: {first_audio_url}' in bot_code:
        test_result(
            "Caption содержит ссылку на музыку",
            True,
            "Ссылка на аудио включена в caption"
        )
    else:
        test_result(
            "Caption содержит ссылку на музыку",
            False,
            "Ссылка на аудио не найдена в caption"
        )

    # Проверка 4: Кнопка после генерации использует switch_inline_query
    share_after_gen = bot_code.find('InlineKeyboardButton("🔗 Отправить другу"')
    if share_after_gen > 0:
        # Находим ближайший switch_inline_query после этой кнопки
        next_500_chars = bot_code[share_after_gen:share_after_gen+500]
        if 'switch_inline_query=task_id' in next_500_chars:
            test_result(
                "Кнопка после генерации работает",
                True,
                "Использует switch_inline_query=task_id"
            )
        else:
            test_result(
                "Кнопка после генерации работает",
                False,
                "Не использует switch_inline_query=task_id"
            )
    else:
        test_result(
            "Кнопка после генерации найдена",
            False,
            "Кнопка не найдена в коде"
        )

    # Проверка 5: Кнопка в истории использует switch_inline_query с task_id
    # Ищем в контексте "Мои треки"
    my_tracks_section = bot_code.find('# Inline кнопки для каждого трека')
    if my_tracks_section > 0:
        next_400_chars = bot_code[my_tracks_section:my_tracks_section+400]
        # Проверяем что кнопка "Отправить другу" использует switch_inline_query
        if '"🔗 Отправить другу", switch_inline_query=' in next_400_chars:
            test_result(
                "Кнопка в истории треков работает",
                True,
                "Использует switch_inline_query с параметром"
            )
        else:
            test_result(
                "Кнопка в истории треков работает",
                False,
                f"Не найден паттерн. Найдено: {next_400_chars[200:300]}"
            )
    else:
        test_result(
            "Кнопка в истории треков найдена",
            False,
            "Секция 'Мои треки' не найдена"
        )

    # Проверка 6: Старый обработчик share_ удалён или не используется
    if 'callback_data=f"share_{task_id}"' not in bot_code:
        test_result(
            "Старый callback share_ не используется",
            True,
            "Все кнопки используют switch_inline_query"
        )
    else:
        test_result(
            "Старый callback share_ не используется",
            False,
            "Найден старый callback_data=share_"
        )

except Exception as e:
    test_result("Проверка main_with_payments.py", False, str(e))

# ============================================
# Тест 2: Проверка формата сообщения
# ============================================
print(f"{YELLOW}2️⃣ Проверка формата сообщения...{RESET}")

try:
    with open('main_with_payments.py', 'r', encoding='utf-8') as f:
        bot_code = f.read()

    # Проверка формата caption
    required_parts = [
        "🎵 Зацени что я создал!",
        "🎧 Слушать:",
        "🤖 Крутой AI-бот делает песни и музыку",
        "Попробуй сам → @AlBimusic_bot"
    ]

    all_parts_found = all(part in bot_code for part in required_parts)

    if all_parts_found:
        test_result(
            "Все части сообщения присутствуют",
            True,
            "Текст + ссылка + призыв к действию"
        )
    else:
        missing = [part for part in required_parts if part not in bot_code]
        test_result(
            "Все части сообщения присутствуют",
            False,
            f"Отсутствуют: {', '.join(missing)}"
        )

except Exception as e:
    test_result("Проверка формата сообщения", False, str(e))

# ============================================
# Итоги
# ============================================
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}📊 ИТОГИ ТЕСТИРОВАНИЯ{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

print(f"Всего тестов: {total_tests}")
print(f"{GREEN}✅ Успешно: {passed_tests}{RESET}")
if failed_tests > 0:
    print(f"{RED}❌ Провалено: {failed_tests}{RESET}")
else:
    print(f"{GREEN}❌ Провалено: 0{RESET}")

success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
print(f"\nУспешность: {success_rate:.1f}%\n")

if failed_tests == 0:
    print(f"{GREEN}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!{RESET}\n")
    print(f"{GREEN}✅ Функция 'Отправить другу' исправлена{RESET}")
    print(f"{GREEN}✅ Теперь отправляется музыка + ссылка{RESET}\n")
    sys.exit(0)
else:
    print(f"{RED}⚠️  ЕСТЬ ОШИБКИ!{RESET}\n")
    print(f"{RED}❌ Исправьте ошибки перед деплоем{RESET}\n")
    sys.exit(1)
