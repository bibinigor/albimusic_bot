import re

with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Исправляем save_generation_task_sync - добавляем проверку в начале
save_pattern = r'(def save_generation_task_sync\(user_id, task_id, prompt, status, audio_url=None\):\s*""".*?"""\s*\n.*?\n\s*)try:'
match = re.search(save_pattern, content, re.DOTALL)

if match:
    # Разделяем на части
    before_try = content[:match.end()]
    after_try = content[match.end():]
    
    # Вставляем проверку после try:
    check_code = '''
    # === ГАРАНТИЯ: task_id никогда не должен быть None ===
    if task_id is None:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: task_id is None!")
        logger.error("❌ Невозможно сохранить задачу без task_id")
        import uuid
        task_id = f"emergency_{uuid.uuid4()}"
        logger.warning(f"⚠️  Создан экстренный task_id: {task_id}")
    
    '''
    
    content = before_try + 'try:' + check_code + after_try
    
    # Удаляем старые проверки внутри функции
    content = re.sub(
        r'if task_id is None:\s*logger\.error\("❌ task_id is None! Невозможно обновить запись"\)\s*return \{"success": False, "error": "task_id is None"\}',
        '',
        content
    )
    
    content = re.sub(
        r'if task_id is None:\s*logger\.error\("❌ task_id is None! Невозможно обновить статус"\)\s*return \{"success": False, "error": "task_id is None"\}',
        '',
        content
    )

# 2. Исправляем generate_song_task
song_text = '''def generate_song_task(self, user_id, lyrics, style, custom_mode=False, task_id=None):
    """Синхронная задача генерации песни с гарантированным сохранением результата"""
    # Используем переданный task_id или генерируем свой
    if task_id is None:
        task_id = self.request.id
    
    # Если self.request.id тоже None (eager mode), генерируем свой
    if task_id is None:
        import uuid
        task_id = str(uuid.uuid4())
        logger.warning(f"⚠️  self.request.id был None! Сгенерирован новый task_id: {task_id}")
    
    logger.info(f"🔄 Запуск генерации песни для пользователя {user_id}, задача {task_id}")'''

content = re.sub(
    r'def generate_song_task\(self, user_id, lyrics, style, custom_mode=False, task_id=None\):\s*""".*?"""\s*\n\s*# Используем переданный task_id или генерируем свой\s*\n\s*if task_id is None:\s*task_id = self\.request\.id\s*\n\s*logger\.info\(f"🔄 Запуск генерации песни',
    song_text,
    content,
    flags=re.DOTALL
)

# 3. Исправляем generate_music_task
music_text = '''def generate_music_task(self, user_id, prompt, task_id=None):
    """Синхронная задача генерации музыки с гарантированным сохранением результата"""
    # Используем переданный task_id или генерируем свой
    if task_id is None:
        task_id = self.request.id
    
    # Если self.request.id тоже None (eager mode), генерируем свой
    if task_id is None:
        import uuid
        task_id = str(uuid.uuid4())
        logger.warning(f"⚠️  self.request.id был None! Сгенерирован новый task_id: {task_id}")
    
    logger.info(f"🔄 Запуск генерации музыки для пользователя {user_id}, задача {task_id}")'''

content = re.sub(
    r'def generate_music_task\(self, user_id, prompt, task_id=None\):\s*""".*?"""\s*\n\s*# Используем переданный task_id или генерируем свой\s*\n\s*if task_id is None:\s*task_id = self\.request\.id\s*\n\s*logger\.info\(f"🔄 Запуск генерации музыки',
    music_text,
    content,
    flags=re.DOTALL
)

# 4. Исправляем строки с 'ERROR:'
content = re.sub(
    r"audio_url=audio_url if audio_url else f'ERROR: \{result_message\}'",
    "audio_url=audio_url  # ✅ Сохраняем None при ошибке, не строку 'ERROR: ...'",
    content
)

with open('celery_tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ celery_tasks.py исправлен')
