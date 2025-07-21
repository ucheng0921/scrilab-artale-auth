"""
itchio_service.py - itch.io 付款服務整合
"""
import requests
import logging
import os
import hashlib
import uuid as uuid_lib
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class ItchioService:
    """itch.io 付款服務"""
    
    def __init__(self, db):
        self.db = db
        self.api_key = os.environ.get('ITCHIO_API_KEY')
        self.base_url = 'https://itch.io/api/1'
        self.webhook_secret = os.environ.get('ITCHIO_WEBHOOK_SECRET')
        
        if not self.api_key:
            logger.warning("⚠️ ITCHIO_API_KEY 未設定")
        else:
            logger.info("✅ itch.io 服務已初始化")
    
    def get_service_plans(self):
        """獲取服務方案配置"""
        return {
            'trial_7': {
                'name': '體驗服務',
                'name_en': 'Scrilab Artale Trial Service',
                'price_twd': 5,
                'price_usd': 0.16,  # 約 5 TWD
                'period': '7天',
                'period_en': '7 days',
                'description': '適合新手玩家體驗的基礎技術服務',
                'description_en': 'Basic gaming service for beginners to experience',
                'days': 7
            },
            'monthly_30': {
                'name': '標準服務',
                'name_en': 'Scrilab Artale Standard Service',
                'price_twd': 599,
                'price_usd': 19.17,  # 約 599 TWD
                'period': '30天',
                'period_en': '30 days',
                'description': '最受歡迎的完整技術服務方案',
                'description_en': 'Most popular complete gaming service package',
                'days': 30
            },
            'quarterly_90': {
                'name': '季度服務',
                'name_en': 'Scrilab Artale Quarterly Service',
                'price_twd': 1499,
                'price_usd': 47.97,  # 約 1499 TWD
                'period': '90天',
                'period_en': '90 days',
                'description': '長期使用最划算的全功能技術服務',
                'description_en': 'Best value long-term complete gaming service',
                'days': 90
            }
        }
    
    def create_purchase_url(self, plan_id, user_info):
        """為指定方案創建 itch.io 購買 URL"""
        try:
            plans = self.get_service_plans()
            if plan_id not in plans:
                raise ValueError(f"無效的方案 ID: {plan_id}")
            
            plan = plans[plan_id]
            
            # 創建付款記錄
            payment_id = self.create_payment_record(plan_id, plan, user_info)
            
            # 構建 itch.io 購買 URL
            # 注意：這裡需要你在 itch.io 上預先創建好對應的產品
            product_urls = {
                'trial_7': os.environ.get('ITCHIO_TRIAL_PRODUCT_URL'),
                'monthly_30': os.environ.get('ITCHIO_MONTHLY_PRODUCT_URL'),
                'quarterly_90': os.environ.get('ITCHIO_QUARTERLY_PRODUCT_URL')
            }
            
            base_purchase_url = product_urls.get(plan_id)
            if not base_purchase_url:
                raise ValueError(f"未設定方案 {plan_id} 的 itch.io 產品 URL")
            
            # 添加自定義參數以便追蹤
            purchase_url = f"{base_purchase_url}?custom_data={payment_id}"
            
            return {
                'success': True,
                'purchase_url': purchase_url,
                'payment_id': payment_id,
                'plan': plan
            }
            
        except Exception as e:
            logger.error(f"創建 itch.io 購買 URL 失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment_record(self, plan_id, plan, user_info):
        """創建付款記錄"""
        try:
            payment_id = f"itchio_{uuid_lib.uuid4().hex[:16]}"
            
            payment_data = {
                'payment_id': payment_id,
                'user_name': user_info['name'],
                'user_email': user_info['email'],
                'user_phone': user_info.get('phone', ''),
                'plan_id': plan_id,
                'plan_name': plan['name'],
                'plan_period': plan['period'],
                'amount_twd': plan['price_twd'],
                'amount_usd': plan['price_usd'],
                'currency': 'USD',
                'status': 'pending',
                'created_at': datetime.now(),
                'payment_method': 'itchio',
                'itchio_data': {
                    'product_name': plan['name_en'],
                    'expected_amount': plan['price_usd']
                }
            }
            
            self.db.collection('payment_records').document(payment_id).set(payment_data)
            logger.info(f"itch.io 付款記錄已創建: {payment_id}")
            
            return payment_id
            
        except Exception as e:
            logger.error(f"創建付款記錄失敗: {str(e)}")
            raise
    
    def verify_webhook_signature(self, payload, signature):
        """驗證 itch.io webhook 簽名"""
        try:
            if not self.webhook_secret:
                logger.warning("未設定 ITCHIO_WEBHOOK_SECRET，跳過簽名驗證")
                return True
            
            # itch.io webhook 簽名驗證
            expected_signature = hashlib.sha256(
                (self.webhook_secret + payload).encode()
            ).hexdigest()
            
            return signature == expected_signature
            
        except Exception as e:
            logger.error(f"Webhook 簽名驗證失敗: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data):
        """處理 itch.io webhook"""
        try:
            # 解析 webhook 數據
            event_type = webhook_data.get('type')
            purchase_data = webhook_data.get('purchase', {})
            
            if event_type != 'purchase':
                logger.info(f"忽略非購買事件: {event_type}")
                return {'success': True, 'message': 'Event ignored'}
            
            # 提取購買信息
            purchase_id = purchase_data.get('id')
            amount = purchase_data.get('amount_cents', 0) / 100  # 轉換為美元
            buyer_email = purchase_data.get('buyer_email')
            custom_data = purchase_data.get('custom_data')  # 我們的 payment_id
            
            if not custom_data:
                logger.error("Webhook 中缺少 custom_data")
                return {'success': False, 'error': 'Missing custom_data'}
            
            # 查找對應的付款記錄
            payment_record = self.get_payment_record(custom_data)
            if not payment_record:
                logger.error(f"找不到付款記錄: {custom_data}")
                return {'success': False, 'error': 'Payment record not found'}
            
            # 驗證金額
            expected_amount = payment_record.get('amount_usd', 0)
            if abs(amount - expected_amount) > 0.01:  # 允許1分錢的誤差
                logger.error(f"金額不匹配: 期望 ${expected_amount}, 收到 ${amount}")
                return {'success': False, 'error': 'Amount mismatch'}
            
            # 更新付款狀態
            self.update_payment_status(custom_data, 'completed', {
                'itchio_purchase_id': purchase_id,
                'actual_amount': amount,
                'buyer_email': buyer_email,
                'completed_at': datetime.now()
            })
            
            # 創建用戶帳號
            user_uuid = self.create_user_account(custom_data)
            
            # 發送序號郵件
            if user_uuid:
                self.send_license_email(
                    payment_record['user_email'],
                    payment_record['user_name'],
                    user_uuid,
                    payment_record['plan_name'],
                    payment_record['plan_period']
                )
            
            logger.info(f"itch.io 付款處理完成: {custom_data} -> {user_uuid}")
            
            return {
                'success': True,
                'payment_id': custom_data,
                'user_uuid': user_uuid
            }
            
        except Exception as e:
            logger.error(f"處理 itch.io webhook 失敗: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_payment_record(self, payment_id):
        """獲取付款記錄"""
        try:
            doc = self.db.collection('payment_records').document(payment_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"獲取付款記錄失敗: {str(e)}")
            return None
    
    def update_payment_status(self, payment_id, status, additional_data=None):
        """更新付款狀態"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now()
            }
            
            if additional_data:
                update_data.update(additional_data)
            
            self.db.collection('payment_records').document(payment_id).update(update_data)
            logger.info(f"付款狀態已更新: {payment_id} -> {status}")
            
        except Exception as e:
            logger.error(f"更新付款狀態失敗: {str(e)}")
    
    def create_user_account(self, payment_id):
        """根據付款記錄創建用戶帳號"""
        try:
            payment_record = self.get_payment_record(payment_id)
            if not payment_record:
                return None
            
            # 生成唯一的 UUID
            user_uuid = f"artale_itchio_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"
            uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
            
            # 確定有效期
            plan_days = {
                'trial_7': 7,
                'monthly_30': 30,
                'quarterly_90': 90
            }
            
            days = plan_days.get(payment_record['plan_id'], 30)
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
                "created_by": "itchio_payment",
                "login_count": 0,
                "expires_at": expires_at,
                "payment_id": payment_id,
                "payment_status": "paid",
                "notes": f"itch.io 付款創建 - {payment_record['plan_name']}"
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
            
            if not all([smtp_server, email_user, email_password]):
                logger.warning("Email 配置不完整，跳過發送")
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

感謝您透過 itch.io 購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
💳 付款方式：itch.io
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
    
    def get_purchase_stats(self):
        """獲取購買統計"""
        try:
            payments_ref = self.db.collection('payment_records')
            itchio_payments = payments_ref.where('payment_method', '==', 'itchio').stream()
            
            total_payments = 0
            completed_payments = 0
            total_revenue = 0
            
            for payment in itchio_payments:
                payment_data = payment.to_dict()
                total_payments += 1
                
                if payment_data.get('status') == 'completed':
                    completed_payments += 1
                    total_revenue += payment_data.get('amount_twd', 0)
            
            return {
                'total_payments': total_payments,
                'completed_payments': completed_payments,
                'pending_payments': total_payments - completed_payments,
                'total_revenue_twd': total_revenue,
                'success_rate': (completed_payments / total_payments * 100) if total_payments > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"獲取購買統計失敗: {str(e)}")
            return {
                'total_payments': 0,
                'completed_payments': 0,
                'pending_payments': 0,
                'total_revenue_twd': 0,
                'success_rate': 0
            }