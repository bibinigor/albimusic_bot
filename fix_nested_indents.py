with open('main_with_payments.py', 'r') as f:
    lines = f.readlines()

# Строка 858: if balance_num == 1 ...
# Строки 859-862: внутри if/else должны иметь +4 пробела

# Проверим и исправим
print("До исправления:")
for i in range(857, 864):  # строки 858-864
    print(f"{i+1}: {lines[i].rstrip() if i < len(lines) else ''}")

# Исправляем вложенные отступы
if len(lines) > 858:  # строка 859
    lines[858] = '            ' + lines[858].lstrip()  # mark_free_generation_used
if len(lines) > 859:  # строка 860  
    lines[859] = '            ' + lines[859].lstrip()  # is_free = True
if len(lines) > 861:  # строка 862
    lines[861] = '            ' + lines[861].lstrip()  # is_free = False

with open('main_with_payments.py', 'w') as f:
    f.writelines(lines)

print("\nПосле исправления:")
for i in range(857, 864):
    print(f"{i+1}: {lines[i].rstrip() if i < len(lines) else ''}")
