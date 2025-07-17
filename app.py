"""
app.py - 重構後的主應用檔案
將路由處理邏輯分離到其他模組，保持主檔案簡潔
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

# 導入模組
from admin_panel import admin_bp
from manual_routes import manual_bp
from disclaimer_routes import disclaimer_bp
from session_manager import session_manager, init_session_manager
from route_handlers import RouteHandlers
from payment_service import PaymentService
from templates import PROFESSIONAL_PRODUCTS_TEMPLATE, PAYMENT_SUCCESS_TEMPLATE, PAYMENT_CANCEL_TEMPLATE

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 應用初始化
app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY', 'dev-key-change-in-production')

# CORS 配置
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# 註冊藍圖
app.register_blueprint(admin_bp)
app.register_blueprint(manual_bp)
app.register_blueprint(disclaimer_bp)

# 全局變數
db = None
firebase_initialized = False
payment_service = None
route_handlers = None

def init_firebase():
    """初始化 Firebase"""
    global db, firebase_initialized
    
    try:
        logger.info("開始初始化 Firebase...")
        
        # 檢查是否已經初始化
        if firebase_admin._apps:
            logger.info("Firebase 應用已存在，刪除後重新初始化")
            firebase_admin.delete_app(firebase_admin.get_app())
        
        # 使用 Base64 編碼的完整憑證
        if 'FIREBASE_CREDENTIALS_BASE64' in os.environ:
            logger.info("使用 Base64 編碼憑證")
            try:
                credentials_base64 = os.environ['FIREBASE_CREDENTIALS_BASE64'].strip()
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                credentials_dict = json.loads(credentials_json)
                logger.info(f"解析 JSON 成功，項目ID: {credentials_dict.get('project_id', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"Base64 憑證處理失敗: {str(e)}")
                raise ValueError(f"Base64 憑證格式錯誤: {str(e)}")
        
        # 使用分別的環境變數（備用方案）
        else:
            logger.info("使用分離式環境變數")
            credentials_dict = {
                "type": "service_account",
                "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
                "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_X509_CERT_URL'),
                "universe_domain": "googleapis.com"
            }
        
        # 檢查必需字段
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if not credentials_dict.get(field)]
        
        if missing_fields:
            raise ValueError(f"缺少必需的憑證字段: {', '.join(missing_fields)}")
        
        # 驗證私鑰格式
        private_key = credentials_dict.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            logger.error("私鑰格式錯誤")
            raise ValueError("私鑰格式錯誤，必須以 -----BEGIN PRIVATE KEY----- 開始")
        
        logger.info("憑證驗證通過，開始初始化 Firebase...")
        
        # 初始化 Firebase
        cred = credentials.Certificate(credentials_dict)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase 應用初始化成功")
        
        # 初始化 Firestore
        db = firestore.client()
        logger.info("Firestore 客戶端創建成功")
        
        # 測試 Firestore 連接
        logger.info("測試 Firestore 連接...")
        test_collection = db.collection('connection_test')
        test_doc_ref = test_collection.document('test_connection')
        
        # 嘗試寫入測試數據
        test_doc_ref.set({
            'timestamp': datetime.now(),
            'test': True,
            'message': 'Connection test from Render server'
        })
        logger.info("Firestore 寫入測試成功")
        
        # 嘗試讀取測試數據
        test_doc = test_doc_ref.get()
        if test_doc.exists:
            logger.info("Firestore 讀取測試成功")
            firebase_initialized = True
            
            # 初始化相關服務
            init_services()
            
            logger.info("✅ Firebase 完全初始化成功")
            return True
        else:
            raise Exception("無法讀取測試文檔")
            
    except Exception as e:
        logger.error(f"❌ Firebase 初始化失敗: {str(e)}")
        firebase_initialized = False
        db = None
        return False

def init_services():
    """初始化相關服務"""
    global payment_service, route_handlers
    
    # 初始化 Session Manager
    init_session_manager(db)
    logger.info("✅ Session Manager 已初始化")
    
    # 初始化付款服務
    payment_service = PaymentService(db)
    logger.info("✅ Payment Service 已初始化")
    
    # 初始化路由處理器
    route_handlers = RouteHandlers(db, session_manager, payment_service)
    logger.info("✅ Route Handlers 已初始化")
    
    # 啟動後台清理任務
    start_background_tasks()

def cleanup_expired_sessions():
    """定期清理過期會話"""
    try:
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
    return route_handlers.root() if route_handlers else jsonify({'error': 'Service initializing'})

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return route_handlers.health_check() if route_handlers else jsonify({'status': 'initializing'})

@app.route('/auth/login', methods=['POST'])
def login():
    """用戶登入端點"""
    return route_handlers.login() if route_handlers else jsonify({'error': 'Service not ready'}), 503

@app.route('/auth/logout', methods=['POST'])
def logout():
    """用戶登出端點"""
    return route_handlers.logout() if route_handlers else jsonify({'error': 'Service not ready'}), 503

@app.route('/auth/validate', methods=['POST'])
def validate_session():
    """驗證會話令牌"""
    return route_handlers.validate_session() if route_handlers else jsonify({'error': 'Service not ready'}), 503

@app.route('/session-stats', methods=['GET'])
def session_stats():
    """Session 統計信息"""
    return route_handlers.session_stats() if route_handlers else jsonify({'error': 'Service not ready'}), 503

@app.route('/cleanup-sessions', methods=['POST'])
def manual_cleanup_sessions():
    """手動清理過期會話"""
    return route_handlers.manual_cleanup_sessions() if route_handlers else jsonify({'error': 'Service not ready'}), 503

# ===== 付款相關路由 =====

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """創建 PayPal 付款"""
    if not payment_service:
        return jsonify({'success': False, 'error': '付款服務未初始化'}), 503
    
    try:
        from route_handlers import rate_limit
        
        # 應用速率限制
        @rate_limit(max_requests=10, time_window=300)
        def _create_payment():
            data = request.get_json()
            plan_id = data.get('plan_id')
            user_info = data.get('user_info')
            
            # 驗證資料
            if not plan_id or not user_info:
                return jsonify({'success': False, 'error': '缺少必要資料'}), 400
            
            if not user_info.get('name') or not user_info.get('email'):
                return jsonify({'success': False, 'error': '請填寫姓名和信箱'}), 400
            
            # 方案資料
            plans = {
                'trial_7': {'id': 'trial_7', 'name': '體驗服務', 'price': 299, 'period': '7天'},
                'monthly_30': {'id': 'monthly_30', 'name': '標準服務', 'price': 549, 'period': '30天'},
                'quarterly_90': {'id': 'quarterly_90', 'name': '季度服務', 'price': 1499, 'period': '90天'}
            }
            
            plan_info = plans.get(plan_id)
            if not plan_info:
                return jsonify({'success': False, 'error': '無效的方案'}), 400
            
            # 創建付款
            payment = payment_service.create_payment(plan_info, user_info)
            
            if payment:
                # 找到 approval_url
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return jsonify({
                    'success': True,
                    'payment_id': payment.id,
                    'approval_url': approval_url
                })
            else:
                return jsonify({'success': False, 'error': '付款創建失敗'}), 500
        
        return _create_payment()
        
    except Exception as e:
        logger.error(f"創建付款錯誤: {str(e)}")
        return jsonify({'success': False, 'error': '系統錯誤'}), 500

@app.route('/payment/success', methods=['GET'])
def payment_success():
    """PayPal 付款成功回調"""
    try:
        logger.info(f"收到付款成功回調: {request.args}")
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        if not payment_id or not payer_id:
            logger.error("缺少必要參數")
            return redirect('/products?error=invalid_payment')
        
        if payment_service is None:
            logger.error("payment_service 未初始化")
            return redirect('/products?error=service_unavailable')
        
        # 執行付款
        success, user_uuid = payment_service.execute_payment(payment_id, payer_id)
        
        if success and user_uuid:
            # 獲取付款記錄詳情
            payment_record = payment_service.get_payment_record(payment_id)
            
            return render_template_string(
                PAYMENT_SUCCESS_TEMPLATE,
                success=True,
                user_uuid=user_uuid,
                payment_record=payment_record
            )
        else:
            logger.error("付款執行失敗")
            return redirect('/products?error=payment_failed')
            
    except Exception as e:
        logger.error(f"付款成功處理錯誤: {str(e)}", exc_info=True)
        return redirect('/products?error=system_error')

@app.route('/payment/cancel', methods=['GET'])
def payment_cancel():
    """PayPal 付款取消回調"""
    return render_template_string(PAYMENT_CANCEL_TEMPLATE)

@app.route('/products', methods=['GET'])
def products_page():
    """軟體服務展示頁面"""
    return render_template_string(PROFESSIONAL_PRODUCTS_TEMPLATE)

# ===== 應用初始化 =====

# 模塊載入時初始化 Firebase
logger.info("🚀 模塊載入時初始化 Firebase...")
try:
    init_firebase()
    logger.info(f"✅ 模塊級別 Firebase 初始化完成: {firebase_initialized}")
except Exception as e:
    logger.error(f"❌ 模塊級別 Firebase 初始化失敗: {str(e)}")

# 如果作為主程式運行
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)