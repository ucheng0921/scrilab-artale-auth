"""
app.py - 完整版本，包含 SimpleSwap 信用卡付款支援和調試功能
"""
from flask import Flask, redirect, request, jsonify, render_template_string
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
from datetime import datetime
import logging
import threading
import schedule
import time as time_module
import requests

# 導入模組
from admin_panel import admin_bp
from manual_routes import manual_bp
from disclaimer_routes import disclaimer_bp
from session_manager import session_manager, init_session_manager
from route_handlers import RouteHandlers
from templates import PROFESSIONAL_PRODUCTS_TEMPLATE, PAYMENT_CANCEL_TEMPLATE
from intro_routes import intro_bp

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 應用初始化
app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY', 'dev-key-change-in-production')

# CORS 配置
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# 全局變數
db = None
firebase_initialized = False
simpleswap_service = None
simpleswap_routes = None
route_handlers = None
initialization_in_progress = False

def check_environment_variables():
    """檢查必要的環境變數"""
    required_vars = ['FIREBASE_CREDENTIALS_BASE64', 'SIMPLESWAP_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ 缺少必要的環境變數: {missing_vars}")
        return False
    
    logger.info("✅ 環境變數檢查通過")
    return True

def init_firebase_with_retry(max_retries=3):
    """改進的 Firebase 初始化，包含重試機制"""
    global db, firebase_initialized, initialization_in_progress
    
    if initialization_in_progress:
        logger.info("Firebase 初始化已在進行中...")
        return firebase_initialized
    
    initialization_in_progress = True
    
    try:
        # 檢查環境變數
        if not check_environment_variables():
            return False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"嘗試初始化 Firebase (第 {attempt + 1}/{max_retries} 次)...")
                
                # 檢查是否已經初始化
                if firebase_admin._apps:
                    logger.info("Firebase 應用已存在，刪除後重新初始化")
                    firebase_admin.delete_app(firebase_admin.get_app())
                
                # 解析憑證
                credentials_base64 = os.environ['FIREBASE_CREDENTIALS_BASE64'].strip()
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                credentials_dict = json.loads(credentials_json)
                
                # 驗證憑證完整性
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not credentials_dict.get(field)]
                
                if missing_fields:
                    logger.error(f"憑證缺少必需字段: {missing_fields}")
                    if attempt == max_retries - 1:
                        return False
                    continue
                
                # 初始化 Firebase
                cred = credentials.Certificate(credentials_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase 應用初始化成功")
                
                # 初始化 Firestore
                db = firestore.client()
                logger.info("Firestore 客戶端創建成功")
                
                # 測試連接
                try:
                    test_collection = db.collection('connection_test')
                    test_doc_ref = test_collection.document('test_connection')
                    
                    # 測試寫入
                    test_doc_ref.set({
                        'timestamp': datetime.now(),
                        'test': True,
                        'message': f'Connection test - attempt {attempt + 1}',
                        'server_time': datetime.now().isoformat()
                    })
                    
                    # 測試讀取
                    test_doc = test_doc_ref.get()
                    if test_doc.exists:
                        logger.info("✅ Firestore 連接測試成功")
                        firebase_initialized = True
                        
                        # 初始化相關服務
                        init_services()
                        
                        logger.info("✅ Firebase 完全初始化成功")
                        return True
                    else:
                        raise Exception("無法讀取測試文檔")
                        
                except Exception as firestore_error:
                    logger.error(f"Firestore 連接測試失敗: {str(firestore_error)}")
                    if attempt == max_retries - 1:
                        raise firestore_error
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Firebase 初始化失敗 (嘗試 {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒後重試...")
                    time_module.sleep(wait_time)
                else:
                    firebase_initialized = False
                    db = None
                    return False
        
        return False
        
    finally:
        initialization_in_progress = False

def init_services():
    """初始化相關服務"""
    global simpleswap_service, simpleswap_routes, route_handlers
    
    try:
        # 初始化 Session Manager
        init_session_manager(db)
        logger.info("✅ Session Manager 已初始化")

        
        # 初始化路由處理器
        route_handlers = RouteHandlers(db, session_manager, simpleswap_service)
        logger.info("✅ Route Handlers 已初始化")
        
        # 啟動後台清理任務
        start_background_tasks()
        
    except Exception as e:
        logger.error(f"❌ 服務初始化失敗: {str(e)}")
        raise

def cleanup_expired_sessions():
    """定期清理過期會話"""
    try:
        if session_manager and firebase_initialized:
            deleted_count = session_manager.cleanup_expired_sessions()
            if deleted_count > 0:
                logger.info(f"🧹 定期清理：刪除了 {deleted_count} 個過期會話")
    except Exception as e:
        logger.error(f"❌ 定期清理失敗: {str(e)}")

def run_background_tasks():
    """運行後台任務"""
    # 每30分鐘清理一次過期會話
    schedule.every(30).minutes.do(cleanup_expired_sessions)
    
    while True:
        schedule.run_pending()
        time_module.sleep(60)  # 每分鐘檢查一次

def start_background_tasks():
    """啟動後台任務線程"""
    if os.environ.get('FLASK_ENV') != 'development':  # 只在生產環境運行
        background_thread = threading.Thread(target=run_background_tasks, daemon=True)
        background_thread.start()
        logger.info("🚀 後台清理任務已啟動")

# ===== Flask 中間件 =====

@app.before_request
def force_https():
    """強制 HTTPS（生產環境）"""
    if (not request.is_secure and 
        request.headers.get('X-Forwarded-Proto') != 'https' and
        os.environ.get('FLASK_ENV') == 'production'):
        from flask import redirect
        return redirect(request.url.replace('http://', 'https://'), code=301)

@app.after_request
def after_request(response):
    """添加安全標頭"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 記錄請求
    logger.info(f"{request.remote_addr} - {request.method} {request.path} - {response.status_code}")
    
    return response

# ===== 主要路由 =====

@app.route('/', methods=['GET'])
def root():
    """根路徑端點"""
    if not firebase_initialized:
        # 嘗試重新初始化
        logger.info("嘗試重新初始化 Firebase...")
        init_firebase_with_retry()
    
    if route_handlers:
        return route_handlers.root()
    else:
        return jsonify({
            'service': 'Scrilab Artale Authentication Service',
            'status': 'initializing',
            'firebase_initialized': firebase_initialized,
            'simpleswap_available': simpleswap_service is not None,
            'message': 'Service is starting up, please wait...'
        })

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'artale-auth-service',
        'version': '3.0.0-simpleswap',
        'checks': {}
    }
    
    # 檢查 Firebase 狀態
    if firebase_initialized and db:
        try:
            # 快速測試查詢
            test_ref = db.collection('connection_test').limit(1)
            list(test_ref.stream())
            health_status['checks']['firebase'] = 'healthy'
        except Exception as e:
            health_status['checks']['firebase'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
    else:
        health_status['checks']['firebase'] = 'not_initialized'
        health_status['status'] = 'degraded'
    
    # 檢查 SimpleSwap 服務
    if simpleswap_service:
        health_status['checks']['simpleswap_service'] = 'healthy'
    else:
        health_status['checks']['simpleswap_service'] = 'not_initialized'
        health_status['status'] = 'degraded'
    
    # 檢查路由處理器
    if route_handlers:
        health_status['checks']['route_handlers'] = 'healthy'
    else:
        health_status['checks']['route_handlers'] = 'not_initialized'
        health_status['status'] = 'degraded'
    
    # 檢查 Session Manager
    if session_manager:
        try:
            stats = session_manager.get_session_stats()
            health_status['checks']['session_manager'] = 'healthy'
            health_status['session_stats'] = stats
        except Exception as e:
            health_status['checks']['session_manager'] = f'error: {str(e)}'
    else:
        health_status['checks']['session_manager'] = 'not_initialized'
    
    status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
    return jsonify(health_status), status_code

# ===== 用戶認證路由 =====

@app.route('/auth/login', methods=['POST'])
def login():
    """用戶登入端點"""
    if not firebase_initialized:
        logger.warning("Firebase 未初始化，嘗試重新初始化...")
        if not init_firebase_with_retry():
            return jsonify({
                'success': False,
                'error': 'Authentication service unavailable. Please try again later.',
                'code': 'SERVICE_UNAVAILABLE'
            }), 503
    
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready. Please try again later.',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.login()

@app.route('/auth/logout', methods=['POST'])
def logout():
    """用戶登出端點"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.logout()

@app.route('/auth/validate', methods=['POST'])
def validate_session():
    """驗證會話令牌"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.validate_session()

@app.route('/session-stats', methods=['GET'])
def session_stats():
    """Session 統計信息"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.session_stats()

@app.route('/cleanup-sessions', methods=['POST'])
def manual_cleanup_sessions():
    """手動清理過期會話"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.manual_cleanup_sessions()

# ===== SimpleSwap 付款相關路由 =====

@app.route('/api/create-simpleswap-payment', methods=['POST'])
def create_simpleswap_payment():
    """創建 SimpleSwap Fiat-to-Crypto 付款（信用卡 → USDT）"""
    if not simpleswap_routes:
        return jsonify({
            'success': False,
            'error': 'SimpleSwap 服務未初始化',
            'code': 'SIMPLESWAP_SERVICE_UNAVAILABLE'
        }), 503
    
    return simpleswap_routes.create_payment()

@app.route('/payment/simpleswap/webhook', methods=['POST'])
def simpleswap_webhook():
    """SimpleSwap/Mercuryo Webhook 處理"""
    if not simpleswap_routes:
        return jsonify({
            'status': 'error',
            'message': 'SimpleSwap service not available'
        }), 503
    
    return simpleswap_routes.webhook_handler()

@app.route('/payment/simpleswap/success', methods=['GET'])
def simpleswap_success():
    """SimpleSwap Fiat-to-Crypto 付款成功頁面"""
    if not simpleswap_routes:
        return redirect('/products?error=service_unavailable')
    
    return simpleswap_routes.payment_success()

@app.route('/payment/simpleswap/details/<exchange_id>', methods=['GET'])
def simpleswap_payment_details(exchange_id):
    """顯示 SimpleSwap 付款詳情頁面"""
    if not simpleswap_routes:
        return redirect('/products?error=service_unavailable')
    
    return simpleswap_routes.payment_details(exchange_id)

@app.route('/payment/mercuryo/mock/<exchange_id>', methods=['GET'])
def mercuryo_mock_payment(exchange_id):
    """顯示模擬的 Mercuryo 信用卡付款頁面"""
    if not simpleswap_routes:
        return redirect('/products?error=service_unavailable')
    
    return simpleswap_routes.show_mercuryo_mock_payment(exchange_id)

@app.route('/payment/mercuryo/mock/<exchange_id>/process', methods=['POST'])
def process_mercuryo_mock_payment(exchange_id):
    """處理模擬的 Mercuryo 信用卡付款"""
    if not simpleswap_routes:
        return jsonify({
            'success': False,
            'error': 'Service not available'
        }), 503
    
    return simpleswap_routes.process_mock_payment(exchange_id)

@app.route('/payment/success', methods=['GET'])
def payment_success():
    """付款成功頁面"""
    try:
        provider = request.args.get('provider', 'simpleswap')
        
        if provider == 'simpleswap' or not provider:
            # SimpleSwap 付款成功處理
            if not simpleswap_routes:
                return redirect('/products?error=service_unavailable')
            return simpleswap_routes.payment_success()
        else:
            # 其他付款方式重定向到 SimpleSwap
            return redirect('/products?error=invalid_provider')
            
    except Exception as e:
        logger.error(f"付款成功處理錯誤: {str(e)}", exc_info=True)
        return redirect('/products?error=system_error')

@app.route('/payment/cancel', methods=['GET'])
def payment_cancel():
    """付款取消回調"""
    return render_template_string(PAYMENT_CANCEL_TEMPLATE)

@app.route('/api/check-simpleswap-payment-status', methods=['POST'])
def check_simpleswap_payment_status():
    """檢查 SimpleSwap Fiat-to-Crypto 付款狀態 API"""
    if not simpleswap_routes:
        return jsonify({
            'success': False,
            'error': 'SimpleSwap 服務未初始化'
        }), 503
    
    return simpleswap_routes.check_payment_status()

@app.route('/products', methods=['GET'])
def products_page():
    """軟體服務展示頁面（支援 SimpleSwap）"""
    return render_template_string(PROFESSIONAL_PRODUCTS_TEMPLATE)

# ===== 調試路由 =====

@app.route('/debug/simpleswap', methods=['GET'])
def simpleswap_debug():
    """SimpleSwap 調試頁面"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimpleSwap API 調試工具</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .section {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h3 {
            color: #007bff;
            margin-top: 0;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #0056b3; }
        .result {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
            white-space: pre-wrap;
            font-family: monospace;
            max-height: 400px;
            overflow-y: auto;
        }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 SimpleSwap API 調試工具</h1>
        
        <div class="section">
            <h3>1. 檢查 API 基本功能</h3>
            <button onclick="testBasicAPI()">測試獲取貨幣列表</button>
            <div id="basic-result" class="result" style="display: none;"></div>
        </div>

        <div class="section">
            <h3>2. 測試估算 API</h3>
            <div class="grid">
                <div class="form-group">
                    <label>From Currency:</label>
                    <select id="from-currency">
                        <option value="eur">EUR</option>
                        <option value="usd">USD</option>
                        <option value="gbp">GBP</option>
                        <option value="btc">BTC</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>To Currency:</label>
                    <select id="to-currency">
                        <option value="usdt">USDT</option>
                        <option value="usdttrc20">USDT TRC20</option>
                        <option value="usdterc20">USDT ERC20</option>
                        <option value="btc">BTC</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Amount:</label>
                    <input type="number" id="amount" value="10" step="0.01">
                </div>
            </div>
            <button onclick="testEstimate()">測試估算</button>
            <div id="estimate-result" class="result" style="display: none;"></div>
        </div>

        <div class="section">
            <h3>3. 批量測試貨幣對</h3>
            <button onclick="batchTestPairs()">批量測試常用貨幣對</button>
            <div id="batch-result" class="result" style="display: none;"></div>
        </div>

        <div class="section">
            <h3>4. 測試付款創建</h3>
            <button onclick="testPaymentCreation()">測試創建 SimpleSwap 付款</button>
            <div id="payment-result" class="result" style="display: none;"></div>
        </div>

        <div class="section">
            <h3>5. API 狀態總結</h3>
            <div id="status-summary" style="background: white; padding: 15px; border-radius: 4px; border: 1px solid #ddd;">
                點擊上面的測試按鈕來生成 API 狀態報告
            </div>
        </div>
    </div>

    <script>
        let testResults = {
            currencies: null,
            estimates: [],
            paymentTest: null
        };

        async function testBasicAPI() {
            const resultDiv = document.getElementById('basic-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '正在測試獲取貨幣列表...';
            
            try {
                const response = await fetch('/api/debug-simpleswap-currencies');
                const data = await response.json();
                
                testResults.currencies = data;
                
                if (data.success) {
                    resultDiv.innerHTML = `✅ 成功獲取貨幣列表
                    
總貨幣數: ${data.total_currencies}
USDT 相關貨幣: ${data.usdt_currencies.length}
法幣支援: ${data.fiat_currencies.length}
BTC 支援: ${data.btc_currencies.length}

USDT 貨幣樣本:
${data.usdt_currencies.map(c => `- ${c.symbol}: ${c.name || 'N/A'}`).join('\\n')}

法幣貨幣:
${data.fiat_currencies.map(c => `- ${c.symbol}: ${c.name || 'N/A'}`).join('\\n')}`;
                    resultDiv.className = 'result success';
                } else {
                    resultDiv.innerHTML = `❌ 獲取貨幣列表失敗
                    
錯誤: ${data.error}
API Key 預覽: ${data.api_key_preview || 'N/A'}
回應: ${data.response || 'N/A'}`;
                    resultDiv.className = 'result error';
                }
            } catch (error) {
                resultDiv.innerHTML = `❌ 請求失敗: ${error.message}`;
                resultDiv.className = 'result error';
            }
            
            updateStatusSummary();
        }

        async function testEstimate() {
            const resultDiv = document.getElementById('estimate-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '正在測試估算 API...';
            
            const fromCurrency = document.getElementById('from-currency').value;
            const toCurrency = document.getElementById('to-currency').value;
            const amount = parseFloat(document.getElementById('amount').value);
            
            try {
                const response = await fetch('/api/test-simpleswap-estimate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        currency_from: fromCurrency,
                        currency_to: toCurrency,
                        amount: amount
                    })
                });
                
                const data = await response.json();
                testResults.estimates.push(data);
                
                if (data.success) {
                    resultDiv.innerHTML = `✅ 估算成功
                    
貨幣對: ${data.currency_pair}
輸入金額: ${data.amount}
估算結果: ${data.response_text}
狀態碼: ${data.status_code}`;
                    resultDiv.className = 'result success';
                } else {
                    resultDiv.innerHTML = `❌ 估算失敗
                    
貨幣對: ${data.currency_pair}
輸入金額: ${data.amount}
狀態碼: ${data.status_code}
回應: ${data.response_text}
錯誤: ${data.error || 'N/A'}`;
                    resultDiv.className = 'result error';
                }
            } catch (error) {
                resultDiv.innerHTML = `❌ 請求失敗: ${error.message}`;
                resultDiv.className = 'result error';
            }
            
            updateStatusSummary();
        }

        async function batchTestPairs() {
            const resultDiv = document.getElementById('batch-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '正在批量測試貨幣對...';
            
            const pairs = [
                ['eur', 'usdt'],
                ['eur', 'usdttrc20'],
                ['eur', 'usdterc20'],
                ['usd', 'usdt'],
                ['usd', 'usdttrc20'],
                ['gbp', 'usdt'],
                ['eur', 'btc'],
                ['usd', 'btc']
            ];
            
            const results = [];
            
            for (const [from, to] of pairs) {
                try {
                    const response = await fetch('/api/test-simpleswap-estimate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            currency_from: from,
                            currency_to: to,
                            amount: 10
                        })
                    });
                    
                    const data = await response.json();
                    results.push({
                        pair: `${from}/${to}`,
                        success: data.success,
                        status: data.status_code,
                        result: data.response_text
                    });
                } catch (error) {
                    results.push({
                        pair: `${from}/${to}`,
                        success: false,
                        error: error.message
                    });
                }
                
                // 短暫延遲避免 API 限制
                await new Promise(resolve => setTimeout(resolve, 200));
            }
            
            const summary = results.map(r => {
                if (r.success) {
                    return `✅ ${r.pair}: ${r.result}`;
                } else {
                    return `❌ ${r.pair}: ${r.error || `HTTP ${r.status}`}`;
                }
            }).join('\\n');
            
            const successCount = results.filter(r => r.success).length;
            
            resultDiv.innerHTML = `批量測試完成 (${successCount}/${results.length} 成功):

${summary}`;
            
            if (successCount > 0) {
                resultDiv.className = 'result success';
            } else {
                resultDiv.className = 'result error';
            }
            
            updateStatusSummary();
        }

        async function testPaymentCreation() {
            const resultDiv = document.getElementById('payment-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '正在測試付款創建...';
            
            const testData = {
                plan_id: 'trial_7',
                user_info: {
                    name: '測試用戶',
                    email: 'test@example.com'
                }
            };
            
            try {
                const response = await fetch('/api/create-simpleswap-payment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testData)
                });
                
                const data = await response.json();
                testResults.paymentTest = data;
                
                if (data.success) {
                    resultDiv.innerHTML = `✅ 付款創建成功
                    
Exchange ID: ${data.exchange_id}
付款 URL: ${data.payment_url}
金額: ${data.amount_fiat || data.amount_usd} ${data.fiat_currency || 'USD'}
預計收到: ${data.estimated_crypto} ${data.crypto_currency}
付款方式: ${data.payment_method}`;
                    resultDiv.className = 'result success';
                } else {
                    resultDiv.innerHTML = `❌ 付款創建失敗
                    
錯誤: ${data.error}`;
                    resultDiv.className = 'result error';
                }
            } catch (error) {
                resultDiv.innerHTML = `❌ 請求失敗: ${error.message}`;
                resultDiv.className = 'result error';
            }
            
            updateStatusSummary();
        }

        function updateStatusSummary() {
            const summaryDiv = document.getElementById('status-summary');
            
            let summary = '<h4>📊 API 狀態總結</h4>';
            
            // 基本 API 狀態
            if (testResults.currencies) {
                if (testResults.currencies.success) {
                    summary += '<p>✅ <strong>貨幣列表 API:</strong> 正常工作</p>';
                } else {
                    summary += '<p>❌ <strong>貨幣列表 API:</strong> 失敗</p>';
                }
            }
            
            // 估算 API 狀態
            const successfulEstimates = testResults.estimates.filter(e => e.success).length;
            const totalEstimates = testResults.estimates.length;
            
            if (totalEstimates > 0) {
                if (successfulEstimates > 0) {
                    summary += `<p>✅ <strong>估算 API:</strong> ${successfulEstimates}/${totalEstimates} 成功</p>`;
                } else {
                    summary += `<p>❌ <strong>估算 API:</strong> 全部失敗 (${totalEstimates} 次測試)</p>`;
                }
            }
            
            // 付款創建狀態
            if (testResults.paymentTest) {
                if (testResults.paymentTest.success) {
                    summary += '<p>✅ <strong>付款創建:</strong> 正常工作</p>';
                } else {
                    summary += '<p>❌ <strong>付款創建:</strong> 失敗</p>';
                }
            }
            
            // 建議
            summary += '<hr><h4>🔧 建議措施</h4>';
            
            if (testResults.currencies && !testResults.currencies.success) {
                summary += '<p>🔴 <strong>API Key 問題:</strong> 請檢查 SIMPLESWAP_API_KEY 環境變數是否正確設置</p>';
                summary += '<p>🔴 <strong>權限問題:</strong> 您的 API Key 可能沒有訪問貨幣列表的權限</p>';
            }
            
            if (totalEstimates > 0 && successfulEstimates === 0) {
                summary += '<p>🟡 <strong>貨幣對不支援:</strong> 嘗試的所有貨幣對都不可用，這可能是正常的</p>';
                summary += '<p>🟡 <strong>建議:</strong> 使用模擬付款功能作為備選方案</p>';
            }
            
            if (successfulEstimates > 0) {
                summary += '<p>🟢 <strong>部分功能正常:</strong> 某些貨幣對可用，系統可以正常工作</p>';
            }
            
            summaryDiv.innerHTML = summary;
        }

        // 頁面載入時的說明
        document.addEventListener('DOMContentLoaded', function() {
            console.log('SimpleSwap API 調試工具已載入');
        });
    </script>
