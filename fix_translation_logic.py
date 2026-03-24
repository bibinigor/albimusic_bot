import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Находим функцию translate_style_to_english
start = content.find('def translate_style_to_english(russian_style):')
if start != -1:
    # Ищем конец функции
    end = content.find('\ndef', start + 1)
    if end == -1:
        end = len(content)
    
    # Заменяем старую функцию на исправленную
    new_function = '''def translate_style_to_english(russian_style):
    """Переводит русский стиль в английский для лучшего понимания Suno API"""
    if not russian_style:
        return ""
    
    # Приводим к нижнему регистру
    style_lower = russian_style.lower()
    
    # Проверяем есть ли русские буквы
    has_russian = any("а" <= char <= "я" for char in style_lower)
    
    if not has_russian:
        # Если нет русских букв, возвращаем как есть (уже английский)
        return russian_style
    
    # Простой словарь перевода ЦЕЛЫХ СЛОВ
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
        
        # Инструменты
        "гитара": "guitar",
        "электрогитара": "electric guitar",
        "соло": "solo",
        "бас": "bass",
        "бас-гитара": "bass guitar",
        "ударные": "drums",
        "барабаны": "drums",
        "синтезатор": "synthesizer",
        "фортепиано": "piano",
        "пианино": "piano",
        "скрипка": "violin",
        "струнные": "strings",
        "оркестр": "orchestra",
        "орган": "organ",
        
        # Вокал
        "вокал": "vocal",
        "мужской": "male",
        "женский": "female",
        "хор": "choir",
        "голос": "voice",
        
        # Темп/атмосфера
        "быстро": "fast tempo",
        "медленно": "slow tempo",
        "грустно": "sad, melancholic",
        "весело": "happy, joyful",
        "тихо": "quiet",
        "громко": "loud",
        "энергично": "energetic",
        "спокойно": "calm",
        "агрессивно": "aggressive",
        "грустный": "sad",
        "радостный": "happy",
        "эпично": "epic",
        
        # Союзы
        "и": "and",
        "с": "with",
    }
    
    # Разбиваем на слова и переводим
    words = style_lower.split()
    translated_words = []
    
    for word in words:
        # Убираем запятые, точки
        clean_word = word.strip(',.!?')
        
        if clean_word in word_translations:
            translated_words.append(word_translations[clean_word])
        else:
            # Если слова нет в словаре, оставляем как есть
            translated_words.append(clean_word)
    
    result = ", ".join(translated_words)
    
    # Добавляем улучшения для Suno
    improvements = {
        "electric guitar": "electric guitar solo",
        "bass": "bass guitar",
        "drums": "drum kit",
        "male vocal": "male rock vocal",
        "female vocal": "female vocal",
        "rock": "rock music",
        "pop": "pop music",
    }
    
    for key, value in improvements.items():
        if key in result:
            result = result + ", " + value
    
    # Логируем перевод
    if russian_style != result:
        logger.info(f"🔄 Перевод стиля: '{russian_style}' → '{result}'")
    
    return result'''
    
    # Заменяем функцию
    content = content[:start] + new_function + content[end:]
    
    with open('celery_tasks.py', 'w') as f:
        f.write(content)
    
    print("✅ Функция перевода исправлена!")
    print("Теперь переводит ЦЕЛЫЕ слова, а не подстроки")
else:
    print("❌ Функция translate_style_to_english не найдена")
