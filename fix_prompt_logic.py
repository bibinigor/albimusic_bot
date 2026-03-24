import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Исправляем логику в generate_song_task
new_song_task_logic = '''@celery_app.task(bind=True, name='celery_tasks.generate_song_task')
def generate_song_task(self, user_id, lyrics, style, custom_mode=False):
    """Синхронная задача генерации песни с текстом"""
    task_id = self.request.id
    logger.info(f"🔄 Запуск генерации песни для пользователя {user_id}, задача {task_id}")
    
    try:
        # Логика в зависимости от режима
        if custom_mode:
            # В custom_mode=true: стиль в поле style, текст в prompt
            prompt = lyrics
            use_style = style
        else:
            # В custom_mode=false: объединяем стиль и текст в prompt
            prompt = f"{style}. {lyrics}" if style else lyrics
            use_style = None  # В non-custom_mode style не передается
        
        # Сохраняем задачу в БД
        save_success = save_generation_task_sync(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt,
            status='processing'
        )'''

# Заменяем старую логику
pattern = r'@celery_app\.task\(bind=True, name=.celery_tasks\.generate_song_task.\)\s+def generate_song_task\(self, user_id, lyrics, style, custom_mode=False\):.*?prompt = .*?# Сохраняем задачу в БД'
content = re.sub(pattern, new_song_task_logic, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Логика generate_song_task исправлена!")
