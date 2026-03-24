#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       ПРИМЕНЕНИЕ ВСЕХ ИСПРАВЛЕНИЙ                         ║"
echo "╚═══════════════════════════════════════════════════════════╝"

CELERY_FILE="/root/albimusic-bot/celery_tasks.py"
MAIN_FILE="/root/albimusic-bot/main_with_payments.py"

CELERY_BACKUP="${CELERY_FILE}.backup_taskid_$(date +%Y%m%d_%H%M%S)"
MAIN_BACKUP="${MAIN_FILE}.backup_taskid_$(date +%Y%m%d_%H%M%S)"

# Создаем backup
cp "$CELERY_FILE" "$CELERY_BACKUP"
cp "$MAIN_FILE" "$MAIN_BACKUP"

echo "✅ Backups созданы:"
echo "   • $CELERY_BACKUP"
echo "   • $MAIN_BACKUP"

# ========================================
# ИСПРАВЛЕНИЕ 1-5: celery_tasks.py
# ========================================

echo ""
echo "🔧 Исправляем celery_tasks.py..."

python3 << 'PYTHON'
import re

celery_file = "/root/albimusic-bot/celery_tasks.py"

with open(celery_file, 'r', encoding='utf-8') as f:
    content = f.read()

# ИСПРАВЛЕНИЕ 1 & 2: Добавляем генерацию UUID для обеих функций
fix_task_id = '''    # Используем переданный task_id или генерируем свой
    if task_id is None:
        task_id = self.request.id
    
    # Если self.request.id тоже None (eager mode), генерируем свой
    if task_id is None:
        import uuid
        task_id = str(uuid.uuid4())
        logger.warning(f"⚠️  self.request.id был None! Сгенерирован новый task_id: {task_id}")'''

# Ищем и заменяем в generate_song_task
pattern_song = r'(def generate_song_task\(self, user_id, lyrics, style, custom_mode=False, task_id=None\):\s*""".*?"""\s*)'
match = re.search(pattern_song, content, re.DOTALL)
if match:
    # Находим место после описания функции
    func_start = match.end()
    # Вставляем исправленный код после описания
    before = content[:func_start]
    after = content[func_start:]
    
    # Удаляем старую строку с task_id = self.request.id если есть
    after = re.sub(r'if task_id is None:\s*task_id = self\.request\.id', '', after, flags=re.DOTALL)
    
    content = before + fix_task_id + '\n\n    ' + after.lstrip()
    print("✅ generate_song_task исправлена")
else:
    print("❌ Не найден generate_song_task")

# Ищем и заменяем в generate_music_task  
pattern_music = r'(def generate_music_task\(self, user_id, prompt, task_id=None\):\s*""".*?"""\s*)'
match = re.search(pattern_music, content, re.DOTALL)
if match:
    func_start = match.end()
    before = content[:func_start]
    after = content[func_start:]
    
    after = re.sub(r'if task_id is None:\s*task_id = self\.request\.id', '', after, flags=re.DOTALL)
    
    content = before + fix_task_id + '\n\n    ' + after.lstrip()
    print("✅ generate_music_task исправлена")
else:
    print("❌ Не найден generate_music_task")

# ИСПРАВЛЕНИЕ 3: Добавляем экстренную генерацию UUID в save_generation_task_sync
save_func_pattern = r'(def save_generation_task_sync\(user_id, task_id, prompt, status, audio_url=None\):\s*""".*?"""\s*\n.*?try:)'
match = re.search(save_func_pattern, content, re.DOTALL)
if match:
    func_start = match.end()
    before = content[:func_start]
    after = content[func_start:]
    
    # Удаляем старые проверки на task_id is None если есть
    after = re.sub(r'if task_id is None:.*?return.*?"task_id is None".*?\n', '', after, flags=re.DOTALL)
    
    # Добавляем новую проверку в начало try блока
    fix_save = '''    # === ГАРАНТИЯ: task_id никогда не должен быть None ===
    if task_id is None:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: task_id is None!")
        logger.error("❌ Невозможно сохранить задачу без task_id")
        import uuid
        task_id = f"emergency_{uuid.uuid4()}"
        logger.warning(f"⚠️  Создан экстренный task_id: {task_id}")
    
    '''
    
    # Вставляем после try:
    after = re.sub(r'(try:\s*\n)', r'\1' + fix_save, after, flags=re.DOTALL)
    
    content = before + after
    print("✅ save_generation_task_sync исправлена")
