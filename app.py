"""
app.py - 安全修復版本，隱藏所有端點信息，使用單一路由
"""
from flask import Flask, redirect, request, jsonify, render_template_string, abort
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
import hashlib
import secrets

# 導入模組
from common.admin_panel import admin_bp
from products.artale.manual_routes import manual_bp
from common.disclaimer_routes import disclaimer_bp
from core.session_manager import session_manager, init_session_manager
from core.route_handlers import RouteHandlers
from core.gumroad_service import GumroadService
from core.gumroad_routes import gumroad_bp, init_gumroad_routes
from common.templates import PROFESSIONAL_PRODUCTS_TEMPLATE, PAYMENT_CANCEL_TEMPLATE
from products.artale.intro_routes import intro_bp

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 應用初始化
app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY', secrets.token_hex(32))
app.config['JSON_SORT_KEYS'] = False

# CORS 配置
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# 全局變數
db = None
firebase_initialized = False
gumroad_service = None
route_handlers = None
initialization_in_progress = False

# 安全配置
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', secrets.token_hex(16))
SECURITY_MODE = os.environ.get('SECURITY_MODE', 'strict').lower()

def check_environment_variables():
    """檢查必要的環境變數"""
    required_vars = [
        'FIREBASE_CREDENTIALS_BASE64',
        'GUMROAD_ACCESS_TOKEN',
        'GUMROAD_TRIAL_PRODUCT_ID',
        'GUMROAD_MONTHLY_PRODUCT_ID',
        'GUMROAD_QUARTERLY_PRODUCT_ID',
        'WEBHOOK_BASE_URL'
    ]
    
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
        if not check_environment_variables():
            return False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"嘗試初始化 Firebase (第 {attempt + 1}/{max_retries} 次)...")
                
                if firebase_admin._apps:
                    logger.info("Firebase 應用已存在，刪除後重新初始化")
                    firebase_admin.delete_app(firebase_admin.get_app())
                
                credentials_base64 = os.environ['FIREBASE_CREDENTIALS_BASE64'].strip()
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                credentials_dict = json.loads(credentials_json)
                
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not credentials_dict.get(field)]
                
                if missing_fields:
                    logger.error(f"憑證缺少必需字段: {missing_fields}")
                    if attempt == max_retries - 1:
                        return False
                    continue
                
                cred = credentials.Certificate(credentials_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase 應用初始化成功")
                
                db = firestore.client()
                logger.info("Firestore 客戶端創建成功")
                
                try:
                    test_collection = db.collection('connection_test')
                    test_doc_ref = test_collection.document('test_connection')
                    
                    test_doc_ref.set({
                        'timestamp': datetime.now(),
                        'test': True,
                        'message': f'Connection test - attempt {attempt + 1}',
                        'server_time': datetime.now().isoformat()
                    })
                    
                    test_doc = test_doc_ref.get()
                    if test_doc.exists:
                        logger.info("✅ Firestore 連接測試成功")
                        firebase_initialized = True
                        
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
    global gumroad_service, route_handlers
    
    try:
        init_session_manager(db)
        logger.info("✅ Session Manager 已初始化")
        
        gumroad_service = GumroadService(db)
        logger.info("✅ Gumroad Service 已初始化")
        
        init_gumroad_routes(gumroad_service)
        logger.info("✅ Gumroad Routes 已初始化")
        
        route_handlers = RouteHandlers(db, session_manager)
        logger.info("✅ Route Handlers 已初始化")
        
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
    schedule.every(30).minutes.do(cleanup_expired_sessions)
    
    while True:
        schedule.run_pending()
        time_module.sleep(60)

def start_background_tasks():
    """啟動後台任務線程"""
    if os.environ.get('FLASK_ENV') != 'development':
        background_thread = threading.Thread(target=run_background_tasks, daemon=True)
        background_thread.start()
        logger.info("🚀 後台清理任務已啟動")

# ===== 安全中間件 =====

def get_client_ip():
    """獲取客戶端真實 IP"""
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP', 
        'HTTP_CF_CONNECTING_IP',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'REMOTE_ADDR'
    ]
    
    for header in headers_to_check:
        ip = request.environ.get(header)
        if ip:
            return ip.split(',')[0].strip()
    
    return request.remote_addr or 'unknown'

