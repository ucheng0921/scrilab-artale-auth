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
from collections import defaultdict
import threading

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
session_store = {}

# 🔥 新增：進階安全監控
class SecurityMonitor:
    def __init__(self):
        self.ip_stats = defaultdict(lambda: {
            'requests': [],
            'failed_attempts': 0,
            'last_blocked': None,
            'total_requests_today': 0,
            'suspicious_patterns': []
        })
        self.global_stats = {
            'total_requests_today': 0,
            'failed_auth_today': 0,
            'blocked_ips': set(),
            'alert_triggered': False
        }
        self.lock = threading.Lock()
        
    def record_request(self, ip, endpoint, success=True):
        with self.lock:
            now = time.time()
            today = datetime.now().date()
            
            # 清理舊數據（保留24小時）
            self.ip_stats[ip]['requests'] = [
                req for req in self.ip_stats[ip]['requests'] 
                if now - req['time'] < 86400
            ]
            
            # 記錄請求
            self.ip_stats[ip]['requests'].append({
                'time': now,
                'endpoint': endpoint,
                'success': success,
                'date': today
            })
            
            if not success:
                self.ip_stats[ip]['failed_attempts'] += 1
                self.global_stats['failed_auth_today'] += 1
            
            # 檢測可疑模式
            self._detect_suspicious_patterns(ip)
            
            # 更新全局統計
            self.global_stats['total_requests_today'] += 1
            
            # 檢查是否需要觸發警報
            self._check_alert_thresholds()
    
    def is_ip_blocked(self, ip):
        with self.lock:
            ip_data = self.ip_stats[ip]
            now = time.time()
            
            # 檢查是否在封鎖期間內
            if ip_data['last_blocked']:
                block_duration = self._get_block_duration(ip)
                if now - ip_data['last_blocked'] < block_duration:
                    return True
                else:
                    # 解除封鎖
                    ip_data['last_blocked'] = None
                    if ip in self.global_stats['blocked_ips']:
                        self.global_stats['blocked_ips'].remove(ip)
            
            # 檢查是否需要封鎖
            recent_failures = sum(1 for req in ip_data['requests'] 
                                if not req['success'] and now - req['time'] < 300)  # 5分鐘內
            
            if recent_failures >= 3:  # 5分鐘內3次失敗就封鎖
                self._block_ip(ip)
                return True
                
            return False
    
    def _detect_suspicious_patterns(self, ip):
        """檢測可疑行為模式"""
        ip_data = self.ip_stats[ip]
        now = time.time()
        
        # 檢測高頻請求
        recent_requests = [req for req in ip_data['requests'] 
                          if now - req['time'] < 60]  # 1分鐘內
        
        if len(recent_requests) > 20:  # 1分鐘超過20次請求
            ip_data['suspicious_patterns'].append({
                'type': 'high_frequency',
                'time': now,
                'count': len(recent_requests)
            })
            logger.warning(f"🚨 高頻請求檢測: IP {ip} 在1分鐘內發送了 {len(recent_requests)} 次請求")
    
    def _block_ip(self, ip):
        """封鎖IP地址"""
        self.ip_stats[ip]['last_blocked'] = time.time()
        self.global_stats['blocked_ips'].add(ip)
        logger.warning(f"🚫 IP已被封鎖: {ip}")
    
    def _get_block_duration(self, ip):
        """獲取封鎖持續時間（根據違規次數遞增）"""
        violations = len(self.ip_stats[ip]['suspicious_patterns'])
        if violations <= 1:
            return 300  # 5分鐘
        elif violations <= 3:
            return 900  # 15分鐘
        elif violations <= 5:
            return 3600  # 1小時
        else:
            return 86400  # 24小時
    
    def _check_alert_thresholds(self):
        """檢查是否需要觸發安全警報"""
        if (self.global_stats['failed_auth_today'] > 100 and 
            not self.global_stats['alert_triggered']):
            self.global_stats['alert_triggered'] = True
            logger.error(f"🚨🚨🚨 安全警報：今日認證失敗次數已達 {self.global_stats['failed_auth_today']} 次！")
            # 這裡可以加入通知機制，例如發送郵件或 Slack 訊息
    
    def get_stats(self):
        """獲取安全統計信息"""
        with self.lock:
            return {
                'blocked_ips_count': len(self.global_stats['blocked_ips']),
                'total_requests_today': self.global_stats['total_requests_today'],
                'failed_auth_today': self.global_stats['failed_auth_today'],
                'alert_status': self.global_stats['alert_triggered']
            }

