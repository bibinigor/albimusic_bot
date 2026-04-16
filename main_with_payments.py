#!/usr/bin/env python3
import re
import time
import logging
import os
import asyncio
import aiohttp
from datetime import datetime
import hashlib
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from threading import Thread

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery, InlineQueryResultArticle, InlineQueryResultAudio, InputTextMessageContent
from aiogram.dispatcher.filters.state import State, StatesGroup

import config
# from database_adapter import db  # Закомментирован - заменен на db_utils
# from redis_cache import init_redis  # Закомментирован - Redis уже инициализирован в Celery
from db_utils import execute_query_sync
from celery_tasks import celery_app, generate_music_task, generate_song_task, generate_suno_lyrics_sync, generate_karaoke_task, generate_cover_task, generate_karaoke_from_upload_task, generate_cover_from_upload_task
import demo_system  # Модуль демо-системы для разблокировки треков

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация пула соединений с БД

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN, proxy='socks5://127.0.0.1:9050')

# Инициализация пула соединений с БД
from db_utils import init_db_pool_sync
init_db_pool_sync()
logging.info("✅ Пул соединений с БД инициализирован")

# Создаём таблицу для сообщений поддержки
try:
    execute_query_sync("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            message TEXT NOT NULL,
            replied BOOLEAN DEFAULT FALSE,
            reply_text TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    logging.info("✅ Таблица support_messages готова")
except Exception as _e:
    logging.error(f"❌ Ошибка создания таблицы support_messages: {_e}")

# Колонки novice_window_started_at и novice_gens_bought добавлены вручную через postgres:
# ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_window_started_at TIMESTAMP DEFAULT NULL;
# ALTER TABLE users ADD COLUMN IF NOT EXISTS novice_gens_bought INT DEFAULT 0;

storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

# ============================================================
# РЕЖИМ ТЕХНИЧЕСКОГО ОБСЛУЖИВАНИЯ
# Установите MAINTENANCE_MODE = False когда сервис восстановлен
# ============================================================
MAINTENANCE_MODE = False
MAINTENANCE_TEXT = (
    "🔧 *Бот находится на техническом обслуживании*\n\n"
    "Мы работаем над улучшением сервиса и скоро вернёмся!\n\n"
    "Приносим извинения за временные неудобства 🙏\n\n"
    "Следите за обновлениями в нашем канале: @ALBImusic_Chart"
)

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

class MaintenanceMiddleware(BaseMiddleware):
    """Перехватывает все обращения к боту в режиме техобслуживания."""

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if MAINTENANCE_MODE and not is_admin(message.from_user.id):
            await message.reply(MAINTENANCE_TEXT, parse_mode="Markdown")
            raise CancelHandler()

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        if MAINTENANCE_MODE and not is_admin(callback_query.from_user.id):
            await callback_query.answer(
                "🔧 Бот на техническом обслуживании. Скоро вернёмся!",
                show_alert=True
            )
            raise CancelHandler()

dp.middleware.setup(MaintenanceMiddleware())

# Регистрация обработчиков демо-системы
demo_system.register_handlers(dp, bot)
logging.info("✅ Обработчики демо-системы зарегистрированы")

# Регистрация обработчиков новых функций (Фото и Видео, Изображения)
from handlers.photo_video_handler import register_photo_video_handlers
from handlers.image_handler import register_image_handlers

register_photo_video_handlers(dp, bot)
register_image_handlers(dp, bot)
logging.info("✅ Обработчики Фото/Видео и Изображений зарегистрированы")

# Демо-треки для приветственного сообщения (file_id получены 22.02.2026)
DEMO_TRACKS = [
    {"file_id": "CQACAgIAAxkDAAIocWmaoqaSOhnK6MavBtmtVwScvTYMAAK9kwACGd7QSAuG117x8v6GOgQ", "title": "🌸 Люба, с 8 марта"},
    {"file_id": "CQACAgIAAxkDAAIocmmaoqf_Y_hXBJ5oDEkj-xM3G8dyAAK-kwACGd7QSGhoOCWNgG2GOgQ", "title": "💪 Бодибилдинг"},
    {"file_id": "CQACAgIAAxkDAAIoc2maoqhyvPWSdddliQ321qa0yPc5AAK_kwACGd7QSBF_BuLDHKS3OgQ", "title": "🐱 Кот"},
    {"file_id": "CQACAgIAAxkDAAI11GmoiE_Y9kzG9AyjvMga09K88ppqAAKknQACFp1JSaQVSpxPx29KOgQ", "title": "🎻 Красивая скрипка"},
    {"file_id": "CQACAgIAAxkDAAI11WmoiFDDYhtgqcqCTQ07l5DdyQkeAAKlnQACFp1JSTfK5ru9v6x1OgQ", "title": "💫 Я буду ждать всегда"},
]

# Инициализация FastAPI
app = FastAPI(title="AlBi-music Bot + Payments")

# Функция для загрузки файла на сервер и получения URL
async def upload_file_to_server(local_path: str, filename: str) -> str:
    """Загружает файл на сервер и возвращает публичный URL"""
    try:
        # Создаем директорию для загрузок если её нет
        upload_dir = "/var/www/albimusic/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Генерируем уникальное имя файла
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        server_path = os.path.join(upload_dir, unique_filename)

        # Копируем файл
        import shutil
        shutil.copy(local_path, server_path)

        # Возвращаем публичный URL (FastAPI на порту 8000)
        public_url = f"http://37.252.23.214:8000/uploads/{unique_filename}"

        logging.info(f"✅ Файл загружен: {public_url}")
        return public_url

    except Exception as e:
        logging.error(f"❌ Ошибка загрузки файла на сервер: {e}")
        raise

# ЮKassa конфигурация
YOOKASSA_SHOP_ID = config.YOOKASSA_SHOP_ID
YOOKASSA_SECRET_KEY = config.YOOKASSA_SECRET_KEY
YOOKASSA_API_URL = 'https://api.yookassa.ru/v3'

# Лимиты
MAX_SONG_LENGTH = 3000
MAX_STYLE_LENGTH = 500

# Состояния FSM
class MusicStates(StatesGroup):
    waiting_for_music_style = State()

class SongStates(StatesGroup):
    waiting_for_song_style = State()
    waiting_for_lyrics = State()
    waiting_for_mode = State()

class ChannelPostStates(StatesGroup):
    waiting_for_version = State()   # Выбор варианта (1 или 2) перед публикацией
    waiting_for_comment = State()

class CoverStates(StatesGroup):
    waiting_for_genre = State()  # Выбор жанра для кавера
    waiting_custom_genre = State()  # Описание своего жанра
    waiting_for_audio_upload = State()  # Ожидание загрузки аудио файла

class KaraokeStates(StatesGroup):
    waiting_for_audio_upload = State()  # Ожидание загрузки аудио файла

# Новый флоу создания песни
class CreateSongStates(StatesGroup):
    choosing_text_type = State()  # Выбор: AI текст или свой
    waiting_song_idea = State()  # Ожидание описания для AI-генерации текста
    choosing_lyrics_variant = State()  # Выбор между вариантом 1 и вариантом 2
    waiting_own_lyrics = State()  # Ожидание своего текста
    reviewing_lyrics = State()  # Просмотр текста: продолжить или перегенерировать
    waiting_genre = State()  # Выбор жанра
    waiting_custom_genre = State()  # Описание своего жанра

class BroadcastStates(StatesGroup):
    waiting_text    = State()
    waiting_confirm = State()

class SupportStates(StatesGroup):
    waiting_message = State()

class SupportReplyStates(StatesGroup):
    waiting_reply = State()

# Инициализация базы данных PostgreSQL - см. функцию init_postgres() в конце файла
# Функции работы с БД
async def add_user(user_id, username, first_name, invited_by=None):
    try:
        from postgres_db import execute_query
        await execute_query(
            'INSERT INTO users (user_id, username, first_name, invited_by, balance) VALUES ($1, $2, $3, $4, 1) ON CONFLICT (user_id) DO NOTHING', 
            user_id, username, first_name, invited_by
        )
    except Exception as e:
        logging.error(f"❌ Ошибка добавления пользователя {user_id}: {e}")

def get_user_balance(user_id):
    if user_id == config.CO_ADMIN_ID:
        return "♾️ неограниченно"
    try:
        from db_utils import execute_query_sync
        result = execute_query_sync('SELECT balance FROM users WHERE user_id = %s', (user_id,))
        if result:
            balance = result[0][0]
            if balance > 0:
                return f"💰 {balance} токенов"
            else:
                return "❌ 0 токенов"
        return "🎁 1 токен в подарок (новый пользователь)"
    except Exception as e:
        logging.error(f"❌ Ошибка получения баланса {user_id}: {e}")
        return "❌ Ошибка получения баланса"


def get_balance_number(user_id):
    """Возвращает числовой баланс пользователя"""
    try:
        from db_utils import execute_query_sync
        result = execute_query_sync('SELECT balance FROM users WHERE user_id = %s', (user_id,))
        if result:
            return result[0][0]
        return 1  # Новый пользователь
    except Exception as e:
        logging.error(f"❌ Ошибка получения числового баланса {user_id}: {e}")
        return 0


def mark_free_generation_used(user_id):
    try:
        from db_utils import execute_query_sync
        # Отмечаем что бесплатная генерация использована
        execute_query_sync('UPDATE users SET free_generation_used = TRUE WHERE user_id = %s', (user_id,))
        # Уменьшаем баланс на 1
        execute_query_sync('UPDATE users SET balance = balance - 1 WHERE user_id = %s', (user_id,))
        logging.info(f"✅ Отмечена бесплатная генерация для пользователя {user_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка отметки бесплатной генерации {user_id}: {e}")

def add_balance(user_id, amount):
    """ИСПРАВЛЕНО: Используем PostgreSQL вместо SQLite"""
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'UPDATE users SET balance = balance + %s WHERE user_id = %s',
            (amount, user_id)
        )
        logging.info(f"✅ Начислено {amount} генераций пользователю {user_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка добавления баланса {user_id}: {e}")

def update_user_balance(user_id, delta):
    """Изменяет баланс пользователя (delta отрицательный для списания)"""
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'UPDATE users SET balance = balance + %s WHERE user_id = %s',
            (delta, user_id)
        )
        logging.info(f"✅ Баланс пользователя {user_id} изменён на {delta}")
    except Exception as e:
        logging.error(f"❌ Ошибка изменения баланса {user_id}: {e}")

def add_generation(user_id, task_id, prompt, audio_url, is_free=False, custom_mode=False):
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'INSERT INTO generations (user_id, task_id, prompt, audio_url, is_free, custom_mode) VALUES (%s, %s, %s, %s, %s, %s)', 
            (user_id, task_id, prompt, audio_url, is_free, custom_mode)
        )
    except Exception as e:
        logging.error(f"❌ Ошибка добавления генерации {user_id}: {e}")

def add_payment(user_id, amount, status, payment_id):
    """ИСПРАВЛЕНО: Используем PostgreSQL вместо SQLite"""
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'INSERT INTO payments (user_id, amount, status, payment_id, platform) VALUES (%s, %s, %s, %s, %s)',
            (user_id, amount, status, payment_id, 'tg')
        )
        logging.info(f"✅ Платеж {payment_id} добавлен для пользователя {user_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка добавления платежа {user_id}: {e}")

def update_payment_status(payment_id, status):
    """ИСПРАВЛЕНО: Используем PostgreSQL вместо SQLite"""
    try:
        from db_utils import execute_query_sync
        execute_query_sync(
            'UPDATE payments SET status = %s WHERE payment_id = %s',
            (status, payment_id)
        )
        logging.info(f"✅ Статус платежа {payment_id} обновлен на {status}")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления платежа {payment_id}: {e}")

def is_admin(user_id):
    return user_id in (config.ADMIN_ID, config.CO_ADMIN_ID)