def is_admin_access():
    """檢查是否為管理員存取"""
    # 檢查 URL 參數中的 admin_key
    admin_key = request.args.get('admin_key')
    if admin_key and admin_key == ADMIN_SECRET:
        return True
    
    # 檢查 headers 中的管理員憑證
    admin_token = request.headers.get('Admin-Secret')
    if admin_token and admin_token == ADMIN_SECRET:
        return True
    
    return False

@app.before_request
def security_middleware():
    """安全中間件"""
    # 強制 HTTPS（生產環境）
    if (not request.is_secure and 
        request.headers.get('X-Forwarded-Proto') != 'https' and
        os.environ.get('FLASK_ENV') == 'production'):
        return redirect(request.url.replace('http://', 'https://'), code=301)
    
    # 管理員路由保護
    if request.path.startswith('/admin'):
        if not is_admin_access():
            # 返回 404 而不是 401，隱藏管理員介面的存在
            abort(404)
    
    # 隱藏內部端點
    protected_paths = ['/auth/', '/session-stats', '/cleanup-sessions', '/health']
    for path in protected_paths:
        if request.path.startswith(path) and request.path != '/':
            # 只允許特定的請求方式訪問
            if request.method != 'POST' or not request.is_json:
                abort(404)

@app.after_request
def after_request(response):
    """添加安全標頭並隱藏敏感信息"""
    # 安全標頭
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # 隱藏 Flask 版本信息
    response.headers.pop('Server', None)
    
    # 記錄請求（不包含敏感信息）
    if not request.path.startswith('/admin'):
        logger.info(f"{get_client_ip()} - {request.method} {request.path} - {response.status_code}")
    
    return response

@app.errorhandler(404)
def not_found(error):
    """自定義 404 頁面 - 重定向到主頁"""
    return redirect('/', code=302)

@app.errorhandler(403)
def forbidden(error):
    """自定義 403 頁面 - 重定向到主頁"""
    return redirect('/', code=302)

@app.errorhandler(500)
def internal_error(error):
    """自定義 500 頁面"""
    logger.error(f"內부錯誤: {str(error)}")
    return redirect('/', code=302)

# ===== 主要路由（使用單一路由策略）=====

@app.route('/')
def index():
    """主頁 - 根據參數決定顯示內容"""
    try:
        # 檢查特殊參數
        page = request.args.get('page', 'home')
        
        if page == 'manual':
            return redirect('/manual')
        elif page == 'disclaimer':
            return redirect('/disclaimer')
        elif page == 'intro':
            return redirect('/intro')
        else:
            # 預設顯示產品頁面
            return render_template_string(PROFESSIONAL_PRODUCTS_TEMPLATE)
            
    except Exception as e:
        logger.error(f"主頁錯誤: {str(e)}")
        return render_template_string(PROFESSIONAL_PRODUCTS_TEMPLATE)

# 註冊藍圖（但隱藏路由）
app.register_blueprint(manual_bp)
app.register_blueprint(disclaimer_bp)
app.register_blueprint(intro_bp)
app.register_blueprint(gumroad_bp)

# 只在管理員認證後註冊管理員藍圖
@app.route('/admin')
def admin_gateway():
    """管理員入口 - 需要特殊認證"""
    if not is_admin_access():
        abort(404)
    
    # 動態註冊管理員藍圖
    if 'admin' not in [bp.name for bp in app.blueprints.values()]:
        app.register_blueprint(admin_bp)
    
    return redirect('/admin/')

# ===== 隱藏的 API 端點 =====

