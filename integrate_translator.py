import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Добавляем функцию перевода и словарь
translator_code = '''
# Словарь перевода русских музыкальных терминов для Suno API
MUSIC_STYLE_TRANSLATIONS = {
    # Жанры
    "рок": "rock",
    "поп": "pop",
    "метал": "metal",
    "хард-рок": "hard rock",
    "хеви-метал": "heavy metal",
    "джаз": "jazz",
    "блюз": "blues",
    "электрон": "electronic",
    "хип-хоп": "hip hop",
    "рэп": "rap",
    "фолк": "folk",
    "классическ": "classical",
    "инди": "indie",
    
    # Инструменты
    "гитар": "guitar",
    "электрогитар": "electric guitar",
    "соло": "solo",
    "бас": "bass",
    "бас-гитар": "bass guitar",
    "ударн": "drums",
    "барабан": "drum",
    "синтезатор": "synthesizer",
    "фортепиано": "piano",
    "пианино": "piano",
    "скрипка": "violin",
    "струнн": "strings",
    "оркестр": "orchestra",
    "орган": "organ",
    
    # Вокал
    "вокал": "vocal",
    "мужск": "male",
    "женск": "female",
    "хор": "choir",
    "голос": "voice",
    
    # Темп/атмосфера
    "быстр": "fast",
    "медлен": "slow",
    "темп": "tempo",
    "энергичн": "energetic",
    "спокойн": "calm",
    "агрессивн": "aggressive",
    "грустн": "sad",
    "радостн": "happy",
    "эпичн": "epic",
    "драйв": "driving beat",
}

def translate_style_to_english(russian_style):
    """Переводит русский стиль в английский для лучшего понимания Suno API"""
    if not russian_style:
        return ""
    
    # Приводим к нижнему регистру для поиска
    style_lower = russian_style.lower()
    
    # Проверяем есть ли русские буквы
    has_russian = any("а" <= char <= "я" for char in style_lower)
    
    if not has_russian:
        # Если нет русских букв, возвращаем как есть (уже английский)
        return russian_style
    
    # Простой перевод: заменяем русские слова английскими
    result = style_lower
    for rus, eng in MUSIC_STYLE_TRANSLATIONS.items():
        if rus in result:
            result = result.replace(rus, eng)
    
    # Добавляем улучшения для лучшего понимания Suno
    improvements = {
        "electric guitar": "electric guitar solo lead, distorted rhythm guitar",
        "bass guitar": "bass guitar, prominent bass",
        "bass": "bass guitar",
        "drums": "full drum kit",
        "drum": "drum kit",
        "male vocal": "male rock vocal, powerful voice",
        "female vocal": "female vocal, clear voice",
        "rock": "rock music",
        "pop": "pop music",
    }
    
    for key, value in improvements.items():
        if key in result:
            result = result + ", " + value
    
    # Убираем дубликаты и лишние запятые
    words = [word.strip() for word in result.split(",") if word.strip()]
    unique_words = []
    for word in words:
        if word not in unique_words:
            unique_words.append(word)
    
    result = ", ".join(unique_words)
    
    # Логируем перевод
    if russian_style != result:
        logger.info(f"🔄 Перевод стиля: '{russian_style}' → '{result}'")
    
    return result
'''

# Находим место для вставки (после logger)
logger_pos = content.find('logger = logging.getLogger(__name__)')
if logger_pos != -1:
    # Ищем конец строки с logger
    insert_pos = content.find('\n', logger_pos) + 1
    # Вставляем наш код
    new_content = content[:insert_pos] + translator_code + content[insert_pos:]
    
    # Теперь модифицируем generate_song_task чтобы использовать перевод
    pattern = r'if custom_mode:\s+# В custom_mode=true: стиль в поле style, текст в prompt \+ указание длины\s+prompt = f.\{lyrics\} \[Song length: 3 minutes\].\s+use_style = style'
    replacement = '''if custom_mode:
            # В custom_mode=true: стиль в поле style, текст в prompt + указание длины
            prompt = f"{lyrics} [Song length: 3 minutes]"
            # Переводим стиль на английский для лучшего понимания Suno
            use_style = translate_style_to_english(style)'''
    
    new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)
    
    with open('celery_tasks.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Переводчик стилей встроен в celery_tasks.py!")
    print("Теперь русские стили автоматически переводятся в английские для Suno API")
else:
    print("❌ Не удалось найти место для вставки кода")
