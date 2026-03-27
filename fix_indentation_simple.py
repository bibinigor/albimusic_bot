    def handle_message(self, event):
        """Обработчик входящих сообщений"""
        user_id = event.user_id
        text = event.text if event.text else ""
        text_lower = text.lower()  # Приводим к нижнему регистру сразу