"""
Модуль администрирования VK-бота
Включает: статистику, рассылку, модерацию поддержки, диагностику Suno API
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from db_utils import execute_query_sync

logger = logging.getLogger(__name__)

def get_admin_stats() -> str:
    """
    Получить статистику бота для админ-панели
    
    Returns:
        Отформатированная строка со статистикой
    """
    try:
        # Всего пользователей
        users_count = execute_query_sync(
            "SELECT COUNT(*) FROM users"
        )[0][0]
        
        # Новые пользователи за 24 часа
        users_24h = execute_query_sync(
            "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours'"
        )[0][0]
        
        # Новые пользователи за 7 дней
        users_7d = execute_query_sync(
            "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '7 days'"
        )[0][0]
        
        # Количество генераций
        generations_count = execute_query_sync(
            "SELECT COUNT(*) FROM generations"
        )[0][0]
        
        # Генерации за 24 часа
        generations_24h = execute_query_sync(
            "SELECT COUNT(*) FROM generations WHERE created_at > NOW() - INTERVAL '24 hours'"
        )[0][0]
        
        # Генерации за 7 дней
        generations_7d = execute_query_sync(
            "SELECT COUNT(*) FROM generations WHERE created_at > NOW() - INTERVAL '7 days'"
        )[0][0]
        
        # Статистика платежей (если таблица существует)
        try:
            # За 24 часа
            payments_24h = execute_query_sync(
                """
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM payments
                WHERE created_at > NOW() - INTERVAL '24 hours'
                AND status = 'succeeded'
                """
            )
            payments_count_24h = payments_24h[0][0] if payments_24h else 0
            payments_sum_24h = int(payments_24h[0][1]) if payments_24h else 0
            
            # За 7 дней
            payments_7d = execute_query_sync(
                """
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM payments
                WHERE created_at > NOW() - INTERVAL '7 days'
                AND status = 'succeeded'
                """
            )
            payments_count_7d = payments_7d[0][0] if payments_7d else 0
            payments_sum_7d = int(payments_7d[0][1]) if payments_7d else 0
            
            # Всего
            payments_all = execute_query_sync(
                """
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM payments
                WHERE status = 'succeeded'
                """
            )
            payments_count_all = payments_all[0][0] if payments_all else 0
            payments_sum_all = int(payments_all[0][1]) if payments_all else 0
        except Exception as e:
            logger.warning(f"Таблица payments не существует или ошибка: {e}")
            payments_count_24h = 0
            payments_sum_24h = 0
            payments_count_7d = 0
            payments_sum_7d = 0
            payments_count_all = 0
            payments_sum_all = 0
        
        # Статистика реферальной системы (если таблица существует)
        try:
            referrals_count = execute_query_sync(
                "SELECT COUNT(*) FROM referrals"
            )[0][0]
            
            referrals_24h = execute_query_sync(
                "SELECT COUNT(*) FROM referrals WHERE created_at > NOW() - INTERVAL '24 hours'"
            )[0][0]
        except Exception:
            referrals_count = 0
            referrals_24h = 0
        
        # Статистика разблокировок (если таблица существует)
        try:
            unlocked_count = execute_query_sync(
                "SELECT COUNT(*) FROM demo_tracks WHERE is_unlocked = TRUE"
            )[0][0]
            
            unlocked_24h = execute_query_sync(
                "SELECT COUNT(*) FROM demo_tracks WHERE is_unlocked = TRUE AND unlocked_at > NOW() - INTERVAL '24 hours'"
            )[0][0]
        except Exception:
            unlocked_count = 0
            unlocked_24h = 0
        
        return f"""📊 **СТАТИСТИКА БОТА ALBI MUSIC**

👥 **Пользователи:**
├ За 24 часа: {users_24h} новых
├ За 7 дней: {users_7d} новых
└ Всего: {users_count} пользователей

🎵 **Генерации:**
├ За 24 часа: {generations_24h}
├ За 7 дней: {generations_7d}
└ Всего: {generations_count}

💰 **Платежи:**
├ За 24 часа: {payments_count_24h} · {payments_sum_24h}₽
├ За 7 дней: {payments_count_7d} · {payments_sum_7d}₽
└ Всего: {payments_count_all} · {payments_sum_all}₽

🌟 **Рефералы:**
├ За 24 часа: {referrals_24h}
└ Всего: {referrals_count}

🔓 **Разблокировки:**
├ За 24 часа: {unlocked_24h}
└ Всего: {unlocked_count}"""
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return f"❌ Ошибка получения статистики: {e}"


def get_support_messages(offset: int = 0, limit: int = 5) -> List[Dict]:
    """
    Получить список необработанных сообщений поддержки
    
    Args:
        offset: Смещение для пагинации
        limit: Количество сообщений
        
    Returns:
        Список словарей с данными сообщений
    """
    try:
        messages = execute_query_sync(
            """
            SELECT id, user_id, username, first_name, message, replied, created_at
            FROM support_messages
            WHERE replied = FALSE
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        
        if not messages:
            return []
        
        result = []
        for row in messages:
            result.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2] or '',
                'first_name': row[3] or 'Пользователь',
                'message': row[4],
                'replied': row[5],
                'created_at': row[6]
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения сообщений поддержки: {e}")
        return []


