# Минимальный словарь перевода русских музыкальных терминов
MUSIC_STYLE_TRANSLATIONS = {
    # Жанры
    'рок': 'rock',
    'поп': 'pop',
    'метал': 'metal',
    'джаз': 'jazz',
    'блюз': 'blues',
    'электрон': 'electronic',
    'хип-хоп': 'hip hop',
    'рэп': 'rap',
    'фолк': 'folk',
    'классическ': 'classical',
    
    # Инструменты
    'гитар': 'guitar',
    'электрогитар': 'electric guitar',
    'соло': 'solo',
    'бас': 'bass',
    'ударн': 'drums',
    'барабан': 'drum',
    'синтезатор': 'synthesizer',
    'фортепиано': 'piano',
    'пианино': 'piano',
    'скрипка': 'violin',
    'струнн': 'strings',
    'оркестр': 'orchestra',
    
    # Вокал
    'вокал': 'vocal',
    'мужск': 'male',
    'женск': 'female',
    'хор': 'choir',
    'голос': 'voice',
    
    # Темп/атмосфера
    'быстр': 'fast',
    'медлен': 'slow',
    'темп': 'tempo',
    'энергичн': 'energetic',
    'спокойн': 'calm',
    'агрессивн': 'aggressive',
    'грустн': 'sad',
    'радостн': 'happy',
}

def translate_style_to_english(russian_style):
    """Переводит русский стиль в английский для Suno API"""
    if not russian_style:
        return ""
    
    # Простой перевод слов
    result = russian_style.lower()
    for rus, eng in MUSIC_STYLE_TRANSLATIONS.items():
        result = result.replace(rus, eng)
    
    # Добавляем улучшения для Suno
    improvements = {
        'electric guitar': 'electric guitar solo lead, distorted rhythm guitar',
        'bass': 'bass guitar, prominent bass',
        'drums': 'full drum kit, strong drums',
        'male vocal': 'male rock vocal, powerful voice',
        'female vocal': 'female vocal, clear voice',
    }
    
    for key, value in improvements.items():
        if key in result:
            result = result.replace(key, value)
    
    # Убираем лишние запятые, делаем красивую строку
    result = ', '.join([word.strip() for word in result.split(',') if word.strip()])
    
    return result

# Тест
test_styles = [
    "рок электрогитара соло бас ударные мужской вокал",
    "поп синтезатор женский вокал",
    "джаз фортепиано скрипка",
]

print("🧪 Тест перевода стилей:")
for style in test_styles:
    translated = translate_style_to_english(style)
    print(f"  Русский: {style}")
    print(f"  Английский: {translated}")
    print()
