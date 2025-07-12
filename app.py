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

@app.route('/products', methods=['GET'])
def products_page():
    """軟體服務展示頁面"""
    return render_template_string(PROFESSIONAL_PRODUCTS_TEMPLATE)

# 專業軟體服務頁面 HTML 模板 - 暗色系設計
# 使用原始字串 (r"...") 避免反斜線問題
PROFESSIONAL_PRODUCTS_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scrilab - python</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            /* 暗色主題配色 */
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --bg-card: #1e1e1e;
            --bg-hover: #333333;
            
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-muted: #808080;
            
            --accent-blue: #00d4ff;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            
            --border-color: #333333;
            --border-hover: #555555;
            
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-accent: linear-gradient(135deg, #00d4ff 0%, #8b5cf6 100%);
            --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 25px rgba(0, 0, 0, 0.25);
            --shadow-lg: 0 15px 35px rgba(0, 0, 0, 0.35);
            --shadow-glow: 0 0 30px rgba(0, 212, 255, 0.3);
            
            --border-radius: 16px;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: 
                var(--bg-primary),
                radial-gradient(ellipse at top left, rgba(0, 212, 255, 0.02) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(139, 92, 246, 0.02) 0%, transparent 50%);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* 增強版背景動效 */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 1;
        }

        .bg-animation::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(16, 185, 129, 0.04) 0%, transparent 50%),
                linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.02) 50%, transparent 70%);
            animation: float 20s ease-in-out infinite;
        }

        .bg-animation::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                conic-gradient(from 0deg at 70% 30%, transparent, rgba(139, 92, 246, 0.03), transparent),
                conic-gradient(from 180deg at 30% 70%, transparent, rgba(0, 212, 255, 0.02), transparent);
            animation: rotate 30s linear infinite;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(30px, -30px) rotate(1deg); }
            66% { transform: translate(-20px, 20px) rotate(-1deg); }
        }

        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.02; }
            50% { opacity: 0.08; }
        }

        @keyframes slide {
            0% { transform: translateX(-10%) translateY(-5%); }
            100% { transform: translateX(10%) translateY(5%); }
        }

        @keyframes fade-slide {
            0%, 100% { opacity: 0; transform: translateY(20px) rotate(var(--rotation)); }
            50% { opacity: 0.08; transform: translateY(-20px) rotate(var(--rotation)); }
        }

        /* Navigation */
        .navbar {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(26, 26, 26, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
            z-index: 1000;
            transition: var(--transition);
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.2rem 2rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--text-primary);
            text-decoration: none;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: var(--gradient-accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 2.5rem;
            align-items: center;
        }

        .nav-links a {
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.95rem;
            transition: var(--transition);
            position: relative;
            padding: 0.5rem 0;
        }

        .nav-links a:hover {
            color: var(--accent-blue);
        }

        .nav-links a::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 0;
            height: 2px;
            background: var(--gradient-accent);
            transition: width 0.3s ease;
        }

        .nav-links a:hover::after {
            width: 100%;
        }

        .nav-cta {
            background: var(--gradient-accent);
            color: white;
            padding: 0.7rem 1.5rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: var(--transition);
        }

        .nav-cta:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            position: relative;
            background: var(--bg-primary);
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                linear-gradient(135deg, transparent 0%, rgba(0, 212, 255, 0.03) 25%, transparent 50%, rgba(139, 92, 246, 0.02) 75%, transparent 100%);
            animation: slide 25s ease-in-out infinite alternate;
        }

        .hero-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            z-index: 2;
            position: relative;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.2);
            color: var(--accent-blue);
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 2rem;
            animation: slideInUp 1s ease-out;
        }

        .hero h1 {
            font-size: clamp(3rem, 8vw, 5.5rem);
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.1;
            animation: slideInUp 1s ease-out 0.2s both;
        }

        .hero .highlight {
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero p {
            font-size: 1.3rem;
            color: var(--text-secondary);
            margin-bottom: 3rem;
            max-width: 700px;
            line-height: 1.7;
            animation: slideInUp 1s ease-out 0.4s both;
        }

        .hero-buttons {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            animation: slideInUp 1s ease-out 0.6s both;
        }

        .btn-primary {
            background: var(--gradient-accent);
            color: white;
            padding: 1rem 2rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
            border: none;
            cursor: pointer;
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-glow);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-primary);
            padding: 1rem 2rem;
            border: 2px solid var(--border-color);
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
        }

        .btn-secondary:hover {
            border-color: var(--accent-blue);
            color: var(--accent-blue);
            transform: translateY(-3px);
        }

        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Features Section */
        .features {
            padding: 8rem 2rem;
            background: var(--bg-secondary);
            position: relative;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .section-header {
            text-align: center;
            margin-bottom: 5rem;
        }

        .section-badge {
            display: inline-block;
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.2);
            color: var(--accent-purple);
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
        }

        .section-description {
            font-size: 1.2rem;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.7;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-top: 4rem;
        }

        .feature-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
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
            height: 3px;
            background: var(--gradient-accent);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }

        .feature-card:hover::before {
            transform: scaleX(1);
        }

        .feature-card:hover {
            transform: translateY(-8px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-lg);
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            background: var(--gradient-accent);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            color: white;
            font-size: 1.5rem;
        }

        .feature-card h3 {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .feature-card p {
            color: var(--text-secondary);
            line-height: 1.7;
            font-size: 1rem;
        }

        /* Games Section */
        .games {
            padding: 8rem 2rem;
            background: var(--bg-secondary);
            position: relative;
        }

        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 3rem;
            margin-top: 4rem;
        }

        .game-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            overflow: hidden;
            transition: var(--transition);
            cursor: pointer;
            position: relative;
        }

        .game-card.active:hover {
            transform: translateY(-5px);
            border-color: var(--accent-blue);
            box-shadow: var(--shadow-lg);
        }

        .game-card.coming-soon {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .game-image {
            position: relative;
            width: 100%;
            height: 200px;
            overflow: hidden;
            background: var(--bg-tertiary);
        }

        .game-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: var(--transition);
        }

        .game-card.active:hover .game-image img {
            transform: scale(1.05);
        }

        .game-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: var(--transition);
        }

        .game-card.active:hover .game-overlay {
            opacity: 1;
        }

        .game-overlay i {
            font-size: 2.5rem;
            color: var(--accent-blue);
        }

        .game-info {
            padding: 2rem;
        }

        .game-info h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .game-subtitle {
            color: var(--accent-blue);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }

        .game-description {
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        .game-status {
            display: flex;
            gap: 1rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .status-badge.active {
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-badge.coming {
            background: rgba(245, 158, 11, 0.1);
            color: var(--accent-orange);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .back-button {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.8rem 1.5rem;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
            transition: var(--transition);
        }

        .back-button:hover {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
            transform: translateX(-5px);
        }

        /* Services Section */
        .services {
            padding: 8rem 2rem;
            background: var(--bg-primary);
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 3rem;
            margin-top: 5rem;
        }

        .service-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            overflow: hidden;
            transition: var(--transition);
            position: relative;
        }

        .service-card:hover {
            transform: translateY(-5px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-lg);
        }

        .service-header {
            padding: 2.5rem 2rem 1.5rem;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border-color);
            position: relative;
        }

        .service-header.premium {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
            border-bottom-color: rgba(139, 92, 246, 0.2);
        }

        .service-header.enterprise {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
            border-bottom-color: rgba(16, 185, 129, 0.2);
        }

        .popular-badge {
            position: absolute;
            top: -12px;
            right: 2rem;
            background: var(--gradient-accent);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            box-shadow: var(--shadow-md);
        }

        .service-title {
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .service-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .service-price {
            font-size: 2.8rem;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .service-price .currency {
            font-size: 1.2rem;
            vertical-align: top;
        }

        .service-price .period {
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 400;
        }

        .service-body {
            padding: 2rem;
        }

        .service-features {
            list-style: none;
            margin-bottom: 2.5rem;
        }

        .service-features li {
            padding: 0.8rem 0;
            display: flex;
            align-items: flex-start;
            gap: 0.8rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .service-features li:last-child {
            border-bottom: none;
        }

        .feature-check {
            color: var(--accent-green);
            font-size: 1.1rem;
            margin-top: 0.1rem;
            flex-shrink: 0;
        }

        .service-button {
            width: 100%;
            padding: 1rem;
            background: var(--gradient-accent);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .service-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        .service-button.premium {
            background: var(--gradient-success);
        }

        .service-button.enterprise {
            background: var(--gradient-warning);
        }

        /* Stats Section */
        .stats {
            padding: 6rem 2rem;
            background: var(--bg-secondary);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 3rem;
            text-align: center;
        }

        .stat-item {
            position: relative;
        }

        .stat-item h3 {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-item p {
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 500;
        }

        /* Footer */
        .footer {
            background: var(--bg-primary);
            border-top: 1px solid var(--border-color);
            padding: 4rem 2rem 2rem;
        }

        .footer-simple {
            text-align: center;
            margin-bottom: 3rem;
        }

        .footer-simple h3 {
            font-size: 1.2rem;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            font-weight: 600;
        }

        .contact-methods {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 3rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .discord-link, .email-link {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 1.1rem;
            transition: var(--transition);
            padding: 0.8rem 1.5rem;
            border-radius: 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
        }

        .discord-link:hover {
            color: #5865F2;
            border-color: #5865F2;
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(88, 101, 242, 0.3);
        }

        .email-link:hover {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
        }

        .discord-link i, .email-link i {
            font-size: 1.5rem;
        }

        .discord-link:hover i {
            animation: bounce 0.5s ease-in-out;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }

        .footer-note {
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-top: 1.5rem;
        }

        .footer-bottom {
            border-top: 1px solid var(--border-color);
            padding-top: 2rem;
            text-align: center;
            color: var(--text-muted);
        }

        /* Purchase Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(10px);
        }

        .modal-content {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            max-width: 500px;
            width: 90%;
            padding: 2.5rem;
            text-align: center;
            position: relative;
            animation: modalSlideIn 0.4s ease-out;
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
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            transition: var(--transition);
        }

        .modal-close:hover {
            color: var(--text-primary);
        }

        .plan-info {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }

        .form-group {
            margin: 1.5rem 0;
            text-align: left;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .form-input {
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: var(--transition);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }

        .modal-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
        }

        .btn-cancel {
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: var(--transition);
        }

        .btn-cancel:hover {
            color: var(--text-primary);
            border-color: var(--border-hover);
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

            .hero-buttons {
                flex-direction: column;
                align-items: flex-start;
            }

            .features-grid,
            .services-grid,
            .games-grid {
                grid-template-columns: 1fr;
            }

            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .section-title {
                font-size: 2.2rem;
            }

            .contact-methods {
                flex-direction: column;
                gap: 1.5rem;
            }

            .discord-link, .email-link {
                width: 100%;
                max-width: 300px;
                justify-content: center;
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
    <div class="bg-animation"></div>

    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="#home" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-code"></i>
                </div>
                <span>Scrilab</span>
            </a>
            <ul class="nav-links">
                <li><a href="#home">首頁</a></li>
                <li><a href="#features">服務特色</a></li>
                <li><a href="#games">遊戲服務</a></li>
                <li><a href="#contact">聯絡我們</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="hero-content">
            <div class="hero-badge">
                <i class="fas fa-star"></i>
                <span>領先的遊戲技術服務提供商</span>
            </div>
            <h1>專業<span class="highlight">遊戲技術服務</span><br>與個人化解決方案</h1>
            <p>Scrilab 為遊戲愛好者提供專業的遊戲技術服務，透過我們的技術團隊為您量身打造個人化的遊戲效率提升方案。我們專注於為客戶提供安全、穩定的遊戲體驗優化服務。</p>
            <div class="hero-buttons">
                <a href="#games" class="btn-primary">
                    <i class="fas fa-gamepad"></i>
                    <span>瀏覽遊戲服務</span>
                </a>
                <a href="#contact" class="btn-secondary">
                    <i class="fas fa-phone"></i>
                    <span>預約諮詢</span>
                </a>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="features">
        <div class="container">
            <div class="section-header scroll-animate">
                <div class="section-badge">專業服務</div>
                <h2 class="section-title">為什麼選擇 Scrilab 服務</h2>
                <p class="section-description">我們擁有豐富的遊戲技術經驗和專業的服務團隊，致力於為遊戲玩家提供最優質的個人化服務</p>
            </div>
            
            <div class="features-grid">
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h3>安全保障</h3>
                    <p>採用業界最高安全標準，多層次加密保護，確保您的帳號和個人資料安全無虞。通過多項安全驗證，為玩家提供可信賴的技術服務。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-cogs"></i>
                    </div>
                    <h3>高度自定義</h3>
                    <p>根據玩家個人需求提供完全客製化的技術方案，支援多種參數調整與個人化設定，確保服務完美符合您的遊戲風格與需求。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-rocket"></i>
                    </div>
                    <h3>多線程處理</h3>
                    <p>採用先進的多線程處理技術，支援並行運算處理，確保服務在各種複雜環境下都能穩定運行，提供流暢的使用體驗。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-headset"></i>
                    </div>
                    <h3>專業客服支援</h3>
                    <p>提供24/7客服支援服務，專業技術人員隨時為您解決使用問題，確保服務穩定運行，讓您專注於享受遊戲樂趣。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-sync-alt"></i>
                    </div>
                    <h3>完全隨機性</h3>
                    <p>內建先進的隨機演算法系統，確保每次執行都具有獨特性，提供最自然的遊戲體驗。</p>
                </div>
                
                <div class="feature-card scroll-animate">
                    <div class="feature-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h3>視覺識別技術</h3>
                    <p>採用先進的圖像識別與截圖分析技術，能夠精確識別遊戲畫面元素，提供智能化的環境感知與適應能力。</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Games Section -->
    <section id="games" class="games">
        <div class="container">
            <div class="section-header scroll-animate">
                <div class="section-badge">遊戲服務</div>
                <h2 class="section-title">選擇您的遊戲</h2>
                <p class="section-description">一次購買越久享受更優惠的價格，所有方案均提供完整的技術服務</p>
            </div>
            
            <div class="games-grid">
                <!-- MapleStory Worlds - Artale -->
                <div class="game-card scroll-animate active" onclick="showGamePlans('artale')">
                    <div class="game-image">
                        <img src="/static/images/artale-cover.jpg" alt="MapleStory Worlds - Artale">
                        <div class="game-overlay">
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>
                    <div class="game-info">
                        <h3>MapleStory Worlds - Artale</h3>
                        <p class="game-subtitle">繁體中文版</p>
                        <p class="game-description">專為 Artale 玩家打造的優化解決方案</p>
                        <div class="game-status">
                            <span class="status-badge active">服務中</span>
                        </div>
                    </div>
                </div>

                <!-- Coming Soon Games -->
                <div class="game-card scroll-animate coming-soon">
                    <div class="game-image">
                        <img src="/static/images/coming-soon.jpg" alt="Coming Soon">
                        <div class="game-overlay">
                            <i class="fas fa-clock"></i>
                        </div>
                    </div>
                    <div class="game-info">
                        <h3>更多遊戲</h3>
                        <p class="game-subtitle">即將推出</p>
                        <p class="game-description">我們正在開發更多遊戲的優化解決方案，敬請期待</p>
                        <div class="game-status">
                            <span class="status-badge coming">開發中</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Services Section (Now for specific game) -->
    <section id="services" class="services" style="display: none;">
        <div class="container">
            <div class="section-header scroll-animate">
                <button class="back-button" onclick="backToGames()">
                    <i class="fas fa-arrow-left"></i>
                    <span>返回遊戲列表</span>
                </button>
                <div class="section-badge">服務方案</div>
                <h2 class="section-title" id="game-plans-title">MapleStory Worlds - Artale 專屬方案</h2>
                <p class="section-description">選擇適合您的服務方案，享受最佳遊戲體驗</p>
            </div>
            
            <div class="services-grid">
                <!-- 體驗方案 -->
                <div class="service-card scroll-animate">
                    <div class="service-header">
                        <div class="service-title">體驗服務</div>
                        <div class="service-subtitle">適合新手玩家體驗</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>299
                            <span class="period">/7天</span>
                        </div>
                    </div>
                    <div class="service-body">
                        <ul class="service-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整技術服務功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多線程處理技術</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>視覺識別與截圖分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完全隨機性演算法</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高度自定義設定</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>24/7技術支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>安全加密保護</span>
                            </li>
                        </ul>
                        <button class="service-button" onclick="selectPlan('trial_7')">
                            <i class="fas fa-star"></i>
                            <span>開始體驗</span>
                        </button>
                    </div>
                </div>

                <!-- 標準方案 -->
                <div class="service-card scroll-animate">
                    <div class="service-header premium">
                        <div class="popular-badge">最受歡迎</div>
                        <div class="service-title">標準服務</div>
                        <div class="service-subtitle">最佳性價比選擇</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>549
                            <span class="period">/30天</span>
                        </div>
                    </div>
                    <div class="service-body">
                        <ul class="service-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整技術服務功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多線程處理技術</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>視覺識別與截圖分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完全隨機性演算法</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高度自定義設定</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>24/7技術支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>安全加密保護</span>
                            </li>
                        </ul>
                        <button class="service-button premium" onclick="selectPlan('monthly_30')">
                            <i class="fas fa-crown"></i>
                            <span>立即選購</span>
                        </button>
                    </div>
                </div>

                <!-- 季度方案 -->
                <div class="service-card scroll-animate">
                    <div class="service-header enterprise">
                        <div class="service-title">季度服務</div>
                        <div class="service-subtitle">長期使用最划算</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>1,499
                            <span class="period">/90天</span>
                        </div>
                    </div>
                    <div class="service-body">
                        <ul class="service-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整技術服務功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多線程處理技術</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>視覺識別與截圖分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完全隨機性演算法</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高度自定義設定</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>24/7技術支援</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>安全加密保護</span>
                            </li>
                        </ul>
                        <button class="service-button enterprise" onclick="selectPlan('quarterly_90')">
                            <i class="fas fa-gem"></i>
                            <span>超值選購</span>
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
                    <h3 id="projects-count">5,000+</h3>
                    <p>服務使用者</p>
                </div>
                <div class="stat-item">
                    <h3 id="clients-count">3,000+</h3>
                    <p>活躍用戶</p>
                </div>
                <div class="stat-item">
                    <h3 id="uptime">99.9%</h3>
                    <p>系統穩定性</p>
                </div>
                <div class="stat-item">
                    <h3 id="satisfaction">4.9★</h3>
                    <p>客戶滿意度</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer id="contact" class="footer">
        <div class="container">
            <div class="footer-simple">
                <h3 style="font-size: 1.2rem; margin-bottom: 1.5rem; color: var(--text-primary); font-weight: 600;">聯絡我們</h3>
                <div class="contact-methods">
                    <a href="https://discord.gg/HPzNrQmN" target="_blank" class="discord-link" title="加入我們的 Discord">
                        <i class="fab fa-discord"></i>
                        <span>Discord 技術支援</span>
                    </a>
                    <a href="mailto:pink870921aa@gmail.com" class="email-link">
                        <i class="fas fa-envelope"></i>
                        <span>pink870921aa@gmail.com</span>
                    </a>
                </div>
                <p class="footer-note">所有技術支援與客服諮詢，請優先透過 Discord 聯繫我們</p>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2025 Scrilab. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <!-- Purchase Modal -->
    <div id="purchase-modal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">服務購買</h3>
            <div id="selected-plan-info" class="plan-info">
                <!-- Plan info will be inserted here -->
            </div>
            <div class="form-group">
                <label for="user-name">姓名</label>
                <input type="text" id="user-name" placeholder="請輸入您的姓名" class="form-input" required>
            </div>
            <div class="form-group">
                <label for="contact-email">聯絡信箱</label>
                <input type="email" id="contact-email" placeholder="請輸入聯絡信箱" class="form-input" required>
            </div>
            <div class="form-group">
                <label for="contact-phone">聯絡電話（選填）</label>
                <input type="tel" id="contact-phone" placeholder="請輸入聯絡電話" class="form-input">
            </div>
            <div class="modal-buttons">
                <button class="btn-cancel" onclick="closeModal()">取消</button>
                <button class="btn-primary" onclick="submitInquiry()" id="inquiry-btn">
                    <span id="inquiry-btn-text">立即購買</span>
                    <div class="loading" id="inquiry-loading" style="display: none;"></div>
                </button>
            </div>
        </div>
    </div>

    <script>
        // Game Selection
        function showGamePlans(gameId) {
            if (gameId === 'artale') {
                document.getElementById('games').style.display = 'none';
                document.getElementById('services').style.display = 'block';
                document.getElementById('game-plans-title').textContent = 'MapleStory Worlds - Artale 專屬方案';
                
                // Smooth scroll to services section
                document.getElementById('services').scrollIntoView({ behavior: 'smooth' });
            }
        }

        function backToGames() {
            document.getElementById('services').style.display = 'none';
            document.getElementById('games').style.display = 'block';
            document.getElementById('games').scrollIntoView({ behavior: 'smooth' });
        }

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
                navbar.style.background = 'rgba(26, 26, 26, 0.98)';
                navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
            } else {
                navbar.style.background = 'rgba(26, 26, 26, 0.95)';
                navbar.style.boxShadow = 'none';
            }
        });

        // Service plans data
        const servicePlans = {
            'trial_7': {
                name: '體驗服務',
                price: 299,
                period: '7天',
                description: '適合新手玩家體驗的基礎技術服務'
            },
            'monthly_30': {
                name: '標準服務',
                price: 549,
                period: '30天',
                description: '最受歡迎的完整技術服務方案'
            },
            'quarterly_90': {
                name: '季度服務',
                price: 1499,
                period: '90天',
                description: '長期使用最划算的全功能技術服務'
            }
        };

        let selectedPlan = null;

        function selectPlan(planId) {
            selectedPlan = planId;
            const plan = servicePlans[planId];
            
            document.getElementById('selected-plan-info').innerHTML = `
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">${plan.name}</h4>
                <p style="margin: 0 0 1rem 0; color: var(--text-secondary);">${plan.description}</p>
                <div style="font-size: 1.5rem; font-weight: bold; color: var(--accent-blue);">
                    NT$ ${plan.price.toLocaleString()} <span style="font-size: 1rem; font-weight: normal;">/ ${plan.period}</span>
                </div>
            `;
            
            document.getElementById('purchase-modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('purchase-modal').style.display = 'none';
            // Clear form
            document.getElementById('user-name').value = '';
            document.getElementById('contact-email').value = '';
            document.getElementById('contact-phone').value = '';
        }

        function submitInquiry() {
            const userName = document.getElementById('user-name').value.trim();
            const contactEmail = document.getElementById('contact-email').value.trim();
            const contactPhone = document.getElementById('contact-phone').value.trim();
            
            if (!userName || !contactEmail) {
                alert('請填寫必要資訊（姓名、聯絡信箱）');
                return;
            }
            
            if (!validateEmail(contactEmail)) {
                alert('請輸入有效的電子郵件地址');
                return;
            }
            
            // Show loading
            document.getElementById('inquiry-btn-text').style.display = 'none';
            document.getElementById('inquiry-loading').style.display = 'inline-block';
            
            // Simulate purchase process
            setTimeout(() => {
                const plan = servicePlans[selectedPlan];
                alert('感謝您選擇 Scrilab 技術服務！\\n\\n服務方案：' + plan.name + '\\n' +
                      '服務期限：' + plan.period + '\\n' +
                      '服務費用：NT$ ' + plan.price.toLocaleString() + '\\n\\n' +
                      '我們將在24小時內透過電子郵件發送服務啟用資訊。\\n' +
                      '如有任何問題，歡迎聯繫客服。');
                
                document.getElementById('inquiry-btn-text').style.display = 'inline';
                document.getElementById('inquiry-loading').style.display = 'none';
                
                closeModal();
            }, 2000);
        }

        function validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        }

        // Counter animation for stats
        function animateCounter(id, target, suffix = '', duration = 2000) {
            const element = document.getElementById(id);
            const start = 0;
            const increment = target / (duration / 16);
            let current = start;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    if (id === 'uptime') {
                        element.textContent = target + '%';
                    } else if (id === 'satisfaction') {
                        element.textContent = target + '★';
                    } else {
                        element.textContent = target + suffix;
                    }
                    clearInterval(timer);
                } else {
                    if (id === 'uptime') {
                        element.textContent = current.toFixed(1) + '%';
                    } else if (id === 'satisfaction') {
                        element.textContent = current.toFixed(1) + '★';
                    } else {
                        element.textContent = Math.floor(current) + suffix;
                    }
                }
            }, 16);
        }

        // Stats animation observer
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => animateCounter('projects-count', 100, '+'), 200);
                    setTimeout(() => animateCounter('clients-count', 50, '+'), 400);
                    setTimeout(() => animateCounter('uptime', 99.9), 600);
                    setTimeout(() => animateCounter('satisfaction', 5), 800);
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

        // 創建代碼風格的背景裝飾
        function createCodeBackground() {
            const codeContainer = document.createElement('div');
            codeContainer.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                pointer-events: none; z-index: -1; opacity: 0.08; 
                font-family: 'Courier New', monospace; color: var(--accent-blue);
                overflow: hidden; font-size: 14px;
            `;
            
            const codeSnippets = [
                'def optimize_game():', 'import threading', 'class GameBot:', 
                'async def process():', 'while running:', 'cv2.imread()', 
                'random.choice()', 'time.sleep()', 'import numpy as np',
                'for i in range(10):', 'if game_active:', 'threading.Thread()',
                'await asyncio.sleep()', 'import cv2', 'def main():'
            ];
            
            for (let i = 0; i < 15; i++) {
                const line = document.createElement('div');
                line.textContent = codeSnippets[i % codeSnippets.length];
                line.style.cssText = `
                    position: absolute; 
                    left: ${Math.random() * 100}%; 
                    top: ${Math.random() * 100}%;
                    animation: fade-slide ${15 + Math.random() * 10}s ease-in-out infinite;
                    animation-delay: ${Math.random() * 10}s;
                    transform: rotate(${Math.random() * 20 - 10}deg);
                `;
                codeContainer.appendChild(line);
            }
            
            document.body.appendChild(codeContainer);
        }

        // Add floating particles effect
        function createFloatingParticles() {
            const particlesContainer = document.createElement('div');
            particlesContainer.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: -1;';
            
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.style.cssText = 'position: absolute; width: 2px; height: 2px; background: var(--accent-blue); border-radius: 50%; opacity: 0.3; animation: float-particle ' + (10 + Math.random() * 10) + 's linear infinite; left: ' + (Math.random() * 100) + '%; top: ' + (Math.random() * 100) + '%; animation-delay: ' + (Math.random() * 10) + 's;';
                particlesContainer.appendChild(particle);
            }
            
            document.body.appendChild(particlesContainer);
        }

        // Add CSS for particle animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes float-particle { 
                0% { transform: translateY(0) translateX(0); opacity: 0; } 
                10% { opacity: 0.3; } 
                90% { opacity: 0.3; } 
                100% { transform: translateY(-100vh) translateX(${Math.random() * 200 - 100}px); opacity: 0; } 
            }
        `;
        document.head.appendChild(style);

        // Initialize enhanced background effects
        createCodeBackground();
        createFloatingParticles();
    </script>
</body>
</html>
"""