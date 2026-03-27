#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
import logging
import requests
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any

import config
from db_utils import execute_query_sync

from celery import Celery, Task
from celery.signals import worker_process_init, worker_process_shutdown

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('celery_tasks')

# Инициализация Celery
celery_app = Celery('albimusic_tasks')
celery_app.config_from_object('celery_config')

# Глобальные переменные для пулов соединений
db_pool = None

def localize_lyrics_tags(text):
    """Переводит теги структуры песни с английского на русский"""
    replacements = {
        "[Verse]": "[Куплет]",
        "[Chorus]": "[Припев]",
        "[Bridge]": "[Бридж]",
        "[Intro]": "[Вступление]",
        "[Outro]": "[Заключение]",
        "[Pre-Chorus]": "[Пред-припев]"
    }
    for eng, rus in replacements.items():
        text = text.replace(eng, rus)
    return text

def delocalize_lyrics_tags(text):
    """Переводит теги структуры песни с русского на английский"""
    replacements = {
        "[Куплет]": "[Verse]",
        "[Припев]": "[Chorus]",
        "[Бридж]": "[Bridge]",
        "[Вступление]": "[Intro]",
        "[Заключение]": "[Outro]",
        "[Пред-припев]": "[Pre-Chorus]"
    }
    for rus, eng in replacements.items():
        text = text.replace(rus, eng)
    return text

