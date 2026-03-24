import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Найдем generate_suno_music_sync и добавим логирование ДО отправки в Suno
pattern = r'def generate_suno_music_sync\(prompt, is_song=False, custom_mode=False, user_id=None, style=None\):.*?headers = \{'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Добавляем отладочное логирование
    debug_code = '''def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None, style=None):
    """Синхронная версия генерации музыки через Suno API"""
    
    # ОТЛАДКА: Логируем что пришло на вход
    logger.info(f"🔍 SUNO DEBUG Входные параметры:")
    logger.info(f"   prompt: {prompt}")
    logger.info(f"   style: {style}")
    logger.info(f"   custom_mode: {custom_mode}")
    logger.info(f"   is_song: {is_song}")
    logger.info(f"   user_id: {user_id}")
    
    headers = {'''
    
    content = content.replace(match.group(0), debug_code)
    
    # Также добавим логирование ДО отправки запроса
    send_pattern = r'try:\s+# Создаем задачу генерации'
    if re.search(send_pattern, content):
        before_send = '''    # Логируем данные ДО отправки в Suno
    logger.info(f"📤 SUNO DEBUG Данные для отправки:")
    logger.info(f"   Данные: {data}")
    
    try:
        # Создаем задачу генерации'''
        
        content = re.sub(send_pattern, before_send, content)
    
    with open('celery_tasks.py', 'w') as f:
        f.write(content)
    
    print("✅ Добавлено отладочное логирование в generate_suno_music_sync")
    print("Теперь в логах будет видно:")
    print("1. Что приходит в функцию")
    print("2. Что отправляется в Suno API")
else:
    print("❌ Не найдена функция generate_suno_music_sync")
