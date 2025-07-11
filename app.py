from flask import Flask, request, jsonify, abort, redirect, render_template_string
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
from datetime import datetime, timedelta
import hashlib
import secrets
import time
from functools import wraps
import logging
import uuid as uuid_lib
from collections import defaultdict
import threading
import re
import schedule
import time as time_module

# 導入管理員模組和會話管理器
from admin_panel import admin_bp
from session_manager import session_manager, init_session_manager

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY', 'dev-key-change-in-production')

# CORS 配置
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# 註冊藍圖
app.register_blueprint(admin_bp)

# 全局變數
db = None
firebase_initialized = False

# ===== IP 封鎖機制 =====
blocked_ips = {}  # {ip: block_until_timestamp}
rate_limit_store = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}
cleanup_lock = threading.Lock()

def cleanup_expired_blocks():
    """清理過期的封鎖記錄"""
    with cleanup_lock:
        now = time.time()
        expired_ips = [ip for ip, block_until in blocked_ips.items() if block_until < now]
        for ip in expired_ips:
            del blocked_ips[ip]
            logger.info(f"IP {ip} 解除封鎖")

def is_ip_blocked(ip):
    """檢查 IP 是否被封鎖"""
    cleanup_expired_blocks()
    return ip in blocked_ips and blocked_ips[ip] > time.time()

def block_ip(ip, duration_minutes=30):
    """封鎖 IP"""
    block_until = time.time() + (duration_minutes * 60)
    blocked_ips[ip] = block_until
    logger.warning(f"IP {ip} 已被封鎖至 {datetime.fromtimestamp(block_until)}")