# 初始化安全監控
security_monitor = SecurityMonitor()

# 🔥 新增：Firebase 使用量監控
class FirebaseMonitor:
    def __init__(self):
        self.daily_reads = 0
        self.daily_writes = 0
        self.last_reset = datetime.now().date()
        self.read_limit = int(os.environ.get('FIREBASE_DAILY_READ_LIMIT', 50000))  # 每日讀取限制
        self.write_limit = int(os.environ.get('FIREBASE_DAILY_WRITE_LIMIT', 20000))  # 每日寫入限制
        
    def record_read(self, count=1):
        self._check_reset_daily()
        self.daily_reads += count
        if self.daily_reads > self.read_limit:
            logger.error(f"🔥 Firebase 讀取限制超標: {self.daily_reads}/{self.read_limit}")
            raise Exception("Firebase daily read limit exceeded")
    
    def record_write(self, count=1):
        self._check_reset_daily()
        self.daily_writes += count
        if self.daily_writes > self.write_limit:
            logger.error(f"🔥 Firebase 寫入限制超標: {self.daily_writes}/{self.write_limit}")
            raise Exception("Firebase daily write limit exceeded")
    
    def _check_reset_daily(self):
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_reads = 0
            self.daily_writes = 0
            self.last_reset = today
            logger.info(f"🔄 Firebase 使用量統計已重置: {today}")
    
    def get_usage(self):
        self._check_reset_daily()
        return {
            'daily_reads': self.daily_reads,
            'daily_writes': self.daily_writes,
            'read_limit': self.read_limit,
            'write_limit': self.write_limit,
            'read_percentage': (self.daily_reads / self.read_limit) * 100,
            'write_percentage': (self.daily_writes / self.write_limit) * 100
        }

# 初始化 Firebase 監控
firebase_monitor = FirebaseMonitor()

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
        firebase_monitor.record_write(1)  # 記錄寫入
        logger.info("Firestore 寫入測試成功")
        
        # 嘗試讀取測試數據
        test_doc = test_doc_ref.get()
        firebase_monitor.record_read(1)  # 記錄讀取
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

def advanced_rate_limit(max_requests=5, time_window=300, endpoint_type='auth'):
    """進階速率限制裝飾器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true':
                return f(*args, **kwargs)
            
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # 🔥 檢查IP是否被封鎖
            if security_monitor.is_ip_blocked(client_ip):
                security_monitor.record_request(client_ip, f.__name__, False)
                logger.warning(f"🚫 封鎖的IP嘗試訪問: {client_ip}")
                return jsonify({
                    'success': False,
                    'error': 'IP address temporarily blocked due to suspicious activity'
                }), 429
            
            # 記錄請求
            security_monitor.record_request(client_ip, f.__name__, True)
            
            # 原有的速率限制邏輯
            now = time.time()
            if client_ip not in session_store:
                session_store[client_ip] = {'requests': []}
            
            # 清理過期記錄
            session_store[client_ip]['requests'] = [
                req_time for req_time in session_store[client_ip]['requests'] 
                if now - req_time < time_window
            ]
            
            # 🔥 動態調整限制（根據端點類型）
            if endpoint_type == 'auth':
                # 認證端點更嚴格
                effective_limit = max_requests
            elif endpoint_type == 'validate':
                # 驗證端點稍微寬鬆
                effective_limit = max_requests * 3
            else:
                effective_limit = max_requests
            
            # 檢查是否超過限制
            if len(session_store[client_ip]['requests']) >= effective_limit:
                security_monitor.record_request(client_ip, f.__name__, False)
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'success': False,
                    'error': f'Rate limit exceeded. Max {effective_limit} requests per {time_window//60} minutes.'
                }), 429
            
            # 記錄此次請求
            session_store[client_ip]['requests'].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def security_checks():
    """請求前安全檢查"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # 🔥 檢查 User-Agent（阻擋明顯的機器人）
    user_agent = request.headers.get('User-Agent', '').lower()
    suspicious_agents = ['curl', 'wget', 'python', 'bot', 'crawler', 'spider']
    
    if any(agent in user_agent for agent in suspicious_agents):
        logger.warning(f"🤖 可疑User-Agent: {user_agent} from {client_ip}")
        # 可以選擇直接阻擋或只是記錄
        # return jsonify({'error': 'Automated requests not allowed'}), 403
    
    # 🔥 檢查請求大小
    if request.content_length and request.content_length > 1024 * 100:  # 100KB
        logger.warning(f"📦 過大請求: {request.content_length} bytes from {client_ip}")
        return jsonify({'error': 'Request too large'}), 413
    
    # 強制 HTTPS（生產環境）
    if (not request.is_secure and 
        request.headers.get('X-Forwarded-Proto') != 'https' and
        os.environ.get('FLASK_ENV') == 'production'):
        return redirect(request.url.replace('http://', 'https://'), code=301)