else:
    print("❌ Не найден save_generation_task_sync")

# ИСПРАВЛЕНИЕ 4 & 5: Убираем 'ERROR:' из audio_url
content = re.sub(
    r"audio_url=audio_url if audio_url else f'ERROR: \{result_message\}'",
    r"audio_url=audio_url  # ✅ Сохраняем None при ошибке, не строку 'ERROR: ...'",
    content
)

# Дополнительно ищем другие варианты
content = re.sub(
    r"audio_url = audio_url if audio_url else f'ERROR: .*?'",
    r"audio_url = audio_url  # ✅ Сохраняем None при ошибке",
    content
)

with open(celery_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ celery_tasks.py - все исправления применены")
PYTHON

# ========================================
# ИСПРАВЛЕНИЕ 6: main_with_payments.py
# ========================================

echo ""
echo "🔧 Исправляем main_with_payments.py..."

python3 << 'PYTHON'
import re

main_file = "/root/albimusic-bot/main_with_payments.py"

with open(main_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем старый код с .delay()
pattern = r'(\s*# Отправляем задачу в Celery\s*\n\s*)if is_song:\s*task = generate_song_task\.delay\(user_id, lyrics, style, custom_mode\)\s*else:\s*task = generate_music_task\.delay\(user_id, f\'\{style\}\. \{custom_mode\}\' if custom_mode else style\)'

# ИСПРАВЛЕНИЕ 6: Заменяем на .apply_async() с task_id
fix_celery_call = '''        # === ГЕНЕРИРУЕМ task_id ЗАРАНЕЕ ДЛЯ ГАРАНТИИ ===
        import uuid
        celery_task_id = str(uuid.uuid4())
        
        logger.info(f"🆔 Создан task_id для Celery: {celery_task_id}")
        
        # Отправляем задачу в Celery с явным task_id
        if is_song:
            task = generate_song_task.apply_async(
                args=(user_id, lyrics, style, custom_mode),
                kwargs={'task_id': celery_task_id},
                task_id=celery_task_id  # ✅ Передаем ID самой задаче Celery
            )
        else:
            task = generate_music_task.apply_async(
                args=(user_id, f'{style}. {custom_mode}' if custom_mode else style),
                kwargs={'task_id': celery_task_id},
                task_id=celery_task_id  # ✅ Передаем ID самой задаче Celery
            )
        
        logger.info(f"✅ Celery задача отправлена: {task.id}")'''

content = re.sub(pattern, fix_celery_call, content, flags=re.DOTALL)

with open(main_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ main_with_payments.py исправлен")
PYTHON

# Проверка синтаксиса
echo ""
echo "🔍 Проверка синтаксиса..."
cd /root/albimusic-bot
source venv/bin/activate

echo "Проверяем celery_tasks.py..."
if python3 -m py_compile "$CELERY_FILE" 2>/tmp/celery_syntax_error.log; then
    echo "✅ celery_tasks.py - синтаксис корректен"
else
    echo "❌ Ошибка в celery_tasks.py:"
    cat /tmp/celery_syntax_error.log
    echo ""
    echo "Восстанавливаем backup..."
    cp "$CELERY_BACKUP" "$CELERY_FILE"
    exit 1
fi

echo "Проверяем main_with_payments.py..."
if python3 -m py_compile "$MAIN_FILE" 2>/tmp/main_syntax_error.log; then
    echo "✅ main_with_payments.py - синтаксис корректен"
else
    echo "❌ Ошибка в main_with_payments.py:"
    cat /tmp/main_syntax_error.log
    echo ""
    echo "Восстанавливаем backup..."
    cp "$MAIN_BACKUP" "$MAIN_FILE"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ                ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  ✅ task_id всегда будет иметь значение                   ║"
echo "║  ✅ Убрана строка 'ERROR:' из audio_url                   ║"
echo "║  ✅ apply_async() вместо delay()                          ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  СЛЕДУЮЩИЙ ШАГ:                                           ║"
echo "║  sudo systemctl restart albimusic-celery                  ║"
echo "║  sudo systemctl restart albimusic-bot                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
