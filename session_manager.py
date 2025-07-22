# session_manager.py - 優化版本，平衡性能與安全性
import logging
import time
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Optional
import os

logger = logging.getLogger(__name__)

class FirestoreSessionManager:
    """優化版 Session 管理器 - 平衡性能與安全性"""
    
    def __init__(self, db=None):
        self.db = db
        self.collection_name = 'user_sessions'
        
        # 用戶信息緩存（包含過期時間）
        self.user_cache = {}  # {uuid: {'expires_at': datetime, 'active': bool, 'cache_time': timestamp}}
        self.cache_duration = 300  # 用戶信息緩存5分鐘
        
        # 驗證間隔配置
        self.quick_validation_interval = 60   # 快速驗證：1分鐘（只檢查會話本身）
        self.full_validation_interval = 300   # 完整驗證：5分鐘（檢查用戶狀態）
        self.expiry_check_interval = 180      # 過期檢查：3分鐘（針對即將過期的用戶）
        
        logger.info("🔥 優化版 Firestore Session Manager 初始化")
    
    def set_db(self, db):
        """設置 Firestore 數據庫實例"""
        self.db = db
        logger.info("✅ Firestore 數據庫實例已設置")
    
    def _now_utc(self):
        """獲取 UTC 時間"""
        return datetime.now(timezone.utc)
    
    def _parse_datetime(self, dt):
        """解析時間對象"""
        if dt is None:
            return None
            
        if isinstance(dt, str):
            try:
                if dt.endswith('Z'):
                    return datetime.fromisoformat(dt[:-1] + '+00:00')
                elif '+' in dt or dt.endswith('UTC'):
                    return datetime.fromisoformat(dt.replace('UTC', '+00:00'))
                else:
                    parsed = datetime.fromisoformat(dt)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
            except Exception as e:
                logger.warning(f"無法解析時間字符串 '{dt}': {e}")
                return None
        
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        if hasattr(dt, 'timestamp'):
            return datetime.fromtimestamp(dt.timestamp(), tz=timezone.utc)
        
        return None
    
    def _get_cached_user_info(self, uuid: str) -> Optional[Dict]:
        """獲取緩存的用戶信息"""
        if uuid not in self.user_cache:
            return None
            
        cache_entry = self.user_cache[uuid]
        current_time = time.time()
        
        # 檢查緩存是否過期
        if current_time - cache_entry['cache_time'] > self.cache_duration:
            del self.user_cache[uuid]
            return None
            
        return cache_entry
    
    def _cache_user_info(self, uuid: str, user_data: Dict):
        """緩存用戶信息"""
        try:
            expires_at = self._parse_datetime(user_data.get('expires_at'))
            
            self.user_cache[uuid] = {
                'expires_at': expires_at,
                'active': user_data.get('active', False),
                'cache_time': time.time(),
                'display_name': user_data.get('display_name', 'Unknown')
            }
        except Exception as e:
            logger.warning(f"緩存用戶信息失敗: {e}")
    
    def _is_user_expired(self, cached_info: Dict, current_time: datetime) -> bool:
        """檢查用戶是否已過期"""
        expires_at = cached_info.get('expires_at')
        if expires_at is None:
            return False  # 永久用戶
            
        return current_time > expires_at
    
    def _is_approaching_expiry(self, cached_info: Dict, current_time: datetime, buffer_minutes: int = 10) -> bool:
        """檢查是否即將過期（用於提前檢查）"""
        expires_at = cached_info.get('expires_at')
        if expires_at is None:
            return False
            
        buffer_time = expires_at - timedelta(minutes=buffer_minutes)
        return current_time > buffer_time
    
    def generate_session_token(self, uuid: str, client_ip: str, session_timeout: int = 3600) -> str:
        """生成會話令牌"""
        try:
            if not self.db:
                raise Exception("Database not initialized")
            
            # 實時檢查用戶狀態（登入時必須實時檢查）
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                raise Exception("User not found")
            
            user_data = user_doc.to_dict()
            
            # 檢查用戶狀態
            if not user_data.get('active', False):
                raise Exception("User account is disabled")
            
            # 檢查是否過期
            now = self._now_utc()
            expires_at = self._parse_datetime(user_data.get('expires_at'))
            if expires_at and now > expires_at:
                raise Exception("User account has expired")
            
            # 緩存用戶信息
            self._cache_user_info(uuid, user_data)
            
            # 生成會話令牌
            token = secrets.token_urlsafe(32)
            session_expires_at = now + timedelta(seconds=session_timeout)
            
            session_data = {
                'uuid': uuid,
                'token': token,
                'created_at': now,
                'expires_at': session_expires_at,
                'last_activity': now,
                'client_ip': client_ip,
                'active': True,
                # 緩存用戶過期時間以避免頻繁查詢
                'user_expires_at': expires_at,
                'user_active': user_data.get('active', False)
            }
            
            session_ref = self.db.collection(self.collection_name).document(token)
            session_ref.set(session_data)
            
            logger.info(f"✅ Session 已創建: {token[:16]}... for user {uuid[:8]}...")
            return token
            
        except Exception as e:
            logger.error(f"❌ 生成 session 失敗: {str(e)}")
            raise
    
    def verify_session_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """驗證會話令牌 - 智能化驗證策略"""
        try:
            if not self.db:
                return False, None
            
            # 1. 獲取會話信息
            session_ref = self.db.collection(self.collection_name).document(token)
            session_doc = session_ref.get()
            
            if not session_doc.exists:
                return False, None
            
            session_data = session_doc.to_dict()
            uuid = session_data.get('uuid')
            
            if not uuid:
                return False, None
            
            now = self._now_utc()
            
            # 2. 檢查會話本身是否過期
            session_expires_at = self._parse_datetime(session_data.get('expires_at'))
            if session_expires_at and now > session_expires_at:
                logger.debug(f"❌ Session 已過期: {token[:16]}...")
                try:
                    session_ref.delete()
                except:
                    pass
                return False, None
            
            # 3. 檢查會話中緩存的用戶過期時間
            cached_user_expires_at = self._parse_datetime(session_data.get('user_expires_at'))
            if cached_user_expires_at and now > cached_user_expires_at:
                logger.info(f"❌ 用戶已過期（會話緩存）: {token[:16]}...")
                try:
                    session_ref.delete()
                except:
                    pass
                return False, None
            
            # 4. 決定是否需要完整的用戶狀態檢查
            last_activity = self._parse_datetime(session_data.get('last_activity', session_data.get('created_at')))
            need_full_check = False
            
            # 情況1: 長時間未活動，需要完整檢查
            if last_activity:
                inactive_duration = (now - last_activity).total_seconds()
                if inactive_duration > self.full_validation_interval:
                    need_full_check = True
            
            # 情況2: 即將過期的用戶，需要更頻繁的檢查
            if cached_user_expires_at and self._is_approaching_expiry(
                {'expires_at': cached_user_expires_at}, now, buffer_minutes=30
            ):
                time_since_activity = (now - last_activity).total_seconds() if last_activity else 0
                if time_since_activity > self.expiry_check_interval:
                    need_full_check = True
            
            # 5. 執行完整的用戶狀態檢查
            if need_full_check:
                user_valid = self._full_user_status_check(uuid, session_ref, session_data)
                if not user_valid:
                    return False, None
            
            # 6. 更新會話活動時間（批量更新以減少寫操作）
            update_data = {'last_activity': now}
            
            # 如果會話快過期，自動延長
            if session_expires_at:
                time_left = (session_expires_at - now).total_seconds()
                if time_left < 300:  # 少於5分鐘
                    session_timeout = int(os.environ.get('SESSION_TIMEOUT', 3600))
                    new_expires_at = now + timedelta(seconds=session_timeout)
                    update_data['expires_at'] = new_expires_at
                    logger.debug(f"🔄 Session 自動延長: {token[:16]}...")
            
            try:
                session_ref.update(update_data)
                session_data.update(update_data)
            except Exception as e:
                logger.warning(f"更新 session 活動時間失敗: {e}")
            
            logger.debug(f"✅ Session 驗證成功: {token[:16]}...")
            return True, session_data
            
        except Exception as e:
            logger.error(f"❌ 驗證 session 失敗: {str(e)}")
            return False, None
    
    def _full_user_status_check(self, uuid: str, session_ref, session_data: Dict) -> bool:
        """執行完整的用戶狀態檢查"""
        try:
            now = self._now_utc()
            
            # 檢查緩存
            cached_info = self._get_cached_user_info(uuid)
            
            # 如果緩存有效且用戶未過期，跳過數據庫查詢
            if cached_info:
                if not cached_info['active']:
                    logger.info(f"❌ 用戶已被停用（緩存）: {uuid[:8]}...")
                    try:
                        session_ref.delete()
                    except:
                        pass
                    return False
                
                if self._is_user_expired(cached_info, now):
                    logger.info(f"❌ 用戶已過期（緩存）: {uuid[:8]}...")
                    try:
                        session_ref.delete()
                    except:
                        pass
                    return False
                
                # 緩存檢查通過，但仍需要偶爾實時檢查
                cache_age = time.time() - cached_info['cache_time']
                if cache_age < self.cache_duration * 0.8:  # 80% 緩存時間內直接使用緩存
                    return True
            
            # 執行實時數據庫檢查
            logger.debug(f"🔍 執行完整用戶狀態檢查: {uuid[:8]}...")
            
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                logger.info(f"❌ 用戶不存在: {uuid[:8]}...")
                try:
                    session_ref.delete()
                except:
                    pass
                return False
            
            user_data = user_doc.to_dict()
            
            # 更新緩存
            self._cache_user_info(uuid, user_data)
            
            # 檢查用戶狀態
            if not user_data.get('active', False):
                logger.info(f"❌ 用戶已被停用: {uuid[:8]}...")
                try:
                    session_ref.delete()
                except:
                    pass
                return False
            
            # 檢查用戶過期時間
            user_expires_at = self._parse_datetime(user_data.get('expires_at'))
            if user_expires_at and now > user_expires_at:
                logger.info(f"❌ 用戶已過期: {uuid[:8]}...")
                try:
                    session_ref.delete()
                except:
                    pass
                return False
            
            # 更新會話中的用戶信息緩存
            try:
                session_ref.update({
                    'user_expires_at': user_expires_at,
                    'user_active': user_data.get('active', False),
                    'last_full_check': now
                })
            except Exception as e:
                logger.warning(f"更新會話用戶信息失敗: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"完整用戶狀態檢查失敗: {e}")
            return False
    
    def revoke_session_token(self, token: str) -> bool:
        """撤銷會話令牌"""
        try:
            if not self.db:
                return False
            
            session_ref = self.db.collection(self.collection_name).document(token)
            session_doc = session_ref.get()
            
            if session_doc.exists:
                session_ref.delete()
                logger.info(f"✅ Session 已撤銷: {token[:16]}...")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ 撤銷 session 失敗: {str(e)}")
            return False
    
    def terminate_user_sessions(self, uuid: str):
        """終止用戶的所有會話"""
        try:
            if not self.db:
                return
            
            # 清除緩存
            if uuid in self.user_cache:
                del self.user_cache[uuid]
            
            sessions_ref = self.db.collection(self.collection_name)
            user_sessions = sessions_ref.where('uuid', '==', uuid).where('active', '==', True).stream()
            
            deleted_count = 0
            for session_doc in user_sessions:
                try:
                    session_doc.reference.delete()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"刪除 session 失敗: {e}")
            
            logger.info(f"✅ 已終止用戶 {uuid[:8]}... 的 {deleted_count} 個會話")
            
        except Exception as e:
            logger.error(f"❌ 終止用戶會話失敗: {str(e)}")
    
    def cleanup_expired_sessions(self) -> int:
        """清理過期的會話"""
        try:
            if not self.db:
                return 0
            
            now = self._now_utc()
            sessions_ref = self.db.collection(self.collection_name)
            
            # 分批清理避免一次性操作過多
            expired_sessions = sessions_ref.where('expires_at', '<', now).limit(50).stream()
            
            deleted_count = 0
            for session_doc in expired_sessions:
                try:
                    session_doc.reference.delete()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"刪除過期 session 失敗: {e}")
            
            if deleted_count > 0:
                logger.info(f"🧹 已清理 {deleted_count} 個過期會話")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ 清理過期會話失敗: {str(e)}")
            return 0
    
    def cleanup_expired_cache(self):
        """清理過期的緩存"""
        current_time = time.time()
        expired_keys = []
        
        for uuid, cache_entry in self.user_cache.items():
            if current_time - cache_entry['cache_time'] > self.cache_duration:
                expired_keys.append(uuid)
        
        for key in expired_keys:
            del self.user_cache[key]
        
        if expired_keys:
            logger.debug(f"🧹 已清理 {len(expired_keys)} 個過期緩存")
    
    def get_session_stats(self) -> Dict:
        """獲取會話統計"""
        try:
            if not self.db:
                return {
                    'storage_type': 'firestore',
                    'firestore_connected': False,
                    'error': 'Database not initialized'
                }
            
            now = self._now_utc()
            sessions_ref = self.db.collection(self.collection_name)
            
            total_sessions = 0
            active_sessions = 0
            expired_sessions = 0
            
            # 限制查詢數量避免性能問題
            all_sessions = sessions_ref.limit(1000).stream()
            for session_doc in all_sessions:
                total_sessions += 1
                session_data = session_doc.to_dict()
                
                expires_at = self._parse_datetime(session_data.get('expires_at'))
                is_active = session_data.get('active', True)
                is_expired = expires_at and now > expires_at
                
                if is_active and not is_expired:
                    active_sessions += 1
                elif is_expired:
                    expired_sessions += 1
            
            return {
                'storage_type': 'firestore',
                'firestore_connected': True,
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'expired_sessions': expired_sessions,
                'cached_users': len(self.user_cache),
                'current_time': now.isoformat(),
                'validation_intervals': {
                    'quick_validation': self.quick_validation_interval,
                    'full_validation': self.full_validation_interval,
                    'expiry_check': self.expiry_check_interval
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取會話統計失敗: {str(e)}")
            return {
                'storage_type': 'firestore',
                'firestore_connected': False,
                'error': str(e)
            }


# 全域 session 管理器實例
session_manager = FirestoreSessionManager()

def init_session_manager(db):
    """初始化 session 管理器"""
    session_manager.set_db(db)
    logger.info("🔥 優化版 Session 管理器已初始化")