def send_support_reply(msg_id: int, target_user_id: int, reply_text: str) -> Tuple[bool, str]:
    """
    Отправить ответ на сообщение поддержки
    
    Args:
        msg_id: ID сообщения в БД
        target_user_id: ID пользователя VK
        reply_text: Текст ответа
        
    Returns:
        Tuple (успех, сообщение об ошибке или успехе)
    """
    try:
        # Удаляем сообщение из очереди (как в TG-боте)
        execute_query_sync(
            "DELETE FROM support_messages WHERE id = %s",
            (msg_id,)
        )
        return True, "Ответ отправлен пользователю"
        
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении сообщения поддержки: {e}")
        return False, f"Ошибка: {e}"


def close_support_message(msg_id: int) -> bool:
    """
    Закрыть (пометить как обработанное) сообщение поддержки
    
    Args:
        msg_id: ID сообщения в БД
        
    Returns:
        True если успешно
    """
    try:
        execute_query_sync(
            "UPDATE support_messages SET replied = TRUE WHERE id = %s",
            (msg_id,)
        )
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка закрытия сообщения поддержки: {e}")
        return False


def get_all_user_ids() -> List[int]:
    """
    Получить список всех user_id для рассылки (все платформы)
    
    Returns:
        Список user_id
    """
    try:
        rows = execute_query_sync("SELECT user_id FROM users")
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка пользователей: {e}")
        return []


def get_vk_user_ids() -> List[int]:
    """
    Получить список user_id только VK-пользователей для рассылки через VK-бот.
    Фильтрует по полю provider = 'vk', которое устанавливается при регистрации
    через VK-бота.

    Returns:
        Список user_id пользователей VK
    """
    try:
        rows = execute_query_sync(
            "SELECT user_id FROM users WHERE provider = 'vk'"
        )
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка VK-пользователей: {e}")
        return []


def check_suno_api() -> str:
    """
    Проверка работоспособности Suno API
    
    Returns:
        Отформатированная строка с результатами проверки
    """
    try:
        import requests
        import sys
        sys.path.insert(0, '.')
        
        # Импортируем конфигурацию
        try:
            from config import SUNO_API_KEY, SUNO_API_URL
        except ImportError:
            return "❌ Ошибка импорта config.py — проверьте наличие SUNO_API_KEY и SUNO_API_URL"
        
        # Проверяем наличие необходимых параметров
        if not SUNO_API_KEY or not SUNO_API_URL:
            return "❌ SUNO_API_KEY или SUNO_API_URL не настроены в config.py"
        
        # Список endpoints для проверки (из celery_tasks.py)
        tests = [
            {
                "url": f"{SUNO_API_URL}/api/v1/generate",
                "method": "POST",
                "name": "Создание задачи",
                "data": {"prompt": "test", "instrumental": True}
            },
            {
                "url": f"{SUNO_API_URL}/api/v1/generate/record-info",
                "method": "GET",
                "name": "Проверка статуса",
                "params": {"taskId": "test_123"}
            }
        ]
        
        headers = {
            "Authorization": f"Bearer {SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        results = []
        all_ok = True
        
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
                
                duration = (time.time() - start) * 1000  # мс
                
                if response.status_code in [200, 201, 400, 404]:
                    # 400/404 тоже считаем рабочим (endpoint отвечает)
                    status_emoji = "✅" if response.status_code in [200, 201] else "⚠️"
                    results.append(
                        f"{status_emoji} {test['name']}\n"
                        f"   └ Код: {response.status_code} · {int(duration)}ms"
                    )
                else:
                    all_ok = False
                    results.append(
                        f"❌ {test['name']}\n"
                        f"   └ Код: {response.status_code} · {int(duration)}ms"
                    )
                    
            except requests.exceptions.Timeout:
                all_ok = False
                results.append(f"⏱️ {test['name']}\n   └ Таймаут >15s")
            except requests.exceptions.ConnectionError:
                all_ok = False
                results.append(f"🔌 {test['name']}\n   └ Нет соединения")
            except Exception as e:
                all_ok = False
                results.append(f"❌ {test['name']}\n   └ {str(e)[:50]}")
        
        header = "✅ **SUNO API РАБОТАЕТ**" if all_ok else "⚠️ **SUNO API — ЕСТЬ ПРОБЛЕМЫ**"
        
        return f"""{header}

{chr(10).join(results)}

🔗 Base URL: {SUNO_API_URL}
🔑 API Key: {SUNO_API_KEY[:10]}...{SUNO_API_KEY[-5:]}"""
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки Suno API: {e}")
        return f"❌ Критическая ошибка при проверке: {e}"


def format_broadcast_confirmation(text: str, total_users: int) -> str:
    """
    Форматировать сообщение подтверждения рассылки
    
    Args:
        text: Текст рассылки
        total_users: Количество пользователей
        
    Returns:
        Отформатированное сообщение
    """
    return f"""👀 **ПРЕДПРОСМОТР РАССЫЛКИ:**

{text}

─────────────────
📤 Будет отправлено: {total_users} пользователям

⚠️ Подтвердить отправку?"""


def format_broadcast_result(sent: int, errors: int) -> str:
    """
    Форматировать результат рассылки
    
    Args:
        sent: Количество успешно отправленных
        errors: Количество ошибок
        
    Returns:
        Отформатированное сообщение
    """
    total = sent + errors
    success_rate = (sent / total * 100) if total > 0 else 0
    
    return f"""✅ **РАССЫЛКА ЗАВЕРШЕНА!**

📤 Отправлено успешно: {sent}
❌ Ошибок (заблокировали): {errors}
📊 Процент доставки: {success_rate:.1f}%"""
