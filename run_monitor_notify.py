import asyncio
import logging
import sys
import os
import time
import socket

# Добавляем путь к проекту
sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync
import config
from config import BOT_TOKEN as TELEGRAM_BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/albimusic/monitor-error.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import subprocess
import tempfile
import os
import aiohttp


async def create_bot_ipv4(token):
    """
    Создаёт Bot через SOCKS5 прокси (127.0.0.1:9050 — Tor).
    Исправляет ошибку: Cannot connect to host api.telegram.org — аналогично main_with_payments.py.
    """
    from aiogram import Bot
    # Используем тот же socks5 прокси, что и основной бот (main_with_payments.py)
    bot = Bot(token=token, proxy='socks5://127.0.0.1:9050')
    return bot


def _is_forbidden_error(e: Exception) -> bool:
    """Проверяет, заблокировал ли пользователь бота (Forbidden / Chat not found / User deactivated)."""
    err_str = str(e).lower()
    return (
        'forbidden' in err_str or
        'bot was blocked' in err_str or
        'chat not found' in err_str or
        'user is deactivated' in err_str
    )


def mark_user_blocked(user_id: int):
    """Помечает пользователя как заблокировавшего бота (is_blocked=TRUE).
    Монитор будет игнорировать таких пользователей.
    Флаг сбрасывается автоматически когда пользователь напишет /start.
    """
    try:
        execute_query_sync(
            "UPDATE users SET is_blocked = TRUE WHERE user_id = %s",
            (user_id,)
        )
        logger.info(f"🚫 Пользователь {user_id} помечен is_blocked=TRUE (заблокировал бота)")
    except Exception as _e:
        logger.error(f"❌ Ошибка mark_user_blocked({user_id}): {_e}")


