#!/usr/bin/env python3
"""
Скрипт для исправления получения 2 ссылок от Suno API
Автоматически создает бэкап и вносит изменения
"""
import os
import shutil
from datetime import datetime

def create_backup(file_path):
    """Создает бэкап файла"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"/root/albimusic-bot/backups_2links_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Бэкап создан: {backup_path}")
    return backup_dir

def fix_celery_tasks():
    """Исправляет получение 2 ссылок в celery_tasks.py"""
    file_path = "/root/albimusic-bot/celery_tasks.py"

    print("🔧 Исправление celery_tasks.py...")

    # Создаем бэкап
    backup_dir = create_backup(file_path)

    # Читаем файл
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Старый код (строки 459-463)
    old_code = """                        if audio_data:
                            audio_url = audio_data[0].get('audioUrl')
                            logger.info(f"[{request_id}] ✅ SUNO GENERATION COMPLETED:")
                            logger.info(f"[{request_id}]    • Audio URL: {audio_url}")
                            logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")
                            return audio_url"""

    # Новый код - получаем ВСЕ ссылки
    new_code = """                        if audio_data:
                            # Получаем ВСЕ ссылки из массива sunoData
                            audio_urls = [item.get('audioUrl') for item in audio_data if item.get('audioUrl')]

                            # Логируем количество полученных ссылок
                            logger.info(f"[{request_id}] ✅ SUNO GENERATION COMPLETED:")
                            logger.info(f"[{request_id}]    • Found {len(audio_urls)} audio URLs")
                            for idx, url in enumerate(audio_urls, 1):
                                logger.info(f"[{request_id}]    • Version {idx}: {url}")
                            logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")

                            # Если несколько ссылок - сохраняем как JSON массив
                            # Если одна ссылка - сохраняем как строку (обратная совместимость)
                            if len(audio_urls) > 1:
                                audio_url = json.dumps(audio_urls)
                                logger.info(f"[{request_id}]    • Saved as JSON array: {audio_url}")
                            elif len(audio_urls) == 1:
                                audio_url = audio_urls[0]
                                logger.info(f"[{request_id}]    • Saved as single URL")
                            else:
                                logger.error(f"[{request_id}]    • No audio URLs found!")
                                return None

                            return audio_url"""

    # Проверяем что старый код есть в файле
    if old_code not in content:
        print("❌ ОШИБКА: Старый код не найден в файле!")
        print("Возможно, файл уже был изменен или структура кода отличается.")
        return False

    # Заменяем код
    new_content = content.replace(old_code, new_code)

    # Проверяем что замена произошла
    if new_content == content:
        print("❌ ОШИБКА: Замена не произошла!")
        return False

    # Сохраняем изменения
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Файл {file_path} успешно изменен!")
    print(f"✅ Бэкап сохранен в: {backup_dir}")

    return True

def check_syntax():
    """Проверяет синтаксис Python файла"""
    print("\n🔍 Проверка синтаксиса...")
    result = os.system("python3 -m py_compile /root/albimusic-bot/celery_tasks.py 2>&1")
    if result == 0:
        print("✅ Синтаксис корректен!")
        return True
    else:
        print("❌ Ошибка синтаксиса!")
        return False

def main():
    print("=" * 60)
    print("🎵 ИСПРАВЛЕНИЕ ПОЛУЧЕНИЯ 2 ССЫЛОК ОТ SUNO API")
    print("=" * 60)
    print()

    # Проверяем что мы на сервере
    if not os.path.exists("/root/albimusic-bot/celery_tasks.py"):
        print("❌ ОШИБКА: Файл /root/albimusic-bot/celery_tasks.py не найден!")
        print("Убедитесь что скрипт запущен на сервере.")
        return

    # Исправляем код
    if not fix_celery_tasks():
        print("\n❌ Исправление не удалось!")
        return

    # Проверяем синтаксис
    if not check_syntax():
        print("\n❌ Обнаружена ошибка синтаксиса! Откатываем изменения...")
        print("Восстановите из последнего бэкапа вручную.")
        return

    print("\n" + "=" * 60)
    print("✅ ВСЕ ГОТОВО!")
    print("=" * 60)
    print("\nТеперь нужно перезапустить Celery worker:")
    print("sudo systemctl restart albimusic-celery")
    print("\nИ проверить что он запустился:")
    print("sudo systemctl status albimusic-celery")
    print("\nПосле этого можно протестировать генерацию музыки!")

if __name__ == "__main__":
    main()
