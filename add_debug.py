import sys
sys.path.insert(0, '.')

with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Вставляем настройки логирования после импортов
for i, line in enumerate(lines):
    if 'import logging' in line:
        insert_idx = i + 1
        debug_code = '''\nlogging.getLogger("aiogram").setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")\n'''
        lines.insert(insert_idx, debug_code)
        break

with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)
