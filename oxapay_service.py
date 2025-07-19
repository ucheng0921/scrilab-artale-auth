import requests
import os
import logging
import hashlib
import uuid as uuid_lib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class OxaPayService:
    """OxaPay 加密貨幣支付服務"""
    
    def __init__(self, db):
        self.db = db
        self.api_base_url = "https://api.oxapay.com"
        self.merchant_key = os.environ.get('OXAPAY_MERCHANT_KEY')
        self.callback_secret = os.environ.get('OXAPAY_CALLBACK_SECRET', 'default_secret')
        
        if not self.merchant_key:
            logger.error("❌ OXAPAY_MERCHANT_KEY 環境變數未設置")
            raise ValueError("OxaPay Merchant Key is required")
        
        logger.info("✅ OxaPay Service 初始化完成")
    
    def create_payment(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建 OxaPay 付款"""
        try:
            # 生成唯一的訂單ID
            order_id = f"artale_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 計算 USDT 金額 (假設 1 TWD = 0.032 USDT)
            twd_amount = plan_info['price']
            usdt_amount = round(twd_amount * 0.032, 2)  # 台幣轉 USDT 匯率
            
            # OxaPay 創建發票 API
            payment_data = {
                "merchant": self.merchant_key,
                "amount": usdt_amount,
                "currency": "USDT",
                "lifeTime": 1800,  # 30分鐘過期
                "feePaidByPayer": 0,  # 手續費由商家承擔
                "underPaidCover": 95,  # 允許95%的付款
                "callbackUrl": f"{os.environ.get('BASE_URL', 'http://localhost:5000')}/payment/oxapay/callback",
                "returnUrl": f"{os.environ.get('BASE_URL', 'http://localhost:5000')}/payment/success?provider=oxapay",
                "description": f"Artale {plan_info['name']} - {plan_info['period']}",
                "orderId": order_id
            }
            
            logger.info(f"創建 OxaPay 付款請求: {order_id}")
            
            response = requests.post(
                f"{self.api_base_url}/merchants/request",
                json=payment_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('result') == 100:  # 成功
                    # 保存付款記錄
                    payment_record = {
                        'payment_id': result['trackId'],
                        'order_id': order_id,
                        'user_name': user_info['name'],
                        'user_email': user_info['email'],
                        'user_phone': user_info.get('phone', ''),
                        'plan_id': plan_info['id'],
                        'plan_name': plan_info['name'],
                        'plan_period': plan_info['period'],
                        'amount_twd': twd_amount,
                        'amount_usdt': usdt_amount,
                        'currency': 'USDT',
                        'status': 'pending',
                        'created_at': datetime.now(),
                        'payment_method': 'oxapay',
                        'payment_url': result['payLink'],
                        'track_id': result['trackId'],
                        'expires_at': datetime.now() + timedelta(minutes=30)
                    }
                    
                    self.save_payment_record(result['trackId'], payment_record)
                    
                    return {
                        'success': True,
                        'payment_url': result['payLink'],
                        'track_id': result['trackId'],
                        'order_id': order_id,
                        'amount_usdt': usdt_amount,
                        'expires_at': payment_record['expires_at'].isoformat()
                    }
                else:
                    logger.error(f"OxaPay API 錯誤: {result.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"OxaPay API 請求失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"創建 OxaPay 付款失敗: {str(e)}")
            return None
    
    def handle_callback(self, callback_data: Dict) -> Tuple[bool, Optional[str]]:
        """處理 OxaPay 回調"""
        try:
            logger.info(f"收到 OxaPay 回調: {callback_data}")
            
            # 驗證回調簽名 (如果有實現)
            if not self.verify_callback_signature(callback_data):
                logger.error("回調簽名驗證失敗")
                return False, None
            
            track_id = callback_data.get('trackId')
            status = callback_data.get('status')
            
            if not track_id:
                logger.error("回調中缺少 trackId")
                return False, None
            
            # 獲取付款記錄
            payment_record = self.get_payment_record(track_id)
            if not payment_record:
                logger.error(f"找不到付款記錄: {track_id}")
                return False, None
            
            # 更新付款狀態
            if status == 'Paid':
                return self.process_successful_payment(track_id, callback_data)
            elif status == 'Confirming':
                self.update_payment_status(track_id, 'confirming')
                return True, None
            elif status == 'Expired':
                self.update_payment_status(track_id, 'expired')
                return True, None
            else:
                logger.warning(f"未知的付款狀態: {status}")
                return True, None
                
        except Exception as e:
            logger.error(f"處理回調失敗: {str(e)}")
            return False, None
    
    def process_successful_payment(self, track_id: str, callback_data: Dict) -> Tuple[bool, Optional[str]]:
        """處理成功付款"""
        try:
            # 更新付款狀態
            self.update_payment_status(track_id, 'completed')
            
            # 生成用戶帳號
            user_uuid = self.create_user_account(track_id)
            
            if user_uuid:
                # 發送 Email
                payment_record = self.get_payment_record(track_id)
                if payment_record:
                    self.send_license_email(
                        payment_record['user_email'],
                        payment_record['user_name'],
                        user_uuid,
                        payment_record['plan_name'],
                        payment_record['plan_period']
                    )
                
                logger.info(f"✅ 付款處理完成: {track_id}, 用戶序號: {user_uuid}")
                return True, user_uuid
            else:
                logger.error(f"❌ 創建用戶帳號失敗: {track_id}")
                return False, None
                
        except Exception as e:
            logger.error(f"處理成功付款失敗: {str(e)}")
            return False, None
    
    def verify_callback_signature(self, callback_data: Dict) -> bool:
        """驗證回調簽名 (簡化版本)"""
        # OxaPay 可能不提供簽名驗證，這裡實現基本驗證
        # 你可以根據實際需求修改
        return True
    
    def get_payment_info(self, track_id: str) -> Optional[Dict]:
        """查詢付款資訊"""
        try:
            response = requests.post(
                f"{self.api_base_url}/merchants/inquiry",
                json={
                    "merchant": self.merchant_key,
                    "trackId": track_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 100:
                    return result
            
            logger.error(f"查詢付款資訊失敗: {track_id}")
            return None
            
        except Exception as e:
            logger.error(f"查詢付款資訊錯誤: {str(e)}")
            return None
    
    def get_exchange_rate(self, from_currency: str = "TWD", to_currency: str = "USDT") -> float:
        """獲取匯率 (這裡使用固定匯率，你可以接入實時匯率API)"""
        # 簡化版本，使用固定匯率
        rates = {
            "TWD_USDT": 0.032,  # 1 TWD = 0.032 USDT
            "USDT_TWD": 31.25   # 1 USDT = 31.25 TWD
        }
        
        rate_key = f"{from_currency}_{to_currency}"
        return rates.get(rate_key, 0.032)
    
    def save_payment_record(self, track_id: str, payment_data: Dict):
        """保存付款記錄"""
        try:
            self.db.collection('oxapay_payments').document(track_id).set(payment_data)
            logger.info(f"付款記錄已保存: {track_id}")
        except Exception as e:
            logger.error(f"保存付款記錄失敗: {str(e)}")
    
    def update_payment_status(self, track_id: str, status: str):
        """更新付款狀態"""
        try:
            self.db.collection('oxapay_payments').document(track_id).update({
                'status': status,
                'updated_at': datetime.now()
            })
            logger.info(f"付款狀態已更新: {track_id} -> {status}")
        except Exception as e:
            logger.error(f"更新付款狀態失敗: {str(e)}")
    
    def get_payment_record(self, track_id: str) -> Optional[Dict]:
        """獲取付款記錄"""
        try:
            doc = self.db.collection('oxapay_payments').document(track_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"獲取付款記錄失敗: {str(e)}")
            return None
    
    def create_user_account(self, track_id: str) -> Optional[str]:
        """根據付款記錄創建用戶帳號"""
        try:
            payment_record = self.get_payment_record(track_id)
            if not payment_record:
                return None
            
            # 生成唯一的 UUID
            user_uuid = f"artale_oxapay_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"
            uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
            
            # 確定有效期
            plan_periods = {
                'trial_7': 7,
                'monthly_30': 30,
                'quarterly_90': 90
            }
            
            days = plan_periods.get(payment_record['plan_id'], 30)
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            
            # 創建用戶
            user_data = {
                "original_uuid": user_uuid,
                "display_name": payment_record['user_name'],
                "permissions": {
                    "script_access": True,
                    "config_modify": True
                },
                "active": True,
                "created_at": datetime.now(),
                "created_by": "oxapay_payment",
                "login_count": 0,
                "expires_at": expires_at,
                "payment_id": track_id,
                "payment_method": "oxapay",
                "payment_status": "paid",
                "notes": f"OxaPay 付款創建 - {payment_record['plan_name']}"
            }
            
            self.db.collection('authorized_users').document(uuid_hash).set(user_data)
            
            # 更新付款記錄
            self.db.collection('oxapay_payments').document(track_id).update({
                'user_uuid': user_uuid,
                'user_created': True,
                'user_created_at': datetime.now()
            })
            
            logger.info(f"用戶帳號已創建: {user_uuid}")
            return user_uuid
            
        except Exception as e:
            logger.error(f"創建用戶帳號失敗: {str(e)}")
            return None
    
    def send_license_email(self, email: str, name: str, uuid: str, plan_name: str, plan_period: str) -> bool:
        """發送序號 Email"""
        try:
            smtp_server = os.environ.get('SMTP_SERVER')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            email_user = os.environ.get('EMAIL_USER')
            email_password = os.environ.get('EMAIL_PASSWORD')
            
            if not all([smtp_server, email_user, email_password]):
                logger.error("Email 設定不完整")
                return False
            
            msg = MIMEMultipart()
            
            # 設置顯示名稱
            from_display_name = "Scrilab"
            msg['From'] = f"{from_display_name} <{email_user}>"
            msg['To'] = email
            msg['Subject'] = f"Scrilab Artale 服務序號 - {plan_name}"
            
            # 設置回覆地址
            support_email = os.environ.get('SUPPORT_EMAIL', email_user)
            msg['Reply-To'] = f"Scrilab Support <{support_email}>"
            
            body = f"""
親愛的 {name}，

感謝您購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
💳 付款方式：加密貨幣 (USDT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 如何使用：
1. 下載 Scrilab Artale 客戶端
2. 在登入界面輸入您的專屬序號
3. 開始享受專業的遊戲技術服務

📞 技術支援：
- Discord：https://discord.gg/HPzNrQmN
- Email：scrilabstaff@gmail.com

⚠️ 重要提醒：
- 請妥善保管您的序號，避免外洩
- 序號僅供個人使用，請勿分享給他人
- 如有任何問題，歡迎透過上述方式聯繫我們

再次感謝您選擇 Scrilab 技術服務！

Scrilab 技術團隊
{datetime.now().strftime('%Y年%m月%d日')}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"序號 Email 已發送至: {email}")
            return True
            
        except Exception as e:
            logger.error(f"發送 Email 失敗: {str(e)}")
            return False