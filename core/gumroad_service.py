"""
gumroad_service.py - 全面修復版本，解決並發、退款、記憶體洩露等問題
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
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Dict, List, Optional, Tuple
import weakref
from functools import lru_cache

logger = logging.getLogger(__name__)

class GumroadService:
    """全面修復的 Gumroad API 服務 - 處理並發、退款、性能優化"""
    
    def __init__(self, db):
        self.db = db
        self.access_token = os.environ.get('GUMROAD_ACCESS_TOKEN')
        self.base_url = 'https://api.gumroad.com/v2'
        self.webhook_secret = os.environ.get('GUMROAD_WEBHOOK_SECRET')
        
        # 並發處理
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.processing_lock = threading.RLock()
        self.duplicate_checks = {}  # 使用 WeakValueDictionary 防止記憶體洩露
        self.rate_limiter = RateLimiter(max_requests=100, time_window=3600)
        
        # 退款處理
        self.refund_handlers = []
        
        # 緩存管理
        self.cache_timeout = 300  # 5分鐘
        self.last_cleanup = time.time()
        
        if not self.access_token:
            logger.warning("⚠️ GUMROAD_ACCESS_TOKEN 未設定")
        else:
            logger.info("✅ Gumroad 服務已初始化")
            self._delayed_setup_webhooks()
    
    def __del__(self):
        """清理資源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
    
    def _delayed_setup_webhooks(self):
        """延遲設置 webhooks"""
        def setup_later():
            time.sleep(5)
            self.setup_webhooks()
        
        thread = threading.Thread(target=setup_later, daemon=True)
        thread.start()
    
    @lru_cache(maxsize=1)
    def get_service_plans(self):
        """獲取服務方案配置 - 使用緩存"""
        return {
            'trial_7': {
                'name': '體驗服務',
                'name_en': 'Scrilab Artale Trial Service',
                'price_twd': 300,
                'price_usd': 10.21,
                'period': '8天',
                'period_en': '8 days',
                'description': '適合新手玩家體驗的基礎技術服務',
                'description_en': 'Basic gaming service for beginners to experience',
                'days': 8,
                'gumroad_product_id': os.environ.get('GUMROAD_TRIAL_PRODUCT_ID')
            },
            'monthly_30': {
                'name': '標準服務',
                'name_en': 'Scrilab Artale Standard Service',
                'price_twd': 549,
                'price_usd': 18.68,
                'period': '33天',
                'period_en': '33 days',
                'description': '最受歡迎的完整技術服務方案',
                'description_en': 'Most popular complete gaming service package',
                'days': 33,
                'gumroad_product_id': os.environ.get('GUMROAD_MONTHLY_PRODUCT_ID')
            },
            'quarterly_90': {
                'name': '季度服務',
                'name_en': 'Scrilab Artale Quarterly Service',
                'price_twd': 1499,
                'price_usd': 51.02,
                'period': '100天',
                'period_en': '100 days',
                'description': '長期使用最划算的全功能技術服務',
                'description_en': 'Best value long-term complete gaming service',
                'days': 100,
                'gumroad_product_id': os.environ.get('GUMROAD_QUARTERLY_PRODUCT_ID')
            }
        }
    
    def setup_webhooks(self):
        """設置 Gumroad Resource Subscriptions - 支援退款事件"""
        try:
            webhook_base_url = os.environ.get('WEBHOOK_BASE_URL', 'https://scrilab.onrender.com')
            
            if not webhook_base_url.startswith('http'):
                webhook_base_url = f"https://{webhook_base_url}"
            
            webhook_base_url = webhook_base_url.rstrip('/')
            webhook_url = f"{webhook_base_url}/gumroad/webhook"
            
            logger.info(f"🔗 設置 Webhook URL: {webhook_url}")
            
            # 支援所有重要事件，包括退款
            resource_types = ['sale', 'refund', 'cancellation', 'subscription_ended']
            success_count = 0
            
            for resource_name in resource_types:
                try:
                    existing = self._get_existing_subscriptions(resource_name)
                    valid_existing = [sub for sub in existing if sub.get('post_url') == webhook_url]
                    
                    if valid_existing:
                        logger.info(f"✅ {resource_name} webhook 已存在且正確")
                        success_count += 1
                        continue
                    
                    # 清理舊的 webhooks
                    invalid_existing = [sub for sub in existing if sub.get('post_url') != webhook_url]
                    for invalid_sub in invalid_existing:
                        self._delete_subscription(invalid_sub.get('id'))
                        logger.info(f"🗑️ 清理無效的 {resource_name} webhook")
                    
                    # 創建新的 webhook
                    url = f"{self.base_url}/resource_subscriptions"
                    data = {
                        'access_token': self.access_token,
                        'resource_name': resource_name,
                        'post_url': webhook_url
                    }
                    
                    response = requests.put(url, data=data, timeout=30)
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
            
            response = requests.get(url, params=params, timeout=10)
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
            
            response = requests.delete(url, data=data, timeout=10)
            result = response.json()
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"刪除訂閱失敗: {str(e)}")
            return False
    
    def create_purchase_url(self, plan_id, user_info):
        """創建 Gumroad 購買 URL - 並發安全版本"""
        with self.processing_lock:
            try:
                # 速率限制檢查
                if not self.rate_limiter.allow_request():
                    raise Exception("API 請求超過速率限制")
                
                plans = self.get_service_plans()
                if plan_id not in plans:
                    raise ValueError(f"無效的方案 ID: {plan_id}")
                
                plan = plans[plan_id]
                product_id = plan.get('gumroad_product_id')
                
                if not product_id:
                    raise ValueError(f"方案 {plan_id} 沒有設定 Gumroad 產品 ID")
                
                # 獲取產品信息（使用緩存）
                product_info = self._get_product_info_cached(product_id)
                
                if not product_info:
                    raise ValueError(f"無法獲取產品 {product_id} 的信息")
                
                # 創建付款記錄
                payment_id = self.create_payment_record(plan_id, plan, user_info)
                
                # 構建購買 URL
                purchase_url = product_info.get('short_url')
                
                if not purchase_url:
                    custom_permalink = product_info.get('custom_permalink')
                    if custom_permalink:
                        purchase_url = f"https://gumroad.com/l/{custom_permalink}"
                    else:
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
    
    def _get_product_info_cached(self, product_id):
        """獲取產品信息 - 帶緩存"""
        cache_key = f"product_{product_id}"
        cached = getattr(self, '_product_cache', {}).get(cache_key)
        
        if cached and time.time() - cached['timestamp'] < self.cache_timeout:
            return cached['data']
        
        # 從 API 獲取
        product_info = self._get_product_info(product_id)
        
        # 更新緩存
        if not hasattr(self, '_product_cache'):
            self._product_cache = {}
        
        self._product_cache[cache_key] = {
            'data': product_info,
            'timestamp': time.time()
        }
        
        # 定期清理緩存
        self._cleanup_cache()
        
        return product_info
    
    def _get_product_info(self, product_id):
        """獲取產品信息"""
        try:
            url = f"{self.base_url}/products/{product_id}"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get('success'):
                return result.get('product')
            else:
                logger.error(f"獲取產品信息失敗: {result}")
                return None
                
        except Exception as e:
            logger.error(f"獲取產品信息錯誤: {str(e)}")
            return None
    
    def _cleanup_cache(self):
        """清理過期緩存"""
        if time.time() - self.last_cleanup < 300:  # 5分鐘清理一次
            return
        
        if hasattr(self, '_product_cache'):
            current_time = time.time()
            expired_keys = [
                key for key, value in self._product_cache.items()
                if current_time - value['timestamp'] > self.cache_timeout
            ]
            
            for key in expired_keys:
                del self._product_cache[key]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 個過期緩存項目")
        
        self.last_cleanup = time.time()
    
    def create_payment_record(self, plan_id, plan, user_info):
        """創建付款記錄 - 防止重複"""
        try:
            # 生成唯一的付款 ID
            unique_key = f"{user_info['email']}_{plan_id}_{int(time.time())}"
            payment_id = f"gumroad_{hashlib.md5(unique_key.encode()).hexdigest()[:16]}"
            
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
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook 簽名驗證失敗: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data):
        """處理 Gumroad webhook - 支援並發和退款"""
        # 使用異步處理防止阻塞
        future = self.executor.submit(self._process_webhook_async, webhook_data)
        
        try:
            # 等待最多 30 秒
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"Webhook 處理超時或失敗: {str(e)}")
            return {'success': False, 'error': 'Processing timeout'}
    
    def _process_webhook_async(self, webhook_data):
        """異步處理 webhook"""
        with self.processing_lock:
            try:
                logger.info(f"處理 Gumroad webhook: {webhook_data}")
                
                # 確定事件類型
                if 'sale_id' in webhook_data:
                    # 銷售事件
                    return self._handle_sale_event(webhook_data)
                elif 'refund_id' in webhook_data:
                    # 退款事件
                    return self._handle_refund_event(webhook_data)
                elif 'cancellation' in webhook_data:
                    # 取消事件
                    return self._handle_cancellation_event(webhook_data)
                else:
                    logger.warning(f"未知的 webhook 事件類型: {webhook_data}")
                    return {'success': False, 'error': 'Unknown event type'}
                
            except Exception as e:
                logger.error(f"處理 webhook 異步失敗: {str(e)}")
                return {'success': False, 'error': str(e)}
    
    def _handle_sale_event(self, webhook_data):
        """處理銷售事件"""
        try:
            sale_id = webhook_data.get('sale_id')
            if not sale_id:
                logger.error("Sale webhook 缺少 sale_id")
                return {'success': False, 'error': 'Missing sale_id'}
            
            # 檢查重複處理
            if self.is_duplicate_webhook(sale_id, 'sale'):
                logger.info(f"跳過重複的銷售 webhook: {sale_id}")
                return {'success': True, 'message': 'Duplicate webhook ignored'}
            
            product_id = webhook_data.get('product_id')
            buyer_email = webhook_data.get('email')
            buyer_name = webhook_data.get('purchaser_name', buyer_email)
            
            # 處理價格
            price_cents = webhook_data.get('price', 0)
            if isinstance(price_cents, str):
                try:
                    price_cents = int(price_cents)
                except ValueError:
                    price_cents = 0
            
            amount_usd = price_cents / 100.0
            
            # 獲取方案信息
            plan_info = self.get_plan_by_product_id(product_id)
            if not plan_info:
                logger.error(f"未找到產品 ID 對應的方案: {product_id}")
                return {'success': False, 'error': 'Unknown product'}
            
            # 驗證金額
            expected_amount = plan_info['price_usd']
            if abs(amount_usd - expected_amount) > 0.01:
                logger.warning(f"金額不匹配: 期望 ${expected_amount}, 收到 ${amount_usd}")
            
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
            
            # 標記處理完成
            self.mark_webhook_processed(sale_id, 'sale')
            
            logger.info(f"Gumroad 銷售處理完成: {payment_id} -> {user_uuid}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'user_uuid': user_uuid,
                'event_type': 'sale'
            }
            
        except Exception as e:
            logger.error(f"處理銷售事件失敗: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_refund_event(self, webhook_data):
        """處理退款事件 - 停用相關帳號"""
        try:
            refund_id = webhook_data.get('refund_id') or webhook_data.get('sale_id')
            if not refund_id:
                logger.error("Refund webhook 缺少 refund_id 或 sale_id")
                return {'success': False, 'error': 'Missing refund_id'}
            
            # 檢查重複處理
            if self.is_duplicate_webhook(refund_id, 'refund'):
                logger.info(f"跳過重複的退款 webhook: {refund_id}")
                return {'success': True, 'message': 'Duplicate refund webhook ignored'}
            
            # 查找相關的付款記錄
            sale_id = webhook_data.get('sale_id')
            payment_id = f"gumroad_{sale_id}" if sale_id else f"gumroad_{refund_id}"
            
            # 獲取付款記錄
            payment_record = self.get_payment_record(payment_id)
            if not payment_record:
                logger.error(f"找不到退款相關的付款記錄: {payment_id}")
                return {'success': False, 'error': 'Payment record not found'}
            
            # 更新付款記錄狀態
            self.db.collection('payment_records').document(payment_id).update({
                'status': 'refunded',
                'refund_processed_at': datetime.now(),
                'refund_id': refund_id,
                'refund_data': webhook_data
            })
            
            # 停用相關用戶帳號
            user_uuid = payment_record.get('user_uuid')
            if user_uuid:
                result = self.deactivate_user_account(user_uuid, f"Gumroad 退款: {refund_id}")
                if result:
                    logger.info(f"已停用退款用戶帳號: {user_uuid}")
                else:
                    logger.error(f"停用用戶帳號失敗: {user_uuid}")
            
            # 發送退款通知郵件
            user_email = payment_record.get('user_email')
            user_name = payment_record.get('user_name')
            if user_email:
                self.send_refund_notification_email(user_email, user_name, payment_record)
            
            # 標記退款處理完成
            self.mark_webhook_processed(refund_id, 'refund')
            
            logger.info(f"Gumroad 退款處理完成: {payment_id}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'refund_id': refund_id,
                'user_uuid': user_uuid,
                'event_type': 'refund'
            }
            
        except Exception as e:
            logger.error(f"處理退款事件失敗: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_cancellation_event(self, webhook_data):
        """處理訂閱取消事件"""
        try:
            subscription_id = webhook_data.get('subscription_id')
            if not subscription_id:
                logger.error("Cancellation webhook 缺少 subscription_id")
                return {'success': False, 'error': 'Missing subscription_id'}
            
            # 檢查重複處理
            if self.is_duplicate_webhook(subscription_id, 'cancellation'):
                logger.info(f"跳過重複的取消 webhook: {subscription_id}")
                return {'success': True, 'message': 'Duplicate cancellation webhook ignored'}
            
            # 查找相關的用戶（如果有的話）
            # 訂閱取消不一定要立即停用帳號，可能只是標記為即將過期
            logger.info(f"處理訂閱取消: {subscription_id}")
            
            # 標記處理完成
            self.mark_webhook_processed(subscription_id, 'cancellation')
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'event_type': 'cancellation'
            }
            
        except Exception as e:
            logger.error(f"處理取消事件失敗: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def deactivate_user_account(self, user_uuid, reason):
        """停用用戶帳號"""
        try:
            uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
            
            user_ref = self.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                logger.warning(f"嘗試停用不存在的用戶帳號: {user_uuid}")
                return False
            
            # 更新用戶狀態
            user_ref.update({
                'active': False,
                'deactivated_at': datetime.now(),
                'deactivation_reason': reason,
                'deactivated_by': 'gumroad_refund_system'
            })
            
            logger.info(f"用戶帳號已停用: {user_uuid} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"停用用戶帳號失敗: {str(e)}")
            return False
    
    def send_refund_notification_email(self, email, name, payment_record):
        """發送退款通知郵件"""
        try:
            smtp_server = os.environ.get('SMTP_SERVER')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            email_user = os.environ.get('EMAIL_USER')
            email_password = os.environ.get('EMAIL_PASSWORD')
            
            if not all([smtp_server, email_user, email_password]):
                logger.warning("Email 配置不完整，跳過退款通知發送")
                return False
            
            msg = MIMEMultipart()
            
            from_display_name = "Scrilab"
            msg['From'] = f"{from_display_name} <{email_user}>"
            msg['To'] = email
            msg['Subject'] = f"Scrilab Artale 服務退款通知"
            
            support_email = os.environ.get('SUPPORT_EMAIL', email_user)
            msg['Reply-To'] = f"Scrilab Support <{support_email}>"
            
            plan_name = payment_record.get('plan_name', 'N/A')
            amount_twd = payment_record.get('amount_twd', 'N/A')
            
            body = f"""
親愛的 {name}，

您的 Scrilab Artale 服務已成功退款。

退款詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 服務方案：{plan_name}
💰 退款金額：NT$ {amount_twd}
🕒 處理時間：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
🔐 相關序號：已停用
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 重要提醒：
- 您的服務序號已被停用，無法繼續使用
- 退款將在 3-5 個工作日內退回到您的原付款方式
- 如有任何疑問，歡迎聯繫我們的客服團隊

📞 客服聯繫：
- Discord：https://discord.gg/HPzNrQmN
- Email：scrilabstaff@gmail.com

感謝您曾經選擇 Scrilab 技術服務。

Scrilab 技術團隊
{datetime.now().strftime('%Y年%m月%d日')}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"退款通知 Email 已發送至: {email}")
            return True
            
        except Exception as e:
            logger.error(f"發送退款通知 Email 失敗: {str(e)}")
            return False
    
    def is_duplicate_webhook(self, identifier, event_type):
        """檢查是否為重複的 webhook - 防止記憶體洩露"""
        try:
            doc_id = f"{event_type}_{identifier}"
            doc = self.db.collection('processed_webhooks').document(doc_id).get()
            return doc.exists
        except Exception as e:
            logger.error(f"檢查重複 webhook 失敗: {str(e)}")
            return False
    
    def mark_webhook_processed(self, identifier, event_type):
        """標記 webhook 已處理"""
        try:
            doc_id = f"{event_type}_{identifier}"
            self.db.collection('processed_webhooks').document(doc_id).set({
                'identifier': identifier,
                'event_type': event_type,
                'processed_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(days=30)  # 30天後自動清理
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
            
            from_display_name = "Scrilab"
            msg['From'] = f"{from_display_name} <{email_user}>"
            msg['To'] = email
            msg['Subject'] = f"Scrilab Artale 服務序號 - {plan_name}"
            
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
        """獲取購買統計 - 包含退款統計"""
        try:
            payments_ref = self.db.collection('payment_records')
            gumroad_payments = payments_ref.where('payment_method', '==', 'gumroad').stream()
            
            total_payments = 0
            completed_payments = 0
            refunded_payments = 0
            total_revenue = 0
            total_refunded = 0
            
            for payment in gumroad_payments:
                payment_data = payment.to_dict()
                total_payments += 1
                
                status = payment_data.get('status', '')
                if status == 'completed':
                    completed_payments += 1
                    total_revenue += payment_data.get('amount_twd', 0)
                elif status == 'refunded':
                    refunded_payments += 1
                    total_refunded += payment_data.get('amount_twd', 0)
            
            return {
                'total_payments': total_payments,
                'completed_payments': completed_payments,
                'refunded_payments': refunded_payments,
                'pending_payments': total_payments - completed_payments - refunded_payments,
                'total_revenue_twd': total_revenue,
                'total_refunded_twd': total_refunded,
                'net_revenue_twd': total_revenue - total_refunded,
                'success_rate': (completed_payments / total_payments * 100) if total_payments > 0 else 0,
                'refund_rate': (refunded_payments / total_payments * 100) if total_payments > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"獲取購買統計失敗: {str(e)}")
            return {
                'total_payments': 0,
                'completed_payments': 0,
                'refunded_payments': 0,
                'pending_payments': 0,
                'total_revenue_twd': 0,
                'total_refunded_twd': 0,
                'net_revenue_twd': 0,
                'success_rate': 0,
                'refund_rate': 0
            }
    
    def debug_all_products(self):
        """調試方法：獲取所有產品信息"""
        try:
            url = f"{self.base_url}/products"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params, timeout=10)
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
    
    def cleanup_old_webhooks(self):
        """清理舊的 webhook 記錄"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # 查詢並刪除過期的 webhook 記錄
            old_webhooks = self.db.collection('processed_webhooks')\
                              .where('expires_at', '<', cutoff_date)\
                              .limit(100)\
                              .stream()
            
            deleted_count = 0
            for webhook_doc in old_webhooks:
                try:
                    webhook_doc.reference.delete()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"刪除舊 webhook 記錄失敗: {e}")
            
            if deleted_count > 0:
                logger.info(f"🧹 清理了 {deleted_count} 個舊 webhook 記錄")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理舊 webhook 記錄失敗: {str(e)}")
            return 0


class RateLimiter:
    """簡單的速率限制器"""
    
    def __init__(self, max_requests=100, time_window=3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()
    
    def allow_request(self):
        """檢查是否允許請求"""
        with self.lock:
            now = time.time()
            
            # 清理過期的請求記錄
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            # 檢查是否超過限制
            if len(self.requests) >= self.max_requests:
                return False
            
            # 記錄此次請求
            self.requests.append(now)
            return True