def translate_style_to_english(russian_style, add_improvements=True):
    """Переводит описание стиля с русского на английский для Suno API"""
    # Словарь соответствий русских и английских терминов
    style_dict = {
        # Жанры
        "рок": "rock",
        "поп": "pop",
        "хип-хоп": "hip hop",
        "рэп": "rap",
        "джаз": "jazz",
        "блюз": "blues",
        "электронная": "electronic",
        "электроника": "electronic",
        "классическая": "classical",
        "классика": "classical",
        "фолк": "folk",
        "народная": "folk",
        "кантри": "country",
        "метал": "metal",
        "металл": "metal",
        "панк": "punk",
        "регги": "reggae",
        "соул": "soul",
        "фанк": "funk",
        "диско": "disco",
        "техно": "techno",
        "хаус": "house",
        "транс": "trance",
        "дабстеп": "dubstep",
        "эмбиент": "ambient",
        "инди": "indie",
        "альтернативный": "alternative",
        "альтернативная": "alternative",
        "эмо": "emo",
        "готик": "gothic",
        "готический": "gothic",
        "готика": "gothic",
        "гранж": "grunge",
        "хардкор": "hardcore",
        "индастриал": "industrial",
        "синти-поп": "synth-pop",
        "синтипоп": "synth-pop",
        "нью-эйдж": "new age",
        "нью эйдж": "new age",
        "ритм-энд-блюз": "r&b",
        "ритм и блюз": "r&b",
        "r&b": "r&b",
        "rnb": "r&b",
        "эйсид-джаз": "acid jazz",
        "эйсид джаз": "acid jazz",
        "лаунж": "lounge",
        "босса-нова": "bossa nova",
        "босса нова": "bossa nova",
        "самба": "samba",
        "румба": "rumba",
        "сальса": "salsa",
        "танго": "tango",
        "фламенко": "flamenco",
        "блюграсс": "bluegrass",
        "госпел": "gospel",
        "спиричуэлс": "spirituals",
        "эйсид-хаус": "acid house",
        "эйсид хаус": "acid house",
        "брейкбит": "breakbeat",
        "драм-н-бэйс": "drum and bass",
        "драм-н-басс": "drum and bass",
        "драм и бэйс": "drum and bass",
        "драм и басс": "drum and bass",
        "гэридж": "garage",
        "гараж": "garage",
        "хип-хаус": "hip house",
        "хип хаус": "hip house",
        "хардкор-техно": "hardcore techno",
        "хардкор техно": "hardcore techno",
        "хэппи-хардкор": "happy hardcore",
        "хэппи хардкор": "happy hardcore",
        "джангл": "jungle",
        "минимал-техно": "minimal techno",
        "минимал техно": "minimal techno",
        "прогрессив-хаус": "progressive house",
        "прогрессив хаус": "progressive house",
        "психоделик-транс": "psychedelic trance",
        "психоделик транс": "psychedelic trance",
        "эйсид-транс": "acid trance",
        "эйсид транс": "acid trance",
        "гоа-транс": "goa trance",
        "гоа транс": "goa trance",
        "хард-транс": "hard trance",
        "хард транс": "hard trance",
        "трип-хоп": "trip hop",
        "трип хоп": "trip hop",
        
        # Инструменты
        "гитара": "guitar",
        "фортепиано": "piano",
        "пианино": "piano",
        "скрипка": "violin",
        "барабаны": "drums",
        "ударные": "drums",
        "бас": "bass",
        "бас-гитара": "bass guitar",
        "синтезатор": "synthesizer",
        "синт": "synth",
        "саксофон": "saxophone",
        "труба": "trumpet",
        "флейта": "flute",
        "виолончель": "cello",
        "арфа": "harp",
        "аккордеон": "accordion",
        "банджо": "banjo",
        "укулеле": "ukulele",
        "орган": "organ",
        "кларнет": "clarinet",
        "гобой": "oboe",
        "туба": "tuba",
        "тромбон": "trombone",
        "контрабас": "double bass",
        "маримба": "marimba",
        "ксилофон": "xylophone",
        "колокольчики": "bells",
        "литавры": "timpani",
        "волынка": "bagpipes",
        "балалайка": "balalaika",
        "домра": "domra",
        "гусли": "gusli",
        
        # Настроения
        "веселая": "happy",
        "веселый": "happy",
        "веселое": "happy",
        "грустная": "sad",
        "грустный": "sad",
        "грустное": "sad",
        "меланхоличная": "melancholic",
        "меланхоличный": "melancholic",
        "меланхоличное": "melancholic",
        "энергичная": "energetic",
        "энергичный": "energetic",
        "энергичное": "energetic",
        "спокойная": "calm",
        "спокойный": "calm",
        "спокойное": "calm",
        "агрессивная": "aggressive",
        "агрессивный": "aggressive",
        "агрессивное": "aggressive",
        "романтическая": "romantic",
        "романтичная": "romantic",
        "романтический": "romantic",
        "романтичный": "romantic",
        "романтическое": "romantic",
        "романтичное": "romantic",
        "мечтательная": "dreamy",
        "мечтательный": "dreamy",
        "мечтательное": "dreamy",
        "эпическая": "epic",
        "эпический": "epic",
        "эпическое": "epic",
        "мрачная": "dark",
        "мрачный": "dark",
        "мрачное": "dark",
        "таинственная": "mysterious",
        "таинственный": "mysterious",
        "таинственное": "mysterious",
        "загадочная": "mysterious",
        "загадочный": "mysterious",
        "загадочное": "mysterious",
        "тревожная": "anxious",
        "тревожный": "anxious",
        "тревожное": "anxious",
        "напряженная": "tense",
        "напряженный": "tense",
        "напряженное": "tense",
        "расслабляющая": "relaxing",
        "расслабляющий": "relaxing",
        "расслабляющее": "relaxing",
        "вдохновляющая": "inspiring",
        "вдохновляющий": "inspiring",
        "вдохновляющее": "inspiring",
        "праздничная": "festive",
        "праздничный": "festive",
        "праздничное": "festive",
        "торжественная": "solemn",
        "торжественный": "solemn",
        "торжественное": "solemn",
        "игривая": "playful",
        "игривый": "playful",
        "игривое": "playful",
        "нежная": "gentle",
        "нежный": "gentle",
        "нежное": "gentle",
        "страстная": "passionate",
        "страстный": "passionate",
        "страстное": "passionate",
        "сентиментальная": "sentimental",
        "сентиментальный": "sentimental",
        "сентиментальное": "sentimental",
        "ностальгическая": "nostalgic",
        "ностальгический": "nostalgic",
        "ностальгическое": "nostalgic",
        
        # Эпохи и стили
        "80-е": "80s",
        "80е": "80s",
        "восьмидесятые": "80s",
        "90-е": "90s",
        "90е": "90s",
        "девяностые": "90s",
        "70-е": "70s",
        "70е": "70s",
        "семидесятые": "70s",
        "60-е": "60s",
        "60е": "60s",
        "шестидесятые": "60s",
        "ретро": "retro",
        "винтаж": "vintage",
        "современная": "modern",
        "современный": "modern",
        "современное": "modern",
        "футуристическая": "futuristic",
        "футуристический": "futuristic",
        "футуристическое": "futuristic",
        
        # Вокал
        "мужской вокал": "male vocals",
        "женский вокал": "female vocals",
        "мужской голос": "male voice",
        "женский голос": "female voice",
        "хор": "choir",
        "хоровое пение": "choral",
        "а капелла": "a cappella",
        "акапелла": "a cappella",
        "бэк-вокал": "backing vocals",
        "бэк вокал": "backing vocals",
        "вокализ": "vocalization",
        "скриминг": "screaming",
        "гроулинг": "growling",
        "рэп-вокал": "rap vocals",
        "рэп вокал": "rap vocals",
    }
    
    # Если стиль на английском, возвращаем как есть
    if russian_style and any(eng in russian_style.lower() for eng in ["rock", "pop", "jazz", "blues", "electronic", "classical", "folk", "country", "metal", "punk", "reggae", "soul", "funk", "disco", "techno", "house", "trance", "dubstep", "ambient", "indie", "alternative", "emo", "gothic", "grunge", "hardcore", "industrial", "synth-pop", "new age", "r&b", "acid jazz", "lounge", "bossa nova", "samba", "rumba", "salsa", "tango", "flamenco", "bluegrass", "gospel", "spirituals", "acid house", "breakbeat", "drum and bass", "garage", "hip house", "hardcore techno", "happy hardcore", "jungle", "minimal techno", "progressive house", "psychedelic trance", "acid trance", "goa trance", "hard trance", "trip hop"]):
        return russian_style
    
    # Переводим каждое слово
    words = russian_style.lower().split()
    translated_words = []
    
    for word in words:
        # Удаляем знаки препинания для поиска в словаре
        clean_word = word.strip(',.!?;:()-')
        
        # Проверяем, есть ли слово в словаре
        if clean_word in style_dict:
            # Заменяем слово на перевод, сохраняя знаки препинания
            translated_word = word.replace(clean_word, style_dict[clean_word])
            translated_words.append(translated_word)
        else:
            # Если слова нет в словаре, оставляем как есть
            translated_words.append(word)
    
    translated_style = ' '.join(translated_words)
    
    # Добавляем улучшения для Suno API
    if add_improvements:
        # Если стиль не содержит упоминания качества
        if not any(quality in translated_style.lower() for quality in ["high quality", "professional", "studio quality", "well produced", "clear sound", "high fidelity"]):
            translated_style += ", high quality, professional, studio quality"
        
        # Если стиль не содержит упоминания инструментов
        if not any(instrument in translated_style.lower() for instrument in ["guitar", "piano", "drums", "bass", "synthesizer", "violin", "orchestra", "band"]):
            # Для рока и похожих жанров
            if any(genre in translated_style.lower() for genre in ["rock", "metal", "punk", "alternative", "grunge"]):
                translated_style += ", electric guitar, drums, bass guitar"
            # Для электронной музыки
            elif any(genre in translated_style.lower() for genre in ["electronic", "techno", "house", "trance", "dubstep", "ambient"]):
                translated_style += ", synthesizer, electronic drums, bass"
            # Для классической музыки
            elif any(genre in translated_style.lower() for genre in ["classical", "orchestra", "symphony"]):
                translated_style += ", orchestra, strings, piano"
            # Для поп-музыки
            elif "pop" in translated_style.lower():
                translated_style += ", piano, drums, synthesizer"
            # Для джаза
            elif "jazz" in translated_style.lower():
                translated_style += ", saxophone, piano, double bass, drums"
            # Для фолка
            elif "folk" in translated_style.lower():
                translated_style += ", acoustic guitar, violin, flute"
            # Общий случай
            else:
                translated_style += ", full band arrangement"
    
    return translated_style

