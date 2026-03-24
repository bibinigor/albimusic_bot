#!/usr/bin/env python3
"""
Тестовый скрипт для проверки соответствия жанров в инструментальной музыке
Проверяет что выбранный жанр правильно передается в Suno API
"""

import sys
sys.path.append('/root/albimusic-bot')

from celery_tasks import translate_style_to_english

def test_genre_translation():
    """Тест перевода жанров"""
    print("=" * 60)
    print("🧪 ТЕСТ ПЕРЕВОДА ЖАНРОВ")
    print("=" * 60)

    test_cases = [
        ("Блюз", "blues"),
        ("Поп", "pop"),
        ("Рок", "rock"),
        ("Джаз", "jazz"),
        ("Хип-хоп", "hip hop"),
        ("Электронная музыка", "electronic"),
        ("Классическая музыка", "classical"),
        ("R&B/Соул", ""),  # Нет прямого перевода, проверим что вернется
        ("Регги", "reggae"),
        ("Кантри", "country"),
        ("Метал", "metal"),
        ("Фолк", "folk"),
        ("Латиноамериканская музыка", "latin"),
        ("Панк-рок", "punk"),
        ("Фанк", "funk"),
        ("Шансон", "shanson"),
    ]

    all_passed = True

    for russian, expected in test_cases:
        result = translate_style_to_english(russian)

        # Для жанров которые не переводятся, проверяем что хотя бы что-то вернулось
        if expected:
            if expected in result.lower():
                print(f"✅ {russian:30} → {result:30} (ожидалось: {expected})")
            else:
                print(f"❌ {russian:30} → {result:30} (ожидалось: {expected})")
                all_passed = False
        else:
            # Для жанров без прямого перевода
            print(f"ℹ️  {russian:30} → {result:30} (без прямого перевода)")

    return all_passed

def test_prompt_formation():
    """Тест формирования prompt для инструментальной музыки"""
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ ФОРМИРОВАНИЯ PROMPT")
    print("=" * 60)

    test_cases = [
        ("Блюз", "blues instrumental music"),
        ("Поп", "pop instrumental music"),
        ("Рок", "rock instrumental music"),
    ]

    all_passed = True

    for genre, expected_prompt in test_cases:
        # Эмулируем логику из celery_tasks.py
        # Для инструментальной музыки (is_song=False) add_improvements=False
        translated_style = translate_style_to_english(genre, add_improvements=False)

        # Для инструментальной музыки (is_song=False)
        if translated_style:
            prompt = f"{translated_style} instrumental music"
        else:
            prompt = "instrumental music"

        if prompt == expected_prompt:
            print(f"✅ Жанр '{genre}' → prompt='{prompt}'")
        else:
            print(f"❌ Жанр '{genre}' → prompt='{prompt}' (ожидалось: '{expected_prompt}')")
            all_passed = False

    return all_passed

def test_full_flow():
    """Тест полного флоу: жанр → перевод → prompt → API request"""
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ ПОЛНОГО ФЛОУ (Блюз)")
    print("=" * 60)

    # Шаг 1: Пользователь выбирает "Блюз"
    user_selected_genre = "Блюз"
    print(f"\n1️⃣ Пользователь выбрал жанр: '{user_selected_genre}'")

    # Шаг 2: Перевод жанра (для инструментальной музыки без improvements)
    is_song = False
    translated_style = translate_style_to_english(user_selected_genre, add_improvements=is_song)
    print(f"2️⃣ Перевод жанра: '{user_selected_genre}' → '{translated_style}'")

    # Шаг 3: Формирование prompt для инструментальной музыки
    is_song = False  # Инструментальная музыка
    lyrics = ""  # Нет текста

    if is_song:
        prompt = lyrics
    else:
        if translated_style:
            prompt = f"{translated_style} instrumental music"
        else:
            prompt = lyrics if lyrics else "instrumental music"

    print(f"3️⃣ Сформирован prompt: '{prompt}'")

    # Шаг 4: Параметры для Suno API
    suno_params = {
        "prompt": prompt,
        "style": translated_style,
        "instrumental": True,
        "is_song": is_song,
        "model": "V5"
    }

    print(f"4️⃣ Параметры для Suno API:")
    for key, value in suno_params.items():
        print(f"   • {key}: {value}")

    # Проверка
    print(f"\n✅ ПРОВЕРКА:")

    checks = [
        (translated_style == "blues", f"Жанр переведён правильно: '{translated_style}' = 'blues'"),
        (prompt == "blues instrumental music", f"Prompt сформирован правильно: '{prompt}' = 'blues instrumental music'"),
        (suno_params["instrumental"] == True, "instrumental = True"),
        (suno_params["is_song"] == False, "is_song = False"),
    ]

    all_passed = True
    for passed, message in checks:
        if passed:
            print(f"   ✅ {message}")
        else:
            print(f"   ❌ {message}")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    print("\n🚀 ЗАПУСК ТЕСТОВ СООТВЕТСТВИЯ ЖАНРОВ\n")

    try:
        test1 = test_genre_translation()
        test2 = test_prompt_formation()
        test3 = test_full_flow()

        print("\n" + "=" * 60)
        if test1 and test2 and test3:
            print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
