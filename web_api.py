#!/usr/bin/env python3
"""
AlBi Music Web API - v2.0
FastAPI backend для веб-версии с OAuth авторизацией (VK + Yandex)
Порт: 8001

НОВЫЕ ВОЗМОЖНОСТИ v2.0:
- Демо-система (45 сек демо → разблокировка за токен)
- YooKassa платежи с idempotency защитой
- Реферальная программа (+2 токена за друга, +5 за 5-го)
- Rate limiting и атомарное списание токенов
- Кросс-платформенная авторизация (Telegram/Yandex/VK)
"""

import os
import logging
import secrets
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

import config
from db_utils import execute_query_sync, init_db_pool_sync

# Настройка логирования (инициализация ПЕРЕД импортами)
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт Celery задач (опциональный для совместимости)
try:
    from celery_tasks import (
        generate_suno_music_sync,
        generate_suno_song_sync,
        generate_suno_lyrics_sync,
        generate_karaoke_task,
        generate_cover_task,
        generate_wav_task
    )
    # Алиасы для обратной совместимости
    generate_music_task = generate_suno_music_sync
    generate_song_task = generate_suno_song_sync
    CELERY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Celery tasks import failed: {e}. Generation endpoints will not work.")
    CELERY_AVAILABLE = False
    generate_music_task = None
    generate_song_task = None
    generate_suno_lyrics_sync = None
    generate_karaoke_task = None
    generate_cover_task = None
    generate_wav_task = None

# Импорт YooKassa (установить: pip install yookassa)
try:
    from yookassa import Configuration, Payment as YooKassaPayment
    YOOKASSA_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ YooKassa library not installed. Payments will not work.")
    YOOKASSA_AVAILABLE = False

# Инициализация FastAPI
app = FastAPI(
    title="AlBi Music Web API",
    description="Web API для генерации музыки через Suno AI",
    version="1.0.0"
)

# CORS - разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://albi-music.ru",
        "http://localhost:3000",  # Для разработки
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация БД
init_db_pool_sync()
logger.info("✅ Database pool initialized")

# JWT конфигурация
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 30  # 30 дней

# OAuth конфигурация
OAUTH_CONFIG = {
    "vk": {
        "app_id": config.VK_APP_ID,
        "client_secret": config.VK_CLIENT_SECRET,
        "auth_url": "https://oauth.vk.com/authorize",
        "token_url": "https://oauth.vk.com/access_token",
        "user_info_url": "https://api.vk.com/method/users.get",
        "redirect_uri": "https://albi-music.ru/auth/vk/callback"
    },
    "yandex": {
        "client_id": config.YANDEX_CLIENT_ID,
        "client_secret": config.YANDEX_CLIENT_SECRET,
        "auth_url": "https://oauth.yandex.ru/authorize",
        "token_url": "https://oauth.yandex.ru/token",
        "user_info_url": "https://login.yandex.ru/info",
        "redirect_uri": "https://albi-music.ru/auth/yandex/callback"
    }
}

# Хранилище state для OAuth (в продакшене использовать Redis)
oauth_states: Dict[str, Dict[str, Any]] = {}

# Security
security = HTTPBearer()


# ========================
# Модели данных (Pydantic)
# ========================

class UserInfo(BaseModel):
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    avatar_url: Optional[str] = None
    balance: int = 1


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserInfo


class GenerateMusicRequest(BaseModel):
    style: str
    is_song: bool = False


class GenerateSongRequest(BaseModel):
    lyrics: str
    genre: str
    custom_mode: bool = False


class GenerateLyricsRequest(BaseModel):
    idea: str


class UnlockTrackRequest(BaseModel):
    task_id: str

class VKIDAuthRequest(BaseModel):
    access_token: str
    user_id: int
    expires_in: int

class ReferralLinkRequest(BaseModel):
    pass  # Не требует параметров, генерируется на основе user_id



# ========================
# Утилиты
# ========================

