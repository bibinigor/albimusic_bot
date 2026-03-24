with open('postgres_db.py', 'r') as f:
    content = f.read()

# Заменяем пароль на правильный
content = content.replace(
    'POSTGRES_DSN = f"postgresql://albimusic_user:albimusic123@localhost/albimusic_bot"',
    'POSTGRES_DSN = f"postgresql://albimusic_user:aXAnAixKT6@?B9@localhost/albimusic_bot"'
)

with open('postgres_db.py', 'w') as f:
    f.write(content)

print('✅ Пароль PostgreSQL исправлен')
