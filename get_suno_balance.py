import requests
import config
import logging

async def get_suno_api_balance():
    """Получить баланс кредитов Suno API"""
    try:
        headers = {
            "Authorization": f"Bearer {config.SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{config.SUNO_API_URL}/account/balance", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'balance': data.get('credits', 0),
                'total_used': data.get('total_used', 0),
                'lifetime_credits': data.get('lifetime_credits', 0)
            }
        else:
            logging.error(f"❌ Ошибка получения баланса Suno: {response.status_code} - {response.text}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к Suno API: {e}")
        return {'success': False, 'error': str(e)}

# Тестируем функцию
if __name__ == "__main__":
    import asyncio
    result = asyncio.run(get_suno_api_balance())
    print("Баланс Suno API:", result)
