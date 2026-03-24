with open('run_monitor_pro.py', 'r') as f:
    content = f.read()

# Заменяем проблемный метод init_db
old_init_db = '''    async def init_db(self):
        """Инициализация БД один раз"""
        if not self.db_initialized:
            from db_utils import execute_query_sync
            await db.init()
            self.db = db
            self.db_initialized = True'''

new_init_db = '''    async def init_db(self):
        """Инициализация БД один раз"""
        if not self.db_initialized:
            from db_utils import execute_query_sync, get_db_pool_sync, init_db_pool_sync
            init_db_pool_sync()
            self.db_initialized = True'''

content = content.replace(old_init_db, new_init_db)

# Заменяем использование db на execute_query_sync
content = content.replace('await self.db.fetch_query', 'execute_query_sync')
content = content.replace('self.db.execute_query', 'execute_query_sync')

with open('run_monitor_pro.py', 'w') as f:
    f.write(content)

print('✅ Мониторинг исправлен')
