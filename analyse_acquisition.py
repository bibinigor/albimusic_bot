#!/usr/bin/env python3
"""
📊 Аналитика источников привлечения пользователей
==================================================
Отвечает на вопрос: новые пользователи приходят сами (реклама/органика)
или через реферальную программу "Пригласи друга"?

Запуск: python3 analyse_acquisition.py
"""

import psycopg2
from datetime import datetime

# ─── Подключение к БД ────────────────────────────────────────────────────────
conn = psycopg2.connect(
    dbname='albimusic_bot',
    user='albimusic_user',
    password='aXAnAixKT6@?B9',
    host='localhost'
)
cur = conn.cursor()

SEP  = '=' * 72
SEP2 = '-' * 72

def header(title):
    print()
    print(SEP)
    print(f'  {title}')
    print(SEP)

def subheader(title):
    print()
    print(f'  {title}')
    print(SEP2)


# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 1 — Общая разбивка: реферал vs органика
# ═══════════════════════════════════════════════════════════════════════════════
header('БЛОК 1 — ОБЩАЯ РАЗБИВКА: РЕФЕРАЛ vs ОРГАНИКА')

cur.execute("""
    SELECT
        CASE WHEN invited_by IS NULL THEN 'Органика (сами пришли)' ELSE 'Реферал (по приглашению)' END AS source,
        COUNT(*)                                                              AS total_users,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days')      AS last_7d,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days')     AS last_30d,
        COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE)                   AS today
    FROM users
    GROUP BY 1
    ORDER BY total_users DESC
""")

rows = cur.fetchall()
total_all = sum(r[1] for r in rows)
total_7d  = sum(r[2] for r in rows)
total_30d = sum(r[3] for r in rows)
total_today = sum(r[4] for r in rows)

print(f"{'Источник':<30} {'Всего':>8} {'%':>6} {'30 дн':>8} {'7 дн':>8} {'Сегодня':>9}")
print(SEP2)
for source, total, last_7d, last_30d, today in rows:
    pct = total * 100.0 / total_all if total_all else 0
    print(f"{source:<30} {total:>8} {pct:>5.1f}% {last_30d:>8} {last_7d:>8} {today:>9}")
print(SEP2)
print(f"{'ИТОГО':<30} {total_all:>8} {'100%':>6} {total_30d:>8} {total_7d:>8} {total_today:>9}")

# Краткий вывод
organic_row  = next((r for r in rows if 'Органика' in r[0]), None)
referral_row = next((r for r in rows if 'Реферал' in r[0]), None)

print()
if referral_row and total_7d > 0:
    ref_pct_7d = referral_row[2] * 100.0 / total_7d
    print(f"  📌 За последние 7 дней реферальных пользователей: {referral_row[2]} из {total_7d} ({ref_pct_7d:.1f}%)")
if organic_row and total_7d > 0:
    org_pct_7d = organic_row[2] * 100.0 / total_7d
    print(f"  📌 За последние 7 дней органических пользователей: {organic_row[2]} из {total_7d} ({org_pct_7d:.1f}%)")


# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 2 — Динамика регистраций по дням (последние 30 дней)
# ═══════════════════════════════════════════════════════════════════════════════
header('БЛОК 2 — ДИНАМИКА РЕГИСТРАЦИЙ ПО ДНЯМ (последние 30 дней)')

cur.execute("""
    SELECT
        DATE(created_at)                                                   AS day,
        COUNT(*) FILTER (WHERE invited_by IS NULL)                         AS organic,
        COUNT(*) FILTER (WHERE invited_by IS NOT NULL)                     AS referral,
        COUNT(*)                                                           AS total
    FROM users
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY day DESC
""")

day_rows = cur.fetchall()

print(f"{'Дата':<12} {'Органика':>10} {'Реферал':>10} {'Итого':>8} {'% Реферал':>11}")
print(SEP2)

for day, organic, referral, total in day_rows:
    ref_pct = referral * 100.0 / total if total else 0
    bar_organic  = '▓' * organic
    bar_referral = '░' * referral
    print(f"{str(day):<12} {organic:>10} {referral:>10} {total:>8} {ref_pct:>10.1f}%  {bar_organic}{bar_referral}")