def get_client_ip():
    """獲取客戶端真實 IP"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).split(',')[0].strip()

def init_firebase():
    """初始化 Firebase - 改進版本"""
    global db, firebase_initialized
    
    try:
        logger.info("開始初始化 Firebase...")
        
        # 檢查是否已經初始化
        if firebase_admin._apps:
            logger.info("Firebase 應用已存在，刪除後重新初始化")
            firebase_admin.delete_app(firebase_admin.get_app())
        
        # 方法1：使用 Base64 編碼的完整憑證
        if 'FIREBASE_CREDENTIALS_BASE64' in os.environ:
            logger.info("使用 Base64 編碼憑證")
            try:
                credentials_base64 = os.environ['FIREBASE_CREDENTIALS_BASE64'].strip()
                logger.info(f"Base64 憑證長度: {len(credentials_base64)} 字符")
                
                # 解碼 Base64
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                logger.info(f"解碼後 JSON 長度: {len(credentials_json)} 字符")
                
                # 解析 JSON
                credentials_dict = json.loads(credentials_json)
                logger.info(f"解析 JSON 成功，項目ID: {credentials_dict.get('project_id', 'Unknown')}")
                
            except base64.binascii.Error as e:
                logger.error(f"Base64 解碼失敗: {str(e)}")
                raise ValueError(f"Base64 憑證格式錯誤: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失敗: {str(e)}")
                raise ValueError(f"憑證 JSON 格式錯誤: {str(e)}")
        
        # 方法2：使用分別的環境變數（備用方案）
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
        missing_fields = []
        for field in required_fields:
            if not credentials_dict.get(field):
                missing_fields.append(field)
        
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
            
            # 初始化 Session Manager
            init_session_manager(db)
            logger.info("✅ Session Manager 已初始化")
            
            # 啟動後台清理任務
            start_background_tasks()
            
            logger.info("✅ Firebase 完全初始化成功")
            return True
        else:
            raise Exception("無法讀取測試文檔")
            
    except Exception as e:
        logger.error(f"❌ Firebase 初始化失敗: {str(e)}")
        logger.error(f"❌ 錯誤類型: {type(e).__name__}")
        
        firebase_initialized = False
        db = None
        return False

# ===== 速率限制 =====
def rate_limit(max_requests=3, time_window=300, block_on_exceed=True):
    """速率限制裝飾器 - 更嚴格版本"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true':
                return f(*args, **kwargs)
            
            client_ip = get_client_ip()
            
            # 檢查 IP 是否被封鎖
            if is_ip_blocked(client_ip):
                remaining_time = int((blocked_ips[client_ip] - time.time()) / 60)
                logger.warning(f"被封鎖的 IP {client_ip} 嘗試訪問")
                return jsonify({
                    'success': False,
                    'error': f'您的 IP 已被暫時封鎖。請在 {remaining_time} 分鐘後再試。'
                }), 429
            
            now = time.time()
            
            # 清理過期記錄
            with cleanup_lock:
                rate_limit_store[client_ip] = [
                    req_time for req_time in rate_limit_store[client_ip]
                    if now - req_time < time_window
                ]
                
                # 檢查是否超過限制
                if len(rate_limit_store[client_ip]) >= max_requests:
                    logger.warning(f"IP {client_ip} 超過速率限制")
                    
                    # 自動封鎖違規 IP
                    if block_on_exceed:
                        block_ip(client_ip, 30)
                    
                    return jsonify({
                        'success': False,
                        'error': '請求過於頻繁。您的 IP 已被暫時封鎖 30 分鐘。'
                    }), 429
                
                # 記錄此次請求
                rate_limit_store[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===== Session 管理函數 =====
def generate_session_token(uuid, client_ip):
    """生成會話令牌 - 使用 Firestore"""
    session_timeout = int(os.environ.get('SESSION_TIMEOUT', 3600))
    return session_manager.generate_session_token(uuid, client_ip, session_timeout)

def verify_session_token(token):
    """驗證會話令牌 - 使用 Firestore"""
    is_valid, session_data = session_manager.verify_session_token(token)
    
    if not is_valid:
        return False, None
    
    # 獲取用戶數據
    try:
        if db is None:
            logger.error("verify_session_token: db 對象為 None")
            return False, None
            
        uuid = session_data.get('uuid')
        uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            # 檢查用戶是否仍然活躍
            if not user_data.get('active', False):
                session_manager.revoke_session_token(token)
                return False, None
            return True, user_data
        else:
            session_manager.revoke_session_token(token)
            return False, None
    except Exception as e:
        logger.error(f"User data retrieval error: {str(e)}")
        return False, None

def revoke_session_token(token):
    """撤銷會話令牌 - 使用 Firestore"""
    return session_manager.revoke_session_token(token)

# ===== 後台任務 =====
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

@app.before_request
def force_https():
    """強制 HTTPS（生產環境）"""
    if (not request.is_secure and 
        request.headers.get('X-Forwarded-Proto') != 'https' and
        os.environ.get('FLASK_ENV') == 'production'):
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

@app.route('/', methods=['GET'])
def root():
    """根路徑端點"""
    return jsonify({
        'service': 'Scrilab Artale Authentication Service',
        'version': '2.2.0',
        'status': 'running',
        'features': [
            '🔐 用戶認證系統',
            '👥 管理員面板',
            '🎲 UUID 生成器',
            '🛡️ IP 封鎖保護',
            '🚀 速率限制',
            '🔥 Firestore 會話存儲',
            '🛍️ 商品展示頁面'
        ],
        'endpoints': {
            'health': '/health',
            'login': '/auth/login',
            'logout': '/auth/logout',
            'validate': '/auth/validate',
            'admin': '/admin',
            'session_stats': '/session-stats',
            'products': '/products'
        },
        'firebase_connected': firebase_initialized
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點 - 包含 session 統計"""
    
    # 檢查 Firebase 狀態
    firebase_status = firebase_initialized and db is not None
    
    # 如果 Firebase 未初始化，嘗試重新初始化
    if not firebase_status:
        logger.warning("健康檢查發現 Firebase 未初始化，嘗試重新初始化...")
        firebase_status = init_firebase()
    
    # 獲取 session 統計
    try:
        session_stats_data = session_manager.get_session_stats()
    except Exception as e:
        session_stats_data = {'error': str(e)}
    
    return jsonify({
        'status': 'healthy' if firebase_status else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'firebase_connected': firebase_status,
        'firebase_initialized': firebase_initialized,
        'db_object_exists': db is not None,
        'service': 'artale-auth-service',
        'version': '2.2.0',
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'admin_panel': 'available at /admin',
        'session_storage': session_stats_data
    })

@app.route('/auth/login', methods=['POST'])
@rate_limit(max_requests=5, time_window=300, block_on_exceed=True)
def login():
    """用戶登入端點 - 改進版本"""
    try:
        # 檢查 Firebase 狀態
        if not firebase_initialized or db is None:
            logger.error("Firebase 未初始化或數據庫對象為 None")
            return jsonify({
                'success': False,
                'error': 'Authentication service unavailable. Please try again later.'
            }), 503
        
        data = request.get_json()
        
        if not data or 'uuid' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing UUID'
            }), 400
        
        uuid = data['uuid'].strip()
        force_login = data.get('force_login', True)
        
        if not uuid:
            return jsonify({
                'success': False,
                'error': 'UUID cannot be empty'
            }), 400
        
        # 記錄登入嘗試
        client_ip = get_client_ip()
        logger.info(f"Login attempt from {client_ip} for UUID: {uuid[:8]}...")
        
        # 呼叫認證邏輯
        success, message, user_data = authenticate_user(uuid, force_login, client_ip)
        
        if success:
            # 生成會話令牌
            session_token = generate_session_token(uuid, client_ip)
            
            logger.info(f"Login successful for UUID: {uuid[:8]}...")
            
            return jsonify({
                'success': True,
                'message': message,
                'user_data': user_data,
                'session_token': session_token
            })
        else:
            logger.warning(f"Login failed for UUID: {uuid[:8]}... - {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/auth/logout', methods=['POST'])
def logout():
    """用戶登出端點"""
    try:
        data = request.get_json()
        session_token = data.get('session_token') if data else None
        
        if session_token:
            # 撤銷會話令牌
            revoked = revoke_session_token(session_token)
            if revoked:
                logger.info(f"Session revoked: {session_token[:16]}...")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500

@app.route('/auth/validate', methods=['POST'])
@rate_limit(max_requests=120, time_window=60)
def validate_session():
    """驗證會話令牌"""
    try:
        # 檢查 Firebase 狀態
        if not firebase_initialized or db is None:
            return jsonify({
                'success': False,
                'error': 'Authentication service unavailable'
            }), 503
            
        data = request.get_json()
        session_token = data.get('session_token') if data else None
        
        if not session_token:
            return jsonify({
                'success': False,
                'error': 'Missing session token'
            }), 400
        
        # 驗證會話令牌
        is_valid, user_data = verify_session_token(session_token)
        
        if is_valid:
            return jsonify({
                'success': True,
                'user_data': user_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired session'
            }), 401
            
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed'
        }), 500

@app.route('/session-stats', methods=['GET'])
def session_stats():
    """Session 統計信息"""
    try:
        stats = session_manager.get_session_stats()
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            **stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/cleanup-sessions', methods=['POST'])
@rate_limit(max_requests=5, time_window=300)
def manual_cleanup_sessions():
    """手動清理過期會話"""
    try:
        deleted_count = session_manager.cleanup_expired_sessions()
        return jsonify({
            'success': True,
            'message': f'已清理 {deleted_count} 個過期會話',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def authenticate_user(uuid, force_login=True, client_ip='unknown'):
    """認證用戶 - 使用 Firestore Session Manager"""
    try:
        if db is None:
            logger.error("authenticate_user: db 對象為 None")
            return False, "認證服務不可用", None
        
        uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
        
        # 直接使用 document().get() 而非 where() 查詢
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            # 記錄未授權嘗試
            log_unauthorized_attempt(uuid_hash, client_ip)
            return False, "UUID 未授權", None
        
        user_data = user_doc.to_dict()
        
        # 檢查用戶狀態
        if not user_data.get('active', False):
            return False, "帳號已被停用", None
        
        # 檢查有效期
        if 'expires_at' in user_data:
            expires_at = user_data['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
            elif hasattr(expires_at, 'timestamp'):
                expires_at = datetime.fromtimestamp(expires_at.timestamp())
            
            if datetime.now() > expires_at:
                return False, "帳號已過期", None
        
        # 處理現有會話 - 使用原始 UUID（不是 hash）
        if force_login:
            session_manager.terminate_user_sessions(uuid)
        else:
            has_active = session_manager.check_existing_session(uuid)
            if has_active:
                return False, "該帳號已在其他地方登入", None
        
        # 更新登入記錄 - 批量更新以減少寫入次數
        update_data = {
            'last_login': datetime.now(),
            'login_count': firestore.Increment(1),
            'last_login_ip': client_ip
        }
        
        # 每10次登入才更新一次詳細統計（減少寫入次數）
        if user_data.get('login_count', 0) % 10 == 0:
            update_data['login_history'] = firestore.ArrayUnion([{
                'timestamp': datetime.now(),
                'ip': client_ip
            }])
        
        user_ref.update(update_data)
        
        return True, "認證成功", user_data
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False, f"認證過程發生錯誤: {str(e)}", None

def log_unauthorized_attempt(uuid_hash, client_ip):
    """記錄未授權登入嘗試"""
    try:
        if db is None:
            logger.error("log_unauthorized_attempt: db 對象為 None")
            return
            
        attempts_ref = db.collection('unauthorized_attempts')
        attempts_ref.add({
            'uuid_hash': uuid_hash,
            'timestamp': datetime.now(),
            'client_ip': client_ip,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        })
    except Exception as e:
        logger.error(f"Failed to log unauthorized attempt: {str(e)}")

# ================================
# 🔥 關鍵修復：將 Firebase 初始化移到模塊級別
# ================================
logger.info("🚀 模塊載入時初始化 Firebase...")
try:
    init_firebase()
    logger.info(f"✅ 模塊級別 Firebase 初始化完成: {firebase_initialized}")
except Exception as e:
    logger.error(f"❌ 模塊級別 Firebase 初始化失敗: {str(e)}")

if __name__ == '__main__':
    # 這裡只處理開發環境的直接運行
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🔧 開發模式啟動:")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Firebase initialized: {firebase_initialized}")
    logger.info(f"   Database object exists: {db is not None}")
    logger.info(f"   Admin panel: http://localhost:{port}/admin")
    logger.info(f"   Products page: http://localhost:{port}/products")
    logger.info(f"   Session storage: Firestore")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

# 在 app.py 中添加商品頁面路由

@app.route('/products', methods=['GET'])
def products_page():
    """商品展示頁面"""
    return render_template_string(PRODUCTS_TEMPLATE)

# 商品頁面 HTML 模板
PRODUCTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artale Script - 專業遊戲腳本解決方案</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #4a6741 100%);
            --text-primary: #2c3e50;
            --text-secondary: #64748b;
            --bg-light: #f8fafc;
            --shadow-light: 0 10px 30px rgba(0, 0, 0, 0.1);
            --shadow-heavy: 0 20px 60px rgba(0, 0, 0, 0.15);
            --border-radius: 20px;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            overflow-x: hidden;
        }

        /* Navigation */
        .navbar {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            z-index: 1000;
            transition: var(--transition);
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 2rem;
        }

        .logo {
            font-size: 1.8rem;
            font-weight: 800;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 2rem;
        }

        .nav-links a {
            text-decoration: none;
            color: var(--text-primary);
            font-weight: 500;
            transition: var(--transition);
            position: relative;
        }

        .nav-links a::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 0;
            height: 2px;
            background: var(--primary-gradient);
            transition: width 0.3s ease;
        }

        .nav-links a:hover::after {
            width: 100%;
        }

        /* Hero Section */
        .hero {
            min-height: 100vh;
            background: var(--primary-gradient);
            display: flex;
            align-items: center;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            animation: float 20s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(30px, -30px) rotate(1deg); }
            66% { transform: translate(-20px, 20px) rotate(-1deg); }
        }

        .hero-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            color: white;
            z-index: 2;
            position: relative;
        }

        .hero h1 {
            font-size: clamp(2.5rem, 6vw, 4rem);
            font-weight: 800;
            margin-bottom: 1.5rem;
            animation: slideInUp 1s ease-out;
        }

        .hero p {
            font-size: 1.25rem;
            margin-bottom: 2.5rem;
            opacity: 0.9;
            max-width: 600px;
            animation: slideInUp 1s ease-out 0.2s both;
        }

        .cta-button {
            display: inline-block;
            padding: 1rem 2.5rem;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            border: 2px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            transition: var(--transition);
            animation: slideInUp 1s ease-out 0.4s both;
        }

        .cta-button:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        }

        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Features Section */
        .features {
            padding: 6rem 2rem;
            background: var(--bg-light);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .section-title {
            text-align: center;
            margin-bottom: 4rem;
        }

        .section-title h2 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .section-title p {
            font-size: 1.1rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 4rem;
        }

        .feature-card {
            background: white;
            padding: 2.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-light);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--accent-gradient);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: var(--shadow-heavy);
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            background: var(--accent-gradient);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            color: white;
            font-size: 1.5rem;
        }

        .feature-card h3 {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .feature-card p {
            color: var(--text-secondary);
            line-height: 1.7;
        }

        /* Products Section */
        .products {
            padding: 6rem 2rem;
            background: white;
        }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2.5rem;
            margin-top: 4rem;
        }

        .product-card {
            background: white;
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow-light);
            transition: var(--transition);
            position: relative;
        }

        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-heavy);
        }

        .product-header {
            padding: 2rem;
            background: var(--primary-gradient);
            color: white;
            text-align: center;
            position: relative;
        }

        .product-header.premium {
            background: var(--secondary-gradient);
        }

        .product-header.enterprise {
            background: var(--dark-gradient);
        }

        .popular-badge {
            position: absolute;
            top: -10px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .product-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .product-subtitle {
            opacity: 0.9;
            font-size: 0.95rem;
        }

        .product-price {
            font-size: 2.5rem;
            font-weight: 800;
            margin: 1rem 0;
        }

        .product-price .currency {
            font-size: 1rem;
            vertical-align: top;
        }

        .product-price .period {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .product-body {
            padding: 2rem;
        }

        .product-features {
            list-style: none;
            margin-bottom: 2rem;
        }

        .product-features li {
            padding: 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border-bottom: 1px solid #f1f5f9;
        }

        .product-features li:last-child {
            border-bottom: none;
        }

        .feature-check {
            color: #10b981;
            font-size: 1.1rem;
        }

        .product-button {
            width: 100%;
            padding: 1rem;
            background: var(--primary-gradient);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
        }

        .product-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .product-button.premium {
            background: var(--secondary-gradient);
        }

        .product-button.enterprise {
            background: var(--dark-gradient);
        }

        /* Stats Section */
        .stats {
            padding: 4rem 2rem;
            background: var(--primary-gradient);
            color: white;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            text-align: center;
        }

        .stat-item h3 {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .stat-item p {
            opacity: 0.9;
            font-size: 1.1rem;
        }

        /* Footer */
        .footer {
            padding: 3rem 2rem 2rem;
            background: #1a202c;
            color: white;
            text-align: center;
        }

        .footer-links {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .footer-links a {
            color: #cbd5e0;
            text-decoration: none;
            transition: var(--transition);
        }

        .footer-links a:hover {
            color: white;
        }

        .footer p {
            color: #718096;
            margin-top: 1rem;
        }

        /* Purchase Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 2000;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background: white;
            padding: 2rem;
            border-radius: 20px;
            max-width: 500px;
            width: 90%;
            text-align: center;
            position: relative;
            animation: modalSlideIn 0.3s ease-out;
        }

        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: scale(0.8) translateY(-50px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        .modal-close {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #6b7280;
        }

        .plan-info {
            background: var(--bg-light);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }

        .form-group {
            margin: 1rem 0;
        }

        .form-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }

        .form-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .modal-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: var(--transition);
        }

        .btn-cancel {
            background: #6b7280;
            color: white;
        }

        .btn-primary {
            background: var(--primary-gradient);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }

            .hero h1 {
                font-size: 2.5rem;
            }

            .hero p {
                font-size: 1.1rem;
            }

            .features-grid,
            .products-grid {
                grid-template-columns: 1fr;
            }

            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .modal-content {
                margin: 1rem;
            }
        }

        /* Scroll Animations */
        .scroll-animate {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease-out;
        }

        .scroll-animate.active {
            opacity: 1;
            transform: translateY(0);
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-robot"></i> Artale Script
            </div>
            <ul class="nav-links">
                <li><a href="#home">首頁</a></li>
                <li><a href="#features">功能</a></li>
                <li><a href="#products">方案</a></li>
                <li><a href="#contact">聯絡</a></li>
                <li><a href="/admin" style="color: #667eea;">管理後台</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="hero-content">
            <h1>🚀 專業遊戲腳本解決方案</h1>
            <p>Artale Script 提供最先進的自動化遊戲腳本，讓您輕鬆提升遊戲效率。安全、穩定、高效能的專業級解決方案。</p>
            <a href="#products" class="cta-button">
                <i class="fas fa-rocket"></i> 立即體驗
            </a>
        </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="features">
        <div class="container">
            <div class="section-title scroll-animate">
                <h2>🎯 核心優勢</h2>
                <p>我們致力於提供最優質的遊戲腳本服務，讓您的遊戲體驗更上一層樓</p>
            </div>
            
            <div class="features-grid">
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h3>🛡️ 安全防護</h3>
                    <p>採用業界領先的加密技術，確保您的帳號安全。內建反檢測機制，讓您安心使用。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-cogs"></i>
                    </div>
                    <h3>⚙️ 智能配置</h3>
                    <p>簡單易用的配置介面，支援多種遊戲模式。智能學習系統，自動優化腳本性能。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-rocket"></i>
                    </div>
                    <h3>🚀 高效執行</h3>
                    <p>優化的演算法確保腳本高效運行，減少資源消耗。支援24/7不間斷運行。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-headset"></i>
                    </div>
                    <h3>💬 專業支援</h3>
                    <p>提供完整的技術支援和使用教學。專業客服團隊隨時為您解決問題。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-sync-alt"></i>
                    </div>
                    <h3>🔄 即時更新</h3>
                    <p>腳本自動更新，確保與遊戲版本同步。新功能持續開發，讓您始終領先。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h3>📊 數據分析</h3>
                    <p>詳細的執行報告和數據分析，幫助您了解腳本效能和遊戲進度。</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Products Section -->
    <section id="products" class="products">
        <div class="container">
            <div class="section-title scroll-animate">
                <h2>💎 選擇您的方案</h2>
                <p>我們提供多種方案選擇，滿足不同用戶的需求。所有方案都包含核心功能和技術支援。</p>
            </div>
            
            <div class="products-grid">
                <!-- 體驗版 -->
                <div class="product-card scroll-animate">
                    <div class="product-header">
                        <div class="product-title">🌟 體驗版</div>
                        <div class="product-subtitle">新手入門首選</div>
                        <div class="product-price">
                            <span class="currency">NT$</span>99
                            <span class="period">/7天</span>
                        </div>
                    </div>
                    <div class="product-body">
                        <ul class="product-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>基礎腳本功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>標準安全防護</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>社群技術支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>基礎數據報告</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>教學文件</span>
                            </li>
                        </ul>
                        <button class="product-button" onclick="selectPlan('trial_7')">
                            <i class="fas fa-star"></i> 開始體驗
                        </button>
                    </div>
                </div>

                <!-- 標準版 -->
                <div class="product-card scroll-animate">
                    <div class="product-header premium">
                        <div class="popular-badge">最受歡迎</div>
                        <div class="product-title">🔥 標準版</div>
                        <div class="product-subtitle">最佳性價比選擇</div>
                        <div class="product-price">
                            <span class="currency">NT$</span>299
                            <span class="period">/30天</span>
                        </div>
                    </div>
                    <div class="product-body">
                        <ul class="product-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整腳本功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高級安全防護</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>優先技術支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>詳細數據分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>自定義配置</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多設備支援</span>
                            </li>
                        </ul>
                        <button class="product-button premium" onclick="selectPlan('monthly_30')">
                            <i class="fas fa-crown"></i> 立即購買
                        </button>
                    </div>
                </div>

                <!-- 專業版 -->
                <div class="product-card scroll-animate">
                    <div class="product-header enterprise">
                        <div class="product-title">💼 專業版</div>
                        <div class="product-subtitle">進階用戶專屬</div>
                        <div class="product-price">
                            <span class="currency">NT$</span>799
                            <span class="period">/90天</span>
                        </div>
                    </div>
                    <div class="product-body">
                        <ul class="product-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>所有高級功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>企業級安全</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>1對1專屬支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>實時監控面板</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>API 整合支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>無限設備授權</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>優先新功能體驗</span>
                            </li>
                        </ul>
                        <button class="product-button enterprise" onclick="selectPlan('quarterly_90')">
                            <i class="fas fa-diamond"></i> 升級專業版
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="stats">
        <div class="container">
            <div class="stats-grid scroll-animate">
                <div class="stat-item">
                    <h3 id="users-count">10,000+</h3>
                    <p>活躍用戶</p>
                </div>
                <div class="stat-item">
                    <h3 id="uptime">99.9%</h3>
                    <p>系統穩定性</p>
                </div>
                <div class="stat-item">
                    <h3 id="support">24/7</h3>
                    <p>技術支援</p>
                </div>
                <div class="stat-item">
                    <h3 id="satisfaction">4.9★</h3>
                    <p>用戶滿意度</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer id="contact" class="footer">
        <div class="container">
            <div class="footer-links">
                <a href="#home">首頁</a>
                <a href="#features">功能介紹</a>
                <a href="#products">方案價格</a>
                <a href="mailto:support@artale-script.com">技術支援</a>
                <a href="/admin">管理後台</a>
                <a href="#">使用條款</a>
                <a href="#">隱私政策</a>
            </div>
            <p>&copy; 2024 Artale Script. 版權所有 | 專業遊戲腳本解決方案</p>
        </div>
    </footer>

    <!-- Purchase Modal -->
    <div id="purchase-modal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">購買確認</h3>
            <div id="selected-plan-info" class="plan-info">
                <!-- Plan info will be inserted here -->
            </div>
            <div class="form-group">
                <input type="email" id="user-email" placeholder="請輸入您的電子郵件" class="form-input" required>
            </div>
            <div class="form-group">
                <input type="text" id="user-name" placeholder="姓名（可選）" class="form-input">
            </div>
            <div class="modal-buttons">
                <button class="btn btn-cancel" onclick="closeModal()">取消</button>
                <button class="btn btn-primary" onclick="proceedToPurchase()" id="purchase-btn">
                    <span id="purchase-btn-text">確認購買</span>
                    <div class="loading" id="purchase-loading" style="display: none;"></div>
                </button>
            </div>
        </div>
    </div>

    <script>
        // Scroll Animation
        function animateOnScroll() {
            const elements = document.querySelectorAll('.scroll-animate');
            elements.forEach(element => {
                const elementTop = element.getBoundingClientRect().top;
                const elementVisible = 150;
                
                if (elementTop < window.innerHeight - elementVisible) {
                    element.classList.add('active');
                }
            });
        }

        window.addEventListener('scroll', animateOnScroll);
        animateOnScroll();

        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Navbar scroll effect
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 100) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = 'none';
            }
        });

        // Plan selection and purchase flow
        const plans = {
            'trial_7': {
                name: '🌟 體驗版',
                price: 99,
                period: '7天',
                description: '適合新手體驗的入門方案'
            },
            'monthly_30': {
                name: '🔥 標準版',
                price: 299,
                period: '30天',
                description: '最受歡迎的性價比選擇'
            },
            'quarterly_90': {
                name: '💼 專業版',
                price: 799,
                period: '90天',
                description: '進階用戶的專業方案'
            }
        };

        let selectedPlan = null;

        function selectPlan(planId) {
            selectedPlan = planId;
            const plan = plans[planId];
            
            document.getElementById('selected-plan-info').innerHTML = `
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">${plan.name}</h4>
                <p style="margin: 0 0 1rem 0; color: var(--text-secondary);">${plan.description}</p>
                <div style="font-size: 1.5rem; font-weight: bold; color: var(--text-primary);">
                    NT$ ${plan.price} <span style="font-size: 1rem; font-weight: normal;">/ ${plan.period}</span>
                </div>
            `;
            
            document.getElementById('purchase-modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('purchase-modal').style.display = 'none';
            document.getElementById('user-email').value = '';
            document.getElementById('user-name').value = '';
        }

        function proceedToPurchase() {
            const email = document.getElementById('user-email').value.trim();
            const name = document.getElementById('user-name').value.trim();
            
            if (!email) {
                alert('請輸入電子郵件地址');
                return;
            }
            
            if (!validateEmail(email)) {
                alert('請輸入有效的電子郵件地址');
                return;
            }
            
            // Show loading
            document.getElementById('purchase-btn-text').style.display = 'none';
            document.getElementById('purchase-loading').style.display = 'inline-block';
            
            // 準備與歐付寶整合
            setTimeout(() => {
                alert(`感謝您選擇 ${plans[selectedPlan].name}！\\n\\n我們即將推出線上付款功能，\\n目前請聯繫客服完成購買。\\n\\n電子郵件：${email}\\n方案：${plans[selectedPlan].name}\\n金額：NT$ ${plans[selectedPlan].price}`);
                
                document.getElementById('purchase-btn-text').style.display = 'inline';
                document.getElementById('purchase-loading').style.display = 'none';
                
                closeModal();
            }, 2000);
        }

        function validateEmail(email) {
            const re = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
            return re.test(email);
        }

        // Counter animation for stats
        function animateCounter(id, target, duration = 2000) {
            const element = document.getElementById(id);
            const start = 0;
            const increment = target / (duration / 16);
            let current = start;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    element.textContent = target.toLocaleString() + (id === 'satisfaction' ? '★' : id === 'uptime' ? '%' : id === 'support' ? '' : '+');
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(current).toLocaleString() + (id === 'satisfaction' ? '★' : id === 'uptime' ? '%' : id === 'support' ? '' : '+');
                }
            }, 16);
        }

        // Stats animation observer
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => animateCounter('users-count', 10000), 200);
                    setTimeout(() => animateCounter('uptime', 99.9), 400);
                    setTimeout(() => animateCounter('satisfaction', 4.9), 800);
                    statsObserver.unobserve(entry.target);
                }
            });
        });

        const statsSection = document.querySelector('.stats');
        if (statsSection) {
            statsObserver.observe(statsSection);
        }

        // Close modal when clicking outside
        document.getElementById('purchase-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });

        // Escape key to close modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""