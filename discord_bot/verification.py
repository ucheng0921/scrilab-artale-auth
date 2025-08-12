"""
驗證相關功能 - 直接使用你現有的驗證邏輯
"""
import hashlib
import logging
from datetime import datetime
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

# 速率限制記錄
verification_attempts = defaultdict(list)

def is_rate_limited(user_id):
    """檢查速率限制（沿用你的邏輯）"""
    now = time.time()
    verification_attempts[user_id] = [t for t in verification_attempts[user_id] if now - t < 600]
    return len(verification_attempts[user_id]) >= 3

def record_failed_attempt(user_id):
    """記錄失敗嘗試"""
    verification_attempts[user_id].append(time.time())

async def verify_user_uuid(uuid_string, db):
    """
    驗證用戶UUID - 直接複製你現有的 verify_user_uuid 函數
    """
    try:
        if not db:
            return False, "認證服務不可用"
        
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return False, "序號無效"
        
        user_data = user_doc.to_dict()
        
        # 檢查用戶狀態
        if not user_data.get('active', False):
            return False, "帳號已被停用"
        
        # 檢查有效期
        if 'expires_at' in user_data:
            expires_at = user_data['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
            elif hasattr(expires_at, 'timestamp'):
                expires_at = datetime.fromtimestamp(expires_at.timestamp())
            
            if datetime.now() > expires_at:
                return False, "帳號已過期"
        
        return True, user_data
        
    except Exception as e:
        logger.error(f"UUID驗證錯誤: {str(e)}")
        return False, "驗證服務錯誤"