def get_admin_stats():
    """Получить статистику из PostgreSQL (синхронная версия)"""
    try:
        # Импортируем синхронные функции БД
        from db_utils import execute_query_sync
        
        # 1. Всего пользователей (из таблицы users)
        users_result = execute_query_sync("SELECT COUNT(*) as total FROM users")
        total_users = users_result[0][0] if users_result and users_result[0] else 0

        # 2. Новых сегодня (по дате создания, сутки)
        new_today_result = execute_query_sync(
            "SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE"
        )
        new_today = new_today_result[0][0] if new_today_result and new_today_result[0] else 0

        # 3. Новых за 7 дней
        new_7days_result = execute_query_sync("SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'")
        new_7days = new_7days_result[0][0] if new_7days_result and new_7days_result[0] else 0

        # 4. Новых за 30 дней
        new_30days_result = execute_query_sync("SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'")
        new_30days = new_30days_result[0][0] if new_30days_result and new_30days_result[0] else 0

        # 5. Генераций за последние 24 часа (по времени создания)
        generations_24h_result = execute_query_sync(
            "SELECT COUNT(*) as total FROM generations WHERE created_at >= NOW() - INTERVAL '24 hours'"
        )
        generations_24h = generations_24h_result[0][0] if generations_24h_result and generations_24h_result[0] else 0

        # 6. Всего генераций (для общей картины)
        generations_result = execute_query_sync("SELECT COUNT(*) as total FROM generations")
        total_generations = generations_result[0][0] if generations_result and generations_result[0] else 0

        # 7. Успешных генераций (completed)
        completed_result = execute_query_sync("SELECT COUNT(*) as total FROM generations WHERE status = 'completed'")
        completed_generations = completed_result[0][0] if completed_result and completed_result[0] else 0

        # 8. Процент успешных
        success_rate = round((completed_generations * 100.0) / total_generations, 1) if total_generations > 0 else 0

        # 9. Оплаченных генераций - ПРАВИЛЬНЫЙ ПОДСЧЕТ через таблицу payments
        # Получаем пользователей с успешными платежами
        paid_users_result = execute_query_sync("""
            SELECT DISTINCT user_id 
            FROM payments 
            WHERE status = 'succeeded'
        """)
        
        if paid_users_result:
            paid_user_ids = [str(row[0]) for row in paid_users_result]
            paid_users_str = ','.join(paid_user_ids)
            
            # Генерации от пользователей с успешными платежами
            paid_7days_result = execute_query_sync(f"""
                SELECT COUNT(*) as total 
                FROM generations 
                WHERE user_id IN ({paid_users_str})
                AND status = 'completed'
                AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            paid_24h_result = execute_query_sync(f"""
                SELECT COUNT(*) as total 
                FROM generations 
                WHERE user_id IN ({paid_users_str})
                AND status = 'completed'
                AND created_at >= NOW() - INTERVAL '24 hours'
            """)
            
            paid_total_result = execute_query_sync(f"""
                SELECT COUNT(*) as total 
                FROM generations 
                WHERE user_id IN ({paid_users_str})
                AND status = 'completed'
            """)
        else:
            paid_7days_result = [[0]]
            paid_24h_result = [[0]]
            paid_total_result = [[0]]
        
        paid_7days = paid_7days_result[0][0] if paid_7days_result and paid_7days_result[0] else 0
        paid_24h = paid_24h_result[0][0] if paid_24h_result and paid_24h_result[0] else 0
        paid_total = paid_total_result[0][0] if paid_total_result and paid_total_result[0] else 0

        # 10. Приглашенных сегодня (по таблице users)
        invited_today_result = execute_query_sync("SELECT COUNT(*) as total FROM users WHERE created_at >= CURRENT_DATE AND invited_by IS NOT NULL")
        invited_today = invited_today_result[0][0] if invited_today_result and invited_today_result[0] else 0

        # 11. Воронка: новые пользователи за 24 часа и те, кто дошёл до меню
        started_24h_result = execute_query_sync("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours'")
        started_24h = started_24h_result[0][0] if started_24h_result and started_24h_result[0] else 0

        menu_24h_result = execute_query_sync("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours' AND first_menu_action_at IS NOT NULL")
        menu_24h = menu_24h_result[0][0] if menu_24h_result and menu_24h_result[0] else 0

        # 12. Суммы платежей
        sum_24h_result = execute_query_sync("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'")
        sum_24h = int(sum_24h_result[0][0]) if sum_24h_result and sum_24h_result[0] else 0

        sum_7days_result = execute_query_sync("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded' AND created_at >= CURRENT_DATE - INTERVAL '7 days'")
        sum_7days = int(sum_7days_result[0][0]) if sum_7days_result and sum_7days_result[0] else 0

        sum_total_result = execute_query_sync("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded'")
        sum_total = int(sum_total_result[0][0]) if sum_total_result and sum_total_result[0] else 0

        # 13. Количество платежей (отдельно от генераций — по таблице payments)
        count_24h_result = execute_query_sync("SELECT COUNT(*) FROM payments WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'")
        count_24h = count_24h_result[0][0] if count_24h_result and count_24h_result[0] else 0

        count_7days_result = execute_query_sync("SELECT COUNT(*) FROM payments WHERE status = 'succeeded' AND created_at >= CURRENT_DATE - INTERVAL '7 days'")
        count_7days = count_7days_result[0][0] if count_7days_result and count_7days_result[0] else 0

        count_total_result = execute_query_sync("SELECT COUNT(*) FROM payments WHERE status = 'succeeded'")
        count_total = count_total_result[0][0] if count_total_result and count_total_result[0] else 0

        # 14. Разбивка оплат за 24 часа по тарифам (amount)
        tariffs_24h_rows = execute_query_sync("""
            SELECT amount, COUNT(*)
            FROM payments
            WHERE status = 'succeeded' AND created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY amount
            ORDER BY amount
        """)
        tariffs_24h = {row[0]: row[1] for row in tariffs_24h_rows} if tariffs_24h_rows else {}

        # 15. Разбивка платежей по платформам (VK / TG) — всего
        platform_total_rows = execute_query_sync("""
            SELECT COALESCE(platform, 'tg') as plat, COUNT(*), COALESCE(SUM(amount), 0)
            FROM payments
            WHERE status = 'succeeded'
            GROUP BY plat
            ORDER BY plat
        """)
        platform_total = {row[0]: (row[1], int(row[2])) for row in platform_total_rows} if platform_total_rows else {}

        # 16. Разбивка платежей по платформам (VK / TG) — за 7 дней
        platform_7d_rows = execute_query_sync("""
            SELECT COALESCE(platform, 'tg') as plat, COUNT(*), COALESCE(SUM(amount), 0)
            FROM payments
            WHERE status = 'succeeded' AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY plat
            ORDER BY plat
        """)
        platform_7d = {row[0]: (row[1], int(row[2])) for row in platform_7d_rows} if platform_7d_rows else {}

        return {
            'total_users': total_users,
            'new_today': new_today,
            'new_7days': new_7days,
            'new_30days': new_30days,
            'generations_24h': generations_24h,
            'total_generations': total_generations,
            'completed_generations': completed_generations,
            'success_rate': success_rate,
            'paid_7days': paid_7days,
            'paid_24h': paid_24h,
            'paid_total': paid_total,
            'invited_today': invited_today,
            'started_24h': started_24h,
            'menu_24h': menu_24h,
            'sum_24h': sum_24h,
            'sum_7days': sum_7days,
            'sum_total': sum_total,
            'count_24h': count_24h,
            'count_7days': count_7days,
            'count_total': count_total,
            'tariffs_24h': tariffs_24h,
            'platform_total': platform_total,
            'platform_7d': platform_7d,
        }
    except Exception as e:
        logging.error(f"❌ Ошибка получения статистики: {e}")
        return {
            'total_users': 0,
            'new_today': 0,
            'new_7days': 0,
            'new_30days': 0,
            'total_generations': 0,
            'completed_generations': 0,
            'success_rate': 0,
            'paid_7days': 0,
            'paid_24h': 0,
            'paid_total': 0,
            'invited_today': 0,
            'started_24h': 0,
            'menu_24h': 0,
            'sum_24h': 0,
            'sum_7days': 0,
            'sum_total': 0,
            'count_24h': 0,
            'count_7days': 0,
            'count_total': 0,
            'platform_total': {},
            'platform_7d': {},
        }
def track_first_menu_action(user_id):
    """Фиксирует первое нажатие кнопки главного меню (записывается только один раз)"""
    try:
        execute_query_sync(
            "UPDATE users SET first_menu_action_at = NOW() WHERE user_id = %s AND first_menu_action_at IS NULL",
            (user_id,)
        )
    except Exception as e:
        logging.error(f"❌ Ошибка track_first_menu_action: {e}")


def get_novice_status(user_id):
    """Возвращает (is_active, hours_left, gens_bought) для 24-часового окна новичка.

    is_active: True если окно активно (novice_window_started_at установлен и < 24ч прошло)
    hours_left: сколько часов осталось (float)
    gens_bought: сколько новичковых генераций уже куплено
    """
    try:
        result = execute_query_sync(
            "SELECT novice_window_started_at, novice_gens_bought FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not result or not result[0] or result[0][0] is None:
            return False, 0.0, 0
        from datetime import datetime, timezone, timedelta
        window_started = result[0][0]
        gens_bought = result[0][1] or 0
        # Убеждаемся что timezone-aware
        if window_started.tzinfo is None:
            window_started = window_started.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        window_end = window_started + timedelta(hours=24)
        if now < window_end:
            hours_left = (window_end - now).total_seconds() / 3600
            return True, round(hours_left, 1), gens_bought
        return False, 0.0, gens_bought
    except Exception as e:
        logging.error(f"❌ get_novice_status error for {user_id}: {e}")
        return False, 0.0, 0


async def create_yookassa_payment(user_id, amount, description, extra_metadata=None):
    headers = {
        'Idempotence-Key': str(uuid.uuid4()),
        'Content-Type': 'application/json'
    }
    metadata = {"user_id": user_id}
    if extra_metadata:
        metadata.update(extra_metadata)
    data = {
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": "https://albi-music.ru/payment/success"
        },
        "description": description,
        "metadata": metadata
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{YOOKASSA_API_URL}/payments',
                json=data,
                headers=headers,
                auth=aiohttp.BasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
            ) as response:
                result = await response.json()
                logging.info(f"ЮKassa payment response: {result}")
                return result
    except Exception as e:
        logging.error(f"❌ ЮKassa API error: {e}")
        return None
async def generate_suno_music(prompt, is_song=False, custom_mode=False, user_id=None):
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {config.SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        if is_song:
            if custom_mode:
                data = {
                    "prompt": prompt,
                    "customMode": True,
                    "instrumental": False,
                    "model": "V5",
                    "callBackUrl": "https://example.com/callback"
                }
            else:
                data = {
                    "prompt": prompt,
                    "customMode": False,
                    "instrumental": False,
                    "model": "V5",
                    "callBackUrl": "https://example.com/callback"
                }
        else:
            data = {
                "prompt": prompt,
                "customMode": False,
                "instrumental": True,
                "model": "V5",
                "callBackUrl": "https://example.com/callback"
            }
        try:
            async with session.post(f"{config.SUNO_API_URL}/api/v1/generate", json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result['data']['taskId']
                    logging.info(f"🎵 Задача создана: {task_id} для пользователя {user_id}")
                    for i in range(30):
                        await asyncio.sleep(10)
                        async with session.get(f"{config.SUNO_API_URL}/api/v1/generate/record-info?taskId={task_id}", headers=headers) as status_response:
                            if status_response.status == 200:
                                status_result = await status_response.json()
                                status = status_result.get('data', {}).get('status')
                                logging.info(f"📊 Статус задачи {task_id}: {status} (попытка {i+1})")
                                if status == 'SUCCESS':
                                    audio_data = status_result.get('data', {}).get('response', {}).get('sunoData', [])
                                    if audio_data:
                                        audio_url = audio_data[0].get('audioUrl')
                                        logging.info(f"✅ Генерация завершена для пользователя {user_id}")
                                        return audio_url
                                elif status in ['PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS']:
                                    continue
                                else:
                                    logging.error(f"❌ Ошибка генерации: {status} для пользователя {user_id}")
                                    return None
                    logging.error(f"⏰ Время ожидания истекло для пользователя {user_id}")
                    return None
                else:
                    error_text = await response.text()
                    logging.error(f"❌ Ошибка API: {error_text} для пользователя {user_id}")
                    return None
        except Exception as e:
            logging.error(f"❌ Ошибка генерации для пользователя {user_id}: {e}")
            return None

# Фоновая обработка генерации
async def process_generation_background(user_id, style, lyrics, is_song, is_free, custom_mode, processing_msg_id, chat_id):
    try:

        # === ГЕНЕРИРУЕМ task_id ЗАРАНЕЕ ДЛЯ ГАРАНТИИ ===

        import uuid

        celery_task_id = str(uuid.uuid4())

        

        logging.info(f"🆔 Создан task_id для Celery: {celery_task_id}")

        

        # Отправляем задачу в Celery с явным task_id

        if is_song:

            task = generate_song_task.apply_async(

                args=(user_id, lyrics, style, custom_mode),

                kwargs={'task_id': celery_task_id},

                task_id=celery_task_id  # ✅ Передаем ID самой задаче Celery

            )

        else:

            task = generate_music_task.apply_async(

                args=(user_id, style),

                kwargs={'task_id': celery_task_id},

                task_id=celery_task_id  # ✅ Передаем ID самой задаче Celery

            )

        

        logging.info(f"✅ Celery задача отправлена: {task.id}")
        
        logging.info(f"🚀 Задача отправлена в Celery: {task.id} для пользователя {user_id}")
        
        # Сохраняем task_id в БД
        add_generation(user_id, task.id, f"Стиль: {style}" + (f". Текст: {lyrics}" if is_song else ""), "", is_free, custom_mode)
        
        # Отправляем GIF-анимацию о начале генерации
        gif_path = '/root/albimusic-bot/robot_music.gif'
        try:
            with open(gif_path, 'rb') as gif:
                await bot.send_animation(
                    chat_id,
                    gif,
                    caption="🎵 **Генерация началась!**\n\n🤖 Робот сочиняет вашу композицию...\n⏰ Подождите 3-5 минут.",
                    parse_mode="Markdown"
                )
        except FileNotFoundError:
            # Если GIF не найдена, отправляем текстовое сообщение
            await bot.send_message(chat_id, "⏳ **Генерация вашей композиции началась!**\n\n⏰ Подождите пожалуйста 3-5 минут. Результат я пришлю вам сюда в чат!", parse_mode="Markdown")
        
        try:
            await bot.delete_message(chat_id, processing_msg_id)
        except:
            pass
            
    except Exception as e:
        logging.error(f"❌ Ошибка отправки задачи в Celery: {e}")
        try:
            await bot.delete_message(chat_id, processing_msg_id)
        except:
            pass
        await bot.send_message(chat_id, "❌ Произошла ошибка при постановке задачи в очередь. Попробуйте позже.")

# ===================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===================================================================

async def send_zero_balance_message(user_id, state=None):
    """Отправляет сообщение о нулевом балансе с кнопкой подписки на канал"""
    if state:
        await state.finish()
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✅ Я подписался! Давай песню", callback_data="check_subscription"),
        InlineKeyboardButton("💳 Не хочу подписываться, хочу купить пакет", callback_data="go_to_balance")
    )
    await bot.send_message(
        user_id,
        "🛑 Ой, бесплатные генерации закончились!\n\n"
        "Хочешь прямо сейчас получить еще 1 песню АБСОЛЮТНО БЕСПЛАТНО?\n\n"
        "1️⃣ Подпишись на наш официальный канал:\n"
        "<a href='https://t.me/ALBImusic_Chart'>@ALBImusic_Chart</a>\n"
        "Там мы публикуем самые смешные треки и раздаём промокоды!\n\n"
        "2️⃣ Возвращайся сюда и жми кнопку «Я подписался».\n\n"
        "3️⃣ Бот автоматически начислит тебе генерацию!",
        reply_markup=markup,
        parse_mode="HTML"
    )

async def send_no_tokens_message(user_id, context_text="У вас недостаточно токенов", state=None):
    """Отправляет сообщение о нехватке токенов.

    Новичкам (newcomer_offer_shown=False) показывает разовый оффер 5 токенов за 99₽.
    Всем остальным — стандартное сообщение с клавиатурой пополнения.
    Флаг newcomer_offer_shown ставится ДО отправки (защита от повторного показа).
    """
    if state:
        await state.finish()
    try:
        result = execute_query_sync(
            "SELECT newcomer_offer_shown FROM users WHERE user_id = %s", (user_id,)
        )
        offer_shown = result[0][0] if result and result[0] else True
    except Exception as _e:
        logger.warning(f"⚠️ newcomer_offer check error for {user_id}: {_e}")
        offer_shown = True

    # Проверяем новичковое 24-часовое окно (приоритетнее newcomer_offer)
    is_novice_active_no, hours_left_no, gens_bought_no = get_novice_status(user_id)
    if is_novice_active_no and gens_bought_no < 10:
        remaining_no = 10 - gens_bought_no
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(
            f"🎁 Создать ещё песню — 29₽ (⏰ {int(hours_left_no)}ч, осталось {remaining_no} из 10)",
            callback_data="pay_29_novice"
        ))
        markup.add(InlineKeyboardButton("💳 Все тарифы", callback_data="go_to_balance"))
        await bot.send_message(
            user_id,
            f"❌ *{context_text}*\n\n"
            f"🎁 *У тебя активно специальное окно новичка!*\n\n"
            f"⏰ Ещё *{int(hours_left_no)} ч* действует цена *29₽ за 1 генерацию* (осталось {remaining_no} из 10).\n\n"
            f"👇 Нажми кнопку ниже:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    if not offer_shown:
        # Ставим флаг ДО отправки — защита от повторного показа при ошибке
        try:
            execute_query_sync(
                "UPDATE users SET newcomer_offer_shown = TRUE WHERE user_id = %s", (user_id,)
            )
        except Exception as _e:
            logger.warning(f"⚠️ newcomer_offer update error for {user_id}: {_e}")
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🎁 5 токенов за 99₽ — ЗАБРАТЬ ОФФЕР", callback_data="newcomer_offer_pay"))
        markup.add(InlineKeyboardButton("💳 Все тарифы", callback_data="go_to_balance"))
        await bot.send_message(
            user_id,
            "❌ *Токены закончились!*\n\n"
            "🎁 *РАЗОВОЕ ПРЕДЛОЖЕНИЕ ДЛЯ НОВИЧКОВ*\n\n"
            "Получи *5 токенов за 99₽* прямо сейчас!\n\n"
            "⚡ Это предложение показывается *ТОЛЬКО ОДИН РАЗ* и больше *НИКОГДА* не появится.\n\n"
            "👇 Нажми кнопку, чтобы воспользоваться оффером:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        await bot.send_message(
            user_id,
            f"❌ {context_text}",
            reply_markup=get_balance_keyboard(user_id)
        )

async def check_channel_subscription(user_id: int) -> bool:
    """Проверяет подписку пользователя на официальный канал через Telegram API"""
    try:
        member = await bot.get_chat_member(chat_id="@ALBImusic_Chart", user_id=user_id)
        return member.status in ('member', 'administrator', 'creator', 'restricted')
    except Exception as e:
        logging.warning(f"⚠️ Ошибка проверки подписки для {user_id}: {e}")
        return False

# ===================================================================
# КЛАВИАТУРЫ
# ===================================================================

# Клавиатуры
def get_main_menu_keyboard(user_id=None):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🎵 Создать песню"), KeyboardButton("🎶 Создать музыку"))
    markup.add(KeyboardButton("📂 Мои треки"), KeyboardButton("💰 Баланс"))
    markup.add(KeyboardButton("❤️ Примеры песен"), KeyboardButton("📞 Поддержка"))
    if user_id and user_id == config.ADMIN_ID:
        markup.add(KeyboardButton("👨‍💻 Админ панель"))
    return markup

def get_song_type_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎤 Песня с текстом", callback_data="create_song"),
        InlineKeyboardButton("🎵 Инструментальная музыка", callback_data="create_music")
    )
    return markup

def get_generation_mode_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎯 Точный режим (только мой текст)", callback_data="mode_exact"),
        InlineKeyboardButton("🎨 Творческий режим (ИИ может дополнять)", callback_data="mode_creative")
    )
    return markup

def get_balance_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    # Проверяем 24-часовое окно новичка
    is_novice_active, hours_left, gens_bought = get_novice_status(user_id)
    if is_novice_active and gens_bought < 10:
        remaining = 10 - gens_bought
        markup.add(
            InlineKeyboardButton(
                f"🎁 НОВИЧОК: ещё песня — 29₽ ⏰ ({int(hours_left)}ч, осталось {remaining} из 10)",
                callback_data="pay_29_novice"
            )
        )
    markup.add(
        # 🔥 СТАРТОВЫЙ ПАКЕТ — первым, чтобы бросался в глаза
        InlineKeyboardButton("🎁 5 генераций (10 треков) — 99₽ (СТАРТ)", callback_data="pay_99"),
        InlineKeyboardButton("📄 Документы", callback_data="show_documents"),
        InlineKeyboardButton("🌟 Пригласить друга (2 токена в подарок)", callback_data="invite_friend"),
        InlineKeyboardButton("💳 10 генераций (20 треков) — 490₽", callback_data="pay_500"),
        InlineKeyboardButton("🔥 25 генераций (50 треков) — 990₽ (ХИТ!)", callback_data="pay_1000"),
        InlineKeyboardButton("⭐ 60 генераций (120 треков) — 1990₽", callback_data="pay_2000"),
        InlineKeyboardButton("💎 140 генераций (280 треков) — 3990₽", callback_data="pay_4000")
    )
    return markup

def get_admin_keyboard():
    """Клавиатура админ-панели"""
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        result = execute_query_sync("SELECT COUNT(*) FROM support_messages WHERE replied = FALSE")
        unread_count = result[0][0] if result else 0
    except Exception:
        unread_count = 0
    support_label = f"📩 Поддержка ({unread_count} новых)" if unread_count > 0 else "📩 Поддержка"
    markup.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🔍 Проверить Suno API", callback_data="check_suno_api"),
        InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton(support_label, callback_data="admin_support"),
    )
    return markup

# ... (продолжение следует)

# FastAPI роуты
@app.get("/")
async def root():
    return {"message": "AlBi-music Bot + Payments is running"}

@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Раздача загруженных аудио файлов"""
    file_path = f"/var/www/albimusic/uploads/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/payment/success")
async def payment_success():
    html_content = """
    <!DOCTYPE html><html><head><title>Оплата успешна</title><meta charset="UTF-8">
    <style>body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
    .success { color: green; font-size: 24px; }</style></head>
    <body><div class="success">✅ Оплата прошла успешно!</div>
    <p>Вернитесь в бота @AlBimusic_bot - токены уже начислены</p></body></html>
    """
    return HTMLResponse(html_content)

@app.get("/payment/failed")
async def payment_failed():
    html_content = """
    <!DOCTYPE html><html><head><title>Оплата не прошла</title><meta charset="UTF-8">
    <style>body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
    .error { color: red; font-size: 24px; }</style></head>
    <body><div class="error">❌ Оплата не прошла</div>
    <p>Попробуйте снова или обратитесь в поддержку</p></body></html>
    """
    return HTMLResponse(html_content)

