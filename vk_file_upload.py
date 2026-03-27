"""
Модуль загрузки файлов для VK-бота
Обработка аудиофайлов для кавера и минусовки
"""
import os
import logging
import tempfile
import subprocess
from typing import Tuple, Optional
from vk_api import VkUpload
import requests

logger = logging.getLogger(__name__)

def download_vk_audio(vk, doc_info) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Скачать аудиофайл из VK
    
    Args:
        vk: VK API объект
        doc_info: Информация о документе из сообщения
        
    Returns:
        Tuple (успех, путь к файлу, сообщение об ошибке)
    """
    try:
        # Получаем URL файла
        file_url = doc_info.get('url')
        if not file_url:
            return False, None, "Не удалось получить URL файла"
        
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp()
        file_id = doc_info.get('id', 'unknown')
        local_path = os.path.join(temp_dir, f"vk_audio_{file_id}.mp3")
        
        # Скачиваем файл
        response = requests.get(file_url, timeout=60)
        response.raise_for_status()
        
        # Сохраняем файл
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ Файл скачан: {local_path} ({len(response.content)} байт)")
        return True, local_path, None
        
    except requests.exceptions.Timeout:
        return False, None, "Таймаут при скачивании файла (>60 сек)"
    except requests.exceptions.RequestException as e:
        return False, None, f"Ошибка сети при скачивании: {str(e)[:100]}"
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания файла: {e}")
        return False, None, f"Ошибка скачивания: {str(e)[:100]}"


def check_audio_duration(file_path: str, max_duration: int = 300) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Проверить длительность аудиофайла через ffprobe
    
    Args:
        file_path: Путь к файлу
        max_duration: Максимальная длительность в секундах (по умолчанию 5 минут)
        
    Returns:
        Tuple (валидный, длительность в секундах, сообщение об ошибке)
    """
    try:
        # Проверяем наличие ffprobe
        result = subprocess.run(
            ['which', 'ffprobe'],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("⚠️ ffprobe не найден, пропускаем проверку длительности")
            return True, None, None
        
        # Получаем длительность через ffprobe
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️ ffprobe вернул ошибку: {result.stderr}")
            return True, None, None  # Пропускаем проверку при ошибке
        
        duration = float(result.stdout.strip())
        
        if duration > max_duration:
            return False, duration, f"Файл слишком длинный: {int(duration)} сек (максимум {max_duration} сек)"
        
        logger.info(f"✅ Длительность файла: {duration:.1f} сек (валидно)")
        return True, duration, None
        
    except subprocess.TimeoutExpired:
        logger.warning("⚠️ Таймаут ffprobe, пропускаем проверку")
        return True, None, None
    except Exception as e:
        logger.warning(f"⚠️ Ошибка проверки длительности: {e}, пропускаем проверку")
        return True, None, None


def check_audio_size(file_path: str, max_size_mb: int = 20) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Проверить размер файла
    
    Args:
        file_path: Путь к файлу
        max_size_mb: Максимальный размер в МБ
        
    Returns:
        Tuple (валидный, размер в байтах, сообщение об ошибке)
    """
    try:
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, file_size, f"Файл слишком большой: {file_size / 1024 / 1024:.1f} МБ (максимум {max_size_mb} МБ)"
        
        logger.info(f"✅ Размер файла: {file_size / 1024 / 1024:.1f} МБ (валидно)")
        return True, file_size, None
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки размера: {e}")
        return False, None, f"Ошибка проверки размера: {e}"


def upload_audio_to_server(file_path: str, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Загрузить аудиофайл на сервер
    
    Поддерживаемые методы (выбирается автоматически по config):
    1. Локальное хранилище + nginx (LOCAL_STORAGE_PATH)
    2. S3-совместимое хранилище (S3_BUCKET)
    3. HTTP POST на внешний сервер (UPLOAD_SERVER_URL)
    
    Args:
        file_path: Путь к локальному файлу
        filename: Имя файла на сервере
        
    Returns:
        Tuple (успех, URL файла, сообщение об ошибке)
    """
    try:
        import shutil
        from config import (
            LOCAL_STORAGE_PATH,
            S3_BUCKET,
            S3_ACCESS_KEY,
            S3_SECRET_KEY,
            S3_ENDPOINT,
            UPLOAD_SERVER_URL,
            DOMAIN
        )
        
        # ВАРИАНТ 1: Локальное хранилище (рекомендуется для начала)
        if LOCAL_STORAGE_PATH := os.getenv('LOCAL_STORAGE_PATH', '/var/www/uploads/audio'):
            try:
                # Создаем директорию если нет
                os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
                
                # Копируем файл
                dest_path = os.path.join(LOCAL_STORAGE_PATH, filename)
                shutil.copy2(file_path, dest_path)
                
                # Устанавливаем права
                os.chmod(dest_path, 0o644)
                
                # Формируем URL
                domain = os.getenv('DOMAIN', 'your-domain.com')
                file_url = f"https://{domain}/uploads/audio/{filename}"
                
                logger.info(f"✅ Файл загружен локально: {file_url}")
                return True, file_url, None
                
            except Exception as e:
                logger.error(f"❌ Ошибка локальной загрузки: {e}")
                # Fallback на следующий метод
        
        # ВАРИАНТ 2: S3-совместимое хранилище (AWS S3, MinIO, Yandex Object Storage)
        if S3_BUCKET := os.getenv('S3_BUCKET'):
            try:
                import boto3
                from botocore.client import Config
                
                # Создаем S3 клиент
                s3_client = boto3.client(
                    's3',
                    endpoint_url=os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com'),
                    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
                    aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
                    config=Config(signature_version='s3v4')
                )
                
                # Загружаем файл
                key = f"audio/{filename}"
                s3_client.upload_file(
                    file_path,
                    S3_BUCKET,
                    key,
                    ExtraArgs={'ContentType': 'audio/mpeg', 'ACL': 'public-read'}
                )
                
                # Формируем URL
                file_url = f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{S3_BUCKET}/{key}"
                
                logger.info(f"✅ Файл загружен в S3: {file_url}")
                return True, file_url, None
                
            except Exception as e:
                logger.error(f"❌ Ошибка S3 загрузки: {e}")
                # Fallback на следующий метод
        
        # ВАРИАНТ 3: HTTP POST на внешний сервер загрузки
        if UPLOAD_SERVER_URL := os.getenv('UPLOAD_SERVER_URL'):
            try:
                import requests
                
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f, 'audio/mpeg')}
                    response = requests.post(
                        UPLOAD_SERVER_URL,
                        files=files,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    file_url = result.get('url')
                    
                    if file_url:
                        logger.info(f"✅ Файл загружен через HTTP: {file_url}")
                        return True, file_url, None
                
                raise Exception(f"HTTP {response.status_code}: {response.text[:100]}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка HTTP загрузки: {e}")
        
        # Если ни один метод не настроен - возвращаем ошибку
        error_msg = (
            "⚠️ Не настроен метод загрузки файлов!\n"
            "Установите одну из переменных:\n"
            "- LOCAL_STORAGE_PATH=/var/www/uploads/audio\n"
            "- S3_BUCKET=your-bucket\n"
            "- UPLOAD_SERVER_URL=https://your-server.com/upload"
        )
        logger.error(error_msg)
        return False, None, error_msg
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка загрузки: {e}")
        return False, None, f"Ошибка загрузки: {str(e)[:100]}"


def process_uploaded_audio(
    vk,
    doc_info,
    max_duration: int = 300,
    max_size_mb: int = 20
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Полная обработка загруженного аудиофайла
    
    Args:
        vk: VK API объект
        doc_info: Информация о документе из сообщения
        max_duration: Максимальная длительность в секундах
        max_size_mb: Максимальный размер в МБ
        
    Returns:
        Tuple (успех, URL на сервере, локальный путь для удаления, сообщение об ошибке)
    """
    local_path = None
    
    try:
        # Шаг 1: Скачиваем файл из VK
        success, local_path, error = download_vk_audio(vk, doc_info)
        if not success:
            return False, None, None, error
        
        # Шаг 2: Проверяем размер файла
        valid, file_size, error = check_audio_size(local_path, max_size_mb)
        if not valid:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
            return False, None, None, error
        
        # Шаг 3: Проверяем длительность
        valid, duration, error = check_audio_duration(local_path, max_duration)
        if not valid:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
            return False, None, None, error
        
        # Шаг 4: Загружаем на сервер
        filename = f"{doc_info.get('id', 'unknown')}_{int(os.time.time())}.mp3"
        success, server_url, error = upload_audio_to_server(local_path, filename)
        if not success:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
            return False, None, None, error
        
        logger.info(f"✅ Файл успешно обработан: {server_url}")
        return True, server_url, local_path, None
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки файла: {e}")
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass
        return False, None, None, f"Критическая ошибка: {str(e)[:100]}"


def cleanup_temp_file(file_path: Optional[str]):
    """
    Удалить временный файл
    
    Args:
        file_path: Путь к файлу
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"🗑️ Временный файл удален: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")
