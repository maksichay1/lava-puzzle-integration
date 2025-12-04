import os
import requests
import json
import time
import hashlib
from flask import Flask, request, jsonify, redirect
from datetime import datetime

app = Flask(__name__)

# === КОНФИГУРАЦИЯ ===
# Получаем из переменных окружения Railway
LAVA_API_KEY = os.environ.get("LAVA_API_KEY", "mCapu9QDm7OTEmbTQlxXoBcM75ctpRsbZHnkYjNsGVmfzAMt4ihMmft081jYvTB4")
LAVA_EMAIL = os.environ.get("LAVA_EMAIL", "stud.atlant@gmail.com")
LAVA_OFFER_ID = os.environ.get("LAVA_OFFER_ID", "")  # Получить в Lava TOP
PUZZLE_BOT_WEBHOOK = os.environ.get("PUZZLE_BOT_WEBHOOK", "")  # Webhook для выполнения команд
LAVA_API_URL = os.environ.get("LAVA_API_URL", "https://api.lavatop.io")  # URL API Lava TOP

# === In-memory хранилище (для демо) ===
# В продакшене лучше использовать базу данных
payments = {}
orders = {}

# === Логирование ===
def log_payment(user_id, action, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User {user_id}: {action} - {details}\n"
    
    # Логируем в файл
    try:
        with open('payments.log', 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except:
        pass
    
    print(log_entry.strip())

# === Проверка обязательных переменных ===
@app.before_request
def check_config():
    if not LAVA_OFFER_ID:
        return jsonify({"error": "LAVA_OFFER_ID не настроен. Добавьте в переменные окружения Railway"}), 500

# === ГЛАВНАЯ СТРАНИЦА ===
@app.route('/')
def home():
    domain = request.host_url.rstrip('/')
    return f'''
    <html>
    <head>
        <title>🤖 Интеграция Puzzle Bot + Lava TOP</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .card {{ background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .success {{ background: #d4edda; }}
            .error {{ background: #f8d7da; }}
            code {{ background: #333; color: #fff; padding: 2px 5px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>🚀 Интеграция Puzzle Bot + Lava TOP</h1>
        <p>Сервер успешно работает на Railway!</p>
        
        <div class="card">
            <h3>📊 Статистика</h3>
            <p>Создано платежей: {len(payments)}</p>
            <p>Успешных заказов: {sum(1 for p in orders.values() if p.get('status') == 'success')}</p>
        </div>
        
        <div class="card">
            <h3>🔗 Ваши ссылки для кнопок:</h3>
            <p>Для кнопки 1:</p>
            <code>{domain}/pay?user_id=USER_ID&button=place1</code>
            
            <p>Для кнопки 2:</p>
            <code>{domain}/pay?user_id=USER_ID&button=place2</code>
            
            <p><small>Замените USER_ID на реальный ID пользователя Telegram</small></p>
        </div>
        
        <div class="card">
            <h3>🌐 Вебхук для Lava TOP:</h3>
            <code>{domain}/webhook/lavatop</code>
            <p>Скопируйте этот URL и настройте в личном кабинете Lava TOP</p>
        </div>
        
        <div class="card">
            <h3>✅ Проверка работы:</h3>
            <p><a href="/pay?user_id=test123&button=place1" target="_blank">Тестовый платеж</a></p>
            <p><a href="/admin/orders" target="_blank">Посмотреть заказы</a></p>
        </div>
    </body>
    </html>
    '''

# === СТРАНИЦА ОПЛАТЫ ===
@app.route('/pay')
def pay_page():
    user_id = request.args.get('user_id', '')
    button_type = request.args.get('button', 'place1')
    
    if not user_id:
        return "Ошибка: не указан user_id", 400
    
    # Сохраняем информацию о платеже
    order_id = f"puzzle_{user_id}_{int(time.time())}"
    orders[order_id] = {
        "user_id": user_id,
        "button": button_type,
        "status": "created",
        "created_at": time.time(),
        "order_id": order_id
    }
    
    log_payment(user_id, "payment_page", f"Страница оплаты для кнопки {button_type}")
    
    return f'''
    <html>
    <head>
        <title>Оплата места - 999₽</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }}
            .btn {{ background: #0088cc; color: white; border: none; padding: 15px 30px; font-size: 18px; 
                    border-radius: 10px; cursor: pointer; margin: 20px 0; display: inline-block; text-decoration: none; }}
            .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h2>💳 Оплата места за 999₽</h2>
        
        <div class="info">
            <p>ID пользователя: <strong>{user_id}</strong></p>
            <p>Тип: <strong>{button_type}</strong></p>
        </div>
        
        <p>Нажмите кнопку ниже для создания платежа</p>
        
        <a href="/create_payment?order_id={order_id}" class="btn">
            🚀 Создать платеж
        </a>
        
        <div style="margin-top: 30px; font-size: 14px; color: #666;">
            <p>После оплаты вы автоматически получите доступ</p>
        </div>
        
        <script>
            // Автоматическое создание платежа при загрузке (опционально)
            // setTimeout(() => {{ window.location.href = "/create_payment?order_id={order_id}"; }}, 2000);
        </script>
    </body>
    </html>
    '''

# === СОЗДАНИЕ ПЛАТЕЖА В LAVA TOP ===
@app.route('/create_payment')
def create_payment():
    order_id = request.args.get('order_id')
    
    if not order_id or order_id not in orders:
        return "Ошибка: неверный order_id", 400
    
    order = orders[order_id]
    user_id = order["user_id"]
    button_type = order["button"]
    
    # Подготовка данных для Lava TOP API
    payload = {
        "email": LAVA_EMAIL,
        "offerId": LAVA_OFFER_ID,
        "amount": 999,
        "currency": "RUB",
        "orderId": order_id,
        "customFields": {
            "user_id": user_id,
            "button_type": button_type,
            "bot": "puzzlebot"
        },
        "successUrl": f"{request.host_url}success?order_id={order_id}",
        "failUrl": f"{request.host_url}fail?order_id={order_id}"
    }
    
    headers = {
        "Authorization": f"Bearer {LAVA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    log_payment(user_id, "create_payment", f"Отправка в Lava TOP: {json.dumps(payload)}")
    
    try:
        # Отправляем запрос в Lava TOP
        # Уточните точный endpoint у поддержки Lava TOP
        response = requests.post(
            f"{LAVA_API_URL}/v1/payment/create",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response_data = response.json()
        log_payment(user_id, "lava_response", f"Статус: {response.status_code}, Ответ: {json.dumps(response_data)}")
        
        if response.status_code == 200:
            if response_data.get("success") or "paymentUrl" in response_data:
                payment_url = response_data.get("paymentUrl") or response_data.get("url")
                
                # Сохраняем информацию о платеже
                payments[order_id] = {
                    **order,
                    "payment_url": payment_url,
                    "lava_response": response_data,
                    "status": "redirecting_to_payment"
                }
                
                orders[order_id]["status"] = "payment_created"
                orders[order_id]["payment_url"] = payment_url
                
                # Перенаправляем на страницу оплаты
                return redirect(payment_url)
            else:
                return f'''
                <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h3>❌ Ошибка при создании платежа</h3>
                    <p>Ответ от Lava TOP: {json.dumps(response_data)}</p>
                    <p><a href="/pay?user_id={user_id}&button={button_type}">Попробовать снова</a></p>
                </body>
                </html>
                '''
        else:
            return f"Ошибка Lava TOP: {response.status_code} - {response.text}", 500
            
    except Exception as e:
        log_payment(user_id, "create_payment_error", str(e))
        return f"Ошибка при создании платежа: {str(e)}", 500

# === ВЕБХУК ОТ LAVA TOP ===
@app.route('/webhook/lavatop', methods=['POST'])
def lavatop_webhook():
    try:
        data = request.get_json()
        
        # Логируем полученный вебхук
        log_payment("system", "webhook_received", json.dumps(data))
        
        # Сохраняем вебхук в файл для отладки
        try:
            with open('webhooks.log', 'a', encoding='utf-8') as f:
                f.write(f"\n{datetime.now().isoformat()}: {json.dumps(data, indent=2)}\n")
        except:
            pass
        
        # Извлекаем данные из вебхука
        order_id = data.get('orderId') or data.get('order_id')
        status = data.get('status')
        amount = data.get('amount')
        custom_fields = data.get('customFields') or data.get('custom_fields', {})
        user_id = custom_fields.get('user_id')
        button_type = custom_fields.get('button_type', 'place1')
        
        if not order_id:
            return jsonify({"success": False, "error": "No order_id"}), 400
        
        # Обновляем статус заказа
        if order_id in orders:
            orders[order_id]["status"] = status
            orders[order_id]["updated_at"] = time.time()
            orders[order_id]["webhook_data"] = data
            
            # Если платеж успешен
            if status in ['success', 'completed', 'paid']:
                log_payment(user_id, "payment_success", f"Заказ {order_id} оплачен")
                
                # Отправляем вебхук в Puzzle Bot
                if PUZZLE_BOT_WEBHOOK:
                    try:
                        puzzle_payload = {
                            "user_id": user_id,
                            "order_id": order_id,
                            "button_type": button_type,
                            "amount": amount,
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        puzzle_response = requests.post(
                            PUZZLE_BOT_WEBHOOK,
                            json=puzzle_payload,
                            timeout=5
                        )
                        
                        log_payment(user_id, "puzzle_webhook_sent", 
                                  f"Статус: {puzzle_response.status_code}, Ответ: {puzzle_response.text}")
                        
                    except Exception as e:
                        log_payment(user_id, "puzzle_webhook_error", str(e))
        
        return jsonify({"success": True, "message": "Webhook processed"}), 200
        
    except Exception as e:
        log_payment("system", "webhook_error", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# === СТРАНИЦА УСПЕХА ===
@app.route('/success')
def success_page():
    order_id = request.args.get('order_id')
    
    if order_id in orders:
        orders[order_id]["status"] = "success_page_shown"
    
    return '''
    <html>
    <head>
        <title>✅ Оплата прошла успешно!</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }
            .success { color: #28a745; font-size: 48px; }
        </style>
    </head>
    <body>
        <div class="success">✅</div>
        <h2>Оплата прошла успешно!</h2>
        <p>Спасибо за оплату. Ваш доступ будет активирован в течение нескольких минут.</p>
        <p>Вы можете вернуться в бот и продолжить использование.</p>
    </body>
    </html>
    '''

# === СТРАНИЦА ОШИБКИ ===
@app.route('/fail')
def fail_page():
    order_id = request.args.get('order_id')
    
    if order_id in orders:
        orders[order_id]["status"] = "failed_page_shown"
    
    return '''
    <html>
    <head>
        <title>❌ Ошибка оплаты</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }
            .error { color: #dc3545; font-size: 48px; }
        </style>
    </head>
    <body>
        <div class="error">❌</div>
        <h2>Ошибка оплаты</h2>
        <p>При обработке платежа произошла ошибка.</p>
        <p>Пожалуйста, попробуйте еще раз или обратитесь в поддержку.</p>
    </body>
    </html>
    '''

# === АДМИН-ПАНЕЛЬ ===
@app.route('/admin/orders')
def admin_orders():
    # Простая проверка (в продакшене нужна реальная аутентификация)
    password = request.args.get('password')
    if password != os.environ.get("ADMIN_PASSWORD", "admin123"):
        return "Доступ запрещен", 403
    
    html = '''
    <html>
    <head>
        <title>Админ-панель</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .success { color: green; }
            .pending { color: orange; }
            .failed { color: red; }
        </style>
    </head>
    <body>
        <h1>Заказы</h1>
        <table>
            <tr>
                <th>Order ID</th>
                <th>User ID</th>
                <th>Кнопка</th>
                <th>Статус</th>
                <th>Время создания</th>
            </tr>
    '''
    
    for order_id, order in orders.items():
        status_class = {
            'success': 'success',
            'completed': 'success',
            'paid': 'success',
            'failed': 'failed'
        }.get(order.get('status'), 'pending')
        
        time_str = time.ctime(order.get('created_at', 0))
        
        html += f'''
        <tr>
            <td>{order_id[:20]}...</td>
            <td>{order.get('user_id', 'N/A')}</td>
            <td>{order.get('button', 'N/A')}</td>
            <td class="{status_class}">{order.get('status', 'unknown')}</td>
            <td>{time_str}</td>
        </tr>
        '''
    
    html += '''
        </table>
        <p>Всего заказов: ''' + str(len(orders)) + '''</p>
    </body>
    </html>
    '''
    
    return html

# === HEALTH CHECK ===
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orders_count": len(orders)
    })

# === ЗАПУСК СЕРВЕРА ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