@app.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    try:
        notification = await request.json()
        logging.info(f"Webhook от ЮKassa: {notification}")
        if notification.get('event') == 'payment.succeeded':
            payment = notification.get('object', {})
            payment_id = payment.get('id')

            # Обработка обычных платежей за генерации
            user_id = payment.get('metadata', {}).get('user_id')
            payment_type_meta = payment.get('metadata', {}).get('payment_type', '')
            task_id_unlock = payment.get('metadata', {}).get('task_id', '')

            # ============================================================
            # Специальная обработка: разблокировка первой генерации за 50₽
            # ============================================================
            if payment_type_meta == 'unlock_first' and task_id_unlock and user_id:
                platform_meta = payment.get('metadata', {}).get('platform', 'telegram')
                _unlock_amount = float(payment.get('amount', {}).get('value', 50.0))
                logging.info(f"🔓 Оплата разблокировки первой генерации: user={user_id}, task={task_id_unlock}, platform={platform_meta}, amount={_unlock_amount}₽")
                add_payment(user_id, _unlock_amount, 'succeeded', payment_id)

                # Разблокируем трек в БД
                execute_query_sync(
                    "UPDATE demo_tracks SET is_unlocked = TRUE, unlocked_at = NOW() WHERE task_id = %s",
                    (task_id_unlock,)
                )

                # Получаем URL полных треков
                demo_data = execute_query_sync(
                    "SELECT full_url_1, full_url_2 FROM demo_tracks WHERE task_id = %s",
                    (task_id_unlock,)
                )

                if platform_meta == 'vk':
                    # ── VK нотификация (синхронная) ──────────────────────────────
                    def _notify_vk_unlock(uid=user_id, tid=task_id_unlock, dd=demo_data):
                        try:
                            from celery_tasks import send_vk_result
                            if dd and dd[0]:
                                full_url_1, full_url_2 = dd[0]
                                urls = [u for u in [full_url_1, full_url_2] if u]
                                for idx, url in enumerate(urls, 1):
                                    send_vk_result(
                                        int(uid),
                                        f"🎉 Оплата прошла! Полная версия {idx}:",
                                        url
                                    )
                            # Текст с опциями
                            from celery_tasks import send_vk_result as _svr
                            _svr(int(uid),
                                "✅ Полная версия разблокирована!\n\n"
                                "💎 Что можно сделать с этой песней:\n\n"
                                "🎤 Минусовка — версия без вокала\n"
                                "🎸 Кавер — перепой в другом жанре\n"
                                "🎵 В WAV — профессиональный формат\n\n"
                                "🚀 Хочешь создать ещё? Напиши «Создать песню»!"
                            )
                        except Exception as e:
                            logging.error(f"❌ Ошибка VK unlock нотификации: {e}")

                    import threading as _threading
                    _threading.Thread(target=_notify_vk_unlock, daemon=True).start()

                else:
                    # ── TG нотификация (асинхронная) ─────────────────────────────
                    async def _send_unlocked_first_gen(uid=user_id, tid=task_id_unlock, dd=demo_data):
                        try:
                            await bot.send_message(
                                int(uid),
                                "🎉 *Оплата прошла! Отправляю полные версии...*",
                                parse_mode="Markdown"
                            )

                            # ── Получаем URL треков (из demo_data или fallback из generations) ──
                            urls_to_send = []
                            if dd and dd[0]:
                                full_url_1, full_url_2 = dd[0]
                                urls_to_send = [u for u in [full_url_1, full_url_2] if u]
                            if not urls_to_send:
                                # Fallback: ищем URL в таблице generations
                                logging.warning(f"⚠️ demo_data пуст для task={tid}, ищем в generations")
                                gen_fallback = execute_query_sync(
                                    "SELECT audio_url FROM generations WHERE task_id = %s",
                                    (tid,)
                                )
                                if gen_fallback and gen_fallback[0][0]:
                                    raw_url = gen_fallback[0][0]
                                    if raw_url.startswith('ALREADY_SENT_'):
                                        raw_url = raw_url[len('ALREADY_SENT_'):]
                                    if raw_url and not raw_url.startswith('ERROR'):
                                        urls_to_send = [raw_url]

                            sent_count = 0
                            for idx, url in enumerate(urls_to_send, 1):
                                try:
                                    await bot.send_audio(
                                        chat_id=int(uid),
                                        audio=url,
                                        caption=f"🎼 *Версия {idx}* — полная версия",
                                        title=f"AI Music - Full Version {idx}",
                                        performer="ALBI Music",
                                        parse_mode="Markdown"
                                    )
                                    sent_count += 1
                                    logging.info(f"✅ Полная версия {idx} отправлена user={uid} (unlock_first)")
                                except Exception as e:
                                    logging.error(f"❌ send_audio версия {idx} не удалась (unlock_first user={uid}): {e} — пробуем URL текстом")
                                    # Fallback: отправить URL текстом
                                    try:
                                        await bot.send_message(
                                            chat_id=int(uid),
                                            text=f"🎼 *Версия {idx}* — полная версия:\n{url}",
                                            parse_mode="Markdown"
                                        )
                                        sent_count += 1
                                        logging.info(f"✅ Полная версия {idx} отправлена текстом user={uid}")
                                    except Exception as e2:
                                        logging.error(f"❌ Даже URL текстом не удался (версия {idx}, user={uid}): {e2}")

                            # Если вообще ничего не отправилось — уведомляем админа
                            if sent_count == 0 and urls_to_send:
                                logging.error(f"🔴 КРИТИЧНО: unlock_first — ни один трек не доставлен! user={uid}, task={tid}, urls={urls_to_send}")
                                try:
                                    await bot.send_message(
                                        ADMIN_ID,
                                        f"🔴 *UNLOCK FAIL* — пользователь оплатил, треки не доставлены!\n"
                                        f"user_id: `{uid}`\ntask_id: `{tid}`\n"
                                        f"URLs: {urls_to_send}\n"
                                        f"⚠️ Требуется ручная отправка!",
                                        parse_mode="Markdown"
                                    )
                                except Exception:
                                    pass
                                await bot.send_message(
                                    int(uid),
                                    "⚠️ Произошла техническая ошибка при отправке треков.\n"
                                    "Деньги зачислены, треки будут отправлены вручную в течение нескольких часов.\n"
                                    "Приносим извинения за неудобства!",
                                )
                            elif not urls_to_send:
                                logging.error(f"🔴 КРИТИЧНО: unlock_first — нет URL треков! user={uid}, task={tid}, dd={dd}")
                                try:
                                    await bot.send_message(
                                        ADMIN_ID,
                                        f"🔴 *UNLOCK FAIL (no URLs)* — пользователь оплатил, URL треков не найдены!\n"
                                        f"user_id: `{uid}`\ntask_id: `{tid}`\n"
                                        f"⚠️ Требуется ручная отправка!",
                                        parse_mode="Markdown"
                                    )
                                except Exception:
                                    pass

                            # Кнопки — всё как при обычной оплаченной генерации
                            full_keyboard = InlineKeyboardMarkup(row_width=2)
                            full_keyboard.add(
                                InlineKeyboardButton("🎧 Послушать", callback_data=f"play_{tid}"),
                            )
                            full_keyboard.add(
                                InlineKeyboardButton("🎤 Минусовка (1 токен)", callback_data=f"karaoke_{tid}"),
                                InlineKeyboardButton("🎸 Кавер (2 токена)", callback_data=f"cover_{tid}")
                            )
                            full_keyboard.add(
                                InlineKeyboardButton("🎵 В WAV (1 токен)", callback_data=f"wav_{tid}"),
                                InlineKeyboardButton("📢 Отправить в канал", callback_data=f"post_{tid}")
                            )
                            full_keyboard.add(
                                InlineKeyboardButton("🔗 Поделиться с другом", switch_inline_query=tid),
                                InlineKeyboardButton("🔔 Перейти в канал", url="https://t.me/ALBImusic_Chart")
                            )
                            await bot.send_message(
                                int(uid),
                                "✅ *Полные версии разблокированы!*\n\n"
                                "💎 *Что можно сделать с этой песней:*\n\n"
                                "🎧 **Послушать** — полная версия без ограничений\n"
                                "🎤 **Минусовка** — версия без вокала для исполнения\n"
                                "🎸 **Кавер** — перепой в другом стиле/жанре\n"
                                "🎵 **В WAV** — конвертируй в WAV формат для профи\n"
                                "📢 **Отправить в канал** — опубликуй в официальном канале\n"
                                "🔗 **Поделиться** — отправь другу прямо сейчас\n\n"
                                "🚀 Хочешь создать ещё? Нажми «Создать песню» в меню!",
                                reply_markup=full_keyboard,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logging.error(f"❌ Ошибка отправки разблокированных треков TG unlock_first (user={uid}, task={tid}): {e}", exc_info=True)
                            # Аварийное уведомление пользователю
                            try:
                                await bot.send_message(
                                    int(uid),
                                    "⚠️ Произошла техническая ошибка при отправке треков.\n"
                                    "Деньги зачислены, треки будут отправлены вручную в течение нескольких часов.\n"
                                    "Приносим извинения за неудобства!"
                                )
                                await bot.send_message(
                                    ADMIN_ID,
                                    f"🔴 *UNLOCK FAIL (exception)* user={uid}, task={tid}\n"
                                    f"Ошибка: {e}\n⚠️ Требуется ручная отправка!",
                                    parse_mode="Markdown"
                                )
                            except Exception:
                                pass

                    # Оборачиваем task чтобы необработанные исключения не поглощались молча
                    def _on_unlock_task_done(fut):
                        if fut.exception():
                            logging.error(f"🔴 asyncio task _send_unlocked_first_gen завершилась с исключением: {fut.exception()}", exc_info=fut.exception())

                    _unlock_task = asyncio.create_task(_send_unlocked_first_gen())
                    _unlock_task.add_done_callback(_on_unlock_task_done)

                return JSONResponse({"status": "ok"})

            amount = float(payment.get('amount', {}).get('value', 0))
            if user_id and amount:
                # ============================================================
                # Специальная обработка: платёж novice_gen (29₽ за 1 токен)
                # ============================================================
                payment_type_novice = payment.get('metadata', {}).get('payment_type', '')
                if payment_type_novice == 'novice_gen' and user_id:
                    _nov_amount = float(payment.get('amount', {}).get('value', 29.0))
                    add_balance(user_id, 1)
                    add_payment(user_id, _nov_amount, 'succeeded', payment.get('id'))
                    # Инкрементируем счётчик новичковых генераций
                    execute_query_sync(
                        "UPDATE users SET novice_gens_bought = COALESCE(novice_gens_bought, 0) + 1 WHERE user_id = %s",
                        (user_id,)
                    )
                    logging.info(f"✅ novice_gen: +1 токен пользователю {user_id}, сумма={_nov_amount}₽")
                    # Уведомляем
                    async def _notify_novice_gen(uid=user_id):
                        try:
                            inline_kb = InlineKeyboardMarkup(row_width=2)
                            inline_kb.add(
                                InlineKeyboardButton("🎵 Создать песню", callback_data="create_song_inline"),
                                InlineKeyboardButton("🎶 Создать музыку", callback_data="create_music_inline")
                            )
                            await bot.send_message(
                                int(uid),
                                "🎁 *Оплата прошла! +1 генерация (2 трека)*\n\n"
                                "✅ Начислен 1 токен — создавай свою следующую песню!\n\n"
                                "Нажми кнопку ниже чтобы начать 👇",
                                reply_markup=inline_kb,
                                parse_mode="Markdown"
                            )
                        except Exception as _ne:
                            logging.error(f"❌ Ошибка уведомления novice_gen {uid}: {_ne}")
                    asyncio.create_task(_notify_novice_gen())
                    return JSONResponse({"status": "ok"})

                # Определяем количество токенов по сумме
                amount_to_tokens = {
                    99.00: 5,
                    250.00: 10,
                    490.00: 10,
                    500.00: 25,
                    990.00: 25,
                    1000.00: 60,
                    1990.00: 60,
                    2000.00: 140,
                    3990.00: 140,
                    4000.00: 140,
                    # Совместимость со старыми ценами
                    29.00: 1,   # новичковая разблокировка
                    50.00: 1,
                    100.00: 1,
                }

                tokens = amount_to_tokens.get(amount, 1)  # По умолчанию 1 если сумма неизвестна
                package_type = payment.get('metadata', {}).get('package_type', '')

                add_balance(user_id, tokens)
                add_payment(user_id, amount, 'succeeded', payment.get('id'))
                logging.info(f"✅ Начислено {tokens} токенов пользователю {user_id} (пакет: {package_type})")

                # Отправляем уведомление через asyncio.create_task чтобы избежать
                # "Timeout context manager should be used inside a task"
                async def _notify_payment(uid=user_id, tok=tokens, pkg=package_type):
                    try:
                        if pkg == 'novice':
                            # Пакет «Новичок» — специальное сообщение
                            await bot.send_message(
                                int(uid),
                                "🎉 Пакет «Новичок» активирован. Тебе начислено 5 токенов. Твори прямо сейчас!\n\n"
                                "И обязательно посмотри примеры треков в нашем канале — <a href='https://t.me/ALBImusic_Chart/146'>ЗДЕСЬ</a>",
                                parse_mode="HTML"
                            )
                        elif pkg == 'weekend':
                            # Пакет «Выходные» — специальное сообщение
                            await bot.send_message(
                                int(uid),
                                "🎉 Тебе начислено 5 токенов. Пакет «Выходные» активирован. Срочно пиши песни про друзей!",
                                parse_mode="HTML"
                            )
                        elif pkg == 'newcomer_offer':
                            # Новичковый оффер — разовое предложение для новичков
                            await bot.send_message(
                                int(uid),
                                "🎁 <b>Стартовый пакет активирован!</b>\n\n"
                                "Тебе начислено 5 токенов — это 10 треков. Твори прямо сейчас!\n\n"
                                "И обязательно посмотри примеры треков в нашем канале — "
                                "<a href='https://t.me/ALBImusic_Chart/146'>ЗДЕСЬ</a>",
                                parse_mode="HTML"
                            )
                        else:
                            inline_kb = InlineKeyboardMarkup(row_width=2)
                            inline_kb.add(
                                InlineKeyboardButton("🎵 Создать песню", callback_data="create_song_inline"),
                                InlineKeyboardButton("🎶 Создать музыку", callback_data="create_music_inline")
                            )
                            await bot.send_message(
                                int(uid),
                                f"🎉 Спасибо! Оплата поступила!\n\n"
                                f"💰 Начислено: *{tok} токенов*\n\n"
                                f"🎵 Теперь вы получаете полные версии песен!\n\n"
                                f"Нажмите кнопку ниже чтобы начать 👇",
                                reply_markup=inline_kb,
                                parse_mode="Markdown"
                            )
                    except Exception as e:
                        logging.error(f"❌ Не удалось отправить уведомление пользователю {uid}: {e}")
                asyncio.create_task(_notify_payment())
                return JSONResponse({"status": "ok"})
        return JSONResponse({"status": "ignored"})
    except Exception as e:
        logging.error(f"❌ Ошибка webhook: {e}")
        return JSONResponse({"status": "error"}, status_code=400)

# Обработчики Telegram бота
@dp.message_handler(Command('start'), state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    # Сбрасываем состояние FSM если пользователь был в процессе генерации
    await state.finish()

    user = message.from_user
    invited_by = None
    if len(message.text.split()) > 1:
        ref_param = message.text.split()[1]
        if ref_param.startswith('ref_'):
            try:
                invited_by = int(ref_param.split('_')[1])
            except:
                pass
    await add_user(user.id, user.username, user.first_name, invited_by)

    # Если пользователь ранее блокировал бота и теперь написал снова — снимаем пометку
    try:
        execute_query_sync(
            "UPDATE users SET is_blocked = FALSE WHERE user_id = %s AND is_blocked = TRUE",
            (user.id,)
        )
    except Exception:
        pass

    if invited_by and invited_by != user.id:
        try:
            # Используем db_utils для реферальной системы
            from db_utils import execute_query_sync
            result = execute_query_sync(
                'SELECT COUNT(*) FROM referrals WHERE referrer_id = %s AND referred_id = %s',
                (invited_by, user.id)
            )
            if result and result[0][0] == 0:
                # Добавляем запись о реферале
                execute_query_sync(
                    'INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (%s, %s, NOW())',
                    (invited_by, user.id)
                )
                
                # Считаем сколько всего рефералов
                count_result = execute_query_sync(
                    'SELECT COUNT(*) FROM referrals WHERE referrer_id = %s',
                    (invited_by,)
                )
                referral_count = count_result[0][0] if count_result else 0
                
                # Базовая награда: 2 токена
                tokens_to_add = 2
                message_text = f"🎉 По вашей ссылке зарегистрировался новый пользователь!\n\n💰 Вам начислено 2 токена бесплатно!"
                
                # Бонус за 5-го реферала
                if referral_count == 5:
                    tokens_to_add = 7  # 2 базовых + 5 бонус
                    message_text = f"🎉🎉🎉 ПОЗДРАВЛЯЕМ!\n\nВы пригласили 5-го друга!\n\n💰 Вам начислено 7 токенов (2 + бонус 5)!\n🎁 Продолжайте приглашать и зарабатывать!"
                
                execute_query_sync(
                    'UPDATE users SET balance = balance + %s WHERE user_id = %s',
                    (tokens_to_add, invited_by)
                )
                
                try:
                    await bot.send_message(invited_by, message_text)
                except:
                    pass
                logging.info(f"✅ Реферал: {invited_by} получил {tokens_to_add} токенов за {user.id} (всего рефералов: {referral_count})")
        except Exception as e:
            logging.error(f"❌ Ошибка обработки реферала: {e}")
    
    # Deep link: ?start=song — сразу переходим к созданию песни (из рассылки/рекламы)
    if len(message.text.split()) > 1 and message.text.split()[1] == 'song':
        await message.answer(
            "Отлично! Придумать за тебя текст или у тебя свой?",
            reply_markup=InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton("✨ ПРИДУМАТЬ ТЕКСТ", callback_data="text_ai"),
                InlineKeyboardButton("📝 У МЕНЯ СВОЙ ТЕКСТ", callback_data="text_own")
            )
        )
        await CreateSongStates.choosing_text_type.set()
        return

    welcome_text = """Привет! Прямо сейчас жми «Создать песню»! Если надо, я сам сочиню слова!"""
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(user.id), parse_mode="Markdown")
    # Отправляем 3 демо-трека — пользователь слышит результат сразу
    await bot.send_message(user.id, "🎧 Вот примеры того, что я умею:")
    for track in DEMO_TRACKS:
        await bot.send_audio(user.id, track["file_id"], title=track["title"], performer="AlBi Music AI")

    # Приглашение в канал после демо-треков
    channel_invite_markup = InlineKeyboardMarkup()
    channel_invite_markup.add(InlineKeyboardButton("🔔 Подписаться на канал", url="https://t.me/ALBImusic_chart"))
    await bot.send_message(
        user.id,
        "🎵 У нас есть канал — там каждый день новые песни от пользователей, "
        "крутые промпты, обучение и первым узнаешь о новых функциях 👇",
        reply_markup=channel_invite_markup
    )

@dp.message_handler(lambda message: message.text == "🎵 Создать песню", state='*')
async def handle_create_song(message: types.Message, state: FSMContext):
    # Сбрасываем состояние FSM если пользователь был в процессе генерации
    await state.finish()
    track_first_menu_action(message.from_user.id)

    # Новый флоу: выбор типа текста (InlineKeyboard внутри сообщения)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✨ ПРИДУМАТЬ ТЕКСТ", callback_data="text_ai"),
        InlineKeyboardButton("📝 У МЕНЯ СВОЙ ТЕКСТ", callback_data="text_own")
    )

    text = "Отлично! Придумать за тебя текст или у тебя свой?"

    await CreateSongStates.choosing_text_type.set()
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "🎶 Создать музыку", state='*')
async def handle_create_music(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Создать музыку' - инструментальная музыка без слов"""
    await state.finish()
    track_first_menu_action(message.from_user.id)

    # Создаем клавиатуру с жанрами (те же 16 жанров)
    markup = InlineKeyboardMarkup(row_width=2)
    genres = [
        ("🎤 Поп", "music_genre_pop"),
        ("🎸 Рок", "music_genre_rock"),
        ("🎺 Джаз", "music_genre_jazz"),
        ("🎵 Блюз", "music_genre_blues"),
        ("🎧 Хип-хоп", "music_genre_hiphop"),
        ("⚡ Электронная", "music_genre_electronic"),
        ("🎻 Классическая", "music_genre_classical"),
        ("💿 R&B/Соул", "music_genre_rnb"),
        ("🌴 Регги", "music_genre_reggae"),
        ("🤠 Кантри", "music_genre_country"),
        ("🤘 Метал", "music_genre_metal"),
        ("🪕 Фолк", "music_genre_folk"),
        ("💃 Латины", "music_genre_latin"),
        ("🎭 Панк", "music_genre_punk"),
        ("🕺 Фанк", "music_genre_funk"),
        ("🎙️ Шансон", "music_genre_shanson"),
        ("✏️ Свой вариант", "music_genre_custom")
    ]

    buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in genres]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.add(buttons[i])

    text = (
        "🎶 **СОЗДАЕМ ИНСТРУМЕНТАЛЬНУЮ МУЗЫКУ**\n\n"
        "🎹 Музыка БЕЗ слов - только мелодия и ритм!\n\n"
        "Выбери жанр для твоей композиции 👇"
    )

    await MusicStates.waiting_for_music_style.set()
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "💰 Баланс", state='*')
async def handle_balance(message: types.Message, state: FSMContext):
    # Сбрасываем состояние FSM если пользователь был в процессе генерации
    await state.finish()
    track_first_menu_action(message.from_user.id)

    user_id_bal = message.from_user.id
    balance = get_user_balance(user_id_bal)
    # Проверяем новичковое окно
    is_novice_active, hours_left_bal, gens_bought_bal = get_novice_status(user_id_bal)
    if is_novice_active and gens_bought_bal < 10:
        remaining_bal = 10 - gens_bought_bal
        novice_block = (
            f"\n🎁 *СПЕЦИАЛЬНАЯ ЦЕНА ДЛЯ НОВИЧКА (⏰ ещё {int(hours_left_bal)} ч):*\n"
            f"🔥 *29₽ за 1 генерацию* — доступно ещё {remaining_bal} из 10!\n"
            f"После истечения 24ч — стандартные цены от 99₽.\n"
        )
    else:
        novice_block = ""
    text = (
        f"💰 *Ваш баланс:* {balance}\n\n"
        f"💳 *Пополнить баланс:*\n"
        f"{novice_block}\n"
        f"🎁 *5 генераций (10 треков) — 99₽* ← старт!\n"
        f"💳 10 генераций (20 треков) — 490₽\n"
        f"🔥 25 генераций (50 треков) — 990₽ (ХИТ!)\n"
        f"⭐ 60 генераций (120 треков) — 1990₽\n"
        f"💎 140 генераций (280 треков) — 3990₽\n\n"
        f"🌟 *Пригласи друга* — получи 2 токена бесплатно!\n\n"
        f"🎵 Вдохновение — в нашем канале: @ALBImusic\\_chart"
    )
    await message.answer(text, reply_markup=get_balance_keyboard(user_id_bal), parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "📂 Мои треки", state='*')
async def handle_my_tracks(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    track_first_menu_action(user_id)

    # Получаем последние 20 генераций.
    # Используем LEFT JOIN с demo_tracks чтобы показывать треки даже если статус в
    # generations был испорчен (например, из-за бага ERROR_NOTIFIED).
    tracks = execute_query_sync(
        """
        SELECT g.task_id, g.prompt,
               COALESCE(dt.full_url_1, g.audio_url) AS audio_url,
               g.created_at, g.status
        FROM generations g
        LEFT JOIN demo_tracks dt ON dt.task_id = g.task_id AND dt.user_id = g.user_id
        WHERE g.user_id = %s
          AND (
              g.status = 'completed'
              OR dt.task_id IS NOT NULL
          )
        ORDER BY g.created_at DESC
        LIMIT 20
        """,
        (user_id,)
    )

    if not tracks:
        await message.answer("📂 У вас пока нет сохраненных треков.\n\nСоздайте свою первую композицию! 🎵")
        return

    text = f"🎵 <b>ТВОИ КОМПОЗИЦИИ</b>\n\n📊 Всего создано: {len(tracks)} треков\n\n"

    for idx, (task_id, prompt, audio_url, created_at, status) in enumerate(tracks[:10], 1):
        # Форматируем дату
        date_str = created_at.strftime("%d %b") if hasattr(created_at, 'strftime') else str(created_at)[:10]
        # Короткое описание - экранируем HTML
        short_prompt = (prompt[:30] + '...') if len(prompt) > 30 else prompt
        short_prompt = short_prompt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text += f"━━━━━━━━━━━━━━━━━\n🎼 #{idx} • {date_str}\n{short_prompt}\n"

        # Inline кнопки для каждого трека
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🔊 Слушать", callback_data=f"play_{task_id}"),
            InlineKeyboardButton("🔁 Повторить", callback_data=f"repeat_{task_id}")
        )
        markup.add(
            InlineKeyboardButton("🔗 Отправить другу", switch_inline_query="")
        )
        # Отправляем каждый трек отдельным сообщением с кнопками
        await message.answer(text, reply_markup=markup, parse_mode="HTML")
        text = ""  # Сбрасываем для следующего

    if len(tracks) > 10:
        await message.answer(f"... и еще {len(tracks)-10} треков")

@dp.message_handler(lambda message: message.text == "🎤 Минусовка", state='*')
async def handle_karaoke_menu(message: types.Message, state: FSMContext):
    """Обработчик кнопки Минусовка в главном меню - выбор источника"""
    await state.finish()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📂 Из моих треков", callback_data="karaoke_source_my"),
        InlineKeyboardButton("📤 Загрузить свой файл", callback_data="karaoke_source_upload")
    )

    text = (
        "🎤 <b>КАРАОКЕ</b>\n\n"
        "Минусовка — это инструментальная версия БЕЗ вокала.\n"
        "Идеально для исполнения!\n\n"
        "💰 Стоимость: 1 токен\n\n"
        "<b>Выбери источник:</b>"
    )

    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "karaoke_source_my")
async def handle_karaoke_from_tracks(callback_query: types.CallbackQuery):
    """Минусовка из своих треков"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Получаем последние 10 треков
    tracks = execute_query_sync(
        "SELECT task_id, prompt, created_at FROM generations WHERE user_id = %s AND status = 'completed' ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    )

    if not tracks:
        await bot.send_message(
            user_id,
            "📂 У вас пока нет треков для минусовка.\n\n"
            "Создайте песню или загрузите свой файл! 🎵"
        )
        return

    text = "🎤 <b>ВЫБЕРИ ТРЕК ДЛЯ КАРАОКЕ</b>\n\n"

    for idx, (task_id, prompt, created_at) in enumerate(tracks, 1):
        date_str = created_at.strftime("%d %b") if hasattr(created_at, 'strftime') else str(created_at)[:10]
        short_prompt = (prompt[:35] + '...') if len(prompt) > 35 else prompt
        short_prompt = short_prompt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            f"🎤 Сделать минусовка",
            callback_data=f"karaoke_{task_id}"
        ))

        track_text = f"🎼 #{idx} • {date_str}\n{short_prompt}"
        await bot.send_message(user_id, track_text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "karaoke_source_upload")
async def handle_karaoke_upload(callback_query: types.CallbackQuery, state: FSMContext):
    """Минусовка из загруженного файла"""
    await bot.answer_callback_query(callback_query.id)

    text = (
        "🎤 <b>ЗАГРУЗИ АУДИО ДЛЯ КАРАОКЕ</b>\n\n"
        "Отправь мне аудио файл (MP3, WAV, M4A, OGG)\n\n"
        "⚠️ Ограничения:\n"
        "• Максимум 5 минут\n"
        "• Размер до 20 МБ\n\n"
        "Я отделю вокал и создам инструментальную версию!"
    )

    await KaraokeStates.waiting_for_audio_upload.set()
    await bot.send_message(callback_query.from_user.id, text, parse_mode="HTML")

@dp.message_handler(lambda message: message.text == "🎸 Кавер", state='*')
async def handle_cover_menu(message: types.Message, state: FSMContext):
    """Обработчик кнопки Кавер в главном меню - выбор источника"""
    await state.finish()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📂 Из моих треков", callback_data="cover_source_my"),
        InlineKeyboardButton("📤 Загрузить свой файл", callback_data="cover_source_upload")
    )

    text = (
        "🎸 <b>КАВЕР</b>\n\n"
        "Кавер — это та же песня в новом стиле.\n"
        "Выбирай из 16 жанров!\n\n"
        "💰 Стоимость: 2 токена\n\n"
        "<b>Выбери источник:</b>"
    )

    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "cover_source_my")
async def handle_cover_from_tracks(callback_query: types.CallbackQuery):
    """Кавер из своих треков"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Получаем последние 10 треков
    tracks = execute_query_sync(
        "SELECT task_id, prompt, created_at FROM generations WHERE user_id = %s AND status = 'completed' ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    )

    if not tracks:
        await bot.send_message(
            user_id,
            "📂 У вас пока нет треков для кавера.\n\n"
            "Создайте песню или загрузите свой файл! 🎵"
        )
        return

    text = "🎸 <b>ВЫБЕРИ ТРЕК ДЛЯ КАВЕРА</b>\n\n"

    for idx, (task_id, prompt, created_at) in enumerate(tracks, 1):
        date_str = created_at.strftime("%d %b") if hasattr(created_at, 'strftime') else str(created_at)[:10]
        short_prompt = (prompt[:35] + '...') if len(prompt) > 35 else prompt
        short_prompt = short_prompt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            f"🎸 Сделать кавер",
            callback_data=f"cover_{task_id}"
        ))

        track_text = f"🎼 #{idx} • {date_str}\n{short_prompt}"
        await bot.send_message(user_id, track_text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "cover_source_upload")
async def handle_cover_upload(callback_query: types.CallbackQuery, state: FSMContext):
    """Кавер из загруженного файла"""
    await bot.answer_callback_query(callback_query.id)

    text = (
        "🎸 <b>ЗАГРУЗИ АУДИО ДЛЯ КАВЕРА</b>\n\n"
        "Отправь мне аудио файл (MP3, WAV, M4A, OGG)\n\n"
        "⚠️ Ограничения:\n"
        "• Максимум 5 минут\n"
        "• Размер до 20 МБ\n\n"
        "После загрузки выберешь новый стиль!"
    )

    await CoverStates.waiting_for_audio_upload.set()
    await bot.send_message(callback_query.from_user.id, text, parse_mode="HTML")

