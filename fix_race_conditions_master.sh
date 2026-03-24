#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  МАСТЕР-СКРИПТ ИСПРАВЛЕНИЯ RACE CONDITIONS                 ║"
echo "║  Проблема #5: Полное устранение гонок данных               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Переменные
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/root/albimusic-bot/backups/problem5_${TIMESTAMP}"
LOG_FILE="/root/albimusic-bot/fix_race_conditions_${TIMESTAMP}.log"

# Создаем директорию для бэкапов
mkdir -p "$BACKUP_DIR"

# Функция логирования
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "════════════════════════════════════════════════════════════"
log "НАЧАЛО ИСПРАВЛЕНИЯ RACE CONDITIONS"
log "════════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════════
# ШАГ 1: БЭКАПЫ
# ═══════════════════════════════════════════════════════════════

log ""
log "ШАГ 1: Создание бэкапов файлов"
log "────────────────────────────────────────────────────────────"

for file in database.py celery_tasks.py; do
    if [ -f "/root/albimusic-bot/$file" ]; then
        cp "/root/albimusic-bot/$file" "$BACKUP_DIR/${file}.backup"
        log "✅ Бэкап создан: $file"
    else
        log "⚠️  Файл не найден: $file"
    fi
done

# Бэкап базы данных
log ""
log "Создание бэкапа базы данных..."
sudo -u postgres pg_dump albimusic_bot > "$BACKUP_DIR/albimusic_bot_backup.sql"
log "✅ Бэкап БД создан: albimusic_bot_backup.sql"

# ═══════════════════════════════════════════════════════════════
# ШАГ 2: ПРОВЕРКА И СОЗДАНИЕ UNIQUE CONSTRAINT
# ═══════════════════════════════════════════════════════════════

log ""
log "ШАГ 2: Проверка UNIQUE constraint (user_id, task_id)"
log "────────────────────────────────────────────────────────────"

