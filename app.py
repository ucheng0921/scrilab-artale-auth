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
from flask import render_template_string
import csv
from io import StringIO

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

# ================================
# 🔥 關鍵修復：將 Firebase 初始化移到模塊級別
# ================================
logger.info("🚀 模塊載入時初始化 Firebase...")
try:
    init_firebase()
    logger.info(f"✅ 模塊級別 Firebase 初始化完成: {firebase_initialized}")
except Exception as e:
    logger.error(f"❌ 模塊級別 Firebase 初始化失敗: {str(e)}")

# ================================
# 🎛️ 用戶管理功能
# ================================

# 管理界面 HTML 模板
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Artale Script 用戶管理</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #1976d2; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .user-table { width: 100%; border-collapse: collapse; }
        .user-table th, .user-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .user-table th { background-color: #4CAF50; color: white; }
        .user-table tr:nth-child(even) { background-color: #f2f2f2; }
        .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 2px; }
        .btn:hover { background: #45a049; }
        .btn-danger { background: #f44336; }
        .btn-danger:hover { background: #da190b; }
        .btn-warning { background: #ff9800; }
        .btn-warning:hover { background: #e68900; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; font-weight: bold; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { margin: 0; font-size: 2em; color: #1976d2; }
        .form-row { display: flex; gap: 20px; }
        .form-row .form-group { flex: 1; }
        .search-box { width: 300px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Artale Script 用戶管理系統</h1>
            <p>管理所有授權用戶、權限和有效期</p>
        </div>
        
        <!-- 統計資訊 -->
        <div class="stats">
            <div class="stat-card">
                <h3 id="total-users">-</h3>
                <p>總用戶數</p>
            </div>
            <div class="stat-card">
                <h3 id="active-users">-</h3>
                <p>活躍用戶</p>
            </div>
            <div class="stat-card">
                <h3 id="expired-users">-</h3>
                <p>已過期</p>
            </div>
        </div>
        
        <!-- 新增用戶表單 -->
        <div class="section">
            <h2>➕ 新增用戶</h2>
            <form id="create-user-form">
                <div class="form-row">
                    <div class="form-group">
                        <label>UUID</label>
                        <input type="text" id="new-uuid" placeholder="artale_user001_20241217" required>
                    </div>
                    <div class="form-group">
                        <label>顯示名稱</label>
                        <input type="text" id="new-display-name" placeholder="用戶名稱" required>
                    </div>
                    <div class="form-group">
                        <label>有效天數</label>
                        <input type="number" id="new-days" value="30" min="1" max="365">
                    </div>
                    <div class="form-group">
                        <label>&nbsp;</label>
                        <button type="submit" class="btn">創建用戶</button>
                    </div>
                </div>
            </form>
        </div>
        
        <!-- 用戶列表 -->
        <div class="section">
            <h2>👥 用戶列表</h2>
            <div style="margin-bottom: 15px;">
                <button onclick="loadUsers()" class="btn">🔄 刷新列表</button>
                <input type="text" id="search-input" placeholder="搜尋用戶..." class="search-box" onkeyup="filterUsers()">
            </div>
            <table class="user-table" id="users-table">
                <thead>
                    <tr>
                        <th>顯示名稱</th>
                        <th>UUID (前16位)</th>
                        <th>狀態</th>
                        <th>到期時間</th>
                        <th>登入次數</th>
                        <th>創建時間</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="users-tbody">
                    <tr><td colspan="7" style="text-align: center;">載入中...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let allUsers = [];
        const ADMIN_TOKEN = prompt('請輸入管理員密碼:');
        if (!ADMIN_TOKEN) {
            alert('需要管理員權限');
            window.location.href = '/';
        }

        // 載入用戶列表
        async function loadUsers() {
            try {
                const response = await fetch('/admin/users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                const data = await response.json();
                
                if (data.success) {
                    allUsers = data.users;
                    renderUsers(allUsers);
                    updateStats(allUsers);
                } else {
                    alert('載入失敗: ' + data.error);
                }
            } catch (error) {
                alert('載入錯誤: ' + error.message);
            }
        }

        // 渲染用戶列表
        function renderUsers(users) {
            const tbody = document.getElementById('users-tbody');
            tbody.innerHTML = '';
            
            users.forEach(user => {
                const row = document.createElement('tr');
                const isActive = user.active;
                const isExpired = user.expires_at && new Date(user.expires_at) < new Date();
                
                row.innerHTML = `
                    <td>${user.display_name}</td>
                    <td><code>${user.uuid_preview}</code></td>
                    <td class="${isActive ? 'status-active' : 'status-inactive'}">
                        ${isActive ? '✅ 啟用' : '❌ 停用'}
                        ${isExpired ? ' (已過期)' : ''}
                    </td>
                    <td>${user.expires_at || '永久'}</td>
                    <td>${user.login_count}</td>
                    <td>${user.created_at}</td>
                    <td>
                        <button onclick="editUser('${user.document_id}', '${user.display_name}')" class="btn">編輯</button>
                        <button onclick="toggleUser('${user.document_id}', ${!isActive})" class="btn btn-warning">
                            ${isActive ? '停用' : '啟用'}
                        </button>
                        <button onclick="deleteUser('${user.document_id}', '${user.display_name}')" class="btn btn-danger">刪除</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // 搜尋過濾
        function filterUsers() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const filteredUsers = allUsers.filter(user => 
                user.display_name.toLowerCase().includes(searchTerm) ||
                user.uuid_preview.toLowerCase().includes(searchTerm)
            );
            renderUsers(filteredUsers);
        }

        // 更新統計
        function updateStats(users) {
            const total = users.length;
            const active = users.filter(u => u.active).length;
            const expired = users.filter(u => u.expires_at && new Date(u.expires_at) < new Date()).length;
            
            document.getElementById('total-users').textContent = total;
            document.getElementById('active-users').textContent = active;
            document.getElementById('expired-users').textContent = expired;
        }

        // 創建用戶
        document.getElementById('create-user-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const uuid = document.getElementById('new-uuid').value;
            const displayName = document.getElementById('new-display-name').value;
            const days = document.getElementById('new-days').value;
            
            try {
                const response = await fetch('/admin/create-user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({
                        uuid: uuid,
                        display_name: displayName,
                        days: parseInt(days)
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('用戶創建成功!');
                    document.getElementById('create-user-form').reset();
                    loadUsers();
                } else {
                    alert('創建失敗: ' + data.error);
                }
            } catch (error) {
                alert('創建錯誤: ' + error.message);
            }
        });

        // 編輯用戶
        async function editUser(documentId, currentName) {
            const newName = prompt('新的顯示名稱:', currentName);
            if (!newName || newName === currentName) return;
            
            const newDays = prompt('延長有效期天數:', '30');
            if (!newDays) return;
            
            try {
                const response = await fetch(`/admin/users/${documentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({
                        display_name: newName,
                        extend_days: parseInt(newDays)
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('用戶更新成功!');
                    loadUsers();
                } else {
                    alert('更新失敗: ' + data.error);
                }
            } catch (error) {
                alert('更新錯誤: ' + error.message);
            }
        }

        // 啟用/停用用戶
        async function toggleUser(documentId, newStatus) {
            try {
                const response = await fetch(`/admin/users/${documentId}/toggle`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({ active: newStatus })
                });
                
                const data = await response.json();
                if (data.success) {
                    loadUsers();
                } else {
                    alert('操作失敗: ' + data.error);
                }
            } catch (error) {
                alert('操作錯誤: ' + error.message);
            }
        }

        // 刪除用戶
        async function deleteUser(documentId, displayName) {
            if (!confirm(`確定要刪除用戶 "${displayName}" 嗎？此操作無法撤銷！`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/users/${documentId}`, {
                    method: 'DELETE',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('用戶已刪除');
                    loadUsers();
                } else {
                    alert('刪除失敗: ' + data.error);
                }
            } catch (error) {
                alert('刪除錯誤: ' + error.message);
            }
        }

        // 頁面載入時自動載入用戶
        loadUsers();
    </script>
</body>
</html>
"""

def generate_secure_uuid():
    """生成安全的UUID"""
    random_part = uuid_lib.uuid4().hex[:12]
    timestamp = datetime.now().strftime('%Y%m%d')
    return f"artale_{random_part}_{timestamp}"

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    """管理員面板"""
    return render_template_string(ADMIN_TEMPLATE)

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    """獲取所有用戶"""
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        users_ref = db.collection('authorized_users')
        users = users_ref.stream()
        
        user_list = []
        for user in users:
            user_data = user.to_dict()
            
            # 處理時間格式
            created_at = user_data.get('created_at')
            if hasattr(created_at, 'strftime'):
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                created_at_str = str(created_at)[:16] if created_at else 'Unknown'
            
            expires_at = user_data.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at_str = expires_at.split('T')[0] + ' ' + expires_at.split('T')[1][:5]
                else:
                    expires_at_str = str(expires_at)[:16]
            else:
                expires_at_str = None
            
            user_list.append({
                'document_id': user.id,
                'uuid_preview': user_data.get('original_uuid', user.id[:16] + '...'),
                'original_uuid': user_data.get('original_uuid', 'Unknown'),
                'display_name': user_data.get('display_name', 'Unknown'),
                'active': user_data.get('active', False),
                'expires_at': expires_at_str,
                'login_count': user_data.get('login_count', 0),
                'created_at': created_at_str,
                'permissions': user_data.get('permissions', {}),
                'notes': user_data.get('notes', '')
            })
        
        # 按創建時間排序
        user_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total_count': len(user_list)
        })
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/create-user', methods=['POST'])
def create_user_admin():
    """創建新用戶（管理員）"""
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        uuid_string = data.get('uuid', '').strip()
        display_name = data.get('display_name', '').strip()
        days_valid = data.get('days', 30)
        
        if not uuid_string or not display_name:
            return jsonify({'success': False, 'error': 'UUID 和顯示名稱為必填'}), 400
        
        # 檢查 UUID 是否已存在
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        
        if user_ref.get().exists:
            return jsonify({'success': False, 'error': 'UUID 已存在'}), 400
        
        # 創建用戶
        expires_at = None
        if days_valid > 0:
            expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
        
        user_data = {
            "original_uuid": uuid_string,  # 🔥 新增：存儲原始 UUID
            "display_name": display_name,
            "permissions": {
                "script_access": True,
                "config_modify": True
            },
            "active": True,
            "created_at": datetime.now(),
            "created_by": "admin_dashboard",
            "login_count": 0,
            "notes": f"管理員創建 - {datetime.now().strftime('%Y-%m-%d')}"
        }
        
        if expires_at:
            user_data["expires_at"] = expires_at
        
        user_ref.set(user_data)
        
        return jsonify({
            'success': True,
            'message': '用戶創建成功',
            'uuid': uuid_string,
            'display_name': display_name
        })
        
    except Exception as e:
        logger.error(f"Create user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/users/<document_id>', methods=['PUT'])
def update_user_admin(document_id):
    """更新用戶資訊"""
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_ref = db.collection('authorized_users').document(document_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        update_data = {}
        
        # 更新顯示名稱
        if 'display_name' in data:
            update_data['display_name'] = data['display_name']
        
        # 延長有效期
        if 'extend_days' in data:
            extend_days = data['extend_days']
            current_data = user_doc.to_dict()
            current_expires = current_data.get('expires_at')
            
            if current_expires:
                if isinstance(current_expires, str):
                    current_expires = datetime.fromisoformat(current_expires.replace('Z', ''))
                
                # 如果已過期，從現在開始計算
                if current_expires < datetime.now():
                    new_expires = datetime.now() + timedelta(days=extend_days)
                else:
                    new_expires = current_expires + timedelta(days=extend_days)
            else:
                # 如果原本是永久，從現在開始計算
                new_expires = datetime.now() + timedelta(days=extend_days)
            
            update_data['expires_at'] = new_expires.isoformat()
        
        update_data['updated_at'] = datetime.now()
        update_data['updated_by'] = 'admin_dashboard'
        
        user_ref.update(update_data)
        
        return jsonify({
            'success': True,
            'message': '用戶資訊已更新'
        })
        
    except Exception as e:
        logger.error(f"Update user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/users/<document_id>/toggle', methods=['PUT'])
def toggle_user_status(document_id):
    """啟用/停用用戶"""
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        new_status = data.get('active', True)
        
        user_ref = db.collection('authorized_users').document(document_id)
        if not user_ref.get().exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        user_ref.update({
            'active': new_status,
            'status_changed_at': datetime.now(),
            'status_changed_by': 'admin_dashboard'
        })
        
        return jsonify({
            'success': True,
            'message': f'用戶已{"啟用" if new_status else "停用"}'
        })
        
    except Exception as e:
        logger.error(f"Toggle user status error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/users/<document_id>', methods=['DELETE'])
def delete_user_admin(document_id):
    """刪除用戶"""
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        user_ref = db.collection('authorized_users').document(document_id)
        if not user_ref.get().exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        # 刪除用戶
        user_ref.delete()
        
        return jsonify({
            'success': True,
            'message': '用戶已刪除'
        })
        
    except Exception as e:
        logger.error(f"Delete user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # 這裡只處理開發環境的直接運行
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🔧 開發模式啟動:")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Firebase initialized: {firebase_initialized}")
    logger.info(f"   Database object exists: {db is not None}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
