import re

with open('celery_tasks.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем функцию generate_suno_music_sync
in_function = False
modified = False

for i in range(len(lines)):
    line = lines[i]
    
    if 'def generate_suno_music_sync' in line:
        in_function = True
        continue
    
    if in_function and line.strip().startswith('def ') and 'generate_suno_music_sync' not in line:
        in_function = False
        continue
    
    if in_function:
        # БЛОК 1: custom_mode=True
        if '"vocalsGender": vocal_gender' in line and lines[i+1].strip() == '}':
            # Добавляем запятую в текущую строку
            lines[i] = lines[i].rstrip() + ',\n'
            # Добавляем callBackUrl перед закрывающей }
            indent = len(lines[i]) - len(lines[i].lstrip())
            lines.insert(i+1, ' ' * indent + '"callBackUrl": "https://albi-music.ru/webhook/suno"\n')
            modified = True
            print(f"✅ Блок 1 исправлен в строке {i+1}")
        
        # БЛОК 2: custom_mode=False (второе вхождение)
        # Найдем по контексту - после "else:" и "data = {"
        elif '"vocalsGender": vocal_gender' in line and i > 10:
            # Проверяем что это второй блок
            context = ''.join(lines[max(0, i-10):i+1])
            if 'else:' in context and '"styleWeight": 0.8' in context:
                if lines[i+1].strip() == '}':
                    lines[i] = lines[i].rstrip() + ',\n'
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    lines.insert(i+1, ' ' * indent + '"callBackUrl": "https://albi-music.ru/webhook/suno"\n')
                    modified = True
                    print(f"✅ Блок 2 исправлен в строке {i+1}")
        
        # БЛОК 3: instrumental
        elif '"styleWeight": 0.8,' in line and lines[i+1].strip() == '}':
            # Проверяем что это блок instrumental
            context = ''.join(lines[max(0, i-5):i+1])
            if '"instrumental": True' in context:
                lines[i] = lines[i].rstrip() + ',\n'
                indent = len(lines[i]) - len(lines[i].lstrip())
                lines.insert(i+1, ' ' * indent + '"callBackUrl": "https://albi-music.ru/webhook/suno"\n')
                modified = True
                print(f"✅ Блок 3 исправлен в строке {i+1}")

if modified:
    with open('celery_tasks.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("\n✅ Файл успешно обновлен")
else:
    print("⚠️  Изменения не внесены (возможно уже исправлено)")