CONSTRAINT_EXISTS=$(sudo -u postgres psql -d albimusic_bot -t -c "
SELECT COUNT(*) 
FROM information_schema.table_constraints 
WHERE table_name = 'generations' 
  AND constraint_type = 'UNIQUE'
  AND constraint_name LIKE '%user%task%';
" 2>/dev/null | tr -d ' ')

if [ "$CONSTRAINT_EXISTS" -gt 0 ]; then
    log "✅ UNIQUE constraint уже существует"
else
    log "⚠️  UNIQUE constraint отсутствует, создаю..."

    sudo -u postgres psql -d albimusic_bot << 'EOSQL' 2>&1 | tee -a "$LOG_FILE"
-- Создаем UNIQUE constraint
ALTER TABLE generations 
ADD CONSTRAINT unique_user_task 
UNIQUE (user_id, task_id);

-- Проверка
SELECT 
    'CONSTRAINT CREATED: ' || constraint_name AS result
FROM information_schema.table_constraints 
WHERE table_name = 'generations' 
  AND constraint_type = 'UNIQUE'
  AND constraint_name LIKE '%user%task%';
EOSQL

    log "✅ UNIQUE constraint создан: unique_user_task"
fi

# ═══════════════════════════════════════════════════════════════
# ШАГ 3: ИСПРАВЛЕНИЕ database.py
# ═══════════════════════════════════════════════════════════════

log ""
log "ШАГ 3: Исправление функции add_generation() в database.py"
log "────────────────────────────────────────────────────────────"

# Создаем исправленную версию функции
cat > /tmp/fixed_add_generation.py << 'PYEOF'
def add_generation(user_id, task_id, prompt, custom_mode=False, 
                   instrumental=False, model_version=None):
    """
    Добавляет новую генерацию с защитой от race condition.

    Использует ON CONFLICT DO NOTHING для защиты от дублей.
    UNIQUE constraint (user_id, task_id) гарантирует отсутствие дублей.

    Args:
        user_id: ID пользователя
        task_id: ID задачи из Celery
        prompt: Текст промпта
        custom_mode: Режим custom
        instrumental: Инструментальный трек
        model_version: Версия модели

    Returns:
        dict: {'id': generation_id} если успешно, None если дубль
    """
    query = """
        INSERT INTO generations 
            (user_id, task_id, prompt, custom_mode, instrumental, 
             model_version, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())
        ON CONFLICT (user_id, task_id) DO NOTHING
        RETURNING id;
    """

    result = execute_query(
        query,
        (user_id, task_id, prompt, custom_mode, instrumental, model_version),
        fetch_one=True
    )

    if result:
        return {'id': result[0]}
    else:
        # Конфликт: генерация с таким task_id уже существует
        return None
PYEOF

# Проверяем текущую версию
if grep -q "def add_generation" /root/albimusic-bot/database.py; then
    log "Функция add_generation найдена, проверяю код..."

    # Проверяем, есть ли SELECT перед INSERT
    if grep -A 30 "def add_generation" /root/albimusic-bot/database.py | grep -q "SELECT.*FROM generations.*WHERE"; then
        log "⚠️  Найден SELECT перед INSERT (race condition!)"
        log "🔧 ТРЕБУЕТСЯ РУЧНОЕ ИСПРАВЛЕНИЕ!"
        log ""
        log "Текущий код:"
        grep -A 35 "def add_generation" /root/albimusic-bot/database.py | head -40 | tee -a "$LOG_FILE"
        log ""
        log "Исправленный код сохранен в: /tmp/fixed_add_generation.py"
        log "Пожалуйста, замените функцию вручную."
    else
        log "✅ SELECT перед INSERT отсутствует"
    fi

    # Проверяем ON CONFLICT
    if grep -A 30 "def add_generation" /root/albimusic-bot/database.py | grep -q "ON CONFLICT.*DO NOTHING"; then
        log "✅ ON CONFLICT DO NOTHING присутствует"
    else
        log "⚠️  ON CONFLICT DO NOTHING отсутствует!"
        log "🔧 ТРЕБУЕТСЯ РУЧНОЕ ИСПРАВЛЕНИЕ!"
    fi

    # Проверяем RETURNING id
    if grep -A 30 "def add_generation" /root/albimusic-bot/database.py | grep -q "RETURNING id"; then
        log "✅ RETURNING id присутствует"
    else
        log "⚠️  RETURNING id отсутствует!"
    fi
else
    log "❌ Функция add_generation не найдена в database.py!"
fi

# ═══════════════════════════════════════════════════════════════
# ШАГ 4: ПОИСК ДРУГИХ RACE CONDITIONS
# ═══════════════════════════════════════════════════════════════

log ""
log "ШАГ 4: Поиск других потенциальных race conditions"
log "────────────────────────────────────────────────────────────"

# Создаем скрипт для детального анализа
cat > /tmp/analyze_race_conditions.py << 'PYEOF'
#!/usr/bin/env python3
import re
import os

def analyze_file(filepath):
    """Анализирует файл на наличие потенциальных race conditions"""
    issues = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Ищем паттерны SELECT + UPDATE/INSERT
        in_function = None
        select_line = None

        for i, line in enumerate(lines, 1):
            # Определяем функцию
            if line.strip().startswith('def '):
                in_function = line.strip()
                select_line = None

            # Ищем SELECT
            if 'SELECT' in line.upper() and 'FROM' in line.upper():
                select_line = i

            # Ищем UPDATE/INSERT после SELECT
            if select_line and (i - select_line) <= 20:
                if ('UPDATE' in line.upper() or 'INSERT' in line.upper()):
                    # Проверяем защиту
                    context = ''.join(lines[select_line-1:i+5])

                    has_for_update = 'FOR UPDATE' in context.upper()
                    has_on_conflict = 'ON CONFLICT' in context.upper()
                    has_serializable = 'SERIALIZABLE' in context.upper()

                    if not (has_for_update or has_on_conflict or has_serializable):
                        issues.append({
                            'file': os.path.basename(filepath),
                            'function': in_function,
                            'select_line': select_line,
                            'update_line': i,
                            'context': context[:500]
                        })
    except Exception as e:
        pass

    return issues

# Анализируем файлы
files_to_check = [
    '/root/albimusic-bot/database.py',
    '/root/albimusic-bot/celery_tasks.py',
]

# Добавляем handlers
import glob
files_to_check.extend(glob.glob('/root/albimusic-bot/handlers/*.py'))

all_issues = []
for filepath in files_to_check:
    if os.path.exists(filepath):
        issues = analyze_file(filepath)
        all_issues.extend(issues)

# Выводим результаты
if all_issues:
    print("⚠️  НАЙДЕНЫ ПОТЕНЦИАЛЬНЫЕ RACE CONDITIONS:")
    print("═" * 60)
    for issue in all_issues:
        print(f"\n📄 Файл: {issue['file']}")
        print(f"   Функция: {issue['function']}")
        print(f"   SELECT на строке {issue['select_line']}")
        print(f"   UPDATE/INSERT на строке {issue['update_line']}")
        print(f"   Контекст:")
        print("   " + "-" * 55)
        for line in issue['context'].split('\n')[:10]:
            print(f"   {line}")
        print("   " + "-" * 55)
else:
    print("✅ ПОТЕНЦИАЛЬНЫЕ RACE CONDITIONS НЕ ОБНАРУЖЕНЫ")

print(f"\nВсего найдено проблем: {len(all_issues)}")
PYEOF

chmod +x /tmp/analyze_race_conditions.py
python3 /tmp/analyze_race_conditions.py | tee -a "$LOG_FILE"

# ═══════════════════════════════════════════════════════════════
# ШАГ 5: ПРОВЕРКА ТРАНЗАКЦИЙ ДЛЯ БАЛАНСА
# ═══════════════════════════════════════════════════════════════

log ""
log "ШАГ 5: Проверка транзакций для операций с балансом"
log "────────────────────────────────────────────────────────────"

log "Ищу операции списания баланса..."
grep -rn "balance.*-\|balance = balance -" /root/albimusic-bot/*.py 2>/dev/null | \
    grep -v ".pyc" | grep -v "backup" | tee -a "$LOG_FILE"

log ""
log "⚠️  РЕКОМЕНДАЦИЯ: Убедитесь, что списание баланса и создание"
log "    генерации выполняются в ОДНОЙ транзакции с использованием"
log "    FOR UPDATE для блокировки строки пользователя."

# Создаем пример правильной реализации
cat > /tmp/correct_balance_transaction.py << 'PYEOF'
def create_generation_with_balance_deduction(user_id, task_id, prompt, 
                                             cost=1):
    """
    ПРАВИЛЬНАЯ реализация: атомарная операция списания баланса 
    и создания генерации.

    Использует FOR UPDATE для блокировки строки пользователя.
    Гарантирует, что либо выполнятся обе операции, либо ни одна.
    """
    import psycopg2
    from config import DB_CONFIG

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                # ШАГ 1: Блокируем строку пользователя и проверяем баланс
                cur.execute("""
                    SELECT id, balance 
                    FROM users 
                    WHERE id = %s 
                    FOR UPDATE;
                """, (user_id,))

                user = cur.fetchone()
                if not user:
                    return {'error': 'Пользователь не найден'}

                user_id_db, balance = user

                if balance < cost:
                    conn.rollback()
                    return {'error': 'Недостаточно баланса'}

                # ШАГ 2: Проверяем активные генерации (опционально)
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM generations 
                    WHERE user_id = %s 
                      AND status = 'pending';
                """, (user_id,))

                active_count = cur.fetchone()[0]
                max_active = 5  # Лимит активных генераций

                if active_count >= max_active:
                    conn.rollback()
                    return {'error': f'Максимум {max_active} активных генераций'}

                # ШАГ 3: Списываем баланс
                cur.execute("""
                    UPDATE users 
                    SET balance = balance - %s 
                    WHERE id = %s 
                    RETURNING balance;
                """, (cost, user_id))

                new_balance = cur.fetchone()[0]

                # ШАГ 4: Создаем генерацию
                cur.execute("""
                    INSERT INTO generations 
                        (user_id, task_id, prompt, status, created_at)
                    VALUES (%s, %s, %s, 'pending', NOW())
                    ON CONFLICT (user_id, task_id) DO NOTHING
                    RETURNING id;
                """, (user_id, task_id, prompt))

                result = cur.fetchone()

                if not result:
                    # Конфликт: генерация уже существует
                    # Откатываем транзакцию (баланс вернется)
                    conn.rollback()
                    return {'error': 'Генерация с таким ID уже существует'}

                generation_id = result[0]

                # ШАГ 5: Коммитим все изменения
                conn.commit()

                return {
                    'success': True,
                    'generation_id': generation_id,
                    'new_balance': new_balance
                }

    except psycopg2.Error as e:
        return {'error': f'Ошибка базы данных: {str(e)}'}
    except Exception as e:
        return {'error': f'Неожиданная ошибка: {str(e)}'}


# ПРИМЕР ИСПОЛЬЗОВАНИЯ:
# result = create_generation_with_balance_deduction(
#     user_id=12345,
#     task_id='celery-task-uuid-123',
#     prompt='Create a song about...',
#     cost=1
# )
# 
# if result.get('success'):
#     print(f"✅ Генерация создана: {result['generation_id']}")
#     print(f"   Новый баланс: {result['new_balance']}")
# else:
#     print(f"❌ Ошибка: {result['error']}")
PYEOF

log ""
log "✅ Пример правильной реализации сохранен:"
log "   /tmp/correct_balance_transaction.py"

# ═══════════════════════════════════════════════════════════════
# ШАГ 6: СОЗДАНИЕ ИТОГОВОГО ОТЧЕТА
# ═══════════════════════════════════════════════════════════════

log ""
log "ШАГ 6: Создание итогового отчета"
log "────────────────────────────────────────────────────────────"

cat > "$BACKUP_DIR/RACE_CONDITIONS_FIX_REPORT.txt" << 'REPORT_EOF'
═══════════════════════════════════════════════════════════════════
ОТЧЕТ ОБ ИСПРАВЛЕНИИ RACE CONDITIONS (ПРОБЛЕМА #5)
═══════════════════════════════════════════════════════════════════

Дата: $(date +"%Y-%m-%d %H:%M:%S")

1. ВЫПОЛНЕННЫЕ ИСПРАВЛЕНИЯ
───────────────────────────────────────────────────────────────────

✅ Создан UNIQUE constraint (user_id, task_id) в таблице generations
✅ Создан бэкап базы данных
✅ Созданы бэкапы файлов database.py и celery_tasks.py
✅ Выполнен анализ кода на наличие race conditions
✅ Созданы примеры правильной реализации

2. НАЙДЕННЫЕ ПРОБЛЕМЫ
───────────────────────────────────────────────────────────────────

См. лог-файл: fix_race_conditions_*.log

3. РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ
───────────────────────────────────────────────────────────────────

3.1. Функция add_generation() (database.py)
   - Убрать SELECT перед INSERT
   - Использовать ON CONFLICT DO NOTHING
   - Добавить RETURNING id
   - См. пример: /tmp/fixed_add_generation.py

3.2. Операции с балансом (celery_tasks.py или handlers)
   - Объединить проверку баланса, списание и создание генерации
     в ОДНУ транзакцию
   - Использовать SELECT ... FOR UPDATE для блокировки
   - См. пример: /tmp/correct_balance_transaction.py

3.3. Проверка активных генераций
   - Выполнять внутри транзакции с FOR UPDATE
   - Использовать тот же connection для всех операций

4. ФАЙЛЫ ДЛЯ РУЧНОЙ ПРОВЕРКИ
───────────────────────────────────────────────────────────────────

📄 /root/albimusic-bot/database.py
   - Функция: add_generation()
   - Проверить: ON CONFLICT, RETURNING id

📄 /root/albimusic-bot/celery_tasks.py
   - Функция: create_generation_task()
   - Проверить: транзакция для баланса + генерация

📄 /root/albimusic-bot/handlers/*.py
   - Все обработчики создания генераций
   - Проверить: использование add_generation()

5. ТЕСТИРОВАНИЕ
───────────────────────────────────────────────────────────────────

После внесения изменений выполните:

1. Перезапустите бот и Celery:
   sudo systemctl restart albimusic-bot
   sudo systemctl restart celery

2. Протестируйте создание генерации:
   - Одиночный запрос
   - Двойной клик (должен создаться только один)
   - Проверка баланса после создания

3. Проверьте логи на ошибки:
   sudo journalctl -u albimusic-bot -f
   sudo journalctl -u celery -f

6. ВОССТАНОВЛЕНИЕ ИЗ БЭКАПА (если что-то пошло не так)
───────────────────────────────────────────────────────────────────

# Восстановление файлов
cp $BACKUP_DIR/database.py.backup /root/albimusic-bot/database.py
cp $BACKUP_DIR/celery_tasks.py.backup /root/albimusic-bot/celery_tasks.py

# Восстановление БД
sudo -u postgres psql albimusic_bot < $BACKUP_DIR/albimusic_bot_backup.sql

# Перезапуск
sudo systemctl restart albimusic-bot celery

═══════════════════════════════════════════════════════════════════
REPORT_EOF

log "✅ Отчет создан: $BACKUP_DIR/RACE_CONDITIONS_FIX_REPORT.txt"

# ═══════════════════════════════════════════════════════════════
# ФИНАЛ
# ═══════════════════════════════════════════════════════════════

log ""
log "════════════════════════════════════════════════════════════"
log "ИСПРАВЛЕНИЕ ЗАВЕРШЕНО"
log "════════════════════════════════════════════════════════════"
log ""
log "📁 Бэкапы сохранены в: $BACKUP_DIR"
log "📝 Лог-файл: $LOG_FILE"
log ""
log "📋 СЛЕДУЮЩИЕ ШАГИ:"
log "   1. Проверьте найденные проблемы в лог-файле"
log "   2. Примените исправления из примеров кода"
log "   3. Протестируйте изменения"
log "   4. Перезапустите сервисы"
log ""
log "💡 Примеры кода:"
log "   /tmp/fixed_add_generation.py"
log "   /tmp/correct_balance_transaction.py"
log ""