@app.route('/api/auth', methods=['POST'])
def api_auth():
    """隱藏的認證端點"""
    if not firebase_initialized or not route_handlers:
        return jsonify({'error': 'Service unavailable'}), 503
    
    action = request.json.get('action') if request.is_json else None
    
    if action == 'login':
        return route_handlers.login()
    elif action == 'logout':
        return route_handlers.logout()
    elif action == 'validate':
        return route_handlers.validate_session()
    else:
        abort(404)

@app.route('/api/system', methods=['POST'])
def api_system():
    """隱藏的系統端點"""
    if not request.is_json:
        abort(404)
    
    action = request.json.get('action')
    
    if action == 'health':
        if not firebase_initialized:
            return jsonify({'status': 'unavailable'}), 503
        
        # 簡化的健康檢查，不暴露內部信息
        try:
            test_ref = db.collection('connection_test').limit(1)
            list(test_ref.stream())
            return jsonify({'status': 'ok'})
        except:
            return jsonify({'status': 'error'}), 503
            
    elif action == 'stats' and route_handlers:
        return route_handlers.session_stats()
    elif action == 'cleanup' and route_handlers:
        return route_handlers.manual_cleanup_sessions()
    else:
        abort(404)

# ===== 付款相關路由（保持原有功能）=====

@app.route('/api/payment', methods=['POST'])
def api_payment():
    """統一付款端點"""
    try:
        if not request.is_json:
            abort(404)
            
        data = request.get_json()
        provider = data.get('provider', 'gumroad')
        
        if provider == 'gumroad':
            # 重定向到 Gumroad 付款創建
            return redirect('/gumroad/create-payment', code=307)
        else:
            return jsonify({
                'success': False,
                'error': f'不支援的付款提供者: {provider}'
            }), 400
            
    except Exception as e:
        logger.error(f"創建付款錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': '系統錯誤，請稍後再試'
        }), 500

@app.route('/payment/success')
def payment_success():
    """付款成功頁面"""
    try:
        provider = request.args.get('provider', 'gumroad')
        
        if provider == 'gumroad':
            return redirect('/gumroad/success?' + request.query_string.decode())
        else:
            return redirect('/?error=invalid_provider')
            
    except Exception as e:
        logger.error(f"付款成功處理錯誤: {str(e)}", exc_info=True)
        return redirect('/?error=system_error')

@app.route('/payment/cancel')
def payment_cancel():
    """付款取消回調"""
    return render_template_string(PAYMENT_CANCEL_TEMPLATE)

# ===== 特殊調試端點（僅開發環境）=====

@app.route('/debug/info')
def debug_info():
    """調試信息端點（僅開發環境且需要特殊認證）"""
    if os.environ.get('FLASK_ENV') != 'development':
        abort(404)
    
    debug_key = request.args.get('debug_key')
    if debug_key != os.environ.get('DEBUG_KEY'):
        abort(404)
    
    return jsonify({
        'firebase_initialized': firebase_initialized,
        'gumroad_available': gumroad_service is not None,
        'route_handlers_ready': route_handlers is not None,
        'environment': os.environ.get('FLASK_ENV', 'unknown')
    })

# ===== 應用初始化 =====

logger.info("🚀 開始初始化應用...")
try:
    success = init_firebase_with_retry()
    if success:
        logger.info(f"✅ 應用初始化成功，安全模式: {SECURITY_MODE}")
    else:
        logger.error(f"❌ 應用初始化失敗")
except Exception as e:
    logger.error(f"❌ 應用初始化異常: {str(e)}")

# 如果作為主程式運行
if __name__ == '__main__':
    if not firebase_initialized:
        logger.warning("⚠️ Firebase 未初始化，應用可能無法正常工作")
    
    if not gumroad_service:
        logger.warning("⚠️ Gumroad 服務未初始化，付款功能不可用")
    
    print(f"🔐 管理員密鑰: {ADMIN_SECRET}")
    print(f"🔗 管理員連結: http://localhost:5000/admin?admin_key={ADMIN_SECRET}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)