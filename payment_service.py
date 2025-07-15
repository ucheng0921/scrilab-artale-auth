import paypalrestsdk
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import hashlib
import uuid as uuid_lib

logger = logging.getLogger(__name__)

# 配置 PayPal SDK
paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET')
})

class PaymentService:
    def __init__(self, db):
        self.db = db
    
    def create_payment(self, plan_info, user_info):
        """創建 PayPal 付款"""
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"{os.environ.get('BASE_URL', 'http://localhost:5000')}/payment/success",
                "cancel_url": f"{os.environ.get('BASE_URL', 'http://localhost:5000')}/payment/cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Artale {plan_info['name']}",
                        "sku": plan_info['id'],
                        "price": str(plan_info['price']),
                        "currency": "TWD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(plan_info['price']),
                    "currency": "TWD"
                },
                "description": f"Artale 遊戲技術服務 - {plan_info['name']}"
            }]
        })
        
        if payment.create():
            # 保存付款記錄
            self.save_payment_record(payment.id, plan_info, user_info, 'pending')
            return payment
        else:
            logger.error(f"PayPal 付款創建失敗: {payment.error}")
            return None
    
    def execute_payment(self, payment_id, payer_id):
        """執行 PayPal 付款"""
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # 更新付款狀態
            self.update_payment_status(payment_id, 'completed')
            
            # 生成用戶帳號
            user_uuid = self.create_user_account(payment_id)
            
            # 發送 Email
            payment_record = self.get_payment_record(payment_id)
            if payment_record and user_uuid:
                self.send_license_email(
                    payment_record['user_email'],
                    payment_record['user_name'],
                    user_uuid,
                    payment_record['plan_name'],
                    payment_record['plan_period']
                )
            
            return True, user_uuid
        else:
            logger.error(f"PayPal 付款執行失敗: {payment.error}")
            return False, None
    
    def save_payment_record(self, payment_id, plan_info, user_info, status):
        """保存付款記錄"""
        try:
            payment_data = {
                'payment_id': payment_id,
                'user_name': user_info['name'],
                'user_email': user_info['email'],
                'user_phone': user_info.get('phone', ''),
                'plan_id': plan_info['id'],
                'plan_name': plan_info['name'],
                'plan_period': plan_info['period'],
                'amount': plan_info['price'],
                'currency': 'TWD',
                'status': status,
                'created_at': datetime.now(),
                'payment_method': 'paypal'
            }
            
            self.db.collection('payment_records').document(payment_id).set(payment_data)
            logger.info(f"付款記錄已保存: {payment_id}")
            
        except Exception as e:
            logger.error(f"保存付款記錄失敗: {str(e)}")
    
    def update_payment_status(self, payment_id, status):
        """更新付款狀態"""
        try:
            self.db.collection('payment_records').document(payment_id).update({
                'status': status,
                'completed_at': datetime.now()
            })
        except Exception as e:
            logger.error(f"更新付款狀態失敗: {str(e)}")
    
    def get_payment_record(self, payment_id):
        """獲取付款記錄"""
        try:
            doc = self.db.collection('payment_records').document(payment_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"獲取付款記錄失敗: {str(e)}")
            return None
    
    def create_user_account(self, payment_id):
        """根據付款記錄創建用戶帳號"""
        try:
            payment_record = self.get_payment_record(payment_id)
            if not payment_record:
                return None
            
            # 生成唯一的 UUID
            user_uuid = f"artale_paid_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"
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
                "created_by": "paypal_payment",
                "login_count": 0,
                "expires_at": expires_at,
                "payment_id": payment_id,
                "payment_status": "paid",
                "notes": f"PayPal 付款創建 - {payment_record['plan_name']}"
            }
            
            self.db.collection('authorized_users').document(uuid_hash).set(user_data)
            
            # 更新付款記錄
            self.db.collection('payment_records').document(payment_id).update({
                'user_uuid': user_uuid,
                'user_created': True
            })
            
            logger.info(f"用戶帳號已創建: {user_uuid}")
            return user_uuid
            
        except Exception as e:
            logger.error(f"創建用戶帳號失敗: {str(e)}")
            return None
    
    def send_license_email(self, email, name, uuid, plan_name, plan_period):
        """發送序號 Email"""
        try:
            smtp_server = os.environ.get('SMTP_SERVER')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            email_user = os.environ.get('EMAIL_USER')
            email_password = os.environ.get('EMAIL_PASSWORD')
            
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = email
            msg['Subject'] = f"Scrilab Artale 服務序號 - {plan_name}"
            
            body = f"""
親愛的 {name}，

感謝您購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 如何使用：
1. 下載 Scrilab Artale 客戶端
2. 在登入界面輸入您的專屬序號
3. 開始享受專業的遊戲技術服務

📞 技術支援：
- Discord：https://discord.gg/HPzNrQmN
- Email：pink870921aa@gmail.com

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