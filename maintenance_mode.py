"""
Модуль для управления режимом технического обслуживания
"""
import os

MAINTENANCE_FILE = "/root/albimusic-bot/MAINTENANCE_MODE"

def is_maintenance_mode():
    """Проверяет включен ли режим техобслуживания"""
    return os.path.exists(MAINTENANCE_FILE)

def enable_maintenance():
    """Включает режим техобслуживания"""
    with open(MAINTENANCE_FILE, 'w') as f:
        f.write("MAINTENANCE MODE ENABLED")

def disable_maintenance():
    """Выключает режим техобслуживания"""
    if os.path.exists(MAINTENANCE_FILE):
        os.remove(MAINTENANCE_FILE)

MAINTENANCE_MESSAGE = """
🔧 **БОТ НА ТЕХНИЧЕСКОМ ОБСЛУЖИВАНИИ**

Мы улучшаем бота для вас! 

⏰ Работы займут несколько минут.
Скоро всё заработает!

Следите за новостями: @ALBImusic_chart
"""
