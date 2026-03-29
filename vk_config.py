import os

# VK Bot Configuration
VK_TOKEN = "vk1.a.pNU9DXJ2mP8mY6Jq-DG79W7eraOmkQoZcX3tp6KUy-DgfkxcBL2wx__TozIQ0Uzeb5BGvXuVQyTdl0LK_NWZD1SnG2Ef53gRLplRyXv4OlN47ro_sv2xak-gDW_Iaq1lKYH8K4LTWOYk1tNWAgADv7MWVD6Ae82PoBZjK9BAuqQavvvdHvbT-btu-czW0DTJ8wU1h07e4VpOkQKF4DF7Qg"
VK_GROUP_ID = 235442407

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Admin configuration
ADMIN_VK_ID = 57725952  # ID администратора VK
CO_ADMIN_ID = 57725952  # ID со-администратора (может быть тот же)
ADMIN_IDS = [ADMIN_VK_ID, CO_ADMIN_ID]  # Список ID администраторов

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# YooKassa Configuration (для платежей)
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', "1208840")
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', 'live_706Kz88KIYBby24ajXDegpCmJfyfL-yLoj_Gu_6cimY')