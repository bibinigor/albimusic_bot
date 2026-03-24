import requests
import json
import config
import time

def test_model(model_name):
    """Тест разных моделей Suno"""
    headers = {
        "Authorization": f"Bearer {config.SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": "Test song for checking model duration",
        "style": "Rock music with guitar solo",
        "title": f"Test {model_name}",
        "customMode": True,
        "instrumental": False,
        "model": model_name,  # Пробуем разные модели
        "callBackUrl": "https://example.com/callback"
    }
    
    print(f"\\n🧪 Тестируем модель: {model_name}")
    print(f"   Данные: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{config.SUNO_API_URL}/api/v1/generate", 
                               json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('data', {}).get('taskId')
            print(f"   ✅ Задача создана: {task_id}")
            
            # Ждем 30 секунд и проверяем статус
            print(f"   ⏳ Ожидаем 30 секунд...")
            time.sleep(30)
            
            status_response = requests.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", 
                                         headers=headers, timeout=30)
            if status_response.status_code == 200:
                status_result = status_response.json()
                status = status_result.get('data', {}).get('status')
                model_type = status_result.get('data', {}).get('type')
                print(f"   📊 Статус: {status}, Модель: {model_type}")
                
                if status == 'SUCCESS':
                    suno_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                    if suno_data:
                        duration = suno_data[0].get('duration', 0)
                        print(f"   ⏱️  Длительность: {duration} секунд")
                        return duration
            return 0
        else:
            print(f"   ❌ Ошибка: {response.status_code}, {response.text}")
            return 0
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return 0

print("🎵 Тестирование разных моделей Suno API")
print("="*60)

models = ["V4", "V4_5", "V4_5PLUS", "V4_5ALL", "V5"]
results = {}

for model in models:
    duration = test_model(model)
    results[model] = duration
    time.sleep(2)  # Пауза между запросами

print("\\n" + "="*60)
print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ МОДЕЛЕЙ:")
for model, duration in results.items():
    status = "✅ ХОРОШО" if duration > 30 else "⚠️ КОРОТКО" if duration > 0 else "❌ ОШИБКА"
    print(f"  {model}: {duration:.1f} сек - {status}")

print("\\n💡 РЕКОМЕНДАЦИЯ:")
best_model = max(results, key=results.get) if results else "V5"
print(f"  Использовать модель: {best_model} (максимальная длина: {results.get(best_model, 0):.1f} сек)")
