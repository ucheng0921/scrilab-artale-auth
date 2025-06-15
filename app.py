from flask import Flask, request, jsonify, abort, redirect  # 添加 redirect 導入
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

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY', 'dev-key-change-in-production')

# CORS 配置
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# 全局變數
db = None
firebase_initialized = False
session_store = {}  # 在生產環境中應使用 Redis

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

def rate_limit(max_requests=10, time_window=60):
    """速率限制裝飾器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true':
                return f(*args, **kwargs)
            
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # 簡單的記憶體速率限制
            now = time.time()
            if client_ip not in session_store:
                session_store[client_ip] = {'requests': []}
            
            # 清理過期記錄
            session_store[client_ip]['requests'] = [
                req_time for req_time in session_store[client_ip]['requests'] 
                if now - req_time < time_window
            ]
            
            # 檢查是否超過限制
            if len(session_store[client_ip]['requests']) >= max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.'
                }), 429
            
            # 記錄此次請求
            session_store[client_ip]['requests'].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
        'service': 'Artale Authentication Service',
        'version': '1.0.1',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'login': '/auth/login',
            'logout': '/auth/logout',
            'validate': '/auth/validate'
        },
        'firebase_connected': firebase_initialized
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點 - 改進版本"""
    
    # 檢查 Firebase 狀態
    firebase_status = firebase_initialized and db is not None
    
    # 如果 Firebase 未初始化，嘗試重新初始化
    if not firebase_status:
        logger.warning("健康檢查發現 Firebase 未初始化，嘗試重新初始化...")
        firebase_status = init_firebase()
    
    return jsonify({
        'status': 'healthy' if firebase_status else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'firebase_connected': firebase_status,
        'firebase_initialized': firebase_initialized,
        'db_object_exists': db is not None,
        'service': 'artale-auth-service',
        'version': '1.0.1',
        'environment': os.environ.get('FLASK_ENV', 'unknown')
    })

@app.route('/auth/login', methods=['POST'])
@rate_limit(max_requests=5, time_window=300)  # 每5分鐘最多5次登入嘗試
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
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
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
@rate_limit(max_requests=120, time_window=60)  # 每分鐘最多120次驗證
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

def authenticate_user(uuid, force_login=True, client_ip='unknown'):
    """認證用戶 - 改進版本"""
    try:
        # 再次檢查 db 對象
        if db is None:
            logger.error("authenticate_user: db 對象為 None")
            return False, "認證服務不可用", None
        
        uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
        
        # 從 Firestore 查詢用戶
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
        
        # 處理現有會話
        if force_login:
            terminate_existing_sessions(uuid_hash)
        else:
            has_active = check_existing_session(uuid_hash)
            if has_active:
                return False, "該帳號已在其他地方登入", None
        
        # 更新登入記錄
        user_ref.update({
            'last_login': datetime.now(),
            'login_count': user_data.get('login_count', 0) + 1,
            'last_login_ip': client_ip
        })
        
        return True, "認證成功", user_data
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False, f"認證過程發生錯誤: {str(e)}", None

def generate_session_token(uuid, client_ip):
    """生成會話令牌"""
    token = secrets.token_urlsafe(32)
    now = time.time()
    expires_at = now + int(os.environ.get('SESSION_TIMEOUT', 3600))
    
    # 存儲會話信息
    session_store[token] = {
        'uuid': uuid,
        'created_at': now,
        'expires_at': expires_at,
        'last_activity': now,
        'client_ip': client_ip
    }
    
    return token

def verify_session_token(token):
    """驗證會話令牌"""
    if token not in session_store:
        return False, None
    
    session = session_store[token]
    now = time.time()
    
    # 檢查是否過期
    if now > session.get('expires_at', 0):
        del session_store[token]
        return False, None
    
    # 更新最後活動時間
    session['last_activity'] = now
    
    # 延長會話（如果快過期了）
    time_left = session['expires_at'] - now
    if time_left < 300:  # 少於5分鐘時自動延長
        session['expires_at'] = now + int(os.environ.get('SESSION_TIMEOUT', 3600))
    
    # 獲取用戶數據
    try:
        if db is None:
            logger.error("verify_session_token: db 對象為 None")
            return False, None
            
        uuid_hash = hashlib.sha256(session['uuid'].encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            # 檢查用戶是否仍然活躍
            if not user_data.get('active', False):
                del session_store[token]
                return False, None
            return True, user_data
        else:
            del session_store[token]
            return False, None
    except Exception as e:
        logger.error(f"User data retrieval error: {str(e)}")
        return False, None

def revoke_session_token(token):
    """撤銷會話令牌"""
    if token in session_store:
        del session_store[token]
        return True
    return False

def terminate_existing_sessions(uuid_hash):
    """終止用戶的所有現有會話"""
    tokens_to_remove = []
    for token, session_data in session_store.items():
        if isinstance(session_data, dict) and session_data.get('uuid'):
            session_uuid_hash = hashlib.sha256(session_data['uuid'].encode()).hexdigest()
            if session_uuid_hash == uuid_hash:
                tokens_to_remove.append(token)
    
    for token in tokens_to_remove:
        del session_store[token]
    
    logger.info(f"Terminated {len(tokens_to_remove)} existing sessions for user")

def check_existing_session(uuid_hash):
    """檢查用戶是否有活躍會話"""
    now = time.time()
    for session_data in session_store.values():
        if isinstance(session_data, dict) and session_data.get('uuid'):
            session_uuid_hash = hashlib.sha256(session_data['uuid'].encode()).hexdigest()
            if (session_uuid_hash == uuid_hash and 
                now < session_data.get('expires_at', 0)):
                return True
    return False

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

if __name__ == '__main__':
    logger.info("啟動 Artale Auth Service...")
    
    if init_firebase():
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        logger.info(f"Starting server on port {port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Firebase initialized: {firebase_initialized}")
        logger.info(f"Database object exists: {db is not None}")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        logger.error("❌ 無法啟動服務：Firebase 初始化失敗")
        logger.error("請檢查環境變數設置和憑證配置")
