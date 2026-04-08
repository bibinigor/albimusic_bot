import os
import sys
import json
import time
import random
import asyncio
import logging
import traceback
from datetime import datetime, timedelta

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import aioredis

# Импортируем модули проекта
from vk_config import VK_TOKEN, VK_GROUP_ID, ADMIN_IDS
from vk_states import States, VKStateManager
from db_utils import execute_query_sync
from celery_tasks import (
    translate_style_to_english,
    generate_suno_lyrics_sync,
    generate_suno_music_sync,
    generate_song_task,
    generate_music_task,
    generate_karaoke_task,
    generate_cover_task,
    generate_wav_task
)

# Импортируем модуль администрирования (рассылка)
try:
    from vk_admin import get_all_user_ids, get_vk_user_ids, format_broadcast_confirmation, format_broadcast_result
    HAS_VK_ADMIN = True
except ImportError:
    HAS_VK_ADMIN = False
    logger_tmp = logging.getLogger(__name__)
    logger_tmp.warning("⚠️ vk_admin.py не найден — функция рассылки недоступна")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Команды для сброса состояния
RESET_COMMANDS = ["начать", "start", "меню", "menu", "отмена", "cancel", "🏠 в главное меню", "в главное меню", "главное меню"]

# Перечисление состояний пользователя (для обратной совместимости)
class UserState:
    START = 0
    WAITING_SONG_DESCRIPTION = 1
    WAITING_INSTRUMENTAL_DESCRIPTION = 2
    WAITING_GENRE = 3
    WAITING_VOCAL_GENDER = 4
    WAITING_MUSIC_STYLE = 5

# Инициализация пула подключений к базе данных
try:
    from db_utils import init_db_pool_sync
    init_db_pool_sync()
    logger.info("✅ Database pool initialized")
except Exception as e:
    logger.error(f"❌ Error initializing database pool: {e}")
    sys.exit(1)

# Create users table if not exists
try:
    execute_query_sync("""
    CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT FALSE,
            referrer_id BIGINT,
            is_free_used BOOLEAN DEFAULT FALSE
    )
    """)
    logging.info("✅ Users table ready")
except Exception as e:
    logger.error(f"❌ Error creating users table: {e}")

