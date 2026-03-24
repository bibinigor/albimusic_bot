#!/usr/bin/env python3
import re

with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Находим место после logger для вставки
logger_line = 'logger = logging.getLogger(__name__)'
logger_pos = content.find(logger_line)
if logger_pos != -1:
    # Находим конец строки с logger
    insert_pos = content.find('\n', logger_pos) + 1
    
    # Вставляем исправленную функцию перевода
    translator_code = '''
def translate_style_to_english(russian_style):
    """Переводит русский стиль в английский для лучшего понимания Suno API"""
    if not russian_style:
        return ""
    
    # Полный словарь перевода
    translations = {
        # Жанры
        "рок": "rock", "поп": "pop", "метал": "metal", "джаз": "jazz", "блюз": "blues",
        "электро": "electronic", "хип-хоп": "hip hop", "рэп": "rap", "фолк": "folk",
        "классика": "classical", "инди": "indie", "кантри": "country", "регги": "reggae",
        "диско": "disco", "фанк": "funk", "соул": "soul", "рнб": "r&b", "техно": "techno",
        "транс": "trance", "хаус": "house", "дабстеп": "dubstep", "лоуфай": "lofi",
        "амбиент": "ambient", "саундтрек": "soundtrack", "оркестровая": "orchestral",
        
        # Инструменты
        "гитара": "guitar", "электрогитара": "electric guitar", "акустическая гитара": "acoustic guitar",
        "соло": "solo", "бас": "bass", "бас-гитара": "bass guitar", "ударные": "drums",
        "барабаны": "drums", "бочка": "kick drum", "тарелки": "cymbals", "синтезатор": "synthesizer",
        "фортепиано": "piano", "пианино": "piano", "рояль": "grand piano", "скрипка": "violin",
        "виолончель": "cello", "арфа": "harp", "флейта": "flute", "саксофон": "saxophone",
        "труба": "trumpet", "тромбон": "trombone", "орган": "organ", "аккордеон": "accordion",
        "укулеле": "ukulele", "банджо": "banjo", "ксилофон": "xylophone",
        
        # Вокал
        "вокал": "vocal", "мужской": "male", "женский": "female", "детский": "children",
        "дети": "children", "хор": "choir", "группа": "group", "голос": "voice",
        
        # Темп/атмосфера
        "быстро": "fast tempo", "медленно": "slow tempo", "грустно": "sad, melancholic",
        "весело": "happy, joyful", "тихо": "quiet", "громко": "loud", "энергично": "energetic",
        "спокойно": "calm", "агрессивно": "aggressive", "романтично": "romantic",
        "эпично": "epic", "драматично": "dramatic", "ностальгично": "nostalgic",
        
        # Союзы
        "и": "and", "с": "with",
    }
    
    # Приводим к нижнему регистру
    style_lower = russian_style.lower()
    
    # Проверяем русские буквы
    has_russian = any("а" <= char <= "я" for char in style_lower)
    if not has_russian:
        return russian_style
    
    # Простая замена слов
    result = style_lower
    for rus, eng in translations.items():
        result = result.replace(rus, eng)
    
    # Улучшения для Suno
    improvements = [
        ("electric guitar", "electric guitar solo"),
        ("bass", "bass guitar"),
        ("drums", "drum kit"),
        ("male vocal", "male rock vocal"),
        ("children vocal", "children choir"),
        ("piano", "piano melody"),
        ("violin", "violin accompaniment"),
        ("sad", "melancholic mood"),
        ("happy", "joyful mood"),
    ]
    
    for key, value in improvements:
        if key in result:
            result += ", " + value
    
    # Убираем дубликаты
    parts = [p.strip() for p in result.split(",") if p.strip()]
    unique_parts = []
    for part in parts:
        if part not in unique_parts:
            unique_parts.append(part)
    
    result = ", ".join(unique_parts)
    
    # Логируем
    if russian_style != result:
        logger.info(f"🔄 Перевод стиля: '{russian_style}' → '{result}'")
    
    return result'''
    
    # Вставляем код
    new_content = content[:insert_pos] + translator_code + content[insert_pos:]
    
    # Теперь исправим generate_song_task чтобы использовать перевод
    # Найдем строку use_style = style в generate_song_task
    generate_song_pattern = r'def generate_song_task\(self, user_id, lyrics, style, custom_mode=False\):'
    start = new_content.find(generate_song_pattern)
    if start != -1:
        # Найдем строку use_style = style
        use_style_pos = new_content.find('use_style = style', start)
        if use_style_pos != -1:
            # Заменяем на use_style = translate_style_to_english(style)
            new_content = new_content[:use_style_pos] + 'use_style = translate_style_to_english(style)' + new_content[use_style_pos + len('use_style = style'):]
        
        # Также исправим prompt для custom_mode=false
        prompt_pos = new_content.find('prompt = f"{style}. {lyrics}"', start)
        if prompt_pos != -1:
            new_content = new_content[:prompt_pos] + 'prompt = f"{translate_style_to_english(style)}. {lyrics}"' + new_content[prompt_pos + len('prompt = f"{style}. {lyrics}"'):]
    
    with open('celery_tasks.py', 'w') as f:
        f.write(content[:insert_pos] + translator_code + content[insert_pos:])
    
    print("✅ Функция перевода добавлена!")
    print("✅ generate_song_task теперь использует переводчик")
else:
    print("❌ Не найден logger в файле")
