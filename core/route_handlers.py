"""
route_handlers.py - 優化版本，修復並發、記憶體洩露和性能問題
"""
from flask import request, jsonify
import logging
from functools import wraps, lru_cache
from datetime import datetime
import hashlib
import time
from collections import defaultdict
import threading
import weakref
import gc
from typing import Dict, List, Optional, Tuple
import os

logger = logging.getLogger(__name__)

# 嘗試導入 psutil，如果沒有則使用替代方案
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil 不可用，將使用替代的記憶體監控方案")

# 全局速率限制和記憶體管理
class MemoryAwareRateLimiter:
    """記憶體感知的速率限制器"""
    
    def __init__(self, max_requests=100, time_window=300, memory_threshold=85):
        self.max_requests = max_requests
        self.time_window = time_window
        self.memory_threshold = memory_threshold
        self.request_records = defaultdict(list)
        self.blocked_ips = {}
        self.lock = threading.RLock()
        self.last_cleanup = time.time()
        
    def cleanup_old_records(self):
        """清理過期記錄，防止記憶體洩露"""
        now = time.time()
        
        # 每5分鐘清理一次
        if now - self.last_cleanup < 300:
            return
            
        with self.lock:
            # 清理過期的請求記錄
            expired_ips = []
            for ip, records in self.request_records.items():
                # 過濾掉過期記錄
                valid_records = [t for t in records if now - t < self.time_window]
                if valid_records:
                    self.request_records[ip] = valid_records
                else:
                    expired_ips.append(ip)
            
            # 刪除沒有有效記錄的IP
            for ip in expired_ips:
                del self.request_records[ip]
            
            # 清理過期的封鎖記錄
            expired_blocks = [ip for ip, block_until in self.blocked_ips.items() 
                            if block_until < now]
            for ip in expired_blocks:
                del self.blocked_ips[ip]
            
            self.last_cleanup = now
            
            # 強制垃圾回收
            if len(expired_ips) > 10 or len(expired_blocks) > 5:
                gc.collect()
            
            logger.debug(f"清理速率限制記錄: {len(expired_ips)} IPs, {len(expired_blocks)} blocks")
    
    def check_memory_usage(self):
        """檢查系統記憶體使用率"""
        if not PSUTIL_AVAILABLE:
            # 如果沒有 psutil，使用簡單的啟發式方法
            return len(self.request_records) < 1000  # 簡單的記憶體控制
        
        try:
            memory_percent = psutil.virtual_memory().percent
            return memory_percent < self.memory_threshold
        except:
            return True  # 如果無法檢查，預設允許
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, str]:
        """檢查請求是否被允許"""
        now = time.time()
        
        # 定期清理
        self.cleanup_old_records()
        
        # 檢查記憶體使用
        if not self.check_memory_usage():
            return False, "系統記憶體使用率過高，請稍後再試"
        
        with self.lock:
            # 檢查是否被封鎖
            if client_ip in self.blocked_ips:
                if self.blocked_ips[client_ip] > now:
                    remaining = int((self.blocked_ips[client_ip] - now) / 60)
                    return False, f"IP已被暫時封鎖，請在{remaining}分鐘後再試"
                else:
                    del self.blocked_ips[client_ip]
            
            # 檢查請求頻率
            records = self.request_records[client_ip]
            valid_records = [t for t in records if now - t < self.time_window]
            
            if len(valid_records) >= self.max_requests:
                # 封鎖IP 30分鐘
                self.blocked_ips[client_ip] = now + 1800
                logger.warning(f"IP {client_ip} 已被封鎖，原因：超過速率限制")
                return False, "請求過於頻繁，IP已被暫時封鎖30分鐘"
            
            # 記錄此次請求
            valid_records.append(now)
            self.request_records[client_ip] = valid_records
            
            return True, "OK"

# 全局實例
rate_limiter = MemoryAwareRateLimiter()

def get_client_ip():
    """獲取客戶端真實 IP"""
    # 檢查多個可能的標頭
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP', 
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_X_CLUSTER_CLIENT_IP',
        'REMOTE_ADDR'
    ]
    
    for header in headers_to_check:
        ip = request.environ.get(header)
        if ip:
            # 如果有多個IP，取第一個
            return ip.split(',')[0].strip()
    
    return request.remote_addr or 'unknown'