async def download_and_cut_audio(url, duration=60):
    """
    Скачивает MP3 файл и обрезает до указанной длительности

    Args:
        url: URL MP3 файла
        duration: Длительность в секундах (по умолчанию 60)
    
    Returns:
        Путь к обрезанному файлу или None при ошибке
    """
    try:
        # Создаем временную директорию
        temp_dir = '/tmp/albimusic_demos'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Генерируем уникальные имена файлов
        import uuid
        file_id = str(uuid.uuid4())[:8]
        full_path = f'{temp_dir}/full_{file_id}.mp3'
        demo_path = f'{temp_dir}/demo_{file_id}.mp3'
        
        # Скачиваем файл
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(full_path, 'wb') as f:
                        f.write(await response.read())
                    logger.info(f"📥 Скачан файл: {full_path}")
                else:
                    logger.error(f"❌ Ошибка скачивания: HTTP {response.status}")
                    return None
        
        # Обрезаем через ffmpeg
        cmd = [
            'ffmpeg',
            '-i', full_path,
            '-t', str(duration),
            '-c', 'copy',
            '-y',  # Перезаписать если существует
            demo_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✂️ Создано демо: {demo_path}")
            # Удаляем полный файл
            os.remove(full_path)
            return demo_path
        else:
            logger.error(f"❌ ffmpeg ошибка: {result.stderr}")
            # Очищаем файлы
            if os.path.exists(full_path):
                os.remove(full_path)
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка обрезки аудио: {e}")
        return None


async def send_telegram_notification(user_id, task_id, audio_url, is_song=False, is_cover=False):
    """Отправка ДЕМО аудио файлов (45 сек) с кнопкой разблокировки"""
    try:
        import json
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from db_utils import execute_query_sync

        bot = await create_bot_ipv4(TELEGRAM_BOT_TOKEN)

        # Парсим JSON массив ссылок
        audio_urls = []
        try:
            if isinstance(audio_url, str) and audio_url.startswith("["):
                parsed_urls = json.loads(audio_url)
                if isinstance(parsed_urls, list):
                    audio_urls = parsed_urls
                    logger.info(f"📊 JSON массив: {len(audio_urls)} ссылок для {task_id}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга JSON: {e}")

        if not audio_urls:
            audio_urls = [audio_url]

        # Проверяем есть ли 2 ссылки
        if len(audio_urls) < 2:
            logger.warning(f"⚠️ Меньше 2 ссылок для {task_id}, отправляю как обычно")

            # Проверяем, это WAV конвертация или другой тип задачи
            from db_utils import execute_query_sync

            # Получаем первый URL из списка
            file_url = audio_urls[0] if audio_urls else ""

            task_info = execute_query_sync(
                "SELECT prompt FROM generations WHERE task_id = %s",
                (task_id,)
            )
            prompt_text = task_info[0][0] if task_info else ""
            is_wav = "WAV" in prompt_text.upper() or file_url.lower().endswith('.wav')

            await bot.send_message(user_id, "🎵 Ваша музыка готова!")

            # Для WAV файлов скачиваем локально и отправляем как документ
            if is_wav:
                try:
                    logger.info(f"📥 Скачиваю WAV файл: {file_url}")

                    # Скачиваем файл
                    temp_dir = '/tmp/albimusic_wav'
                    os.makedirs(temp_dir, exist_ok=True)

                    import uuid
                    # WAV файлы обычно >50MB (лимит Telegram), отправляем ссылку
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🎵 *WAV файл готов!*\n\n📥 Скачать: {file_url}\n\n⚠️ Файл доступен 24 часа",
                        parse_mode="Markdown"
                    )
                    logger.info(f"✅ WAV ссылка отправлена user {user_id}")

                except Exception as e:
                    logger.error(f"❌ Ошибка отправки WAV: {e}")
                    await bot.send_message(user_id, "❌ Произошла ошибка при отправке файла.")
                    await bot.close()
                    return False  # Ошибка - пометить как ERROR_NOTIFIED
            else:
                # Для обычных треков отправляем по ссылке
                for idx, url in enumerate(audio_urls, 1):
                    await bot.send_audio(user_id, url, caption=f"🎼 Версия {idx}")

            await bot.close()
            return True

        # Для админа отправляем полные версии
        if user_id == config.ADMIN_ID:
            logger.info(f"👑 Админ {user_id}: отправляю ПОЛНЫЕ версии")
            header = "👑 **АДМИН MODE**: Полные версии готовы!"
            await bot.send_message(chat_id=user_id, text=header, parse_mode="Markdown")

            for idx, url in enumerate(audio_urls[:2], 1):
                try:
                    await bot.send_audio(
                        chat_id=user_id,
                        audio=url,
                        caption=f"🎼 Полная версия {idx}",
                        title=f"AI Music Full v{idx}",
                        performer="ALBI Music"
                    )
                    logger.info(f"✅ Полная версия {idx}/2 отправлена админу")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки полной версии {idx}: {e}")

            # Сохраняем в БД как разблокированное
            try:
                execute_query_sync(
                    """INSERT INTO demo_tracks (task_id, user_id, full_url_1, full_url_2, is_unlocked)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO UPDATE SET is_unlocked = true""",
                    (task_id, user_id, audio_urls[0], audio_urls[1], True)
                )
                logger.info(f"💾 Админ трек сохранён как разблокированный: {task_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения админ трека: {e}")

            # Отправляем описание функций и кнопки для админа
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎤 Минусовка (1 токен)",
                        callback_data=f"karaoke_{task_id}"
                    ),
                    InlineKeyboardButton(
                        text="🎸 Кавер (1 токен)",
                        callback_data=f"cover_{task_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎵 В WAV (2 токена)",
                        callback_data=f"wav_{task_id}"
                    ),
                    InlineKeyboardButton(
                        text="📢 Отправить в канал",
                        callback_data=f"post_{task_id}"
                    )
                ],
                [InlineKeyboardButton(
                    text="🔗 Поделиться с другом",
                    switch_inline_query=""
                )],
                [InlineKeyboardButton(
                    text="🔔 Перейти в канал",
                    url="https://t.me/ALBImusic_Chart"
                )]
            ])

            await bot.send_message(
                chat_id=user_id,
                text="💎 **Что можно сделать с этой песней:**\n\n" +
                     "🎤 **Минусовка** — версия без вокала для исполнения\n" +
                     "🎸 **Кавер** — перепой в другом стиле/жанре\n" +
                     "🎵 **В WAV** — конвертируй в WAV формат для профи\n" +
                     "📢 **Отправить в канал** — опубликуй в нашем официальном канале\n" +
                     "🔗 **Поделиться** — отправь другу прямо сейчас",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

            await bot.close()
            return True

        # Для кавера (уже оплачен) - отправляем ПОЛНЫЕ версии без обрезки
        if is_cover:
            logger.info(f"🎸 Кавер {task_id}: отправляю ПОЛНЫЕ версии для user {user_id}")
            await bot.send_message(chat_id=user_id, text="🎸 **Ваш кавер готов!**", parse_mode="Markdown")

            for idx, url in enumerate(audio_urls[:2], 1):
                try:
                    await bot.send_audio(
                        chat_id=user_id,
                        audio=url,
                        caption=f"🎸 Кавер — Версия {idx}",
                        title=f"Cover v{idx}",
                        performer="ALBI Music"
                    )
                    logger.info(f"✅ Кавер версия {idx}/2 отправлена user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки кавера {idx}: {e}")

            # Кавер уже оплачен — сохраняем как разблокированный
            try:
                execute_query_sync(
                    """INSERT INTO demo_tracks (task_id, user_id, full_url_1, full_url_2, is_unlocked)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO UPDATE SET is_unlocked = true""",
                    (task_id, user_id, audio_urls[0], audio_urls[1] if len(audio_urls) > 1 else audio_urls[0], True)
                )
                logger.info(f"💾 Кавер сохранён как разблокированный: {task_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения кавера в demo_tracks: {e}")

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🎤 Минусовка (1 токен)", callback_data=f"karaoke_{task_id}"),
                    InlineKeyboardButton(text="🎸 Кавер (1 токен)", callback_data=f"cover_{task_id}")
                ],
                [
                    InlineKeyboardButton(text="🎵 В WAV (2 токена)", callback_data=f"wav_{task_id}"),
                    InlineKeyboardButton(text="📢 Отправить в канал", callback_data=f"post_{task_id}")
                ]
            ])
            await bot.send_message(
                chat_id=user_id,
                text="💎 **Что можно сделать с кавером:**\n\n"
                     "🎤 **Минусовка** — версия без вокала\n"
                     "🎸 **Кавер** — создай ещё один кавер\n"
                     "🎵 **В WAV** — конвертируй в WAV формат\n"
                     "📢 **Отправить в канал** — опубликуй",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await bot.close()
            return True

        # Проверяем: первая ли это генерация пользователя
        # (если да — отправляем ПОЛНУЮ версию в подарок, токен уже списан)
        first_gen_check = execute_query_sync(
            "SELECT COUNT(*) FROM generations WHERE user_id = %s AND status = 'completed'",
            (user_id,)
        )
        completed_count = first_gen_check[0][0] if first_gen_check and first_gen_check[0] else 0
        is_first_generation = (completed_count == 1)

        if is_first_generation:
            logger.info(f"🎁 Первая генерация user {user_id}: отправляю ДЕМО 45 сек + предложение разблокировки за 29₽")
            header = "🎤 Ваша первая песня готова! 🎁" if is_song else "🎵 Ваша первая музыка готова! 🎁"
            await bot.send_message(chat_id=user_id, text=header, parse_mode="Markdown")

            # Отправляем 45-секундное демо (без полного трека)
            demo_paths = []
            for idx, url in enumerate(audio_urls[:2], 1):
                try:
                    demo_path = await download_and_cut_audio(url, duration=45)
                    if demo_path:
                        with open(demo_path, 'rb') as audio_file:
                            await bot.send_audio(
                                chat_id=user_id,
                                audio=audio_file,
                                caption=f"🎼 Демо — Версия {idx} (45 сек)",
                                title=f"AI Music Demo v{idx}",
                                performer="ALBI Music"
                            )
                        demo_paths.append(demo_path)
                        logger.info(f"✅ Демо {idx}/2 отправлено user {user_id} (первая генерация)")
                    else:
                        logger.error(f"❌ Не удалось создать демо {idx} для первой генерации user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки демо {idx} (первая генерация): {e}")

            # Сохраняем в demo_tracks как НЕ разблокированное
            try:
                execute_query_sync(
                    """INSERT INTO demo_tracks (task_id, user_id, full_url_1, full_url_2, is_unlocked)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO NOTHING""",
                    (task_id, user_id, audio_urls[0], audio_urls[1] if len(audio_urls) > 1 else audio_urls[0], False)
                )
                logger.info(f"💾 Первая генерация сохранена в demo_tracks (unlocked=False): {task_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения первой генерации в demo_tracks: {e}")

            # ✅ Запускаем 24-часовое окно новичка (novice window)
            try:
                execute_query_sync(
                    "UPDATE users SET novice_window_started_at = NOW() "
                    "WHERE user_id = %s AND novice_window_started_at IS NULL",
                    (user_id,)
                )
                logger.info(f"⏰ 24-часовое окно новичка запущено для user {user_id}")
            except Exception as _nw:
                logger.warning(f"⚠️ Ошибка записи novice_window_started_at для {user_id}: {_nw}")

            # ✅ TG П4: Начисляем реферальный бонус пригласившему при первой генерации
            try:
                ref_row = execute_query_sync(
                    "SELECT referrer_id FROM referrals WHERE referred_id = %s AND bonus_applied = FALSE",
                    (user_id,)
                )
                if ref_row:
                    referrer_id_tg = ref_row[0][0]
                    execute_query_sync(
                        "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                        (referrer_id_tg,)
                    )
                    execute_query_sync(
                        """INSERT INTO token_transactions (user_id, amount, transaction_type, description)
                           VALUES (%s, %s, %s, %s)""",
                        (referrer_id_tg, 2, 'credit',
                         f'Referral bonus: TG friend {user_id} first generation')
                    )
                    execute_query_sync(
                        "UPDATE referrals SET bonus_applied = TRUE WHERE referred_id = %s",
                        (user_id,)
                    )
                    logger.info(
                        f"💰 TG referral bonus: +2 tokens to {referrer_id_tg} "
                        f"(invited {user_id}, first TG generation)"
                    )
            except Exception as _ref_e:
                logger.warning(f"⚠️ TG referral bonus error for user {user_id}: {_ref_e}")

            # Кнопки: только «Послушать» и «Разблокировать за 29₽» (первые 24 часа) — без «Скачать» и прочих функций
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔓 Получить ПОЛНУЮ версию — 29₽ ⏰ (только 24 часа!)",
                    callback_data=f"pay_unlock_29_{task_id}"
                )],
                [InlineKeyboardButton(
                    text="🎧 Послушать ещё раз",
                    callback_data=f"play_{task_id}"
                )],
                [InlineKeyboardButton(
                    text="🔔 Перейти в канал",
                    url="https://t.me/ALBImusic_Chart"
                )]
            ])
            # ИСПРАВЛЕНИЕ: оборачиваем в try/except чтобы Forbidden/Chat not found
            # не ломал цикл мониторинга — функция должна вернуть True даже если
            # пользователь заблокировал бота, иначе монитор зациклится.
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🎧 *Это демо твоей первой песни (45 секунд)*\n\n"
                        "⚠️ Это только Preview — полная версия длиннее!\n\n"
                        "🔓 *Разблокируй полную версию за 29₽:*\n"
                        "• Оба трека без ограничений по времени\n"
                        "• Кнопки «Послушать» и «Скачать»\n"
                        "• Минусовка, Кавер, WAV и многое другое\n\n"
                        "⏰ *Цена 29₽ действует только 24 часа с момента создания первой песни!*\n"
                        "После — стандартная цена от 99₽.\n\n"
                        "👇 Нажми кнопку ниже:"
                    ),
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Кнопка разблокировки (29₽) отправлена user {user_id}")
            except Exception as _send_err:
                logger.error(f"❌ Ошибка отправки кнопки разблокировки user {user_id}: {_send_err} — помечаем ALREADY_SENT всё равно")
                if _is_forbidden_error(_send_err):
                    mark_user_blocked(user_id)

            # ✅ Планируем оффер «Новичок» через 3 мин (резерв)
            try:
                execute_query_sync(
                    "UPDATE users SET novice_offer_pending_at = NOW() "
                    "WHERE user_id = %s AND novice_offer_pending_at IS NULL "
                    "AND (novice_offer_sent IS NULL OR novice_offer_sent = FALSE)",
                    (user_id,)
                )
                logger.info(f"⏰ Оффер «Новичок» запланирован для user {user_id}")
            except Exception as _ne:
                logger.warning(f"⚠️ Ошибка планирования оффера для {user_id}: {_ne}")

            # Очищаем временные демо файлы
            for demo_path in demo_paths:
                try:
                    if os.path.exists(demo_path):
                        os.remove(demo_path)
                        logger.info(f"🗑️ Удален временный файл: {demo_path}")
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления {demo_path}: {e}")

            await bot.close()
            return True

        # Для пользователей с оплатой - отправляем ПОЛНЫЕ версии
        has_paid_result = execute_query_sync(
            "SELECT COUNT(*) FROM payments WHERE user_id = %s AND status = 'succeeded'",
            (user_id,)
        )
        has_paid = has_paid_result and has_paid_result[0][0] > 0

        if has_paid:
            logger.info(f"💳 Пользователь {user_id} оплатил: отправляю ПОЛНЫЕ версии для {task_id}")
            header = "🎤 Ваша песня готова!" if is_song else "🎵 Ваша музыка готова!"
            await bot.send_message(chat_id=user_id, text=header)

            for idx, url in enumerate(audio_urls[:2], 1):
                try:
                    await bot.send_audio(
                        chat_id=user_id,
                        audio=url,
                        caption=f"🎼 Полная версия {idx}",
                        title=f"AI Music Full v{idx}",
                        performer="ALBI Music"
                    )
                    logger.info(f"✅ Полная версия {idx}/2 отправлена user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки полной версии {idx}: {e}")

            # Сохраняем как разблокированное
            try:
                execute_query_sync(
                    """INSERT INTO demo_tracks (task_id, user_id, full_url_1, full_url_2, is_unlocked)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO UPDATE SET is_unlocked = true""",
                    (task_id, user_id, audio_urls[0], audio_urls[1] if len(audio_urls) > 1 else audio_urls[0], True)
                )
                logger.info(f"💾 Оплаченный трек сохранён как разблокированный: {task_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения в demo_tracks: {e}")

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🎤 Минусовка (1 токен)", callback_data=f"karaoke_{task_id}"),
                    InlineKeyboardButton(text="🎸 Кавер (1 токен)", callback_data=f"cover_{task_id}")
                ],
                [
                    InlineKeyboardButton(text="🎵 В WAV (2 токена)", callback_data=f"wav_{task_id}"),
                    InlineKeyboardButton(text="📢 Отправить в канал", callback_data=f"post_{task_id}")
                ],
                [InlineKeyboardButton(text="🔗 Поделиться с другом", switch_inline_query="")],
                [InlineKeyboardButton(text="🔔 Перейти в канал", url="https://t.me/ALBImusic_Chart")]
            ])

            await bot.send_message(
                chat_id=user_id,
                text="💎 **Что можно сделать с этой песней:**\n\n" +
                     "🎤 **Минусовка** — версия без вокала для исполнения\n" +
                     "🎸 **Кавер** — перепой в другом стиле/жанре\n" +
                     "🎵 **В WAV** — конвертируй в WAV формат для профи\n" +
                     "📢 **Отправить в канал** — опубликуй в нашем официальном канале\n" +
                     "🔗 **Поделиться** — отправь другу прямо сейчас",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

            await bot.close()
            return True

        # Отправляем заголовок (для обычных пользователей без оплаты)
        header = "🎤 Ваша песня готова!" if is_song else "🎵 Ваша музыка готова!"
        header += "\n\n🎧 Демо-версии (60 секунд):"
        await bot.send_message(chat_id=user_id, text=header)

        # Обрезаем и отправляем демо версии
        demo_paths = []
        for idx, url in enumerate(audio_urls[:2], 1):  # Только первые 2
            try:
                # Скачиваем и обрезаем
                demo_path = await download_and_cut_audio(url, duration=60)

                if demo_path:
                    # Отправляем демо как аудио файл
                    with open(demo_path, 'rb') as audio_file:
                        await bot.send_audio(
                            chat_id=user_id,
                            audio=audio_file,
                            caption=f"🎼 Демо - Версия {idx} (60 сек)",
                            title=f"AI Music Demo v{idx}",
                            performer="ALBI Music"
                        )
                    
                    demo_paths.append(demo_path)
                    logger.info(f"✅ Демо {idx}/2 отправлено user {user_id}")
                else:
                    logger.error(f"❌ Не удалось создать демо {idx}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка отправки демо {idx}: {e}")
        
        # Кнопки после демо-трека
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔓 Разблокировать полные версии (1 токен)",
                callback_data=f"unlock_{task_id}"
            )],
            [
                InlineKeyboardButton(
                    text="🎤 Минусовка (1 токен)",
                    callback_data=f"karaoke_{task_id}"
                ),
                InlineKeyboardButton(
                    text="🎸 Кавер (1 токен)",
                    callback_data=f"cover_{task_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 В WAV (2 токена)",
                    callback_data=f"wav_{task_id}"
                ),
                InlineKeyboardButton(
                    text="📢 Отправить в канал",
                    callback_data=f"post_{task_id}"
                )
            ],
            [InlineKeyboardButton(
                text="🔗 Поделиться с другом",
                switch_inline_query=""
            )],
            [InlineKeyboardButton(
                text="🔔 Перейти в канал",
                url="https://t.me/ALBImusic_Chart"
            )]
        ])

        # ✅ Соц. доказательство в DEMO-пейволле
        try:
            _tu_tg = execute_query_sync("SELECT COUNT(*) FROM users")
            _total_tg = _tu_tg[0][0] if _tu_tg else 658
        except Exception:
            _total_tg = 658
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"🎵 Уже *{_total_tg}+* музыкантов создают треки в ALBI Music!\n\n"
                "💎 **Что можно сделать с этой песней:**\n\n"
                "🔓 **Разблокировать** — получи полные версии (1 токен)\n"
                "🎤 **Минусовка** — версия без вокала для исполнения\n"
                "🎸 **Кавер** — перепой в другом стиле/жанре\n"
                "🎵 **В WAV** — конвертируй в WAV формат для профи\n"
                "📢 **Отправить в канал** — опубликуй в нашем канале\n"
                "🔗 **Поделиться** — отправь другу и получи 1 ТОКЕН БЕСПЛАТНО! 🎁"
            ),
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        
        # Сохраняем в БД demo_tracks
        try:
            execute_query_sync(
                """INSERT INTO demo_tracks (task_id, user_id, full_url_1, full_url_2, is_unlocked)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (task_id) DO NOTHING""",
                (task_id, user_id, audio_urls[0], audio_urls[1], False)
            )
            logger.info(f"💾 Сохранено в demo_tracks: {task_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в demo_tracks: {e}")

        # === АВТООФФЕР НОВИЧКУ ===
        # Проверяем: это первая генерация у пользователя?
        try:
            gen_count_result = execute_query_sync(
                "SELECT COUNT(*) FROM generations WHERE user_id = %s AND status = 'completed'",
                (user_id,)
            )
            gen_count = gen_count_result[0][0] if gen_count_result else 0
            novice_check = execute_query_sync(
                "SELECT novice_offer_sent FROM users WHERE user_id = %s",
                (user_id,)
            )
            novice_sent = novice_check and novice_check[0][0]

            if gen_count == 1 and not novice_sent:
                # Планируем оффер через 3 минуты — записываем текущее время
                execute_query_sync(
                    "UPDATE users SET novice_offer_pending_at = NOW() WHERE user_id = %s AND novice_offer_pending_at IS NULL",
                    (user_id,)
                )
                logger.info(f"⏰ Запланирован оффер «Новичок» для user {user_id} через 3 мин")
        except Exception as _e:
            logger.error(f"❌ Ошибка планирования оффера новичку {user_id}: {_e}")

        # Очищаем временные демо файлы
        for demo_path in demo_paths:
            try:
                if os.path.exists(demo_path):
                    os.remove(demo_path)
                    logger.info(f"🗑️ Удален временный файл: {demo_path}")
            except Exception as e:
                logger.error(f"❌ Ошибка удаления {demo_path}: {e}")
        
        await bot.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки демо user {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if _is_forbidden_error(e):
            mark_user_blocked(user_id)
        return False

async def send_error_notification(user_id, task_id, prompt=None):
    """Отправка уведомления об ошибке генерации"""
    try:
        bot = await create_bot_ipv4(TELEGRAM_BOT_TOKEN)
        
        message_text = "❌ К сожалению, генерация не удалась.\n\n"
        if prompt:
            message_text += f"📝 Запрос: {prompt[:200]}...\n\n"
        message_text += "Попробуйте снова или обратитесь в поддержку."
        
        await bot.send_message(chat_id=user_id, text=message_text)
        await bot.close()
        
        logger.info(f"✅ Уведомление об ошибке отправлено user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления об ошибке user {user_id}: {e}")
        if _is_forbidden_error(e):
            mark_user_blocked(user_id)
        return False



async def send_novice_offer(user_id: int):
    """Отправляет предложение пакета «Новичок» через 3 минуты после первой песни"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        bot = await create_bot_ipv4(TELEGRAM_BOT_TOKEN)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("⏳ Забрать 5 треков за 99₽", callback_data="pay_99_novice")
        )
        await bot.send_message(
            user_id,
            "⚡️ Поздравляю! Ты создал свой первый хит! Тебе понравилось?\n\n"
            "Обычно наши пользователи не могут остановиться на одной песне 😅  "
            "Пока ты здесь, держи секретное предложение, которое сгорит через 60 минут. "
            "Это одноразовое предложение и его больше не будет никогда:\n\n"
            "🎁 Скрытый Пакет «Новичок» (5 полных треков) всего за 99₽ (вместо 250₽).\n"
            "Хватит, чтобы сделать трек про друга (подругу), признаться в любви, "
            "поздравить маму или просто поржать!\n"
            "👇 Жми на кнопку, пока таймер не истёк!",
            reply_markup=markup
        )
        # Отмечаем оффер как отправленный
        execute_query_sync(
            "UPDATE users SET novice_offer_sent = TRUE, novice_offer_pending_at = NULL WHERE user_id = %s",
            (user_id,)
        )
        logger.info(f"✅ Оффер «Новичок» отправлен пользователю {user_id}")
        await bot.close()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки оффера «Новичок» для {user_id}: {e}")
        # Если пользователь заблокировал бота или чат не найден — помечаем отправленным,
        # чтобы монитор не спамил ошибками каждые 10 секунд навсегда.
        err_str = str(e).lower()
        if 'forbidden' in err_str or 'bot was blocked' in err_str or 'chat not found' in err_str or 'user is deactivated' in err_str:
            try:
                execute_query_sync(
                    "UPDATE users SET novice_offer_sent = TRUE, novice_offer_pending_at = NULL WHERE user_id = %s",
                    (user_id,)
                )
                logger.info(f"🚫 Оффер «Новичок» для {user_id} помечен sent=TRUE (пользователь заблокировал бота)")
                mark_user_blocked(user_id)
            except Exception:
                pass
        return False


async def check_and_send_novice_offers():
    """Проверяет пользователей с pending-оффером >= 3 мин и отправляет им предложение «Новичок»"""
    try:
        pending = execute_query_sync(
            """SELECT user_id FROM users
               WHERE novice_offer_pending_at IS NOT NULL
               AND (novice_offer_sent IS NULL OR novice_offer_sent = FALSE)
               AND NOW() - novice_offer_pending_at >= interval '3 minutes'
               AND (is_blocked IS NULL OR is_blocked = FALSE)
               LIMIT 10"""
        )
        if pending:
            for (uid,) in pending:
                await send_novice_offer(uid)
                await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ Ошибка check_and_send_novice_offers: {e}")


async def check_and_clean_duplicates():
    """
    Проверяет и очищает дублирующиеся записи в таблице generations.
    Оставляет только последнюю запись для каждой пары (user_id, task_id).
    """
    logger.info("🔍 Проверка дубликатов в БД...")
    
    try:
        # Находим дубликаты
        duplicates = await execute_query("""
            SELECT 
                user_id,
                task_id,
                COUNT(*) as duplicate_count,
                MAX(created_at) as latest_created,
                MIN(created_at) as earliest_created
            FROM generations
            GROUP BY user_id, task_id
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 20
        """)
        
        if duplicates:
            logger.warning(f"⚠️  Найдено {len(duplicates)} групп дубликатов")
            
            for dup in duplicates:
                user_id, task_id, count, latest, earliest = dup
                logger.warning(f"   • user_id={user_id}, task_id={task_id}: {count} дубликатов")
                
                # Удаляем старые дубликаты, оставляя только последний
                deleted = await execute_query("""
                    DELETE FROM generations
                    WHERE user_id = %s 
                      AND task_id = %s 
                      AND id NOT IN (
                          SELECT id 
                          FROM generations 
                          WHERE user_id = %s 
                            AND task_id = %s 
                          ORDER BY created_at DESC 
                          LIMIT 1
                      )
                    RETURNING COUNT(*)
                """, (user_id, task_id, user_id, task_id))
                
                if deleted and deleted[0]:
                    logger.info(f"     ✅ Удалено {deleted[0]} старых дубликатов")
        else:
            logger.info("✅ Дубликатов не найдено")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке дубликатов: {e}")

# Множество задач, которым уже отправили "ещё генерируется"
_progress_notified: set = set()


async def check_long_running_generations():
    """
    Ищет генерации с status='processing' дольше 3 минут и отправляет пользователю
    одно промежуточное уведомление «ещё работаем», чтобы не беспокоился.
    Это решает жалобы типа «почему так долго / нет трека».
    """
    global _progress_notified
    try:
        long_running = execute_query_sync(
            """
            SELECT g.task_id, g.user_id, g.created_at
            FROM generations g
            LEFT JOIN users u ON u.user_id = g.user_id
            WHERE g.status = 'processing'
              AND g.created_at < NOW() - INTERVAL '3 minutes'
              AND g.created_at > NOW() - INTERVAL '20 minutes'
              AND (u.is_blocked IS NULL OR u.is_blocked = FALSE)
            LIMIT 20
            """
        )
        if not long_running:
            return

        for task_id, user_id, created_at in long_running:
            if task_id in _progress_notified:
                continue
            try:
                import datetime
                elapsed_sec = (
                    (datetime.datetime.utcnow() - created_at.replace(tzinfo=None)).total_seconds()
                    if hasattr(created_at, 'replace') else 180
                )
                elapsed_min = max(1, int(elapsed_sec / 60))

                bot = await create_bot_ipv4(TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⏳ Ваш трек всё ещё создаётся...\n\n"
                        f"🎵 AI уже работает над вашей музыкой {elapsed_min}+ мин — "
                        f"это нормально для сложных запросов!\n\n"
                        f"Как только трек будет готов — мы сразу отправим его вам 🎶\n"
                        f"Обычно генерация занимает 2–7 минут."
                    )
                )
                await bot.close()
                _progress_notified.add(task_id)
                logger.info(f"⏳ Progress notification sent: user={user_id}, task={task_id}, elapsed={elapsed_min}m")
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"❌ Progress notify failed for user {user_id} task {task_id}: {e}")
                if _is_forbidden_error(e):
                    mark_user_blocked(user_id)

        # Чистим память: убираем из множества те задачи, которые уже завершились
        if len(_progress_notified) > 200:
            _progress_notified = set(list(_progress_notified)[-100:])

    except Exception as e:
        logger.error(f"❌ check_long_running_generations error: {e}")


async def monitor_generations():
    """Основная функция мониторинга"""
    # Инициализируем пул подключений к БД
    from db_utils import init_db_pool_sync
    init_db_pool_sync()
    logger.info("🚀 Запуск мониторинга завершенных задач...")
    
    # Словарь для отслеживания уже отправленных уведомлений
    sent_notifications = set()
    
    while True:
        try:
            # Ищем завершенные задачи в БД (и ошибки)
            # Исключаем задачи с префиксами ALREADY_SENT_, ALREADY_NOTIFIED_ или ERROR_NOTIFIED
            results = execute_query_sync(
                """SELECT g.task_id, g.user_id, g.prompt, g.audio_url, g.status
                   FROM generations g
                   LEFT JOIN users u ON u.user_id = g.user_id
                   WHERE ((g.status = 'completed' AND g.audio_url IS NOT NULL)
                      OR (g.status = 'error' AND g.audio_url IS NOT NULL))
                   AND g.audio_url NOT LIKE 'ALREADY_SENT_%'
                   AND g.audio_url NOT LIKE 'ALREADY_NOTIFIED_%'
                   AND g.audio_url != 'ERROR_NOTIFIED'
                   AND (u.is_blocked IS NULL OR u.is_blocked = FALSE)
                   ORDER BY g.created_at DESC LIMIT 10"""
            )
            
            if results:
                for task_id, user_id, prompt, audio_url, status in results:
                    # Проверяем, не отправляли ли уже уведомление для этой задачи
                    if task_id not in sent_notifications:
                        logger.info(f"📨 Найдена задача {task_id} для пользователя {user_id} (статус: {status})")
                        
                        # Для ошибок отправляем особое уведомление
                        if status == 'error' or "ERROR:" in str(audio_url):
                            await send_error_notification(user_id, task_id, prompt)
                            sent_notifications.add(task_id)
                            # Помечаем в БД как уведомленную
                            execute_query_sync(
                                "UPDATE generations SET audio_url = 'ERROR_NOTIFIED' WHERE task_id = %s",
                                (task_id,)
                            )
                            logger.info(f"💾 Ошибка {task_id} помечена в БД как уведомленная")
                            continue
                        
                        # Определяем тип задачи (песня, музыка или кавер)
                        is_song = "текст" in prompt.lower() if prompt else False
                        is_cover = "кавер" in prompt.lower() if prompt else False

                        # Отправляем уведомление об успехе
                        success = await send_telegram_notification(user_id, task_id, audio_url, is_song, is_cover)

                        # КРИТИЧНО: Помечаем задачу ВСЕГДА, даже при ошибке,
                        # чтобы избежать бесконечного цикла повторной отправки
                        sent_notifications.add(task_id)

                        if success:
                            # Успешная отправка - помечаем как ALREADY_SENT
                            new_audio_url = f"ALREADY_SENT_{audio_url}" if not audio_url.startswith("ALREADY_SENT_") else audio_url
                            execute_query_sync(
                                "UPDATE generations SET audio_url = %s WHERE task_id = %s",
                                (new_audio_url, task_id)
                            )
                            logger.info(f"✅ Уведомление для задачи {task_id} отправлено и помечено в БД")
                        else:
                            # ИСПРАВЛЕНИЕ: При ошибке отправки НЕ перезаписываем audio_url и НЕ меняем статус.
                            # Раньше здесь был баг: audio_url заменялся на 'ERROR_NOTIFIED',
                            # что уничтожало ссылку на готовую песню пользователя.
                            # Теперь убираем задачу из sent_notifications → монитор повторит попытку.
                            sent_notifications.discard(task_id)
                            logger.error(
                                f"❌ Не удалось отправить уведомление для задачи {task_id} "
                                f"(вероятно, проблема сети). audio_url сохранён — будет повтор через 10 сек."
                            )
            
            # Очищаем старые уведомления (чтобы не накапливать память)
            if len(sent_notifications) > 100:
                # Оставляем только последние 50 уведомлений
                sent_notifications = set(list(sent_notifications)[-50:])
                logger.info(f"🧹 Очищены старые уведомления, осталось: {len(sent_notifications)}")
            
            # Проверяем отложенные офферы для новичков (через 3 мин после первой песни)
            await check_and_send_novice_offers()

            # Уведомляем пользователей, у которых генерация идёт >3 мин без ответа
            await check_long_running_generations()

            # Пауза между проверками
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в мониторинге: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_generations())
    except KeyboardInterrupt:
        logger.info("👋 Мониторинг остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
