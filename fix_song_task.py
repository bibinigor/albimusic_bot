import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Шаг 1: Найдём начало функции generate_song_task
task_start = content.find('def generate_song_task(self, user_id, lyrics, style, custom_mode=False):')
if task_start == -1:
    print("❌ Не найдена функция generate_song_task")
    exit(1)

# Шаг 2: Найдём строку с prompt = lyrics
# И заменим её на логику с объединением стиля и текста
pattern = r'(prompt = lyrics  # ТОЛЬКО текст песни)'
replacement = '''# ОБЪЕДИНЕНИЕ СТИЛЯ И ТЕКСТА
        if style:
            # Переводим русский стиль на английский для Suno API
            translated_style = translate_style_to_english(style)
            logger.info(f"🔄 Перевод стиля '{style}' -> '{translated_style}'")
            prompt = f"{translated_style}. {lyrics}"
        else:
            prompt = lyrics  # Только текст песни если стиль не указан'''

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
    print("✅ Заменено формирование prompt с учётом стиля")
else:
    print("❌ Не найден pattern 'prompt = lyrics'")

# Шаг 3: Добавим передачу style в вызов generate_suno_music_sync
# Найдём вызов функции
pattern2 = r'audio_url = generate_suno_music_sync\(\s*prompt=prompt,\s*is_song=True,\s*custom_mode=custom_mode,\s*user_id=user_id\s*\)'
replacement2 = '''audio_url = generate_suno_music_sync(
            prompt=prompt,
            is_song=True,
            custom_mode=custom_mode,
            user_id=user_id,
            style=style  # Передаём стиль для отладки
        )'''

if re.search(pattern2, content, re.DOTALL):
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    print("✅ Добавлена передача style в generate_suno_music_sync")
else:
    print("❌ Не найден вызов generate_suno_music_sync в generate_song_task")

# Сохраняем исправленный файл
with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Файл celery_tasks.py обновлён")
print("Изменения:")
print("1. Стиль теперь переводится и добавляется к prompt")
print("2. Стиль передаётся в generate_suno_music_sync для отладки")