@dp.message_handler(lambda message: message.text == "❤️ Примеры песен", state='*')
async def handle_song_examples(message: types.Message, state: FSMContext):
    await state.finish()
    track_first_menu_action(message.from_user.id)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("❤️ Слушать примеры песен", url="https://t.me/ALBImusic_Chart/146"))
    await message.answer("Слушай треки, созданные нашим ботом 🎵", reply_markup=markup)
@dp.message_handler(lambda message: message.text == "📄 Документы", state='*')
async def handle_documents(message: types.Message, state: FSMContext):
    # Сбрасываем состояние FSM если пользователь был в процессе генерации
    await state.finish()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📜 Политика конфиденциальности", callback_data="show_privacy"),
        InlineKeyboardButton("📄 Публичная оферта", callback_data="show_offer")
    )
    await message.answer("📄 *Правовые документы:*", reply_markup=markup, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "👨‍💻 Админ панель", state='*')
async def handle_admin_panel(message: types.Message, state: FSMContext):
    # Сбрасываем состояние FSM если пользователь был в процессе генерации
    await state.finish()

    if is_admin(message.from_user.id):
        await message.answer("👨‍💻 *Панель администратора:*", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("⛔ Доступ запрещен")

# ========== INLINE QUERY HANDLER (Отправить другу) ==========

@dp.inline_handler()
async def inline_query_handler(inline_query: InlineQuery):
    """Обработчик inline запросов для функции 'Отправить другу'"""
    user_id = inline_query.from_user.id
    query_text = inline_query.query.strip()

    try:
        logging.info(f"🔍 Inline query: user_id={user_id}, query='{query_text}'")

        # Извлекаем UUID из начала строки (игнорируем остальной текст)
        import re
        task_id_match = re.match(r'^([a-f0-9\-]{36})', query_text)
        task_id = task_id_match.group(1) if task_id_match else query_text

        # Если в query есть task_id - показываем конкретный трек
        if task_id:
            tracks = execute_query_sync(
                """SELECT task_id, prompt, audio_url, created_at
                   FROM generations
                   WHERE user_id = %s AND task_id = %s AND status = 'completed' AND audio_url NOT LIKE 'ERROR%%'
                   LIMIT 1""",
                (user_id, task_id)
            )
            logging.info(f"🔍 UUID извлечён: '{task_id}', найдено треков: {len(tracks) if tracks else 0}")
        else:
            # Иначе показываем последние 5 треков
            tracks = execute_query_sync(
                """SELECT task_id, prompt, audio_url, created_at
                   FROM generations
                   WHERE user_id = %s AND status = 'completed' AND audio_url NOT LIKE 'ERROR%%'
                   ORDER BY created_at DESC
                   LIMIT 5""",
                (user_id,)
            )

        results = []

        if tracks:
            for idx, (task_id, prompt, audio_url_raw, created_at) in enumerate(tracks):
                # Парсим JSON если есть массив
                import json
                audio_urls = []

                # Убираем префикс ALREADY_SENT_ если есть
                if isinstance(audio_url_raw, str) and audio_url_raw.startswith('ALREADY_SENT_'):
                    audio_url_raw = audio_url_raw.replace('ALREADY_SENT_', '', 1)

                if isinstance(audio_url_raw, str) and audio_url_raw.startswith('['):
                    try:
                        audio_urls = json.loads(audio_url_raw)
                    except:
                        audio_urls = [audio_url_raw]
                else:
                    audio_urls = [audio_url_raw] if audio_url_raw else []

                if not audio_urls:
                    continue

                first_audio_url = audio_urls[0]

                # Короткое описание
                short_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
                date_str = created_at.strftime("%d.%m.%Y") if hasattr(created_at, 'strftime') else str(created_at)[:10]

                # Экранируем HTML специальные символы
                import html
                safe_prompt = html.escape(short_prompt)
                # Для URL: экранируем &, <, >, но НЕ кавычки (они нужны в атрибуте)
                safe_url = html.escape(first_audio_url, quote=False)

                # Формируем сообщение с ссылкой на музыку (HTML формат)
                # Используем одинарные кавычки для атрибута href
                message_text = (
                    f"🎵 <b>Зацени что я создал!</b>\n\n"
                    f"{safe_prompt}\n\n"
                    f"🎧 <a href='{safe_url}'>Слушать трек</a>\n\n"
                    f"🤖 Крутой AI-бот делает песни и музыку за пару минут!\n\n"
                    f"Попробуй сам → @AlBimusic_bot 🚀"
                )

                # Создаем результат для отправки (Article вместо Audio)
                result = InlineQueryResultArticle(
                    id=str(idx),
                    title="👆 НАЖМИ СЮДА ЧТОБЫ ОТПРАВИТЬ 👆",
                    description=f"🎵 {short_prompt[:60]}",
                    thumb_url="https://albi-music.ru/logo.png",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    )
                )
                results.append(result)

        if not results:
            # Если нет треков, показываем приглашение
            logging.warning(f"⚠️ Треки не найдены для user_id={user_id}, query='{query_text}'")
            result = InlineQueryResultArticle(
                id="0",
                title="🎵 У вас пока нет треков",
                description="Создайте свою первую песню в боте!",
                input_message_content=InputTextMessageContent(
                    message_text="🎵 Зацени что я нашёл!\n\nКрутой AI-бот делает песни за пару минут!\n\nПопробуй сам → @AlBimusic_bot 🚀"
                )
            )
            results.append(result)
        else:
            logging.info(f"✅ Отправка {len(results)} результатов для inline query")

        await bot.answer_inline_query(inline_query.id, results=results, cache_time=1)

    except Exception as e:
        logging.error(f"❌ Ошибка inline query: {e}")
        # Возвращаем пустой результат при ошибке
        await bot.answer_inline_query(inline_query.id, results=[], cache_time=1)

# ========== НОВЫЙ ФЛОУ СОЗДАНИЯ ПЕСНИ ==========

