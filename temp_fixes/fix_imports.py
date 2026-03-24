import re

# Читаем текущий файл
with open('main_with_payments.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем старые импорты на новые
content = content.replace(
    "from database_adapter import db", 
    "# from database_adapter import db  # Закомментирован - заменен на db_utils"
)

content = content.replace(
    "from redis_cache import init_redis", 
    "# from redis_cache import init_redis  # Закомментирован - Redis уже инициализирован в Celery"
)

# Добавляем новые импорты если их нет
if "from db_utils import" not in content:
    # Находим место после других импортов
    import_section_end = content.find("from celery_tasks import")
    if import_section_end != -1:
        content = content[:import_section_end] + "from db_utils import execute_query_sync\n" + content[import_section_end:]

# Записываем обратно
with open('main_with_payments.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Импорты исправлены")
