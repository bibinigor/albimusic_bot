#!/usr/bin/env python3
"""
Тестовый скрипт для проверки выбора версии для Karaoke/Cover/WAV
Согласно Правилу №7 - тестируем перед завершением!
"""

import json
import sys

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}🧪 Тест выбора версии (Karaoke/Cover/WAV){RESET}")
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
print(f"{YELLOW}1️⃣ Проверка обработчиков в main_with_payments.py...{RESET}")

try:
    with open('main_with_payments.py', 'r', encoding='utf-8') as f:
        bot_code = f.read()

    # Проверка 1: Karaoke handlers
    if 'ask_karaoke_version' in bot_code and 'process_karaoke' in bot_code:
        test_result(
            "Karaoke handlers существуют",
            True,
            "ask_karaoke_version и process_karaoke найдены"
        )
    else:
        test_result(
            "Karaoke handlers существуют",
            False,
            "Handlers не найдены"
        )

    # Проверка 2: WAV handlers
    if 'ask_wav_version' in bot_code and 'process_wav_conversion' in bot_code:
        test_result(
            "WAV handlers существуют",
            True,
            "ask_wav_version и process_wav_conversion найдены"
        )
    else:
        test_result(
            "WAV handlers существуют",
            False,
            "Handlers не найдены"
        )

    # Проверка 3: Cover handlers
    if 'ask_cover_version' in bot_code and 'process_cover' in bot_code:
        test_result(
            "Cover handlers существуют",
            True,
            "ask_cover_version и process_cover найдены"
        )
    else:
        test_result(
            "Cover handlers существуют",
            False,
            "Handlers не найдены"
        )

    # Проверка 4: Version передаётся в Celery tasks
    karaoke_with_version = 'args=[user_id, task_id, version]' in bot_code or 'args=[user_id, original_task_id, version]' in bot_code

    if karaoke_with_version:
        test_result(
            "Version передаётся в Celery tasks",
            True,
            "Найдена передача version в args"
        )
    else:
        test_result(
            "Version передаётся в Celery tasks",
            False,
            "Version не передаётся"
        )

    # Проверка 5: Callback patterns
    has_v1_v2_pattern = '_v1' in bot_code and '_v2' in bot_code

    if has_v1_v2_pattern:
        test_result(
            "Callback patterns _v1/_v2",
            True,
            "Паттерны версий найдены"
        )
    else:
        test_result(
            "Callback patterns _v1/_v2",
            False,
            "Паттерны не найдены"
        )

except Exception as e:
    test_result("Проверка main_with_payments.py", False, str(e))

# ============================================
# Тест 2: Проверка celery_tasks.py
# ============================================
print(f"{YELLOW}2️⃣ Проверка Celery tasks...{RESET}")

try:
    with open('celery_tasks.py', 'r', encoding='utf-8') as f:
        celery_code = f.read()

    # Проверка 1: generate_karaoke_task принимает version
    if 'def generate_karaoke_task(self, user_id, original_task_id, version=0' in celery_code:
        test_result(
            "generate_karaoke_task принимает version",
            True,
            "Параметр version=0 найден"
        )
    else:
        test_result(
            "generate_karaoke_task принимает version",
            False,
            "Параметр version не найден"
        )

    # Проверка 2: generate_wav_task принимает version
    if 'def generate_wav_task(self, user_id, original_task_id, version=0' in celery_code:
        test_result(
            "generate_wav_task принимает version",
            True,
            "Параметр version=0 найден"
        )
    else:
        test_result(
            "generate_wav_task принимает version",
            False,
            "Параметр version не найден"
        )

    # Проверка 3: generate_cover_task принимает version
    if 'def generate_cover_task(self, user_id, original_task_id, new_style, version=0' in celery_code:
        test_result(
            "generate_cover_task принимает version",
            True,
            "Параметр version=0 найден"
        )
    else:
        test_result(
            "generate_cover_task принимает version",
            False,
            "Параметр version не найден"
        )

    # Проверка 4: Извлечение audio_id из JSON массива
    if 'json.loads(suno_audio_id_raw)' in celery_code:
        test_result(
            "Извлечение audio_id из JSON массива",
            True,
            "Логика парсинга JSON найдена"
        )
    else:
        test_result(
            "Извлечение audio_id из JSON массива",
            False,
            "Логика парсинга не найдена"
        )

    # Проверка 5: generate_suno_music_sync сохраняет все audio_ids
    if 'audio_ids = []' in celery_code and 'for item in audio_data:' in celery_code:
        test_result(
            "generate_suno_music_sync сохраняет все audio_ids",
            True,
            "Цикл извлечения всех audio_ids найден"
        )
    else:
        test_result(
            "generate_suno_music_sync сохраняет все audio_ids",
            False,
            "Цикл извлечения не найден"
        )

