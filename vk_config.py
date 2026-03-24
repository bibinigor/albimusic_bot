import os

# VK Bot Configuration
VK_TOKEN = "vk1.a.pNU9DXJ2mP8mY6Jq-DG79W7eraOmkQoZcX3tp6KUy-DgfkxcBL2wx__TozIQ0Uzeb5BGvXuVQyTdl0LK_NWZD1SnG2Ef53gRLplRyXv4OlN47ro_sv2xak-gDW_Iaq1lKYH8K4LTWOYk1tNWAgADv7MWVD6Ae82PoBZjK9BAuqQavvvdHvbT-btu-czW0DTJ8wU1h07e4VpOkQKF4DF7Qg"
VK_GROUP_ID = 235442407

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Other configurations can be added here as needed
DEBUG = os.getenv("DEBUG", "False").lower() == "true"