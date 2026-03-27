#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys

def fix_returns_in_handle_message(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим метод handle_message
    handle_message_pattern = r'def handle_message\(self, event\):(.*?)def [a-zA-Z_]+\('
    handle_message_match = re.search(handle_message_pattern, content, re.DOTALL)
    
    if not handle_message_match:
        print("Метод handle_message не найден")
        return
    
    handle_message_code = handle_message_match.group(1)
    
    # Заменяем все return на continue
    fixed_code = handle_message_code.replace("\n                return", "\n                continue")
    
    # Заменяем исходный код
    new_content = content.replace(handle_message_code, fixed_code)
    
    # Записываем исправленный код обратно в файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Файл {file_path} успешно исправлен")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "main_vk.py"
    
    fix_returns_in_handle_message(file_path)