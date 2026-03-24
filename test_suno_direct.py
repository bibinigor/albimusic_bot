import requests
import json
import config

def test_suno_api(prompt, style=None, custom_mode=False, is_song=True):
    """Прямой тест Suno API"""
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if is_song:
        if custom_mode:
            data = {
                "prompt": prompt,
                "style": style if style else "pop",
                "title": "Test Song",
                "customMode": True,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
        else:
            # В non-custom_mode стиль объединяем с промптом
            full_prompt = f"{style}. {prompt}" if style else prompt
            data = {
                "prompt": full_prompt,
                "customMode": False,
                "instrumental": False,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
    else:
        data = {
            "prompt": prompt,
            "customMode": False,
            "instrumental": True,
            "model": "V5",
            "callBackUrl": "https://example.com/callback"
        }
    
    print(f"\n📤 Отправляем запрос к Suno API:")
    print(f"  Prompt: {prompt[:50]}...")
    print(f"  Style: {style}")
    print(f"  Custom mode: {custom_mode}")
    print(f"  Is song: {is_song}")
    print(f"  Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", 
                               json=data, headers=headers, timeout=30)
        print(f"\n📥 Ответ Suno API: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Task ID: {result.get('data', {}).get('taskId')}")
            print(f"  Message: {result.get('msg')}")
            return result.get('data', {}).get('taskId')
        else:
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None

print("🧪 Тестирование Suno API с разными параметрами")

# Тест 1: Английский стиль, точный режим
print("\n" + "="*60)
print("ТЕСТ 1: Английский стиль, точный режим (custom_mode=True)")
task1 = test_suno_api(
    prompt="This is a test song about testing Suno API",
    style="Rock music with electric guitar and drums, male voice",
    custom_mode=True,
    is_song=True
)

# Тест 2: Английский стиль, творческий режим  
print("\n" + "="*60)
print("ТЕСТ 2: Английский стиль, творческий режим (custom_mode=False)")
task2 = test_suno_api(
    prompt="This is another test song",
    style="Pop music with synthesizer, female voice",
    custom_mode=False,
    is_song=True
)

# Тест 3: Русский стиль, точный режим
print("\n" + "="*60)
print("ТЕСТ 3: Русский стиль, точный режим (custom_mode=True)")
task3 = test_suno_api(
    prompt="Это тестовая песня на русском языке",
    style="Рок музыка с электрогитарой, мужской голос",
    custom_mode=True,
    is_song=True
)

# Тест 4: Инструментальная музыка (должна работать)
print("\n" + "="*60)
print("ТЕСТ 4: Инструментальная музыка (для сравнения)")
task4 = test_suno_api(
    prompt="Rock instrumental with electric guitar solo",
    style=None,
    custom_mode=False,
    is_song=False
)

print("\n" + "="*60)
print("🎯 ИТОГИ ТЕСТИРОВАНИЯ:")
print(f"Тест 1 (Английский, точный): {'✅' if task1 else '❌'} Task ID: {task1}")
print(f"Тест 2 (Английский, творческий): {'✅' if task2 else '❌'} Task ID: {task2}")
print(f"Тест 3 (Русский, точный): {'✅' if task3 else '❌'} Task ID: {task3}")
print(f"Тест 4 (Инструментальная): {'✅' if task4 else '❌'} Task ID: {task4}")

print("\n💡 ВЫВОДЫ:")
print("1. Если тесты 1-2 работают, а 3 нет - проблема в русском языке")
print("2. Если тест 4 работает - инструментальная музыка в порядке")
print("3. Если все работают - проблема в коде бота, а не в Suno API")