@app.after_request
def after_request(response):
    """添加安全標頭"""
    # 🔥 增強安全標頭
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    # 🔥 隱藏技術資訊
    response.headers.pop('Server', None)
    
    # 記錄請求
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    logger.info(f"{client_ip} - {request.method} {request.path} - {response.status_code}")
    
    return response

@app.route('/', methods=['GET'])
def root():
    """根路徑端點"""
    security_stats = security_monitor.get_stats()
    firebase_usage = firebase_monitor.get_usage()
    
    return jsonify({
        'service': 'Artale Authentication Service',
        'version': '1.1.0',  # 版本升級
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'login': '/auth/login',
            'logout': '/auth/logout',
            'validate': '/auth/validate',
            'security': '/security/stats'  # 新增安全統計端點
        },
        'firebase_connected': firebase_initialized,
        'security_status': {
            'blocked_ips': security_stats['blocked_ips_count'],
            'requests_today': security_stats['total_requests_today'],
            'alert_status': 'active' if security_stats['alert_status'] else 'normal'
        },
        'firebase_usage': {
            'read_usage': f"{firebase_usage['read_percentage']:.1f}%",
            'write_usage': f"{firebase_usage['write_percentage']:.1f}%"
        }
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
    
    # 🔥 新增詳細健康檢查
    security_stats = security_monitor.get_stats()
    firebase_usage = firebase_monitor.get_usage()
    
    health_status = 'healthy'
    if not firebase_status:
        health_status = 'critical'
    elif (firebase_usage['read_percentage'] > 80 or 
          firebase_usage['write_percentage'] > 80):
        health_status = 'warning'
    elif security_stats['alert_status']:
        health_status = 'degraded'
    
    return jsonify({
        'status': health_status,
        'timestamp': datetime.now().isoformat(),
        'firebase_connected': firebase_status,
        'firebase_initialized': firebase_initialized,
        'db_object_exists': db is not None,
        'service': 'artale-auth-service',
        'version': '1.1.0',
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'security': security_stats,
        'firebase_usage': firebase_usage,
        'system_limits': {
            'firebase_read_limit': firebase_monitor.read_limit,
            'firebase_write_limit': firebase_monitor.write_limit
        }
    })

@app.route('/security/stats', methods=['GET'])
def security_stats():
    """🔥 新增：安全統計端點"""
    # 簡單的管理員驗證
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = security_monitor.get_stats()
    firebase_usage = firebase_monitor.get_usage()
    
    return jsonify({
        'security': stats,
        'firebase_usage': firebase_usage,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/auth/login', methods=['POST'])
@advanced_rate_limit(max_requests=3, time_window=300, endpoint_type='auth')  # 🔥 更嚴格：5分鐘3次
def login():
    """用戶登入端點 - 加強安全版本"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    try:
        # 🔥 檢查 Firebase 使用量
        firebase_usage = firebase_monitor.get_usage()
        if firebase_usage['read_percentage'] > 90:
            logger.error(f"🔥 Firebase 讀取使用量過高: {firebase_usage['read_percentage']:.1f}%")
            return jsonify({
                'success': False,
                'error': 'Service temporarily unavailable due to high load'
            }), 503
        
        # 檢查 Firebase 狀態
        if not firebase_initialized or db is None:
            logger.error("Firebase 未初始化或數據庫對象為 None")
            return jsonify({
                'success': False,
                'error': 'Authentication service unavailable. Please try again later.'
            }), 503
        
        data = request.get_json()
        
        if not data or 'uuid' not in data:
            security_monitor.record_request(client_ip, 'login', False)
            return jsonify({
                'success': False,
                'error': 'Missing UUID'
            }), 400
        
        uuid = data['uuid'].strip()
        force_login = data.get('force_login', True)
        
        # 🔥 增強UUID驗證
        if not uuid or len(uuid) < 10 or len(uuid) > 100:
            security_monitor.record_request(client_ip, 'login', False)
            return jsonify({
                'success': False,
                'error': 'Invalid UUID format'
            }), 400
        
        # 記錄登入嘗試
        logger.info(f"Login attempt from {client_ip} for UUID: {uuid[:8]}...")
        
        # 呼叫認證邏輯
        success, message, user_data = authenticate_user(uuid, force_login, client_ip)
        
        if success:
            # 生成會話令牌
            session_token = generate_session_token(uuid, client_ip)
            
            security_monitor.record_request(client_ip, 'login', True)
            logger.info(f"Login successful for UUID: {uuid[:8]}...")
            
            return jsonify({
                'success': True,
                'message': message,
                'user_data': user_data,
                'session_token': session_token
            })
        else:
            security_monitor.record_request(client_ip, 'login', False)
            logger.warning(f"Login failed for UUID: {uuid[:8]}... - {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 401
            
    except Exception as e:
        security_monitor.record_request(client_ip, 'login', False)
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
@advanced_rate_limit(max_requests=60, time_window=60, endpoint_type='validate')  # 🔥 每分鐘60次驗證
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
    """認證用戶 - 加強監控版本"""
    try:
        # 再次檢查 db 對象
        if db is None:
            logger.error("authenticate_user: db 對象為 None")
            return False, "認證服務不可用", None
        
        uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
        
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
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
        
        # 🔥 記錄 Firebase 寫入操作
        firebase_monitor.record_write(1)
        
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
        
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
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
        
        # 🔥 記錄 Firebase 寫入操作
        firebase_monitor.record_write(1)
            
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
# 🎛️ 用戶管理功能 - 增強版
# ================================

# 🔥 更新管理界面 HTML 模板，加入安全監控
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Artale Script 用戶管理 - 安全增強版</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #1976d2, #42a5f5); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert-section { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
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
        .btn-security { background: #9c27b0; }
        .btn-security:hover { background: #7b1fa2; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; font-weight: bold; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; flex: 1; min-width: 200px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { margin: 0; font-size: 2em; color: #1976d2; }
        .stat-card.warning h3 { color: #ff9800; }
        .stat-card.danger h3 { color: #f44336; }
        .form-row { display: flex; gap: 20px; }
        .form-row .form-group { flex: 1; }
        .search-box { width: 300px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-left: 10px; }
        .progress-bar { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; transition: width 0.3s ease; }
        .progress-safe { background: #4CAF50; }
        .progress-warning { background: #ff9800; }
        .progress-danger { background: #f44336; }
        .security-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .tabs { display: flex; border-bottom: 2px solid #1976d2; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e0e0e0; border: none; cursor: pointer; }
        .tab.active { background: #1976d2; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Artale Script 用戶管理系統 - 安全增強版</h1>
            <p>管理所有授權用戶、監控安全狀態和Firebase使用量</p>
        </div>
        
        <!-- 系統狀態警報 -->
        <div id="system-alerts" class="alert-section" style="display: none;">
            <h3>⚠️ 系統警報</h3>
            <div id="alert-content"></div>
        </div>
        
        <!-- 選項卡導航 -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">概覽</button>
            <button class="tab" onclick="showTab('users')">用戶管理</button>
            <button class="tab" onclick="showTab('security')">安全監控</button>
            <button class="tab" onclick="showTab('firebase')">Firebase監控</button>
        </div>
        
        <!-- 概覽標籤 -->
        <div id="overview" class="tab-content active">
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
                <div class="stat-card" id="blocked-ips-card">
                    <h3 id="blocked-ips">-</h3>
                    <p>封鎖IP數</p>
                </div>
                <div class="stat-card" id="requests-today-card">
                    <h3 id="requests-today">-</h3>
                    <p>今日請求數</p>
                </div>
            </div>
            
            <!-- Firebase 使用量 -->
            <div class="section">
                <h2>📊 Firebase 使用量</h2>
                <div class="security-stats">
                    <div>
                        <h4>每日讀取次數</h4>
                        <div class="progress-bar">
                            <div id="read-progress" class="progress-fill progress-safe" style="width: 0%"></div>
                        </div>
                        <p id="read-stats">0 / 50000 (0%)</p>
                    </div>
                    <div>
                        <h4>每日寫入次數</h4>
                        <div class="progress-bar">
                            <div id="write-progress" class="progress-fill progress-safe" style="width: 0%"></div>
                        </div>
                        <p id="write-stats">0 / 20000 (0%)</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 用戶管理標籤 -->
        <div id="users" class="tab-content">
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
        
        <!-- 安全監控標籤 -->
        <div id="security" class="tab-content">
            <div class="section">
                <h2>🛡️ 安全監控</h2>
                <button onclick="loadSecurityStats()" class="btn btn-security">🔄 刷新安全統計</button>
                <div id="security-details" class="security-stats" style="margin-top: 20px;">
                    <div>
                        <h4>今日失敗認證次數</h4>
                        <h3 id="failed-auth" style="color: #f44336;">-</h3>
                    </div>
                    <div>
                        <h4>警報狀態</h4>
                        <h3 id="alert-status">-</h3>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Firebase監控標籤 -->
        <div id="firebase" class="tab-content">
            <div class="section">
                <h2>🔥 Firebase 詳細監控</h2>
                <div id="firebase-details">
                    <p>載入中...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let allUsers = [];
        const ADMIN_TOKEN = prompt('請輸入管理員密碼:');
        if (!ADMIN_TOKEN) {
            alert('需要管理員權限');
            window.location.href = '/';
        }

        // 選項卡切換
        function showTab(tabName) {
            // 隱藏所有內容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 顯示選中的內容
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // 載入相應數據
            if (tabName === 'security') {
                loadSecurityStats();
            } else if (tabName === 'firebase') {
                loadFirebaseStats();
            }
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

        // 載入系統狀態
        async function loadSystemStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                updateFirebaseUsage(data.firebase_usage);
                updateSecurityOverview(data.security);
                
                // 檢查警報
                checkSystemAlerts(data);
                
            } catch (error) {
                console.error('系統狀態載入錯誤:', error);
            }
        }

        // 載入安全統計
        async function loadSecurityStats() {
            try {
                const response = await fetch('/security/stats', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                const data = await response.json();
                
                if (data.security) {
                    document.getElementById('failed-auth').textContent = data.security.failed_auth_today;
                    document.getElementById('alert-status').textContent = 
                        data.security.alert_status ? '🚨 警報啟動' : '✅ 正常';
                    document.getElementById('alert-status').style.color = 
                        data.security.alert_status ? '#f44336' : '#4CAF50';
                }
            } catch (error) {
                console.error('安全統計載入錯誤:', error);
            }
        }

        // 載入Firebase統計
        async function loadFirebaseStats() {
            try {
                const response = await fetch('/security/stats', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                const data = await response.json();
                
                if (data.firebase_usage) {
                    const usage = data.firebase_usage;
                    document.getElementById('firebase-details').innerHTML = `
                        <div class="security-stats">
                            <div>
                                <h4>讀取使用量</h4>
                                <p>${usage.daily_reads} / ${usage.read_limit}</p>
                                <p>${usage.read_percentage.toFixed(1)}%</p>
                            </div>
                            <div>
                                <h4>寫入使用量</h4>
                                <p>${usage.daily_writes} / ${usage.write_limit}</p>
                                <p>${usage.write_percentage.toFixed(1)}%</p>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Firebase統計載入錯誤:', error);
            }
        }

        // 更新Firebase使用量顯示
        function updateFirebaseUsage(usage) {
            if (!usage) return;
            
            const readPercent = parseFloat(usage.read_usage.replace('%', ''));
            const writePercent = parseFloat(usage.write_usage.replace('%', ''));
            
            // 更新進度條
            const readProgress = document.getElementById('read-progress');
            const writeProgress = document.getElementById('write-progress');
            
            readProgress.style.width = readPercent + '%';
            writeProgress.style.width = writePercent + '%';
            
            // 更新顏色
            readProgress.className = 'progress-fill ' + getProgressColor(readPercent);
            writeProgress.className = 'progress-fill ' + getProgressColor(writePercent);
            
            // 更新統計文字
            document.getElementById('read-stats').textContent = usage.read_usage;
            document.getElementById('write-stats').textContent = usage.write_usage;
        }

        function getProgressColor(percent) {
            if (percent < 70) return 'progress-safe';
            if (percent < 90) return 'progress-warning';
            return 'progress-danger';
        }

        // 更新安全概覽
        function updateSecurityOverview(security) {
            if (!security) return;
            
            document.getElementById('blocked-ips').textContent = security.blocked_ips || 0;
            document.getElementById('requests-today').textContent = security.requests_today || 0;
            
            // 根據數據更新卡片樣式
            const blockedCard = document.getElementById('blocked-ips-card');
            const requestsCard = document.getElementById('requests-today-card');
            
            if (security.blocked_ips > 0) {
                blockedCard.classList.add('warning');
            }
            
            if (security.requests_today > 1000) {
                requestsCard.classList.add('warning');
            }
        }

        // 檢查系統警報
        function checkSystemAlerts(data) {
            const alerts = [];
            
            if (data.firebase_usage) {
                const readPercent = parseFloat(data.firebase_usage.read_usage.replace('%', ''));
                const writePercent = parseFloat(data.firebase_usage.write_usage.replace('%', ''));
                
                if (readPercent > 80) {
                    alerts.push(`⚠️ Firebase 讀取使用量過高: ${readPercent.toFixed(1)}%`);
                }
                if (writePercent > 80) {
                    alerts.push(`⚠️ Firebase 寫入使用量過高: ${writePercent.toFixed(1)}%`);
                }
            }
            
            if (data.security && data.security.alert_status === 'active') {
                alerts.push('🚨 安全警報已觸發');
            }
            
            const alertSection = document.getElementById('system-alerts');
            const alertContent = document.getElementById('alert-content');
            
            if (alerts.length > 0) {
                alertContent.innerHTML = alerts.join('<br>');
                alertSection.style.display = 'block';
            } else {
                alertSection.style.display = 'none';
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

        // 頁面載入時自動載入數據
        loadUsers();
        loadSystemStatus();
        
        // 定期更新狀態
        setInterval(loadSystemStatus, 30000); // 每30秒更新一次
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
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
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
        
        # 🔥 增強UUID驗證
        if len(uuid_string) < 10 or len(uuid_string) > 100:
            return jsonify({'success': False, 'error': 'UUID長度必須在10-100字符之間'}), 400
        
        # 檢查 UUID 是否已存在
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
        user_ref = db.collection('authorized_users').document(uuid_hash)
        
        if user_ref.get().exists:
            return jsonify({'success': False, 'error': 'UUID 已存在'}), 400
        
        # 創建用戶
        expires_at = None
        if days_valid > 0:
            expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
        
        user_data = {
            "original_uuid": uuid_string,
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
        
        # 🔥 記錄 Firebase 寫入操作
        firebase_monitor.record_write(1)
        
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
        
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
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
        
        # 🔥 記錄 Firebase 寫入操作
        firebase_monitor.record_write(1)
        
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
        
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
        user_ref = db.collection('authorized_users').document(document_id)
        if not user_ref.get().exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        # 🔥 記錄 Firebase 寫入操作
        firebase_monitor.record_write(1)
        
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
        # 🔥 記錄 Firebase 讀取操作
        firebase_monitor.record_read(1)
        
        user_ref = db.collection('authorized_users').document(document_id)
        if not user_ref.get().exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        # 🔥 記錄 Firebase 寫入操作
        firebase_monitor.record_write(1)
        
        # 刪除用戶
        user_ref.delete()
        
        return jsonify({
            'success': True,
            'message': '用戶已刪除'
        })
        
    except Exception as e:
        logger.error(f"Delete user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# 🔥 新增：緊急停機端點
@app.route('/admin/emergency-shutdown', methods=['POST'])
def emergency_shutdown():
    """緊急停機端點"""
    admin_token = request.headers.get('Admin-Token')
    if admin_token != os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        # 清空所有會話
        session_store.clear()
        
        # 記錄緊急停機
        logger.critical("🚨 緊急停機已啟動！所有用戶會話已清除")
        
        return jsonify({
            'success': True,
            'message': '緊急停機成功，所有用戶會話已清除'
        })
        
    except Exception as e:
        logger.error(f"Emergency shutdown error: {str(e)}")
        return jsonify({'success': False, 'error': 'Emergency shutdown failed'}), 500

if __name__ == '__main__':
    # 這裡只處理開發環境的直接運行
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🔧 開發模式啟動:")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Firebase initialized: {firebase_initialized}")
    logger.info(f"   Database object exists: {db is not None}")
    logger.info(f"   Security monitoring: Enabled")
    logger.info(f"   Firebase monitoring: Enabled")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
