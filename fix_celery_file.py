import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# 1. Проверим есть ли celery_app в начале файла
if 'celery_app = Celery' not in content[:500]:
    print("❌ Нет celery_app в начале файла")
    
    # Найдем где начинаются импорты
    import_pos = content.find('#!/usr/bin/env python3')
    if import_pos == -1:
        import_pos = content.find('import time')
    
    if import_pos != -1:
        # Вставляем celery_app после импортов
        celery_code = '''
# Инициализация Celery
celery_app = Celery('albimusic_tasks', broker=config.BROKER_URL)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_send_task_events=True,
    task_send_sent_event=True,
)'''
        
        # Найдем куда вставить (после logger)
        logger_pos = content.find('logger = logging.getLogger(__name__)')
        if logger_pos != -1:
            insert_pos = content.find('\n', logger_pos) + 1
            content = content[:insert_pos] + celery_code + '\n' + content[insert_pos:]
            print("✅ Добавлен celery_app")
else:
    print("✅ celery_app уже есть")

# 2. Обновим словарь перевода, добавим детей, детский и больше инструментов
translation_dict = '''
def translate_style_to_english(russian_style):
    """Переводит русский стиль в английский для лучшего понимания Suno API"""
    if not russian_style:
        return ""
    
    # Полный словарь перевода ЦЕЛЫХ СЛОВ
    word_translations = {
        # Жанры
        "рок": "rock",
        "поп": "pop",
        "метал": "metal",
        "джаз": "jazz",
        "блюз": "blues",
        "электро": "electronic",
        "хип-хоп": "hip hop",
        "рэп": "rap",
        "фолк": "folk",
        "классика": "classical",
        "инди": "indie",
        "кантри": "country",
        "регги": "reggae",
        "диско": "disco",
        "фанк": "funk",
        "соул": "soul",
        "рнб": "r&b",
        "техно": "techno",
        "транс": "trance",
        "хаус": "house",
        "дабстеп": "dubstep",
        "лоуфай": "lofi",
        "амбиент": "ambient",
        "саундтрек": "soundtrack",
        "оркестровая": "orchestral",
        
        # Инструменты
        "гитара": "guitar",
        "электрогитара": "electric guitar",
        "акустическая гитара": "acoustic guitar",
        "соло": "solo",
        "бас": "bass",
        "бас-гитара": "bass guitar",
        "ударные": "drums",
        "барабаны": "drums",
        "бочка": "kick drum",
        "малый барабан": "snare drum",
        "тарелки": "cymbals",
        "томы": "tom drums",
        "синтезатор": "synthesizer",
        "фортепиано": "piano",
        "пианино": "piano",
        "рояль": "grand piano",
        "скрипка": "violin",
        "альт": "viola",
        "виолончель": "cello",
        "контрабас": "double bass",
        "арфа": "harp",
        "флейта": "flute",
        "саксофон": "saxophone",
        "труба": "trumpet",
        "тромбон": "trombone",
        "туба": "tuba",
        "кларнет": "clarinet",
        "гобой": "oboe",
        "фагот": "bassoon",
        "орган": "organ",
        "аккордеон": "accordion",
        "баян": "button accordion",
        "гиталеле": "guitalelle",
        "укулеле": "ukulele",
        "банджо": "banjo",
        "мандолина": "mandolin",
        "арфа": "harp",
        "челеста": "celesta",
        "колокольчики": "glockenspiel",
        "ксилофон": "xylophone",
        "вибрафон": "vibraphone",
        "маримба": "marimba",
        
        # Вокал
        "вокал": "vocal",
        "мужской": "male",
        "женский": "female",
        "детский": "children",
        "дети": "children",
        "хор": "choir",
        "группа": "group",
        "солист": "soloist",
        "голос": "voice",
        "пение": "singing",
        "скриминг": "screaming",
        "гроул": "growl",
        "скэт": "scat",
        "битбокс": "beatbox",
        
        # Темп/атмосфера
        "быстро": "fast tempo",
        "медленно": "slow tempo",
        "средне": "medium tempo",
        "грустно": "sad, melancholic",
        "весело": "happy, joyful",
        "тихо": "quiet, soft",
        "громко": "loud, powerful",
        "энергично": "energetic",
        "спокойно": "calm, peaceful",
        "агрессивно": "aggressive",
        "романтично": "romantic",
        "мистично": "mystical",
        "эпично": "epic, cinematic",
        "драматично": "dramatic",
        "ностальгично": "nostalgic",
        "мечтательно": "dreamy",
        "таинственно": "mysterious",
        "торжественно": "solemn",
        "игриво": "playful",
        
        # Союзы и предлоги
        "и": "and",
        "с": "with",
        "без": "without",
        "на": "on",
        "в": "in",
    }
    
    # Приводим к нижнему регистру
    style_lower = russian_style.lower()
    
    # Проверяем есть ли русские буквы
    has_russian = any("а" <= char <= "я" for char in style_lower)
    
    if not has_russian:
        # Если нет русских букв, возвращаем как есть
        return russian_style
    
    # Разбиваем на слова (учитывая запятые)
    import re
    words = re.split(r'[,\s]+', style_lower)
    words = [w for w in words if w]  # Убираем пустые
    
    translated_words = []
    
    for word in words:
        # Убираем знаки препинания
        clean_word = word.strip(',.!?')
        
        if clean_word in word_translations:
            translated_words.append(word_translations[clean_word])
        else:
            translated_words.append(clean_word)
    
    result = ", ".join(translated_words)
    
    # Добавляем улучшения для Suno
    improvements = {
        "electric guitar": "electric guitar solo",
        "bass": "bass guitar",
        "drums": "drum kit",
        "male vocal": "male rock vocal",
        "female vocal": "female vocal",
        "children vocal": "children choir",
        "rock": "rock music",
        "pop": "pop music",
        "sad": "sad, melancholic mood",
        "happy": "happy, joyful mood",
        "piano": "piano melody",
        "violin": "violin accompaniment",
    }
    
    for key, value in improvements.items():
        if key in result:
            result = result + ", " + value
    
    # Убираем дубликаты
    parts = [p.strip() for p in result.split(",")]
    unique_parts = []
    for part in parts:
        if part and part not in unique_parts:
            unique_parts.append(part)
    
    result = ", ".join(unique_parts)
    
    # Логируем перевод
    if russian_style != result:
        logger.info(f"🔄 Перевод стиля: '{russian_style}' → '{result}'")
    
    return result'''

# Найдем старую функцию translate_style_to_english и заменим ее
pattern = r'def translate_style_to_english\(russian_style\):.*?return result\n'
content = re.sub(pattern, translation_dict, content, flags=re.DOTALL)

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("✅ Файл исправлен!")
print("Добавлены: дети, детский, много инструментов и жанров")
print("Также проверено наличие celery_app")