def create_jwt_token(user_id: int, provider: str) -> str:
    """Создает JWT токен для пользователя"""
    payload = {
        "user_id": user_id,
        "provider": provider,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Проверяет и декодирует JWT токен"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Извлекает user_id из JWT токена"""
    token = credentials.credentials
    payload = verify_jwt_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload["user_id"]


def get_or_create_user(user_id: int, provider: str, username: str = None, first_name: str = None) -> UserInfo:
    """Получает или создает пользователя в БД"""
    try:
        # Проверяем существует ли пользователь
        result = execute_query_sync(
            "SELECT user_id, username, first_name, balance FROM users WHERE user_id = %s",
            (user_id,)
        )

        if result:
            row = result[0]
            return UserInfo(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                balance=row[3]
            )

        # Создаем нового пользователя
        execute_query_sync(
            """
            INSERT INTO users (user_id, username, first_name, balance, created_at, invited_by)
            VALUES (%s, %s, %s, 1, NOW(), NULL)
            """,
            (user_id, username, first_name)
        )

        logger.info(f"✅ Created new user: {user_id} via {provider}")

        return UserInfo(
            user_id=user_id,
            username=username,
            first_name=first_name,
            balance=1
        )

    except Exception as e:
        logger.error(f"❌ Error getting/creating user: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# ========================
# OAuth endpoints
# ========================

@app.get("/auth/{provider}/login")
async def oauth_login(provider: str):
    """
    Начало OAuth авторизации (VK или Yandex)
    Возвращает URL для перенаправления пользователя
    """
    if provider not in OAUTH_CONFIG:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    config = OAUTH_CONFIG[provider]

    # Генерируем state для защиты от CSRF
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "provider": provider,
        "created_at": datetime.utcnow()
    }

    # Формируем URL авторизации
    if provider == "vk":
        params = {
            "client_id": config["app_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "display": "page",
            "state": state,
            "v": "5.131"
        }
    else:  # yandex
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "state": state
        }

    auth_url = f"{config['auth_url']}?{urlencode(params)}"

    logger.info(f"🔐 OAuth login started: {provider}, state={state}")

    return JSONResponse({
        "auth_url": auth_url,
        "state": state
    })


@app.get("/auth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str):
    """
    Callback для OAuth авторизации
    Обменивает code на access_token и создает JWT токен
    """
    if provider not in OAUTH_CONFIG:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    # Проверяем state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Удаляем использованный state
    oauth_states.pop(state)

    config = OAUTH_CONFIG[provider]

    try:
        # Обмениваем code на access_token
        async with httpx.AsyncClient() as client:
            if provider == "vk":
                token_params = {
                    "client_id": config["app_id"],
                    "client_secret": config["client_secret"],
                    "redirect_uri": config["redirect_uri"],
                    "code": code
                }
                token_response = await client.post(config["token_url"], data=token_params)
                token_data = token_response.json()

                if "error" in token_data:
                    raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth error"))

                access_token = token_data["access_token"]
                vk_user_id = token_data["user_id"]

                # Получаем информацию о пользователе
                user_info_params = {
                    "access_token": access_token,
                    "user_ids": vk_user_id,
                    "fields": "photo_200",
                    "v": "5.131"
                }
                user_response = await client.get(config["user_info_url"], params=user_info_params)
                user_data = user_response.json()

                if "error" in user_data:
                    raise HTTPException(status_code=400, detail="Failed to get user info")

                user = user_data["response"][0]
                user_id = user["id"]
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                username = f"{first_name} {last_name}"
                avatar_url = user.get("photo_200")

            else:  # yandex
                token_params = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"]
                }
                token_response = await client.post(config["token_url"], data=token_params)
                token_data = token_response.json()

                if "error" in token_data:
                    raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth error"))

                access_token = token_data["access_token"]

                # Получаем информацию о пользователе
                headers = {"Authorization": f"OAuth {access_token}"}
                user_response = await client.get(config["user_info_url"], headers=headers)
                user_data = user_response.json()

                # Yandex ID возвращает строковый ID, преобразуем в числовой hash
                yandex_id = user_data["id"]
                user_id = int(hashlib.sha256(f"yandex_{yandex_id}".encode()).hexdigest()[:15], 16) % (10**9)

                first_name = user_data.get("first_name", "")
                last_name = user_data.get("last_name", "")
                username = f"{first_name} {last_name}" if first_name or last_name else user_data.get("display_name", "User")
                avatar_url = user_data.get("default_avatar_id")
                if avatar_url:
                    avatar_url = f"https://avatars.yandex.net/get-yapic/{avatar_url}/islands-200"

        # Создаем или получаем пользователя в БД
        user_info = get_or_create_user(user_id, provider, username, first_name)

        # Создаем JWT токен
        jwt_token = create_jwt_token(user_id, provider)

        logger.info(f"✅ OAuth successful: {provider}, user_id={user_id}")

        # Редирект на фронтенд с токеном
        frontend_url = f"https://albi-music.ru/app?token={jwt_token}"
        return RedirectResponse(url=frontend_url)

    except httpx.HTTPError as e:
        logger.error(f"❌ OAuth HTTP error: {e}")
        raise HTTPException(status_code=500, detail="OAuth provider error")
    except Exception as e:
        logger.error(f"❌ OAuth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")




# ========================
# VK ID Auth (NEW)
# ========================

@app.post("/api/auth/vk/token")
async def vk_id_auth(request: VKIDAuthRequest):
    """
    Новая авторизация через VK ID
    Принимает данные от VK ID SDK после exchangeCode и создаёт JWT токен
    """
    try:
        logger.info(f"🔐 VK ID auth: user_id={request.user_id}")

        # Получаем информацию о пользователе через VK API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.vk.com/method/users.get",
                params={
                    "user_ids": request.user_id,
                    "fields": "first_name,last_name",
                    "access_token": request.access_token,
                    "v": "5.131"
                },
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"VK API failed: {response.status_code} {response.text}")
                raise HTTPException(status_code=400, detail="VK API error")

            vk_data = response.json()

            if "error" in vk_data:
                logger.error(f"VK API error: {vk_data['error']}")
                raise HTTPException(status_code=400, detail="Invalid VK token")

            user_info_vk = vk_data.get("response", [{}])[0]

        # Извлекаем данные пользователя
        user_id = request.user_id
        first_name = user_info_vk.get("first_name", "")
        last_name = user_info_vk.get("last_name", "")
        username = f"{first_name} {last_name}".strip()

        logger.info(f"✅ VK user info: user_id={user_id}, name={username}")

        # Создаём/получаем пользователя в БД
        user_info = get_or_create_user(user_id, "vk", username, first_name)

        # Создаём наш JWT токен
        jwt_token = create_jwt_token(user_id, "vk")

        logger.info(f"✅ VK ID auth successful: user_id={user_id}")

        return JSONResponse({
            "access_token": jwt_token,
            "token_type": "bearer",
            "user_info": {
                "user_id": user_info.user_id,
                "username": user_info.username,
                "first_name": user_info.first_name,
                "balance": user_info.balance
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ VK ID auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


# ========================
# User endpoints
# ========================

@app.get("/api/user/me")
async def get_current_user_info(user_id: int = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    try:
        result = execute_query_sync(
            "SELECT user_id, username, first_name, balance FROM users WHERE user_id = %s",
            (user_id,)
        )

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        row = result[0]
        return UserInfo(
            user_id=row[0],
            username=row[1],
            first_name=row[2],
            balance=row[3]
        )

    except Exception as e:
        logger.error(f"❌ Error getting user info: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/user/balance")
async def get_user_balance(user_id: int = Depends(get_current_user)):
    """Получить баланс пользователя"""
    try:
        result = execute_query_sync(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )

        if not result:
            return JSONResponse({"balance": 1})

        return JSONResponse({"balance": result[0][0]})

    except Exception as e:
        logger.error(f"❌ Error getting balance: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# ========================
# Generation endpoints
# ========================

@app.post("/api/generate/music")
async def generate_music(request: GenerateMusicRequest, user_id: int = Depends(get_current_user)):
    """
    Генерация инструментальной музыки
    Использует атомарное списание токенов через PostgreSQL функцию
    """
    try:
        # Проверяем rate limit
        rate_check = execute_query_sync(
            "SELECT check_rate_limit(%s, %s, %s, %s)",
            (user_id, 'generate_music', 5, 1)
        )
        
        if not (rate_check and rate_check[0][0]):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait.")
        
        # Атомарно списываем токен и начинаем генерацию
        # (проверяет баланс, списывает токен, увеличивает счетчик активных генераций)
        if user_id != config.ADMIN_ID:
            deduct_result = execute_query_sync(
                "SELECT start_generation_safe(%s, %s, %s)",
                (user_id, 1, 3)  # cost=1, max_concurrent=3
            )
            
            if not (deduct_result and deduct_result[0][0]):
                raise HTTPException(status_code=402, detail="Insufficient balance or too many active generations")
        
        # Запускаем Celery задачу
        task = generate_music_task.delay(user_id, request.style)
        
        logger.info(f"✅ Music generation started: user={user_id}, task={task.id}")
        
        return JSONResponse({
            "task_id": task.id,
            "status": "pending",
            "message": "Генерация началась. Ожидайте результат."
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating music: {e}")
        # Возвращаем токен при ошибке
        if user_id != config.ADMIN_ID:
            execute_query_sync("SELECT refund_tokens(%s, %s, %s)", (user_id, 1, f"Generation error: {str(e)}"))
        raise HTTPException(status_code=500, detail="Generation failed")


@app.post("/api/generate/lyrics")
async def generate_lyrics(request: GenerateLyricsRequest, user_id: int = Depends(get_current_user)):
    """
    Генерация текста песни через AI (бесплатно, без списания токенов)
    Используется как помощник перед генерацией песни
    """
    try:
        # Rate limit для защиты от спама
        rate_check = execute_query_sync(
            "SELECT check_rate_limit(%s, %s, %s, %s)",
            (user_id, 'generate_lyrics', 10, 1)  # 10 запросов в минуту
        )
        
        if not (rate_check and rate_check[0][0]):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait.")
        
        # Генерируем текст синхронно (БЕЗ списания токенов)
        lyrics = generate_suno_lyrics_sync(request.idea[:200])
        
        if not lyrics:
            raise HTTPException(status_code=500, detail="Failed to generate lyrics")
        
        logger.info(f"✅ Lyrics generated: user={user_id}, length={len(lyrics)}")
        
        return JSONResponse({
            "lyrics": lyrics,
            "idea": request.idea
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating lyrics: {e}")
        raise HTTPException(status_code=500, detail="Generation failed")


@app.post("/api/generate/song")
async def generate_song(request: GenerateSongRequest, user_id: int = Depends(get_current_user)):
    """
    Генерация песни с текстом
    Использует атомарное списание токенов и rate limiting
    """
    try:
        # Проверяем rate limit
        rate_check = execute_query_sync(
            "SELECT check_rate_limit(%s, %s, %s, %s)",
            (user_id, 'generate_song', 5, 1)
        )
        
        if not (rate_check and rate_check[0][0]):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait.")
        
        # Атомарно списываем токен
        if user_id != config.ADMIN_ID:
            deduct_result = execute_query_sync(
                "SELECT start_generation_safe(%s, %s, %s)",
                (user_id, 1, 3)
            )
            
            if not (deduct_result and deduct_result[0][0]):
                raise HTTPException(status_code=402, detail="Insufficient balance or too many active generations")
        
        # Определяем custom_mode
        custom_mode = len(request.lyrics) > 500
        
        # Запускаем Celery задачу
        task = generate_song_task.delay(user_id, request.lyrics, request.genre, custom_mode)
        
        logger.info(f"✅ Song generation started: user={user_id}, task={task.id}, custom={custom_mode}")
        
        return JSONResponse({
            "task_id": task.id,
            "status": "pending",
            "message": "Генерация началась. Ожидайте результат.",
            "custom_mode": custom_mode
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating song: {e}")
        # Возвращаем токен при ошибке
        if user_id != config.ADMIN_ID:
            execute_query_sync("SELECT refund_tokens(%s, %s, %s)", (user_id, 1, f"Generation error: {str(e)}"))
        raise HTTPException(status_code=500, detail="Generation failed")


@app.get("/api/generation/{task_id}/status")
async def get_generation_status(task_id: str, user_id: int = Depends(get_current_user)):
    """Проверить статус генерации"""
    try:
        result = execute_query_sync(
            """
            SELECT status, audio_url, error_message, created_at
            FROM generations
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, user_id)
        )

        if not result:
            raise HTTPException(status_code=404, detail="Generation not found")

        row = result[0]
        status_value = row[0]
        audio_url = row[1]
        error_message = row[2]
        created_at = row[3]

        response_data = {
            "task_id": task_id,
            "status": status_value,
            "created_at": created_at.isoformat() if created_at else None
        }

        if status_value == "completed":
            # audio_url хранится как JSON массив для демо-системы
            try:
                urls = json.loads(audio_url) if isinstance(audio_url, str) else audio_url
                response_data["audio_urls"] = urls
                response_data["is_demo"] = True  # Всегда демо 45 сек
            except:
                response_data["audio_urls"] = [audio_url]
                response_data["is_demo"] = True
        elif status_value == "failed":
            response_data["error"] = error_message

        return JSONResponse(response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting generation status: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# ========================
# History endpoints
# ========================

@app.get("/api/history")
async def get_user_history(user_id: int = Depends(get_current_user), limit: int = 20):
    """Получить историю генераций пользователя"""
    try:
        result = execute_query_sync(
            """
            SELECT task_id, prompt, audio_url, status, created_at, custom_mode
            FROM generations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

        history = []
        for row in result:
            task_id, prompt, audio_url, status_value, created_at, custom_mode = row

            item = {
                "task_id": task_id,
                "prompt": prompt,
                "status": status_value,
                "created_at": created_at.isoformat() if created_at else None,
                "custom_mode": custom_mode
            }

            if status_value == "completed" and audio_url:
                try:
                    urls = json.loads(audio_url) if isinstance(audio_url, str) else audio_url
                    item["audio_urls"] = urls
                    item["is_demo"] = not audio_url.startswith("ALR_")
                except:
                    item["audio_urls"] = [audio_url]
                    item["is_demo"] = True

            history.append(item)

        return JSONResponse({"history": history})

    except Exception as e:
        logger.error(f"❌ Error getting history: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# ========================
# Unlock Track endpoint (DEMO → FULL)
# ========================

@app.post("/api/unlock/{task_id}")
async def unlock_track(task_id: str, user_id: int = Depends(get_current_user)):
    """
    Разблокировать полные версии трека (из демо 45 сек)
    Списывает 1 токен атомарно через PostgreSQL функцию
    """
    try:
        # Проверяем, существует ли трек и принадлежит ли он пользователю
        track_check = execute_query_sync(
            """
            SELECT audio_url, status FROM generations
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Track not found")
        
        audio_url, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Track is not ready yet")
        
        # Проверяем demo_tracks: уже разблокирован или нет
        demo_check = execute_query_sync(
            """
            SELECT is_unlocked, full_url_1, full_url_2
            FROM demo_tracks
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, user_id)
        )
        
        if demo_check:
            is_unlocked, full_url_1, full_url_2 = demo_check[0]
            
            if is_unlocked:
                # Уже разблокирован
                return JSONResponse({
                    "success": True,
                    "message": "Track already unlocked",
                    "audio_urls": [full_url_1, full_url_2]
                })
        
        # Атомарно списываем 1 токен через PostgreSQL функцию
        deduct_result = execute_query_sync(
            "SELECT deduct_tokens_atomic(%s, %s, %s)",
            (user_id, 1, 'unlock_track')
        )
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance")
        
        # Обновляем demo_tracks - помечаем как разблокированный
        execute_query_sync(
            """
            UPDATE demo_tracks
            SET is_unlocked = TRUE,
                unlocked_at = CURRENT_TIMESTAMP
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, user_id)
        )
        
        # Получаем полные URL
        full_urls_result = execute_query_sync(
            """
            SELECT full_url_1, full_url_2
            FROM demo_tracks
            WHERE task_id = %s AND user_id = %s
            """,
            (task_id, user_id)
        )
        
        if full_urls_result:
            full_url_1, full_url_2 = full_urls_result[0]
            
            logger.info(f"✅ Track unlocked: user={user_id}, task={task_id}")
            
            return JSONResponse({
                "success": True,
                "message": "Track unlocked successfully",
                "audio_urls": [full_url_1, full_url_2],
                "tokens_spent": 1
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve full tracks")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error unlocking track: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ========================
# Additional Audio Processing Endpoints
# (Минусовка, Кавер, WAV конвертация)
# ========================

class GenerateKaraokeRequest(BaseModel):
    task_id: str
    version: int = 0

class GenerateCoverRequest(BaseModel):
    task_id: str
    genre: str
    version: int = 0

class GenerateWAVRequest(BaseModel):
    task_id: str
    version: int = 0


@app.post("/api/karaoke/create")
async def create_karaoke(request: GenerateKaraokeRequest, user_id: int = Depends(get_current_user)):
    """Создать минусовку (инструментальную версию) из существующего трека. Стоимость: 1 токен"""
    if not CELERY_AVAILABLE or not generate_karaoke_task:
        raise HTTPException(status_code=503, detail="Karaoke service temporarily unavailable")
    
    try:
        track_check = execute_query_sync(
            "SELECT suno_task_id, suno_audio_id, prompt, status FROM generations WHERE task_id = %s AND user_id = %s",
            (request.task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Original track not found")
        
        suno_task_id, suno_audio_id, prompt, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Original track is not ready yet")
        
        if not suno_task_id or not suno_audio_id:
            raise HTTPException(status_code=400, detail="This track was created before the system update. Please create a new track.")
        
        deduct_result = execute_query_sync("SELECT deduct_tokens_atomic(%s, %s, %s)", (user_id, 1, 'create_karaoke'))
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance")
        
        new_task_id = str(uuid.uuid4())
        celery_task = generate_karaoke_task.apply_async(
            args=[user_id, request.task_id, request.version, new_task_id],
            queue='generation'
        )
        
        logger.info(f"🎤 Karaoke task created: user={user_id}, original={request.task_id}, new={new_task_id}")
        
        return JSONResponse({
            "success": True,
            "message": "Karaoke generation started",
            "task_id": new_task_id,
            "celery_task_id": celery_task.id,
            "estimated_time": "3-5 minutes"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating karaoke: {e}")
        try:
            execute_query_sync("UPDATE users SET balance = balance + 1 WHERE user_id = %s", (user_id,))
        except:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/cover/create")
async def create_cover(request: GenerateCoverRequest, user_id: int = Depends(get_current_user)):
    """Создать кавер (та же песня в другом жанре/стиле). Стоимость: 1 токен"""
    if not CELERY_AVAILABLE or not generate_cover_task:
        raise HTTPException(status_code=503, detail="Cover service temporarily unavailable")
    
    try:
        track_check = execute_query_sync(
            "SELECT suno_task_id, suno_audio_id, prompt, status FROM generations WHERE task_id = %s AND user_id = %s",
            (request.task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Original track not found")
        
        suno_task_id, suno_audio_id, prompt, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Original track is not ready yet")
        
        deduct_result = execute_query_sync("SELECT deduct_tokens_atomic(%s, %s, %s)", (user_id, 1, 'create_cover'))
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance")
        
        new_task_id = str(uuid.uuid4())
        celery_task = generate_cover_task.apply_async(
            args=[user_id, request.task_id, request.genre, request.version, new_task_id],
            queue='generation'
        )
        
        logger.info(f"🎸 Cover task created: user={user_id}, genre={request.genre}, new={new_task_id}")
        
        return JSONResponse({
            "success": True,
            "message": "Cover generation started",
            "task_id": new_task_id,
            "celery_task_id": celery_task.id,
            "genre": request.genre,
            "estimated_time": "2-3 minutes"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating cover: {e}")
        try:
            execute_query_sync("UPDATE users SET balance = balance + 1 WHERE user_id = %s", (user_id,))
        except:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/wav/convert")
async def convert_to_wav(request: GenerateWAVRequest, user_id: int = Depends(get_current_user)):
    """Конвертировать трек в WAV формат (высокое качество). Стоимость: 2 токена"""
    if not CELERY_AVAILABLE or not generate_wav_task:
        raise HTTPException(status_code=503, detail="WAV conversion service temporarily unavailable")
    
    try:
        track_check = execute_query_sync(
            "SELECT suno_task_id, suno_audio_id, prompt, status FROM generations WHERE task_id = %s AND user_id = %s",
            (request.task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Original track not found")
        
        suno_task_id, suno_audio_id, prompt, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Original track is not ready yet")
        
        if not suno_task_id or not suno_audio_id:
            raise HTTPException(status_code=400, detail="This track was created before the system update. Please create a new track.")
        
        deduct_result = execute_query_sync("SELECT deduct_tokens_atomic(%s, %s, %s)", (user_id, 2, 'convert_wav'))
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance (need 2 tokens)")
        
        new_task_id = str(uuid.uuid4())
        celery_task = generate_wav_task.apply_async(
            args=[user_id, request.task_id, request.version, new_task_id],
            queue='generation'
        )
        
        logger.info(f"🎵 WAV conversion task created: user={user_id}, original={request.task_id}, new={new_task_id}")
        
        return JSONResponse({
            "success": True,
            "message": "WAV conversion started",
            "task_id": new_task_id,
            "celery_task_id": celery_task.id,
            "estimated_time": "2-3 minutes",
            "tokens_spent": 2
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error converting to WAV: {e}")
        try:
            execute_query_sync("UPDATE users SET balance = balance + 2 WHERE user_id = %s", (user_id,))
        except:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")


# ========================
# Payment endpoints (YooKassa integration)
# ========================

class CreatePaymentRequest(BaseModel):
    amount: float  # Сумма в рублях (50, 250, 500, 1000, 2000)

class PaymentWebhookEvent(BaseModel):
    type: str
    event: str
    object: Dict[str, Any]


@app.get("/api/pricing")
async def get_pricing():
    """Получить тарифные планы"""
    try:
        result = execute_query_sync(
            """
            SELECT amount, tokens, currency
            FROM pricing_plans
            WHERE is_active = TRUE
            ORDER BY amount ASC
            """
        )
        
        plans = []
        for row in result:
            amount, tokens, currency = row
            plans.append({
                "amount": float(amount),
                "tokens": tokens,
                "currency": currency
            })
        
        return JSONResponse({"plans": plans})
    
    except Exception as e:
        logger.error(f"❌ Error getting pricing: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/api/payment/create")
async def create_payment(request: CreatePaymentRequest, user_id: int = Depends(get_current_user)):
    """Создать платеж через YooKassa"""
    try:
        from yookassa import Configuration, Payment as YooKassaPayment
        import uuid
        
        # Настраиваем YooKassa
        Configuration.account_id = config.YOOKASSA_SHOP_ID
        Configuration.secret_key = config.YOOKASSA_SECRET_KEY
        
        # Определяем количество токенов по сумме
        pricing_map = {
            50: 1,
            250: 10,
            500: 25,
            1000: 60,
            2000: 140
        }
        
        tokens_amount = pricing_map.get(int(request.amount))
        if not tokens_amount:
            raise HTTPException(status_code=400, detail="Invalid payment amount")
        
        # Создаем idempotency key
        idempotency_key = str(uuid.uuid4())
        
        # Создаем платеж в YooKassa
        payment = YooKassaPayment.create({
            "amount": {
                "value": f"{request.amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://albi-music.ru/app/?payment=success"
            },
            "capture": True,
            "description": f"Пополнение баланса: {tokens_amount} токенов",
            "metadata": {
                "user_id": user_id,
                "tokens": tokens_amount,
                "source": "web"  # Маркер: платеж с веб-сайта
            }
        }, idempotency_key)
        
        # Сохраняем платеж в БД
        execute_query_sync(
            """
            INSERT INTO payments (user_id, amount, tokens_amount, status, payment_id, provider, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, request.amount, tokens_amount, 'pending', payment.id, 'yookassa', json.dumps({
                "idempotency_key": idempotency_key
            }))
        )
        
        logger.info(f"✅ Payment created: user={user_id}, amount={request.amount}, payment_id={payment.id}")
        
        return JSONResponse({
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "amount": request.amount,
            "tokens": tokens_amount
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")


@app.post("/api/payment/webhook")
async def payment_webhook(request: Request):
    """
    Webhook для обработки уведомлений от YooKassa
    Использует idempotency для защиты от повторного начисления
    """
    try:
        # Получаем тело запроса
        body = await request.json()
        
        event_type = body.get("event")
        payment_obj = body.get("object", {})
        payment_id = payment_obj.get("id")
        payment_status = payment_obj.get("status")
        
        logger.info(f"📥 Payment webhook: event={event_type}, payment_id={payment_id}, status={payment_status}")
        
        # Обрабатываем только успешные платежи
        if event_type == "payment.succeeded" and payment_status == "succeeded":
            # Извлекаем данные
            amount = float(payment_obj.get("amount", {}).get("value", 0))
            metadata = payment_obj.get("metadata", {})
            user_id = int(metadata.get("user_id", 0))
            tokens = int(metadata.get("tokens", 0))
            
            if not user_id or not tokens:
                logger.error(f"❌ Invalid metadata in payment {payment_id}")
                return JSONResponse({"status": "error", "message": "Invalid metadata"})
            
            # Используем idempotent функцию PostgreSQL
            process_result = execute_query_sync(
                "SELECT process_payment_idempotent(%s, %s, %s, %s, %s)",
                (payment_id, user_id, amount, tokens, 'yookassa')
            )
            
            if process_result and process_result[0][0]:
                logger.info(f"✅ Payment processed: user={user_id}, tokens={tokens}, payment_id={payment_id}")
            else:
                logger.info(f"⏭️ Payment already processed (idempotency): payment_id={payment_id}")
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        # Возвращаем 200 чтобы YooKassa не повторял запрос
        return JSONResponse({"status": "error", "message": str(e)})


# ========================
# Referral System endpoints
# ========================

@app.get("/api/referral/link")
async def get_referral_link(user_id: int = Depends(get_current_user)):
    """Получить реферальную ссылку пользователя"""
    try:
        # Генерируем реферальную ссылку
        ref_code = f"ref_{user_id}"
        referral_url = f"https://albi-music.ru/app/?ref={ref_code}"
        
        # Получаем статистику рефералов
        referrals_result = execute_query_sync(
            """
            SELECT COUNT(*), COALESCE(SUM(CASE WHEN bonus_paid THEN 1 ELSE 0 END), 0)
            FROM referrals
            WHERE referrer_id = %s
            """,
            (user_id,)
        )
        
        total_referrals = 0
        paid_referrals = 0
        
        if referrals_result:
            total_referrals = referrals_result[0][0] or 0
            paid_referrals = referrals_result[0][1] or 0
        
        return JSONResponse({
            "referral_url": referral_url,
            "ref_code": ref_code,
            "total_invited": total_referrals,
            "tokens_earned": paid_referrals * 2,  # 2 токена за каждого
            "bonus_5th_received": total_referrals >= 5
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting referral link: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/referral/stats")
async def get_referral_stats(user_id: int = Depends(get_current_user)):
    """Получить детальную статистику рефералов"""
    try:
        # Получаем список приглашенных пользователей
        referrals_list = execute_query_sync(
            """
            SELECT r.referred_id, u.first_name, r.created_at, r.bonus_paid
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = %s
            ORDER BY r.created_at DESC
            LIMIT 50
            """,
            (user_id,)
        )
        
        invited_users = []
        for row in referrals_list:
            referred_id, first_name, created_at, bonus_paid = row
            invited_users.append({
                "user_id": referred_id,
                "name": first_name or f"User {referred_id}",
                "joined_at": created_at.isoformat() if created_at else None,
                "bonus_received": bonus_paid
            })
        
        return JSONResponse({
            "invited_users": invited_users,
            "total_count": len(invited_users)
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting referral stats: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/api/referral/register")
async def register_referral(ref_code: str, user_id: int = Depends(get_current_user)):
    """
    Зарегистрировать пользователя как реферала
    Вызывается при первом входе пользователя с ?ref= параметром
    """
    try:
        # Извлекаем referrer_id из ref_code (формат: ref_12345)
        if not ref_code.startswith("ref_"):
            raise HTTPException(status_code=400, detail="Invalid referral code")
        
        referrer_id = int(ref_code[4:])
        
        # Проверяем, что пользователь не пытается пригласить сам себя
        if referrer_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot refer yourself")
        
        # Проверяем, что пользователь еще не был приглашен
        existing_ref = execute_query_sync(
            "SELECT id FROM referrals WHERE referred_id = %s",
            (user_id,)
        )
        
        if existing_ref:
            return JSONResponse({
                "success": False,
                "message": "User already has a referrer"
            })
        
        # Создаем реферальную связь
        execute_query_sync(
            """
            INSERT INTO referrals (referrer_id, referred_id, bonus_paid)
            VALUES (%s, %s, TRUE)
            """,
            (referrer_id, user_id)
        )
        
        # Начисляем 2 токена рефереру
        execute_query_sync(
            """
            UPDATE users
            SET balance = balance + 2
            WHERE user_id = %s
            """,
            (referrer_id,)
        )
        
        # Логируем транзакцию
        execute_query_sync(
            """
            INSERT INTO token_transactions (user_id, amount, transaction_type, description)
            VALUES (%s, %s, %s, %s)
            """,
            (referrer_id, 2, 'credit', f'Referral bonus for user {user_id}')
        )
        
        # Проверяем, не 5-й ли это друг (бонус +5 токенов)
        referral_count_result = execute_query_sync(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = %s",
            (referrer_id,)
        )
        
        if referral_count_result and referral_count_result[0][0] == 5:
            # Начисляем бонус за 5-го друга
            execute_query_sync(
                """
                UPDATE users
                SET balance = balance + 5,
                    referral_bonus_given = TRUE
                WHERE user_id = %s
                """,
                (referrer_id,)
            )
            
            # Логируем бонусную транзакцию
            execute_query_sync(
                """
                INSERT INTO token_transactions (user_id, amount, transaction_type, description)
                VALUES (%s, %s, %s, %s)
                """,
                (referrer_id, 5, 'credit', 'Bonus for 5th referral')
            )
            
            logger.info(f"🎁 5th referral bonus awarded: user={referrer_id}")
        
        logger.info(f"✅ Referral registered: referrer={referrer_id}, referred={user_id}")
        
        return JSONResponse({
            "success": True,
            "message": "Referral registered successfully",
            "tokens_awarded": 2
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registering referral: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Security & Rate Limiting endpoints
# ========================

@app.post("/api/check-rate-limit")
async def check_rate_limit_endpoint(
    action_type: str,
    user_id: int = Depends(get_current_user)
):
    """
    Проверить rate limit для действия (используется frontend перед запросом)
    Возвращает: можно ли выполнить действие
    """
    try:
        # Вызываем PostgreSQL функцию check_rate_limit
        result = execute_query_sync(
            "SELECT check_rate_limit(%s, %s, %s, %s)",
            (user_id, action_type, 5, 1)  # 5 запросов в минуту
        )
        
        can_proceed = result[0][0] if result else False
        
        if not can_proceed:
            return JSONResponse({
                "allowed": False,
                "message": "Rate limit exceeded. Please wait a moment.",
                "retry_after": 60  # секунд
            }, status_code=429)
        
        return JSONResponse({
            "allowed": True
        })
    
    except Exception as e:
        logger.error(f"❌ Error checking rate limit: {e}")
        # В случае ошибки разрешаем действие (fail-open)
        return JSONResponse({"allowed": True})


# ========================
# Health check
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "service": "AlBi Music Web API",
        "version": "2.0.0"
    })


# ========================
# Startup
# ========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
