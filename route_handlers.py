"""
route_handlers.py - 將 app.py 中的路由處理邏輯分離到這個檔案
"""
from flask import request, jsonify, redirect, render_template_string
import logging
from functools import wraps
from datetime import datetime
import hashlib
import time
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

# 從 app.py 移過來的變數和函數
blocked_ips = {}
rate_limit_store = defaultdict(list)
cleanup_lock = threading.Lock()

def get_client_ip():
    """獲取客戶端真實 IP"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).split(',')[0].strip()

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

def rate_limit(max_requests=3, time_window=300, block_on_exceed=True):
    """速率限制裝飾器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            import os
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

class RouteHandlers:
    """路由處理器類別"""
    
    def __init__(self, db, session_manager, payment_service):
        self.db = db
        self.session_manager = session_manager
        self.payment_service = payment_service
    
    def root(self):
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
                '🛍️ 商品展示頁面',
                '📖 操作手冊',
                '⚖️ 免責聲明'
            ],
            'endpoints': {
                'health': '/health',
                'login': '/auth/login',
                'logout': '/auth/logout',
                'validate': '/auth/validate',
                'admin': '/admin',
                'session_stats': '/session-stats',
                'products': '/products',
                'manual': '/manual',
                'disclaimer': '/disclaimer'
            },
            'firebase_connected': self.db is not None
        })
    
    def health_check(self):
        """健康檢查端點"""
        firebase_status = self.db is not None
        
        # 獲取 session 統計
        try:
            session_stats_data = self.session_manager.get_session_stats()
        except Exception as e:
            session_stats_data = {'error': str(e)}
        
        return jsonify({
            'status': 'healthy' if firebase_status else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'firebase_connected': firebase_status,
            'service': 'artale-auth-service',
            'version': '2.2.0',
            'admin_panel': 'available at /admin',
            'manual': 'available at /manual',
            'session_storage': session_stats_data
        })
    
    @rate_limit(max_requests=5, time_window=300, block_on_exceed=True)
    def login(self):
        """用戶登入端點"""
        try:
            if not self.db:
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
            
            client_ip = get_client_ip()
            logger.info(f"Login attempt from {client_ip} for UUID: {uuid[:8]}...")
            
            # 呼叫認證邏輯
            success, message, user_data = self.authenticate_user(uuid, force_login, client_ip)
            
            if success:
                # 生成會話令牌
                session_token = self.generate_session_token(uuid, client_ip)
                
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
    
    def logout(self):
        """用戶登出端點"""
        try:
            data = request.get_json()
            session_token = data.get('session_token') if data else None
            
            if session_token:
                # 撤銷會話令牌
                revoked = self.session_manager.revoke_session_token(session_token)
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
    
    @rate_limit(max_requests=120, time_window=60)
    def validate_session(self):
        """驗證會話令牌"""
        try:
            if not self.db:
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
            is_valid, user_data = self.verify_session_token(session_token)
            
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
    
    def session_stats(self):
        """Session 統計信息"""
        try:
            stats = self.session_manager.get_session_stats()
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
    
    @rate_limit(max_requests=5, time_window=300)
    def manual_cleanup_sessions(self):
        """手動清理過期會話"""
        try:
            deleted_count = self.session_manager.cleanup_expired_sessions()
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
    
    def generate_session_token(self, uuid, client_ip):
        """生成會話令牌"""
        import os
        session_timeout = int(os.environ.get('SESSION_TIMEOUT', 3600))
        return self.session_manager.generate_session_token(uuid, client_ip, session_timeout)
    
    def verify_session_token(self, token):
        """驗證會話令牌"""
        is_valid, session_data = self.session_manager.verify_session_token(token)
        
        if not is_valid:
            return False, None
        
        # 獲取用戶數據
        try:
            uuid = session_data.get('uuid')
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                # 檢查用戶是否仍然活躍
                if not user_data.get('active', False):
                    self.session_manager.revoke_session_token(token)
                    return False, None
                return True, user_data
            else:
                self.session_manager.revoke_session_token(token)
                return False, None
        except Exception as e:
            logger.error(f"User data retrieval error: {str(e)}")
            return False, None
    
    def authenticate_user(self, uuid, force_login=True, client_ip='unknown'):
        """認證用戶"""
        try:
            if self.db is None:
                logger.error("authenticate_user: db 對象為 None")
                return False, "認證服務不可用", None
            
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            
            user_ref = self.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                self.log_unauthorized_attempt(uuid_hash, client_ip)
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
                self.session_manager.terminate_user_sessions(uuid)
            else:
                has_active = self.session_manager.check_existing_session(uuid)
                if has_active:
                    return False, "該帳號已在其他地方登入", None
            
            # 更新登入記錄
            from firebase_admin import firestore
            update_data = {
                'last_login': datetime.now(),
                'login_count': firestore.Increment(1),
                'last_login_ip': client_ip
            }
            
            user_ref.update(update_data)
            
            return True, "認證成功", user_data
            
    def log_unauthorized_attempt(self, uuid_hash, client_ip):
        """記錄未授權登入嘗試"""
        try:
            if self.db is None:
                logger.error("log_unauthorized_attempt: db 對象為 None")
                return
                
            attempts_ref = self.db.collection('unauthorized_attempts')
            attempts_ref.add({
                'uuid_hash': uuid_hash,
                'timestamp': datetime.now(),
                'client_ip': client_ip,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            })
        except Exception as e:
            logger.error(f"Failed to log unauthorized attempt: {str(e)}")

    
    def log_unauthorized_attempt(self, uuid_hash, client_ip):
        """記錄未授權登入嘗試"""
        try:
            attempts_ref = self.db.collection('unauthorized_attempts')
            attempts_ref.add({
                'uuid_hash': uuid_hash,
                'timestamp': datetime.now(),
                'client_ip': client_ip,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            })
        except Exception as e:
            logger.error(f"Failed to log unauthorized attempt: {str(e)}")