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
    Загрузить аудиофайл на сервер (заглушка, нужна реализация upload_file_to_server)
    
    Args:
        file_path: Путь к локальному файлу
        filename: Имя файла на сервере
        
    Returns:
        Tuple (успех, URL файла, сообщение об ошибке)
    """
    try:
        # ВРЕМЕННАЯ ЗАГЛУШКА
        # В реальности нужно реализовать загрузку на ваш сервер
        # Например, через S3, FTP, или HTTP POST
        
        # Пример для локального сервера:
        # import requests
        # files = {'file': open(file_path, 'rb')}
        # response = requests.post('https://your-server.com/upload', files=files)
        # return True, response.json()['url'], None
        
        logger.warning("⚠️ upload_audio_to_server - заглушка! Нужна реализация загрузки на сервер")
        
        # Возвращаем фейковый URL для тестирования
        fake_url = f"https://example.com/audio/{filename}"
        return True, fake_url, None
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки на сервер: {e}")
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