class VKBot:
    def __init__(self):
        # Инициализация базовых компонентов с обработкой ошибок
        try:
            self.vk_session = vk_api.VkApi(token=VK_TOKEN)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
            logger.info("✅ Подключение к VK API успешно установлено (BotLongPoll)")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации VK API: {e}")
            # Повторная попытка инициализации с задержкой
            time.sleep(5)
            self.vk_session = vk_api.VkApi(token=VK_TOKEN)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
            logger.info("✅ Подключение к VK API успешно установлено со второй попытки (BotLongPoll)")
        
        # Словарь для хранения состояний пользователей (для обратной совместимости)
        self.user_states = {}
        
        # Инициализация Redis и менеджера состояний с обработкой ошибок
        max_redis_retries = 3
        redis_retry_count = 0
        
        while redis_retry_count < max_redis_retries:
            try:
                self.redis = asyncio.get_event_loop().run_until_complete(
                    aioredis.from_url("redis://localhost", socket_timeout=10.0, socket_connect_timeout=10.0)
                )
                self.state_manager = VKStateManager(self.redis)
                logger.info("✅ Подключение к Redis успешно установлено")
                break
            except Exception as e:
                redis_retry_count += 1
                logger.error(f"❌ Ошибка при подключении к Redis (попытка {redis_retry_count}/{max_redis_retries}): {e}")
                if redis_retry_count >= max_redis_retries:
                    logger.critical("❌ Не удалось подключиться к Redis после нескольких попыток")
                    # Создаем заглушку для Redis, чтобы бот мог работать без сохранения состояний
                    from unittest.mock import MagicMock
                    self.redis = MagicMock()
                    self.state_manager = VKStateManager(self.redis)
                    logger.warning("⚠️ Используется заглушка для Redis. Состояния пользователей не будут сохраняться.")
                else:
                    time.sleep(3 * redis_retry_count)
        
        logger.info("VK Bot initialized successfully")

    def get_cancel_keyboard(self):
        """Создать клавиатуру с кнопкой возврата в меню"""
        # Используем клавиатуру из модуля vk_keyboards
        from vk_keyboards import get_cancel_keyboard
        return get_cancel_keyboard()

    def get_home_keyboard(self):
        """Создать клавиатуру с кнопкой возврата в главное меню"""
        # Используем клавиатуру из модуля vk_keyboards
        from vk_keyboards import get_home_keyboard
        return get_home_keyboard()
        
    def get_music_style_keyboard(self):
        """Создать клавиатуру выбора стиля музыки"""
        # Используем клавиатуру из модуля vk_keyboards
        from vk_keyboards import get_music_style_keyboard
        return get_music_style_keyboard()

    def reset_state(self, user_id):
        """Сбросить состояние пользователя"""
        # Сброс состояния в старом хранилище (для обратной совместимости)
        if user_id in self.user_states:
            del self.user_states[user_id]
            
        # Сброс состояния в новом менеджере состояний
        try:
            # Принудительно удаляем все данные состояния из Redis
            try:
                asyncio.get_event_loop().run_until_complete(
                    self.redis.delete(f"vk:state:{user_id}")
                )
                asyncio.get_event_loop().run_until_complete(
                    self.redis.delete(f"vk:data:{user_id}")
                )
                logger.info(f"✅ Данные состояния пользователя {user_id} удалены из Redis")
            except Exception as e:
                logger.error(f"❌ Ошибка при удалении данных из Redis: {e}")
            
            # Сначала очищаем все данные состояния
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.update_data(user_id, {})
            )
            
            # Затем устанавливаем состояние START
            asyncio.get_event_loop().run_until_complete(
                self.state_manager.set_state(user_id, States.START)
            )
            
            logger.info(f"✅ Состояние пользователя {user_id} успешно сброшено")
        except Exception as e:
            logger.error(f"❌ Ошибка при сбросе состояния пользователя {user_id}: {e}")
        
        # Реинициализация компонентов VK API
        self.vk_session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
        logger.info("VK Bot initialized successfully")

    def send_message(self, user_id, message, keyboard=None, attachment=None, max_retries=3):
        """Send message to user with optional keyboard and/or attachment"""
        retries = 0
        while retries < max_retries:
            try:
                params = {
                    'user_id': user_id,
                    'message': message,
                    'random_id': get_random_id()
                }
                
                if keyboard:
                    # Преобразуем клавиатуру в JSON строку с помощью метода get_keyboard()
                    params['keyboard'] = keyboard.get_keyboard()

                if attachment:
                    # Вложение: аудио-сообщение, документ и т.д. (формат 'doc{owner}_{id}')
                    params['attachment'] = attachment
                    
                self.vk.messages.send(**params)
                return True
            except Exception as e:
                retries += 1
                error_msg = str(e)
                
                # Проверяем тип ошибки
                if "Connection reset by peer" in error_msg or "Read timed out" in error_msg:
                    # Сетевая ошибка, пробуем еще раз после паузы
                    logger.warning(f"⚠️ Сетевая ошибка при отправке сообщения (попытка {retries}/{max_retries}): {e}")
                    time.sleep(2 * retries)  # Увеличиваем время ожидания с каждой попыткой
                    continue
                elif "flood control" in error_msg.lower():
                    # Ограничение на частоту отправки сообщений
                    logger.warning(f"⚠️ Сработало ограничение на отправку сообщений (попытка {retries}/{max_retries}): {e}")
                    time.sleep(3 * retries)  # Более длительная пауза при флуд-контроле
                    continue
                else:
                    # Другая ошибка, логируем и пробуем еще раз
                    logger.error(f"❌ Ошибка отправки сообщения (попытка {retries}/{max_retries}): {e}")
                    if retries < max_retries:
                        time.sleep(1)
                        continue
                    else:
                        # Исчерпаны все попытки
                        logger.error(f"❌ Не удалось отправить сообщение после {max_retries} попыток")
                        return False
        
        return False

    def upload_mp3_as_vk_doc(self, user_id, cdn_url, title="ALBI Music"):
        """Скачивает MP3 с CDN Suno, конвертирует в OGG Opus и загружает в VK.

        Алгоритм:
          1. Скачиваем MP3 во временный файл (timeout connect=30с, read=120с).
          2. Конвертируем MP3 → OGG Opus через FFmpeg.
             Это КЛЮЧЕВОЕ исправление: VK не перекодирует OGG-файл на своих серверах,
             поэтому трек не обрезается и не зацикливается при воспроизведении.
          3. Загружаем .ogg как audio_message — inline-плеер (▶) прямо в чате.
          4. Если audio_message недоступен — fallback: document_message (MP3 как файл).
          5. Оба временных файла (.mp3 и .ogg) удаляются в блоке finally.

        Args:
            user_id:  ID пользователя VK (нужен как peer_id при загрузке)
            cdn_url:  URL MP3 файла (CDN Suno)
            title:    Название трека (отображается в плеере)

        Returns:
            str: строка вложения 'doc{owner_id}_{id}' для messages.send(attachment=...)
                 или None при ошибке
        """
        import tempfile
        import os
        import subprocess
        import requests as _req
        from vk_api import VkUpload

        temp_mp3_path = None
        temp_ogg_path = None
        try:
            # ── Шаг 1: скачиваем MP3 во временный файл ──────────────────────────
            logger.info(f"📥 Скачиваем MP3 для загрузки в VK: {cdn_url[:80]}...")
            resp = _req.get(cdn_url, timeout=(30, 120), stream=True)
            resp.raise_for_status()

            expected_size = int(resp.headers.get('Content-Length', 0))

            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                temp_mp3_path = tmp.name
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        tmp.write(chunk)

            actual_size = os.path.getsize(temp_mp3_path)
            size_kb = actual_size // 1024
            logger.info(f"✅ MP3 скачан — {size_kb} КБ → {temp_mp3_path}")

            if expected_size > 0 and actual_size < expected_size:
                logger.warning(
                    f"⚠️ Файл скачан не полностью: {actual_size} / {expected_size} байт"
                )

            # ── Шаг 2: конвертируем MP3 → OGG Opus через FFmpeg ─────────────────
            # VK принимает OGG без перекодирования → трек не обрезается.
            ogg_fd, temp_ogg_path = tempfile.mkstemp(suffix='.ogg')
            os.close(ogg_fd)

            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', temp_mp3_path,
                '-c:a', 'libopus',
                '-b:a', '128k',
                '-vbr', 'on',
                '-frame_duration', '20',
                '-application', 'audio',
                temp_ogg_path
            ]
            ffmpeg_result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120
            )

            if ffmpeg_result.returncode != 0:
                ffmpeg_err = ffmpeg_result.stderr.decode('utf-8', errors='replace')[-300:]
                logger.warning(f"⚠️ FFmpeg завершился с ошибкой (код {ffmpeg_result.returncode}): {ffmpeg_err}")
                # Если конвертация не удалась — используем исходный MP3
                upload_path = temp_mp3_path
                upload_mime = 'audio/mpeg'
                upload_ext  = 'mp3'
            else:
                ogg_size_kb = os.path.getsize(temp_ogg_path) // 1024
                logger.info(f"✅ FFmpeg конвертация завершена — {ogg_size_kb} КБ → {temp_ogg_path}")
                upload_path = temp_ogg_path
                upload_mime = 'audio/ogg'
                upload_ext  = 'ogg'

            # ── Шаг 3: audio_message (inline-плеер ▶ прямо в чате) ──────────────
            try:
                server = self.vk.docs.getMessagesUploadServer(
                    type='audio_message',
                    peer_id=user_id
                )
                upload_url = server['upload_url']

                with open(upload_path, 'rb') as f:
                    up_resp = _req.post(
                        upload_url,
                        files={'file': (f'{title}.{upload_ext}', f, upload_mime)},
                        timeout=(30, 180)
                    )
                up_data = up_resp.json()

                save_result = self.vk.docs.save(file=up_data['file'], title=title)

                doc = save_result.get('audio_message') or save_result.get('doc')
                if doc:
                    attachment = f"doc{doc['owner_id']}_{doc['id']}"
                    logger.info(f"✅ Загружен как audio_message (OGG Opus, inline-плеер): {attachment}")
                    return attachment

            except Exception as am_err:
                logger.warning(
                    f"⚠️ audio_message недоступен ({am_err}), "
                    f"переключаемся на document_message..."
                )

            # ── Шаг 4: fallback — обычный документ (MP3 как вложение-файл) ───────
            upload = VkUpload(self.vk_session)
            doc_result = upload.document_message(temp_mp3_path, peer_id=user_id, title=title)
            attachment = f"doc{doc_result['doc']['owner_id']}_{doc_result['doc']['id']}"
            logger.info(f"✅ Загружен как document_message (MP3): {attachment}")
            return attachment

        except Exception as e:
            logger.error(f"❌ Ошибка upload_mp3_as_vk_doc ({cdn_url[:60]}): {e}")
            return None

        finally:
            # Удаляем оба временных файла
            for path in (temp_mp3_path, temp_ogg_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                        logger.debug(f"🗑️ Temp-файл удалён: {path}")
                    except Exception:
                        pass

    def get_main_keyboard(self, user_id):
        """Create main menu keyboard"""
        try:
            logger.info("⌨️ Создание главной клавиатуры")
            
            # Используем клавиатуру из модуля vk_keyboards
            from vk_keyboards import get_main_keyboard
            
            keyboard = get_main_keyboard(user_id)
            logger.info("✅ Клавиатура успешно создана")
            return keyboard
        except Exception as e:
            logger.error(f"❌ Ошибка создания клавиатуры: {e}")
            return None

    def register_user(self, user_id, username, first_name, referrer_id=None):
        """Register new user in database. Returns True if user is NEW, False if already existed."""
        try:
            result = execute_query_sync(
                "INSERT INTO users (user_id, username, first_name, balance, created_at, provider) VALUES (%s, %s, %s, 1, NOW(), 'vk') ON CONFLICT (user_id) DO UPDATE SET provider = 'vk' WHERE users.provider = 'telegram' RETURNING user_id",
                (user_id, username, first_name)
            )
            is_new_user = bool(result)
            if is_new_user:
                logger.info(f"✅ Пользователь {user_id} успешно зарегистрирован с 1 токеном")
                # Устанавливаем реферальную связь и сразу начисляем бонус пригласившему
                # ВАЖНО: реферер должен быть VK-пользователем (provider='vk')
                if referrer_id and int(referrer_id) != int(user_id):
                    try:
                        ref_exists = execute_query_sync(
                            "SELECT user_id FROM users WHERE user_id = %s AND provider = 'vk'",
                            (int(referrer_id),)
                        )
                        if ref_exists:
                            execute_query_sync(
                                "UPDATE users SET invited_by = %s WHERE user_id = %s AND invited_by IS NULL",
                                (int(referrer_id), user_id)
                            )
                            # Создаём запись в referrals (bonus_applied=FALSE — до реального начисления)
                            execute_query_sync(
                                "INSERT INTO referrals (referrer_id, referred_id, bonus_applied) SELECT %s, %s, FALSE WHERE NOT EXISTS (SELECT 1 FROM referrals WHERE referred_id = %s)",
                                (int(referrer_id), user_id, user_id)
                            )
                            # ✅ Бонус НЕ начисляется сразу при регистрации.
                            # bonus_applied=FALSE → _award_referral_bonus() выдаст +2 токена
                            # автоматически, как только приглашённый создаст первую песню.
                            logger.info(f"🔗 Реферал VK: {user_id} → {referrer_id}. Бонус начислится после первой генерации друга.")
                            # Уведомляем пригласившего о регистрации друга (без токенов — пока)
                            self.send_message(
                                user_id=int(referrer_id),
                                message=(
                                    "🎉 Ваш друг присоединился к ALBI Music!\n\n"
                                    "🎵 Как только он создаст первую песню — вы получите "
                                    "+2 токена автоматически! 🚀"
                                )
                            )
                        else:
                            logger.warning(f"⚠️ Реферал VK: реферер {referrer_id} не найден как VK-пользователь — бонус пропущен.")
                    except Exception as ref_e:
                        logger.warning(f"⚠️ Ошибка реферальной системы VK при регистрации: {ref_e}", exc_info=True)
            else:
                logger.info(f"📝 Пользователь {user_id} уже был в базе данных")
            return is_new_user
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации пользователя {user_id}: {e}")
            return False

    def _award_referral_bonus(self, referred_user_id):
        """Начислить 2 токена пригласившему, если приглашённый впервые создал музыку."""
        try:
            ref_row = execute_query_sync(
                "SELECT referrer_id FROM referrals WHERE referred_id = %s AND bonus_applied = FALSE",
                (referred_user_id,)
            )
            if not ref_row:
                return  # Нет реферала или бонус уже выплачен

            referrer_id = ref_row[0][0]

            # Начисляем 2 токена рефереру
            execute_query_sync(
                "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                (referrer_id,)
            )
            # Помечаем бонус как выплаченный
            execute_query_sync(
                "UPDATE referrals SET bonus_applied = TRUE WHERE referred_id = %s",
                (referred_user_id,)
            )
            # Уведомляем реферера
            self.send_message(
                user_id=referrer_id,
                message=(
                    "🎉 Ваш друг создал первую песню!\n\n"
                    "💰 Вам начислено +2 токена за приглашение друга.\n"
                    "Продолжайте приглашать — за каждого получаете 2 токена! 🚀"
                )
            )
            logger.info(f"💰 Реферальный бонус: +2 токена пользователю {referrer_id} (пригласил {referred_user_id})")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка начисления реферального бонуса для {referred_user_id}: {e}")

    def get_admin_stats(self):
        """Получить статистику для админ-панели (аналог Telegram-бота)"""
        try:
            # 1. Всего пользователей
            users_result = execute_query_sync("SELECT COUNT(*) as total FROM users")
            total_users = users_result[0][0] if users_result and users_result[0] else 0

            # 2. Новых сегодня (за текущие сутки)
            new_today_result = execute_query_sync(
                "SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE"
            )
            new_today = new_today_result[0][0] if new_today_result and new_today_result[0] else 0

            # 3. Новых за 7 дней
            new_7days_result = execute_query_sync(
                "SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )
            new_7days = new_7days_result[0][0] if new_7days_result and new_7days_result[0] else 0

            # 4. Новых за 30 дней
            new_30days_result = execute_query_sync(
                "SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"
            )
            new_30days = new_30days_result[0][0] if new_30days_result and new_30days_result[0] else 0

            # 5. Воронка: новые за 24ч и дошедшие до меню
            started_24h_result = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours'"
            )
            started_24h = started_24h_result[0][0] if started_24h_result and started_24h_result[0] else 0

            menu_24h_result = execute_query_sync(
                "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours' AND first_menu_action_at IS NOT NULL"
            )
            menu_24h = menu_24h_result[0][0] if menu_24h_result and menu_24h_result[0] else 0

            menu_pct = round(menu_24h * 100.0 / started_24h, 1) if started_24h > 0 else 0

            # 6. Генерации за 24 часа
            generations_24h_result = execute_query_sync(
                "SELECT COUNT(*) as total FROM generations WHERE created_at >= NOW() - INTERVAL '24 hours'"
            )
            generations_24h = generations_24h_result[0][0] if generations_24h_result and generations_24h_result[0] else 0

            # 7. Всего генераций и успешных
            total_gen_result = execute_query_sync("SELECT COUNT(*) as total FROM generations")
            total_generations = total_gen_result[0][0] if total_gen_result and total_gen_result[0] else 0

            completed_result = execute_query_sync(
                "SELECT COUNT(*) as total FROM generations WHERE status = 'completed'"
            )
            completed_generations = completed_result[0][0] if completed_result and completed_result[0] else 0

            success_rate = round((completed_generations * 100.0) / total_generations, 1) if total_generations > 0 else 0

            # 8. Приглашённых сегодня
            invited_today_result = execute_query_sync(
                "SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE AND invited_by IS NOT NULL"
            )
            invited_today = invited_today_result[0][0] if invited_today_result and invited_today_result[0] else 0

            # 9. Статистика платежей
            try:
                count_24h_result = execute_query_sync(
                    "SELECT COUNT(*) FROM payments WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'"
                )
                count_24h = count_24h_result[0][0] if count_24h_result and count_24h_result[0] else 0

                sum_24h_result = execute_query_sync(
                    "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'"
                )
                sum_24h = int(sum_24h_result[0][0]) if sum_24h_result and sum_24h_result[0] else 0

                count_7days_result = execute_query_sync(
                    "SELECT COUNT(*) FROM payments WHERE status = 'succeeded' AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
                )
                count_7days = count_7days_result[0][0] if count_7days_result and count_7days_result[0] else 0

                sum_7days_result = execute_query_sync(
                    "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded' AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
                )
                sum_7days = int(sum_7days_result[0][0]) if sum_7days_result and sum_7days_result[0] else 0

                count_total_result = execute_query_sync(
                    "SELECT COUNT(*) FROM payments WHERE status = 'succeeded'"
                )
                count_total = count_total_result[0][0] if count_total_result and count_total_result[0] else 0

                sum_total_result = execute_query_sync(
                    "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded'"
                )
                sum_total = int(sum_total_result[0][0]) if sum_total_result and sum_total_result[0] else 0

                # Разбивка по тарифам за 24ч
                tariffs_rows = execute_query_sync(
                    """
                    SELECT amount, COUNT(*)
                    FROM payments
                    WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY amount
                    ORDER BY amount
                    """
                )
                tariffs_24h = {row[0]: row[1] for row in tariffs_rows} if tariffs_rows else {}
            except Exception as e:
                logger.error(f"❌ Ошибка получения статистики платежей: {e}")
                count_24h = sum_24h = count_7days = sum_7days = count_total = sum_total = 0
                tariffs_24h = {}

            # Формируем строку разбивки по тарифам
            if tariffs_24h:
                amount_to_tokens = {50: 1, 250: 10, 500: 25, 1000: 60, 2000: 140}
                tariff_lines = []
                for amount, cnt in sorted(tariffs_24h.items()):
                    tokens = amount_to_tokens.get(amount)
                    if tokens:
                        tariff_lines.append(f"• {cnt}×{amount}₽ ({tokens} ток.)")
                    else:
                        tariff_lines.append(f"• {cnt}×{amount}₽")
                tariffs_text = "\n".join(tariff_lines)
            else:
                tariffs_text = "• нет оплат за 24ч"

            return f"""📊 Статистика бота:

👥 Всего пользователей: {total_users} (+{new_today})
📈 Новых за 7 дней: {new_7days}
📅 Новых за 30 дней: {new_30days}

📊 Воронка (НОВЫЕ за 24ч):
▶️ Нажали /start (новые): {started_24h}
🖱 Дошли до меню (из новых): {menu_24h} ({menu_pct}%)

🎵 Генераций за 24ч: {generations_24h} шт
✅ Общий успех (все время): {success_rate}%

💳 Оплаты:
⏰ За 24ч: {count_24h} платежей · {sum_24h}₽
    🔍 По тарифам (24ч):
{tariffs_text}
📆 За 7 дней: {count_7days} платежей · {sum_7days}₽
📊 Всего: {count_total} платежей · {sum_total}₽

👥 Приглашенных сегодня: {invited_today}"""

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return "❌ Ошибка получения статистики"
    def handle_message(self, event):
        """Обработчик входящих сообщений (VkBotLongPoll)"""
        # Поддержка VkBotLongPoll (event.obj['message']) и VkLongPoll (event.user_id) как fallback
        if hasattr(event, 'obj') and isinstance(event.obj, dict) and 'message' in event.obj:
            msg = event.obj['message']
            user_id = msg.get('from_id') or msg.get('user_id', 0)
            text = msg.get('text', '') or ''
        else:
            user_id = getattr(event, 'user_id', 0)
            text = getattr(event, 'text', '') or ''
        text_lower = text.lower()  # Приводим к нижнему регистру сразу

        # ============================================================
        # РЕЖИМ ТЕХНИЧЕСКОГО ОБСЛУЖИВАНИЯ
        # Установите MAINTENANCE_MODE = False когда сервис восстановлен
        # ============================================================
        MAINTENANCE_MODE = False
        if MAINTENANCE_MODE and user_id not in ADMIN_IDS:
            self.send_message(
                user_id,
                "🔧 Бот находится на техническом обслуживании\n\n"
                "Мы работаем над улучшением сервиса и скоро вернёмся!\n\n"
                "Приносим извинения за временные неудобства 🙏\n\n"
                "Следите за обновлениями в нашем сообществе VK."
            )
            return

        # Логируем все входящие сообщения до любой обработки
        logger.info(f"📩 Получено новое сообщение от {user_id}: '{text}' (в нижнем регистре: '{text_lower}')")
        print(f"Получено сообщение: {text}")
        
        # Специальная обработка команды "Начать"/"start"
        # ВАЖНО: сначала регистрируем пользователя с ref_param, потом отправляем приветствие
        if text_lower in ["начать", "start"]:
            logger.info(f"🔄 Получена команда начала работы от {user_id}: '{text}'")

            # 1. Извлекаем реферальный параметр (VK передаёт ref ТОЛЬКО в первом сообщении)
            ref_param_start = None
            try:
                if hasattr(event, 'obj') and isinstance(event.obj, dict) and 'message' in event.obj:
                    ref_raw = event.obj['message'].get('ref', None)
                    if ref_raw:
                        ref_param_start = int(ref_raw)
                        logger.info(f"🔗 Новый пользователь {user_id} пришёл по реферальной ссылке от {ref_param_start}")
            except Exception:
                ref_param_start = None

            # 2. Регистрируем пользователя (с реферальным бонусом если есть ref)
            try:
                user_info_start = self.vk.users.get(user_ids=user_id)[0]
                logger.info(f"👤 Получена информация о пользователе: {user_info_start}")
                registered_start = self.register_user(
                    user_id=user_id,
                    username=user_info_start.get('screen_name'),
                    first_name=user_info_start.get('first_name'),
                    referrer_id=ref_param_start
                )
                logger.info(f"📝 Регистрация при 'начать': {'новый' if registered_start else 'уже был в базе'}")
            except Exception as e:
                logger.error(f"❌ Ошибка регистрации при команде 'начать' для {user_id}: {e}")

            # 3. Сбрасываем состояние
            self.reset_state(user_id)

            welcome_text = """🎵 Привет! Я — бот для создания музыки с помощью ИИ.

🎼 Что я умею:
• Создавать песни с вашим текстом
• Генерировать инструментальную музыку
• Сочинять тексты для песен

💫 Первая генерация — бесплатно!
🎁 Выберите действие в меню 👇"""

            keyboard = self.get_main_keyboard(user_id)
            if keyboard:
                result = self.send_message(
                    user_id=user_id,
                    message=welcome_text,
                    keyboard=keyboard
                )
                logger.info(f"📨 Отправка приветственного сообщения: {'успешно' if result else 'ошибка'}")
            return
        
        # Проверяем наличие payload в сообщении (VkBotLongPoll и VkLongPoll)
        payload = None
        try:
            payload_raw = None
            if hasattr(event, 'obj') and isinstance(event.obj, dict) and 'message' in event.obj:
                # VkBotLongPoll: payload хранится в event.obj['message']['payload'] как строка
                payload_raw = event.obj['message'].get('payload', '')
            elif hasattr(event, 'payload') and event.payload:
                # VkLongPoll fallback
                payload_raw = event.payload
            if payload_raw:
                payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                print(f"Получен payload: {payload}")
                logger.info(f"📩 Получен payload от {user_id}: {payload}")
        except Exception as e:
            logger.error(f"❌ Ошибка при разборе payload: {e}")

        # Извлекаем реферальный параметр ref (когда пользователь пришёл по ссылке ?ref=USER_ID)
        ref_param = None
        try:
            if hasattr(event, 'obj') and isinstance(event.obj, dict) and 'message' in event.obj:
                ref_raw = event.obj['message'].get('ref', None)
                if ref_raw:
                    ref_param = int(ref_raw)
                    logger.info(f"🔗 Пользователь {user_id} пришёл по реферальной ссылке от {ref_param}")
        except Exception:
            ref_param = None

        try:
            # Флаг для отслеживания обработки команды
            command_handled = False
            
            # Регистрация пользователя при первом сообщении
            try:
                user_info = self.vk.users.get(user_ids=user_id)[0]
                logger.info(f"👤 Получена информация о пользователе: {user_info}")
                
                registered = self.register_user(
                    user_id=user_id,
                    username=user_info.get('screen_name'),
                    first_name=user_info.get('first_name'),
                    referrer_id=ref_param
                )
                logger.info(f"📝 Регистрация пользователя: {'новый' if registered else 'уже был в базе'}")
            except Exception as e:
                logger.error(f"❌ Ошибка при работе с пользователем: {e}")
                return

            # Проверяем базовые команды до любой другой обработки
            if text.lower() in [cmd.lower() for cmd in RESET_COMMANDS]:
                logger.info(f"🔄 Получена команда сброса состояния от {user_id}: '{text}'")
                self.reset_state(user_id)
                welcome_text = "Вы вернулись в главное меню!"
                
                if text.lower() in ["начать", "start"]:
                    welcome_text = """🎵 Привет! Я — бот для создания музыки с помощью ИИ.

🎼 Что я умею:
• Создавать песни с вашим текстом
• Генерировать инструментальную музыку
• Сочинять тексты для песен

💫 Первая генерация — бесплатно!
🎁 Выберите действие в меню 👇"""
                
                keyboard = self.get_main_keyboard(user_id)
                if keyboard:
                    result = self.send_message(
                        user_id=user_id,
                        message=welcome_text,
                        keyboard=keyboard
                    )
                    logger.info(f"📨 Отправка сообщения: {'успешно' if result else 'ошибка'}")
                command_handled = True
                return

            # Обработка команд меню
            
            # Проверяем, есть ли payload и обрабатываем его
            if payload and isinstance(payload, dict):
                # Обработка payload от кнопок
                action = payload.get('action')
                if action:
                    logger.info(f"🔘 Обработка действия из payload: {action}")
                    
                    # Обработка различных действий из payload
                    if action == "create_song":
                        text = "🎵 Создать песню"
                        text_lower = text.lower()
                    elif action == "create_music":
                        text = "🎶 Создать музыку"
                        text_lower = text.lower()
                    elif action == "balance":
                        text = "💰 Баланс"
                        text_lower = text.lower()
                    elif action == "my_tracks":
                        text = "📂 Мои треки"
                        text_lower = text.lower()
                    elif action == "examples":
                        text = "🎧 Примеры песен"
                        text_lower = text.lower()
                    elif action == "support":
                        text = "📞 Поддержка"
                        text_lower = text.lower()
                    elif action == "admin":
                        text = "⚙️ Админ"
                        text_lower = text.lower()
                    elif action == "home":
                        text = "🏠 В главное меню"
                        text_lower = text.lower()
                    elif action == "select_variant_1":
                        text = "Выбрать вариант 1"
                        text_lower = text.lower()
                    elif action == "select_variant_2":
                        text = "Выбрать вариант 2"
                        text_lower = text.lower()
                    elif action == "write_own_text":
                        text = "Написать свой текст"
                        text_lower = text.lower()
            
            # ── Получаем состояние ЗАРАНЕЕ, чтобы защитить свободный текст от перехвата меню ──
            try:
                vk_state = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_state(user_id)
                )
            except Exception as _se:
                logger.error(f"❌ Ошибка получения состояния пользователя {user_id}: {_se}")
                self.reset_state(user_id)
                vk_state = States.START

            # Состояния, в которых пользователь вводит произвольный текст (лирику, идею и т.п.)
            # В этих состояниях НЕЛЬЗЯ применять substring-поиск по ключевым словам меню:
            # например, слово «поддержка» в тексте песни иначе запускало бы обработчик поддержки.
            _TEXT_INPUT_STATES = {
                States.WAITING_SONG_IDEA,
                States.WAITING_OWN_LYRICS,
                States.WAITING_CUSTOM_GENRE,
                States.WAITING_BROADCAST_TEXT,
            }
            # payload означает нажатие кнопки — там текст заранее нормализован, substring-поиск безопасен
            _in_text_input_state = vk_state in _TEXT_INPUT_STATES and not payload

            # Обработка команд меню по тексту
            # ТРЮК: если пользователь в режиме ввода текста → берём ветку pass и ВСЕ elif ниже пропускаются.
            if _in_text_input_state:
                pass  # свободный текст — пропускаем меню, идём к обработке состояний
            elif "создать песню" in text_lower or text == "🎵 Создать песню":
                logger.info(f"🎵 Запрос на создание песни от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Устанавливаем состояние выбора типа текста
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.CHOOSING_TEXT_TYPE)
                        )
                        # Для обратной совместимости
                        self.user_states[user_id] = UserState.WAITING_SONG_DESCRIPTION
                        
                        # Сообщение с выбором типа текста
                        prompt_message = """✨ Отлично! Придумать за тебя текст или у тебя свой?

Чтобы вернуться в главное меню, нажмите кнопку ниже."""
                        
                        # Импортируем клавиатуру для выбора типа текста
                        from vk_keyboards import get_song_type_keyboard
                        
                        # Создаем клавиатуру для выбора типа текста (inline=True для отображения под сообщением)
                        keyboard = get_song_type_keyboard()
                        
                        # Отправляем сообщение с клавиатурой выбора типа текста
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=keyboard
                        )
                        
                        logger.info(f"✅ Пользователь {user_id} переведен в режим выбора типа текста")
                        command_handled = True
                        return  # Прерываем обработку текущего сообщения
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания песни при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания песни: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True

            elif "создать музыку" in text_lower or text == "🎶 Создать музыку":
                logger.info(f"🎶 Запрос на создание инструментальной музыки от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Устанавливаем состояние выбора жанра музыки
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_MUSIC_STYLE)
                        )
                        # Для обратной совместимости
                        self.user_states[user_id] = UserState.WAITING_INSTRUMENTAL_DESCRIPTION
                        
                        # Импортируем клавиатуру для выбора жанра музыки
                        from vk_keyboards import get_music_genres_keyboard
                        
                        # Создаем клавиатуру с жанрами
                        keyboard = get_music_genres_keyboard()
                        
                        # Сообщение с выбором жанра
                        prompt_message = """🎶 **СОЗДАЕМ ИНСТРУМЕНТАЛЬНУЮ МУЗЫКУ**

🎹 Музыка БЕЗ слов - только мелодия и ритм!

Выбери жанр для твоей композиции 👇"""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=keyboard
                        )
                        
                        logger.info(f"✅ Пользователь {user_id} переведен в режим выбора жанра инструментальной музыки")
                        command_handled = True
                        return  # Прерываем обработку текущего сообщения
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания музыки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания музыки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True

            # ──── БАЛАНС ────
            elif "баланс" in text_lower or text == "💰 Баланс":
                logger.info(f"💰 Запрос баланса от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    balance_num = result[0][0] if result else 0
                    balance_msg = (
                        f"💰 Ваш баланс: {balance_num} токенов\n\n"
                        f"💳 Выберите тариф для пополнения:\n\n"
                        f"🎁 Первый токен в подарок — для новых пользователей!"
                    )
                    
                    # Создаем клавиатуру с тарифами
                    from vk_keyboards import get_payment_tariffs_keyboard
                    payment_keyboard = get_payment_tariffs_keyboard()
                    
                    self.send_message(
                        user_id=user_id,
                        message=balance_msg,
                        keyboard=payment_keyboard
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка при получении баланса: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Ошибка при получении баланса. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True
                return

            # ──── МОИ ТРЕКИ ────
            elif "мои треки" in text_lower or text == "📂 Мои треки":
                logger.info(f"📂 Запрос треков от пользователя {user_id}")
                try:
                    tracks = execute_query_sync(
                        """SELECT task_id, prompt, audio_url, created_at, suno_audio_id
                           FROM generations
                           WHERE user_id = %s
                           ORDER BY id DESC LIMIT 10""",
                        (user_id,)
                    )
                    if not tracks:
                        self.send_message(
                            user_id=user_id,
                            message="🎵 У вас пока нет созданных треков. Самое время это исправить!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                    else:
                        self.send_message(
                            user_id=user_id,
                            message=f"🎵 Ваши последние треки ({len(tracks)} шт.):\n━━━━━━━━━━━━━━━━━",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        for idx, (task_id, prompt, audio_url, created_at, suno_audio_id) in enumerate(tracks, 1):
                            try:
                                date_str = created_at.strftime("%d.%m.%Y") if hasattr(created_at, 'strftime') else str(created_at)[:10]
                            except Exception:
                                date_str = "—"
                            short_prompt = (prompt[:80] + '...') if prompt and len(prompt) > 80 else (prompt or '—')
                            urls_text = ""
                            if audio_url:
                                # Убираем служебные префиксы мониторинга (добавляются после уведомления)
                                real_url = audio_url
                                for prefix in ('ALREADY_NOTIFIED_', 'ALREADY_SENT_'):
                                    if isinstance(audio_url, str) and audio_url.startswith(prefix):
                                        real_url = audio_url[len(prefix):]
                                        break
                                if real_url == 'ERROR_NOTIFIED':
                                    # Пробуем восстановить ссылки через suno_audio_id
                                    if suno_audio_id:
                                        try:
                                            import json as _json2
                                            sids = _json2.loads(suno_audio_id) if isinstance(suno_audio_id, str) and suno_audio_id.startswith('[') else [suno_audio_id]
                                            for i, sid in enumerate(sids, 1):
                                                label = f"Вариант {i}" if len(sids) > 1 else "Слушать"
                                                urls_text += f"\n🔗 {label}: https://cdn1.suno.ai/{sid}.mp3"
                                        except Exception:
                                            urls_text = f"\n🔗 Слушать: https://cdn1.suno.ai/{suno_audio_id}.mp3"
                                    else:
                                        urls_text = "\n❌ Ошибка генерации"
                                else:
                                    try:
                                        import json as _json
                                        urls = _json.loads(real_url) if real_url.startswith('[') else [real_url]
                                        for i, url in enumerate(urls, 1):
                                            label = f"Вариант {i}" if len(urls) > 1 else "Слушать"
                                            urls_text += f"\n🔗 {label}: {url}"
                                    except Exception:
                                        urls_text = f"\n🔗 Слушать: {real_url}"
                            track_msg = (
                                f"🎼 Трек #{idx} ({date_str})\n"
                                f"📝 {short_prompt}"
                                f"{urls_text}"
                            )
                            self.send_message(user_id=user_id, message=track_msg)
                except Exception as e:
                    logger.error(f"❌ Ошибка при получении треков: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Ошибка при получении треков. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                command_handled = True
                return

            # ──── ПРИМЕРЫ ПЕСЕН ────
            elif "примеры" in text_lower or text == "🎧 Примеры песен":
                logger.info(f"🎧 Запрос примеров от пользователя {user_id}")
                self.send_message(
                    user_id=user_id,
                    message=(
                        "🔐 Это портал для перехода в наше сообщество\n\n"
                        "«ALBImusic/ Музыка/ Промпты/ Новости/ Обучение»\n\n"
                        "Там твоё вдохновение! Там твоё секретное оружие — идеи! "
                        "И там же обучение и новости!\n\n"
                        "👉 Переходи в сообщество: https://vk.com/club235442407"
                    ),
                    keyboard=self.get_main_keyboard(user_id)
                )
                command_handled = True
                return

            # ──── ПОДДЕРЖКА ────
            elif "поддержка" in text_lower or text == "📞 Поддержка":
                logger.info(f"📞 Запрос поддержки от пользователя {user_id}")
                self.send_message(
                    user_id=user_id,
                    message=(
                        "Служба поддержки ALBI Music 🛠\n\n"
                        "По всем вопросам пишите мне в личные сообщения:\n"
                        "👉 https://vk.com/igorbibin\n\n"
                        "⏳ Отвечу вам в течение дня."
                    ),
                    keyboard=self.get_main_keyboard(user_id)
                )
                command_handled = True
                return

            # ──── АДМИН ПАНЕЛЬ ────
            elif "админ" in text_lower or text == "⚙️ Админ":
                logger.info(f"⚙️ Запрос админ панели от пользователя {user_id}")
                
                # Проверка является ли пользователь администратором
                if user_id not in ADMIN_IDS:
                    logger.warning(f"⛔ Попытка доступа к админ панели от не-администратора {user_id}")
                    self.send_message(
                        user_id=user_id,
                        message="⛔ Доступ запрещен",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    command_handled = True
                    return
                
                # Получаем статистику
                stats_text = self.get_admin_stats()

                # Показываем панель с кнопкой рассылки
                from vk_api.keyboard import VkKeyboard, VkKeyboardColor
                admin_kb = VkKeyboard(inline=True)
                admin_kb.add_callback_button(
                    "📨 Рассылка",
                    color=VkKeyboardColor.POSITIVE,
                    payload={"cmd": "admin_broadcast"}
                )

                self.send_message(
                    user_id=user_id,
                    message=f"👨‍💻 **Панель администратора**\n\n{stats_text}",
                    keyboard=admin_kb
                )
                command_handled = True
                return

            # vk_state уже получен выше (до блока проверок команд меню)

            # ──── ОБРАБОТКА СОСТОЯНИЙ РАССЫЛКИ (ADMIN) ────
            if vk_state == States.WAITING_BROADCAST_TEXT:
                if text_lower in ['отмена', 'cancel']:
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.finish(user_id)
                    )
                    self.send_message(
                        user_id=user_id,
                        message="❌ Рассылка отменена",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                else:
                    self._handle_broadcast_text(user_id, text)
                return

            if vk_state == States.WAITING_BROADCAST_CONFIRM:
                # Подтверждение происходит через callback-кнопки — текст игнорируем
                self.send_message(
                    user_id=user_id,
                    message="⚠️ Нажмите кнопку «✅ Отправить всем» или «❌ Отмена»"
                )
                return

            # Обработка выбора типа текста
            if vk_state == States.CHOOSING_TEXT_TYPE:
                if "ai-текст" in text_lower or "придумать текст" in text_lower or "🤖 ai-текст" in text_lower:
                    # Обработка выбора AI-текста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_SONG_IDEA)
                    )
                    
                    prompt_message = """✨ **СЕЙЧАС МЫ ТЕБЕ СОЧИНИМ САМЫЙ ЛУЧШИЙ ТЕКСТ!**

Про что и для кого ты хочешь песню? Напиши мне.

▪️ для кого / о ком
▪️ какие интересные моменты упомянуть
▪️ идея которую хочется передать песней

📩 Всё в ОДНОМ сообщении — и я создам текст!

💡 Совет: опиши кратко самое главное (до 200 символов) ✨"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=prompt_message,
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал генерацию AI-текста")
                    command_handled = True
                    return
                
                elif "свой текст" in text_lower or "✍️ свой текст" in text_lower:
                    # Обработка выбора своего текста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_OWN_LYRICS)
                    )
                    
                    prompt_message = """📝 **ОТЛИЧНО!**

Отправь мне текст своей песни, и мы перейдем к выбору жанра 🎵"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=prompt_message,
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал использование своего текста")
                    command_handled = True
                    return
            
            # Обработка ввода идеи для AI-текста
            elif vk_state == States.WAITING_SONG_IDEA:
                command_handled = True  # ВАЖНО: помечаем команду как обработанную
                
                # Сохраняем идею для генерации текста
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, song_idea=text)
                )
                
                # Отправляем сообщение о начале генерации
                self.send_message(
                    user_id=user_id,
                    message="⏳ Генерирую текст песни, подождите 1-2 минуты...",
                    keyboard=self.get_cancel_keyboard()
                )
                
                print(f"Запуск генерации текста для пользователя {user_id}, идея: {text}")
                logger.info(f"📝 Запуск генерации текста для пользователя {user_id}, идея: {text}")
                
                # Генерируем два варианта текста песни на основе идеи
                try:
                    # Ограничиваем длину идеи
                    idea = text[:500]
                    
                    # Генерируем первый вариант текста
                    lyrics_variant1 = generate_suno_lyrics_sync(idea)
                    
                    # Генерируем второй вариант текста с небольшим изменением запроса
                    lyrics_variant2 = generate_suno_lyrics_sync(idea + " (альтернативный вариант)")
                    
                    if lyrics_variant1 and lyrics_variant2:
                        # Сохраняем сгенерированные тексты
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(
                                user_id, 
                                lyrics_variant1=lyrics_variant1,
                                lyrics_variant2=lyrics_variant2
                            )
                        )
                        
                        # Отправляем первый вариант текста пользователю
                        self.send_message(
                            user_id=user_id,
                            message=f"✨ Вариант 1:\n\n{lyrics_variant1}"
                        )
                        
                        # Отправляем второй вариант текста пользователю
                        self.send_message(
                            user_id=user_id,
                            message=f"✨ Вариант 2:\n\n{lyrics_variant2}"
                        )
                        
                        # Импортируем клавиатуру для выбора варианта текста
                        from vk_keyboards import get_lyrics_variants_selection_keyboard
                        
                        # Отправляем клавиатуру выбора варианта текста
                        self.send_message(
                            user_id=user_id,
                            message="Выберите вариант текста или напишите свой:",
                            keyboard=get_lyrics_variants_selection_keyboard()
                        )
                        
                        # Переводим в состояние выбора варианта текста
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.CHOOSING_LYRICS_VARIANT)
                        )
                    else:
                        # Если не удалось сгенерировать текст — НЕ сбрасываем состояние,
                        # оставляем пользователя в WAITING_SONG_IDEA чтобы он мог попробовать снова
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_SONG_IDEA)
                        )
                        self.send_message(
                            user_id=user_id,
                            message=(
                                "❌ Не удалось сгенерировать текст песни.\n\n"
                                "💡 Попробуйте описать идею подробнее:\n"
                                "• Напишите 2-3 предложения\n"
                                "• Укажите настроение (весёлая, грустная, романтичная)\n"
                                "• Опишите тему или главных героев\n\n"
                                "Пример: «Весёлая песня про дружбу, как мы с друзьями проводим лето на даче»\n\n"
                                "✍️ Введите новую идею:"
                            ),
                            keyboard=self.get_cancel_keyboard()
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации текста: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при генерации текста. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    self.reset_state(user_id)
                
                logger.info(f"✅ Пользователь {user_id} отправил идею для AI-текста")
                command_handled = True
                return
            # Обработка ввода своего текста
            elif vk_state == States.WAITING_OWN_LYRICS:
                command_handled = True  # ВАЖНО: помечаем команду как обработанную
                
                # Сохраняем текст песни
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, lyrics=text)
                )
                
                # Переводим в состояние выбора жанра
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.set_state(user_id, States.WAITING_GENRE)
                )
                
                # Импортируем клавиатуру для выбора жанра песни
                from vk_keyboards import get_song_genres_keyboard
                
                # Отправляем клавиатуру выбора жанра
                self.send_message(
                    user_id=user_id,
                    message="Выберите жанр для вашей песни:",
                    keyboard=get_song_genres_keyboard()
                )
                
                logger.info(f"✅ Пользователь {user_id} отправил свой текст")
                command_handled = True
                return
            
            # Обработка выбора варианта текста
            elif vk_state == States.CHOOSING_LYRICS_VARIANT:
                if "выбрать вариант 1" in text_lower or text == "Выбрать вариант 1" or "выбрать 1 вариант" in text_lower:
                    # Пользователь выбрал первый вариант текста
                    # Получаем данные состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    # Получаем первый вариант текста
                    lyrics = state_data.get('lyrics_variant1', '')
                    
                    if lyrics:
                        # Сохраняем выбранный текст
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(user_id, lyrics=lyrics)
                        )
                        
                        # Переводим в состояние выбора жанра
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_GENRE)
                        )
                        
                        # Импортируем клавиатуру для выбора жанра песни
                        from vk_keyboards import get_song_genres_keyboard
                        
                        # Отправляем клавиатуру выбора жанра
                        self.send_message(
                            user_id=user_id,
                            message="Выберите жанр для вашей песни:",
                            keyboard=get_song_genres_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} выбрал первый вариант текста")
                    else:
                        # Если текст не найден, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: текст песни не найден. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    command_handled = True
                    return
                
                elif "выбрать вариант 2" in text_lower or text == "Выбрать вариант 2" or "выбрать 2 вариант" in text_lower:
                    # Пользователь выбрал второй вариант текста
                    # Получаем данные состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    # Получаем второй вариант текста
                    lyrics = state_data.get('lyrics_variant2', '')
                    
                    if lyrics:
                        # Сохраняем выбранный текст
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.update_data(user_id, lyrics=lyrics)
                        )
                        
                        # Переводим в состояние выбора жанра
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_GENRE)
                        )
                        
                        # Импортируем клавиатуру для выбора жанра песни
                        from vk_keyboards import get_song_genres_keyboard
                        
                        # Отправляем клавиатуру выбора жанра
                        self.send_message(
                            user_id=user_id,
                            message="Выберите жанр для вашей песни:",
                            keyboard=get_song_genres_keyboard()
                        )
                        logger.info(f"✅ Пользователь {user_id} выбрал второй вариант текста")
                    else:
                        # Если текст не найден, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: текст песни не найден. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    command_handled = True
                    return
                
                elif "написать свой текст" in text_lower or "✍️ написать свой текст" in text_lower:
                    # Пользователь хочет написать свой текст
                    # Переводим в состояние ожидания своего текста
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_OWN_LYRICS)
                    )
                    
                    prompt_message = """📝 **ОТЛИЧНО!**

Отправь мне текст своей песни, и мы перейдем к выбору жанра 🎵"""
                    
                    self.send_message(
                        user_id=user_id,
                        message=prompt_message,
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал написать свой текст")
                    command_handled = True
                    return
                
                elif "сгенерировать другие" in text_lower or "🔄 сгенерировать другие" in text_lower:
                    # Пользователь хочет сгенерировать другие варианты текста
                    # Получаем идею для песни из данных состояния
                    state_data = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    
                    song_idea = state_data.get('song_idea', '')
                    
                    if song_idea:
                        # Отправляем сообщение о генерации новых текстов
                        self.send_message(
                            user_id=user_id,
                            message="⏳ Генерирую новые варианты текста...",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Генерируем новые варианты текста
                        try:
                            # Ограничиваем длину идеи
                            idea = song_idea[:500]
                            
                            # Генерируем первый вариант текста с небольшим изменением запроса
                            lyrics_variant1 = generate_suno_lyrics_sync(idea + " (новый вариант)")
                            
                            # Генерируем второй вариант текста с другим изменением запроса
                            lyrics_variant2 = generate_suno_lyrics_sync(idea + " (другой стиль)")
                            
                            if lyrics_variant1 and lyrics_variant2:
                                # Сохраняем сгенерированные тексты
                                asyncio.get_event_loop().run_until_complete(
                                    self.state_manager.update_data(
                                        user_id, 
                                        lyrics_variant1=lyrics_variant1,
                                        lyrics_variant2=lyrics_variant2
                                    )
                                )
                                
                                # Отправляем первый вариант текста пользователю
                                self.send_message(
                                    user_id=user_id,
                                    message=f"✨ Новый вариант 1:\n\n{lyrics_variant1}"
                                )
                                
                                # Отправляем второй вариант текста пользователю
                                self.send_message(
                                    user_id=user_id,
                                    message=f"✨ Новый вариант 2:\n\n{lyrics_variant2}"
                                )
                                
                                # Импортируем клавиатуру для выбора варианта текста
                                from vk_keyboards import get_lyrics_variants_keyboard_with_two_options
                                
                                # Отправляем клавиатуру выбора варианта текста
                                self.send_message(
                                    user_id=user_id,
                                    message="Выберите вариант текста или напишите свой:",
                                    keyboard=get_lyrics_variants_keyboard_with_two_options()
                                )
                            else:
                                # Если не удалось сгенерировать текст
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Не удалось сгенерировать новые тексты. Попробуйте использовать текущие варианты или написать свой.",
                                    keyboard=get_lyrics_variants_keyboard_with_two_options()
                                )
                        except Exception as e:
                            logger.error(f"❌ Ошибка генерации новых текстов: {e}")
                            self.send_message(
                                user_id=user_id,
                                message="❌ Произошла ошибка при генерации новых текстов. Попробуйте использовать текущие варианты или написать свой.",
                                keyboard=get_lyrics_variants_keyboard_with_two_options()
                            )
                    else:
                        # Если идея не найдена, сообщаем об ошибке
                        self.send_message(
                            user_id=user_id,
                            message="❌ Произошла ошибка: идея для песни не найдена. Попробуйте начать сначала.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        self.reset_state(user_id)
                    
                    logger.info(f"✅ Пользователь {user_id} запросил новые варианты текста")
                    command_handled = True
                    return
            
            # Обработка выбора жанра
            elif vk_state == States.WAITING_GENRE:
                # Проверяем, выбрал ли пользователь "Свой вариант"
                if "свой вариант" in text_lower or text == "✏️ Свой вариант":
                    # Переводим в состояние ввода своего жанра
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_CUSTOM_GENRE)
                    )
                    
                    # Отправляем сообщение с просьбой ввести свой жанр
                    self.send_message(
                        user_id=user_id,
                        message=(
                            "Опишите жанр и стиль песни своими словами:\n\n"
                            "⚠️ Максимальная длина описания — 400 символов.\n"
                            "Пример: «Энергичный поп-рок, яркие гитары, женский вокал»"
                        ),
                        keyboard=self.get_cancel_keyboard()
                    )
                    
                    logger.info(f"✅ Пользователь {user_id} выбрал ввод своего жанра")
                    command_handled = True
                    return
                else:
                    # Сохраняем выбранный жанр
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.update_data(user_id, genre=text)
                    )
                    
                    # Сразу запускаем генерацию (без выбора пола вокалиста)
                    _sd = asyncio.get_event_loop().run_until_complete(
                        self.state_manager.get_data(user_id)
                    ) or {}
                    _lyrics = _sd.get('lyrics', '')
                    self.reset_state(user_id)
                    
                    self.send_message(
                        user_id=user_id,
                        message="🎵 Генерация началась!\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                        keyboard=self.get_cancel_keyboard()
                    )
                    
                    import threading as _threading
                    _threading.Thread(
                        target=self._launch_song_generation,
                        args=(user_id, _lyrics, text),
                        daemon=True
                    ).start()
                    
                    logger.info(f"✅ Пользователь {user_id} выбрал жанр: {text}, генерация запущена")
                    command_handled = True
                    return
                    
            # Обработка ввода своего жанра
            elif vk_state == States.WAITING_CUSTOM_GENRE:
                # Проверяем длину описания жанра
                MAX_GENRE_LENGTH = 400
                if len(text) > MAX_GENRE_LENGTH:
                    self.send_message(
                        user_id=user_id,
                        message=(
                            f"✂️ Описание жанра слишком длинное ({len(text)} символов).\n\n"
                            f"Пожалуйста, сократите до {MAX_GENRE_LENGTH} символов.\n"
                            f"Сейчас лишних: {len(text) - MAX_GENRE_LENGTH} символов.\n\n"
                            "Пример: «Энергичный поп-рок, яркие гитары, женский вокал»"
                        ),
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"⚠️ Пользователь {user_id} ввел слишком длинный жанр: {len(text)} символов")
                    command_handled = True
                    return
                
                # Сохраняем введенный пользователем жанр
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, genre=text)
                )
                
                # Сразу запускаем генерацию (без выбора пола вокалиста)
                _sd = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_data(user_id)
                ) or {}
                _lyrics = _sd.get('lyrics', '')
                self.reset_state(user_id)
                
                self.send_message(
                    user_id=user_id,
                    message="🎵 Генерация началась!\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                    keyboard=self.get_cancel_keyboard()
                )
                
                import threading as _threading
                _threading.Thread(
                    target=self._launch_song_generation,
                    args=(user_id, _lyrics, text),
                    daemon=True
                ).start()
                
                logger.info(f"✅ Пользователь {user_id} ввел свой жанр: {text}, генерация запущена")
                command_handled = True
                return
                
            # Обработка выбора пола вокалиста
            elif vk_state == States.WAITING_VOCAL_GENDER:
                # СРАЗУ отправляем сообщение о начале генерации (до любых операций)
                self.send_message(
                    user_id=user_id,
                    message="🎵 **Генерация началась!**\n\n🤖 Создаю новую песню...\n⏰ Это займет 3-5 минут",
                    keyboard=self.get_cancel_keyboard()
                )
                
                # Сохраняем выбранный пол вокалиста
                vocal_gender = "male"
                if "женский" in text_lower or text == "👩 Женский":
                    vocal_gender = "female"
                
                asyncio.get_event_loop().run_until_complete(
                    self.state_manager.update_data(user_id, vocal_gender=vocal_gender)
                )
                
                # Получаем данные пользователя
                state_data = asyncio.get_event_loop().run_until_complete(
                    self.state_manager.get_data(user_id)
                ) or {}
                
                # Получаем текст песни и жанр
                lyrics = state_data.get('lyrics', '')
                genre = state_data.get('genre', '')
                
                # Пробуем отправить GIF-анимацию (опционально, без блокировки)
                gif_path = '/root/albimusic-bot/robot_music.gif'
                try:
                    # Проверяем, существует ли файл
                    import os
                    if os.path.exists(gif_path):
                        # Отправляем GIF
                        from vk_api.upload import VkUpload
                        upload = VkUpload(self.vk_session)
                        doc = upload.document_message(gif_path, peer_id=user_id)
                        attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
                        
                        # Отправляем GIF как документ с обработкой ошибок
                        try:
                            self.vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                attachment=attachment
                            )
                        except Exception as gif_error:
                            logger.warning(f"⚠️ Не удалось отправить GIF: {gif_error}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке GIF: {e}")
                
                # Запускаем генерацию песни
                try:
                    # Переводим жанр на английский для Suno API (с improvements для лучшего результата)
                    translated_genre = translate_style_to_english(genre, add_improvements=True)
                    logger.info(f"🔄 Перевод жанра для песни: '{genre}' → '{translated_genre}'")
                    
                    # Формируем стиль с учетом пола вокалиста
                    style = f"{translated_genre}, {vocal_gender} vocals"
                    
                    # Проверяем длину текста песни и автоматически включаем customMode для длинных текстов
                    use_custom_mode = len(lyrics) > 500
                    if use_custom_mode:
                        logger.info(f"ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")
                    
                    # Запускаем генерацию песни
                    logger.info(f"🎵 Запуск генерации песни для пользователя {user_id}")
                    logger.info(f"🎵 Текст: {lyrics[:100]}...")
                    logger.info(f"🎵 Стиль: {style}")
                    logger.info(f"🎵 Custom Mode: {use_custom_mode}")
                    
                    # Запускаем генерацию в отдельном потоке, чтобы не блокировать бота
                    import threading
                    def generate_song_thread():
                        try:
                            # Генерируем песню (используем generate_suno_music_sync с параметром is_song=True)
                            result = generate_suno_music_sync(
                                prompt=lyrics,
                                is_song=True,
                                custom_mode=use_custom_mode,
                                user_id=user_id,
                                style=style
                            )
                            
                            if result:
                                # Проверяем формат результата
                                if isinstance(result, tuple) and len(result) == 3:
                                    audio_url, suno_task_id, suno_audio_id = result
                                elif isinstance(result, str):
                                    audio_url = result
                                    suno_task_id = None
                                    suno_audio_id = None
                                else:
                                    audio_url = str(result)
                                    suno_task_id = None
                                    suno_audio_id = None
                                
                                # Генерируем UUID для task_id базы данных
                                import uuid
                                db_task_id = str(uuid.uuid4())
                                
                                # Сохраняем результат в базу данных с status='completed'
                                execute_query_sync(
                                    'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_task_id, suno_audio_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                                    (user_id, db_task_id, style, audio_url, False, use_custom_mode, suno_task_id, suno_audio_id, 'completed')
                                )

                                # Проверяем: первая ли генерация пользователя (count=1 значит только что добавленная)
                                _first_gen_check_vk = execute_query_sync(
                                    "SELECT COUNT(*) FROM generations WHERE user_id = %s AND status = 'completed'",
                                    (user_id,)
                                )
                                _completed_count_vk = _first_gen_check_vk[0][0] if _first_gen_check_vk and _first_gen_check_vk[0] else 0
                                _is_first_vk_gen = (_completed_count_vk == 1)

                                # Импортируем клавиатуру с опциями
                                from vk_keyboards import get_song_options_keyboard

                                # Подготовка сообщения с результатом
                                message_text = f"✅ Ваша песня готова!\n\n🎵 Жанр: {genre}\n\n"
                                
                                # Проверяем, содержит ли audio_url несколько ссылок (JSON массив)
                                import urllib.parse as _urlparse
                                try:
                                    if isinstance(audio_url, str):
                                        audio_urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                                    else:
                                        audio_urls = [str(audio_url)]

                                    # Если есть несколько вариантов — указываем количество
                                    if len(audio_urls) > 1:
                                        message_text += f"🎼 Сгенерировано {len(audio_urls)} варианта\n\n"

                                except Exception as json_error:
                                    logger.error(f"❌ Ошибка при парсинге JSON аудио URL: {json_error}")
                                    audio_urls = [str(audio_url)]

                                # Отправляем сообщение с кнопками "Скачать"
                                from vk_keyboards import get_music_result_keyboard
                                song_keyboard = get_music_result_keyboard(audio_url)

                                self.send_message(
                                    user_id=user_id,
                                    message=message_text,
                                    keyboard=song_keyboard
                                )
                                
                                # Для первой генерации — демо + оффер 50₽ вместо опций
                                if _is_first_vk_gen:
                                    # Сохраняем в demo_tracks как НЕ разблокированное
                                    try:
                                        _urls_demo = json.loads(audio_url) if isinstance(audio_url, str) and audio_url.startswith('[') else [str(audio_url)]
                                        _full_url_1 = _urls_demo[0] if len(_urls_demo) > 0 else str(audio_url)
                                        _full_url_2 = _urls_demo[1] if len(_urls_demo) > 1 else _full_url_1
                                        execute_query_sync(
                                            """INSERT INTO demo_tracks (task_id, user_id, full_url_1, full_url_2, is_unlocked)
                                            VALUES (%s, %s, %s, %s, %s)
                                            ON CONFLICT (task_id) DO NOTHING""",
                                            (db_task_id, user_id, _full_url_1, _full_url_2, False)
                                        )
                                        logger.info(f"💾 VK первая генерация сохранена в demo_tracks: {db_task_id}")
                                    except Exception as _demo_err:
                                        logger.error(f"❌ Ошибка сохранения VK первой генерации в demo_tracks: {_demo_err}")

                                    # Создаём платёж YooKassa 50₽ для разблокировки опций
                                    _unlock_url = None
                                    try:
                                        from yookassa import Configuration, Payment as _YooPayment
                                        import uuid as _uuid_vk
                                        from vk_config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
                                        Configuration.account_id = YOOKASSA_SHOP_ID
                                        Configuration.secret_key = YOOKASSA_SECRET_KEY
                                        _idempotence_key = str(_uuid_vk.uuid4())
                                        _unlock_payment = _YooPayment.create({
                                            "amount": {"value": "50.00", "currency": "RUB"},
                                            "confirmation": {
                                                "type": "redirect",
                                                "return_url": "https://vk.com/club235442407"
                                            },
                                            "capture": True,
                                            "description": "Разблокировка полной версии трека ALBI Music",
                                            "metadata": {
                                                "user_id": str(user_id),
                                                "payment_type": "unlock_first",
                                                "task_id": db_task_id,
                                                "platform": "vk"
                                            }
                                        }, _idempotence_key)
                                        _unlock_url = _unlock_payment.confirmation.confirmation_url
                                        logger.info(f"💳 Создан платёж unlock_first для VK user {user_id}: {_unlock_payment.id}")
                                    except Exception as _pay_err:
                                        logger.error(f"❌ Ошибка создания платежа unlock_first VK: {_pay_err}")

                                    # Отправляем предупреждение о демо и оффер 50₽
                                    _demo_msg = (
                                        "⚠️ Это демо-версия твоей первой песни.\n\n"
                                        "🔓 Разблокируй ПОЛНЫЕ функции за 50₽:\n"
                                        "• Минусовка — версия без вокала\n"
                                        "• Кавер — перепой в другом жанре\n"
                                        "• В WAV — профессиональный формат\n"
                                        "• Поделиться — опубликовать трек\n\n"
                                        "👇 Нажми кнопку для оплаты:"
                                    )
                                    if _unlock_url:
                                        from vk_keyboards import get_payment_keyboard
                                        self.send_message(
                                            user_id=user_id,
                                            message=_demo_msg,
                                            keyboard=get_payment_keyboard(_unlock_url)
                                        )
                                    else:
                                        self.send_message(
                                            user_id=user_id,
                                            message=_demo_msg + "\n\nДля оплаты перейдите в раздел «Баланс»."
                                        )

                                # Для обычных пользователей — показываем опции (минусовка и т.д.)
                                elif suno_task_id:
                                    options_text = (
                                        "💎 Что можно сделать с этой песней:\n\n"
                                        "🎤 Минусовка — версия без вокала\n"
                                        "🎸 Кавер — перепой в другом жанре\n"
                                        "🎵 В WAV — конвертация в WAV формат\n"
                                        "🔗 Поделиться — опубликовать трек"
                                    )

                                    self.send_message(
                                        user_id=user_id,
                                        message=options_text,
                                        keyboard=get_song_options_keyboard(db_task_id)
                                    )
                                
                                # Списываем баланс
                                execute_query_sync(
                                    "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                    (user_id,)
                                )
                                logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")

                                # ✅ Начисляем реферальный бонус пригласившему (если это первая генерация)
                                self._award_referral_bonus(user_id)

                                # Помечаем в БД как уже доставленное (чтобы Telegram-монитор не отправил дубль)
                                try:
                                    execute_query_sync(
                                        "UPDATE generations SET audio_url = %s WHERE task_id = %s",
                                        (f"ALREADY_SENT_{audio_url}", db_task_id)
                                    )
                                except Exception as mark_err:
                                    logger.warning(f"⚠️ Не удалось пометить генерацию как отправленную: {mark_err}")

                                # ✅ Upsell после результата — показывать ВСЕГДА (пока эмоции свежи)
                                try:
                                    bal_result = execute_query_sync(
                                        "SELECT balance FROM users WHERE user_id = %s", (user_id,)
                                    )
                                    new_balance = bal_result[0][0] if bal_result and bal_result[0] else 0
                                    total_users_res = execute_query_sync("SELECT COUNT(*) FROM users")
                                    total_users = total_users_res[0][0] if total_users_res else 658
                                    from vk_keyboards import get_buy_more_keyboard
                                    if new_balance <= 0:
                                        # Токены закончились — сильный пейволл с соц. доказательством
                                        self.send_message(
                                            user_id=user_id,
                                            message=(
                                                f"🎵 Понравилось? Уже {total_users}+ музыкантов создают треки в ALBI!\n\n"
                                                "⚠️ Токены закончились. Пополните баланс:\n"
                                                "🎁 5 треков — 99₽ (выгоднее всего для старта)\n"
                                                "💳 10 треков — 250₽\n\n"
                                                "🤝 Или пригласите друга — получите 2 токена бесплатно!"
                                            ),
                                            keyboard=get_buy_more_keyboard()
                                        )
                                    else:
                                        # Баланс есть — лёгкий upsell
                                        self.send_message(
                                            user_id=user_id,
                                            message=(
                                                f"💡 Осталось токенов: {new_balance} | "
                                                "Пополните заранее — чтобы не прерываться на вдохновении!"
                                            ),
                                            keyboard=get_buy_more_keyboard()
                                        )
                                except Exception as bal_err:
                                    logger.warning(f"⚠️ Ошибка upsell после генерации: {bal_err}")
                            else:
                                # Если не удалось сгенерировать песню
                                self.send_message(
                                    user_id=user_id,
                                    message="❌ Не удалось сгенерировать песню. Попробуйте другой жанр или позже.",
                                    keyboard=self.get_main_keyboard(user_id)
                                )
                        except Exception as e:
                            logger.error(f"❌ Ошибка генерации песни: {e}")
                            logger.error(traceback.format_exc())
                            self.send_message(
                                user_id=user_id,
                                message="❌ Произошла ошибка при генерации песни. Попробуйте позже.",
                                keyboard=self.get_main_keyboard(user_id)
                            )
                    
                    # Запускаем генерацию в отдельном потоке
                    thread = threading.Thread(target=generate_song_thread)
                    thread.start()
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка запуска генерации песни: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при запуске генерации песни. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                
                # Сбрасываем состояние пользователя
                self.reset_state(user_id)
                
                logger.info(f"✅ Пользователь {user_id} выбрал пол вокалиста: {vocal_gender}")
                command_handled = True
                return

            # Обработка выбора жанра для инструментальной музыки
            elif vk_state == States.WAITING_MUSIC_STYLE:
                # Проверяем, выбрал ли пользователь "Свой вариант"
                if "свой вариант" in text_lower:
                    asyncio.get_event_loop().run_until_complete(
                        self.state_manager.set_state(user_id, States.WAITING_CUSTOM_STYLE)
                    )
                    self.send_message(
                        user_id=user_id,
                        message=(
                            "✏️ Опишите стиль и жанр музыки своими словами:\n\n"
                            "⚠️ Максимальная длина описания — 400 символов.\n"
                            "Пример: «медленный джаз с саксофоном» или «агрессивный дабстеп»"
                        ),
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"✅ Пользователь {user_id} выбрал ввод своего стиля для инструментала")
                    command_handled = True
                    return

                genre = text  # Выбранный жанр

                # Переводим жанр на английский для Suno API
                translated_genre = translate_style_to_english(genre, add_improvements=False)
                logger.info(f"🔄 Перевод жанра для музыки: '{genre}' → '{translated_genre}'")

                # Используем переведенный жанр
                genre = translated_genre
                logger.info(f"🎶 Пользователь {user_id} выбрал жанр для инструментала: {genre}")

                # Сбрасываем состояние ДО запуска потока
                self.reset_state(user_id)

                # Отправляем сообщение о начале генерации
                self.send_message(
                    user_id=user_id,
                    message="🎵 Генерация началась. Это займет 3-5 минут. Результат пришлю сюда в чат"
                )

                # Пробуем отправить GIF
                gif_path = '/root/albimusic-bot/robot_music.gif'
                try:
                    import os
                    if os.path.exists(gif_path):
                        from vk_api.upload import VkUpload
                        upload = VkUpload(self.vk_session)
                        doc = upload.document_message(gif_path, peer_id=user_id)
                        attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
                        try:
                            self.vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                attachment=attachment
                            )
                        except Exception as gif_err:
                            logger.warning(f"⚠️ Не удалось отправить GIF: {gif_err}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка GIF при генерации музыки: {e}")

                # Запускаем генерацию в отдельном потоке
                import threading
                _genre = genre
                _uid = user_id

                def generate_instrumental_thread():
                    try:
                        result = generate_suno_music_sync(
                            prompt=_genre,
                            is_song=False,
                            custom_mode=False,
                            user_id=_uid
                        )

                        if result:
                            # Проверяем формат результата (может быть tuple или строка)
                            if isinstance(result, tuple) and len(result) == 3:
                                audio_url, suno_task_id, suno_audio_id = result
                            elif isinstance(result, str):
                                audio_url = result
                                suno_task_id = None
                                suno_audio_id = None
                            else:
                                audio_url = str(result)
                                suno_task_id = None
                                suno_audio_id = None
                            
                            # Генерируем UUID для task_id базы данных
                            import uuid
                            db_task_id = str(uuid.uuid4())
                            
                            # Сохраняем в БД со status='completed'
                            try:
                                execute_query_sync(
                                    'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_task_id, suno_audio_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                                    (_uid, db_task_id, _genre, audio_url, False, False, suno_task_id, suno_audio_id, 'completed')
                                )
                            except Exception as db_err:
                                logger.error(f"❌ Ошибка сохранения музыки в БД: {db_err}")

                            # Парсим URL: может быть JSON-массив из 2 ссылок
                            try:
                                import json as _json
                                if isinstance(audio_url, str):
                                    urls = _json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                                else:
                                    urls = [str(audio_url)]
                            except Exception:
                                urls = [str(audio_url)]

                            # Сообщение о готовой инструментальной музыке
                            result_msg = (
                                f"✅ Ваша инструментальная музыка готова!\n\n"
                                f"🎵 Жанр: {_genre}\n\n"
                            )

                            if len(urls) > 1:
                                result_msg += f"🎼 Сгенерировано {len(urls)} варианта\n\n"

                            result_msg += "🎧 Нажмите «Слушать» чтобы открыть плеер, или «Скачать» для сохранения файла."

                            # Отправляем сообщение с кнопками "Скачать"
                            from vk_keyboards import get_music_result_keyboard
                            music_keyboard = get_music_result_keyboard(audio_url)

                            self.send_message(
                                user_id=_uid,
                                message=result_msg,
                                keyboard=music_keyboard
                            )
                            
                            # Затем отправляем главное меню отдельным сообщением
                            self.send_message(
                                user_id=_uid,
                                message="Что делаем дальше?",
                                keyboard=self.get_main_keyboard(_uid)
                            )

                            # Списываем 1 токен
                            try:
                                execute_query_sync(
                                    "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                                    (_uid,)
                                )
                                logger.info(f"💰 Списан 1 токен за инструментальную музыку: пользователь {_uid}")
                            except Exception as bal_err:
                                logger.error(f"❌ Ошибка списания баланса за музыку: {bal_err}")
                        else:
                            self.send_message(
                                user_id=_uid,
                                message="❌ Не удалось сгенерировать музыку. Попробуйте другой жанр или позже.",
                                keyboard=self.get_main_keyboard(_uid)
                            )
                    except Exception as e:
                        logger.error(f"❌ Ошибка в потоке генерации музыки: {e}")
                        logger.error(traceback.format_exc())
                        self.send_message(
                            user_id=_uid,
                            message="❌ Произошла ошибка при генерации музыки. Попробуйте позже.",
                            keyboard=self.get_main_keyboard(_uid)
                        )

                music_thread = threading.Thread(target=generate_instrumental_thread, daemon=True)
                music_thread.start()

                command_handled = True
                return

            # Обработка ввода своего стиля для инструментальной музыки (после выбора "Свой вариант")
            elif vk_state == States.WAITING_CUSTOM_STYLE:
                # Проверяем длину описания стиля
                MAX_GENRE_LENGTH = 400
                if len(text) > MAX_GENRE_LENGTH:
                    self.send_message(
                        user_id=user_id,
                        message=(
                            f"✂️ Описание стиля слишком длинное ({len(text)} символов).\n\n"
                            f"Пожалуйста, сократите до {MAX_GENRE_LENGTH} символов.\n"
                            f"Сейчас лишних: {len(text) - MAX_GENRE_LENGTH} символов.\n\n"
                            "Пример: «медленный джаз с саксофоном» или «агрессивный дабстеп»"
                        ),
                        keyboard=self.get_cancel_keyboard()
                    )
                    logger.info(f"⚠️ Пользователь {user_id} ввел слишком длинный стиль: {len(text)} символов")
                    command_handled = True
                    return

                genre = text  # Пользователь ввёл свой стиль

                # Переводим жанр на английский для Suno API
                translated_genre = translate_style_to_english(genre, add_improvements=False)
                logger.info(f"🔄 Перевод своего стиля для музыки: '{genre}' → '{translated_genre}'")

                genre = translated_genre
                logger.info(f"🎶 Пользователь {user_id} ввёл свой жанр для инструментала: {genre}")

                # Сбрасываем состояние ДО запуска потока
                self.reset_state(user_id)

                # Отправляем сообщение о начале генерации
                self.send_message(
                    user_id=user_id,
                    message="🎵 Генерация началась. Это займет 3-5 минут. Результат пришлю сюда в чат",
                    keyboard=self.get_main_keyboard(user_id)
                )

                # Запускаем генерацию в отдельном потоке
                import threading
                _genre_cs = genre
                _uid_cs = user_id

                def generate_custom_instrumental_thread():
                    try:
                        result = generate_suno_music_sync(
                            prompt=_genre_cs,
                            is_song=False,
                            custom_mode=False,
                            user_id=_uid_cs
                        )

                        if result:
                            audio_url = None
                            suno_task_id = None
                            suno_audio_id = None
                            if isinstance(result, tuple):
                                audio_url = result[0] if len(result) > 0 else None
                                suno_task_id = result[1] if len(result) > 1 else None
                                suno_audio_id = result[2] if len(result) > 2 else None
                            else:
                                audio_url = result

                            if audio_url:
                                import uuid
                                db_task_id = str(uuid.uuid4())
                                try:
                                    execute_query_sync(
                                        'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_task_id, suno_audio_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                                        (_uid_cs, db_task_id, _genre_cs, audio_url, False, False, suno_task_id, suno_audio_id, 'completed')
                                    )
                                except Exception as db_err:
                                    logger.error(f"❌ Ошибка записи в БД: {db_err}")

                                self.send_message(
                                    user_id=_uid_cs,
                                    message=(
                                        f"✅ Ваша инструментальная музыка готова!\n\n"
                                        f"🎵 Стиль: {_genre_cs}\n\n"
                                    ),
                                    keyboard=self.get_main_keyboard(_uid_cs)
                                )
                                self.send_message(
                                    user_id=_uid_cs,
                                    message=f"🔗 Слушать: {audio_url}"
                                )
                                logger.info(f"✅ Инструментальная музыка готова для {_uid_cs}: {audio_url}")
                            else:
                                self.send_message(
                                    user_id=_uid_cs,
                                    message="❌ Не удалось получить аудио. Попробуйте другой стиль или позже.",
                                    keyboard=self.get_main_keyboard(_uid_cs)
                                )
                        else:
                            self.send_message(
                                user_id=_uid_cs,
                                message="❌ Не удалось сгенерировать музыку. Попробуйте другой стиль или позже.",
                                keyboard=self.get_main_keyboard(_uid_cs)
                            )
                    except Exception as e:
                        logger.error(f"❌ Ошибка в потоке генерации своего стиля: {e}")
                        logger.error(traceback.format_exc())
                        self.send_message(
                            user_id=_uid_cs,
                            message="❌ Произошла ошибка при генерации. Попробуйте позже.",
                            keyboard=self.get_main_keyboard(_uid_cs)
                        )

                cs_thread = threading.Thread(target=generate_custom_instrumental_thread, daemon=True)
                cs_thread.start()

                command_handled = True
                return

            # Если команда не была обработана выше
            if not command_handled:
                # Если команда всё ещё не обработана - отправляем сообщение о неизвестной команде
                    logger.warning(f"❓ Неизвестная команда от {user_id}: '{text}' (в нижнем регистре: '{text_lower}')")
                    keyboard = self.get_main_keyboard(user_id)
                    if keyboard:
                        result = self.send_message(
                            user_id=user_id,
                            message="Я не понимаю эту команду. Воспользуйтесь меню 👇",
                            keyboard=keyboard
                        )
                        logger.info(f"📨 Отправка сообщения с меню: {'успешно' if result else 'ошибка'}")
                    else:
                        logger.error("❌ Не удалось создать клавиатуру для обычного сообщения")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.error(traceback.format_exc())
            
            # Пытаемся сбросить состояние пользователя и отправить сообщение об ошибке
            try:
                self.reset_state(user_id)
                self.send_message(
                    user_id=user_id,
                    message="Произошла ошибка при обработке сообщения. Попробуйте начать сначала.",
                    keyboard=self.get_main_keyboard(user_id)
                )
                logger.info(f"✅ Состояние пользователя {user_id} сброшено после ошибки")
            except Exception as inner_e:
                logger.error(f"❌ Ошибка при восстановлении после ошибки: {inner_e}")
            
    def start_music_generation(self, user_id, genre):
        """Запуск генерации инструментальной музыки"""
        try:
            # Отправляем сообщение о начале генерации
            self.send_message(
                user_id=user_id,
                message="⏳ Генерирую музыку, подождите 1-2 минуты...",
                keyboard=self.get_cancel_keyboard()
            )
            
            print(f"Запуск генерации музыки для пользователя {user_id}, жанр: {genre}")
            logger.info(f"🎵 Запуск генерации музыки для пользователя {user_id}, жанр: {genre}")
            
            # Запускаем генерацию музыки через Celery
            try:
                # Генерируем музыку
                audio_url = generate_suno_music_sync(
                    prompt=genre,
                    is_song=False,
                    custom_mode=False,
                    user_id=user_id
                )
                
                if audio_url:
                    # Сохраняем результат в базу данных
                    try:
                        execute_query_sync(
                            'INSERT INTO generations (user_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s)',
                            (user_id, genre, audio_url, False, False)
                        )
                        logger.info(f"✅ Результат генерации музыки сохранен в базе данных для пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения результата генерации музыки в базе данных: {e}")
                    
                    # Отправляем результат пользователю
                    self.send_message(
                        user_id=user_id,
                        message=f"✅ Ваша музыка готова!\n\nЖанр: {genre}\n\nСсылка: {audio_url}",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    
                    # Списываем баланс
                    try:
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")

                        # ✅ Реферальный бонус (если первая генерация приглашённого)
                        self._award_referral_bonus(user_id)

                        # ✅ Upsell после результата
                        try:
                            _b = execute_query_sync("SELECT balance FROM users WHERE user_id = %s", (user_id,))
                            _nb = _b[0][0] if _b and _b[0] else 0
                            _tu = execute_query_sync("SELECT COUNT(*) FROM users")
                            _total = _tu[0][0] if _tu else 658
                            from vk_keyboards import get_buy_more_keyboard
                            if _nb <= 0:
                                self.send_message(
                                    user_id=user_id,
                                    message=(
                                        f"🎵 Понравилось? Уже {_total}+ музыкантов создают треки в ALBI!\n\n"
                                        "⚠️ Токены закончились. Пополните баланс:\n"
                                        "🎁 5 треков — 99₽ (выгоднее всего для старта)\n"
                                        "💳 10 треков — 250₽\n\n"
                                        "🤝 Или пригласите друга — получите 2 токена бесплатно!"
                                    ),
                                    keyboard=get_buy_more_keyboard()
                                )
                            else:
                                self.send_message(
                                    user_id=user_id,
                                    message=(
                                        f"💡 Осталось токенов: {_nb} | "
                                        "Пополните заранее — чтобы не прерываться на вдохновении!"
                                    ),
                                    keyboard=get_buy_more_keyboard()
                                )
                        except Exception as _ue:
                            logger.warning(f"⚠️ Ошибка upsell после генерации музыки: {_ue}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка списания баланса: {e}")
                else:
                    # Если не удалось сгенерировать музыку
                    self.send_message(
                        user_id=user_id,
                        message="❌ Не удалось сгенерировать музыку. Попробуйте другой жанр или позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка генерации музыки: {e}")
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при генерации музыки. Попробуйте позже.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            
            # Сбрасываем состояние пользователя
            self.reset_state(user_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска генерации музыки: {e}")
            self.send_message(
                user_id=user_id,
                message="❌ Произошла ошибка. Попробуйте позже.",
                keyboard=self.get_main_keyboard(user_id)
            )
            self.reset_state(user_id)
    
    def start_song_generation(self, user_id, lyrics, genre):
        """Запуск генерации песни с текстом"""
        try:
            # Отправляем сообщение о начале генерации
            self.send_message(
                user_id=user_id,
                message="⏳ Генерирую песню, подождите 1-2 минуты...",
                keyboard=self.get_cancel_keyboard()
            )
            
            print(f"Запуск генерации песни для пользователя {user_id}, жанр: {genre}")
            logger.info(f"🎵 Запуск генерации песни для пользователя {user_id}, жанр: {genre}")
            
            # Запускаем генерацию песни через Celery
            try:
                # Проверяем длину текста песни и автоматически включаем customMode для длинных текстов
                use_custom_mode = len(lyrics) > 500
                if use_custom_mode:
                    logger.info(f"ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")
                
                # Генерируем песню (используем generate_suno_music_sync с is_song=True)
                result = generate_suno_music_sync(
                    prompt=lyrics,
                    is_song=True,
                    custom_mode=use_custom_mode,
                    user_id=user_id,
                    style=genre
                )
                
                if result:
                    audio_url, suno_task_id, suno_audio_id = result
                    
                    # Генерируем UUID для task_id базы данных
                    import uuid
                    db_task_id = str(uuid.uuid4())
                    
                    # Сохраняем результат в базу данных со status='completed'
                    try:
                        execute_query_sync(
                            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_task_id, suno_audio_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                            (user_id, db_task_id, genre, audio_url, False, use_custom_mode, suno_task_id, suno_audio_id, 'completed')
                        )
                        logger.info(f"✅ Результат генерации песни сохранен в базе данных для пользователя {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения результата генерации песни в базе данных: {e}")
                    
                    # Импортируем клавиатуру с опциями
                    from vk_keyboards import get_song_options_keyboard
                    
                    # Подготовка сообщения с результатом
                    message_text = f"✅ Ваша песня готова!\n\nЖанр: {genre}\n\n"
                    
                    # Проверяем, содержит ли audio_url несколько ссылок (JSON массив)
                    try:
                        audio_urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                        
                        # Если есть несколько ссылок, добавляем их все в сообщение
                        if len(audio_urls) > 1:
                            message_text += "🎵 **Варианты песни:**\n\n"
                            for i, url in enumerate(audio_urls, 1):
                                message_text += f"Вариант {i}: {url}\n\n"
                        else:
                            message_text += f"Ссылка: {audio_url}\n\n"
                    except Exception as json_error:
                        # Если не удалось распарсить JSON, логируем ошибку и используем строку как есть
                        logger.error(f"❌ Ошибка при парсинге JSON аудио URL: {json_error}")
                        message_text += f"Ссылка: {audio_url}\n\n"
                    
                    # Добавляем информацию о возможных действиях
                    message_text += "💎 **Что можно сделать с этой песней:**\n\n"
                    message_text += "🎤 **Минусовка** (1 токен) — версия без вокала для исполнения\n"
                    message_text += "🎸 **Кавер** (1 токен) — перепой в другом стиле/жанре\n"
                    message_text += "🎵 **В WAV** (2 токена) — конвертируй в WAV формат для профи\n"
                    message_text += "🔗 **Поделиться** — опубликуй трек на своей странице ВКонтакте"
                    
                    # Отправляем результат пользователю с клавиатурой опций
                    self.send_message(
                        user_id=user_id,
                        message=message_text,
                        keyboard=get_song_options_keyboard(db_task_id)
                    )
                    
                    # Списываем баланс
                    try:
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")

                        # ✅ Начисляем реферальный бонус (если это первая генерация приглашённого)
                        self._award_referral_bonus(user_id)

                        # ✅ Upsell после результата — показывать ВСЕГДА
                        try:
                            bal_res2 = execute_query_sync(
                                "SELECT balance FROM users WHERE user_id = %s", (user_id,)
                            )
                            new_bal2 = bal_res2[0][0] if bal_res2 and bal_res2[0] else 0
                            total_u2 = execute_query_sync("SELECT COUNT(*) FROM users")
                            total_users2 = total_u2[0][0] if total_u2 else 658
                            from vk_keyboards import get_buy_more_keyboard
                            if new_bal2 <= 0:
                                self.send_message(
                                    user_id=user_id,
                                    message=(
                                        f"🎵 Понравилось? Уже {total_users2}+ музыкантов создают треки в ALBI!\n\n"
                                        "⚠️ Токены закончились. Пополните баланс:\n"
                                        "🎁 5 треков — 99₽ (выгоднее всего для старта)\n"
                                        "💳 10 треков — 250₽\n\n"
                                        "🤝 Или пригласите друга — получите 2 токена бесплатно!"
                                    ),
                                    keyboard=get_buy_more_keyboard()
                                )
                            else:
                                self.send_message(
                                    user_id=user_id,
                                    message=(
                                        f"💡 Осталось токенов: {new_bal2} | "
                                        "Пополните заранее — чтобы не прерываться на вдохновении!"
                                    ),
                                    keyboard=get_buy_more_keyboard()
                                )
                        except Exception as upsell_e:
                            logger.warning(f"⚠️ Ошибка upsell после генерации: {upsell_e}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка списания баланса: {e}")
                else:
                    # Если не удалось сгенерировать песню
                    self.send_message(
                        user_id=user_id,
                        message="❌ Не удалось сгенерировать песню. Попробуйте другой жанр или позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка генерации песни: {e}")
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при генерации песни. Попробуйте позже.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            
            # Сбрасываем состояние пользователя
            self.reset_state(user_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска генерации песни: {e}")
            self.send_message(
                user_id=user_id,
                message="❌ Произошла ошибка. Попробуйте позже.",
                keyboard=self.get_main_keyboard(user_id)
            )
            self.reset_state(user_id)
    
    # ════════════════════════════════════════════════════════════════
    # ГЕНЕРАЦИЯ ПЕСНИ — вспомогательный метод (запускается в треде)
    # ════════════════════════════════════════════════════════════════

    def _launch_song_generation(self, user_id, lyrics, genre):
        """Генерация песни: переводит жанр, вызывает Suno API, отправляет результат.
        Пол вокала НЕ задаётся принудительно — пользователь может указать его
        в тексте жанра (например: «рок, женский вокал» или «хор, детские голоса»).
        Запускается в отдельном потоке."""
        try:
            # Переводим жанр на английский для Suno API
            translated_genre = translate_style_to_english(genre, add_improvements=True)
            logger.info(f"🔄 Перевод жанра для песни: '{genre}' → '{translated_genre}'")

            # Стиль = жанр без принудительного пола вокала
            style = translated_genre

            # Включаем customMode для длинных текстов
            use_custom_mode = len(lyrics) > 500
            if use_custom_mode:
                logger.info(f"ℹ️ Автоматически включен customMode из-за длины текста ({len(lyrics)} символов)")

            logger.info(f"🎵 Запуск генерации песни для пользователя {user_id}")
            logger.info(f"🎵 Текст: {lyrics[:100]}...")
            logger.info(f"🎵 Стиль: {style}")

            # Пробуем отправить GIF-анимацию (опционально, без блокировки)
            gif_path = '/root/albimusic-bot/robot_music.gif'
            try:
                import os
                if os.path.exists(gif_path):
                    from vk_api.upload import VkUpload
                    upload = VkUpload(self.vk_session)
                    doc = upload.document_message(gif_path, peer_id=user_id)
                    attachment = f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}"
                    try:
                        self.vk.messages.send(
                            user_id=user_id,
                            random_id=get_random_id(),
                            attachment=attachment
                        )
                    except Exception as gif_error:
                        logger.warning(f"⚠️ Не удалось отправить GIF: {gif_error}")
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке GIF: {e}")

            # Запускаем генерацию
            result = generate_suno_music_sync(
                prompt=lyrics,
                is_song=True,
                custom_mode=use_custom_mode,
                user_id=user_id,
                style=style
            )

            if result:
                if isinstance(result, tuple) and len(result) == 3:
                    audio_url, suno_task_id, suno_audio_id = result
                elif isinstance(result, str):
                    audio_url = result
                    suno_task_id = None
                    suno_audio_id = None
                else:
                    audio_url = str(result)
                    suno_task_id = None
                    suno_audio_id = None

                import uuid
                db_task_id = str(uuid.uuid4())

                execute_query_sync(
                    'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode, suno_task_id, suno_audio_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (user_id, db_task_id, style, audio_url, False, use_custom_mode, suno_task_id, suno_audio_id, 'completed')
                )

                from vk_keyboards import get_song_options_keyboard
                from vk_keyboards import get_music_result_keyboard

                message_text = f"✅ Ваша песня готова!\n\n🎵 Жанр: {genre}\n\n"

                try:
                    audio_urls = json.loads(audio_url) if isinstance(audio_url, str) and audio_url.startswith('[') else [audio_url]
                    if len(audio_urls) > 1:
                        message_text += f"🎼 Сгенерировано {len(audio_urls)} варианта\n\n"
                except Exception:
                    audio_urls = [str(audio_url)]

                song_keyboard = get_music_result_keyboard(audio_url)
                self.send_message(user_id=user_id, message=message_text, keyboard=song_keyboard)

                if suno_task_id:
                    options_text = (
                        "💎 Что можно сделать с этой песней:\n\n"
                        "🎤 Минусовка — версия без вокала\n"
                        "🎸 Кавер — перепой в другом жанре\n"
                        "🎵 В WAV — конвертация в WAV формат\n"
                        "🔗 Поделиться — опубликовать трек"
                    )
                    self.send_message(
                        user_id=user_id,
                        message=options_text,
                        keyboard=get_song_options_keyboard(db_task_id)
                    )

                execute_query_sync(
                    "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                    (user_id,)
                )
                logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id}")

                # ✅ Реферальный бонус (если первая генерация приглашённого)
                self._award_referral_bonus(user_id)

                try:
                    execute_query_sync(
                        "UPDATE generations SET audio_url = %s WHERE task_id = %s",
                        (f"ALREADY_SENT_{audio_url}", db_task_id)
                    )
                except Exception as mark_err:
                    logger.warning(f"⚠️ Не удалось пометить генерацию как отправленную: {mark_err}")

                # ✅ Upsell после результата — ВСЕГДА (пока эмоции свежи)
                try:
                    bal_result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s", (user_id,)
                    )
                    new_balance = bal_result[0][0] if bal_result and bal_result[0] else 0
                    total_users_res3 = execute_query_sync("SELECT COUNT(*) FROM users")
                    total_users3 = total_users_res3[0][0] if total_users_res3 else 658
                    from vk_keyboards import get_buy_more_keyboard
                    if new_balance <= 0:
                        self.send_message(
                            user_id=user_id,
                            message=(
                                f"🎵 Понравилось? Уже {total_users3}+ музыкантов создают треки в ALBI!\n\n"
                                "⚠️ Токены закончились. Пополните баланс:\n"
                                "🎁 5 треков — 99₽ (выгоднее всего для старта)\n"
                                "💳 10 треков — 250₽\n\n"
                                "🤝 Или пригласите друга — получите 2 токена бесплатно!"
                            ),
                            keyboard=get_buy_more_keyboard()
                        )
                    else:
                        self.send_message(
                            user_id=user_id,
                            message=(
                                f"💡 Осталось токенов: {new_balance} | "
                                "Пополните заранее — чтобы не прерываться на вдохновении!"
                            ),
                            keyboard=get_buy_more_keyboard()
                        )
                except Exception as bal_err:
                    logger.warning(f"⚠️ Ошибка upsell после генерации: {bal_err}")
            else:
                self.send_message(
                    user_id=user_id,
                    message="❌ Не удалось сгенерировать песню. Попробуйте другой жанр или позже.",
                    keyboard=self.get_main_keyboard(user_id)
                )
        except Exception as e:
            logger.error(f"❌ Ошибка генерации песни: {e}")
            logger.error(traceback.format_exc())
            self.send_message(
                user_id=user_id,
                message="❌ Произошла ошибка при генерации песни. Попробуйте позже.",
                keyboard=self.get_main_keyboard(user_id)
            )

    # ════════════════════════════════════════════════════════════════
    # РАССЫЛКА — методы
    # ════════════════════════════════════════════════════════════════

    def _handle_broadcast_start(self, user_id):
        """Начать процесс рассылки: перевести администратора в состояние ввода текста"""
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.set_state(user_id, States.WAITING_BROADCAST_TEXT)
        )
        self.send_message(
            user_id,
            "📨 **РАССЫЛКА ALBI MUSIC**\n\n"
            "Отправьте текст сообщения для рассылки всем пользователям.\n\n"
            "⚠️ Напишите «отмена» для отмены."
        )

    def _handle_broadcast_text(self, user_id, text):
        """Получить текст рассылки и показать предпросмотр с кнопками подтверждения"""
        if not HAS_VK_ADMIN:
            self.send_message(user_id, "❌ Модуль vk_admin не найден — рассылка недоступна")
            asyncio.get_event_loop().run_until_complete(self.state_manager.finish(user_id))
            return

        total_users = len(get_vk_user_ids()) if HAS_VK_ADMIN else 0
        confirmation_text = format_broadcast_confirmation(text, total_users)

        # Сохраняем текст в данных состояния
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.update_data(user_id, broadcast_text=text)
        )
        asyncio.get_event_loop().run_until_complete(
            self.state_manager.set_state(user_id, States.WAITING_BROADCAST_CONFIRM)
        )

        from vk_api.keyboard import VkKeyboard, VkKeyboardColor
        keyboard = VkKeyboard(inline=True)
        keyboard.add_callback_button(
            "✅ Отправить всем",
            color=VkKeyboardColor.POSITIVE,
            payload={"cmd": "broadcast_confirm"}
        )
        keyboard.add_callback_button(
            "❌ Отмена",
            color=VkKeyboardColor.NEGATIVE,
            payload={"cmd": "broadcast_cancel"}
        )

        self.send_message(user_id, confirmation_text, keyboard=keyboard)

    def _handle_broadcast_confirm(self, user_id):
        """Выполнить рассылку после подтверждения"""
        if not HAS_VK_ADMIN:
            self.send_message(user_id, "❌ Модуль vk_admin не найден")
            asyncio.get_event_loop().run_until_complete(self.state_manager.finish(user_id))
            return

        data = asyncio.get_event_loop().run_until_complete(
            self.state_manager.get_data(user_id)
        )

        if not data or 'broadcast_text' not in data:
            self.send_message(
                user_id,
                "❌ Ошибка: текст рассылки не найден. Начните заново.",
                keyboard=self.get_main_keyboard(user_id)
            )
            asyncio.get_event_loop().run_until_complete(self.state_manager.finish(user_id))
            return

        text = data['broadcast_text']

        # Сбрасываем состояние ДО рассылки
        asyncio.get_event_loop().run_until_complete(self.state_manager.finish(user_id))

        user_ids = get_vk_user_ids()

        self.send_message(
            user_id,
            f"🚀 **Рассылка запущена!**\n\n"
            f"📨 Начинаю отправку {len(user_ids)} VK-пользователям...\n"
            f"⏳ Пришлю итог когда закончу."
        )

        sent = 0
        errors = 0
        for target_uid in user_ids:
            try:
                self.send_message(target_uid, text)
                sent += 1
                time.sleep(0.5)  # Задержка против антиспама VK
            except Exception as e:
                logger.warning(f"Ошибка отправки пользователю {target_uid}: {e}")
                errors += 1

        result_text = format_broadcast_result(sent, errors)
        self.send_message(user_id, result_text, keyboard=self.get_main_keyboard(user_id))
        logger.info(f"✅ Рассылка завершена: отправлено {sent}, ошибок {errors}")

    def handle_callback(self, event):
        """Обработчик событий от кнопок (callback)"""
        try:
            # Получаем данные из события
            user_id = event.obj.get('user_id')
            payload = event.obj.get('payload', {})
            
            logger.info(f"📩 Получено событие от кнопки от {user_id}: {payload}")
            print(f"Получен callback: {payload}")
            
            # Проверяем наличие payload
            if not payload:
                logger.error("❌ Пустой payload в событии от кнопки")
                return
            
            # Преобразуем payload в словарь, если он строка
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception as e:
                    logger.error(f"❌ Ошибка при разборе payload: {e}")
                    return
            
            # Обработка различных действий из payload
            action = payload.get('action')
            task_id_from_payload = payload.get('task_id', '')

            # ──── ADMIN CMD-КНОПКИ (рассылка) ────
            cmd = payload.get('cmd')
            if cmd:
                if cmd == 'admin_broadcast':
                    if user_id in ADMIN_IDS:
                        self._handle_broadcast_start(user_id)
                    else:
                        self.send_message(user_id, "❌ Доступ запрещён")
                    return
                elif cmd == 'broadcast_confirm':
                    if user_id in ADMIN_IDS:
                        self._handle_broadcast_confirm(user_id)
                    return
                elif cmd == 'broadcast_cancel':
                    if user_id in ADMIN_IDS:
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.finish(user_id)
                        )
                        self.send_message(
                            user_id,
                            "❌ Рассылка отменена",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                    return

            # Обработка кнопок оплаты
            if action == "payment":
                amount = payload.get('amount', 0)
                logger.info(f"💳 Запрос на оплату от пользователя {user_id}, сумма: {amount}₽")
                
                try:
                    # Импортируем модуль для работы с YooKassa
                    try:
                        from yookassa import Configuration, Payment
                        import uuid
                        from vk_config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
                        Configuration.account_id = YOOKASSA_SHOP_ID
                        Configuration.secret_key = YOOKASSA_SECRET_KEY
                    except ImportError as e:
                        logger.error(f"❌ Не найдены настройки YooKassa: {e}")
                        self.send_message(
                            user_id=user_id,
                            message="❌ Оплата временно недоступна. Обратитесь в поддержку.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        return
                    
                    # Определяем количество токенов по сумме
                    tokens_map = {
                        50: 1,
                        250: 10,
                        500: 25,
                        1000: 60,
                        2000: 140
                    }
                    tokens = tokens_map.get(amount, 0)
                    
                    if tokens == 0:
                        logger.error(f"❌ Неизвестная сумма оплаты: {amount}")
                        self.send_message(
                            user_id=user_id,
                            message="❌ Ошибка при создании платежа. Попробуйте позже.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        return
                    
                    # Создаем платеж
                    idempotence_key = str(uuid.uuid4())
                    payment = Payment.create({
                        "amount": {
                            "value": str(amount),
                            "currency": "RUB"
                        },
                        "confirmation": {
                            "type": "redirect",
                            "return_url": "https://vk.com/club235442407"
                        },
                        "capture": True,
                        "description": f"Пополнение баланса: {tokens} токенов",
                        "metadata": {
                            "user_id": str(user_id),
                            "tokens": str(tokens),
                            "platform": "vk"
                        }
                    }, idempotence_key)
                    
                    # Получаем ссылку на оплату
                    payment_url = payment.confirmation.confirmation_url
                    
                    # Сохраняем информацию о платеже в БД
                    try:
                        execute_query_sync(
                            """INSERT INTO payments (user_id, payment_id, amount, status, platform)
                               VALUES (%s, %s, %s, 'pending', 'vk')
                               ON CONFLICT (payment_id) DO NOTHING""",
                            (user_id, payment.id, amount)
                        )
                        # Сохраняем tokens в metadata платежа, так как в таблице нет колонки tokens
                        logger.info(f"💾 Платеж сохранен: payment_id={payment.id}, amount={amount}, tokens={tokens}")
                    except Exception as db_err:
                        logger.warning(f"⚠️ Ошибка сохранения платежа в БД: {db_err}")
                    
                    # Отправляем ссылку на оплату
                    from vk_keyboards import get_payment_keyboard
                    payment_keyboard = get_payment_keyboard(payment_url)
                    
                    self.send_message(
                        user_id=user_id,
                        message=f"💳 Оплата {tokens} токенов за {amount}₽\n\n👉 Нажмите кнопку ниже для перехода к оплате:",
                        keyboard=payment_keyboard
                    )
                    
                    logger.info(f"✅ Создан платеж для пользователя {user_id}: {payment.id}")
                    return  # Важно: выходим, чтобы не отправлять "Команда получена"
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при создании платежа: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка при создании платежа. Попробуйте позже или обратитесь в поддержку.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
                    return
            
            # Обработка кнопки "Пригласить друга"
            elif action == "invite_friend":
                logger.info(f"🌟 Запрос реферальной ссылки от пользователя {user_id}")
                
                # Генерируем реферальную ссылку
                referral_link = f"https://vk.com/club235442407?ref={user_id}"
                
                self.send_message(
                    user_id=user_id,
                    message=(
                        f"🌟 **ПРИГЛАСИ ДРУГА И ПОЛУЧИ БОНУС!**\n\n"
                        f"🎁 За каждого друга получишь 2 ТОКЕНА бесплатно!\n\n"
                        f"📎 Твоя реферальная ссылка:\n{referral_link}\n\n"
                        f"💡 Отправь её другу, и как только он создаст первую песню — "
                        f"ты получишь 2 токена в подарок, а он получит 1 токен как новичок!"
                    ),
                    keyboard=self.get_main_keyboard(user_id)
                )
            
            elif action == "create_music":
                print("Обработка кнопки 'Создать музыку'")
                logger.info(f"🎶 Запрос на создание инструментальной музыки от пользователя {user_id}")
                
                # Проверяем баланс пользователя
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Устанавливаем состояние выбора жанра музыки
                        asyncio.get_event_loop().run_until_complete(
                            self.state_manager.set_state(user_id, States.WAITING_MUSIC_STYLE)
                        )
                        # Для обратной совместимости
                        self.user_states[user_id] = UserState.WAITING_INSTRUMENTAL_DESCRIPTION
                        
                        # Импортируем клавиатуру для выбора жанра музыки
                        from vk_keyboards import get_music_genres_keyboard
                        
                        # Создаем клавиатуру с жанрами
                        keyboard = get_music_genres_keyboard()
                        
                        # Сообщение с выбором жанра
                        prompt_message = """🎶 **СОЗДАЕМ ИНСТРУМЕНТАЛЬНУЮ МУЗЫКУ**

🎹 Музыка БЕЗ слов - только мелодия и ритм!

Выбери жанр для твоей композиции 👇"""
                        
                        self.send_message(
                            user_id=user_id,
                            message=prompt_message,
                            keyboard=keyboard
                        )
                        
                        logger.info(f"✅ Пользователь {user_id} переведен в режим выбора жанра инструментальной музыки")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно генераций. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания музыки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания музыки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка кнопки "Минусовка" - показываем выбор версии
            elif action == "karaoke":
                logger.info(f"🎤 Запрос на создание минусовки от пользователя {user_id}")
                
                # Проверяем баланс пользователя
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Показываем выбор версии
                        from vk_keyboards import get_version_selection_keyboard
                        self.send_message(
                            user_id=user_id,
                            message="🎤 **МИНУСОВКА**\n\nВыбери версию для создания минусовки:\n\n🎵 Версия 1 - первый трек\n🎵 Версия 2 - второй трек",
                            keyboard=get_version_selection_keyboard(task_id_from_payload, "karaoke")
                        )
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания минусовки при нулевом балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для создания минусовки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка выбора версии для минусовки
            elif action == "karaoke_v1" or action == "karaoke_v2":
                version = 0 if action == "karaoke_v1" else 1
                logger.info(f"🎤 Запуск минусовки версии {version+1} от пользователя {user_id}")
                
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] > 0:
                        # Списываем баланс СРАЗУ
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id} ДО генерации минусовки")
                        
                        # Отправляем сообщение о начале генерации
                        version_name = "Версия 1" if version == 0 else "Версия 2"
                        self.send_message(
                            user_id=user_id,
                            message=f"🎤 Создаю минусовку ({version_name})!\n\n⏰ Удаление вокала займет 3-5 минут.\n\nВы получите инструментальную версию вашей песни без вокала 🎸",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Создаем новую задачу Celery для минусовки АСИНХРОННО
                        import uuid
                        new_task_id = str(uuid.uuid4())
                        
                        celery_task = generate_karaoke_task.apply_async(
                            args=[user_id, task_id_from_payload, version],
                            kwargs={'task_id': new_task_id},
                            queue='generation'
                        )
                        
                        logger.info(f"✅ Минусовка задача запущена для user {user_id}: {new_task_id}, версия {version+1}")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка при запуске минусовки: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка кнопки "WAV" - показываем выбор версии
            elif action == "wav":
                logger.info(f"🎵 Запрос на конвертацию в WAV от пользователя {user_id}")
                
                # Проверяем баланс пользователя
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 2:  # WAV стоит 2 токена
                        # Показываем выбор версии
                        from vk_keyboards import get_version_selection_keyboard
                        self.send_message(
                            user_id=user_id,
                            message="🎵 **КОНВЕРТАЦИЯ В WAV**\n\nВыбери версию для конвертации в WAV:\n\n🎵 Версия 1 - первый трек\n🎵 Версия 2 - второй трек",
                            keyboard=get_version_selection_keyboard(task_id_from_payload, "wav")
                        )
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для конвертации в WAV нужно 2 токена. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка конвертации в WAV при недостаточном балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для конвертации в WAV: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка выбора версии для WAV
            elif action == "wav_v1" or action == "wav_v2":
                version = 0 if action == "wav_v1" else 1
                logger.info(f"🎵 Запуск WAV конвертации версии {version+1} от пользователя {user_id}")
                
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 2:  # WAV стоит 2 токена
                        # Списываем баланс СРАЗУ
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 2 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списано 2 токена с баланса пользователя {user_id} ДО конвертации WAV")
                        
                        # Отправляем сообщение о начале конвертации
                        version_name = "Версия 1" if version == 0 else "Версия 2"
                        self.send_message(
                            user_id=user_id,
                            message=f"🎵 Конвертирую в WAV формат ({version_name})!\n\n⏰ Конвертация займет 2-3 минуты.\n\nВы получите профессиональный WAV файл с максимальным качеством 🎧",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Создаем новую задачу Celery для WAV АСИНХРОННО
                        import uuid
                        new_task_id = str(uuid.uuid4())
                        
                        celery_task = generate_wav_task.apply_async(
                            args=[user_id, task_id_from_payload, version],
                            kwargs={'task_id': new_task_id},
                            queue='generation'
                        )
                        
                        logger.info(f"✅ WAV конвертация запущена для user {user_id}: {new_task_id}, версия {version+1}")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для конвертации в WAV нужно 2 токена. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка при запуске WAV конвертации: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка кнопки "Кавер" - показываем выбор версии
            elif action == "cover":
                logger.info(f"🎸 Запрос на создание кавера от пользователя {user_id}")
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 1:  # Кавер стоит 1 токен
                        # Показываем выбор версии
                        from vk_keyboards import get_version_selection_keyboard
                        self.send_message(
                            user_id=user_id,
                            message="🎸 **КАВЕР В НОВОМ ЖАНРЕ**\n\nВыбери версию для создания кавера:\n\n🎵 Версия 1 - первый трек\n🎵 Версия 2 - второй трек",
                            keyboard=get_version_selection_keyboard(task_id_from_payload, "cover")
                        )
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для создания кавера нужен 1 токен. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания кавера при недостаточном балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для кавера: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )
            
            # Обработка выбора версии для кавера - показываем выбор жанра
            elif action == "cover_v1" or action == "cover_v2":
                version = 0 if action == "cover_v1" else 1
                logger.info(f"🎸 Пользователь {user_id} выбрал версию {version+1} для кавера")
                
                try:
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    if result and result[0][0] >= 1:  # Кавер стоит 1 токен
                        # ✅ КРИТИЧНО: Списываем баланс СРАЗУ при выборе версии
                        execute_query_sync(
                            "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
                            (user_id,)
                        )
                        logger.info(f"💰 Списан 1 токен с баланса пользователя {user_id} при выборе версии {version+1} для кавера")
                        
                        # Показываем выбор жанра с версией в payload
                        from vk_keyboards import get_cover_genre_keyboard
                        self.send_message(
                            user_id=user_id,
                            message="🎸 **Выбери жанр для кавера:**",
                            keyboard=get_cover_genre_keyboard(task_id_from_payload, version)
                        )
                        logger.info(f"✅ Пользователь {user_id} получил клавиатуру выбора жанра (версия {version+1}, task_id={task_id_from_payload})")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для создания кавера нужен 1 токен. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для кавера: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )

            # Обработка выбора жанра для кавера - запускаем генерацию
            elif action == "cover_genre":
                genre = payload.get('genre', '')
                version = payload.get('version', 0)  # Получаем версию из payload
                cover_task_id = task_id_from_payload
                logger.info(f"🎸 Запуск кавера: user {user_id}, жанр '{genre}', версия {version+1}, task_id={cover_task_id}")

                try:
                    # ✅ ИСПРАВЛЕНО: Баланс уже списан в cover_v1/v2, здесь только проверяем что задача не дублируется
                    # Проверяем что у пользователя достаточно баланса (на случай если он нажал кнопку повторно)
                    result = execute_query_sync(
                        "SELECT balance FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    # Разрешаем запуск даже с балансом 0, т.к. баланс УЖЕ списан при выборе версии
                    if result:  # Просто проверяем что пользователь существует
                        
                        # Отправляем сообщение о начале генерации
                        version_name = "Версия 1" if version == 0 else "Версия 2"
                        self.send_message(
                            user_id=user_id,
                            message=f"🎸 Создаю кавер в жанре «{genre}» ({version_name})!\n\n⏰ Создание кавера займет 3-5 минут.\n\nВы получите ту же песню в новом стиле 🎭",
                            keyboard=self.get_cancel_keyboard()
                        )
                        
                        # Создаем новую задачу Celery для кавера АСИНХРОННО
                        import uuid
                        new_task_id = str(uuid.uuid4())
                        
                        celery_task = generate_cover_task.apply_async(
                            args=[user_id, cover_task_id, genre, version],
                            kwargs={'task_id': new_task_id},
                            queue='generation'
                        )
                        
                        logger.info(f"✅ Кавер задача запущена для user {user_id}: {new_task_id}, жанр '{genre}', версия {version+1}")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ У вас недостаточно токенов. Для создания кавера нужен 1 токен. Пополните баланс!",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.warning(f"⚠️ Попытка создания кавера при недостаточном балансе: {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке баланса для кавера: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )

            # Обработка кнопки "Поделиться"
            elif action == "share":
                logger.info(f"🔗 Запрос на публикацию песни от пользователя {user_id}")
                try:
                    # Получаем данные о треке
                    if task_id_from_payload:
                        song_info = execute_query_sync(
                            "SELECT audio_url, prompt FROM generations WHERE task_id = %s AND user_id = %s LIMIT 1",
                            (task_id_from_payload, user_id)
                        )
                    else:
                        song_info = execute_query_sync(
                            "SELECT audio_url, prompt FROM generations WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                            (user_id,)
                        )

                    if song_info and song_info[0][0]:
                        import urllib.parse
                        audio_url = song_info[0][0]
                        # Если несколько URL — берём первый
                        try:
                            urls = json.loads(audio_url) if audio_url.startswith('[') else [audio_url]
                            share_url = urls[0]
                        except Exception:
                            share_url = audio_url

                        bot_link = "https://vk.com/club235442407"
                        share_text = f"🎵 Послушай мою песню, созданную с помощью ALBI Music!\n\n🤖 Создай свою: {bot_link}"
                        vk_share_link = f"https://vk.com/share.php?url={urllib.parse.quote(share_url, safe='')}&title={urllib.parse.quote(share_text, safe='')}"

                        self.send_message(
                            user_id=user_id,
                            message=(
                                f"🔗 **Поделиться своей песней**\n\n"
                                f"Нажмите на ссылку ниже, чтобы опубликовать трек на своей странице ВКонтакте:\n\n"
                                f"{vk_share_link}\n\n"
                                f"или скопируйте прямую ссылку на трек:\n{share_url}"
                            ),
                            keyboard=self.get_main_keyboard(user_id)
                        )
                        logger.info(f"✅ Ссылка для публикации отправлена пользователю {user_id}")
                    else:
                        self.send_message(
                            user_id=user_id,
                            message="❌ Не найдена информация о песне. Сначала создайте песню.",
                            keyboard=self.get_main_keyboard(user_id)
                        )
                except Exception as e:
                    logger.error(f"❌ Ошибка при создании ссылки для публикации: {e}")
                    self.send_message(
                        user_id=user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        keyboard=self.get_main_keyboard(user_id)
                    )

            # Кнопка "Слушать" теперь openlink (open_link), callback сюда не придёт.
            # Оставляем блок для обратной совместимости (на случай старых клавиатур в истории чата).
            elif action == "listen":
                cdn_url = payload.get('url', '')
                logger.info(f"[listen-legacy] получен старый callback от {user_id}, url={cdn_url[:60] if cdn_url else 'empty'}")
                # Ничего не отправляем в чат — новые кнопки openlink, старый callback игнорируем

            # Отправляем ответ на событие (обязательно для callback-кнопок)
            try:
                self.vk.messages.sendMessageEventAnswer(
                    event_id=event.obj.get('event_id'),
                    user_id=user_id,
                    peer_id=event.obj.get('peer_id'),
                    event_data=json.dumps({"type": "show_snackbar", "text": "✅ Команда обрабатывается"})
                )
            except Exception as callback_error:
                logger.error(f"❌ Ошибка при отправке ответа на callback: {callback_error}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке события от кнопки: {e}")
            logger.error(traceback.format_exc())
            # Пытаемся отправить сообщение об ошибке пользователю
            try:
                self.send_message(
                    user_id=user_id,
                    message="❌ Произошла ошибка при обработке команды. Попробуйте еще раз.",
                    keyboard=self.get_main_keyboard(user_id)
                )
            except Exception as msg_error:
                logger.error(f"❌ Не удалось отправить сообщение об ошибке: {msg_error}")
    
    def run(self):
        """Запуск бота и прослушивание событий"""
        logger.info("🎧 Начинаю прослушивание событий...")
        
        # Увеличиваем таймаут для longpoll
        self.longpoll.wait = 60  # Увеличиваем время ожидания до 60 секунд
        
        # Запускаем прослушивание событий с обработкой ошибок соединения
        while True:
            try:
                # Переинициализируем longpoll при каждой итерации для избежания проблем с соединением
                self.longpoll = VkBotLongPoll(self.vk_session, group_id=VK_GROUP_ID)
                logger.info("✅ Подключение к VK API успешно установлено (BotLongPoll)")
                
                # Запускаем прослушивание событий
                for event in self.longpoll.listen():
                    try:
                        # Обрабатываем новые входящие сообщения
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            # Обрабатываем сообщение
                            self.handle_message(event)
                        # Обрабатываем события от callback-кнопок (Минусовка, WAV, Кавер, Поделиться)
                        elif event.type == VkBotEventType.MESSAGE_EVENT:
                            # Обрабатываем событие от кнопки и отвечаем sendMessageEventAnswer
                            self.handle_callback(event)
                    except Exception as e:
                        logger.error(f"❌ Ошибка при обработке события: {e}")
                        logger.error(traceback.format_exc())
                        # Продолжаем работу после ошибки обработки события
            except requests.exceptions.ReadTimeout:
                logger.warning("⚠️ Таймаут соединения с VK API. Переподключение...")
                time.sleep(5)  # Ждем 5 секунд перед переподключением
                continue
            except requests.exceptions.ConnectionError:
                logger.warning("⚠️ Ошибка соединения с VK API. Переподключение...")
                time.sleep(10)  # Ждем 10 секунд перед переподключением
                continue
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле бота: {e}")
                logger.error(traceback.format_exc())
                logger.info("🔄 Перезапуск основного цикла через 15 секунд...")
                time.sleep(15)  # Ждем 15 секунд перед перезапуском

if __name__ == '__main__':
    # Создаем экземпляр бота с обработкой ошибок
    max_restart_attempts = 3
    restart_count = 0
    
    while restart_count < max_restart_attempts:
        try:
            # Создаем экземпляр бота
            bot = VKBot()
            
            # Запускаем бота
            try:
                logger.info("🚀 Запуск VK бота...")
                logger.info("🎯 Бот ВК успешно запущен и слушает сообщения!")
                bot.run()
            except KeyboardInterrupt:
                logger.info("👋 Бот остановлен пользователем")
                break  # Выходим из цикла перезапуска при ручной остановке
            except Exception as e:
                restart_count += 1
                logger.error(f"❌ Ошибка при запуске бота (попытка {restart_count}/{max_restart_attempts}): {e}")
                logger.error(f"❌ Трассировка ошибки: {traceback.format_exc()}")
                
                if restart_count < max_restart_attempts:
                    wait_time = 15 * restart_count  # Увеличиваем время ожидания с каждой попыткой
                    logger.info(f"🔄 Перезапуск бота через {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    logger.critical("❌ Достигнуто максимальное количество попыток перезапуска")
        except Exception as init_error:
            restart_count += 1
            logger.critical(f"❌ Критическая ошибка при инициализации бота (попытка {restart_count}/{max_restart_attempts}): {init_error}")
            logger.critical(f"❌ Трассировка ошибки: {traceback.format_exc()}")
            
            if restart_count < max_restart_attempts:
                wait_time = 20 * restart_count  # Более длительное ожидание при ошибке инициализации
                logger.info(f"🔄 Повторная попытка через {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                logger.critical("❌ Не удалось запустить бота после нескольких попыток")