def generate_suno_music_sync(prompt, is_song=False, custom_mode=False, user_id=None, style=None):
    """Синхронная версия генерации музыки через Suno API с расширенным логированием"""
    
    import uuid
    import time
    request_id = str(uuid.uuid4())[:8]  # Короткий уникальный ID
    start_time = time.time()
    
    logger.info(f"╔═══════════════════════════════════════════════════════════╗")
    logger.info(f"║  SUNO API REQUEST | ID: {request_id} | User: {user_id}    ")
    logger.info(f"╚═══════════════════════════════════════════════════════════╝")
    
    # ОТЛАДКА: Логируем что пришло на вход
    logger.info(f"[{request_id}] 📝 INPUT PARAMETERS:")
    logger.info(f"[{request_id}]    • Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"[{request_id}]    • Prompt: {prompt}")
    logger.info(f"[{request_id}]    • Style: {style}")
    logger.info(f"[{request_id}]    • Custom mode: {custom_mode}")
    logger.info(f"[{request_id}]    • Is song: {is_song}")
    logger.info(f"[{request_id}]    • User ID: {user_id}")
    
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    

    # Конвертируем русские теги структуры обратно в английские для Suno
    prompt = delocalize_lyrics_tags(prompt)

    if is_song:
        # Определяем пол вокала из стиля
        vocal_gender = "m"  # по умолчанию мужской
        if style and ("female" in style.lower() or "женск" in style.lower()):
            vocal_gender = "f"
            # Усиливаем пол в строке стиля — Suno учитывает style сильнее чем vocalsGender
            if "female vocals" not in style.lower():
                style = style + ", female vocals, female voice"
        elif style and ("male" in style.lower() or "мужск" in style.lower()):
            vocal_gender = "m"
            # Усиливаем пол в строке стиля — Suno учитывает style сильнее чем vocalsGender
            if "male vocals" not in style.lower():
                style = style + ", male vocals, male voice"

        if custom_mode:
            data = {
                "prompt": prompt,  # ТОЛЬКО текст песни
                "model": "V5",
                "callBackUrl": "https://albi-music.ru/webhook/suno",
                "style": style if style else "",  # ТОЛЬКО стиль
                "customMode": True,
                "instrumental": False,
                "styleWeight": 0.9,
                "vocalsGender": vocal_gender
            }
        else:
            data = {
                "callBackUrl": "https://albi-music.ru/webhook/suno",
                "model": "V5",
                "prompt": prompt,  # ТОЛЬКО текст песни
                "style": style if style else "",  # ТОЛЬКО стиль
                "customMode": False,
                "instrumental": False,
                "styleWeight": 0.8,
                "vocalsGender": vocal_gender
            }
    else:
        data = {
            "callBackUrl": "https://albi-music.ru/webhook/suno",
            "prompt": prompt,  # ТОЛЬКО описание музыки
            "model": "V5",
            "style": style if style else "",  # ТОЛЬКО стиль
            "customMode": False,
            "instrumental": True,
            "styleWeight": 0.8,
        }
    
    # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДАННЫХ
    logger.info(f"[{request_id}] 📤 REQUEST DATA TO SUNO API:")
    safe_data = data.copy()
    if 'Authorization' in headers:
        safe_headers = headers.copy()
        safe_headers['Authorization'] = 'Bearer ***HIDDEN***'
        logger.info(f"[{request_id}]    • Headers: {safe_headers}")
    logger.info(f"[{request_id}]    • Data: {json.dumps(safe_data, ensure_ascii=False)}")
    
    try:
        # Создаем задачу генерации
        api_start = time.time()
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers, timeout=300)
        api_duration = time.time() - api_start
        
        logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
        logger.info(f"[{request_id}]    • Status code: {response.status_code}")
        logger.info(f"[{request_id}]    • Response time: {api_duration:.2f}s")
        logger.info(f"[{request_id}]    • Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            result = response.json()
            
            logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
            logger.info(f"[{request_id}]    • Response size: {len(response.text)} bytes")
            logger.info(f"[{request_id}]    • Response keys: {list(result.keys())}")
            logger.info(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)[:500]}...")
            
            # Проверяем код ответа Suno API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                logger.error(f"[{request_id}]    • Data: {data_obj}")
                return None
            
            # Проверяем что data не null
            if not data_obj:
                logger.error(f"[{request_id}] ❌ SUNO API: data is null!")
                logger.error(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)}")
                return None
            
            # Проверяем что data - это словарь
            if not isinstance(data_obj, dict):
                logger.error(f"[{request_id}] ❌ ОШИБКА: result['data'] не является словарем!")
                logger.error(f"[{request_id}]    • Тип: {type(data_obj)}")
                logger.error(f"[{request_id}]    • Значение: {data_obj}")
                return None
            
            logger.info(f"[{request_id}]    • Data keys: {list(data_obj.keys())}")
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')
            logger.info(f"[{request_id}] 🎵 SUNO TASK CREATED:")
            logger.info(f"[{request_id}]    • Task ID: {task_id}")
            
            # Ожидаем завершения генерации
            for i in range(90):  # 90 попыток по 10 секунд = 15 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers, timeout=60)
                status_duration = time.time() - api_start - api_duration - (i * 10)
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    
                    logger.info(f"[{request_id}] 📊 TASK STATUS #{i+1}:")
                    logger.info(f"[{request_id}]    • Status: {status}")
                    logger.info(f"[{request_id}]    • Total wait time: {(i+1)*10}s")
                    
                    if status == 'SUCCESS':
                        audio_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                        if audio_data:
                            # Извлекаем все ссылки (обычно 2 версии)
                            audio_urls = [item.get('audioUrl') for item in audio_data if item.get('audioUrl')]

                            # Извлекаем ВСЕ audioId для всех версий (для karaoke/WAV)
                            audio_ids = []
                            for item in audio_data:
                                # Пробуем разные возможные поля
                                audio_id = item.get('id') or item.get('audioId') or item.get('songId')
                                if audio_id:
                                    audio_ids.append(audio_id)
                                    logger.info(f"[{request_id}]    • Audio ID {len(audio_ids)}: {audio_id}")

                            # Если одна ссылка - возвращаем как строку, если несколько - как JSON массив
                            if len(audio_urls) == 1:
                                audio_url = audio_urls[0]
                            else:
                                audio_url = json.dumps(audio_urls)

                            # То же самое для audio_ids
                            if len(audio_ids) == 1:
                                suno_audio_id = audio_ids[0]
                            elif len(audio_ids) > 1:
                                suno_audio_id = json.dumps(audio_ids)
                            else:
                                suno_audio_id = None

                            logger.info(f"[{request_id}] ✅ SUNO GENERATION COMPLETED:")
                            logger.info(f"[{request_id}]    • Audio URLs: {len(audio_urls)} versions")
                            logger.info(f"[{request_id}]    • URLs: {audio_url[:200]}...")
                            logger.info(f"[{request_id}]    • Task ID: {task_id}")
                            logger.info(f"[{request_id}]    • Audio IDs: {suno_audio_id}")
                            logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")

                            # Возвращаем кортеж: (audio_url, suno_task_id, suno_audio_id)
                            return (audio_url, task_id, suno_audio_id)
                    elif status == 'ERROR' or status == 'SENSITIVE_WORD_ERROR':
                        error_msg = status_result.get('data', {}).get('response', {}).get('error', 'Unknown error')
                        logger.error(f"[{request_id}] ❌ SUNO GENERATION ERROR:")
                        logger.error(f"[{request_id}]    • Status: {status}")
                        logger.error(f"[{request_id}]    • Error: {error_msg}")
                        logger.error(f"[{request_id}]    • Full response: {json.dumps(status_result, ensure_ascii=False)}")
                        
                        # Возвращаем специальное сообщение для SENSITIVE_WORD_ERROR
                        if status == 'SENSITIVE_WORD_ERROR':
                            return ('SENSITIVE_WORD_ERROR', None, None)
                        return None
                    elif i > 30 and status == "PENDING":
                        logger.warning(f"[{request_id}] ⚠️ SUNO API SLOW:")
                        logger.warning(f"[{request_id}]    • Task {task_id} still PENDING after {(i+1)*10} seconds")
                else:
                    logger.warning(f"[{request_id}] ⚠️ STATUS CHECK FAILED:")
                    logger.warning(f"[{request_id}]    • Status code: {status_response.status_code}")
                    logger.warning(f"[{request_id}]    • Response: {status_response.text[:500]}")
            
            logger.error(f"[{request_id}] ⏰ SUNO TIMEOUT:")
            logger.error(f"[{request_id}]    • Task {task_id} timed out after 900 seconds")
            return None
        else:
            logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
            logger.error(f"[{request_id}]    • Status: {response.status_code}")
            logger.error(f"[{request_id}]    • Response: {response.text[:1000]}")
            return None
            
    except requests.exceptions.Timeout as e:
        logger.error(f"[{request_id}] ⏱️ SUNO REQUEST TIMEOUT:")
        logger.error(f"[{request_id}]    • Error: {str(e)}")
        logger.error(f"[{request_id}]    • Duration: {time.time() - start_time:.2f}s")
        return None
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[{request_id}] 🔌 SUNO CONNECTION ERROR:")
        logger.error(f"[{request_id}]    • Error: {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ UNEXPECTED SUNO ERROR:")
        logger.error(f"[{request_id}]    • Type: {type(e).__name__}")
        logger.error(f"[{request_id}]    • Error: {str(e)}")
        return None

