# session_manager.py - 修復時間格式問題版本
import logging
import time
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Optional
import os

logger = logging.getLogger(__name__)

class FirestoreSessionManager:
    """基於 Firestore 的 Session 管理器 - 修復時間格式問題"""
    
    def __init__(self, db=None):
        self.db = db
        self.collection_name = 'user_sessions'
        logger.info("🔥 Firestore Session Manager 初始化")
    
    def set_db(self, db):
        """設置 Firestore 數據庫實例"""
        self.db = db
        logger.info("✅ Firestore 數據庫實例已設置")
    
    def _now_utc(self):
        """獲取 UTC 時間（有時區信息）"""
        return datetime.now(timezone.utc)
    
    def _parse_datetime(self, dt):
        """解析時間對象，確保有時區信息"""
        if dt is None:
            return None
            
        if isinstance(dt, str):
            try:
                # 嘗試解析 ISO 格式
                if dt.endswith('Z'):
                    return datetime.fromisoformat(dt[:-1] + '+00:00')
                elif '+' in dt or dt.endswith('UTC'):
                    return datetime.fromisoformat(dt.replace('UTC', '+00:00'))
                else:
                    # 假設是 UTC 時間
                    parsed = datetime.fromisoformat(dt)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
            except Exception as e:
                logger.warning(f"無法解析時間字符串 '{dt}': {e}")
                return None
        
        # 如果是 datetime 對象
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                # 假設是 UTC 時間
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        # Firestore Timestamp 對象
        if hasattr(dt, 'timestamp'):
            return datetime.fromtimestamp(dt.timestamp(), tz=timezone.utc)
        
        logger.warning(f"未知的時間格式: {type(dt)} - {dt}")
        return None
    
    def generate_session_token(self, uuid: str, client_ip: str, session_timeout: int = 3600) -> str:
        """生成會話令牌並存儲到 Firestore"""
        try:
            if not self.db:
                logger.error("❌ Firestore 數據庫未初始化")
                raise Exception("Database not initialized")
            
            # *** 新增：獲取用戶過期時間 ***
            user_expires_at = None
            try:
                uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
                user_ref = self.db.collection('authorized_users').document(uuid_hash)
                user_doc = user_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    user_expires_at = user_data.get('expires_at')
            except Exception as e:
                logger.warning(f"無法獲取用戶過期時間: {e}")
            
            token = secrets.token_urlsafe(32)
            now = self._now_utc()
            expires_at = now + timedelta(seconds=session_timeout)
            
            session_data = {
                'uuid': uuid,
                'token': token,
                'created_at': now,
                'expires_at': expires_at,
                'last_activity': now,
                'client_ip': client_ip,
                'active': True,
                'user_expires_at': user_expires_at  # *** 新增：緩存用戶過期時間 ***
            }
            
            # 存儲到 Firestore
            session_ref = self.db.collection(self.collection_name).document(token)
            session_ref.set(session_data)
            
            logger.info(f"✅ Session 已創建: {token[:16]}... for user {uuid[:8]}...")
            return token
            
        except Exception as e:
            logger.error(f"❌ 生成 session 失敗: {str(e)}")
            raise
    
    def verify_session_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """驗證會話令牌 - 優化版本，使用緩存的過期時間"""
        try:
            if not self.db:
                logger.error("❌ Firestore 數據庫未初始化")
                return False, None
            
            session_ref = self.db.collection(self.collection_name).document(token)
            session_doc = session_ref.get()
            
            if not session_doc.exists:
                logger.debug(f"❌ Session 不存在: {token[:16]}...")
                return False, None
            
            session_data = session_doc.to_dict()
            
            # 檢查是否被標記為非活躍
            if not session_data.get('active', True):
                logger.debug(f"❌ Session 已被停用: {token[:16]}...")
                return False, None
            
            # 檢查會話本身是否過期
            expires_at = self._parse_datetime(session_data.get('expires_at'))
            now = self._now_utc()
            
            if expires_at and now > expires_at:
                logger.debug(f"❌ Session 已過期: {token[:16]}...")
                try:
                    session_ref.delete()
                except Exception as e:
                    logger.warning(f"刪除過期 session 失敗: {e}")
                return False, None
            
            # *** 新增：檢查緩存的用戶過期時間 ***
            user_expires_at = self._parse_datetime(session_data.get('user_expires_at'))
            if user_expires_at and now > user_expires_at:
                logger.info(f"❌ 用戶已過期: {token[:16]}... (cached check)")
                try:
                    session_ref.delete()
                except Exception as e:
                    logger.warning(f"刪除過期用戶 session 失敗: {e}")
                return False, None
            
            # 更新最後活動時間
            update_data = {
                'last_activity': now
            }
            
            # 如果會話快過期了，自動延長
            if expires_at:
                time_left = (expires_at - now).total_seconds()
                if time_left < 300:  # 少於5分鐘
                    session_timeout = int(os.environ.get('SESSION_TIMEOUT', 3600))
                    new_expires_at = now + timedelta(seconds=session_timeout)
                    update_data['expires_at'] = new_expires_at
                    logger.debug(f"🔄 Session 自動延長: {token[:16]}...")
            
            # 批量更新
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
    
    def revoke_session_token(self, token: str) -> bool:
        """撤銷會話令牌"""
        try:
            if not self.db:
                logger.error("❌ Firestore 數據庫未初始化")
                return False
            
            session_ref = self.db.collection(self.collection_name).document(token)
            session_doc = session_ref.get()
            
            if session_doc.exists:
                session_ref.delete()
                logger.info(f"✅ Session 已撤銷: {token[:16]}...")
                return True
            else:
                logger.debug(f"⚠️ 嘗試撤銷不存在的 session: {token[:16]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ 撤銷 session 失敗: {str(e)}")
            return False
    
    def terminate_user_sessions(self, uuid: str):
        """終止用戶的所有會話"""
        try:
            if not self.db:
                logger.error("❌ Firestore 數據庫未初始化")
                return
            
            # 查詢該用戶的所有 session
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
    
    def check_existing_session(self, uuid: str) -> bool:
        """檢查用戶是否有活躍會話"""
        try:
            if not self.db:
                logger.error("❌ Firestore 數據庫未初始化")
                return False
            
            now = self._now_utc()
            
            # 查詢活躍且未過期的 session
            sessions_ref = self.db.collection(self.collection_name)
            active_sessions = sessions_ref.where('uuid', '==', uuid)\
                                        .where('active', '==', True)\
                                        .where('expires_at', '>', now)\
                                        .limit(1)\
                                        .stream()
            
            # 檢查是否有結果
            for _ in active_sessions:
                logger.debug(f"✅ 用戶 {uuid[:8]}... 有活躍會話")
                return True
            
            logger.debug(f"❌ 用戶 {uuid[:8]}... 沒有活躍會話")
            return False
            
        except Exception as e:
            logger.error(f"❌ 檢查會話失敗: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """清理過期的會話"""
        try:
            if not self.db:
                logger.error("❌ Firestore 數據庫未初始化")
                return 0
            
            now = self._now_utc()
            
            # 查詢過期的 session
            sessions_ref = self.db.collection(self.collection_name)
            expired_sessions = sessions_ref.where('expires_at', '<', now).limit(100).stream()
            
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

    def sync_user_expiration_cache(self, uuid: str, session_token: str):
        """同步用戶過期時間緩存"""
        try:
            # 獲取最新的用戶過期時間
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                new_expires_at = user_data.get('expires_at')
                
                # 更新會話中的緩存
                session_ref = self.db.collection(self.collection_name).document(session_token)
                session_ref.update({
                    'user_expires_at': new_expires_at,
                    'cache_updated_at': self._now_utc()
                })
                
                logger.debug(f"✅ 用戶過期時間緩存已更新: {uuid[:8]}...")
                return new_expires_at
            else:
                # 用戶不存在，撤銷會話
                session_ref = self.db.collection(self.collection_name).document(session_token)
                session_ref.delete()
                logger.info(f"❌ 用戶已刪除，撤銷會話: {uuid[:8]}...")
                return None
                
        except Exception as e:
            logger.error(f"同步用戶過期時間失敗: {e}")
            return None

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
            
            # 計算總會話數
            total_sessions = 0
            active_sessions = 0
            expired_sessions = 0
            
            # 獲取所有會話並統計
            all_sessions = sessions_ref.stream()
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
                'current_time': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取會話統計失敗: {str(e)}")
            return {
                'storage_type': 'firestore',
                'firestore_connected': False,
                'error': str(e)
            }
    
    def get_user_sessions(self, uuid: str) -> list:
        """獲取用戶的所有會話"""
        try:
            if not self.db:
                return []
            
            sessions_ref = self.db.collection(self.collection_name)
            user_sessions = sessions_ref.where('uuid', '==', uuid).stream()
            
            sessions = []
            for session_doc in user_sessions:
                session_data = session_doc.to_dict()
                
                created_at = self._parse_datetime(session_data.get('created_at'))
                last_activity = self._parse_datetime(session_data.get('last_activity'))
                expires_at = self._parse_datetime(session_data.get('expires_at'))
                
                sessions.append({
                    'token': session_data.get('token', 'Unknown')[:16] + '...',
                    'created_at': created_at.isoformat() if created_at else 'Unknown',
                    'last_activity': last_activity.isoformat() if last_activity else 'Unknown',
                    'expires_at': expires_at.isoformat() if expires_at else 'Unknown',
                    'client_ip': session_data.get('client_ip'),
                    'active': session_data.get('active', True)
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"❌ 獲取用戶會話失敗: {str(e)}")
            return []

# 創建全局 session 管理器實例
session_manager = FirestoreSessionManager()

# 在 app.py 中需要調用這個函數來設置 db
def init_session_manager(db):
    """初始化 session 管理器"""
    session_manager.set_db(db)
    logger.info("🔥 Session 管理器已初始化")