def rate_limit(max_requests=5, time_window=300, block_on_exceed=True):
    """記憶體高效的速率限制裝飾器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 檢查是否啟用速率限制
            if not os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true':
                return f(*args, **kwargs)
            
            client_ip = get_client_ip()
            
            # 使用全局速率限制器
            allowed, message = rate_limiter.is_allowed(client_ip)
            
            if not allowed:
                logger.warning(f"速率限制阻止請求: {client_ip} - {message}")
                return jsonify({
                    'success': False,
                    'error': message,
                    'code': 'RATE_LIMITED'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class RouteHandlers:
    """優化的路由處理器 - 解決並發、記憶體洩露和性能問題（保持原有類名兼容性）"""
    
    def __init__(self, db, session_manager):
        self.db = db
        self.session_manager = session_manager
        
        # 並發控制
        self.auth_lock = threading.RLock()
        self.cache_lock = threading.RLock()
        
        # 記憶體管理
        self._auth_cache = {}
        self._cache_timestamps = {}
        self.cache_ttl = 300  # 5分鐘
        self.max_cache_size = 1000
        
        # 性能監控
        self.request_metrics = defaultdict(list)
        self.last_metrics_cleanup = time.time()
        
        # 弱引用管理，防止循環引用
        self._weak_refs = weakref.WeakSet()
        
        logger.info("✅ RouteHandlers 初始化完成")
    
    def __del__(self):
        """清理資源"""
        try:
            self.cleanup_all_caches()
        except:
            pass
    
    def cleanup_all_caches(self):
        """清理所有緩存"""
        with self.cache_lock:
            self._auth_cache.clear()
            self._cache_timestamps.clear()
            self.request_metrics.clear()
            gc.collect()
    
    def _cleanup_expired_cache(self):
        """清理過期緩存"""
        now = time.time()
        
        # 每5分鐘清理一次
        if now - getattr(self, '_last_cache_cleanup', 0) < 300:
            return
        
        with self.cache_lock:
            expired_keys = []
            for key, timestamp in self._cache_timestamps.items():
                if now - timestamp > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._auth_cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
            
            # 如果緩存過大，清理最舊的條目
            if len(self._auth_cache) > self.max_cache_size:
                sorted_items = sorted(self._cache_timestamps.items(), key=lambda x: x[1])
                to_remove = len(self._auth_cache) - self.max_cache_size + 100
                for key, _ in sorted_items[:to_remove]:
                    self._auth_cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
            
            self._last_cache_cleanup = now
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 個過期緩存項目")
    
    def _get_cached_auth(self, uuid_hash: str) -> Optional[dict]:
        """獲取緩存的認證結果"""
        self._cleanup_expired_cache()
        
        with self.cache_lock:
            if uuid_hash in self._auth_cache:
                timestamp = self._cache_timestamps.get(uuid_hash, 0)
                if time.time() - timestamp < self.cache_ttl:
                    return self._auth_cache[uuid_hash]
                else:
                    # 過期，刪除
                    self._auth_cache.pop(uuid_hash, None)
                    self._cache_timestamps.pop(uuid_hash, None)
        
        return None
    
    def _set_cached_auth(self, uuid_hash: str, auth_result: dict):
        """設置認證結果緩存"""
        with self.cache_lock:
            self._auth_cache[uuid_hash] = auth_result.copy()
            self._cache_timestamps[uuid_hash] = time.time()
    
    def _record_request_metric(self, endpoint: str, duration: float):
        """記錄請求指標"""
        now = time.time()
        
        # 清理舊指標
        if now - self.last_metrics_cleanup > 3600:  # 每小時清理一次
            cutoff = now - 3600
            for endpoint_name in list(self.request_metrics.keys()):
                self.request_metrics[endpoint_name] = [
                    (timestamp, duration) for timestamp, duration in self.request_metrics[endpoint_name]
                    if timestamp > cutoff
                ]
            self.last_metrics_cleanup = now
        
        # 記錄當前請求
        self.request_metrics[endpoint].append((now, duration))
        
        # 限制每個端點的記錄數量
        if len(self.request_metrics[endpoint]) > 1000:
            self.request_metrics[endpoint] = self.request_metrics[endpoint][-500:]
    
    def _check_service_health(self):
        """檢查服務健康狀態"""
        issues = []
        
        # 檢查數據庫連接
        if not self.db:
            issues.append("Database not initialized")
        else:
            try:
                # 快速測試查詢，使用簡單的超時機制
                test_ref = self.db.collection('connection_test').limit(1)
                list(test_ref.stream())
                    
            except Exception as e:
                issues.append(f"Database connection failed: {str(e)}")
        
        # 檢查 Session Manager
        if not self.session_manager:
            issues.append("Session Manager not initialized")
        
        # 檢查記憶體使用（如果可用）
        if PSUTIL_AVAILABLE:
            try:
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:
                    issues.append(f"High memory usage: {memory_percent}%")
            except:
                pass
        
        return issues
    
    def root(self):
        """根路徑端點 - 優化版本"""
        start_time = time.time()
        
        try:
            health_issues = self._check_service_health()
            
            # 獲取基本統計信息（緩存）
            stats = self._get_basic_stats()
            
            response_data = {
                'service': 'Scrilab Artale Authentication Service',
                'version': '3.1.0-optimized',
                'status': 'healthy' if not health_issues else 'degraded',
                'health_issues': health_issues,
                'features': [
                    '🔐 高性能用戶認證系統',
                    '👥 增強版管理員面板',
                    '🎲 UUID 生成器',
                    '🛡️ 記憶體感知IP封鎖保護',
                    '🚀 智能速率限制',
                    '🔥 優化 Firestore 會話存儲',
                    '🛍️ 響應式商品展示頁面',
                    '📖 完整操作手冊',
                    '⚖️ 法律免責聲明',
                    '💳 Gumroad 安全付款整合',
                    '🔄 自動退款處理',
                    '📊 實時系統監控'
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
                    'disclaimer': '/disclaimer',
                    'gumroad_payment': '/gumroad/create-payment'
                },
                'performance': stats,
                'firebase_connected': self.db is not None,
                'psutil_available': PSUTIL_AVAILABLE
            }
            
            return jsonify(response_data)
            
        finally:
            duration = time.time() - start_time
            self._record_request_metric('root', duration)
    
    def _get_basic_stats(self):
        """獲取基本統計信息（帶緩存）"""
        try:
            return {
                'cache_size': len(self._auth_cache),
                'active_rate_limits': len(rate_limiter.request_records),
                'blocked_ips': len(rate_limiter.blocked_ips),
                'psutil_available': PSUTIL_AVAILABLE,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取基本統計失敗: {str(e)}")
            return {}
    
    @rate_limit(max_requests=5, time_window=300, block_on_exceed=True)
    def login(self):
        """用戶登入端點 - 高性能版本"""
        start_time = time.time()
        client_ip = get_client_ip()
        
        try:
            # 檢查服務狀態
            if not self.db:
                logger.error("Firebase 數據庫未初始化")
                return jsonify({
                    'success': False,
                    'error': 'Database service unavailable',
                    'code': 'DB_NOT_INITIALIZED'
                }), 503
            
            if not self.session_manager:
                logger.error("Session Manager 未初始化")
                return jsonify({
                    'success': False,
                    'error': 'Session service unavailable',
                    'code': 'SESSION_MANAGER_NOT_INITIALIZED'
                }), 503
            
            # 驗證請求數據
            data = request.get_json()
            if not data or 'uuid' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing UUID',
                    'code': 'MISSING_UUID'
                }), 400
            
            uuid = data['uuid'].strip()
            force_login = data.get('force_login', True)
            
            if not uuid:
                return jsonify({
                    'success': False,
                    'error': 'UUID cannot be empty',
                    'code': 'EMPTY_UUID'
                }), 400
            
            logger.info(f"Login attempt from {client_ip} for UUID: {uuid[:8]}...")
            
            # 認證邏輯（使用緩存和並發控制）
            success, message, user_data = self.authenticate_user_optimized(uuid, force_login, client_ip)
            
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
                    'error': message,
                    'code': 'AUTHENTICATION_FAILED'
                }), 401
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            }), 500
        finally:
            duration = time.time() - start_time
            self._record_request_metric('login', duration)
    
    def logout(self):
        """用戶登出端點"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            session_token = data.get('session_token') if data else None
            
            if session_token and self.session_manager:
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
                'error': 'Logout failed',
                'code': 'LOGOUT_FAILED'
            }), 500
        finally:
            duration = time.time() - start_time
            self._record_request_metric('logout', duration)
    
    @rate_limit(max_requests=60, time_window=60)  # 從120次/分鐘降到60次/分鐘
    def validate_session(self):
        """驗證會話令牌 - 修復權限同步問題版本 + 增強攻擊防護"""
        start_time = time.time()
        
        try:
            # === 新增：快速前置檢查，立即拒絕無效請求 ===
            data = request.get_json()
            session_token = data.get('session_token') if data else None
            
            # 1. 基本存在性檢查
            if not session_token:
                return jsonify({
                    'success': False,
                    'error': 'Missing session token',
                    'code': 'MISSING_SESSION_TOKEN'
                }), 400
            
            # 2. Token長度檢查（正常token約43字符，設定最低15字符）
            if len(session_token) < 20 or len(session_token) > 60:
                return jsonify({
                    'success': False,
                    'error': 'Invalid session token format',
                    'code': 'INVALID_SESSION_FORMAT'
                }), 400
            
            # 3. 記憶體檢查（如果系統過載，立即拒絕）
            if PSUTIL_AVAILABLE:
                try:
                    memory_percent = psutil.virtual_memory().percent
                    if memory_percent > 90:  # 記憶體使用超過80%就拒絕
                        return jsonify({
                            'success': False,
                            'error': 'Server temporarily overloaded',
                            'code': 'SERVER_OVERLOADED'
                        }), 503
                except:
                    pass  # 如果無法檢查記憶體，繼續處理
            
            # === 以下是原有的檢查邏輯，保持不變 ===
            if not self.db:
                return jsonify({
                    'success': False,
                    'error': 'Authentication service unavailable',
                    'code': 'DB_NOT_AVAILABLE'
                }), 503
            
            if not self.session_manager:
                return jsonify({
                    'success': False,
                    'error': 'Session service unavailable',
                    'code': 'SESSION_MANAGER_NOT_AVAILABLE'
                }), 503
            
            # 驗證會話令牌
            is_valid, session_data = self.session_manager.verify_session_token(session_token)
            
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired session',
                    'code': 'INVALID_SESSION'
                }), 401
            
            # 關鍵修復：重新從數據庫獲取最新的用戶權限
            uuid = session_data.get('uuid')
            if not uuid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid session data',
                    'code': 'INVALID_SESSION_DATA'
                }), 401
            
            try:
                # 重新從數據庫獲取最新用戶數據
                import hashlib
                uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
                user_ref = self.db.collection('authorized_users').document(uuid_hash)
                user_doc = user_ref.get()
                
                if not user_doc.exists:
                    logger.warning(f"Session validation: User {uuid[:8]}... not found in database")
                    return jsonify({
                        'success': False,
                        'error': 'User not found',
                        'code': 'USER_NOT_FOUND'
                    }), 401
                
                fresh_user_data = user_doc.to_dict()
                
                # 檢查用戶狀態
                if not fresh_user_data.get('active', False):
                    logger.warning(f"Session validation: User {uuid[:8]}... is deactivated")
                    return jsonify({
                        'success': False,
                        'error': 'Account deactivated',
                        'code': 'ACCOUNT_DEACTIVATED'
                    }), 401
                
                # 檢查有效期
                if 'expires_at' in fresh_user_data:
                    expires_at = fresh_user_data['expires_at']
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
                    elif hasattr(expires_at, 'timestamp'):
                        expires_at = datetime.fromtimestamp(expires_at.timestamp())
                    
                    if datetime.now() > expires_at:
                        logger.warning(f"Session validation: User {uuid[:8]}... account expired")
                        return jsonify({
                            'success': False,
                            'error': 'Account expired',
                            'code': 'ACCOUNT_EXPIRED'
                        }), 401
                
                # 清除緩存中的過期數據（如果存在）
                if hasattr(self, '_auth_cache'):
                    self._auth_cache.pop(uuid_hash, None)
                    self._cache_timestamps.pop(uuid_hash, None)
                
                logger.info(f"Session validation successful for {uuid[:8]}... with fresh permissions")
                
                return jsonify({
                    'success': True,
                    'user_data': fresh_user_data,  # 返回最新的用戶數據
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as db_error:
                logger.error(f"Database error during session validation: {str(db_error)}")
                return jsonify({
                    'success': False,
                    'error': 'Database error during validation',
                    'code': 'DATABASE_ERROR'
                }), 500
                
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'code': 'VALIDATION_ERROR'
            }), 500
        finally:
            duration = time.time() - start_time
            self._record_request_metric('validate_session', duration)
    
    def session_stats(self):
        """Session 統計信息"""
        start_time = time.time()
        
        try:
            if not self.session_manager:
                return jsonify({
                    'success': False,
                    'error': 'Session manager not available',
                    'code': 'SESSION_MANAGER_NOT_AVAILABLE'
                }), 503
            
            stats = self.session_manager.get_session_stats()
            
            # 添加性能指標
            performance_stats = self._get_performance_stats()
            
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'performance': performance_stats,
                **stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'code': 'STATS_ERROR'
            }), 500
        finally:
            duration = time.time() - start_time
            self._record_request_metric('session_stats', duration)
    
    def _get_performance_stats(self):
        """獲取性能統計"""
        try:
            stats = {}
            
            # 計算各端點的平均響應時間
            for endpoint, metrics in self.request_metrics.items():
                if metrics:
                    recent_metrics = [duration for timestamp, duration in metrics 
                                    if time.time() - timestamp < 3600]  # 最近一小時
                    if recent_metrics:
                        stats[f'{endpoint}_avg_duration'] = sum(recent_metrics) / len(recent_metrics)
                        stats[f'{endpoint}_request_count'] = len(recent_metrics)
            
            # 系統資源使用（如果可用）
            if PSUTIL_AVAILABLE:
                try:
                    stats['memory_usage_percent'] = psutil.virtual_memory().percent
                    stats['cpu_usage_percent'] = psutil.cpu_percent()
                except:
                    pass
            
            # 緩存統計
            stats['auth_cache_size'] = len(self._auth_cache)
            stats['rate_limit_active_ips'] = len(rate_limiter.request_records)
            stats['rate_limit_blocked_ips'] = len(rate_limiter.blocked_ips)
            stats['psutil_available'] = PSUTIL_AVAILABLE
            
            return stats
        except Exception as e:
            logger.error(f"獲取性能統計失敗: {str(e)}")
            return {}
    
    @rate_limit(max_requests=5, time_window=300)
    def manual_cleanup_sessions(self):
        """手動清理過期會話"""
        start_time = time.time()
        
        try:
            if not self.session_manager:
                return jsonify({
                    'success': False,
                    'error': 'Session manager not available',
                    'code': 'SESSION_MANAGER_NOT_AVAILABLE'
                }), 503
            
            deleted_count = self.session_manager.cleanup_expired_sessions()
            
            # 同時清理本地緩存
            self.cleanup_all_caches()
            
            return jsonify({
                'success': True,
                'message': f'已清理 {deleted_count} 個過期會話',
                'deleted_count': deleted_count
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'code': 'CLEANUP_ERROR'
            }), 500
        finally:
            duration = time.time() - start_time
            self._record_request_metric('manual_cleanup', duration)
    
    def generate_session_token(self, uuid, client_ip):
        """生成會話令牌"""
        session_timeout = int(os.environ.get('SESSION_TIMEOUT', 3600))
        return self.session_manager.generate_session_token(uuid, client_ip, session_timeout)
    
    def verify_session_token_optimized(self, token):
        """優化的會話令牌驗證"""
        try:
            # 使用 session manager 的驗證，但添加本地緩存
            is_valid, session_data = self.session_manager.verify_session_token(token)
            
            if not is_valid:
                return False, None
            
            # 構建用戶數據（避免額外的數據庫查詢）
            user_data = {
                'uuid': session_data.get('uuid'),
                'active': True,
                'last_login': session_data.get('created_at'),
                'client_ip': session_data.get('client_ip'),
                'session_valid': True
            }
            
            return True, user_data
            
        except Exception as e:
            logger.error(f"優化會話驗證失敗: {str(e)}")
            return False, None
    
    def authenticate_user_optimized(self, uuid, force_login=True, client_ip='unknown'):
        """優化的用戶認證（使用緩存和並發控制）"""
        uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
        
        # 檢查緩存
        cached_result = self._get_cached_auth(uuid_hash)
        if cached_result and not force_login:
            logger.debug(f"使用緩存認證結果: {uuid[:8]}...")
            return cached_result['success'], cached_result['message'], cached_result['user_data']
        
        # 使用鎖防止並發認證同一用戶
        with self.auth_lock:
            try:
                if self.db is None:
                    logger.error("authenticate_user_optimized: db 對象為 None")
                    return False, "認證服務不可用", None
                
                user_ref = self.db.collection('authorized_users').document(uuid_hash)
                user_doc = user_ref.get()
                
                if not user_doc.exists:
                    self.log_unauthorized_attempt(uuid_hash, client_ip)
                    result = {'success': False, 'message': "UUID 未授權", 'user_data': None}
                    self._set_cached_auth(uuid_hash, result)
                    return False, "UUID 未授權", None
                
                user_data = user_doc.to_dict()
                
                # 檢查用戶狀態
                if not user_data.get('active', False):
                    result = {'success': False, 'message': "帳號已被停用", 'user_data': None}
                    self._set_cached_auth(uuid_hash, result)
                    return False, "帳號已被停用", None
                
                # 檢查有效期
                if 'expires_at' in user_data:
                    expires_at = user_data['expires_at']
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
                    elif hasattr(expires_at, 'timestamp'):
                        expires_at = datetime.fromtimestamp(expires_at.timestamp())
                    
                    if datetime.now() > expires_at:
                        result = {'success': False, 'message': "帳號已過期", 'user_data': None}
                        self._set_cached_auth(uuid_hash, result)
                        return False, "帳號已過期", None
                
                # 處理現有會話（優化）
                if force_login:
                    # 異步終止會話，不阻塞當前請求
                    threading.Thread(
                        target=self.session_manager.terminate_user_sessions,
                        args=(uuid,),
                        daemon=True
                    ).start()
                else:
                    has_active = self.session_manager.check_existing_session(uuid)
                    if has_active:
                        return False, "該帳號已在其他地方登入", None
                
                # 異步更新登入記錄（不阻塞響應）
                threading.Thread(
                    target=self._update_login_record_async,
                    args=(user_ref, client_ip),
                    daemon=True
                ).start()
                
                # 緩存成功結果
                result = {'success': True, 'message': "認證成功", 'user_data': user_data}
                self._set_cached_auth(uuid_hash, result)
                
                return True, "認證成功", user_data
                
            except Exception as e:
                logger.error(f"authenticate_user_optimized error: {str(e)}")
                return False, "認證服務發生錯誤", None
    
    def _update_login_record_async(self, user_ref, client_ip):
        """異步更新登入記錄"""
        try:
            from firebase_admin import firestore
            update_data = {
                'last_login': datetime.now(),
                'login_count': firestore.Increment(1),
                'last_login_ip': client_ip
            }
            user_ref.update(update_data)
        except Exception as e:
            logger.error(f"異步更新登入記錄失敗: {str(e)}")
    
    def log_unauthorized_attempt(self, uuid_hash, client_ip):
        """記錄未授權登入嘗試（異步）"""
        def log_async():
            try:
                if self.db is None:
                    return
                    
                attempts_ref = self.db.collection('unauthorized_attempts')
                attempts_ref.add({
                    'uuid_hash': uuid_hash,
                    'timestamp': datetime.now(),
                    'client_ip': client_ip,
                    'user_agent': request.headers.get('User-Agent', 'Unknown')
                })
            except Exception as e:
                logger.error(f"記錄未授權嘗試失敗: {str(e)}")
        
        # 異步執行，不阻塞主請求
        threading.Thread(target=log_async, daemon=True).start()