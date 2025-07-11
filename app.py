from flask import Flask, request, jsonify, abort, redirect
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