@celery_app.task(name='generate_suno_song')
def generate_suno_song(lyrics, style):
    """Генерация песни через Suno API"""
    return generate_suno_song_sync(lyrics, style)

def generate_suno_song_sync(lyrics, style):
    """Синхронная версия генерации песни через Suno API"""
    import uuid
    import time
    request_id = str(uuid.uuid4())[:8]  # Короткий уникальный ID
    start_time = time.time()
    
    logger.info(f"╔═══════════════════════════════════════════════════════════╗")
    logger.info(f"║  SUNO SONG API REQUEST | ID: {request_id}                 ")
    logger.info(f"╚═══════════════════════════════════════════════════════════╝")
    
    # ОТЛАДКА: Логируем что пришло на вход
    logger.info(f"[{request_id}] 📝 INPUT PARAMETERS:")
    logger.info(f"[{request_id}]    • Lyrics: {lyrics[:100]}..." if len(lyrics) > 100 else f"[{request_id}]    • Lyrics: {lyrics}")
    logger.info(f"[{request_id}]    • Style: {style}")
    
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Конвертируем русские теги структуры обратно в английские для Suno
    lyrics = delocalize_lyrics_tags(lyrics)
    
    # Определяем пол вокала из стиля
    vocal_gender = "m"  # по умолчанию мужской
    if style and ("female" in style.lower() or "женск" in style.lower()):
        vocal_gender = "f"
        # Усиливаем пол в строке стиля — Suno учитывает style сильнее чем vocalsGender
        if "female vocals" not in style.lower():
            style = style + ", female vocals, female voice"
    elif style and ("male" in style.lower() or "мужск" in style.lower()):
        vocal_gender = "m"
        # Усиливаем пол в строке стиля — Suno учитывает style сильнее чем vocalsGender
        if "male vocals" not in style.lower():
            style = style + ", male vocals, male voice"
    
    # Проверяем длину текста песни и автоматически включаем customMode для длинных текстов
    use_custom_mode = len(lyrics) > 500
    
    data = {
        "prompt": lyrics,  # ТОЛЬКО текст песни
        "model": "V5",
        "callBackUrl": "https://albi-music.ru/webhook/suno",
        "style": style,  # ТОЛЬКО стиль
        "customMode": use_custom_mode,  # Автоматически включаем для длинных текстов
        "instrumental": False,
        "styleWeight": 0.8 if not use_custom_mode else 0.9,  # Увеличиваем вес стиля для customMode
        "vocalsGender": vocal_gender
    }
    
    # Логируем информацию о режиме
    if use_custom_mode:
        logger.info(f"[{request_id}] ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")
    
    # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДАННЫХ
    logger.info(f"[{request_id}] 📤 REQUEST DATA TO SUNO API:")
    safe_data = data.copy()
    if 'Authorization' in headers:
        safe_headers = headers.copy()
        safe_headers['Authorization'] = 'Bearer ***HIDDEN***'
        logger.info(f"[{request_id}]    • Headers: {safe_headers}")
    logger.info(f"[{request_id}]    • Data: {json.dumps(safe_data, ensure_ascii=False)}")
    
    try:
        # Создаем задачу генерации
        api_start = time.time()
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers, timeout=300)
        api_duration = time.time() - api_start
        
        logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
        logger.info(f"[{request_id}]    • Status code: {response.status_code}")
        logger.info(f"[{request_id}]    • Response time: {api_duration:.2f}s")
        logger.info(f"[{request_id}]    • Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            result = response.json()
            
            logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
            logger.info(f"[{request_id}]    • Response size: {len(response.text)} bytes")
            logger.info(f"[{request_id}]    • Response keys: {list(result.keys())}")
            logger.info(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)[:500]}...")
            
            # Проверяем код ответа Suno API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                logger.error(f"[{request_id}]    • Data: {data_obj}")
                return None
            
            # Проверяем что data не null
            if not data_obj:
                logger.error(f"[{request_id}] ❌ SUNO API: data is null!")
                logger.error(f"[{request_id}]    • Full response: {json.dumps(result, ensure_ascii=False)}")
                return None
            
            # Проверяем что data - это словарь
            if not isinstance(data_obj, dict):
                logger.error(f"[{request_id}] ❌ ОШИБКА: result['data'] не является словарем!")
                logger.error(f"[{request_id}]    • Тип: {type(data_obj)}")
                logger.error(f"[{request_id}]    • Значение: {data_obj}")
                return None
            
            logger.info(f"[{request_id}]    • Data keys: {list(data_obj.keys())}")
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')
            logger.info(f"[{request_id}] 🎵 SUNO TASK CREATED:")
            logger.info(f"[{request_id}]    • Task ID: {task_id}")
            
            # Ожидаем завершения генерации
            for i in range(90):  # 90 попыток по 10 секунд = 15 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers, timeout=60)
                status_duration = time.time() - api_start - api_duration - (i * 10)
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    
                    logger.info(f"[{request_id}] 📊 TASK STATUS #{i+1}:")
                    logger.info(f"[{request_id}]    • Status: {status}")
                    logger.info(f"[{request_id}]    • Total wait time: {(i+1)*10}s")
                    
                    if status == 'SUCCESS':
                        audio_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                        if audio_data:
                            # Извлекаем все ссылки (обычно 2 версии)
                            audio_urls = [item.get('audioUrl') for item in audio_data if item.get('audioUrl')]

                            # Извлекаем ВСЕ audioId для всех версий (для karaoke/WAV)
                            audio_ids = []
                            for item in audio_data:
                                # Пробуем разные возможные поля
                                audio_id = item.get('id') or item.get('audioId') or item.get('songId')
                                if audio_id:
                                    audio_ids.append(audio_id)
                                    logger.info(f"[{request_id}]    • Audio ID {len(audio_ids)}: {audio_id}")

                            # Если одна ссылка - возвращаем как строку, если несколько - как JSON массив
                            if len(audio_urls) == 1:
                                audio_url = audio_urls[0]
                            else:
                                audio_url = json.dumps(audio_urls)

                            # То же самое для audio_ids
                            if len(audio_ids) == 1:
                                suno_audio_id = audio_ids[0]
                            elif len(audio_ids) > 1:
                                suno_audio_id = json.dumps(audio_ids)
                            else:
                                suno_audio_id = None

                            logger.info(f"[{request_id}] ✅ SUNO SONG GENERATION COMPLETED:")
                            logger.info(f"[{request_id}]    • Audio URLs: {len(audio_urls)} versions")
                            logger.info(f"[{request_id}]    • URLs: {audio_url[:200]}...")
                            logger.info(f"[{request_id}]    • Task ID: {task_id}")
                            logger.info(f"[{request_id}]    • Audio IDs: {suno_audio_id}")
                            logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")

                            # Возвращаем кортеж: (audio_url, suno_task_id, suno_audio_id)
                            return (audio_url, task_id, suno_audio_id)
                    elif status == 'ERROR' or status == 'SENSITIVE_WORD_ERROR':
                        error_msg = status_result.get('data', {}).get('response', {}).get('error', 'Unknown error')
                        logger.error(f"[{request_id}] ❌ SUNO GENERATION ERROR:")
                        logger.error(f"[{request_id}]    • Status: {status}")
                        logger.error(f"[{request_id}]    • Error: {error_msg}")
                        logger.error(f"[{request_id}]    • Full response: {json.dumps(status_result, ensure_ascii=False)}")
                        
                        # Возвращаем специальное сообщение для SENSITIVE_WORD_ERROR
                        if status == 'SENSITIVE_WORD_ERROR':
                            return ('SENSITIVE_WORD_ERROR', None, None)
                        return None
                    elif i > 30 and status == "PENDING":
                        logger.warning(f"[{request_id}] ⚠️ SUNO API SLOW:")
                        logger.warning(f"[{request_id}]    • Task {task_id} still PENDING after {(i+1)*10} seconds")
                else:
                    logger.warning(f"[{request_id}] ⚠️ STATUS CHECK FAILED:")
                    logger.warning(f"[{request_id}]    • Status code: {status_response.status_code}")
                    logger.warning(f"[{request_id}]    • Response: {status_response.text[:500]}")
            
            logger.error(f"[{request_id}] ⏰ SUNO TIMEOUT:")
            logger.error(f"[{request_id}]    • Task {task_id} timed out after 900 seconds")
            return None
        else:
            logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
            logger.error(f"[{request_id}]    • Status: {response.status_code}")
            logger.error(f"[{request_id}]    • Response: {response.text[:1000]}")
            return None
            
    except requests.exceptions.Timeout as e:
        logger.error(f"[{request_id}] ⏱️ SUNO REQUEST TIMEOUT:")
        logger.error(f"[{request_id}]    • Error: {str(e)}")
        logger.error(f"[{request_id}]    • Duration: {time.time() - start_time:.2f}s")
        return None
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[{request_id}] 🔌 SUNO CONNECTION ERROR:")
        logger.error(f"[{request_id}]    • Error: {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ UNEXPECTED SUNO ERROR:")
        logger.error(f"[{request_id}]    • Type: {type(e).__name__}")
        logger.error(f"[{request_id}]    • Error: {str(e)}")
        return None

