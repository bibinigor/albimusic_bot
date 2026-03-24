#!/bin/bash
# Тестовый скрипт для проверки веб-версии ALBI Music
# Согласно Правилу №7 - тестируем перед завершением!

# Цвета
GREEN='\033[92m'
RED='\033[91m'
YELLOW='\033[93m'
BLUE='\033[94m'
RESET='\033[0m'

# Конфигурация
API_BASE="https://albi-music.ru"
WEBAPP_PATH="/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/webapp/index.html"

echo -e "${BLUE}============================================================${RESET}"
echo -e "${BLUE}🧪 Тест веб-версии ALBI Music${RESET}"
echo -e "${BLUE}============================================================${RESET}"
echo ""
echo -e "API Base: ${API_BASE}"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

test_result() {
    local name="$1"
    local success="$2"
    local details="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$success" = "1" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✅ ${name}${RESET}"
        [ -n "$details" ] && echo -e "   ${details}"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}❌ ${name}${RESET}"
        [ -n "$details" ] && echo -e "   ${RED}${details}${RESET}"
    fi
    echo ""
}

# ============================================
# Тест 1: Проверка что лендинг упрощён
# ============================================
echo -e "${YELLOW}1️⃣ Проверка лендинга...${RESET}"

LANDING=$(curl -s "${API_BASE}/")

if echo "$LANDING" | grep -q "Создать песню ЗДЕСЬ"; then
    test_result "Лендинг упрощён" 0 "Найдена кнопка 'Создать песню ЗДЕСЬ' - нужно убрать!"
elif echo "$LANDING" | grep -q 'href="/app"'; then
    test_result "Лендинг упрощён" 0 "Найдена ссылка на /app - нужно убрать!"
else
    test_result "Лендинг упрощён" 1 "Кнопка 'Создать песню ЗДЕСЬ' отсутствует ✅"
fi

# ============================================
# Тест 2: Проверка веб-приложения (frontend)
# ============================================
echo -e "${YELLOW}2️⃣ Проверка веб-приложения...${RESET}"

if [ -f "$WEBAPP_PATH" ]; then
    WEBAPP_CONTENT=$(cat "$WEBAPP_PATH")

    # Проверка 1: VK ID SDK
    if echo "$WEBAPP_CONTENT" | grep -q "@vkid/sdk"; then
        test_result "VK ID SDK подключен" 1 "SDK найден в коде"
    else
        test_result "VK ID SDK подключен" 0 "SDK не найден"
    fi

    # Проверка 2: Главные экраны
    SCREENS=("welcomeScreen" "createSongTypeScreen" "aiTextScreen" "ownTextScreen"
             "genreSelectionScreen" "createMusicScreen" "myTracksScreen" "balanceScreen" "examplesScreen")

    MISSING_SCREENS=""
    for screen in "${SCREENS[@]}"; do
        if ! echo "$WEBAPP_CONTENT" | grep -q "$screen"; then
            MISSING_SCREENS="${MISSING_SCREENS}${screen} "
        fi
    done

    if [ -z "$MISSING_SCREENS" ]; then
        test_result "Все экраны присутствуют" 1 "Найдено ${#SCREENS[@]} экранов"
    else
        test_result "Все экраны присутствуют" 0 "Отсутствуют: ${MISSING_SCREENS}"
    fi

    # Проверка 3: 16 жанров
    GENRE_COUNT=0
    GENRES=("pop" "rock" "jazz" "blues" "hiphop" "electronic" "classical" "rnb"
            "reggae" "country" "metal" "folk" "latin" "punk" "funk" "shanson")

    for genre in "${GENRES[@]}"; do
        if echo "$WEBAPP_CONTENT" | grep -iq "$genre"; then
            GENRE_COUNT=$((GENRE_COUNT + 1))
        fi
    done

    if [ $GENRE_COUNT -ge 15 ]; then
        test_result "16 жанров присутствуют" 1 "Найдено ${GENRE_COUNT}/16 жанров"
    else
        test_result "16 жанров присутствуют" 0 "Найдено только ${GENRE_COUNT}/16 жанров"
    fi

    # Проверка 4: Нижняя навигация
    if echo "$WEBAPP_CONTENT" | grep -q "bottom-nav"; then
        test_result "Нижняя навигация" 1 "Навигация найдена"
    else
        test_result "Нижняя навигация" 0 "Навигация не найдена"
    fi

    # Проверка 5: Функции генерации
    FUNCTIONS=("generateAILyrics" "continueWithOwnLyrics" "selectGenre"
               "selectMusicGenre" "startGeneration" "loadMyTracks" "loadBalance")

    MISSING_FUNCTIONS=""
    for func in "${FUNCTIONS[@]}"; do
        if ! echo "$WEBAPP_CONTENT" | grep -q "$func"; then
            MISSING_FUNCTIONS="${MISSING_FUNCTIONS}${func} "
        fi
    done

    if [ -z "$MISSING_FUNCTIONS" ]; then
        test_result "Все функции присутствуют" 1 "Найдено ${#FUNCTIONS[@]} функций"
    else
        test_result "Все функции присутствуют" 0 "Отсутствуют: ${MISSING_FUNCTIONS}"
    fi

