"""
驗證相關功能
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
    """檢查速率限制"""
    now = time.time()
    verification_attempts[user_id] = [t for t in verification_attempts[user_id] if now - t < 600]
    return len(verification_attempts[user_id]) >= 3

def record_failed_attempt(user_id):
    """記錄失敗嘗試"""
    verification_attempts[user_id].append(time.time())

async def verify_user_uuid(uuid_string, db):
    """驗證用戶UUID"""
    try:
        if not db:
            logger.error("數據庫連接不可用")
            return False, "認證服務不可用"
        
        logger.info(f"開始驗證序號: {uuid_string[:8]}...")
        
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            logger.warning("序號不存在")
            return False, "序號無效"
        
        user_data = user_doc.to_dict()
        logger.info("序號存在，檢查狀態...")
        
        # 檢查用戶狀態
        if not user_data.get('active', False):
            logger.warning("帳號已被停用")
            return False, "帳號已被停用"
        
        # 檢查有效期
        if 'expires_at' in user_data:
            expires_at = user_data['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
            elif hasattr(expires_at, 'timestamp'):
                expires_at = datetime.fromtimestamp(expires_at.timestamp())
            
            if datetime.now() > expires_at:
                logger.warning("帳號已過期")
                return False, "帳號已過期"
        
        logger.info("✅ 序號驗證成功")
        return True, user_data
        
    except Exception as e:
        logger.error(f"UUID驗證錯誤: {str(e)}")
        return False, "驗證服務錯誤"

async def record_verification(discord_id, uuid, user_data, db):
    """記錄驗證信息到數據庫"""
    try:
        if db:
            verification_ref = db.collection('discord_verifications').document(str(discord_id))
            verification_data = {
                'discord_id': discord_id,
                'uuid_hash': hashlib.sha256(uuid.encode()).hexdigest(),
                'verified_at': datetime.now(),
                'user_data': user_data,
                'status': 'active'
            }
            verification_ref.set(verification_data)
            logger.info(f"✅ 記錄驗證信息: 用戶 {discord_id}")
    except Exception as e:
        logger.error(f"記錄驗證信息錯誤: {str(e)}")