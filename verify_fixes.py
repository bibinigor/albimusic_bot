#!/usr/bin/env python3
"""
СКРИПТ ПРОВЕРКИ ИСПРАВЛЕНИЙ
"""

import re
import sys

CELERY_FILE = "/root/albimusic-bot/celery_tasks.py"

def check(name, condition, success_msg, fail_msg):
    """Проверка условия"""
    if condition:
        print(f"✅ {name}: {success_msg}")
        return True
    else:
        print(f"❌ {name}: {fail_msg}")
        return False

def main():
    print("\n" + "═" * 80)
    print("  ПРОВЕРКА ИСПРАВЛЕНИЙ AlBi-music Bot")
    print("═" * 80 + "\n")
    
    with open(CELERY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # 1. Функция validate_audio_url определена
    checks.append(check(
        "Функция validate_audio_url",
        'def validate_audio_url(url, request_id):' in content,
        "Определена",
        "НЕ найдена"
    ))
    
    # 2. Функция validate_audio_url вызывается
    checks.append(check(
        "Вызов validate_audio_url",
        'validate_audio_url(audio_url, request_id)' in content,
        "Присутствует",
        "НЕ найден"
    ))
    
    # 3. Только один MUSIC_STYLE_TRANSLATIONS
    count = len(re.findall(r'MUSIC_STYLE_TRANSLATIONS\s*=\s*{', content))
    checks.append(check(
        "MUSIC_STYLE_TRANSLATIONS",
        count == 1,
        f"Единственный словарь (без дубликатов)",
        f"Найдено {count} определений"
    ))
    
    # 4. Защита от race conditions
    checks.append(check(
        "Race condition защита",
        "WHERE generations.status NOT IN ('completed', 'error')" in content,
        "WHERE условие присутствует",
        "WHERE условие НЕ найдено"
    ))
    
    # 5. Использование translate_style_to_english
    checks.append(check(
        "Перевод стиля",
        'style = translate_style_to_english(style)' in content,
        "Вызов присутствует",
        "Вызов НЕ найден"
    ))
    
    # 6. Синтаксис Python
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', CELERY_FILE], capture_output=True)
    checks.append(check(
        "Синтаксис Python",
        result.returncode == 0,
        "Корректный",
        "ОШИБКИ"
    ))
    
    print("\n" + "═" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ({passed}/{total})")
        print("═" * 80 + "\n")
        return 0
    else:
        print(f"⚠️  ПРОЙДЕНО {passed}/{total} ПРОВЕРОК")
        print("═" * 80 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