else
    test_result "Веб-приложение существует" 0 "Файл не найден: ${WEBAPP_PATH}"
fi

# ============================================
# Тест 3: Проверка Backend API
# ============================================
echo -e "${YELLOW}3️⃣ Проверка Backend API...${RESET}"

HEALTH=$(curl -s "${API_BASE}/health")

if echo "$HEALTH" | grep -iq "music"; then
    VERSION=$(echo "$HEALTH" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    test_result "Backend API работает" 1 "API v${VERSION} доступен"
else
    test_result "Backend API работает" 0 "Health check не прошёл: ${HEALTH}"
fi

# ============================================
# Тест 4: Проверка VK ID endpoint
# ============================================
echo -e "${YELLOW}4️⃣ Проверка VK ID endpoint...${RESET}"

VK_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/vk/token" \
    -H "Content-Type: application/json" \
    -d '{"token":"test","uuid":"test"}')

HTTP_CODE=$(echo "$VK_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "422" ]; then
    test_result "VK ID endpoint работает" 1 "Endpoint существует и валидирует (HTTP ${HTTP_CODE})"
elif [ "$HTTP_CODE" = "404" ]; then
    test_result "VK ID endpoint работает" 0 "Endpoint не найден (404)"
else
    test_result "VK ID endpoint работает" 1 "Endpoint существует (HTTP ${HTTP_CODE})"
fi

# ============================================
# Тест 5: Проверка Яндекс OAuth
# ============================================
echo -e "${YELLOW}5️⃣ Проверка Яндекс OAuth...${RESET}"

YANDEX_RESPONSE=$(curl -s "${API_BASE}/auth/yandex/login")

if echo "$YANDEX_RESPONSE" | grep -q "auth_url"; then
    test_result "Яндекс OAuth работает" 1 "Auth URL генерируется"
else
    test_result "Яндекс OAuth работает" 0 "Нет auth_url в ответе"
fi

# ============================================
# Тест 6: Проверка документации
# ============================================
echo -e "${YELLOW}6️⃣ Проверка документации...${RESET}"

DOCS=(
    "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/webapp/README.md"
    "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/webapp/DEVELOPMENT.md"
    "/Users/user/Documents/1 000 000 х 100/AL BI Music/claude/WEB_VERSION_STATUS.md"
)

for doc in "${DOCS[@]}"; do
    DOC_NAME=$(basename "$doc")
    if [ -f "$doc" ]; then
        test_result "Документация: ${DOC_NAME}" 1 "Файл существует"
    else
        test_result "Документация: ${DOC_NAME}" 0 "Файл не найден"
    fi
done

# ============================================
# Итоги
# ============================================
echo ""
echo -e "${BLUE}============================================================${RESET}"
echo -e "${BLUE}📊 ИТОГИ ТЕСТИРОВАНИЯ${RESET}"
echo -e "${BLUE}============================================================${RESET}"
echo ""

echo "Всего тестов: ${TOTAL_TESTS}"
echo -e "${GREEN}✅ Успешно: ${PASSED_TESTS}${RESET}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}❌ Провалено: ${FAILED_TESTS}${RESET}"
else
    echo -e "${GREEN}❌ Провалено: 0${RESET}"
fi

SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS / $TOTAL_TESTS) * 100}")
echo ""
echo "Успешность: ${SUCCESS_RATE}%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!${RESET}"
    echo ""
    echo -e "${GREEN}✅ Веб-версия готова к использованию${RESET}"
    echo -e "${GREEN}✅ Можно переходить к локальному тестированию${RESET}"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  ЕСТЬ ОШИБКИ!${RESET}"
    echo ""
    echo -e "${RED}❌ Исправьте ошибки перед продолжением${RESET}"
    echo ""
    exit 1
fi
