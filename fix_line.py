with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Строка 589 (нумерация с 0)
lines[589] = '🔥 Попробуй создать песню **БЕСПЛАТНО**! \n'

with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("✅ Исправлена строка 590")
