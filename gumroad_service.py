"""
gumroad_service.py - 修復版本，正確實現 Gumroad API 整合
"""
import requests
import logging
import os
import hashlib
import uuid as uuid_lib
import hmac
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

logger = logging.getLogger(__name__)

class GumroadService:
    """正確的 Gumroad API 服務實現"""
    
    def __init__(self, db):
        self.db = db
        self.access_token = os.environ.get('GUMROAD_ACCESS_TOKEN')
        self.base_url = 'https://api.gumroad.com/v2'
        self.webhook_secret = os.environ.get('GUMROAD_WEBHOOK_SECRET')
        
        if not self.access_token:
            logger.warning("⚠️ GUMROAD_ACCESS_TOKEN 未設定")
        else:
            logger.info("✅ Gumroad 服務已初始化")
            # 延遲設置 webhooks，讓應用先完全啟動
            self._delayed_setup_webhooks()
    
    def _delayed_setup_webhooks(self):
        """延遲設置 webhooks"""
        import threading
        def setup_later():
            import time
            time.sleep(5)  # 等待 5 秒讓應用完全啟動
            self.setup_webhooks()
        
        thread = threading.Thread(target=setup_later, daemon=True)
        thread.start()
    
    def get_service_plans(self):
        """獲取服務方案配置 - 使用正確的產品 ID"""
        return {
            'trial_7': {
                'name': '體驗服務',
                'name_en': 'Scrilab Artale Trial Service',
                'price_twd': 150,
                'price_usd': 5.00,
                'period': '7天',
                'period_en': '7 days',
                'description': '適合新手玩家體驗的基礎技術服務',
                'description_en': 'Basic gaming service for beginners to experience',
                'days': 7,
                'gumroad_product_id': os.environ.get('GUMROAD_TRIAL_PRODUCT_ID')
            },
            'monthly_30': {
                'name': '標準服務',
                'name_en': 'Scrilab Artale Standard Service',
                'price_twd': 899,
                'price_usd': 29.99,
                'period': '30天',
                'period_en': '30 days',
                'description': '最受歡迎的完整技術服務方案',
                'description_en': 'Most popular complete gaming service package',
                'days': 30,
                'gumroad_product_id': os.environ.get('GUMROAD_MONTHLY_PRODUCT_ID')
            },
            'quarterly_90': {
                'name': '季度服務',
                'name_en': 'Scrilab Artale Quarterly Service',
                'price_twd': 2399,
                'price_usd': 79.99,
                'period': '90天',
                'period_en': '90 days',
                'description': '長期使用最划算的全功能技術服務',
                'description_en': 'Best value long-term complete gaming service',
                'days': 90,
                'gumroad_product_id': os.environ.get('GUMROAD_QUARTERLY_PRODUCT_ID')
            }
        }
    
    def setup_webhooks(self):
        """正確設置 Gumroad Resource Subscriptions"""
        try:
            webhook_base_url = os.environ.get('WEBHOOK_BASE_URL', 'https://scrilab.onrender.com')
            
            if not webhook_base_url.startswith('http'):
                webhook_base_url = f"https://{webhook_base_url}"
            
            webhook_base_url = webhook_base_url.rstrip('/')
            webhook_url = f"{webhook_base_url}/gumroad/webhook"
            
            logger.info(f"🔗 設置 Webhook URL: {webhook_url}")
            
            # 只監聽 sale 事件
            resource_types = ['sale', 'refund']
            success_count = 0
            
            for resource_name in resource_types:
                try:
                    # 先檢查是否已存在
                    existing = self._get_existing_subscriptions(resource_name)
                    valid_existing = [sub for sub in existing if sub.get('post_url') == webhook_url]
                    
                    if valid_existing:
                        logger.info(f"✅ {resource_name} webhook 已存在且正確")
                        success_count += 1
                        continue
                    
                    # 清理舊的無效 webhooks
                    invalid_existing = [sub for sub in existing if sub.get('post_url') != webhook_url]
                    for invalid_sub in invalid_existing:
                        self._delete_subscription(invalid_sub.get('id'))
                        logger.info(f"🗑️ 清理無效的 {resource_name} webhook: {invalid_sub.get('post_url')}")
                    
                    # 創建新的 webhook
                    url = f"{self.base_url}/resource_subscriptions"
                    data = {
                        'access_token': self.access_token,
                        'resource_name': resource_name,
                        'post_url': webhook_url
                    }
                    
                    response = requests.put(url, data=data)
                    result = response.json()
                    
                    if result.get('success'):
                        logger.info(f"✅ 成功創建 {resource_name} webhook")
                        success_count += 1
                    else:
                        logger.error(f"❌ 創建 {resource_name} webhook 失敗: {result}")
                        
                except Exception as e:
                    logger.error(f"❌ 設置 {resource_name} webhook 時發生錯誤: {str(e)}")
            
            if success_count > 0:
                logger.info(f"🎉 Webhook 設置完成 {success_count}/{len(resource_types)}")
                return True
            else:
                logger.error("❌ 沒有成功設置任何 webhook")
                return False
                
        except Exception as e:
            logger.error(f"❌ 設置 webhooks 失敗: {str(e)}")
            return False
    
    def _get_existing_subscriptions(self, resource_name):
        """獲取現有的 resource subscriptions"""
        try:
            url = f"{self.base_url}/resource_subscriptions"
            params = {
                'access_token': self.access_token,
                'resource_name': resource_name
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('success'):
                return result.get('resource_subscriptions', [])
            return []
            
        except Exception as e:
            logger.error(f"獲取現有訂閱失敗: {str(e)}")
            return []
    
    def _delete_subscription(self, subscription_id):
        """刪除 resource subscription"""
        try:
            url = f"{self.base_url}/resource_subscriptions/{subscription_id}"
            data = {'access_token': self.access_token}
            
            response = requests.delete(url, data=data)
            result = response.json()
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"刪除訂閱失敗: {str(e)}")
            return False
    
    def create_purchase_url(self, plan_id, user_info):
        """創建 Gumroad 購買 URL - 修復版本"""
        try:
            plans = self.get_service_plans()
            if plan_id not in plans:
                raise ValueError(f"無效的方案 ID: {plan_id}")
            
            plan = plans[plan_id]
            product_id = plan.get('gumroad_product_id')
            
            if not product_id:
                raise ValueError(f"方案 {plan_id} 沒有設定 Gumroad 產品 ID")
            
            # 獲取產品的實際購買 URL
            product_info = self._get_product_info(product_id)
            
            if not product_info:
                raise ValueError(f"無法獲取產品 {product_id} 的信息")
            
            # 創建付款記錄用於追蹤
            payment_id = self.create_payment_record(plan_id, plan, user_info)
            
            # 使用產品的 short_url
            purchase_url = product_info.get('short_url')
            
            if not purchase_url:
                # 如果沒有 short_url，嘗試使用其他方式
                custom_permalink = product_info.get('custom_permalink')
                if custom_permalink:
                    purchase_url = f"https://gumroad.com/l/{custom_permalink}"
                else:
                    # 最後手段，使用產品 ID
                    purchase_url = f"https://gumroad.com/l/{product_id}"
            
            # 添加追蹤參數
            separator = '&' if '?' in purchase_url else '?'
            purchase_url += f"{separator}payment_tracking={payment_id}"
            
            logger.info(f"生成購買 URL: {purchase_url}")
            
            return {
                'success': True,
                'purchase_url': purchase_url,
                'payment_id': payment_id,
                'plan': plan
            }
            
        except Exception as e:
            logger.error(f"創建 Gumroad 購買 URL 失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_product_info(self, product_id):
        """獲取產品信息"""
        try:
            url = f"{self.base_url}/products/{product_id}"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('success'):
                return result.get('product')
            else:
                logger.error(f"獲取產品信息失敗: {result}")
                return None
                
        except Exception as e:
            logger.error(f"獲取產品信息錯誤: {str(e)}")
            return None
    
    def create_payment_record(self, plan_id, plan, user_info):
        """創建付款記錄"""
        try:
            payment_id = f"gumroad_{uuid_lib.uuid4().hex[:16]}"
            
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
                'payment_method': 'gumroad',
                'gumroad_data': {
                    'product_id': plan.get('gumroad_product_id'),
                    'product_name': plan['name_en'],
                    'expected_amount': plan['price_usd']
                }
            }
            
            self.db.collection('payment_records').document(payment_id).set(payment_data)
            logger.info(f"Gumroad 付款記錄已創建: {payment_id}")
            
            return payment_id
            
        except Exception as e:
            logger.error(f"創建付款記錄失敗: {str(e)}")
            raise
    
    def verify_webhook_signature(self, payload, signature):
        """驗證 Gumroad webhook 簽名"""
        try:
            if not self.webhook_secret:
                logger.warning("未設定 GUMROAD_WEBHOOK_SECRET，跳過簽名驗證")
                return True
            
            if not signature:
                logger.warning("沒有收到簽名")
                return True
            
            # Gumroad 使用 HMAC-SHA256 簽名
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode() if isinstance(payload, str) else payload,
                hashlib.sha256
            ).hexdigest()
            
            # 比較簽名
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook 簽名驗證失敗: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data):
        """處理 Gumroad webhook - 修復版本"""
        try:
            logger.info(f"處理 Gumroad webhook: {webhook_data}")
            
            # 提取關鍵信息
            sale_id = webhook_data.get('sale_id')
            if not sale_id:
                logger.error("Webhook 缺少 sale_id")
                return {'success': False, 'error': 'Missing sale_id'}
            
            product_id = webhook_data.get('product_id')
            buyer_email = webhook_data.get('email')
            buyer_name = webhook_data.get('purchaser_name', buyer_email)
            
            # price 是以美分為單位的整數
            price_cents = webhook_data.get('price', 0)
            if isinstance(price_cents, str):
                try:
                    price_cents = int(price_cents)
                except ValueError:
                    price_cents = 0
            
            amount_usd = price_cents / 100.0
            
            # 檢查是否為重複處理
            if self.is_duplicate_webhook(sale_id):
                logger.info(f"跳過重複的 webhook: {sale_id}")
                return {'success': True, 'message': 'Duplicate webhook ignored'}
            
            # 根據 product_id 確定方案
            plan_info = self.get_plan_by_product_id(product_id)
            if not plan_info:
                logger.error(f"未找到產品 ID 對應的方案: {product_id}")
                return {'success': False, 'error': 'Unknown product'}
            
            # 驗證金額
            expected_amount = plan_info['price_usd']
            if abs(amount_usd - expected_amount) > 0.01:
                logger.warning(f"金額不匹配: 期望 ${expected_amount}, 收到 ${amount_usd}")
                # 不直接拒絕，記錄警告即可
            
            # 創建或更新付款記錄
            payment_id = self.create_or_update_payment_record(webhook_data, plan_info)
            
            # 創建用戶帳號
            user_uuid = self.create_user_account(payment_id, webhook_data, plan_info)
            
            # 發送序號郵件
            if user_uuid:
                email_sent = self.send_license_email(
                    buyer_email,
                    buyer_name,
                    user_uuid,
                    plan_info['name'],
                    plan_info['period']
                )
                
                if email_sent:
                    logger.info(f"序號郵件已發送至: {buyer_email}")
                else:
                    logger.warning(f"序號郵件發送失敗: {buyer_email}")
            
            # 記錄處理完成
            self.mark_webhook_processed(sale_id)
            
            logger.info(f"Gumroad 付款處理完成: {payment_id} -> {user_uuid}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'user_uuid': user_uuid
            }
            
        except Exception as e:
            logger.error(f"處理 Gumroad webhook 失敗: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def is_duplicate_webhook(self, sale_id):
        """檢查是否為重複的 webhook"""
        try:
            doc = self.db.collection('processed_webhooks').document(sale_id).get()
            return doc.exists
        except Exception as e:
            logger.error(f"檢查重複 webhook 失敗: {str(e)}")
            return False
    
    def mark_webhook_processed(self, sale_id):
        """標記 webhook 已處理"""
        try:
            self.db.collection('processed_webhooks').document(sale_id).set({
                'sale_id': sale_id,
                'processed_at': datetime.now()
            })
        except Exception as e:
            logger.error(f"標記 webhook 已處理失敗: {str(e)}")
    
    def get_plan_by_product_id(self, product_id):
        """根據 Gumroad 產品 ID 獲取方案信息"""
        plans = self.get_service_plans()
        for plan_id, plan in plans.items():
            if plan.get('gumroad_product_id') == product_id:
                plan['plan_id'] = plan_id
                return plan
        return None
    
    def create_or_update_payment_record(self, webhook_data, plan_info):
        """創建或更新付款記錄"""
        try:
            payment_id = f"gumroad_{webhook_data['sale_id']}"
            
            price_cents = webhook_data.get('price', 0)
            if isinstance(price_cents, str):
                try:
                    price_cents = int(price_cents)
                except ValueError:
                    price_cents = 0
            
            payment_data = {
                'payment_id': payment_id,
                'sale_id': webhook_data['sale_id'],
                'user_name': webhook_data.get('purchaser_name', ''),
                'user_email': webhook_data['email'],
                'plan_id': plan_info['plan_id'],
                'plan_name': plan_info['name'],
                'plan_period': plan_info['period'],
                'amount_twd': plan_info['price_twd'],
                'amount_usd': price_cents / 100.0,
                'currency': webhook_data.get('currency', 'usd').upper(),
                'status': 'completed',
                'payment_method': 'gumroad',
                'gumroad_data': {
                    'product_id': webhook_data['product_id'],
                    'seller_id': webhook_data.get('seller_id'),
                    'order_number': webhook_data.get('order_number'),
                    'gumroad_fee': webhook_data.get('gumroad_fee', 0),
                    'can_contact': webhook_data.get('can_contact', False)
                },
                'created_at': datetime.now(),
                'completed_at': datetime.now(),
                'webhook_received_at': datetime.now()
            }
            
            self.db.collection('payment_records').document(payment_id).set(payment_data)
            logger.info(f"付款記錄已更新: {payment_id}")
            
            return payment_id
            
        except Exception as e:
            logger.error(f"創建/更新付款記錄失敗: {str(e)}")
            raise
    
    def create_user_account(self, payment_id, webhook_data, plan_info):
        """根據付款記錄創建用戶帳號"""
        try:
            # 生成唯一的 UUID
            user_uuid = f"artale_gumroad_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"
            uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
            
            # 確定有效期
            days = plan_info['days']
            expires_at = None
            if days > 0:
                expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            
            # 創建用戶
            user_data = {
                "original_uuid": user_uuid,
                "display_name": webhook_data.get('purchaser_name', webhook_data['email']),
                "permissions": {
                    "script_access": True,
                    "config_modify": True
                },
                "active": True,
                "created_at": datetime.now(),
                "created_by": "gumroad_payment",
                "login_count": 0,
                "payment_id": payment_id,
                "payment_status": "paid",
                "gumroad_data": {
                    "sale_id": webhook_data['sale_id'],
                    "product_id": webhook_data['product_id']
                },
                "notes": f"Gumroad 付款創建 - {plan_info['name']} - {webhook_data['sale_id']}"
            }
            
            if expires_at:
                user_data["expires_at"] = expires_at
            
            self.db.collection('authorized_users').document(uuid_hash).set(user_data)
            
            # 更新付款記錄
            self.db.collection('payment_records').document(payment_id).update({
                'user_uuid': user_uuid,
                'user_created': True,
                'user_created_at': datetime.now()
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

感謝您透過 Gumroad 購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
💳 付款方式：Gumroad
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
    
    def get_payment_record(self, payment_id):
        """獲取付款記錄"""
        try:
            doc = self.db.collection('payment_records').document(payment_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"獲取付款記錄失敗: {str(e)}")
            return None
    
    def get_purchase_stats(self):
        """獲取購買統計"""
        try:
            payments_ref = self.db.collection('payment_records')
            gumroad_payments = payments_ref.where('payment_method', '==', 'gumroad').stream()
            
            total_payments = 0
            completed_payments = 0
            total_revenue = 0
            
            for payment in gumroad_payments:
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
    
    def debug_all_products(self):
        """調試方法：獲取所有產品信息"""
        try:
            url = f"{self.base_url}/products"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('success'):
                products = result.get('products', [])
                logger.info(f"找到 {len(products)} 個產品")
                return {
                    'success': True,
                    'products': products
                }
            else:
                logger.error(f"獲取產品列表失敗: {result}")
                return {
                    'success': False,
                    'error': result
                }
                
        except Exception as e:
            logger.error(f"調試獲取產品失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
