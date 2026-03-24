#!/usr/bin/env python3
"""
Тестовый скрипт для проверки VK авторизации
Симулирует полный флоу OAuth
"""

import requests
import json
from urllib.parse import urlparse, parse_qs

# Конфигурация
API_BASE = "https://albi-music.ru"
VK_APP_ID = "54451761"
VK_CLIENT_SECRET = "EXsS6C2HrdCS8I5Pddjn"

print("🔍 Тест VK OAuth авторизации")
print("=" * 50)

# Шаг 1: Получаем auth URL
print("\n1️⃣ Получаем auth URL от нашего API...")
try:
    response = requests.get(f"{API_BASE}/auth/vk/login")
    response.raise_for_status()
    data = response.json()
    auth_url = data.get("auth_url")
    state = data.get("state")

    print(f"✅ Auth URL получен")
    print(f"   State: {state}")
    print(f"   URL: {auth_url[:80]}...")

    # Парсим URL
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)

    print(f"\n   Параметры:")
    print(f"   - client_id: {params.get('client_id', ['N/A'])[0]}")
    print(f"   - redirect_uri: {params.get('redirect_uri', ['N/A'])[0]}")
    print(f"   - response_type: {params.get('response_type', ['N/A'])[0]}")
    print(f"   - v: {params.get('v', ['N/A'])[0]}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    exit(1)

# Шаг 2: Проверяем доступность VK OAuth
print("\n2️⃣ Проверяем доступность VK OAuth...")
try:
    # Делаем HEAD запрос к VK OAuth
    vk_response = requests.head(auth_url, allow_redirects=True, timeout=10)
    print(f"✅ VK OAuth доступен (HTTP {vk_response.status_code})")

    # Проверяем редиректы
    if vk_response.history:
        print(f"   Редиректов: {len(vk_response.history)}")
        for i, resp in enumerate(vk_response.history, 1):
            print(f"   {i}. {resp.status_code} → {resp.headers.get('Location', 'N/A')[:50]}...")

except Exception as e:
    print(f"❌ VK OAuth недоступен: {e}")

# Шаг 3: Проверяем callback endpoint
print("\n3️⃣ Проверяем доступность callback endpoint...")
try:
    # Проверяем что наш callback endpoint существует
    # (без параметров он должен вернуть ошибку, но 400, а не 404)
    callback_response = requests.get(
        f"{API_BASE}/auth/vk/callback",
        params={"code": "test", "state": "test"},
        allow_redirects=False
    )

    if callback_response.status_code == 404:
        print(f"❌ Callback endpoint не найден (404)")
    elif callback_response.status_code == 400:
        print(f"✅ Callback endpoint существует (400 - ожидаемо без валидных параметров)")
    else:
        print(f"⚠️  Callback endpoint вернул: {callback_response.status_code}")

except Exception as e:
    print(f"❌ Ошибка при проверке callback: {e}")

# Шаг 4: Проверяем health endpoint
print("\n4️⃣ Проверяем работоспособность Web API...")
try:
    health_response = requests.get(f"{API_BASE}/health")
    health_response.raise_for_status()
    health_data = health_response.json()

    print(f"✅ Web API работает")
    print(f"   Status: {health_data.get('status')}")
    print(f"   Service: {health_data.get('service')}")
    print(f"   Version: {health_data.get('version')}")

except Exception as e:
    print(f"❌ Web API не работает: {e}")

# Итоги
print("\n" + "=" * 50)
print("📊 ИТОГИ ТЕСТА:")
print()
print("✅ Если все шаги прошли успешно, то проблема НЕ в нашем коде.")
print("   Возможные причины проблемы:")
print("   1. Браузер блокирует cookies (проверь настройки браузера)")
print("   2. VK возвращает ошибку после авторизации (проверь логи)")
print("   3. Проблема с обработкой токена на фронтенде")
print()
print("📝 Следующий шаг:")
print("   Попробуй авторизоваться через VK и посмотри в консоль браузера (F12)")
print("   Там должны быть ошибки если что-то не так.")
print()
print("🔗 Тестовый URL для ручной проверки:")
print(f"   {auth_url}")
print()
