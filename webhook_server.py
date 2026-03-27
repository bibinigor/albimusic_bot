#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook сервер для обработки платежей YooKassa
Можно запускать отдельно или интегрировать в main_vk.py
"""

from flask import Flask, request, jsonify
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Импорт после создания app
try:
    from vk_payments import process_payment_callback
    logger.info("✅ Модуль vk_payments загружен")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта vk_payments: {e}")
    sys.exit(1)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "vk-bot-webhook",
        "version": "1.0.0"
    }), 200


@app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    """
    Обработка webhook от YooKassa
    
    Ожидаемый формат:
    {
        "type": "notification",
        "event": "payment.succeeded",
        "object": {
            "id": "payment_id",
            "status": "succeeded",
            "amount": {"value": "250.00", "currency": "RUB"},
            "metadata": {"user_id": "123456789"}
        }
    }
    """
    try:
        # Получаем данные
        data = request.json
        
        if not data:
            logger.warning("⚠️ Пустой webhook payload")
            return jsonify({"error": "Empty payload"}), 400
        
        logger.info(f"📥 Webhook от YooKassa: {data.get('event', 'unknown')}")
        logger.debug(f"Полные данные: {data}")
        
        # Проверяем тип события
        event = data.get('event')
        if event != 'payment.succeeded':
            logger.info(f"ℹ️ Пропускаем событие: {event}")
            return jsonify({"status": "ok", "message": "Event ignored"}), 200
        
        # Обрабатываем платеж
        import threading
        thread = threading.Thread(
            target=process_payment_callback,
            args=(data,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"✅ Webhook обработан в фоновом потоке")
        
        return jsonify({
            "status": "ok",
            "message": "Payment processing started"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Обработка 404"""
    logger.warning(f"⚠️ 404: {request.path}")
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработка 500"""
    logger.error(f"❌ 500: {error}")
    return jsonify({"error": "Internal server error"}), 500


def main():
    """Запуск webhook сервера"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК WEBHOOK СЕРВЕРА")
    logger.info("=" * 60)
    logger.info("Порт: 8080")
    logger.info("Endpoints:")
    logger.info("  - GET  /health")
    logger.info("  - POST /webhook/yookassa")
    logger.info("=" * 60)
    
    # Запуск сервера
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    main()