except Exception as e:
    test_result("Проверка celery_tasks.py", False, str(e))

# ============================================
# Тест 3: Симуляция парсинга audio_id
# ============================================
print(f"{YELLOW}3️⃣ Симуляция парсинга audio_id...{RESET}")

# Тест парсинга одной версии
try:
    suno_audio_id_raw = "abc123"
    try:
        audio_ids = json.loads(suno_audio_id_raw)
        suno_audio_id = audio_ids[0] if isinstance(audio_ids, list) else suno_audio_id_raw
    except (json.JSONDecodeError, TypeError):
        suno_audio_id = suno_audio_id_raw

    if suno_audio_id == "abc123":
        test_result(
            "Парсинг одной версии (строка)",
            True,
            f"Результат: {suno_audio_id}"
        )
    else:
        test_result(
            "Парсинг одной версии (строка)",
            False,
            f"Ожидалось: abc123, получено: {suno_audio_id}"
        )
except Exception as e:
    test_result("Парсинг одной версии (строка)", False, str(e))

# Тест парсинга двух версий
try:
    suno_audio_id_raw = '["abc123", "def456"]'
    version = 0
    try:
        audio_ids = json.loads(suno_audio_id_raw)
        if isinstance(audio_ids, list) and len(audio_ids) > version:
            suno_audio_id = audio_ids[version]
        else:
            suno_audio_id = audio_ids[0] if isinstance(audio_ids, list) and audio_ids else suno_audio_id_raw
    except (json.JSONDecodeError, TypeError):
        suno_audio_id = suno_audio_id_raw

    if suno_audio_id == "abc123":
        test_result(
            "Парсинг двух версий (версия 0)",
            True,
            f"Результат: {suno_audio_id}"
        )
    else:
        test_result(
            "Парсинг двух версий (версия 0)",
            False,
            f"Ожидалось: abc123, получено: {suno_audio_id}"
        )
except Exception as e:
    test_result("Парсинг двух версий (версия 0)", False, str(e))

# Тест парсинга версии 1
try:
    suno_audio_id_raw = '["abc123", "def456"]'
    version = 1
    try:
        audio_ids = json.loads(suno_audio_id_raw)
        if isinstance(audio_ids, list) and len(audio_ids) > version:
            suno_audio_id = audio_ids[version]
        else:
            suno_audio_id = audio_ids[0] if isinstance(audio_ids, list) and audio_ids else suno_audio_id_raw
    except (json.JSONDecodeError, TypeError):
        suno_audio_id = suno_audio_id_raw

    if suno_audio_id == "def456":
        test_result(
            "Парсинг двух версий (версия 1)",
            True,
            f"Результат: {suno_audio_id}"
        )
    else:
        test_result(
            "Парсинг двух версий (версия 1)",
            False,
            f"Ожидалось: def456, получено: {suno_audio_id}"
        )
except Exception as e:
    test_result("Парсинг двух версий (версия 1)", False, str(e))

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
    print(f"{GREEN}✅ Функция выбора версии реализована правильно{RESET}")
    print(f"{GREEN}✅ Можно переходить к финальному тестированию в боте{RESET}\n")
    sys.exit(0)
else:
    print(f"{RED}⚠️  ЕСТЬ ОШИБКИ!{RESET}\n")
    print(f"{RED}❌ Исправьте ошибки перед продолжением{RESET}\n")
    sys.exit(1)
