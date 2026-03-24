#!/bin/bash
echo "🔍 Проверка статуса SunoAPI.org: $(date)"

# Проверяем доступность API
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer 615290cfecdf58e6251835ba7971ab65" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","customMode":false,"instrumental":false,"model":"V5","callBackUrl":"https://example.com/callback"}' \
  https://api.sunoapi.org/api/v1/generate)

if [ "$response" = "200" ]; then
    echo "✅ API доступен! (HTTP $response)"
elif [ "$response" = "503" ]; then
    echo "❌ API временно недоступен (HTTP $response)"
else
    echo "⚠️  API возвращает: HTTP $response"
fi
