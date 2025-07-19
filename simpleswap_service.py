# simpleswap_service.py - SimpleSwap 真正的信用卡到加密貨幣整合
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

class SimpleSwapService:
    """SimpleSwap 真正的信用卡到加密貨幣服務"""
    
    def __init__(self, db):
        self.db = db
        self.api_base_url = "https://api.simpleswap.io"
        self.api_key = os.environ.get('SIMPLESWAP_API_KEY')
        self.partner_id = os.environ.get('SIMPLESWAP_PARTNER_ID')
        
        if not self.api_key:
            logger.error("❌ SIMPLESWAP_API_KEY 環境變數未設置")
            raise ValueError("SimpleSwap API Key is required")
        
        logger.info("✅ SimpleSwap Service 初始化完成")
    
    def get_supported_fiat_currencies(self) -> Optional[list]:
        """獲取支援的法定貨幣"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_currencies",
                params={
                    'api_key': self.api_key,
                    'fiat': 'true'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                currencies = response.json()
                logger.info(f"支援的法定貨幣: {currencies}")
                return currencies
            else:
                logger.error(f"獲取法定貨幣失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"獲取支援法定貨幣錯誤: {str(e)}")
            return None
    
    def get_exchange_estimate(self, from_currency: str, to_currency: str, amount: float) -> Optional[Dict]:
        """獲取匯率估算"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_estimated",
                params={
                    'api_key': self.api_key,
                    'fixed': 'false',
                    'currency_from': from_currency,
                    'currency_to': to_currency,
                    'amount': amount
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"匯率估算: {amount} {from_currency} ≈ {result} {to_currency}")
                return {
                    'estimated_amount': float(result),
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'original_amount': amount
                }
            else:
                logger.error(f"獲取匯率估算失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"獲取匯率估算錯誤: {str(e)}")
            return None
    
    def create_fiat_exchange(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建法定貨幣到加密貨幣交換"""
        try:
            # 生成唯一的訂單ID
            order_id = f"artale_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 設定交換參數
            from_currency = "usd"  # 使用 USD 作為法定貨幣
            to_currency = "usdttrc20"  # 接收 USDT (TRC20)
            amount = plan_info['price'] * 0.032  # TWD 轉 USD 概算
            
            # 獲取匯率估算
            estimate = self.get_exchange_estimate(from_currency, to_currency, amount)
            if not estimate:
                logger.error("無法獲取匯率估算")
                return None
            
            # 生成收款地址（你的錢包地址）
            receiving_address = os.environ.get('RECEIVING_WALLET_ADDRESS', 'YOUR_USDT_TRC20_ADDRESS')
            
            # 創建交換訂單
            exchange_data = {
                'api_key': self.api_key,
                'fixed': 'false',
                'currency_from': from_currency,
                'currency_to': to_currency,
                'amount': amount,
                'address_to': receiving_address,
                'extra_id_to': '',
                'user_refund_address': '',
                'user_refund_extra_id': ''
            }
            
            if self.partner_id:
                exchange_data['partner_id'] = self.partner_id
            
            response = requests.post(
                f"{self.api_base_url}/create_exchange",
                data=exchange_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"SimpleSwap 交換創建成功: {result}")
                
                # 檢查是否成功
                if 'id' in result:
                    # 保存交換記錄
                    exchange_record = {
                        'exchange_id': result['id'],
                        'order_id': order_id,
                        'user_name': user_info['name'],
                        'user_email': user_info['email'],
                        'plan_id': plan_info['id'],
                        'plan_name': plan_info['name'],
                        'plan_period': plan_info['period'],
                        'amount_twd': plan_info['price'],
                        'amount_usd': amount,
                        'estimated_usdt': estimate['estimated_amount'],
                        'from_currency': from_currency,
                        'to_currency': to_currency,
                        'status': 'waiting',
                        'created_at': datetime.now(),
                        'payment_method': 'simpleswap_fiat',
                        'receiving_address': receiving_address,
                        'expires_at': datetime.now() + timedelta(minutes=30)
                    }
                    
                    # 添加 SimpleSwap 返回的重要信息
                    if 'address_from' in result:
                        exchange_record['payment_address'] = result['address_from']
                    if 'amount_to' in result:
                        exchange_record['expected_amount'] = result['amount_to']
                    
                    self.save_exchange_record(result['id'], exchange_record)
                    
                    # 創建法定貨幣付款連結
                    payment_url = self.create_fiat_payment_url(result['id'], amount, from_currency, user_info)
                    
                    return {
                        'success': True,
                        'exchange_id': result['id'],
                        'order_id': order_id,
                        'payment_url': payment_url,
                        'amount_usd': amount,
                        'estimated_usdt': estimate['estimated_amount'],
                        'expires_at': exchange_record['expires_at'].isoformat()
                    }
                else:
                    logger.error(f"SimpleSwap 交換創建失敗: {result}")
                    return None
            else:
                logger.error(f"SimpleSwap API 請求失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"創建 SimpleSwap 法定貨幣交換失敗: {str(e)}", exc_info=True)
            return None
    
    def create_fiat_payment_url(self, exchange_id: str, amount: float, currency: str, user_info: Dict) -> str:
        """創建法定貨幣付款 URL（通過 Mercuryo）"""
        try:
            base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
            
            # SimpleSwap 與 Mercuryo 整合的付款 URL
            # 這個 URL 會引導用戶到真正的信用卡付款頁面
            payment_url = f"https://widget.simpleswap.io/?apiKey={self.api_key}&id={exchange_id}&theme=dark&returnUrl={base_url}/payment/simpleswap/success&cancelUrl={base_url}/payment/cancel"
            
            logger.info(f"生成法定貨幣付款 URL: {payment_url}")
            return payment_url
            
        except Exception as e:
            logger.error(f"創建法定貨幣付款 URL 失敗: {str(e)}")
            return f"https://simpleswap.io/exchange/{exchange_id}"
    
    def get_exchange_status(self, exchange_id: str) -> Optional[Dict]:
        """獲取交換狀態"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_exchange",
                params={
                    'api_key': self.api_key,
                    'id': exchange_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"交換狀態查詢: {result}")
                return result
            else:
                logger.error(f"獲取交換狀態失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"獲取交換狀態錯誤: {str(e)}")
            return None
    
    def handle_webhook(self, webhook_data: Dict) -> Tuple[bool, Optional[str]]:
        """處理 SimpleSwap Webhook"""
        try:
            logger.info(f"收到 SimpleSwap Webhook: {webhook_data}")
            
            exchange_id = webhook_data.get('id')
            status = webhook_data.get('status')
            
            if not exchange_id:
                logger.error("Webhook 中缺少 exchange_id")
                return False, None
            
            # 獲取交換記錄
            exchange_record = self.get_exchange_record(exchange_id)
            if not exchange_record:
                logger.error(f"找不到交換記錄: {exchange_id}")
                return False, None
            
            # 更新交換狀態
            if status == 'finished':
                return self.process_successful_exchange(exchange_id, webhook_data)
            elif status in ['confirming', 'exchanging']:
                self.update_exchange_status(exchange_id, 'processing')
                return True, None
            elif status == 'failed':
                self.update_exchange_status(exchange_id, 'failed')
                return True, None
            else:
                logger.info(f"交換狀態更新: {exchange_id} -> {status}")
                self.update_exchange_status(exchange_id, status)
                return True, None
                
        except Exception as e:
            logger.error(f"處理 Webhook 失敗: {str(e)}")
            return False, None
    
    def process_successful_exchange(self, exchange_id: str, webhook_data: Dict) -> Tuple[bool, Optional[str]]:
        """處理成功的交換"""
        try:
            # 更新交換狀態
            self.update_exchange_status(exchange_id, 'completed')
            
            # 生成用戶帳號
            user_uuid = self.create_user_account(exchange_id)
            
            if user_uuid:
                # 發送 Email
                exchange_record = self.get_exchange_record(exchange_id)
                if exchange_record:
                    self.send_license_email(
                        exchange_record['user_email'],
                        exchange_record['user_name'],
                        user_uuid,
                        exchange_record['plan_name'],
                        exchange_record['plan_period']
                    )
                
                logger.info(f"✅ SimpleSwap 交換處理完成: {exchange_id}, 用戶序號: {user_uuid}")
                return True, user_uuid
            else:
                logger.error(f"❌ 創建用戶帳號失敗: {exchange_id}")
                return False, None
                
        except Exception as e:
            logger.error(f"處理成功交換失敗: {str(e)}")
            return False, None
    
    def save_exchange_record(self, exchange_id: str, exchange_data: Dict):
        """保存交換記錄"""
        try:
            self.db.collection('simpleswap_exchanges').document(exchange_id).set(exchange_data)
            logger.info(f"SimpleSwap 交換記錄已保存: {exchange_id}")
        except Exception as e:
            logger.error(f"保存交換記錄失敗: {str(e)}")
    
    def update_exchange_status(self, exchange_id: str, status: str):
        """更新交換狀態"""
        try:
            self.db.collection('simpleswap_exchanges').document(exchange_id).update({
                'status': status,
                'updated_at': datetime.now()
            })
            logger.info(f"SimpleSwap 交換狀態已更新: {exchange_id} -> {status}")
        except Exception as e:
            logger.error(f"更新交換狀態失敗: {str(e)}")
    
    def get_exchange_record(self, exchange_id: str) -> Optional[Dict]:
        """獲取交換記錄"""
        try:
            doc = self.db.collection('simpleswap_exchanges').document(exchange_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"獲取交換記錄失敗: {str(e)}")
            return None
    
    def create_user_account(self, exchange_id: str) -> Optional[str]:
        """根據交換記錄創建用戶帳號"""
        try:
            exchange_record = self.get_exchange_record(exchange_id)
            if not exchange_record:
                return None
            
            # 生成唯一的 UUID
            user_uuid = f"artale_swap_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"
            uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
            
            # 確定有效期
            plan_periods = {
                'trial_7': 7,
                'monthly_30': 30,
                'quarterly_90': 90
            }
            
            days = plan_periods.get(exchange_record['plan_id'], 30)
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            
            # 創建用戶
            user_data = {
                "original_uuid": user_uuid,
                "display_name": exchange_record['user_name'],
                "permissions": {
                    "script_access": True,
                    "config_modify": True
                },
                "active": True,
                "created_at": datetime.now(),
                "created_by": "simpleswap_fiat_exchange",
                "login_count": 0,
                "expires_at": expires_at,
                "exchange_id": exchange_id,
                "payment_method": "simpleswap_fiat",
                "payment_status": "completed",
                "notes": f"SimpleSwap 法定貨幣交換創建 - {exchange_record['plan_name']}"
            }
            
            self.db.collection('authorized_users').document(uuid_hash).set(user_data)
            
            # 更新交換記錄
            self.db.collection('simpleswap_exchanges').document(exchange_id).update({
                'user_uuid': user_uuid,
                'user_created': True,
                'user_created_at': datetime.now()
            })
            
            logger.info(f"SimpleSwap 用戶帳號已創建: {user_uuid}")
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
💳 付款方式：SimpleSwap 信用卡付款
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
            
            logger.info(f"SimpleSwap 序號 Email 已發送至: {email}")
            return True
            
        except Exception as e:
            logger.error(f"發送 Email 失敗: {str(e)}")
            return False