</body>
</html>'''

@app.route('/api/debug-simpleswap-currencies', methods=['GET'])
def debug_simpleswap_currencies():
    """調試 SimpleSwap 支援的貨幣"""
    if not simpleswap_service:
        return jsonify({
            'success': False,
            'error': 'SimpleSwap 服務未初始化'
        }), 503
    
    try:
        # 獲取支援的貨幣列表
        api_key = os.environ.get('SIMPLESWAP_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'SimpleSwap API Key 未設定'
            }), 500
        
        response = requests.get(
            "https://api.simpleswap.io/get_currencies",
            params={'api_key': api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            currencies = response.json()
            
            # 篩選出 USDT 相關貨幣
            usdt_currencies = [c for c in currencies if 'usdt' in c.get('symbol', '').lower()]
            fiat_currencies = [c for c in currencies if c.get('symbol', '').lower() in ['usd', 'eur', 'gbp']]
            btc_currencies = [c for c in currencies if c.get('symbol', '').lower() == 'btc']
            
            return jsonify({
                'success': True,
                'total_currencies': len(currencies),
                'usdt_currencies': usdt_currencies[:10],
                'fiat_currencies': fiat_currencies,
                'btc_currencies': btc_currencies,
                'sample_currencies': currencies[:20]
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API 請求失敗: {response.status_code}',
                'response': response.text,
                'api_key_preview': api_key[:8] + '...' if api_key else 'None'
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'調試錯誤: {str(e)}'
        }), 500

@app.route('/api/test-simpleswap-estimate', methods=['POST'])
def test_simpleswap_estimate():
    """測試 SimpleSwap 估算 API"""
    try:
        data = request.get_json()
        currency_from = data.get('currency_from', 'eur')
        currency_to = data.get('currency_to', 'usdt')
        amount = data.get('amount', 10.0)
        
        api_key = os.environ.get('SIMPLESWAP_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API Key 未設定'
            }), 500
        
        estimate_params = {
            'api_key': api_key,
            'fixed': 'false',
            'currency_from': currency_from,
            'currency_to': currency_to,
            'amount': amount
        }
        
        response = requests.get(
            "https://api.simpleswap.io/get_estimated",
            params=estimate_params,
            timeout=30
        )
        
        return jsonify({
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'response_text': response.text,
            'currency_pair': f"{currency_from}/{currency_to}",
            'amount': amount,
            'api_key_preview': api_key[:8] + '...' if api_key else 'None'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'測試錯誤: {str(e)}'
        }), 500

# ===== 應用初始化 =====

# 模塊載入時初始化 Firebase
logger.info("🚀 開始初始化應用...")
try:
    success = init_firebase_with_retry()
    if success:
        logger.info(f"✅ 應用初始化成功，SimpleSwap 服務: {'已啟用' if simpleswap_service else '未啟用'}")
    else:
        logger.error(f"❌ 應用初始化失敗")
except Exception as e:
    logger.error(f"❌ 應用初始化異常: {str(e)}")

# 如果作為主程式運行
if __name__ == '__main__':
    # 開發環境下的額外檢查
    if not firebase_initialized:
        logger.warning("⚠️ Firebase 未初始化，應用可能無法正常工作")
    
    if not simpleswap_service:
        logger.warning("⚠️ SimpleSwap 服務未初始化，信用卡付款功能不可用")
    
    app.run(debug=True, host='0.0.0.0', port=5000)