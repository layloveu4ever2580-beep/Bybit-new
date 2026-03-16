import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import threading

import database
from bot_logic import enter_trade, sync_trades
from leverage_config import LEVERAGE_SETTINGS

load_dotenv()

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)

# Serve React App
@app.route('/')
def serve_frontend():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/') or request.path.startswith('/webhook'):
        return jsonify({"status": "error", "message": "Not found"}), 404
    return app.send_static_file('index.html')

# Initialize database
database.init_db()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400
            
        ticker = payload.get("ticker")
        if not ticker or ticker not in LEVERAGE_SETTINGS:
            return jsonify({"status": "error", "message": "Ticker not supported"}), 400
            
        # Run trade execution in a separate thread so webhook returns quickly
        def process_trade(pd):
            result = enter_trade(pd)
            if result.get("success"):
                print(f"Trade executed successfully: {result}")
            else:
                print(f"Trade execution failed: {result}")
                
        thread = threading.Thread(target=process_trade, args=(payload,))
        thread.start()
        
        return jsonify({"status": "success", "message": "Webhook received, processing trade"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = database.get_settings()
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
    target_profit = data.get("target_profit")
    timezone = data.get("timezone")
    theme = data.get("theme")
    
    if target_profit is None or timezone is None or theme is None:
        return jsonify({"status": "error", "message": "Missing fields"}), 400
        
    database.update_settings(target_profit, timezone, theme)
    return jsonify({"status": "success", "message": "Settings updated"})

@app.route('/api/trades', methods=['GET'])
def get_trades():
    trades = database.get_trades()
    return jsonify(trades)

@app.route('/api/trades/<int:trade_id>/target-profit', methods=['PATCH'])
def update_trade_target_profit(trade_id):
    data = request.get_json()
    target_profit = data.get("target_profit")
    if target_profit is None:
        return jsonify({"status": "error", "message": "Missing target_profit"}), 400
        
    database.update_trade(trade_id, target_profit=target_profit)
    return jsonify({"status": "success", "message": "Trade target profit updated"})

@app.route('/api/sync-trades', methods=['POST'])
def sync_trades_endpoint():
    try:
        result = sync_trades()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