@dp.callback_query_handler(lambda c: c.data == "text_ai", state=[CreateSongStates.choosing_text_type, CreateSongStates.waiting_own_lyrics, CreateSongStates.waiting_song_idea])
async def handle_ai_text(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    text = (
        "✨ **СЕЙЧАС МЫ ТЕБЕ СОЧИНИМ САМЫЙ ЛУЧШИЙ ТЕКСТ!**\n\n"
        "Про что и для кого ты хочешь песню? Напиши мне.\n\n"
        "▪️ для кого / о ком\n"
        "▪️ какие интересные моменты упомянуть\n"
        "▪️ идея которую хочется передать песней\n\n"
        "📩 Всё в ОДНОМ сообщении — и я создам текст!\n\n"
        "💡 _Совет: опиши кратко самое главное (до 200 символов)_ ✨"
    )

    await CreateSongStates.waiting_song_idea.set()
    refresh_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"))
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown", reply_markup=refresh_btn)

@dp.callback_query_handler(lambda c: c.data == "text_own", state=[CreateSongStates.choosing_text_type, CreateSongStates.waiting_own_lyrics, CreateSongStates.waiting_song_idea])
async def handle_own_text(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    text = (
        "📝 **ОТЛИЧНО!**\n\n"
        "Отправь мне текст своей песни, и мы перейдем к выбору жанра 🎵"
    )

    await CreateSongStates.waiting_own_lyrics.set()
    refresh_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"))
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown", reply_markup=refresh_btn)

@dp.message_handler(state=CreateSongStates.waiting_song_idea)
async def process_song_idea(message: types.Message, state: FSMContext):
    """Получили описание для AI-генерации текста"""
    song_idea = message.text
    user_id = message.from_user.id

    # Проверяем баланс (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance <= 0:
            await send_no_tokens_message(user_id, "Бесплатные генерации закончились! Нажмите 💰 Баланс для пополнения.", state)
            return

    # Ограничение Suno API: макс 200 символов
    MAX_PROMPT_LENGTH = 200

    if len(song_idea) > MAX_PROMPT_LENGTH:
        # Сокращаем до 200 символов
        song_idea_short = song_idea[:MAX_PROMPT_LENGTH]
        await message.answer(
            f"⚠️ Ваше описание слишком длинное ({len(message.text)} символов).\n"
            f"Suno API принимает максимум {MAX_PROMPT_LENGTH} символов (примерно 30-35 слов).\n\n"
            f"Использую сокращенное описание (первые {MAX_PROMPT_LENGTH} символов):\n\n_{song_idea_short}_",
            parse_mode="Markdown"
        )
        song_idea = song_idea_short

    # Сохраняем описание
    await state.update_data(song_idea=song_idea)

    await message.answer("⏳ Генерирую ДВА варианта текста... Это займет около 1-2 минут...")

    # Вызываем Suno API для генерации ДВУХ вариантов текста
    import asyncio

    try:
        # Запускаем генерацию двух вариантов параллельно
        loop = asyncio.get_event_loop()

        # Генерируем два варианта одновременно
        results = await asyncio.gather(
            loop.run_in_executor(None, generate_suno_lyrics_sync, song_idea, user_id),
            loop.run_in_executor(None, generate_suno_lyrics_sync, song_idea, user_id),
            return_exceptions=True
        )

        lyrics_variant1, lyrics_variant2 = results

        # Проверяем что оба варианта сгенерировались
        if not lyrics_variant1 or not lyrics_variant2:
            await message.answer(
                "❌ **К сожалению, AI не смог подобрать текст для этой идеи.**\n\n"
                "💡 **Что можно сделать:**\n"
                "• Попробуй переформулировать идею по-другому\n"
                "• Или нажми «У меня свой текст» и напиши текст сам\n\n"
                "👇 Жми «Создать песню» чтобы попробовать снова!",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
            await state.finish()
            return

        # Сохраняем оба варианта в FSM
        await state.update_data(
            lyrics_variant1=lyrics_variant1,
            lyrics_variant2=lyrics_variant2,
            is_ai_generated=True
        )

        # Показываем оба варианта пользователю
        MAX_MSG_LENGTH = 3500  # Оставляем место для заголовка

        # Вариант 1
        variant1_text = f"✨ **ВАРИАНТ 1:**\n\n{lyrics_variant1}"
        if len(variant1_text) <= MAX_MSG_LENGTH:
            await message.answer(variant1_text, parse_mode="Markdown")
        else:
            await message.answer(f"✨ **ВАРИАНТ 1:**\n\n{lyrics_variant1[:MAX_MSG_LENGTH]}", parse_mode="Markdown")
            remaining = lyrics_variant1[MAX_MSG_LENGTH:]
            while remaining:
                chunk = remaining[:4000]
                await message.answer(chunk, parse_mode="Markdown")
                remaining = remaining[4000:]

        await message.answer("━━━━━━━━━━━━━━━━━━")

        # Вариант 2
        variant2_text = f"✨ **ВАРИАНТ 2:**\n\n{lyrics_variant2}"
        if len(variant2_text) <= MAX_MSG_LENGTH:
            await message.answer(variant2_text, parse_mode="Markdown")
        else:
            await message.answer(f"✨ **ВАРИАНТ 2:**\n\n{lyrics_variant2[:MAX_MSG_LENGTH]}", parse_mode="Markdown")
            remaining = lyrics_variant2[MAX_MSG_LENGTH:]
            while remaining:
                chunk = remaining[:4000]
                await message.answer(chunk, parse_mode="Markdown")
                remaining = remaining[4000:]

        # Кнопки выбора варианта
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📝 Выбрать вариант 1", callback_data="lyrics_variant_1"),
            InlineKeyboardButton("📝 Выбрать вариант 2", callback_data="lyrics_variant_2")
        )
        markup.add(InlineKeyboardButton("✏️ Написать свой текст", callback_data="lyrics_write_own"))

        await CreateSongStates.choosing_lyrics_variant.set()
        await message.answer(
            "👆 **Выбери понравившийся вариант!**\n\n"
            "💡 _Совет: ты можешь скопировать любой вариант, откорректировать его и отправить как свой текст (кнопка \"Написать свой текст\")_",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Ошибка генерации текста: {e}")
        await message.answer(
            "❌ Произошла ошибка при генерации текста. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        await state.finish()

@dp.message_handler(state=CreateSongStates.waiting_own_lyrics)
async def process_own_lyrics(message: types.Message, state: FSMContext):
    """Получили текст от пользователя"""
    lyrics = message.text
    
    # Убираем "Текст:" если пользователь добавил его в начале
    lyrics = re.sub(r'^Текст:\s*', '', lyrics, flags=re.IGNORECASE).strip()

    if len(lyrics) > 3000:
        await message.answer("❌ Текст слишком длинный. Максимум 3000 символов.")
        return

    await state.update_data(lyrics=lyrics, is_ai_generated=False)

    # Сразу переходим к выбору жанра (свой текст не требует подтверждения)
    await show_genre_selection(message, state)

# ========== ОБРАБОТЧИКИ ВЫБОРА ВАРИАНТА ТЕКСТА ==========

@dp.callback_query_handler(lambda c: c.data == "lyrics_variant_1", state=CreateSongStates.choosing_lyrics_variant)
async def handle_lyrics_variant_1(callback_query: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал вариант 1"""
    await bot.answer_callback_query(callback_query.id)

    # Получаем вариант 1 из FSM
    data = await state.get_data()
    lyrics = data.get('lyrics_variant1', '')

    if not lyrics:
        await bot.send_message(callback_query.from_user.id, "❌ Ошибка: текст не найден. Попробуй создать песню заново.")
        await state.finish()
        return

    # Сохраняем выбранный текст
    await state.update_data(lyrics=lyrics, is_ai_generated=True)

    await bot.send_message(
        callback_query.from_user.id,
        "✅ **Отлично! Ты выбрал вариант 1**\n\nТеперь выбери жанр для своей песни 🎵",
        parse_mode="Markdown"
    )

    # Переходим к выбору жанра
    await show_genre_selection_callback(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == "lyrics_variant_2", state=CreateSongStates.choosing_lyrics_variant)
async def handle_lyrics_variant_2(callback_query: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал вариант 2"""
    await bot.answer_callback_query(callback_query.id)

    # Получаем вариант 2 из FSM
    data = await state.get_data()
    lyrics = data.get('lyrics_variant2', '')

    if not lyrics:
        await bot.send_message(callback_query.from_user.id, "❌ Ошибка: текст не найден. Попробуй создать песню заново.")
        await state.finish()
        return

    # Сохраняем выбранный текст
    await state.update_data(lyrics=lyrics, is_ai_generated=True)

    await bot.send_message(
        callback_query.from_user.id,
        "✅ **Отлично! Ты выбрал вариант 2**\n\nТеперь выбери жанр для своей песни 🎵",
        parse_mode="Markdown"
    )

    # Переходим к выбору жанра
    await show_genre_selection_callback(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == "lyrics_write_own", state=CreateSongStates.choosing_lyrics_variant)
async def handle_lyrics_write_own(callback_query: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет написать свой текст (редактировать)"""
    await bot.answer_callback_query(callback_query.id)

    text = (
        "✏️ **РЕДАКТИРОВАНИЕ ТЕКСТА**\n\n"
        "Отправь мне текст своей песни.\n\n"
        "💡 _Совет: скопируй понравившийся вариант выше, внеси изменения и отправь мне_"
    )

    await CreateSongStates.waiting_own_lyrics.set()
    refresh_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"))
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown", reply_markup=refresh_btn)

async def show_lyrics_for_review(message: types.Message, state: FSMContext, lyrics: str, is_regeneration=False):
    """Показывает сгенерированный текст и кнопки: продолжить или перегенерировать"""

    # Показываем полный текст (разбиваем если > 4000 символов)
    MAX_MSG_LENGTH = 4000

    if len(lyrics) <= MAX_MSG_LENGTH:
        await message.answer(f"🎵 **ВОТ ТВОЙ ТЕКСТ:**\n\n{lyrics}", parse_mode="Markdown")
    else:
        # Разбиваем на части
        await message.answer(f"🎵 **ВОТ ТВОЙ ТЕКСТ:**\n\n{lyrics[:MAX_MSG_LENGTH]}", parse_mode="Markdown")
        remaining = lyrics[MAX_MSG_LENGTH:]
        while remaining:
            chunk = remaining[:MAX_MSG_LENGTH]
            await message.answer(chunk, parse_mode="Markdown")
            remaining = remaining[MAX_MSG_LENGTH:]

    # Кнопки выбора
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✅ Отлично, продолжить", callback_data="lyrics_approve"),
        InlineKeyboardButton("🔄 Сгенерировать другой текст", callback_data="lyrics_regenerate")
    )

    await CreateSongStates.reviewing_lyrics.set()
    await message.answer(
        "💡 **Что делаем дальше?**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def show_genre_selection(message: types.Message, state: FSMContext):
    """Показывает кнопки выбора жанра"""

    # Создаем клавиатуру с жанрами
    markup = InlineKeyboardMarkup(row_width=2)
    genres = [
        ("🎤 Поп", "genre_pop"),
        ("🎸 Рок", "genre_rock"),
        ("🎺 Джаз", "genre_jazz"),
        ("🎵 Блюз", "genre_blues"),
        ("🎧 Хип-хоп", "genre_hiphop"),
        ("⚡ Электронная", "genre_electronic"),
        ("🎻 Классическая", "genre_classical"),
        ("💿 R&B/Соул", "genre_rnb"),
        ("🌴 Регги", "genre_reggae"),
        ("🤠 Кантри", "genre_country"),
        ("🤘 Метал", "genre_metal"),
        ("🪕 Фолк", "genre_folk"),
        ("💃 Латины", "genre_latin"),
        ("🎭 Панк", "genre_punk"),
        ("🕺 Фанк", "genre_funk"),
        ("🎙️ Шансон", "genre_shanson"),
        ("✏️ Свой вариант", "genre_custom")
    ]

    buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in genres]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.add(buttons[i])

    await CreateSongStates.waiting_genre.set()
    await message.answer("🎸 **Выбери в каком жанре написать песню:**", reply_markup=markup, parse_mode="Markdown")

async def show_genre_selection_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Wrapper для show_genre_selection для callback_query"""
    # Создаем fake message object для совместимости
    class FakeMessage:
        def __init__(self, callback_query):
            self.from_user = callback_query.from_user
            self.chat = callback_query.message.chat

        async def answer(self, text, **kwargs):
            return await bot.send_message(self.from_user.id, text, **kwargs)

    fake_msg = FakeMessage(callback_query)
    await show_genre_selection(fake_msg, state)

# ... (продолжение следует)

# Callback обработчики
@dp.callback_query_handler(lambda c: c.data == 'create_song')
async def process_create_song(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "🎤 *Отлично! Сначала опишите стиль песни:*\n\n• Жанр (рок, поп, хип-хоп, классика...)\n• Музыкальные инструменты\n• Мужской/женский голос\n• Темп, настроение", parse_mode="Markdown")
    await SongStates.waiting_for_song_style.set()

@dp.callback_query_handler(lambda c: c.data == 'create_music')
async def process_create_music(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "🎵 *Опишите стиль музыки:*\n\n• Жанр и направление\n• Музыкальные инструменты\n• Ритм и темп\n• Настроение и атмосфера", parse_mode="Markdown")
    await MusicStates.waiting_for_music_style.set()

@dp.callback_query_handler(lambda c: c.data.startswith('pay_') and c.data != 'pay_29_novice' and not c.data.startswith('pay_unlock_29_'))
async def process_payment(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Определяем сумму и количество токенов
    payment_data = {
        'pay_99':         (99,  5,   "Пакет «Старт» (5 генераций — 10 треков)"),   # ← новая кнопка
        'pay_500':        (490,  10,  "10 генераций (20 треков)"),
        'pay_1000':       (990,  25,  "25 генераций (50 треков)"),
        'pay_2000':       (1990, 60,  "60 генераций (120 треков)"),
        'pay_4000':       (3990, 140, "140 генераций (280 треков)"),
        'pay_99_novice':  (99,   5,   "Пакет «Новичок» (5 генераций — 10 треков)"),
        'pay_99_weekend': (99,   5,   "Пакет «Выходные» (5 генераций — 10 треков)"),
        # Обратная совместимость со старыми кнопками
        'pay_100':  (50,   1,   "1 токен"),
        'pay_490':  (490,  10,  "10 токенов"),
        'pay_990':  (990,  25,  "25 токенов"),
        'pay_1990': (1990, 60,  "60 токенов"),
        'pay_3990': (3990, 140, "140 токенов")
    }

    if callback_query.data in payment_data:
        amount, tokens, description = payment_data[callback_query.data]
    else:
        await bot.send_message(user_id, "❌ Неизвестный тариф")
        return

    # Определяем тип пакета для метаданных платежа
    package_type = ''
    if callback_query.data == 'pay_99_novice':
        package_type = 'novice'
    elif callback_query.data == 'pay_99_weekend':
        package_type = 'weekend'

    extra_meta = {'package_type': package_type} if package_type else None
    payment = await create_yookassa_payment(user_id, amount, f"Пополнение баланса: {description}", extra_meta)
    if payment and payment.get('confirmation', {}).get('confirmation_url'):
        payment_url = payment['confirmation']['confirmation_url']
        payment_id = payment['id']
        add_payment(user_id, amount, 'pending', payment_id)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("💳 Перейти к оплате", url=payment_url))

        await bot.send_message(
            user_id,
            f"💳 *Оплата {amount}₽*\n\n"
            f"🎵 Вы получите: {tokens} токенов\n\n"
            f"✅ После успешной оплаты баланс пополнится автоматически в течение 1-2 минут.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await bot.send_message(user_id, "❌ Ошибка при создании платежа. Попробуйте позже.")

@dp.callback_query_handler(lambda c: c.data == 'invite_friend')
async def process_invite_friend(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    referral_link = f"https://t.me/AlBimusic_bot?start=ref_{user_id}"

    # Считаем рефералов
    from db_utils import execute_query_sync
    count_result = execute_query_sync(
        'SELECT COUNT(*) FROM referrals WHERE referrer_id = %s',
        (user_id,)
    )
    referral_count = count_result[0][0] if count_result else 0
    
    # Прогресс-бар
    progress = "🟢" * referral_count + "⚪" * (5 - referral_count)
    bonus_text = ""
    if referral_count < 5:
        remaining = 5 - referral_count
        bonus_text = f"\n🎯 До бонуса +5 токенов: осталось {remaining} {'друг' if remaining == 1 else 'друга' if remaining < 5 else 'друзей'}!"
    elif referral_count == 5:
        bonus_text = "\n🎉 Бонус за 5-го друга получен!"
    
    # Отправляем сообщение с прогрессом
    await bot.send_message(
        user_id, 
        f"🎁 *Приглашено друзей:* {referral_count}/5\n{progress}{bonus_text}\n\nЧтобы получить 2 токена, скопируйте сообщение ниже и отправьте другу 👇",
        parse_mode="Markdown"
    )
    
    ready_text = f"""Привет! Я нашел крутого бота для создания музыки с помощью Искусственного Интеллекта. Попробуй! Там первый токен в подарок — это 1 песня бесплатно. Бот может просто музыку написать по описанию, а может реальную песню, если ему стихи загрузишь.
Прикольная штука :)
Вот ссылка - {referral_link}
Реально круто! ✨"""
    
    await bot.send_message(user_id, ready_text)

# ========================================
# ПРОВЕРКА ПОДПИСКИ НА КАНАЛ (нулевой баланс)
# ========================================

@dp.callback_query_handler(lambda c: c.data == 'check_subscription', state='*')
async def handle_check_subscription(callback_query: types.CallbackQuery, state: FSMContext):
    """Проверяет подписку пользователя на канал и начисляет 1 токен (один раз)"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Проверяем, не использовал ли уже этот бонус
    try:
        result = execute_query_sync(
            "SELECT channel_bonus_used FROM users WHERE user_id = %s",
            (user_id,)
        )
        already_used = result and result[0][0]
    except Exception:
        already_used = False

    if already_used:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("💳 Купить пакет генераций", callback_data="go_to_balance")
        )
        await bot.send_message(
            user_id,
            "⚠️ Бонус за подписку уже был использован.\n\n"
            "Для продолжения приобрети пакет генераций 👇",
            reply_markup=markup
        )
        return

    # Проверяем реальную подписку через Telegram API
    is_subscribed = await check_channel_subscription(user_id)

    if is_subscribed:
        # Начисляем 1 токен и отмечаем бонус использованным
        try:
            execute_query_sync(
                "UPDATE users SET balance = balance + 1, channel_bonus_used = TRUE WHERE user_id = %s",
                (user_id,)
            )
            logging.info(f"✅ Bonus channel token added for user {user_id}")
        except Exception as e:
            logging.error(f"❌ Error adding channel bonus for {user_id}: {e}")

        await bot.send_message(
            user_id,
            "✅ Вам начислен 1 токен!\n\n"
            "🎵 Теперь нажмите «Создать песню» и создайте свой первый трек!",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    else:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📢 Подписаться на @ALBImusic_Chart", url="https://t.me/ALBImusic_Chart"),
            InlineKeyboardButton("✅ Я подписался! Давай песню", callback_data="check_subscription"),
            InlineKeyboardButton("💳 Не хочу подписываться, хочу купить пакет", callback_data="go_to_balance")
        )
        await bot.send_message(
            user_id,
            "❗ Подписка не обнаружена.\n\n"
            "Сначала подпишись на канал @ALBImusic_Chart, затем нажми кнопку ниже 👇",
            reply_markup=markup
        )

@dp.callback_query_handler(lambda c: c.data == 'go_to_balance', state='*')
async def handle_go_to_balance(callback_query: types.CallbackQuery, state: FSMContext):
    """Перенаправляет на раздел Баланс для покупки пакета"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    balance = get_user_balance(user_id)
    text = (
        f"💰 *Ваш баланс:* {balance}\n\n"
        f"💳 *Выбери пакет:*"
    )
    await bot.send_message(user_id, text, reply_markup=get_balance_keyboard(user_id), parse_mode="Markdown")

# ========================================
# INLINE КНОПКИ ПОСЛЕ ОПЛАТЫ
# ========================================

@dp.callback_query_handler(lambda c: c.data == 'create_song_inline', state='*')
async def process_create_song_inline(callback_query: types.CallbackQuery, state: FSMContext):
    """Инлайн кнопка 'Создать песню' — показывается после оплаты"""
    await bot.answer_callback_query(callback_query.id)
    await state.finish()
    user_id = callback_query.from_user.id

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✨ ПРИДУМАТЬ ТЕКСТ", callback_data="text_ai"),
        InlineKeyboardButton("📝 У МЕНЯ СВОЙ ТЕКСТ", callback_data="text_own")
    )
    await CreateSongStates.choosing_text_type.set()
    await bot.send_message(user_id, "Отлично! Придумать за тебя текст или у тебя свой?", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == 'create_music_inline', state='*')
async def process_create_music_inline(callback_query: types.CallbackQuery, state: FSMContext):
    """Инлайн кнопка 'Создать музыку' — показывается после оплаты"""
    await bot.answer_callback_query(callback_query.id)
    await state.finish()
    user_id = callback_query.from_user.id

    markup = InlineKeyboardMarkup(row_width=2)
    genres = [
        ("🎤 Поп", "music_genre_pop"), ("🎸 Рок", "music_genre_rock"),
        ("🎺 Джаз", "music_genre_jazz"), ("🎵 Блюз", "music_genre_blues"),
        ("🎧 Хип-хоп", "music_genre_hiphop"), ("⚡ Электронная", "music_genre_electronic"),
        ("🎻 Классическая", "music_genre_classical"), ("💿 R&B/Соул", "music_genre_rnb"),
        ("🌴 Регги", "music_genre_reggae"), ("🤠 Кантри", "music_genre_country"),
        ("🤘 Метал", "music_genre_metal"), ("🪕 Фолк", "music_genre_folk"),
        ("💃 Латины", "music_genre_latin"), ("🎭 Панк", "music_genre_punk"),
        ("🕺 Фанк", "music_genre_funk"), ("🎙️ Шансон", "music_genre_shanson"),
        ("✏️ Свой вариант", "music_genre_custom")
    ]
    buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in genres]
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.add(buttons[i])

    await MusicStates.waiting_for_music_style.set()
    await bot.send_message(
        user_id,
        "🎶 **СОЗДАЕМ ИНСТРУМЕНТАЛЬНУЮ МУЗЫКУ**\n\n🎹 Музыка БЕЗ слов - только мелодия и ритм!\n\nВыбери жанр для твоей композиции 👇",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ========================================
# CALLBACK: ПОКАЗАТЬ ДОКУМЕНТЫ (ИЗ МЕНЮ БАЛАНСА)
# ========================================

@dp.callback_query_handler(lambda c: c.data == "show_documents")
async def show_documents_callback(callback_query: types.CallbackQuery):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📜 Политика конфиденциальности", callback_data="show_privacy"),
        InlineKeyboardButton("📄 Публичная оферта", callback_data="show_offer")
    )
    
    await callback_query.message.edit_text(
        "📄 **Правовые документы:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'show_privacy')
async def show_privacy(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "📜 Политика конфиденциальности: https://albi-music.ru/documents/privacy.html")

@dp.callback_query_handler(lambda c: c.data == 'show_offer')
async def show_offer(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "📄 Публичная оферта: https://albi-music.ru/documents/offer.html")


@dp.callback_query_handler(lambda c: c.data == 'admin_stats')
async def process_admin_stats(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    if not is_admin(callback_query.from_user.id):
        return
    stats = get_admin_stats()

    # Воронка: процент дошедших до меню среди НОВЫХ за 24 часа
    started = stats.get("started_24h", 0)
    menu = stats.get("menu_24h", 0)
    menu_pct = round(menu * 100.0 / started, 1) if started > 0 else 0

    # Разбивка оплат за 24 часа по тарифам
    tariffs_24h = stats.get("tariffs_24h", {}) or {}
    if tariffs_24h:
        amount_to_tokens = {
            50: 1,
            99: 5,
            250: 10,
            500: 25,
            1000: 60,
            2000: 140,
        }
        tariff_lines = []
        for amount, cnt in sorted(tariffs_24h.items()):
            tokens = amount_to_tokens.get(amount)
            if tokens:
                tariff_lines.append(f"• {cnt}×{amount}₽ ({tokens} ток.)")
            else:
                tariff_lines.append(f"• {cnt}×{amount}₽")
        tariffs_24h_text = "\n".join(tariff_lines)
    else:
        tariffs_24h_text = "• нет оплат за 24ч"

    # Разбивка по платформам
    platform_total = stats.get("platform_total", {}) or {}
    platform_7d = stats.get("platform_7d", {}) or {}
    vk_total_cnt, vk_total_sum = platform_total.get('vk', (0, 0))
    tg_total_cnt, tg_total_sum = platform_total.get('tg', (0, 0))
    vk_7d_cnt, vk_7d_sum = platform_7d.get('vk', (0, 0))
    tg_7d_cnt, tg_7d_sum = platform_7d.get('tg', (0, 0))

    text = f"""📊 *Статистика бота:*

👥 Всего пользователей: {stats.get("total_users", 0)} (+{stats.get("new_today", 0)})
📈 Новых за 7 дней: {stats.get("new_7days", 0)}
📅 Новых за 30 дней: {stats.get("new_30days", 0)}

📊 *Воронка (НОВЫЕ за 24ч):*
▶️ Нажали /start (новые): {started}
🖱 Дошли до меню (из новых): {menu} ({menu_pct}%)

🎵 Генераций за 24ч: {stats.get("generations_24h", 0)} шт
✅ Общий успех (все время): {stats.get("success_rate", 0)}%

💳 *Оплаты:*
⏰ За 24ч: {stats.get("count_24h", 0)} платежей · {stats.get("sum_24h", 0)}₽
    🔍 По тарифам (24ч):
{tariffs_24h_text}
📆 За 7 дней: {stats.get("count_7days", 0)} платежей · {stats.get("sum_7days", 0)}₽
    📱 VK: {vk_7d_cnt} платежей · {vk_7d_sum}₽
    ✈️ TG: {tg_7d_cnt} платежей · {tg_7d_sum}₽
📊 Всего: {stats.get("count_total", 0)} платежей · {stats.get("sum_total", 0)}₽
    📱 VK: {vk_total_cnt} платежей · {vk_total_sum}₽
    ✈️ TG: {tg_total_cnt} платежей · {tg_total_sum}₽

👥 Приглашенных сегодня: {stats.get("invited_today", 0)}"""

    refresh_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"))
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown", reply_markup=refresh_btn)

# ─── Рассылка (Админ) ────────────────────────────────────────

@dp.callback_query_handler(lambda c: c.data == 'admin_broadcast', state='*')
async def albi_broadcast_start(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if not is_admin(callback_query.from_user.id):
        return
    await bot.send_message(
        callback_query.from_user.id,
        "📨 *Рассылка AlBi Music*\n\n"
        "Отправь текст сообщения для рассылки.\n"
        "Поддерживается *жирный*, _курсив_, `код`, ссылки.\n\n"
        "Отправь /cancel для отмены.",
        parse_mode="Markdown",
    )
    await BroadcastStates.waiting_text.set()


@dp.message_handler(commands=["cancel"], state=BroadcastStates)
async def albi_broadcast_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Рассылка отменена.")


@dp.message_handler(state=BroadcastStates.waiting_text)
async def albi_broadcast_got_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(text=message.text)

    from postgres_db import fetch_query
    rows = await fetch_query("SELECT COUNT(*) as cnt FROM users")
    total = rows[0]["cnt"] if rows else 0

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Отправить всем", callback_data="albi_bc_confirm"),
        InlineKeyboardButton("❌ Отмена",          callback_data="albi_bc_cancel"),
    )

    # Пробуем с Markdown, если не получается — показываем как обычный текст
    try:
        await message.answer(
            f"👀 *Предпросмотр (Markdown):*\n\n{message.text}\n\n"
            f"─────────────────\n"
            f"Будет отправлено: *{total} пользователям*\n\n"
            f"Подтвердить?",
            parse_mode="Markdown",
            reply_markup=kb,
        )
    except Exception:
        # Markdown сломан (например, _ в @username) — показываем как plain text
        await message.answer(
            f"👀 Предпросмотр (plain text — Markdown отключён из-за спецсимволов):\n\n"
            f"{message.text}\n\n"
            f"─────────────────\n"
            f"⚠️ В тексте есть символы _ * ` которые ломают Markdown. "
            f"Рассылка будет отправлена как обычный текст (без форматирования).\n\n"
            f"Будет отправлено: {total} пользователям\n\n"
            f"Подтвердить?",
            reply_markup=kb,
        )

    await BroadcastStates.waiting_confirm.set()


@dp.callback_query_handler(lambda c: c.data == 'albi_bc_cancel', state=BroadcastStates.waiting_confirm)
async def albi_broadcast_cancel_cb(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "❌ Рассылка отменена.")


@dp.callback_query_handler(lambda c: c.data == 'albi_bc_confirm', state=BroadcastStates.waiting_confirm)
async def albi_broadcast_confirm_cb(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if not is_admin(callback_query.from_user.id):
        return

    data = await state.get_data()
    text = data["text"]
    await state.finish()

    from postgres_db import fetch_query
    import asyncio as _asyncio
    rows = await fetch_query("SELECT user_id FROM users")
    total = len(rows)

    start_msg = await bot.send_message(
        callback_query.from_user.id,
        f"🚀 *Рассылка запущена!*\n\n"
        f"📨 Начинаю отправку *{total}* пользователям...\n"
        f"⏳ Буду сообщать о прогрессе каждые 25 человек.",
        parse_mode="Markdown",
    )

    sent = 0
    errors = 0
    PROGRESS_STEP = 100  # сообщать прогресс каждые N пользователей

    for i, row in enumerate(rows, start=1):
        uid = row["user_id"]
        try:
            # Пробуем с Markdown, если не парсится — отправляем plain text
            try:
                await bot.send_message(uid, text, parse_mode="Markdown")
            except Exception as md_err:
                if "CantParseEntities" in str(type(md_err).__name__) or "parse" in str(md_err).lower():
                    await bot.send_message(uid, text)  # plain text fallback
                else:
                    raise
            sent += 1
        except Exception:
            errors += 1
        await _asyncio.sleep(0.3)  # ~3 сообщения/сек — безопасно, без риска бана

        # Прогресс каждые 25 пользователей
        if i % PROGRESS_STEP == 0 and i < total:
            pct = int(i / total * 100)
            try:
                await bot.send_message(
                    callback_query.from_user.id,
                    f"📊 *Прогресс рассылки:* {pct}%\n"
                    f"✅ Отправлено: {sent} / {total}\n"
                    f"❌ Ошибок: {errors}",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    await bot.send_message(
        callback_query.from_user.id,
        f"✅ *Рассылка завершена!*\n\n"
        f"📤 Успешно отправлено: *{sent}* из *{total}*\n"
        f"❌ Не доставлено (заблокировали бот): *{errors}*\n\n"
        f"📋 Рассылка полностью завершена.",
        parse_mode="Markdown",
    )


@dp.callback_query_handler(lambda c: c.data == 'check_suno_api')
async def check_suno_api_status(callback_query: types.CallbackQuery):
    """Проверка РЕАЛЬНЫХ путей Suno API (из celery_tasks.py)"""
    await bot.answer_callback_query(callback_query.id)
    
    if not is_admin(callback_query.from_user.id):
        return
    
    status_msg = await bot.send_message(callback_query.from_user.id, 
        "🔍 *Проверяю рабочие endpoints Suno API...*", 
        parse_mode="Markdown")
    
    try:
        import requests
        import time
        import sys
        sys.path.insert(0, '.')
        from config import SUNO_API_KEY, SUNO_API_URL
        
        # РЕАЛЬНЫЕ пути из celery_tasks.py
        tests = [
            {
                "url": f"{SUNO_API_URL}/api/v1/generate",
                "method": "POST",
                "name": "Создание задачи (/api/v1/generate)",
                "data": {"prompt": "test", "instrumental": True}  # Минимальный тестовый запрос
            },
            {
                "url": f"{SUNO_API_URL}/api/v1/generate/record-info",
                "method": "GET", 
                "name": "Проверка статуса (/api/v1/generate/record-info)",
                "params": {"taskId": "test_task_123"}  # Тестовый ID
            },
        ]
        
        headers = {
            "Authorization": f"Bearer {SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        results = []
        suno_working = False
        
        for test in tests:
            try:
                start = time.time()
                
                if test['method'] == 'POST':
                    response = requests.post(
                        test['url'], 
                        json=test.get('data', {}), 
                        headers=headers, 
                        timeout=15
                    )
                else:  # GET
                    response = requests.get(
                        test['url'], 
                        params=test.get('params', {}),
                        headers=headers, 
                        timeout=15
                    )
                
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    results.append(f"✅ {test['name']}: 200 OK ({elapsed:.1f} сек)")
                    suno_working = True
                elif response.status_code == 401:
                    results.append(f"🔒 {test['name']}: 401 (Проблема с API ключом)")
                elif response.status_code == 404:
                    results.append(f"❌ {test['name']}: 404 (Путь не найден)")
                elif response.status_code == 429:
                    results.append(f"⚠️ {test['name']}: 429 (Слишком много запросов)")
                elif response.status_code == 503:
                    results.append(f"🚧 {test['name']}: 503 (Сервис перегружен)")
                else:
                    results.append(f"⚠️ {test['name']}: HTTP {response.status_code}")
                
                # Добавляем детали ответа для диагностики
                if response.status_code != 200:
                    try:
                        error_detail = response.json()
                        results.append(f"   Ответ: {str(error_detail)[:150]}")
                    except:
                        results.append(f"   Текст: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                results.append(f"⏰ {test['name']}: Таймаут")
            except requests.exceptions.ConnectionError:
                results.append(f"🔌 {test['name']}: Ошибка соединения")
            except Exception as e:
                results.append(f"❌ {test['name']}: {str(e)[:50]}")
        
        # Формируем отчет
        from datetime import datetime
        report_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        report = f"*Проверка Suno API*\n⏰ {report_time}\n\n"
        report += "\n".join(results)
        
        # Добавляем итоговый вердикт
        report += "\n\n📢 *Вердикт:* "
        if suno_working:
            report += "✅ API отвечает корректно"
        else:
            report += "❌ Есть проблемы с подключением"
        
        await status_msg.edit_text(report, parse_mode="Markdown")
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ *Ошибка проверки:*\n`{str(e)[:150]}`", 
            parse_mode="Markdown"
        )

@dp.message_handler(state=SongStates.waiting_for_lyrics)
async def process_song_lyrics(message: types.Message, state: FSMContext):
    if len(message.text) > MAX_SONG_LENGTH:
        await message.answer(f"❌ Слишком длинный текст. Максимум {MAX_SONG_LENGTH} символов.")
        return
    await state.update_data(lyrics=message.text, generation_type='song')
    await SongStates.waiting_for_mode.set()
    await message.answer("🎵 *Выберите режим генерации:*\n\n🎯 *Точный режим* - Suno использует ТОЛЬКО ваш текст\n🎨 *Творческий режим* - Suno может дополнять и улучшать текст\n\n**Какой режим предпочитаете?**", reply_markup=get_generation_mode_keyboard(), parse_mode="Markdown")

@dp.message_handler(state=SongStates.waiting_for_song_style)
async def process_song_style(message: types.Message, state: FSMContext):
    if len(message.text) > MAX_STYLE_LENGTH:
        await message.answer(f"❌ Слишком длинное описание. Максимум {MAX_STYLE_LENGTH} символов.")
        return
    await state.update_data(style=message.text, generation_type='song')
    await SongStates.waiting_for_lyrics.set()
    await message.answer(f"🎤 *Теперь введите текст вашей песни:*\n\n📝 Максимум {MAX_SONG_LENGTH} символов\n\n**Пример:**\nЯ иду по улице,\nСолнце светит ярко...", parse_mode="Markdown")

# СТАРЫЙ ОБРАБОТЧИК УДАЛЕН - теперь используется process_custom_music_genre (строка ~2003)
# Этот обработчик конфликтовал с новым флоу создания музыки и вызывал проблемы с балансом

# Функция отправки поста в канал
async def send_to_channel(audio_url, comment, user_info):
    try:
        # Берём первую ссылку (поддержка JSON массива)
        first_audio_url = audio_url
        if audio_url and audio_url.startswith('['):
            try:
                import json
                audio_urls = json.loads(audio_url)
                if audio_urls and len(audio_urls) > 0:
                    first_audio_url = audio_urls[0]
            except:
                pass  # Если ошибка парсинга, оставляем как есть

        audio_url_to_use = first_audio_url
        # Экранируем специальные символы Markdown в комментарии
        from aiogram.utils.markdown import escape_md
        safe_comment = escape_md(comment)
        safe_user_info = escape_md(user_info)

        # Форматируем сообщение для канала БЕЗ ссылки скачивания
        caption = f"🎵 *Новая AI-песня!*\n\n{safe_comment}\n\n" + \
                 f"👤 Автор: {safe_user_info}\n\n" + \
                 f"💡 _Чтобы скачать песню, нажмите правой кнопкой мыши на плеер и далее «Сохранить как…»_\n\n" + \
                 f"\#AIмузыка \#AlBiMusic"

        # Отправляем аудио в канал (ДЕМО-версия 45 сек)
        message = await bot.send_audio(
            chat_id=config.CHANNEL_USERNAME,
            audio=audio_url,
            caption=caption,
            parse_mode="Markdown"
        )
        
        logging.info(f"✅ Пост подготовлен для канала: {comment[:50]}...")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка отправки в канал: {e}")
        return False
def add_channel_post(user_id, audio_url, comment, message_id=None):
    """Сохраняет публикацию в PostgreSQL"""
    try:
        from db_utils import execute_query_sync
        
        result = execute_query_sync(
            "INSERT INTO channel_posts (user_id, audio_url, comment, message_id, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (user_id, audio_url, comment, message_id)
        )
        
        logging.info(f"✅ Публикация сохранена для пользователя {user_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения публикации {user_id}: {e}")
        return False

@dp.message_handler(state=ChannelPostStates.waiting_for_comment)
async def process_channel_comment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    audio_url = user_data.get('audio_url')
    comment = message.text
    user_id = message.from_user.id
    
    # Получаем информацию о пользователе
    user = await bot.get_chat(user_id)
    user_info = f"@{user.username}" if user.username else f"{user.first_name}"
    
    # Отправляем в канал (пока только логируем)
    success = await send_to_channel(audio_url, comment, user_info)
    
    if success:
        # Сохраняем в БД
        add_channel_post(user_id, audio_url, comment)
        await message.answer(
            "✅ Ваша песня опубликована в канале!\n\n" +
            f"📝 Ваш комментарий: {comment}\n\n" +
            "📢 Посмотреть в канале: @ALBImusic_chart\n\n" +
            "Спасибо за участие в нашем музыкальном сообществе! 🎶"
        )
    else:
        await message.answer(
            "❌ *Не удалось опубликовать песню.*\n\n" +
            "Попробуйте позже или обратитесь в поддержку.", 
            parse_mode="Markdown"
        )
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('play_'), state='*')
async def process_play_track(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    task_id = callback_query.data.replace('play_', '')
    user_id = callback_query.from_user.id

    import json

    # Берём полные URL и статус разблокировки из demo_tracks
    demo_check = execute_query_sync(
        "SELECT full_url_1, full_url_2, is_unlocked FROM demo_tracks WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )

    if demo_check and demo_check[0]:
        full_url_1, full_url_2, is_unlocked = demo_check[0]
        urls = [u for u in [full_url_1, full_url_2] if u]
    else:
        # Fallback: берём из generations.audio_url, убираем ALREADY_SENT_ префикс
        result = execute_query_sync(
            "SELECT audio_url FROM generations WHERE task_id = %s AND user_id = %s",
            (task_id, user_id)
        )
        if not result:
            await bot.send_message(user_id, "❌ Трек не найден")
            return
        audio_url_raw = result[0][0] or ""
        for prefix in ("ALREADY_SENT_", "ALREADY_NOTIFIED_"):
            if audio_url_raw.startswith(prefix):
                audio_url_raw = audio_url_raw[len(prefix):]
                break
        try:
            urls = json.loads(audio_url_raw) if audio_url_raw.startswith('[') else [audio_url_raw]
        except Exception:
            urls = [audio_url_raw]
        is_unlocked = False

    # Отправляем аудио
    sent = 0
    for idx, url in enumerate(urls[:2], 1):
        if not url or url.startswith('ALREADY_'):
            continue
        try:
            caption = f"🎼 Версия {idx}" if is_unlocked else f"🎧 Демо {idx} (45 сек)"
            await bot.send_audio(user_id, url, caption=caption, title=f"AI Music v{idx}", performer="ALBI Music")
            sent += 1
        except Exception as e:
            logging.error(f"Ошибка отправки аудио play_ {task_id}: {e}")

    if sent == 0:
        await bot.send_message(user_id, "⚠️ Не удалось загрузить аудио — ссылка устарела. Попробуйте сгенерировать заново.")
        return

    # Кнопки и текст зависят от статуса разблокировки
    markup = InlineKeyboardMarkup(row_width=2)

    if is_unlocked:
        info_text = (
            "✅ **Полные версии разблокированы!**\n\n"
            "**Что ещё можно сделать:**\n"
            "🎤 **Минусовка** — версия без вокала для исполнения\n"
            "🎸 **Кавер** — перепой в другом стиле/жанре\n"
            "🎵 **В WAV** — конвертируй в WAV формат для профи\n"
            "📢 **Отправить в канал** — опубликуй в нашем официальном канале\n"
            "🔗 **Поделиться** — отправь другу прямо сейчас"
        )
    else:
        # Определяем: новичок (без платёжной истории) → 50₽, иначе → 1 токен
        paid_check = execute_query_sync(
            "SELECT COUNT(*) FROM payments WHERE user_id = %s AND status = 'succeeded'",
            (user_id,)
        )
        user_has_paid = paid_check and paid_check[0][0] > 0

        if not user_has_paid:
            # Проверяем новичковое окно — если активно, цена 29₽, иначе 50₽
            _is_novice_play, _hours_play, _gens_play = get_novice_status(user_id)
            if _is_novice_play:
                _unlock_price_label = f"29₽ ⏰ (ещё {int(_hours_play)}ч!)"
                _unlock_cb = f"pay_unlock_29_{task_id}"
                _price_note = f"\n\n⏰ *Цена 29₽ действует только {int(_hours_play)}ч — потом стандартная цена*"
            else:
                _unlock_price_label = "50₽"
                _unlock_cb = f"pay_unlock_50_{task_id}"
                _price_note = ""
            info_text = (
                "🎧 **Это 45-секундное демо**\n\n"
                f"🔓 Разблокируй полную версию за **{_unlock_price_label}** — без ограничений по времени!\n\n"
                "**Что получишь после оплаты:**\n"
                "🎤 **Минусовка** — версия без вокала\n"
                "🎸 **Кавер** — перепой в другом стиле\n"
                "🎵 **В WAV** — профессиональный формат\n"
                "📢 **В канал** — поделись с другими!\n"
                f"🔗 **Скачать** — сохрани трек навсегда{_price_note}"
            )
            markup.add(
                InlineKeyboardButton(f"🔓 Получить ПОЛНУЮ версию — {_unlock_price_label}", callback_data=_unlock_cb)
            )
        else:
            # Пользователь уже платил — предлагаем 1 токен
            info_text = (
                "🎧 **Это 45-секундное демо**\n\n"
                "🔓 Разблокируй полные версии за **1 токен** — без ограничений по времени!\n\n"
                "**Что ещё можно сделать:**\n"
                "🎤 **Минусовка** — версия без вокала для исполнения\n"
                "🎸 **Кавер** — перепой в другом стиле/жанре\n"
                "🎵 **В WAV** — конвертируй в WAV формат для профи\n"
                "📢 **Отправить в канал** — опубликуй в нашем официальном канале\n"
                "🔗 **Поделиться** — отправь другу прямо сейчас"
            )
            markup.add(
                InlineKeyboardButton("🔓 Разблокировать полные версии (1 токен)", callback_data=f"unlock_{task_id}")
            )

    if is_unlocked:
        markup.add(
            InlineKeyboardButton("🎤 Минусовка (1 токен)", callback_data=f"karaoke_{task_id}"),
            InlineKeyboardButton("🎸 Кавер (2 токена)", callback_data=f"cover_{task_id}")
        )
        markup.add(
            InlineKeyboardButton("🎵 В WAV (1 токен)", callback_data=f"wav_{task_id}"),
            InlineKeyboardButton("📢 Отправить в канал", callback_data=f"post_{task_id}")
        )
        markup.add(
            InlineKeyboardButton("🔗 Отправить другу", switch_inline_query=task_id),
            InlineKeyboardButton("🔔 Перейти в канал", url="https://t.me/ALBImusic_Chart")
        )
    else:
        markup.add(
            InlineKeyboardButton("🔔 Перейти в канал", url="https://t.me/ALBImusic_Chart")
        )

    await bot.send_message(user_id, info_text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith('repeat_'))
async def process_repeat_track(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id, "🔄 Создаем новую версию...")
    task_id = callback_query.data.replace('repeat_', '')
    user_id = callback_query.from_user.id

    # Получаем параметры оригинальной генерации
    result = execute_query_sync(
        "SELECT prompt, custom_mode FROM generations WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )

    if not result:
        await bot.send_message(user_id, "❌ Не удалось повторить генерацию")
        return

    prompt, custom_mode = result[0]

    # Парсим prompt для извлечения style и lyrics
    # Формат: "Стиль: {style}. Текст: {lyrics}" или "Стиль: {style}"
    style = ""
    lyrics = ""

    if prompt.startswith("Стиль: "):
        parts = prompt.split(". Текст: ", 1)
        style = parts[0].replace("Стиль: ", "")
        if len(parts) > 1:
            lyrics = parts[1]

    # Если нет текста - это инструментальная музыка
    is_song = bool(lyrics)

    # Проверяем баланс (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance <= 0:
            await send_no_tokens_message(user_id, "Недостаточно токенов! Нажмите 💰 Баланс для пополнения.")
            return
        # Списываем генерацию
        execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))

    # Создаем новую задачу Celery с правильным порядком параметров
    new_task_id = str(uuid.uuid4())

    if is_song:
        # Для песни: (user_id, lyrics, style, custom_mode)
        task = generate_song_task.apply_async(
            args=(user_id, lyrics, style, custom_mode),
            kwargs={'task_id': new_task_id},
            task_id=new_task_id
        )
    else:
        # Для инструментальной музыки
        task = generate_music_task.apply_async(
            args=(user_id, style),
            kwargs={'task_id': new_task_id},
            task_id=new_task_id
        )

    # Сохраняем в БД
    add_generation(user_id, new_task_id, prompt, "", False, custom_mode)

    # GIF
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        with open(gif_path, 'rb') as gif:
            await bot.send_animation(user_id, gif, caption="🎵 **Генерация началась!**\n\n🤖 Создаю новую версию...\n⏰ 3-5 минут", parse_mode="Markdown")
    except:
        await bot.send_message(user_id, "⏳ Генерация началась! Результат пришлю через 3-5 минут")

# ========== ОБРАБОТЧИКИ ПРОВЕРКИ ТЕКСТА ==========

@dp.callback_query_handler(lambda c: c.data == 'lyrics_approve', state=CreateSongStates.reviewing_lyrics)
async def process_lyrics_approve(callback_query: types.CallbackQuery, state: FSMContext):
    """Пользователь одобрил текст - переходим к выбору жанра"""
    await bot.answer_callback_query(callback_query.id, "✅ Отлично!")
    await bot.edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=None
    )

    # Переходим к выбору жанра
    await show_genre_selection(callback_query.message, state)

@dp.callback_query_handler(lambda c: c.data == 'lyrics_regenerate', state=CreateSongStates.reviewing_lyrics)
async def process_lyrics_regenerate(callback_query: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет перегенерировать текст"""
    user_id = callback_query.from_user.id

    # Проверяем баланс (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance <= 0:
            await bot.answer_callback_query(callback_query.id)
            await send_no_tokens_message(user_id, "Недостаточно токенов для перегенерации текста. Нажмите 💰 Баланс для пополнения.")
            return

    await bot.answer_callback_query(callback_query.id, "🔄 Генерирую новый текст...")
    await bot.edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=None
    )

    # Получаем оригинальное описание
    state_data = await state.get_data()
    song_idea = state_data.get('song_idea', '')

    if not song_idea:
        await bot.send_message(user_id, "❌ Не удалось найти описание. Попробуйте заново.")
        await state.finish()
        return

    # Списываем генерацию (кроме админа)
    if not is_admin(user_id):
        execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))

    await bot.send_message(user_id, "⏳ Генерирую новый текст... Это займет около 30-60 секунд...")

    # Генерируем новый текст
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        generated_lyrics = await loop.run_in_executor(None, generate_suno_lyrics_sync, song_idea, user_id)

        if not generated_lyrics:
            await bot.send_message(
                user_id,
                "❌ **К сожалению, AI не смог подобрать текст для этой идеи.**\n\n"
                "💡 **Что можно сделать:**\n"
                "• Попробуй переформулировать идею по-другому\n"
                "• Или нажми «У меня свой текст» и напиши текст сам\n\n"
                "👇 Жми «Создать песню» чтобы попробовать снова!",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
            await state.finish()
            return

        await state.update_data(lyrics=generated_lyrics)

        # Показываем новый текст
        await show_lyrics_for_review(callback_query.message, state, generated_lyrics, is_regeneration=True)

    except Exception as e:
        logging.error(f"Ошибка перегенерации текста: {e}")
        await bot.send_message(
            user_id,
            "❌ Произошла ошибка при генерации текста. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        await state.finish()

# ========== ОБРАБОТЧИКИ ВЫБОРА ЖАНРА ==========

@dp.callback_query_handler(lambda c: c.data.startswith('genre_'), state=CreateSongStates.waiting_genre)
async def process_genre_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    genre_code = callback_query.data.replace('genre_', '')

    # Если выбран "Свой вариант" - запрашиваем описание
    if genre_code == 'custom':
        await CreateSongStates.waiting_custom_genre.set()
        await bot.send_message(
            user_id,
            "✏️ **Опиши свой вариант**\n\nКак должна звучать песня? Опиши стиль, инструменты, настроение...",
            parse_mode="Markdown"
        )
        return

    # Маппинг кодов жанров в названия (унифицировано со всеми местами)
    genre_names = {
        'pop': 'Поп',
        'rock': 'Рок',
        'jazz': 'Джаз',
        'blues': 'Блюз',
        'hiphop': 'Хип-хоп',
        'electronic': 'Электронная музыка',
        'classical': 'Классическая музыка',
        'rnb': 'R&B/Соул',
        'reggae': 'Регги',
        'country': 'Кантри',
        'metal': 'Метал',
        'folk': 'Фолк',
        'latin': 'Латиноамериканская музыка',
        'punk': 'Панк-рок',
        'funk': 'Фанк',
        'shanson': 'Шансон'
    }

    genre = genre_names.get(genre_code, genre_code)

    # Получаем данные из состояния
    state_data = await state.get_data()
    lyrics = state_data.get('lyrics', '')

    # Запускаем генерацию
    await start_song_generation(user_id, lyrics, genre, state, callback_query.message)

@dp.message_handler(state=CreateSongStates.waiting_custom_genre)
async def process_custom_genre(message: types.Message, state: FSMContext):
    """Получили описание своего варианта жанра (после нажатия кнопки 'Свой вариант')"""
    custom_genre = message.text
    state_data = await state.get_data()
    lyrics = state_data.get('lyrics', '')
    await start_song_generation(message.from_user.id, lyrics, custom_genre, state, message)

@dp.message_handler(state=CreateSongStates.waiting_genre)
async def process_genre_as_text(message: types.Message, state: FSMContext):
    """Пользователь написал жанр текстом вместо нажатия кнопки — обрабатываем как свой вариант"""
    custom_genre = message.text
    state_data = await state.get_data()
    lyrics = state_data.get('lyrics', '')
    await start_song_generation(message.from_user.id, lyrics, custom_genre, state, message)

# ========== ОБРАБОТЧИКИ ИНСТРУМЕНТАЛЬНОЙ МУЗЫКИ ==========

@dp.callback_query_handler(lambda c: c.data.startswith('music_genre_'), state=MusicStates.waiting_for_music_style)
async def process_music_genre_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора жанра для инструментальной музыки"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    genre_code = callback_query.data.replace('music_genre_', '')

    # Если выбран "Свой вариант" - запрашиваем описание
    if genre_code == 'custom':
        # Устанавливаем состояние для ожидания текста от пользователя
        await MusicStates.waiting_for_music_style.set()
        await bot.send_message(
            user_id,
            "✏️ **Опиши свой стиль музыки**\n\n"
            "Например: энергичная электронная музыка с тяжелыми басами, спокойная акустическая гитара...",
            parse_mode="Markdown"
        )
        return

    # Маппинг кодов жанров в названия
    genre_names = {
        'pop': 'Поп',
        'rock': 'Рок',
        'jazz': 'Джаз',
        'blues': 'Блюз',
        'hiphop': 'Хип-хоп',
        'electronic': 'Электронная музыка',
        'classical': 'Классическая музыка',
        'rnb': 'R&B/Соул',
        'reggae': 'Регги',
        'country': 'Кантри',
        'metal': 'Метал',
        'folk': 'Фолк',
        'latin': 'Латиноамериканская музыка',
        'punk': 'Панк-рок',
        'funk': 'Фанк',
        'shanson': 'Шансон'
    }

    genre = genre_names.get(genre_code, genre_code)

    # Запускаем генерацию инструментальной музыки
    await start_music_generation(user_id, genre, state, callback_query.message)

@dp.message_handler(state=MusicStates.waiting_for_music_style, content_types=['text'])
async def process_custom_music_genre(message: types.Message, state: FSMContext):
    """Получили описание своего варианта жанра для инструментальной музыки"""
    custom_genre = message.text

    # Запускаем генерацию
    await start_music_generation(message.from_user.id, custom_genre, state, message)

async def start_music_generation(user_id, genre, state: FSMContext, message):
    """Запускает генерацию инструментальной музыки с выбранным жанром"""

    # Проверяем баланс (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance <= 0:
            await send_no_tokens_message(user_id, "Бесплатные генерации закончились! Нажмите 💰 Баланс для пополнения.", state)
            return
        # Списываем генерацию
        execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))

    # Создаем задачу генерации
    import uuid
    task_id = str(uuid.uuid4())

    # Для инструментальной музыки: БЕЗ текста, только жанр
    # Запускаем Celery задачу (lyrics пустой, custom_mode=False, is_song=False)
    try:
        task = generate_song_task.apply_async(
            args=(user_id, "", genre, False),  # custom_mode=False для инструментальной
            kwargs={'task_id': task_id, 'is_song': False},  # is_song=False для инструментальной музыки
            task_id=task_id
        )
    except Exception as _celery_err:
        logging.error(f"❌ Ошибка запуска Celery задачи (музыка) для user {user_id}: {_celery_err}")
        # Возвращаем токен — задача не запустилась
        if not is_admin(user_id):
            execute_query_sync("UPDATE users SET balance = balance + 1 WHERE user_id = %s", (user_id,))
        await state.finish()
        await bot.send_message(
            user_id,
            "❌ Произошла техническая ошибка при запуске генерации.\n\n"
            "✅ Ваш токен возвращён. Попробуйте ещё раз через несколько минут.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return

    # Завершаем FSM
    await state.finish()

    # Отправляем GIF с анимацией
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        with open(gif_path, 'rb') as gif:
            await bot.send_animation(
                user_id,
                gif,
                caption="🎶 **Генерация инструментальной музыки началась!**\n\n🤖 Создаю композицию...\n⏰ 3-5 минут",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except:
        await bot.send_message(
            user_id,
            "⏳ Генерация началась! Результат пришлю через 3-5 минут",
            reply_markup=get_main_menu_keyboard(user_id)
        )

async def start_song_generation(user_id, lyrics, genre, state: FSMContext, message):
    """Запускает генерацию песни с выбранным жанром"""

    # Проверяем баланс (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance <= 0:
            await send_no_tokens_message(user_id, "Бесплатные генерации закончились! Нажмите 💰 Баланс для пополнения.", state)
            return
        # Списываем генерацию
        execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))

    # Создаем задачу генерации
    import uuid
    task_id = str(uuid.uuid4())

    # Определяем нужен ли custom mode (для текстов > 500 символов)
    custom_mode = len(lyrics) > 500

    # Запускаем Celery задачу (Celery сам создаст запись в БД)
    try:
        task = generate_song_task.apply_async(
            args=(user_id, lyrics, genre, custom_mode),
            kwargs={'task_id': task_id},
            task_id=task_id
        )
    except Exception as _celery_err:
        logging.error(f"❌ Ошибка запуска Celery задачи (песня) для user {user_id}: {_celery_err}")
        # Возвращаем токен — задача не запустилась
        if not is_admin(user_id):
            execute_query_sync("UPDATE users SET balance = balance + 1 WHERE user_id = %s", (user_id,))
        await state.finish()
        await bot.send_message(
            user_id,
            "❌ Произошла техническая ошибка при запуске генерации.\n\n"
            "✅ Ваш токен возвращён. Попробуйте ещё раз через несколько минут.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return

    # Завершаем FSM
    await state.finish()

    # Отправляем GIF с анимацией
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        with open(gif_path, 'rb') as gif:
            await bot.send_animation(
                user_id,
                gif,
                caption="🎵 **Генерация началась!**\n\n🤖 Создаю твою песню...\n⏰ 3-5 минут",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except:
        await bot.send_message(
            user_id,
            "⏳ Генерация началась! Результат пришлю через 3-5 минут",
            reply_markup=get_main_menu_keyboard(user_id)
        )

# Обработчик share_ больше не нужен - кнопка теперь использует switch_inline_query напрямую

# Обработчик загрузки аудио для минусовка
@dp.message_handler(content_types=['audio', 'voice', 'document'], state=KaraokeStates.waiting_for_audio_upload)
async def process_karaoke_audio_upload(message: types.Message, state: FSMContext):
    """Обработка загруженного аудио для минусовка"""
    user_id = message.from_user.id

    # Проверка баланса
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 1:
            await send_no_tokens_message(user_id, "Недостаточно токенов! Стоимость минусовки: 1 токен", state)
            return
        update_user_balance(user_id, -1)

    # Получаем файл
    file_id = None
    if message.audio:
        file_id = message.audio.file_id
    elif message.voice:
        file_id = message.voice.file_id
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        await message.answer("❌ Не удалось получить аудио файл. Попробуйте еще раз.")
        return

    # Скачиваем файл
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Скачиваем во временную директорию
        import tempfile
        import subprocess
        temp_dir = tempfile.mkdtemp()
        local_path = f"{temp_dir}/{file_id}.mp3"

        await bot.download_file(file_path, local_path)

        # Проверяем длительность через ffprobe
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', local_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            duration = float(result.stdout.strip())

            if duration > 300:  # Больше 5 минут
                await message.answer(
                    f"❌ Файл слишком длинный: {int(duration)}сек\n\n"
                    "⚠️ Максимум 5 минут (300 секунд)\n"
                    "Обрежьте файл и попробуйте снова."
                )
                os.remove(local_path)
                await state.finish()
                return
        except Exception as e:
            logging.warning(f"⚠️ Не удалось проверить длительность: {e}")

        await message.answer(
            "✅ Файл получен!\n\n"
            "📤 Загружаю на сервер...",
            parse_mode="Markdown"
        )

        # Загружаем файл на сервер и получаем URL
        try:
            file_url = await upload_file_to_server(local_path, f"{file_id}.mp3")
        except Exception as e:
            await message.answer("❌ Ошибка загрузки файла на сервер. Попробуйте позже.")
            os.remove(local_path)
            await state.finish()
            return

        await message.answer(
            "🎤 Создаю минусовка-версию...\n"
            "⏰ Подождите 1-2 минуты",
            parse_mode="Markdown"
        )

        # Создаем Celery задачу
        new_task_id = str(uuid.uuid4())
        celery_task = generate_karaoke_from_upload_task.apply_async(
            args=[user_id, file_url],
            kwargs={'task_id': new_task_id},
            queue='generation'
        )

        logging.info(f"🎤 Минусовка задача создана: {new_task_id} для пользователя {user_id}, URL: {file_url}")

        # Удаляем локальный файл
        os.remove(local_path)
        await state.finish()

    except Exception as e:
        logging.error(f"❌ Ошибка загрузки аудио: {e}")
        await message.answer("❌ Ошибка обработки файла. Попробуйте другой файл.")
        await state.finish()

# Обработчик загрузки аудио для кавера
@dp.message_handler(content_types=['audio', 'voice', 'document'], state=CoverStates.waiting_for_audio_upload)
async def process_cover_audio_upload(message: types.Message, state: FSMContext):
    """Обработка загруженного аудио для кавера"""
    user_id = message.from_user.id

    # Проверка баланса
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 2:
            await send_no_tokens_message(user_id, "Недостаточно токенов! Стоимость кавера: 2 токена", state)
            return
        update_user_balance(user_id, -2)

    # Получаем файл
    file_id = None
    if message.audio:
        file_id = message.audio.file_id
    elif message.voice:
        file_id = message.voice.file_id
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        await message.answer("❌ Не удалось получить аудио файл. Попробуйте еще раз.")
        return

    # Скачиваем файл
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Скачиваем во временную директорию
        import tempfile
        import subprocess
        temp_dir = tempfile.mkdtemp()
        local_path = f"{temp_dir}/{file_id}.mp3"

        await bot.download_file(file_path, local_path)

        # Проверяем длительность через ffprobe
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', local_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            duration = float(result.stdout.strip())

            if duration > 300:  # Больше 5 минут
                await message.answer(
                    f"❌ Файл слишком длинный: {int(duration)}сек\n\n"
                    "⚠️ Максимум 5 минут (300 секунд)\n"
                    "Обрежьте файл и попробуйте снова."
                )
                os.remove(local_path)
                await state.finish()
                return
        except Exception as e:
            logging.warning(f"⚠️ Не удалось проверить длительность: {e}")

        # Сохраняем путь и показываем выбор жанра
        await state.update_data(audio_file_path=local_path, is_uploaded=True)

        # Показываем выбор жанра
        markup = InlineKeyboardMarkup(row_width=2)
        genres = [
            ("🎤 Поп", "upload_cover_genre_pop"),
            ("🎸 Рок", "upload_cover_genre_rock"),
            ("🎷 Джаз", "upload_cover_genre_jazz"),
            ("🎺 Блюз", "upload_cover_genre_blues"),
            ("🎧 Хип-хоп", "upload_cover_genre_hiphop"),
            ("🎹 Электронная", "upload_cover_genre_electronic"),
            ("🎻 Классическая", "upload_cover_genre_classical"),
            ("🎤 R&B/Соул", "upload_cover_genre_rnb"),
            ("🥁 Регги", "upload_cover_genre_reggae"),
            ("🎸 Кантри", "upload_cover_genre_country"),
            ("🎸 Метал", "upload_cover_genre_metal"),
            ("🪕 Фолк", "upload_cover_genre_folk"),
            ("🎺 Латины", "upload_cover_genre_latin"),
            ("🎸 Панк", "upload_cover_genre_punk"),
            ("🎷 Фанк", "upload_cover_genre_funk"),
            ("🎤 Шансон", "upload_cover_genre_chanson"),
        ]

        for genre_name, callback_data in genres:
            markup.add(InlineKeyboardButton(genre_name, callback_data=callback_data))

        markup.add(InlineKeyboardButton("✍️ Свой вариант", callback_data="upload_cover_genre_custom"))

        await message.answer(
            "✅ Файл получен!\n\n"
            "🎸 *Выбери в каком жанре создать кавер:*",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"❌ Ошибка загрузки аудио: {e}")
        await message.answer("❌ Ошибка обработки файла. Попробуйте другой файл.")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('karaoke_') and not c.data.endswith(('_v1', '_v2')), state='*')
async def ask_karaoke_version(callback_query: types.CallbackQuery, state: FSMContext):
    """Спрашиваем какую версию использовать для минусовки"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace('karaoke_', '')

    # Показываем выбор версии
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎵 Версия 1", callback_data=f"karaoke_{task_id}_v1"),
        InlineKeyboardButton("🎵 Версия 2", callback_data=f"karaoke_{task_id}_v2")
    )

    await bot.send_message(
        user_id,
        "🎤 *МИНУСОВКА*\n\n"
        "Выбери версию для создания минусовки:\n\n"
        "🎵 Версия 1 - первый трек\n"
        "🎵 Версия 2 - второй трек",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('karaoke_') and c.data.endswith(('_v1', '_v2')), state='*')
async def process_karaoke(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик создания минусовка-версии (удаление вокала)"""
    # Сбрасываем любое текущее состояние
    current_state = await state.get_state()
    if current_state:
        await state.finish()

    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Извлекаем task_id и версию
    data = callback_query.data.replace('karaoke_', '')
    if data.endswith('_v1'):
        task_id = data.replace('_v1', '')
        version = 0  # Первая версия (индекс 0)
    else:
        task_id = data.replace('_v2', '')
        version = 1  # Вторая версия (индекс 1)

    # Проверка баланса (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 1:
            await send_no_tokens_message(user_id, "Недостаточно токенов для создания минусовки! Стоимость: 1 токен")
            return

        # Списываем 1 генерацию
        update_user_balance(user_id, -1)

    # Создаем новую задачу Celery для минусовка
    new_task_id = str(uuid.uuid4())

    from celery_tasks import generate_karaoke_task
    celery_task = generate_karaoke_task.apply_async(
        args=[user_id, task_id, version],  # Добавили version
        kwargs={'task_id': new_task_id},
        queue='generation'
    )

    version_name = "Версия 1" if version == 0 else "Версия 2"
    await bot.send_message(
        user_id,
        f"🎤 *Создаю минусовка-версию ({version_name})!*\n\n"
        "⏰ Удаление вокала займет 3-5 минут.\n\n"
        "Вы получите инструментальную версию вашей песни без вокала 🎸",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )

    logger.info(f"✅ Минусовка задача запущена для user {user_id}: {new_task_id}")

@dp.callback_query_handler(lambda c: c.data.startswith('wav_') and not c.data.endswith(('_v1', '_v2')), state='*')
async def ask_wav_version(callback_query: types.CallbackQuery, state: FSMContext):
    """Спрашиваем какую версию конвертировать в WAV"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace('wav_', '')

    # Показываем выбор версии
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎵 Версия 1", callback_data=f"wav_{task_id}_v1"),
        InlineKeyboardButton("🎵 Версия 2", callback_data=f"wav_{task_id}_v2")
    )

    await bot.send_message(
        user_id,
        "🎵 *КОНВЕРТАЦИЯ В WAV*\n\n"
        "Выбери версию для конвертации в WAV:\n\n"
        "🎵 Версия 1 - первый трек\n"
        "🎵 Версия 2 - второй трек",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('wav_') and c.data.endswith(('_v1', '_v2')), state='*')
async def process_wav_conversion(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик конвертации в WAV формат"""
    # Сбрасываем любое текущее состояние
    current_state = await state.get_state()
    if current_state:
        await state.finish()

    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Извлекаем task_id и версию
    data = callback_query.data.replace('wav_', '')
    if data.endswith('_v1'):
        task_id = data.replace('_v1', '')
        version = 0  # Первая версия (индекс 0)
    else:
        task_id = data.replace('_v2', '')
        version = 1  # Вторая версия (индекс 1)

    # Проверка баланса (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 1:
            await send_no_tokens_message(user_id, "Недостаточно токенов для конвертации в WAV! Стоимость: 1 токен")
            return

        # Списываем 1 генерацию
        update_user_balance(user_id, -1)

    # Создаем новую задачу Celery для конвертации в WAV
    new_task_id = str(uuid.uuid4())

    from celery_tasks import generate_wav_task
    celery_task = generate_wav_task.apply_async(
        args=[user_id, task_id, version],  # Добавили version
        kwargs={'task_id': new_task_id},
        queue='generation'
    )

    version_name = "Версия 1" if version == 0 else "Версия 2"
    await bot.send_message(
        user_id,
        f"🎵 *Конвертирую в WAV формат ({version_name})!*\n\n"
        "⏰ Конвертация займет 2-3 минуты.\n\n"
        "Вы получите профессиональный WAV файл с максимальным качеством 🎧",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )

    logger.info(f"✅ WAV конвертация запущена для user {user_id}: {new_task_id}")

@dp.callback_query_handler(lambda c: c.data.startswith('unlock_'), state='*')
async def process_unlock_full_versions(callback_query: types.CallbackQuery, state: FSMContext):
    """Разблокировка полных версий трека — списывает 1 токен"""
    current_state = await state.get_state()
    if current_state:
        await state.finish()

    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace('unlock_', '')

    # Проверяем статус разблокировки
    result = execute_query_sync(
        "SELECT full_url_1, full_url_2, is_unlocked FROM demo_tracks WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )

    if not result:
        await callback_query.answer("❌ Трек не найден", show_alert=True)
        return

    full_url_1, full_url_2, is_unlocked = result[0]

    if is_unlocked:
        await callback_query.answer("✅ Этот трек уже разблокирован!", show_alert=True)
        return

    # Проверка баланса (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 1:
            await send_no_tokens_message(user_id, "Недостаточно токенов для разблокировки! Стоимость: 1 токен")
            return

        # Списываем 1 токен
        update_user_balance(user_id, -1)

    # Разблокируем в БД
    execute_query_sync(
        "UPDATE demo_tracks SET is_unlocked = TRUE, unlocked_at = NOW() WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )

    await bot.send_message(
        user_id,
        "🎉 *Полные версии разблокированы!*\n\nОтправляю треки...",
        parse_mode="Markdown"
    )

    # Отправляем оба трека
    for idx, url in enumerate([full_url_1, full_url_2], start=1):
        if url:
            try:
                await bot.send_audio(
                    chat_id=user_id,
                    audio=url,
                    caption=f"🎼 *Версия {idx}* (полная)",
                    title=f"AI Music - Full Version {idx}",
                    performer="ALBI Music",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"❌ Ошибка отправки версии {idx}: {e}")

    channel_markup = InlineKeyboardMarkup()
    channel_markup.add(InlineKeyboardButton("🔔 Поделиться и смотреть примеры", url="https://t.me/ALBImusic_chart"))
    await bot.send_message(
        user_id,
        "✅ *Готово!* Наслаждайтесь полными версиями! 🎵\n\n"
        "🎉 Поделись своей песней в нашем канале — вдохнови других!\n"
        "Там же свежие примеры, промпты и обучение 👇",
        reply_markup=channel_markup,
        parse_mode="Markdown"
    )
    logger.info(f"✅ Разблокированы полные версии: user {user_id}, task {task_id}")


@dp.callback_query_handler(lambda c: c.data.startswith('pay_unlock_29_'), state='*')
async def process_pay_unlock_first_gen_29(callback_query: types.CallbackQuery, state: FSMContext):
    """Создаёт платёж ЮKassa 29₽ для разблокировки первой (демо) генерации (новичковое окно 24ч)"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace('pay_unlock_29_', '')

    # Проверяем — вдруг уже разблокирован (двойной клик)
    demo_check = execute_query_sync(
        "SELECT is_unlocked FROM demo_tracks WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )
    if demo_check and demo_check[0] and demo_check[0][0]:
        await callback_query.answer("✅ Этот трек уже разблокирован!", show_alert=True)
        return

    # Проверяем: окно ещё активно?
    is_novice_active_ul, hours_left_ul, _ = get_novice_status(user_id)
    unlock_price = 29 if is_novice_active_ul else 50
    timer_text = f"\n\n⏰ Специальная цена {unlock_price}₽ ещё {int(hours_left_ul)} ч! Потом — от 99₽." if is_novice_active_ul else ""

    payment = await create_yookassa_payment(
        user_id,
        unlock_price,
        f"Разблокировка полной версии трека ALBI Music ({unlock_price}₽ — новичковое окно)",
        {"payment_type": "unlock_first", "task_id": task_id}
    )

    if payment and payment.get('confirmation', {}).get('confirmation_url'):
        payment_url = payment['confirmation']['confirmation_url']
        payment_id = payment['id']

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"💳 Оплатить {unlock_price}₽ — получить полную версию", url=payment_url))
        markup.add(InlineKeyboardButton("🎧 Послушать демо ещё раз", callback_data=f"play_{task_id}"))

        await bot.send_message(
            user_id,
            f"🔓 *Разблокировка полной версии трека*\n\n"
            f"💰 Стоимость: *{unlock_price}₽* — разовый платёж{timer_text}\n\n"
            "✅ После оплаты ты получишь:\n"
            "• Оба трека без ограничения по времени\n"
            "• Кнопки «Послушать» и «Скачать»\n"
            "• Минусовку, Кавер, WAV и всё остальное\n\n"
            "👇 Нажми кнопку ниже для оплаты:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        logging.info(f"💳 Создан платёж unlock_first {unlock_price}₽: user={user_id}, task={task_id}, payment_id={payment_id}")
    else:
        await bot.send_message(
            user_id,
            "❌ Не удалось создать платёж. Попробуйте ещё раз или обратитесь в поддержку.",
        )
        logging.error(f"❌ Ошибка создания платежа unlock_first: user={user_id}, task={task_id}")


@dp.callback_query_handler(lambda c: c.data.startswith('pay_unlock_50_'), state='*')
async def process_pay_unlock_first_gen(callback_query: types.CallbackQuery, state: FSMContext):
    """Создаёт платёж ЮKassa 50₽ для разблокировки первой (демо) генерации"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace('pay_unlock_50_', '')

    # Проверяем — вдруг уже разблокирован (двойной клик)
    demo_check = execute_query_sync(
        "SELECT is_unlocked FROM demo_tracks WHERE task_id = %s AND user_id = %s",
        (task_id, user_id)
    )
    if demo_check and demo_check[0] and demo_check[0][0]:
        await callback_query.answer("✅ Этот трек уже разблокирован!", show_alert=True)
        return

    # Создаём платёж ЮKassa на 50₽
    payment = await create_yookassa_payment(
        user_id,
        50,
        "Разблокировка полной версии трека ALBI Music",
        {"payment_type": "unlock_first", "task_id": task_id}
    )

    if payment and payment.get('confirmation', {}).get('confirmation_url'):
        payment_url = payment['confirmation']['confirmation_url']
        payment_id = payment['id']

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Оплатить 50₽ — получить полную версию", url=payment_url))
        markup.add(InlineKeyboardButton("🎧 Послушать демо ещё раз", callback_data=f"play_{task_id}"))

        await bot.send_message(
            user_id,
            "🔓 *Разблокировка полной версии трека*\n\n"
            "💰 Стоимость: *50₽* — разовый платёж\n\n"
            "✅ После оплаты ты получишь:\n"
            "• Оба трека без ограничения по времени\n"
            "• Кнопки «Послушать» и «Скачать»\n"
            "• Минусовку, Кавер, WAV и всё остальное\n\n"
            "👇 Нажми кнопку ниже для оплаты:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        logging.info(f"💳 Создан платёж unlock_first: user={user_id}, task={task_id}, payment_id={payment_id}")
    else:
        await bot.send_message(
            user_id,
            "❌ Не удалось создать платёж. Попробуйте ещё раз или обратитесь в поддержку.",
        )
        logging.error(f"❌ Ошибка создания платежа unlock_first: user={user_id}, task={task_id}")


# ============================================================
# ОБРАБОТЧИК: новичковая генерация (1 токен за 29₽, 24 часового окно, лимит 10 шт)
# ============================================================
@dp.callback_query_handler(lambda c: c.data == 'pay_29_novice', state='*')
async def process_pay_29_novice(callback_query: types.CallbackQuery, state: FSMContext):
    """Создаёт платёж YooKassa 29₽ → 1 токен (новичковое 24-часовое окно, до 10 покупок)"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Проверяем, что окно ещё активно и лимит не исчерпан
    is_novice_active_np, hours_left_np, gens_bought_np = get_novice_status(user_id)
    if not is_novice_active_np:
        await bot.send_message(
            user_id,
            "⏰ *Специальная цена 29₽ закончилась.*\n\n"
            "Твоё 24-часовое новичковое окно истекло.\n"
            "Теперь доступны стандартные пакеты 👇",
            reply_markup=get_balance_keyboard(user_id),
            parse_mode="Markdown"
        )
        return

    if gens_bought_np >= 10:
        await bot.send_message(
            user_id,
            "✅ Ты уже воспользовался максимальным количеством новичковых генераций (10 из 10)!\n\n"
            "Теперь доступны стандартные пакеты 👇",
            reply_markup=get_balance_keyboard(user_id),
            parse_mode="Markdown"
        )
        return

    remaining_np = 10 - gens_bought_np
    logging.info(f"🎁 Новичковая генерация 29₽: user={user_id}, куплено={gens_bought_np}, осталось={remaining_np}")

    payment = await create_yookassa_payment(
        user_id,
        29,
        "1 генерация — Подарок новичку ALBI Music",
        {"payment_type": "novice_gen"}
    )
    if payment and payment.get('confirmation', {}).get('confirmation_url'):
        payment_url = payment['confirmation']['confirmation_url']
        payment_id = payment['id']
        add_payment(user_id, 29, 'pending', payment_id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("💳 Оплатить 29₽ — получить 1 генерацию (2 трека)", url=payment_url))
        await bot.send_message(
            user_id,
            f"🎁 *Подарок новичку — 1 генерация за 29₽*\n\n"
            f"⏰ Ещё {int(hours_left_np)} ч действует специальная цена.\n"
            f"Осталось: {remaining_np} из 10 новичковых генераций.\n\n"
            "✅ После оплаты баланс пополнится автоматически!\n"
            "1 генерация = 2 трека (2 варианта вашей песни)\n\n"
            "👇 Нажми кнопку для оплаты:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        logging.info(f"✅ Создан novice_gen платёж для {user_id}: {payment_id}")
    else:
        await bot.send_message(user_id, "❌ Ошибка при создании платежа. Попробуйте позже.")
        logging.error(f"❌ Ошибка pay_29_novice для {user_id}")


# ОБРАБОТЧИК: разовое предложение новичку (5 токенов за 99₽)
# ============================================================
@dp.callback_query_handler(lambda c: c.data == 'newcomer_offer_pay', state='*')
async def process_newcomer_offer_pay(callback_query: types.CallbackQuery, state: FSMContext):
    """Создаёт платёж YooKassa 99₽ → 5 токенов (разовое предложение новичку)"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    logger.info(f"🎁 Новичковый оффер TG: создаём платёж 99₽ для пользователя {user_id}")

    payment = await create_yookassa_payment(
        user_id,
        99,
        "5 токенов — Стартовый пакет ALBI Music",
        {"package_type": "newcomer_offer"}
    )
    if payment and payment.get('confirmation', {}).get('confirmation_url'):
        payment_url = payment['confirmation']['confirmation_url']
        payment_id = payment['id']
        add_payment(user_id, 99, 'pending', payment_id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("💳 Оплатить 99₽ — получить 5 токенов", url=payment_url))
        await bot.send_message(
            user_id,
            "🎁 *Стартовый пакет — 5 токенов за 99₽*\n\n"
            "✅ После оплаты баланс пополнится автоматически в течение 1-2 минут!\n\n"
            "👇 Нажми кнопку для оплаты:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        logger.info(f"✅ Создан newcomer_offer платёж для {user_id}: {payment_id}")
    else:
        await bot.send_message(user_id, "❌ Ошибка при создании платежа. Попробуйте позже.")
        logger.error(f"❌ Ошибка newcomer_offer_pay для {user_id}")


@dp.callback_query_handler(lambda c: c.data.startswith('cover_') and not c.data.endswith(('_v1', '_v2')) and not c.data.startswith('cover_genre_'), state='*')
async def ask_cover_version(callback_query: types.CallbackQuery, state: FSMContext):
    """Спрашиваем какую версию использовать для кавера"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    task_id = callback_query.data.replace('cover_', '')

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎵 Версия 1", callback_data=f"cover_{task_id}_v1"),
        InlineKeyboardButton("🎵 Версия 2", callback_data=f"cover_{task_id}_v2")
    )

    await bot.send_message(
        user_id,
        "🎸 *КАВЕР В НОВОМ ЖАНРЕ*\n\n"
        "Выбери версию для создания кавера:\n\n"
        "🎵 Версия 1 - первый трек\n"
        "🎵 Версия 2 - второй трек",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('cover_') and c.data.endswith(('_v1', '_v2')) and not c.data.startswith('cover_genre_'), state='*')
async def process_cover(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик создания кавера - показ выбора жанра"""
    # Сбрасываем любое текущее состояние (кроме CoverStates)
    current_state = await state.get_state()
    if current_state and not current_state.startswith('CoverStates'):
        await state.finish()

    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Извлекаем task_id и версию
    data = callback_query.data.replace('cover_', '')
    if data.endswith('_v1'):
        task_id = data.replace('_v1', '')
        version = 0  # Первая версия (индекс 0)
    else:
        task_id = data.replace('_v2', '')
        version = 1  # Вторая версия (индекс 1)

    # Проверка баланса (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance < 2:
            await send_no_tokens_message(user_id, "Недостаточно токенов для создания кавера! Стоимость: 2 токена")
            return

    # Сохраняем task_id и version в FSM для последующего использования
    await state.update_data(cover_original_task_id=task_id, cover_version=version)

    # Показываем выбор жанра (те же 16 жанров)
    markup = InlineKeyboardMarkup(row_width=2)
    genres = [
        ("🎤 Поп", "cover_genre_pop"),
        ("🎸 Рок", "cover_genre_rock"),
        ("🎷 Джаз", "cover_genre_jazz"),
        ("🎺 Блюз", "cover_genre_blues"),
        ("🎧 Хип-хоп", "cover_genre_hiphop"),
        ("🎹 Электронная", "cover_genre_electronic"),
        ("🎻 Классическая", "cover_genre_classical"),
        ("🎤 R&B/Соул", "cover_genre_rnb"),
        ("🥁 Регги", "cover_genre_reggae"),
        ("🎸 Кантри", "cover_genre_country"),
        ("🎸 Метал", "cover_genre_metal"),
        ("🪕 Фолк", "cover_genre_folk"),
        ("🎺 Латины", "cover_genre_latin"),
        ("🎸 Панк", "cover_genre_punk"),
        ("🎷 Фанк", "cover_genre_funk"),
        ("🎤 Шансон", "cover_genre_chanson"),
    ]

    for genre_name, callback_data in genres:
        markup.add(InlineKeyboardButton(genre_name, callback_data=callback_data))

    markup.add(InlineKeyboardButton("✍️ Свой вариант", callback_data="cover_genre_custom"))

    await CoverStates.waiting_for_genre.set()
    await bot.send_message(
        user_id,
        "🎸 *Выбери в каком жанре создать кавер:*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# Обработчик выбора жанра для загруженного кавера
@dp.callback_query_handler(lambda c: c.data.startswith('upload_cover_genre_'), state=CoverStates.waiting_for_audio_upload)
async def process_upload_cover_genre(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора жанра для кавера из загруженного файла"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    genre_map = {
        "upload_cover_genre_pop": "Поп",
        "upload_cover_genre_rock": "Рок",
        "upload_cover_genre_jazz": "Джаз",
        "upload_cover_genre_blues": "Блюз",
        "upload_cover_genre_hiphop": "Хип-хоп",
        "upload_cover_genre_electronic": "Электронная музыка",
        "upload_cover_genre_classical": "Классическая музыка",
        "upload_cover_genre_rnb": "R&B/Соул",
        "upload_cover_genre_reggae": "Регги",
        "upload_cover_genre_country": "Кантри",
        "upload_cover_genre_metal": "Метал",
        "upload_cover_genre_folk": "Фолк",
        "upload_cover_genre_latin": "Латиноамериканская музыка",
        "upload_cover_genre_punk": "Панк-рок",
        "upload_cover_genre_funk": "Фанк",
        "upload_cover_genre_chanson": "Шансон",
    }

    if callback_query.data == "upload_cover_genre_custom":
        await bot.send_message(
            user_id,
            "✍️ *Опиши свой жанр:*\n\n"
            "Например: синти-поп 80-х, акустический инди, тяжелый метал",
            parse_mode="Markdown"
        )
        # TODO: добавить состояние для ожидания custom genre
        await state.finish()
        return

    selected_genre = genre_map.get(callback_query.data, "Поп")

    # Получаем путь к файлу из FSM
    data = await state.get_data()
    audio_file_path = data.get('audio_file_path')

    if not audio_file_path or not os.path.exists(audio_file_path):
        await bot.send_message(user_id, "❌ Ошибка: файл не найден. Попробуйте снова.")
        await state.finish()
        return

    # Загружаем файл на сервер и получаем URL
    try:
        file_url = await upload_file_to_server(audio_file_path, f"cover_{user_id}.mp3")
    except Exception as e:
        await bot.send_message(user_id, "❌ Ошибка загрузки файла на сервер. Попробуйте позже.")
        os.remove(audio_file_path)
        await state.finish()
        return

    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        with open(gif_path, 'rb') as gif:
            await bot.send_animation(
                user_id, gif,
                caption=f"🎸 *Создаю кавер в стиле {selected_genre}...*\n\n⏰ Подождите 3-5 минут!",
                parse_mode="Markdown"
            )
    except Exception:
        await bot.send_message(
            user_id,
            f"🎸 *Создаю кавер в стиле {selected_genre}...*\n\n⏰ Подождите 3-5 минут!",
            parse_mode="Markdown"
        )

    # Создаем Celery задачу
    new_task_id = str(uuid.uuid4())
    celery_task = generate_cover_from_upload_task.apply_async(
        args=[user_id, file_url, selected_genre],
        kwargs={'task_id': new_task_id},
        queue='generation'
    )

    logging.info(f"🎸 Кавер задача создана: {new_task_id} для пользователя {user_id}, жанр: {selected_genre}, URL: {file_url}")

    # Удаляем локальный файл
    os.remove(audio_file_path)
    await state.finish()

# Обработчик выбора жанра для кавера
@dp.callback_query_handler(lambda c: c.data.startswith('cover_genre_'), state=CoverStates.waiting_for_genre)
async def process_cover_genre(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора жанра для кавера"""
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    genre_map = {
        "cover_genre_pop": "Поп",
        "cover_genre_rock": "Рок",
        "cover_genre_jazz": "Джаз",
        "cover_genre_blues": "Блюз",
        "cover_genre_hiphop": "Хип-хоп",
        "cover_genre_electronic": "Электронная музыка",
        "cover_genre_classical": "Классическая музыка",
        "cover_genre_rnb": "R&B/Соул",
        "cover_genre_reggae": "Регги",
        "cover_genre_country": "Кантри",
        "cover_genre_metal": "Метал",
        "cover_genre_folk": "Фолк",
        "cover_genre_latin": "Латиноамериканская музыка",
        "cover_genre_punk": "Панк-рок",
        "cover_genre_funk": "Фанк",
        "cover_genre_chanson": "Шансон",
    }

    if callback_query.data == "cover_genre_custom":
        await CoverStates.waiting_custom_genre.set()
        await bot.send_message(
            user_id,
            "✍️ *Опиши свой жанр:*\n\n"
            "Например: синти-поп 80-х, акустический инди, тяжелый метал",
            parse_mode="Markdown"
        )
        return

    # Получаем выбранный жанр
    selected_genre = genre_map.get(callback_query.data, "Поп")

    # Получаем оригинальный task_id и version из FSM
    data = await state.get_data()
    original_task_id = data.get('cover_original_task_id')
    version = data.get('cover_version', 0)  # По умолчанию версия 0

    if not original_task_id:
        await bot.send_message(user_id, "❌ Ошибка: не найден оригинальный трек")
        await state.finish()
        return

    # Списываем 2 генерации (кроме админа)
    if not is_admin(user_id):
        update_user_balance(user_id, -2)

    # Создаем задачу Celery
    new_task_id = str(uuid.uuid4())
    celery_task = generate_cover_task.apply_async(
        args=[user_id, original_task_id, selected_genre, version],  # Добавили version
        kwargs={'task_id': new_task_id},
        queue='generation'
    )

    version_name = "Версия 1" if version == 0 else "Версия 2"
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        with open(gif_path, 'rb') as gif:
            await bot.send_animation(
                user_id, gif,
                caption=f"🎸 *Создаю кавер в стиле {selected_genre} ({version_name})...*\n\nНовая версия будет готова через 3-5 минут!",
                parse_mode="Markdown"
            )
    except Exception:
        await bot.send_message(
            user_id,
            f"🎸 *Создаю кавер в стиле {selected_genre} ({version_name})...*\n\nНовая версия будет готова через 3-5 минут!",
            parse_mode="Markdown"
        )

    await state.finish()
    logging.info(f"🎸 Кавер задача создана: {new_task_id} для пользователя {user_id}, жанр: {selected_genre}, версия: {version}")

# Обработчик своего жанра для кавера
@dp.message_handler(state=CoverStates.waiting_custom_genre)
async def process_cover_custom_genre(message: types.Message, state: FSMContext):
    """Обработчик описания своего жанра для кавера"""
    user_id = message.from_user.id
    custom_genre = message.text.strip()

    if len(custom_genre) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return

    # Получаем оригинальный task_id и version из FSM
    data = await state.get_data()
    original_task_id = data.get('cover_original_task_id')
    version = data.get('cover_version', 0)  # По умолчанию версия 0

    if not original_task_id:
        await message.answer("❌ Ошибка: не найден оригинальный трек")
        await state.finish()
        return

    # Списываем 2 генерации (кроме админа)
    if not is_admin(user_id):
        update_user_balance(user_id, -2)

    # Создаем задачу Celery
    new_task_id = str(uuid.uuid4())
    celery_task = generate_cover_task.apply_async(
        args=[user_id, original_task_id, custom_genre, version],  # Добавили version
        kwargs={'task_id': new_task_id},
        queue='generation'
    )

    version_name = "Версия 1" if version == 0 else "Версия 2"
    gif_path = '/root/albimusic-bot/robot_music.gif'
    try:
        with open(gif_path, 'rb') as gif:
            await bot.send_animation(
                user_id, gif,
                caption=f"🎸 *Создаю кавер в стиле '{custom_genre}' ({version_name})...*\n\nНовая версия будет готова через 3-5 минут!",
                parse_mode="Markdown"
            )
    except Exception:
        await message.answer(
            f"🎸 *Создаю кавер в стиле '{custom_genre}' ({version_name})...*\n\nНовая версия будет готова через 3-5 минут!",
            parse_mode="Markdown"
        )

    await state.finish()
    logging.info(f"🎸 Кавер задача создана: {new_task_id} для пользователя {user_id}, жанр: {custom_genre}, версия: {version}")

@dp.callback_query_handler(lambda c: c.data.startswith('post_'), state='*')
async def process_post_to_channel(callback_query: types.CallbackQuery, state: FSMContext):
    # Сбрасываем любое текущее состояние (кроме ChannelPostStates)
    current_state = await state.get_state()
    if current_state and not current_state.startswith('ChannelPostStates'):
        await state.finish()

    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id

    # Извлекаем task_id из callback_data
    task_id = callback_query.data.replace('post_', '')

    # Получаем ДЕМО-версию из базы данных (demo_tracks)
    try:
        # Сначала проверяем разблокирован ли трек
        demo_result = execute_query_sync(
            "SELECT full_url_1, is_unlocked FROM demo_tracks WHERE task_id = %s AND user_id = %s",
            (task_id, user_id)
        )

        if demo_result and demo_result[0]:
            demo_url = demo_result[0][0]
            is_unlocked = demo_result[0][1]

            if not is_unlocked:
                # Если не разблокирован, отправляем сообщение
                await bot.send_message(
                    user_id,
                    "❌ Для публикации в канале сначала нужно разблокировать полные версии (1 токен).\n\n"
                    "После разблокировки вы сможете размещать треки в нашем канале!",
                    parse_mode="Markdown"
                )
                return

            audio_url = demo_url  # Используем полную версию если разблокировано
        else:
            # Если нет в demo_tracks, ищем в generations
            result = execute_query_sync(
                "SELECT audio_url FROM generations WHERE task_id = %s AND user_id = %s",
                (task_id, user_id)
            )

            if not result or not result[0][0]:
                await bot.send_message(user_id, "❌ Не удалось найти аудио для этой генерации.")
                return

            audio_url_raw = result[0][0]

            # Если это JSON массив (2 варианта) — спрашиваем какой публиковать
            import json
            if isinstance(audio_url_raw, str) and audio_url_raw.startswith('['):
                try:
                    urls = json.loads(audio_url_raw)
                    if isinstance(urls, list) and len(urls) >= 2:
                        # Есть 2 варианта — даём выбор
                        await state.update_data(
                            audio_url_1=urls[0], audio_url_2=urls[1], task_id=task_id
                        )
                        await ChannelPostStates.waiting_for_version.set()
                        kb = InlineKeyboardMarkup(row_width=2)
                        kb.add(
                            InlineKeyboardButton("🎵 Вариант 1", callback_data="channel_version_1"),
                            InlineKeyboardButton("🎵 Вариант 2", callback_data="channel_version_2"),
                        )
                        kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_channel_post"))
                        await bot.send_message(
                            user_id,
                            "🎵 *Выберите вариант для публикации в канале:*",
                            reply_markup=kb,
                            parse_mode="Markdown"
                        )
                        return
                    elif isinstance(urls, list) and len(urls) > 0:
                        audio_url = urls[0]
                    else:
                        audio_url = audio_url_raw
                except Exception:
                    audio_url = audio_url_raw
            else:
                audio_url = audio_url_raw

        # Сохраняем audio_url в состоянии
        await state.update_data(audio_url=audio_url, task_id=task_id)
        await ChannelPostStates.waiting_for_comment.set()

        # Добавляем кнопку "Отмена"
        cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_channel_post")]
        ])

        await bot.send_message(
            user_id,
            "📝 *Добавьте комментарий к вашей публикации:*\n\n" +
            "Напишите текст, который будет отображаться вместе с вашей песней в канале. " +
            "Например, опишите настроение, вдохновение или историю создания.\n\n" +
            "Или нажмите Отмена, если передумали.",
            reply_markup=cancel_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"❌ Ошибка при получении audio_url для публикации: {e}")
        await bot.send_message(user_id, "❌ Произошла ошибка. Попробуйте снова.")

@dp.callback_query_handler(
    lambda c: c.data in ('channel_version_1', 'channel_version_2'),
    state=ChannelPostStates.waiting_for_version
)
async def process_channel_version(callback_query: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал вариант (1 или 2) для публикации в канале"""
    await bot.answer_callback_query(callback_query.id)
    data = await state.get_data()
    if callback_query.data == 'channel_version_1':
        audio_url = data.get('audio_url_1')
    else:
        audio_url = data.get('audio_url_2')
    await state.update_data(audio_url=audio_url)
    await ChannelPostStates.waiting_for_comment.set()
    cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_channel_post")]
    ])
    await bot.send_message(
        callback_query.from_user.id,
        "📝 *Добавьте комментарий к вашей публикации:*\n\n"
        "Напишите текст, который будет отображаться вместе с вашей песней в канале. "
        "Например, опишите настроение, вдохновение или историю создания.\n\n"
        "Или нажмите Отмена, если передумали.",
        reply_markup=cancel_markup,
        parse_mode="Markdown"
    )


@dp.callback_query_handler(lambda c: c.data == 'cancel_channel_post', state='*')
async def cancel_channel_post(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена публикации в канале"""
    await bot.answer_callback_query(callback_query.id, "❌ Отменено")
    await state.finish()

    await bot.send_message(
        callback_query.from_user.id,
        "❌ Публикация в канале отменена.",
        reply_markup=get_main_menu_keyboard(callback_query.from_user.id)
    )

# Запуск приложения
def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("BOT_PORT", 8000)), log_level="info")

def run_bot():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    """Действия при запуске бота"""
    logging.info("✅ Бот запущен! Запускаем мониторинг...")
    # Запускаем мониторинг завершенных задач
    import asyncio


# Запуск бота



@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mode_'), state='*')
async def process_generation_mode(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора режима генерации (старый флоу)"""
    await callback_query.answer()

    user_id = callback_query.from_user.id  # int, не str

    # Проверяем баланс (кроме админа)
    if not is_admin(user_id):
        balance = get_balance_number(user_id)
        if balance <= 0:
            await send_no_tokens_message(user_id, "Недостаточно токенов на балансе. Нажмите 💰 Баланс для пополнения.", state)
            return
        execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))

    mode = callback_query.data.replace('mode_', '')

    # Получаем данные из состояния
    state_data = await state.get_data()

    lyrics = state_data.get("lyrics", "").strip()
    style = state_data.get("style", "")

    if not lyrics:
        await callback_query.message.answer("❌ Ошибка: текст песни не найден. Начни заново.")
        await state.finish()
        return

    # Запускаем генерацию через правильный механизм с task_id
    new_task_id = str(uuid.uuid4())
    custom_mode = (mode == "creative") or len(lyrics) > 500

    task = generate_song_task.apply_async(
        args=(user_id, lyrics, style, custom_mode),
        kwargs={'task_id': new_task_id},
        task_id=new_task_id
    )

    await callback_query.message.answer(
        "⏳ Генерация вашей композиции началась. Это займет 2-5 минут, подождите пожалуйста! Результат я пришлю сюда в чат"
    )

    await state.finish()

# ─── Поддержка (пользователи) ────────────────────────────────

@dp.message_handler(lambda message: message.text == "📞 Поддержка", state='*')
async def handle_support_button(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "📞 *Поддержка*\n\n"
        "Напиши своё сообщение — мы ответим в ближайшее время.\n\n"
        "Отправь /cancel для отмены.",
        parse_mode="Markdown"
    )
    await SupportStates.waiting_message.set()


@dp.message_handler(commands=["cancel"], state=SupportStates)
async def support_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Отменено.", reply_markup=get_main_menu_keyboard(message.from_user.id))


@dp.message_handler(state=SupportStates.waiting_message)
async def handle_support_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    text = message.text
    try:
        execute_query_sync(
            "INSERT INTO support_messages (user_id, username, first_name, message) VALUES (%s, %s, %s, %s)",
            (user_id, username, first_name, text)
        )
    except Exception as e:
        logging.error(f"Ошибка сохранения сообщения поддержки: {e}")
    await state.finish()
    await message.answer(
        "✅ *Сообщение отправлено!*\n\nМы ответим вам в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )


# ─── Поддержка (админ) ───────────────────────────────────────

@dp.callback_query_handler(lambda c: c.data == 'admin_support', state='*')
async def process_admin_support(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if not is_admin(callback_query.from_user.id):
        return
    await _show_support_messages(callback_query.from_user.id, offset=0)


def _escape_md(text: str) -> str:
    """Экранирует спецсимволы Markdown в пользовательском тексте"""
    if not text:
        return text
    for char in ['_', '*', '`', '[']:
        text = text.replace(char, f'\\{char}')
    return text


async def _show_support_messages(admin_id, offset=0):
    try:
        messages = execute_query_sync(
            """SELECT id, user_id, username, first_name, message, replied, created_at
               FROM support_messages
               WHERE replied = FALSE
               ORDER BY created_at DESC
               LIMIT 5 OFFSET %s""",
            (offset,)
        )
    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка: {e}")
        return

    if not messages:
        await bot.send_message(admin_id, "📭 Нет сообщений поддержки.")
        return

    for row in messages:
        msg_id, user_id, username, first_name, text, replied, created_at = row
        status_icon = "✅" if replied else "🔴"
        user_str = f"@{username}" if username else f"id{user_id}"
        date_str = created_at.strftime("%d.%m %H:%M") if created_at else ""
        # Экранируем пользовательские данные, чтобы Markdown не ломался
        safe_first_name = _escape_md(str(first_name or "Пользователь"))
        safe_user_str = _escape_md(user_str)
        safe_text = _escape_md(str(text or ""))
        header = f"{status_icon} *{safe_first_name}* ({safe_user_str}) — {date_str}"
        display_text = f"{header}\n\n{safe_text}"

        kb = InlineKeyboardMarkup(row_width=2)
        if not replied:
            kb.add(InlineKeyboardButton(
                "💬 Ответить",
                callback_data=f"sup_reply_{msg_id}_{user_id}"
            ))
        kb.add(InlineKeyboardButton("🗑 Закрыть", callback_data=f"sup_close_{msg_id}"))
        await bot.send_message(admin_id, display_text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query_handler(lambda c: c.data.startswith('sup_reply_'), state='*')
async def start_support_reply(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if not is_admin(callback_query.from_user.id):
        return
    parts = callback_query.data.split('_')
    msg_id = parts[2]
    user_id = parts[3]
    await state.update_data(support_msg_id=msg_id, support_user_id=user_id)
    await SupportReplyStates.waiting_reply.set()
    await bot.send_message(
        callback_query.from_user.id,
        "💬 Напиши ответ пользователю. /cancel для отмены."
    )


@dp.message_handler(commands=["cancel"], state=SupportReplyStates)
async def support_reply_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Ответ отменён.")


@dp.message_handler(state=SupportReplyStates.waiting_reply)
async def handle_support_reply(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    msg_id = data.get('support_msg_id')
    target_user_id = int(data.get('support_user_id'))
    reply_text = message.text
    try:
        await bot.send_message(
            target_user_id,
            f"📩 *Ответ поддержки AlBi Music:*\n\n{reply_text}",
            parse_mode="Markdown"
        )
        # Удаляем сообщение после ответа (не копим отвеченные)
        execute_query_sync(
            "DELETE FROM support_messages WHERE id = %s",
            (msg_id,)
        )
        await state.finish()
        await message.answer("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
        await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('sup_close_'), state='*')
async def close_support_message(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id, "Закрыто")
    if not is_admin(callback_query.from_user.id):
        return
    msg_id = callback_query.data.split('_')[2]
    try:
        execute_query_sync("UPDATE support_messages SET replied = TRUE WHERE id = %s", (msg_id,))
    except Exception:
        pass
    try:
        await bot.edit_message_reply_markup(
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=None
        )
    except Exception:
        pass


if __name__ == '__main__':
    # init_db()  # SQLite больше не используется
    import asyncio
    # asyncio.run(db.init())  # Инициализация адаптера БД - ЗАКОММЕНТИРОВАНО
    # init_redis()  # Инициализация Redis - ЗАКОММЕНТИРОВАНО

    import asyncio
    logging.info("🚀 Запуск AlBi-music Bot + Payments...")
    import threading
    # Запуск FastAPI в отдельном потоке
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Запуск Telegram бота (правильный способ из бэкапа)
    logging.info("🚀 Запуск AlBi-music Bot + Payments...")
    
    # Инициализация PostgreSQL
    from postgres_db import init_postgres
    import asyncio
    
    async def init_db():
        await init_postgres()
    
    # Запускаем инициализацию в event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    
    executor.start_polling(dp, skip_updates=True)


