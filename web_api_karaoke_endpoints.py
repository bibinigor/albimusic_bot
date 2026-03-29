# ========================
# Additional Audio Processing Endpoints
# Добавить в web_api.py после @app.post("/api/unlock/{task_id}")
# ========================

# Pydantic модели для запросов
class GenerateKaraokeRequest(BaseModel):
    task_id: str  # ID оригинального трека
    version: int = 0  # Версия (0 или 1)

class GenerateCoverRequest(BaseModel):
    task_id: str  # ID оригинального трека
    genre: str  # Новый жанр для кавера
    version: int = 0  # Версия (0 или 1)

class GenerateWAVRequest(BaseModel):
    task_id: str  # ID оригинального трека
    version: int = 0  # Версия (0 или 1)


# ========================
# Karaoke (Минусовка) endpoint
# ========================

@app.post("/api/karaoke/create")
async def create_karaoke(request: GenerateKaraokeRequest, user_id: int = Depends(get_current_user)):
    """
    Создать минусовку (инструментальную версию) из существующего трека
    Стоимость: 1 токен
    """
    if not CELERY_AVAILABLE or not generate_karaoke_task:
        raise HTTPException(status_code=503, detail="Karaoke service temporarily unavailable")
    
    try:
        # Проверяем, что трек существует и принадлежит пользователю
        track_check = execute_query_sync(
            """
            SELECT suno_task_id, suno_audio_id, prompt, status 
            FROM generations
            WHERE task_id = %s AND user_id = %s
            """,
            (request.task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Original track not found")
        
        suno_task_id, suno_audio_id, prompt, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Original track is not ready yet")
        
        if not suno_task_id or not suno_audio_id:
            raise HTTPException(
                status_code=400, 
                detail="This track was created before the system update. Please create a new track."
            )
        
        # Атомарно списываем 1 токен
        deduct_result = execute_query_sync(
            "SELECT deduct_tokens_atomic(%s, %s, %s)",
            (user_id, 1, 'create_karaoke')
        )
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance")
        
        # Создаем новую задачу
        new_task_id = str(uuid.uuid4())
        
        # Запускаем Celery task АСИНХРОННО
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
        # Возврат токена при ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
        except:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")


# ========================
# Cover (Кавер) endpoint
# ========================

@app.post("/api/cover/create")
async def create_cover(request: GenerateCoverRequest, user_id: int = Depends(get_current_user)):
    """
    Создать кавер (та же песня в другом жанре/стиле)
    Стоимость: 1 токен
    """
    if not CELERY_AVAILABLE or not generate_cover_task:
        raise HTTPException(status_code=503, detail="Cover service temporarily unavailable")
    
    try:
        # Проверяем, что трек существует и принадлежит пользователю
        track_check = execute_query_sync(
            """
            SELECT suno_task_id, suno_audio_id, prompt, status 
            FROM generations
            WHERE task_id = %s AND user_id = %s
            """,
            (request.task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Original track not found")
        
        suno_task_id, suno_audio_id, prompt, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Original track is not ready yet")
        
        # Атомарно списываем 1 токен
        deduct_result = execute_query_sync(
            "SELECT deduct_tokens_atomic(%s, %s, %s)",
            (user_id, 1, 'create_cover')
        )
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance")
        
        # Создаем новую задачу
        new_task_id = str(uuid.uuid4())
        
        # Запускаем Celery task АСИНХРОННО
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
        # Возврат токена при ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1 WHERE user_id = %s",
                (user_id,)
            )
        except:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")


# ========================
# WAV Conversion endpoint
# ========================

@app.post("/api/wav/convert")
async def convert_to_wav(request: GenerateWAVRequest, user_id: int = Depends(get_current_user)):
    """
    Конвертировать трек в WAV формат (высокое качество)
    Стоимость: 2 токена
    """
    if not CELERY_AVAILABLE or not generate_wav_task:
        raise HTTPException(status_code=503, detail="WAV conversion service temporarily unavailable")
    
    try:
        # Проверяем, что трек существует и принадлежит пользователю
        track_check = execute_query_sync(
            """
            SELECT suno_task_id, suno_audio_id, prompt, status 
            FROM generations
            WHERE task_id = %s AND user_id = %s
            """,
            (request.task_id, user_id)
        )
        
        if not track_check:
            raise HTTPException(status_code=404, detail="Original track not found")
        
        suno_task_id, suno_audio_id, prompt, status = track_check[0]
        
        if status != "completed":
            raise HTTPException(status_code=400, detail="Original track is not ready yet")
        
        if not suno_task_id or not suno_audio_id:
            raise HTTPException(
                status_code=400, 
                detail="This track was created before the system update. Please create a new track."
            )
        
        # Атомарно списываем 2 токена (WAV дороже)
        deduct_result = execute_query_sync(
            "SELECT deduct_tokens_atomic(%s, %s, %s)",
            (user_id, 2, 'convert_wav')
        )
        
        if not deduct_result or not deduct_result[0][0]:
            raise HTTPException(status_code=402, detail="Insufficient balance (need 2 tokens)")
        
        # Создаем новую задачу
        new_task_id = str(uuid.uuid4())
        
        # Запускаем Celery task АСИНХРОННО
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
        # Возврат 2 токенов при ошибке
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                (user_id,)
            )
        except:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")
