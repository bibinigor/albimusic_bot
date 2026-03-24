#!/usr/bin/env python3
"""
Тест для проверки всех исправлений из комплексного аудита.
Запускать на сервере: python3 test_audit_fixes.py
"""

import sys
import os
import json

sys.path.insert(0, '/root/albimusic-bot')

errors = []
passed = []

print("=" * 60)
print("ТЕСТ: Комплексный аудит бота - проверка исправлений")
print("=" * 60)

# =============================================
# ТЕСТ 1: Функции balance в main_with_payments.py
# =============================================
print("\n[1] Проверяем функции баланса...")
try:
    # Читаем файл и ищем функции
    with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
        content = f.read()

    # Проверяем что update_user_balance определена
    if 'def update_user_balance(user_id, delta):' in content:
        passed.append("✅ update_user_balance() определена")
    else:
        errors.append("❌ update_user_balance() НЕ НАЙДЕНА - NameError при вызове!")

    # Проверяем что get_balance_number определена
    if 'def get_balance_number(user_id):' in content:
        passed.append("✅ get_balance_number() определена")
    else:
        errors.append("❌ get_balance_number() НЕ НАЙДЕНА!")

    # Проверяем что нет get_user_balance в числовых сравнениях
    import re
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Ищем get_user_balance в сравнениях (кроме отображения)
        if 'get_user_balance' in line and ('< ' in line or '> ' in line or '<=' in line or '>=' in line or '== ' in line):
            errors.append(f"❌ Строка {i}: get_user_balance() используется в числовом сравнении: {line.strip()}")

    if not any('get_user_balance' in e and 'сравнении' in e for e in errors):
        passed.append("✅ get_user_balance() не используется в числовых сравнениях")

except Exception as e:
    errors.append(f"❌ Ошибка при проверке balance функций: {e}")

# =============================================
# ТЕСТ 2: MUSIC_STYLE_TRANSLATIONS в celery_tasks.py
# =============================================
print("\n[2] Проверяем MUSIC_STYLE_TRANSLATIONS...")
try:
    with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
        content = f.read()

    # Ищем проблемные английские ключи ВНУТРИ словаря MUSIC_STYLE_TRANSLATIONS
    # (не в API-параметрах, а именно в словаре переводов)
    # Вычленяем блок MUSIC_STYLE_TRANSLATIONS
    dict_start = content.find('MUSIC_STYLE_TRANSLATIONS = {')
    dict_end = content.find('\n}', dict_start) + 2
    translations_block = content[dict_start:dict_end] if dict_start >= 0 else ""

    bad_keys = ['"model": "V5"', '"styleWeight":', '"vocalGender":', '"weirdnessConstraint":', '"prompt": "prompt,', '"instrumental": "True"']
    found_bad = []
    for key in bad_keys:
        if key in translations_block:
            found_bad.append(key)

    if found_bad:
        errors.append(f"❌ Найдены плохие английские ключи в MUSIC_STYLE_TRANSLATIONS: {found_bad}")
    else:
        passed.append("✅ Английские мусорные ключи удалены из MUSIC_STYLE_TRANSLATIONS")

    # Проверяем что русские ключи на месте (жанр - Метал с одной л, не Металл)
    required_russian = ['"метал"', '"джаз"', '"блюз"', '"рок"', '"поп"']
    for key in required_russian:
        if key in translations_block:
            passed.append(f"✅ Русский ключ {key} присутствует")
        else:
            errors.append(f"❌ Русский ключ {key} НЕ НАЙДЕН в MUSIC_STYLE_TRANSLATIONS!")

except Exception as e:
    errors.append(f"❌ Ошибка при проверке celery_tasks.py: {e}")

# =============================================
# ТЕСТ 3: Cover custom_mode в celery_tasks.py
# =============================================
print("\n[3] Проверяем cover custom_mode...")
try:
    with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
        content = f.read()

    # Ищем старый неправильный custom_mode для covers
    if 'custom_mode=len(lyrics) > 500 if lyrics else False' in content:
        errors.append("❌ Старый custom_mode для cover: len(lyrics) > 500 - стиль не применяется для коротких текстов!")
    else:
        passed.append("✅ custom_mode для cover исправлен (bool(lyrics))")

except Exception as e:
    errors.append(f"❌ Ошибка при проверке cover custom_mode: {e}")

# =============================================
# ТЕСТ 4: Улучшенные дескрипторы жанров
# =============================================
print("\n[4] Проверяем дескрипторы жанров...")
try:
    with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
        content = f.read()

    # Проверяем rich descriptors для metal
    if 'heavy metal, distorted guitar' in content or 'distorted guitar' in content:
        passed.append("✅ Metal descriptor улучшен")
    else:
        errors.append("❌ Metal descriptor не улучшен - просто 'metal'")

    if 'boom bap' in content or 'hip-hop beat' in content:
        passed.append("✅ Hip-hop descriptor улучшен")
    else:
        errors.append("❌ Hip-hop descriptor не улучшен")

