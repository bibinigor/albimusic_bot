import re

# Читаем оригинальную версию
with open('celery_tasks.py.original', 'r') as f:
    original = f.read()

# Читаем нашу исправленную версию
with open('celery_tasks.py', 'r') as f:
    current = f.read()

# Находим нашу исправленную функцию save_generation_task_sync в текущей версии
pattern = r'def save_generation_task_sync\(user_id, task_id, prompt, status, audio_url=None\):.*?except Exception as e:.*?logger\.error\(f".*?{e}"\)'
match = re.search(pattern, current, re.DOTALL)

if match:
    our_fixed_function = match.group(0)
    print("✅ Нашли нашу исправленную функцию save_generation_task_sync")
    
    # Заменяем в оригинале старую функцию на нашу исправленную
    original = re.sub(r'def save_generation_task_sync\(user_id, task_id, prompt, status, audio_url=None\):.*?except Exception as e:.*?logger\.error\(f".*?{e}"\)', 
                     our_fixed_function, original, flags=re.DOTALL)
    
    # Сохраняем гибридную версию
    with open('celery_tasks.py', 'w') as f:
        f.write(original)
    
    print("✅ Создана гибридная версия:")
    print("   - Оригинальный celery_tasks.py")
    print("   + Наша исправленная функция save_generation_task_sync (UPSERT)")
else:
    print("❌ Не нашли нашу функцию в текущей версии")
    # Просто восстанавливаем оригинал
    with open('celery_tasks.py', 'w') as f:
        f.write(original)
    print("✅ Восстановлен оригинальный celery_tasks.py")
