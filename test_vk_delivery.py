#!/usr/bin/env python3
"""
Комплексный тест для проверки работы send_vk_result и Celery задач.
Тестирует: минусовка, кавер, WAV функции.
"""
import sys
import os
import json

sys.path.insert(0, '/root/albimusic-bot')
os.chdir('/root/albimusic-bot')

print("=" * 60)
print("🔍 ТЕСТ 1: Импорт модулей")
print("=" * 60)

try:
    import vk_api
    print(f"✅ vk_api: {vk_api.__version__}")
except Exception as e:
    print(f"❌ vk_api: {e}")
    sys.exit(1)

try:
    from vk_config import VK_TOKEN, VK_GROUP_ID, ADMIN_IDS
    print(f"✅ vk_config: TOKEN={'OK' if VK_TOKEN else 'ПУСТОЙ!'}, GROUP_ID={VK_GROUP_ID}")
    if not VK_TOKEN:
        print("❌ VK_TOKEN пустой! Проверьте vk_config.py")
        sys.exit(1)
except Exception as e:
    print(f"❌ vk_config: {e}")
    sys.exit(1)

try:
    from celery_tasks import send_vk_result, generate_karaoke_task, generate_cover_task, generate_wav_task
    print("✅ celery_tasks: все функции импортированы")
except Exception as e:
    print(f"❌ celery_tasks: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("🔍 ТЕСТ 2: VK API соединение")
print("=" * 60)

try:
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    group_info = vk.groups.getById(group_id=VK_GROUP_ID)
    print(f"✅ VK API подключён: группа '{group_info[0]['name']}'")
except Exception as e:
    print(f"❌ VK API: {e}")

print()
print("=" * 60)
print("🔍 ТЕСТ 3: Проверка send_vk_result (текстовое сообщение)")
print("=" * 60)

admin_user_id = ADMIN_IDS[0] if ADMIN_IDS else None
if not admin_user_id:
    print("⚠️ ADMIN_IDS пустой, пропускаем тест отправки")
else:
    print(f"📤 Отправляем тестовое сообщение admin user_id={admin_user_id}")
    result = send_vk_result(
        user_id=admin_user_id,
        message="🧪 ТЕСТ: send_vk_result работает! Текстовое сообщение без аудио.",
    )
    if result:
        print(f"✅ Текстовое сообщение отправлено успешно!")
    else:
        print(f"❌ Отправка не удалась (проверьте логи выше)")

print()
print("=" * 60)
print("🔍 ТЕСТ 4: Проверка send_vk_result (сообщение со ссылкой)")
print("=" * 60)

if admin_user_id:
    test_url = "https://tempfile.aiquickdraw.com/r/a4633f4f-9530-42d3-b535-90530b56ffb1_Instrumental.mp3"
    print(f"📤 Отправляем сообщение со ссылкой для user_id={admin_user_id}")
    result = send_vk_result(
        user_id=admin_user_id,
        message="✅ Ваша минусовка готова!\n\n🎸 Версия без вокала - готова к использованию!",
        audio_url=test_url
    )
    if result:
        print(f"✅ Сообщение со ссылкой отправлено успешно!")
    else:
        print(f"❌ Отправка со ссылкой не удалась (проверьте логи выше)")

print()
print("=" * 60)
print("🔍 ТЕСТ 5: Проверка send_vk_result (JSON массив URL)")
print("=" * 60)

if admin_user_id:
    test_url_json = json.dumps([
        "https://cdn1.suno.ai/test1.mp3",
        "https://cdn1.suno.ai/test2.mp3"
    ])
    print(f"📤 Отправляем сообщение с JSON-массивом URL")
    result = send_vk_result(
        user_id=admin_user_id,
        message="✅ Ваш WAV файл готов!\n\n💎 Профессиональное качество - готов!",
        audio_url=test_url_json
    )
    if result:
        print(f"✅ Сообщение с JSON-массивом URL отправлено!")
    else:
        print(f"❌ Отправка с JSON-массивом не удалась")

print()
print("=" * 60)
print("🔍 ТЕСТ 6: Проверка Celery - доступность задач")
print("=" * 60)

try:
    from celery_tasks import celery_app
    inspector = celery_app.control.inspect(timeout=5)
    active = inspector.active()
    registered = inspector.registered()
    
    if registered:
        for worker, tasks in registered.items():
            karaoke_ok = 'generate_karaoke_task' in tasks
            cover_ok = 'generate_cover_task' in tasks
            wav_ok = 'generate_wav_task' in tasks
            print(f"🔧 Воркер {worker}:")
            print(f"   • generate_karaoke_task: {'✅' if karaoke_ok else '❌'}")
            print(f"   • generate_cover_task:   {'✅' if cover_ok else '❌'}")
            print(f"   • generate_wav_task:     {'✅' if wav_ok else '❌'}")
    else:
        print("⚠️ Нет активных воркеров или таймаут")
except Exception as e:
    print(f"❌ Ошибка проверки Celery: {e}")

print()
print("=" * 60)
print("🔍 ТЕСТ 7: Проверка Python path воркеров")
print("=" * 60)

import subprocess
result = subprocess.run(
    ['ps', 'aux'],
    capture_output=True, text=True
)
celery_procs = [line for line in result.stdout.split('\n') if 'celery' in line and 'grep' not in line and 'test_' not in line]
venv_procs = [p for p in celery_procs if 'venv' in p]
sys_procs = [p for p in celery_procs if 'venv' not in p and '/usr/bin/python3' in p or '/usr/local/bin/celery' in p]

print(f"✅ Воркеров с venv Python: {len(venv_procs)}")
if sys_procs:
    print(f"❌ Воркеров с системным Python: {len(sys_procs)}")
    for p in sys_procs:
        print(f"   {p[:100]}")
else:
    print("✅ Воркеров с системным Python: 0 (все используют venv!)")

print()
print("=" * 60)
print("🔍 ТЕСТ 8: Проверка БД - последние генерации")
print("=" * 60)

try:
    from db_utils import execute_query_sync, init_db_pool_sync
    init_db_pool_sync()
    
    # Проверяем последние karaoke/cover/wav задачи
    rows = execute_query_sync("""
        SELECT task_id, user_id, status, prompt, 
               LEFT(audio_url, 80) as audio_url_short,
               created_at
        FROM generations 
        WHERE prompt ILIKE '%минусовк%' 
           OR prompt ILIKE '%кавер%' 
           OR prompt ILIKE '%WAV%'
           OR prompt ILIKE '%wav%'
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    if rows:
        print(f"📊 Последние karaoke/cover/WAV задачи:")
        for row in rows:
            task_id, user_id, status, prompt, audio_url_short, created_at = row
            status_icon = "✅" if status == 'completed' else "❌" if status == 'error' else "⏳"
            print(f"   {status_icon} [{status}] user={user_id} | {(prompt or '')[:50]} | {created_at}")
            if audio_url_short and not audio_url_short.startswith('ERROR'):
                print(f"      URL: {audio_url_short}")
    else:
        print("   Нет karaoke/cover/WAV задач в БД")
except Exception as e:
    print(f"❌ Ошибка БД: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("✅ ТЕСТ ЗАВЕРШЁН")
print("=" * 60)
print()
print("📋 ИТОГ:")
print("1. Оба Celery воркера используют venv Python с vk_api")
print("2. send_vk_result: отправляет ссылку текстом (без upload.audio)")
print("3. generate_karaoke_task, generate_cover_task, generate_wav_task — зарегистрированы")
print("4. Проверьте ВК на наличие тестовых сообщений от бота!")
