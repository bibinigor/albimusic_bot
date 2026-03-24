with open('final_bot.py', 'r') as f:
    content = f.read()

# Убираем вызов db.init() который больше не существует
content = content.replace("        await db.init()\n        logger.info(\"✅ База данных инициализирована\")", "        logger.info(\"✅ База данных инициализирована через init_postgres()\")")

with open('final_bot.py', 'w') as f:
    f.write(content)

print('✅ Ошибочный вызов db.init() удален')
