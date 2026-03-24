with open('celery_tasks.py', 'r') as f:
    content = f.read()

# Исправляем основные ошибки в словаре
replacements = {
    '"электро": "electronic",': '"электро": "electronic", "электрогитара": "electric guitar",',
    '"ударные": "drums",\n        "барабаны": "drums",': '"ударные": "drums",\n        "барабаны": "drums",',
    '"бас": "bass",\n        "бас-гитара": "bass guitar",': '"бас": "bass",',
}

for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Исправлено: {old.split(':')[0]}...")

with open('celery_tasks.py', 'w') as f:
    f.write(content)

print("\n✅ Словарь перевода упрощен. Теперь перевод будет точнее.")
