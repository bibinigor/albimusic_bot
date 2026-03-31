#!/usr/bin/env python3
"""
Прямой тест Suno API для диагностики проблем с минусовками
"""
import requests
import time
import sys
import json

sys.path.append('/root/albimusic-bot')
import config

def test_vocal_removal():
    """Тестируем vocal removal API напрямую"""
    
    # Используем известные ID из успешной генерации
    suno_task_id = "0a4d71edab496a88293cead27da38c26"
    suno_audio_id = "277d1c49-8323-4332-ab44-c779daa093fb"
    
    print(f"🧪 Тест Suno API Vocal Removal")
    print(f"{'='*60}")
    print(f"Suno Task ID: {suno_task_id}")
    print(f"Suno Audio ID: {suno_audio_id}")
    print(f"{'='*60}\n")
    
    suno_api_url = config.SUNO_API_URL
    headers = {
        'Authorization': f'Bearer {config.SUNO_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Шаг 1: Отправляем запрос на vocal removal
    payload = {
        'taskId': suno_task_id,
        'audioId': suno_audio_id,
        'callBackUrl': 'http://37.252.23.214:8000/webhook'
    }
    
    print("📤 Отправка запроса на vocal removal...")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(
            f"{suno_api_url}/api/v1/vocal-removal/generate",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"📥 Ответ: HTTP {response.status_code}")
        response_data = response.json()
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        if response.status_code == 200 and response_data.get('code') == 200:
            vocal_task_id = response_data.get('data', {}).get('taskId')
            print(f"\n✅ Задача создана: {vocal_task_id}")
            print(f"⏳ Ожидание завершения (максимум 5 минут)...\n")
            
            # Шаг 2: Polling
            for attempt in range(1, 61):
                print(f"🔄 Попытка {attempt}/60...")
                time.sleep(5)
                
                status_resp = requests.get(
                    f"{suno_api_url}/api/v1/vocal-removal/record-info?taskId={vocal_task_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    success_flag = status_data.get('data', {}).get('successFlag')
                    print(f"   Status: {success_flag}")
                    
                    if success_flag == 'SUCCESS':
                        response_data = status_data.get('data', {}).get('response', {})
                        karaoke_url = response_data.get('audioUrl') or response_data.get('instrumentalUrl')
                        
                        print(f"\n🎉 УСПЕХ!")
                        print(f"URL: {karaoke_url}")
                        return True
                    elif success_flag in ['ERROR', 'GENERATE_AUDIO_FAILED']:
                        print(f"\n❌ ОШИБКА API: {success_flag}")
                        print(json.dumps(status_data, indent=2, ensure_ascii=False))
                        return False
                else:
                    print(f"   HTTP {status_resp.status_code}: {status_resp.text[:100]}")
            
            print(f"\n⏱️ ТАЙМАУТ: задача не завершилась за 5 минут")
            print(f"Последний статус: {success_flag}")
            return False
        else:
            print(f"\n❌ Ошибка создания задачи:")
            print(f"Code: {response_data.get('code')}")
            print(f"Message: {response_data.get('msg')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_vocal_removal()
    sys.exit(0 if result else 1)
