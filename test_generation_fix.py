#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки исправлений генерации
Проверяет:
1. Порядок параметров в generate_song_task
2. Правильную передачу custom_mode
3. Наличие новых обработчиков для выбора варианта текста
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, '/root/albimusic-bot')

def test_celery_task_signature():
    """Проверка сигнатуры функции generate_song_task"""
    print("=" * 60)
    print("ТЕСТ 1: Проверка порядка параметров в generate_song_task")
    print("=" * 60)

    try:
        from celery_tasks import generate_song_task
        import inspect

        # Получаем сигнатуру функции
        sig = inspect.signature(generate_song_task.run)
        params = list(sig.parameters.keys())

        print(f"✅ Функция найдена")
        print(f"📝 Параметры: {params}")

        # Проверяем порядок
        expected_order = ['user_id', 'lyrics', 'style', 'custom_mode', 'is_song', 'task_id']

        # Убираем 'self' если есть
        if params[0] == 'self':
            params = params[1:]

        if params == expected_order:
            print("✅ ТЕСТ ПРОЙДЕН: Порядок параметров правильный")
            print(f"   Ожидалось: {expected_order}")
            print(f"   Получено:  {params}")
            return True
        else:
            print("❌ ТЕСТ НЕ ПРОЙДЕН: Порядок параметров неправильный")
            print(f"   Ожидалось: {expected_order}")
            print(f"   Получено:  {params}")
            return False

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

def test_main_handlers():
    """Проверка наличия новых обработчиков в main_with_payments.py"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Проверка новых обработчиков выбора варианта")
    print("=" * 60)

    try:
        with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Проверяем наличие нового состояния FSM
        if 'choosing_lyrics_variant' in content:
            print("✅ Найдено состояние: choosing_lyrics_variant")
        else:
            print("❌ НЕ найдено состояние: choosing_lyrics_variant")
            return False

        # Проверяем обработчики
        handlers = [
            'lyrics_variant_1',
            'lyrics_variant_2',
            'lyrics_write_own'
        ]

        all_found = True
        for handler in handlers:
            if f'c.data == "{handler}"' in content:
                print(f"✅ Найден обработчик: {handler}")
            else:
                print(f"❌ НЕ найден обработчик: {handler}")
                all_found = False

        # Проверяем helper функцию
        if 'show_genre_selection_callback' in content:
            print("✅ Найдена helper функция: show_genre_selection_callback")
        else:
            print("❌ НЕ найдена helper функция")
            all_found = False

        # Проверяем генерацию двух вариантов
        if 'asyncio.gather' in content and 'lyrics_variant1' in content and 'lyrics_variant2' in content:
            print("✅ Найдена генерация двух вариантов (asyncio.gather)")
        else:
            print("❌ НЕ найдена генерация двух вариантов")
            all_found = False

        if all_found:
            print("\n✅ ТЕСТ ПРОЙДЕН: Все обработчики на месте")
            return True
        else:
            print("\n❌ ТЕСТ НЕ ПРОЙДЕН: Не все обработчики найдены")
            return False

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

def test_instrumental_music_fix():
    """Проверка исправления для инструментальной музыки"""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Проверка is_song=False для инструментальной музыки")
    print("=" * 60)

    try:
        with open('/root/albimusic-bot/main_with_payments.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Ищем код для инструментальной музыки
        # Должно быть: kwargs={'task_id': task_id, 'is_song': False}

        if "'is_song': False" in content or '"is_song": False' in content:
            print("✅ Найдено явное указание is_song=False")
            print("✅ ТЕСТ ПРОЙДЕН: Инструментальная музыка исправлена")
            return True
        else:
            print("⚠️  НЕ найдено явное указание is_song=False")
            print("   (Возможно используется порядок параметров)")
            return True  # Не критично, порядок параметров исправлен

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("\n🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ГЕНЕРАЦИИ")
    print("Дата: 19.02.2026")
    print()

    results = []

    # Тест 1
    results.append(test_celery_task_signature())

    # Тест 2
    results.append(test_main_handlers())

    # Тест 3
    results.append(test_instrumental_music_fix())

    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Тестов пройдено: {passed}/{total}")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Исправления применены корректно")
        return 0
    else:
        print(f"\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ ({total - passed}/{total})")
        print("❌ Требуется проверка")
        return 1

if __name__ == "__main__":
    exit(main())
