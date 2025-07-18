"""
app.py - 修復版本，加強錯誤處理和重試機制
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

# 註冊藍圖
app.register_blueprint(admin_bp)
app.register_blueprint(manual_bp)
app.register_blueprint(disclaimer_bp)
app.register_blueprint(intro_bp)

# 全局變數
db = None
firebase_initialized = False
payment_service = None
route_handlers = None
initialization_in_progress = False

def check_environment_variables():
    """檢查必要的環境變數"""
    required_vars = ['FIREBASE_CREDENTIALS_BASE64']
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
                
                # 測試連接（加上超時處理）
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
    global payment_service, route_handlers
    
    try:
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
            'message': 'Service is starting up, please wait...'
        })

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'artale-auth-service',
        'version': '2.2.0',
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

@app.route('/auth/login', methods=['POST'])
def login():
    """用戶登入端點"""
    # 確保服務已初始化
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

# ===== 付款相關路由 =====

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """創建 PayPal 付款"""
    if not payment_service:
        return jsonify({
            'success': False,
            'error': '付款服務未初始化',
            'code': 'PAYMENT_SERVICE_UNAVAILABLE'
        }), 503
    
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
logger.info("🚀 開始初始化應用...")
try:
    success = init_firebase_with_retry()
    if success:
        logger.info(f"✅ 應用初始化成功")
    else:
        logger.error(f"❌ 應用初始化失敗")
except Exception as e:
    logger.error(f"❌ 應用初始化異常: {str(e)}")

# 如果作為主程式運行
if __name__ == '__main__':
    # 開發環境下的額外檢查
    if not firebase_initialized:
        logger.warning("⚠️ Firebase 未初始化，應用可能無法正常工作")
    
    app.run(debug=True, host='0.0.0.0', port=5000)