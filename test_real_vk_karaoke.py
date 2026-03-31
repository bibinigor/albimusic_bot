#!/usr/bin/env python3
"""
Тест создания минусовки на РЕАЛЬНОМ треке VK бота
"""

import sys
sys.path.append('/root/albimusic-bot')

import logging
from db_utils import execute_query_sync, init_db_pool_sync
from celery_tasks import generate_karaoke_task
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*70)
    print("🧪 ТЕСТ МИНУСОВКИ НА РЕАЛЬНОМ ТРЕКЕ")
    print("="*70 + "\n")
    
    init_db_pool_sync()
    
    # Ищем последний успешный трек с Suno IDs
    print("🔍 Поиск последнего трека с Suno IDs...")
    result = execute_query_sync("""
        SELECT task_id, user_id, prompt, suno_task_id, suno_audio_id, audio_url
        FROM generations
        WHERE status = 'completed'
        AND suno_task_id IS NOT NULL
        AND suno_audio_id IS NOT NULL
        AND prompt NOT ILIKE '%минусовка%'
        AND prompt NOT ILIKE '%кавер%'
        AND prompt NOT ILIKE '%WAV%'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    if not result:
        print("❌ Не найдено треков с Suno IDs!")
        print("\n💡 РЕШЕНИЕ: Создайте новый трек через VK бота")
        return
    
    task_id, user_id, prompt, suno_task_id, suno_audio_id, audio_url = result[0]
    
    print(f"✅ Найден трек:")
    print(f"   Task ID: {task_id}")
    print(f"   User ID: {user_id}")
    print(f"   Prompt: {prompt[:50]}...")
    print(f"   Suno Task: {suno_task_id}")
    print(f"   Suno Audio: {suno_audio_id}")
    print(f"   Audio URL: {audio_url[:60] if audio_url else 'None'}...")
    
    # Проверяем формат suno_audio_id
    if suno_audio_id:
        if suno_audio_id.startswith('['):
            print(f"   ✅ suno_audio_id это JSON массив (есть версии)")
            import json
            try:
                audio_ids = json.loads(suno_audio_id)
                print(f"      Версий: {len(audio_ids)}")
                for i, aid in enumerate(audio_ids):
                    print(f"      - Версия {i}: {aid}")
            except:
                print(f"      ⚠️ Ошибка парсинга JSON")
        else:
            print(f"   ✅ suno_audio_id это строка (одна версия)")
    
    print(f"\n🚀 Запускаем тест минусовки (версия 0)...")
    print(f"   Это создаст минусовку и отправит пользователю {user_id}")
    
    # Спрашиваем подтверждение
    confirm = input("\n⚠️  Продолжить? Это РЕАЛЬНО отправит сообщение пользователю! (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Отменено пользователем")
        return
    
    # Запускаем задачу
    print("\n📤 Запуск задачи Celery...")
    try:
        result = generate_karaoke_task.apply_async(
            args=[user_id, task_id, 0],  # version=0
            queue='generation'
        )
        
        print(f"✅ Задача запущена: {result.id}")
        print(f"\n⏳ Ожидание результата (макс 5 минут)...")
        
        # Ждем результат
        for i in range(60):  # 60 попыток по 5 секунд = 5 минут
            time.sleep(5)
            
            # Проверяем статус в БД
            status_check = execute_query_sync("""
                SELECT status, audio_url, prompt
                FROM generations
                WHERE user_id = %s
                AND prompt ILIKE '%минусовка%'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            if status_check:
                status, url, prompt_text = status_check[0]
                print(f"   [{i+1}/60] Статус: {status}")
                
                if status == 'completed':
                    print(f"\n✅ УСПЕХ! Минусовка создана!")
                    print(f"   Audio URL: {url[:80] if url else 'None'}...")
                    
                    if url and url.startswith('ALREADY_SENT'):
                        print(f"   ✅ Результат УЖЕ ОТПРАВЛЕН пользователю!")
                    else:
                        print(f"   ⚠️ Результат НЕ отправлен (нет префикса ALREADY_SENT)")
                    break
                    
                elif status == 'error':
                    print(f"\n❌ ОШИБКА! Минусовка не создана")
                    if url and url.startswith('ERROR'):
                        error_msg = url.replace('ERROR: ', '')
                        print(f"   Ошибка: {error_msg}")
                    break
        else:
            print(f"\n⏱️ Таймаут! Задача не завершилась за 5 минут")
            
    except Exception as e:
        print(f"\n❌ Ошибка запуска задачи: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
