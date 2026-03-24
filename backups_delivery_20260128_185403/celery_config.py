
from celery.schedules import crontab

# Конфигурация периодических задач
beat_schedule = {
    'cleanup-old-tasks-daily': {
        'task': 'celery_tasks.cleanup_old_tasks',
        'schedule': crontab(hour=3, minute=0),  # Каждый день в 3:00
    },
}

# Настройки очередей
task_routes = {
    'celery_tasks.cleanup_old_tasks': {'queue': 'cleanup'},
    'generate_music_task': {'queue': 'generation'},
    'generate_song_task': {'queue': 'generation'},
}