if day_rows:
    sum_org = sum(r[1] for r in day_rows)
    sum_ref = sum(r[2] for r in day_rows)
    sum_tot = sum(r[3] for r in day_rows)
    print(SEP2)
    print(f"{'ИТОГО за 30д':<12} {sum_org:>10} {sum_ref:>10} {sum_tot:>8}")


# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 3 — Поведение: генерации по группам
# ═══════════════════════════════════════════════════════════════════════════════
header('БЛОК 3 — ПОВЕДЕНИЕ: ГЕНЕРАЦИИ ПО ГРУППАМ')

cur.execute("""
    SELECT
        CASE WHEN u.invited_by IS NULL THEN 'Органика' ELSE 'Реферал' END AS source,
        COUNT(DISTINCT u.user_id)                                          AS users_count,
        COUNT(g.id)                                                        AS total_gens,
        COUNT(g.id) FILTER (WHERE g.status = 'completed')                 AS completed_gens,
        COUNT(DISTINCT g.user_id)                                          AS users_with_gens,
        ROUND(
            COUNT(g.id)::numeric / NULLIF(COUNT(DISTINCT g.user_id), 0), 2
        )                                                                  AS avg_gens_per_active_user,
        ROUND(
            COUNT(g.id)::numeric / NULLIF(COUNT(DISTINCT u.user_id), 0), 2
        )                                                                  AS avg_gens_per_all_user
    FROM users u
    LEFT JOIN generations g ON u.user_id = g.user_id
    GROUP BY 1
    ORDER BY total_gens DESC
""")

gen_rows = cur.fetchall()

print(f"{'Источник':<12} {'Польз.':>8} {'Геnerац.':>10} {'Успешно':>9} "
      f"{'С генер.':>9} {'Ср./актив.':>11} {'Ср./всего':>10}")
print(SEP2)

for source, users_count, total_gens, completed_gens, users_with_gens, avg_active, avg_all in gen_rows:
    has_gens_pct = users_with_gens * 100.0 / users_count if users_count else 0
    print(f"{source:<12} {users_count:>8} {total_gens:>10} {completed_gens:>9} "
          f"{users_with_gens:>8} ({has_gens_pct:.0f}%) {str(avg_active):>10} {str(avg_all):>10}")

print()
print("  Пояснение: 'С генер.' — пользователи, сделавшие хоть 1 генерацию")
print("             'Ср./актив.' — среднее среди тех, кто генерировал")
print("             'Ср./всего'  — среднее по всем пользователям группы")


# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 4 — Конверсия в платящих
# ═══════════════════════════════════════════════════════════════════════════════
header('БЛОК 4 — КОНВЕРСИЯ В ПЛАТЯЩИХ')

cur.execute("""
    SELECT
        CASE WHEN u.invited_by IS NULL THEN 'Органика' ELSE 'Реферал' END AS source,
        COUNT(DISTINCT u.user_id)                                          AS total_users,
        COUNT(DISTINCT p.user_id)                                          AS paid_users,
        ROUND(
            COUNT(DISTINCT p.user_id) * 100.0 / NULLIF(COUNT(DISTINCT u.user_id), 0), 1
        )                                                                  AS conversion_pct,
        COALESCE(SUM(p.amount), 0)                                        AS total_revenue,
        ROUND(
            COALESCE(SUM(p.amount), 0)::numeric / NULLIF(COUNT(DISTINCT p.user_id), 0), 2
        )                                                                  AS avg_check
    FROM users u
    LEFT JOIN payments p ON u.user_id = p.user_id AND p.status = 'succeeded'
    GROUP BY 1
    ORDER BY total_users DESC
""")

pay_rows = cur.fetchall()

print(f"{'Источник':<12} {'Польз.':>8} {'Платили':>9} {'Конверсия':>11} {'Выручка':>10} {'Ср. чек':>9}")
print(SEP2)

for source, total_users, paid_users, conversion_pct, total_revenue, avg_check in pay_rows:
    print(f"{source:<12} {total_users:>8} {paid_users:>9} {str(conversion_pct)+'%':>11} "
          f"{float(total_revenue):>9.0f}р {str(avg_check)+'р':>9}")

print()
print("  📌 Если конверсия рефералов НИЖЕ — они используют только бесплатные токены")
print("     от приглашения и не платят.")
print("  📌 Если конверсия примерно одинакова — реферальный трафик такой же качественный.")


# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 5 — Топ-10 рефереров
# ═══════════════════════════════════════════════════════════════════════════════
header('БЛОК 5 — ТОП-10 РЕФЕРЕРОВ')

cur.execute("""
    SELECT
        u_ref.user_id,
        COALESCE(u_ref.username, '—')                                      AS username,
        COALESCE(u_ref.first_name, '—')                                    AS name,
        COUNT(DISTINCT r.referred_id)                                      AS invited,
        COUNT(DISTINCT g.id)                                               AS gens_by_invited,
        COUNT(DISTINCT p.user_id)                                          AS invited_paid,
        COALESCE(SUM(p.amount), 0)                                        AS invited_revenue,
        u_ref.balance                                                      AS referrer_balance
    FROM referrals r
    JOIN users u_ref ON r.referrer_id = u_ref.user_id
    LEFT JOIN generations g ON r.referred_id = g.user_id
    LEFT JOIN payments p    ON r.referred_id = p.user_id AND p.status = 'succeeded'
    GROUP BY u_ref.user_id, u_ref.username, u_ref.first_name, u_ref.balance
    ORDER BY invited DESC
    LIMIT 10
""")

top_rows = cur.fetchall()

if top_rows:
    print(f"{'User ID':>12} {'@username':<20} {'Имя':<15} "
          f"{'Привёл':>8} {'Генерац.':>10} {'Заплатили':>11} {'Выручка':>10} {'Баланс реф.':>12}")
    print(SEP2)
    for uid, uname, name, invited, gens, paid_cnt, revenue, balance in top_rows:
        uname_fmt = f'@{uname}' if uname != '—' else '—'
        print(f"{uid:>12} {uname_fmt:<20} {name:<15} "
              f"{invited:>8} {gens:>10} {paid_cnt:>11} {float(revenue):>9.0f}р {balance:>12}")
else:
    print("  Нет данных в таблице referrals")


# ═══════════════════════════════════════════════════════════════════════════════
# БЛОК 6 — Сводный ответ на главный вопрос
# ═══════════════════════════════════════════════════════════════════════════════
header('ИТОГОВЫЙ ВЫВОД: ОТКУДА ПРИХОДЯТ НОВЫЕ ПОЛЬЗОВАТЕЛИ?')

# Считаем соотношение за последние 7 дней
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE invited_by IS NULL)     AS organic_7d,
        COUNT(*) FILTER (WHERE invited_by IS NOT NULL) AS referral_7d,
        COUNT(*)                                       AS total_7d
    FROM users
    WHERE created_at >= NOW() - INTERVAL '7 days'
""")
o7, r7, t7 = cur.fetchone()
o7_pct = round(o7 * 100.0 / t7, 1) if t7 else 0
r7_pct = round(r7 * 100.0 / t7, 1) if t7 else 0

print()
print(f"  За последние 7 дней зарегистрировалось {t7} пользователей:")
print(f"    🌐 Органика (реклама/сами нашли): {o7} чел. ({o7_pct}%)")
print(f"    🤝 Реферал  (по приглашению):     {r7} чел. ({r7_pct}%)")
print()
if t7 == 0:
    print("  ⚠️  Нет новых пользователей за 7 дней")
elif r7_pct >= 50:
    print("  ✅ ВЫВОД: Большинство новых пользователей приходит по РЕФЕРАЛЬНЫМ ссылкам.")
    print("     Люди активно пользуются программой 'Пригласи друга'.")
elif r7_pct >= 20:
    print("  ℹ️  ВЫВОД: Реферальная программа даёт заметный вклад, но основной трафик —")
    print("     органический (реклама, прямой поиск, ViralA).")
else:
    print("  ℹ️  ВЫВОД: Большинство пользователей приходит ОРГАНИЧЕСКИ (реклама, поиск).")
    print("     Реферальная программа дала менее 20% новых пользователей за 7 дней.")
print()

# Подсказка: сколько бесплатных токенов "съедено" через рефералы
cur.execute("""
    SELECT COUNT(*) FROM referrals
""")
total_referrals_in_table = cur.fetchone()[0]
print(f"  📊 Всего реферальных связей в таблице referrals: {total_referrals_in_table}")
print(f"     (каждая = +2 токена реферу; итого ~{total_referrals_in_table * 2} бесплатных токена выдано)")

print()
print(SEP)
print(f"  Скрипт выполнен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

cur.close()
conn.close()