@celery_app.task(name='generate_suno_karaoke')
def generate_suno_karaoke(suno_id):
    """Генерация минусовки через Suno API"""
    return generate_suno_karaoke_sync(suno_id)

def generate_suno_karaoke_sync(suno_id):
    """Синхронная версия генерации минусовки через Suno API"""
    import uuid
    import time
    request_id = str(uuid.uuid4())[:8]  # Короткий уникальный ID
    start_time = time.time()
    
    logger.info(f"╔═══════════════════════════════════════════════════════════╗")
    logger.info(f"║  SUNO KARAOKE API REQUEST | ID: {request_id}              ")
    logger.info(f"╚═══════════════════════════════════════════════════════════╝")
    
    # ОТЛАДКА: Логируем что пришло на вход
    logger.info(f"[{request_id}] 📝 INPUT PARAMETERS:")
    logger.info(f"[{request_id}]    • Suno ID: {suno_id}")
    
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "songId": suno_id,
        "callBackUrl": "https://albi-music.ru/webhook/suno"
    }
    
    try:
        # Создаем задачу генерации минусовки
        api_start = time.time()
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/karaoke", json=data, headers=headers, timeout=300)
        api_duration = time.time() - api_start
        
        logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
        logger.info(f"[{request_id}]    • Status code: {response.status_code}")
        logger.info(f"[{request_id}]    • Response time: {api_duration:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            # Проверяем код ответа Suno API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                return None
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')
            logger.info(f"[{request_id}] 🎵 SUNO KARAOKE TASK CREATED:")
            logger.info(f"[{request_id}]    • Task ID: {task_id}")
            
            # Ожидаем завершения генерации
            for i in range(90):  # 90 попыток по 10 секунд = 15 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/karaoke/record-info?taskId={task_id}", headers=headers, timeout=60)
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    
                    logger.info(f"[{request_id}] 📊 KARAOKE TASK STATUS #{i+1}:")
                    logger.info(f"[{request_id}]    • Status: {status}")
                    logger.info(f"[{request_id}]    • Total wait time: {(i+1)*10}s")
                    
                    if status == 'SUCCESS':
                        audio_url = status_result.get('data', {}).get('response', {}).get('audioUrl')
                        
                        if audio_url:
                            logger.info(f"[{request_id}] ✅ SUNO KARAOKE COMPLETED:")
                            logger.info(f"[{request_id}]    • Audio URL: {audio_url}")
                            logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")
                            
                            return audio_url
                    elif status == 'ERROR':
                        error_msg = status_result.get('data', {}).get('response', {}).get('error', 'Unknown error')
                        logger.error(f"[{request_id}] ❌ SUNO KARAOKE ERROR:")
                        logger.error(f"[{request_id}]    • Error: {error_msg}")
                        return None
        else:
            logger.error(f"[{request_id}] ❌ SUNO API ERROR: Status code {response.status_code}")
            logger.error(f"[{request_id}]    • Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"[{request_id}] ❌ SUNO KARAOKE ERROR: {e}")
        return None
    
    logger.error(f"[{request_id}] ❌ SUNO KARAOKE TIMEOUT")
    return None

@celery_app.task(name='generate_suno_wav')
def generate_suno_wav(suno_id):
    """Генерация WAV через Suno API"""
    return generate_suno_wav_sync(suno_id)

def generate_suno_wav_sync(suno_id):
    """Синхронная версия генерации WAV через Suno API"""
    import uuid
    import time
    request_id = str(uuid.uuid4())[:8]  # Короткий уникальный ID
    start_time = time.time()
    
    logger.info(f"╔═══════════════════════════════════════════════════════════╗")
    logger.info(f"║  SUNO WAV API REQUEST | ID: {request_id}                  ")
    logger.info(f"╚═══════════════════════════════════════════════════════════╝")
    
    # ОТЛАДКА: Логируем что пришло на вход
    logger.info(f"[{request_id}] 📝 INPUT PARAMETERS:")
    logger.info(f"[{request_id}]    • Suno ID: {suno_id}")
    
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "songId": suno_id,
        "callBackUrl": "https://albi-music.ru/webhook/suno"
    }
    
    try:
        # Создаем задачу генерации WAV
        api_start = time.time()
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/wav", json=data, headers=headers, timeout=300)
        api_duration = time.time() - api_start
        
        logger.info(f"[{request_id}] 📥 SUNO API RESPONSE:")
        logger.info(f"[{request_id}]    • Status code: {response.status_code}")
        logger.info(f"[{request_id}]    • Response time: {api_duration:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            # Проверяем код ответа Suno API
            api_code = result.get('code')
            api_msg = result.get('msg', 'No message')
            data_obj = result.get('data')
            
            if api_code != 200:
                logger.error(f"[{request_id}] ❌ SUNO API ERROR:")
                logger.error(f"[{request_id}]    • Code: {api_code}")
                logger.error(f"[{request_id}]    • Message: {api_msg}")
                return None
            
            # Извлекаем taskId
            task_id = data_obj.get('taskId')
            logger.info(f"[{request_id}] 🎵 SUNO WAV TASK CREATED:")
            logger.info(f"[{request_id}]    • Task ID: {task_id}")
            
            # Ожидаем завершения генерации
            for i in range(90):  # 90 попыток по 10 секунд = 15 минут
                time.sleep(10)
                status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/wav/record-info?taskId={task_id}", headers=headers, timeout=60)
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('data', {}).get('status')
                    
                    logger.info(f"[{request_id}] 📊 WAV TASK STATUS #{i+1}:")
                    logger.info(f"[{request_id}]    • Status: {status}")
                    logger.info(f"[{request_id}]    • Total wait time: {(i+1)*10}s")
                    
                    if status == 'SUCCESS':
                        audio_url = status_result.get('data', {}).get('response', {}).get('audioUrl')
                        
                        if audio_url:
                            logger.info(f"[{request_id}] ✅ SUNO WAV COMPLETED:")
                            logger.info(f"[{request_id}]    • Audio URL: {audio_url}")
                            logger.info(f"[{request_id}]    • Total time: {time.time() - start_time:.2f}s")
                            
                            return audio_url
                    elif status == 'ERROR':
                        error_msg = status_result.get('data', {}).get('response', {}).get('error', 'Unknown error')
                        logger.error(f"[{request_id}] ❌ SUNO WAV ERROR:")
                        logger.error(f"[{request_id}]    • Error: {error_msg}")
                        return None
        else:
            logger.error(f"[{request_id}] ❌ SUNO API ERROR: Status code {response.status_code}")
            logger.error(f"[{request_id}]    • Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"[{request_id}] ❌ SUNO WAV ERROR: {e}")
        return None
    
    logger.error(f"[{request_id}] ❌ SUNO WAV TIMEOUT")
    return None

# ═══════════════════════════════════════════════════════════════
# WORKER SIGNALS
# ═══════════════════════════════════════════════════════════════

@worker_process_init.connect
def init_worker_db_pool(**kwargs):
    """
    Инициализация пула соединений с БД при старте worker
    """
    global db_pool
    
    try:
        from db_utils import init_db_pool_for_worker
        db_pool = init_db_pool_for_worker()
        logger.info("✅ [WORKER INIT] Database connection pool initialized")
    except ImportError as e:
        logger.warning(f"⚠️  [WORKER INIT] Function not found: {e}")
    except Exception as e:
        logger.error(f"❌ [WORKER INIT] Failed to initialize DB pool: {e}")

@worker_process_shutdown.connect
def shutdown_worker_db_pool(**kwargs):
    """
    Закрытие пула соединений с БД при остановке worker
    """
    logger.info("🔒 [WORKER SHUTDOWN] Closing database connection pool...")

    try:
        from db_utils import shutdown_pool_for_worker
        shutdown_pool_for_worker()
        logger.info("✅ [WORKER SHUTDOWN] Database pool closed successfully")
    except ImportError as e:
        logger.warning(f"⚠️  [WORKER SHUTDOWN] Function not found: {e}")
    except Exception as e:
        logger.error(f"❌ [WORKER SHUTDOWN] Failed to close DB pool: {e}")


@worker_process_init.connect
def log_worker_ready(**kwargs):
    """Логирование готовности worker к обработке задач"""
    logger.info("✅ [WORKER] Ready to process tasks")

# ═══════════════════════════════════════════════════════════════
# КОНЕЦ SIGNALS
# ═══════════════════════════════════════════════════════════════
