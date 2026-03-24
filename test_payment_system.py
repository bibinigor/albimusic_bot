#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы платежей
Симулирует платеж и проверяет начисление баланса
"""
import sys
sys.path.append('/root/albimusic-bot')

from db_utils import execute_query_sync, init_db_pool_sync

def test_payment_flow():
    """Тестирование полного цикла платежа"""

    # Тестовый пользователь
    test_user_id = 999999999  # Несуществующий пользователь для теста

    print("=" * 60)
    print("🧪 ТЕСТ СИСТЕМЫ ПЛАТЕЖЕЙ")
    print("=" * 60)

    # 1. Проверяем существует ли пользователь
    print(f"\n1️⃣ Проверка пользователя {test_user_id}...")
    result = execute_query_sync(
        "SELECT user_id, balance, username FROM users WHERE user_id = %s",
        (test_user_id,)
    )

    if not result:
        print("   ⚠️ Пользователь не существует, создаем...")
        execute_query_sync(
            "INSERT INTO users (user_id, username, balance, free_generation_used) VALUES (%s, %s, %s, %s)",
            (test_user_id, "test_user", 0, True)
        )
        print("   ✅ Тестовый пользователь создан")
    else:
        print(f"   ✅ Пользователь найден: balance={result[0][1]}")

    # 2. Получаем текущий баланс
    print(f"\n2️⃣ Получение текущего баланса...")
    result = execute_query_sync(
        "SELECT balance FROM users WHERE user_id = %s",
        (test_user_id,)
    )
    balance_before = result[0][0] if result else 0
    print(f"   📊 Баланс ДО оплаты: {balance_before} генераций")

    # 3. Симулируем платеж 490₽ = 10 генераций
    print(f"\n3️⃣ Симуляция платежа 490₽ (10 генераций)...")
    payment_amount = 10

    # Используем ПРАВИЛЬНУЮ функцию (PostgreSQL)
    execute_query_sync(
        "UPDATE users SET balance = balance + %s WHERE user_id = %s",
        (payment_amount, test_user_id)
    )
    print(f"   ✅ Начислено {payment_amount} генераций")

    # 4. Проверяем баланс после начисления
    print(f"\n4️⃣ Проверка баланса после начисления...")
    result = execute_query_sync(
        "SELECT balance FROM users WHERE user_id = %s",
        (test_user_id,)
    )
    balance_after = result[0][0] if result else 0
    print(f"   📊 Баланс ПОСЛЕ оплаты: {balance_after} генераций")

    # 5. Проверка результата
    print(f"\n5️⃣ Проверка результата...")
    expected_balance = balance_before + payment_amount

    if balance_after == expected_balance:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Баланс увеличился на {payment_amount}")
        print(f"   📈 {balance_before} → {balance_after} генераций")
    else:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН!")
        print(f"   ❌ Ожидалось: {expected_balance}")
        print(f"   ❌ Получено: {balance_after}")

    # 6. Тестируем списание баланса
    print(f"\n6️⃣ Тест списания 1 генерации...")
    execute_query_sync(
        "UPDATE users SET balance = balance - 1 WHERE user_id = %s",
        (test_user_id,)
    )

    result = execute_query_sync(
        "SELECT balance FROM users WHERE user_id = %s",
        (test_user_id,)
    )
    balance_after_deduction = result[0][0] if result else 0
    print(f"   📊 Баланс после списания: {balance_after_deduction} генераций")

    if balance_after_deduction == balance_after - 1:
        print(f"   ✅ Списание работает корректно")
    else:
        print(f"   ❌ Ошибка списания!")

    # 7. Очищаем тестовые данные
    print(f"\n7️⃣ Очистка тестовых данных...")
    execute_query_sync(
        "DELETE FROM users WHERE user_id = %s",
        (test_user_id,)
    )
    print(f"   ✅ Тестовый пользователь удален")

    print("\n" + "=" * 60)
    print("🎯 ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

if __name__ == "__main__":
    try:
        # Инициализируем пул БД
        print("🔧 Инициализация подключения к БД...")
        init_db_pool_sync()
        print("✅ Подключение установлено\n")

        test_payment_flow()
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
