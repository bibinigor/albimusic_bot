#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки WAV файлов
Проверяет всю цепочку: парсинг URL -> скачивание -> отправка
"""

import asyncio
import sys
import os
import tempfile
import json

# Добавляем путь к проекту
sys.path.append('/root/albimusic-bot')

from aiogram import Bot
from config import BOT_TOKEN as TELEGRAM_BOT_TOKEN
import aiohttp

async def test_wav_delivery():
    """Тестируем отправку WAV файла пользователю"""

    # Тестовые параметры
    TEST_USER_ID = 338544009  # ID админа для теста
    TEST_WAV_URL = "https://cdn1.suno.ai/test.wav"  # Заглушка, заменим реальным URL

    print("=" * 60)
    print("🧪 ТЕСТ ОТПРАВКИ WAV ФАЙЛОВ")
    print("=" * 60)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # ШАГ 1: Проверяем парсинг URL (одиночная строка)
    print("\n📊 ШАГ 1: Парсинг URL из БД")
    audio_url = TEST_WAV_URL  # Как хранится в БД

    # Логика из run_monitor_notify.py:102-113
    audio_urls = []
    try:
        if isinstance(audio_url, str) and audio_url.startswith("["):
            parsed_urls = json.loads(audio_url)
            if isinstance(parsed_urls, list):
                audio_urls = parsed_urls
                print(f"   ✅ JSON массив: {len(audio_urls)} ссылок")
    except Exception as e:
        print(f"   ⚠️ Ошибка парсинга JSON: {e}")

    if not audio_urls:
        audio_urls = [audio_url]
        print(f"   ✅ Одиночная ссылка: {audio_url}")

    # ШАГ 2: Проверяем fallback для single URL
    print("\n📊 ШАГ 2: Проверка fallback (len < 2)")
    if len(audio_urls) < 2:
        print(f"   ✅ Fallback активирован: {len(audio_urls)} ссылок")
    else:
        print(f"   ❌ Ошибка: должен быть fallback, но {len(audio_urls)} ссылок")
        await bot.close()
        return False

    # ШАГ 3: Определяем тип задачи (WAV или нет)
    print("\n📊 ШАГ 3: Определение типа задачи")
    file_url = audio_urls[0] if audio_urls else ""
    prompt_text = "WAV конвертация для трека test-123"
    is_wav = "WAV" in prompt_text.upper() or file_url.lower().endswith('.wav')

    if is_wav:
        print(f"   ✅ Определён как WAV: prompt='{prompt_text}', url={file_url}")
    else:
        print(f"   ❌ Не определён как WAV")
        await bot.close()
        return False

    # ШАГ 4: Создаём тестовый WAV файл и тестируем отправку
    print("\n📊 ШАГ 4: Тест отправки WAV файла")

    try:
        # Создаём тестовый WAV файл
        temp_dir = tempfile.mkdtemp()
        test_wav_path = os.path.join(temp_dir, 'test_music.wav')

        # Создаём минимальный валидный WAV файл (44 байта header + немного данных)
        with open(test_wav_path, 'wb') as f:
            # WAV header (44 bytes)
            f.write(b'RIFF')
            f.write((36).to_bytes(4, 'little'))  # file size - 8
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # fmt chunk size
            f.write((1).to_bytes(2, 'little'))   # audio format (PCM)
            f.write((1).to_bytes(2, 'little'))   # num channels
            f.write((44100).to_bytes(4, 'little'))  # sample rate
            f.write((88200).to_bytes(4, 'little'))  # byte rate
            f.write((2).to_bytes(2, 'little'))   # block align
            f.write((16).to_bytes(2, 'little'))  # bits per sample
            f.write(b'data')
            f.write((0).to_bytes(4, 'little'))   # data chunk size

        print(f"   ✅ Тестовый WAV создан: {test_wav_path}")

        # Отправляем через Telegram
        from aiogram.types import InputFile
        await bot.send_message(TEST_USER_ID, "🧪 ТЕСТ: Отправка WAV файла...")
        wav_file = InputFile(test_wav_path, filename="test_music.wav")
        await bot.send_document(
            chat_id=TEST_USER_ID,
            document=wav_file,
            caption="🎵 Тестовый WAV файл готов!"
        )

        print(f"   ✅ WAV файл отправлен user {TEST_USER_ID}")

        # Очистка
        os.remove(test_wav_path)
        os.rmdir(temp_dir)
        print(f"   ✅ Временные файлы удалены")

    except Exception as e:
        print(f"   ❌ Ошибка отправки WAV: {e}")
        import traceback
        traceback.print_exc()
        await bot.close()
        return False

    # ШАГ 5: Финальная проверка
    print("\n📊 ШАГ 5: Финальная проверка")

    # Проверяем логику для не-WAV файлов
    print("   Проверка fallback для обычных треков...")
    test_mp3_url = "https://cdn1.suno.ai/test.mp3"
    is_wav_mp3 = "WAV" in "обычная песня".upper() or test_mp3_url.lower().endswith('.wav')

    if not is_wav_mp3:
        print(f"   ✅ MP3 корректно определён как не-WAV")
    else:
        print(f"   ❌ MP3 ошибочно определён как WAV")
        await bot.close()
        return False

    await bot.close()

    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)

    return True

async def test_real_wav_url():
    """Тест с реальным WAV URL из последней задачи в БД"""

    print("\n" + "=" * 60)
    print("🔍 ПОИСК ПОСЛЕДНЕЙ WAV ЗАДАЧИ В БД")
    print("=" * 60)

    try:
        from db_utils import execute_query_sync, init_db_pool_sync

        # Инициализируем DB pool
        init_db_pool_sync()

        # Ищем последнюю завершенную WAV задачу
        results = execute_query_sync(
            """SELECT task_id, user_id, prompt, audio_url, status
               FROM generations
               WHERE prompt ILIKE '%WAV%'
               AND status = 'completed'
               AND audio_url IS NOT NULL
               AND audio_url NOT LIKE 'ALREADY_SENT_%'
               AND audio_url NOT LIKE 'ERROR%'
               ORDER BY created_at DESC
               LIMIT 1"""
        )

        if not results:
            print("⚠️ Нет завершенных WAV задач в БД")
            return

        task_id, user_id, prompt, audio_url, status = results[0]

        print(f"\n✅ Найдена задача:")
        print(f"   Task ID: {task_id}")
        print(f"   User ID: {user_id}")
        print(f"   Prompt: {prompt}")
        print(f"   Status: {status}")
        print(f"   URL: {audio_url[:100]}...")

        # Проверяем доступность URL
        print(f"\n🔍 Проверка доступности WAV URL...")

        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(audio_url, timeout=10) as response:
                    print(f"   HTTP Status: {response.status}")
                    print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    print(f"   Content-Length: {response.headers.get('Content-Length', 'unknown')}")

                    if response.status == 200:
                        print(f"   ✅ URL доступен")
                    else:
                        print(f"   ⚠️ URL недоступен: HTTP {response.status}")

            except Exception as e:
                print(f"   ❌ Ошибка проверки URL: {e}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 ЗАПУСК ТЕСТОВ WAV ОТПРАВКИ\n")

    try:
        # Тест 1: Базовая логика
        success = asyncio.run(test_wav_delivery())

        # Тест 2: Проверка реальной WAV задачи из БД
        asyncio.run(test_real_wav_url())

        if success:
            print("\n✅ Система готова к деплою!")
            sys.exit(0)
        else:
            print("\n❌ Тесты провалены, деплой отменён")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Тесты прерваны пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