except Exception as e:
        errors.append(f"❌ Ошибка при проверке жанров: {e}")

# =============================================
# ТЕСТ 5: Monitor - двойной init_db_pool_sync
# =============================================
print("\n[5] Проверяем run_monitor_notify.py...")
try:
    with open('/root/albimusic-bot/run_monitor_notify.py', 'r') as f:
        content = f.read()

    # Считаем количество init_db_pool_sync() вызовов в monitor_generations
    # Ищем начало функции monitor_generations
    idx = content.find('async def monitor_generations():')
    if idx >= 0:
        # Следующие 500 символов после начала функции
        func_start = content[idx:idx+500]
        count = func_start.count('init_db_pool_sync()')
        if count > 1:
            errors.append(f"❌ monitor_generations() содержит {count} вызовов init_db_pool_sync() (должен быть 1)")
        else:
            passed.append(f"✅ monitor_generations() содержит ровно {count} вызов init_db_pool_sync()")
    else:
        errors.append("❌ monitor_generations() не найдена в run_monitor_notify.py")

except Exception as e:
    errors.append(f"❌ Ошибка при проверке monitor: {e}")

# =============================================
# ТЕСТ 6: Cover handler - нет конфликтующих callback
# =============================================
print("\n[6] Проверяем cover handlers в main_with_payments.py...")
try:
    with open('/root/albimusic-bot/main_with_payments.py', 'r') as f:
        content = f.read()

    # Ищем handlers для cover, проверяем что cover_genre_ исключены
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if "startswith('cover_')" in line and 'cover_genre_' not in line and '@dp.callback' in content.split('\n')[i-2] if i > 2 else False:
            errors.append(f"⚠️  Строка {i}: Возможный конфликт в cover handler: {line.strip()}")

    # Проверяем что exclusion есть
    if "not c.data.startswith('cover_genre_')" in content:
        passed.append("✅ cover_genre_ исключение добавлено в handlers")
    else:
        errors.append("❌ cover_genre_ exclusion НЕ НАЙДЕНА - возможен infinite loop!")

except Exception as e:
    errors.append(f"❌ Ошибка при проверке cover handlers: {e}")

# =============================================
# ТЕСТ 7: Подключение к БД
# =============================================
print("\n[7] Проверяем подключение к БД...")
try:
    from db_utils import execute_query_sync, init_db_pool_sync
    init_db_pool_sync()
    result = execute_query_sync("SELECT COUNT(*) FROM users")
    if result:
        passed.append(f"✅ БД подключена, пользователей: {result[0][0]}")
    else:
        errors.append("❌ БД подключена но нет данных")
except Exception as e:
    errors.append(f"❌ Ошибка подключения к БД: {e}")

# =============================================
# ТЕСТ 8: Проверка translate_style_to_english
# =============================================
print("\n[8] Проверяем translate_style_to_english...")
try:
    # Импортируем функцию напрямую
    import importlib.util
    spec = importlib.util.spec_from_file_location("celery_tasks", "/root/albimusic-bot/celery_tasks.py")
    module = importlib.util.load_from_spec = None

    # Читаем файл и ищем improvements dict внутри translate_style_to_english
    with open('/root/albimusic-bot/celery_tasks.py', 'r') as f:
        ct_content = f.read()

    # Вычленяем блок функции translate_style_to_english
    func_start = ct_content.find('def translate_style_to_english(')
    func_end = ct_content.find('\ndef ', func_start + 1)
    translate_func = ct_content[func_start:func_end] if func_start >= 0 else ""

    # Проверяем что в improvements нет английских мусорных ключей
    bad_in_translate = ['"model": "V5"', '"styleWeight":', '"vocalGender":', '"instrumental": "True"', '"weirdnessConstraint":']
    found_translate_bad = [k for k in bad_in_translate if k in translate_func]
    if found_translate_bad:
        errors.append(f"❌ В translate_style_to_english найдены мусорные ключи: {found_translate_bad}")
    else:
        passed.append("✅ translate_style_to_english не содержит мусорных английских ключей")

except Exception as e:
    errors.append(f"⚠️  Ошибка при проверке translate_style_to_english: {e}")

# =============================================
# ИТОГ
# =============================================
print("\n" + "=" * 60)
print("ИТОГ:")
print("=" * 60)
for p in passed:
    print(p)
print()
if errors:
    print("ОШИБКИ:")
    for e in errors:
        print(e)
    print(f"\n❌ {len(errors)} ошибок, {len(passed)} тестов прошло")
    sys.exit(1)
else:
    print(f"✅ ВСЕ {len(passed)} ТЕСТОВ ПРОШЛИ УСПЕШНО!")
    sys.exit(0)
