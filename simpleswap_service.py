# simpleswap_service.py - 正確的 Fiat API 實現
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
    """SimpleSwap Fiat-to-Crypto 服務 - 正確實現版本"""
    
    def __init__(self, db):
        self.db = db
        self.api_base_url = "https://api.simpleswap.io"
        self.api_key = os.environ.get('SIMPLESWAP_API_KEY')
        
        if not self.api_key:
            logger.error("❌ SIMPLESWAP_API_KEY 環境變數未設置")
            raise ValueError("SimpleSwap API Key is required")
        
        logger.info("✅ SimpleSwap Fiat-to-Crypto Service 初始化完成")
    
    def test_api_connection(self):
        """測試 API 連接"""
        try:
            test_response = requests.get(
                f"{self.api_base_url}/get_all_currencies",
                params={'api_key': self.api_key},
                timeout=10
            )
            
            logger.info(f"API 連接測試: {test_response.status_code}")
            
            if test_response.status_code == 200:
                try:
                    currencies = test_response.json()
                    logger.info(f"✅ API 連接成功，獲取到 {len(currencies)} 個貨幣")
                    return True, currencies
                except Exception as e:
                    logger.error(f"解析 API 回應失敗: {e}")
                    return False, None
            else:
                logger.error(f"❌ API 連接失敗: {test_response.status_code} - {test_response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ API 連接測試異常: {str(e)}")
            return False, None
    
    def get_supported_currencies(self):
        """獲取支援的貨幣列表"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_all_currencies",
                params={'api_key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"獲取貨幣列表失敗: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"獲取貨幣列表錯誤: {str(e)}")
            return None

    def create_fiat_to_crypto_exchange(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建真正的 Fiat-to-Crypto 交換 - 使用正確的 API"""
        try:
            order_id = f"fiat_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            amount_twd = plan_info['price']
            amount_usd = amount_twd * 0.032
            
            logger.info(f"開始創建 SimpleSwap Fiat-to-Crypto 交換 - Plan: {plan_info['name']}, USD: {amount_usd}")
            
            # 第一步：測試 API 連接
            api_working, currencies = self.test_api_connection()
            if not api_working:
                logger.error("API 連接失敗")
                return {'success': False, 'error': 'API 連接失敗'}
            
            # 第二步：獲取法幣估算
            # 根據文檔，對於法幣交換，from_currency 使用法幣代碼，to_currency 使用加密貨幣
            estimate_response = self.get_fiat_estimate('usd', 'usdt', amount_usd)
            if not estimate_response:
                logger.error("無法獲取 USD->USDT 估算，嘗試其他組合")
                # 嘗試其他 USDT 變體
                for crypto in ['usdttrc20', 'usdterc20', 'usdtbep20']:
                    estimate_response = self.get_fiat_estimate('usd', crypto, amount_usd)
                    if estimate_response:
                        break
                
                if not estimate_response:
                    logger.error("所有法幣組合都不可用")
                    return {'success': False, 'error': '當前無法處理法幣付款'}
            
            # 第三步：創建真正的 Fiat 交換
            # 使用標準的 create_exchange 端點，但使用法幣參數
            receiving_address = os.environ.get('USDT_WALLET_ADDRESS', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
            
            exchange_data = {
                'currency_from': 'usd',  # 法幣代碼
                'currency_to': 'usdt',    # 加密貨幣代碼
                'amount': amount_usd,
                'address_to': receiving_address,
                'fixed': False,
                'extra_id_to': '',
                'user_refund_address': '',
                'user_refund_extra_id': ''
            }
            
            response = requests.post(
                f"{self.api_base_url}/create_exchange",  # 使用標準端點
                params={'api_key': self.api_key},
                json=exchange_data,
                timeout=30
            )
            
            logger.info(f"Fiat 交換創建請求: {exchange_data}")
            logger.info(f"API 回應狀態: {response.status_code}")
            logger.info(f"API 回應內容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ SimpleSwap Fiat 交換創建成功: {result}")
                
                if 'id' in result:
                    exchange_id = result['id']
                    
                    # 保存交換記錄
                    exchange_record = {
                        'exchange_id': exchange_id,
                        'order_id': order_id,
                        'user_name': user_info['name'],
                        'user_email': user_info['email'],
                        'plan_id': plan_info['id'],
                        'plan_name': plan_info['name'],
                        'plan_period': plan_info['period'],
                        'amount_twd': amount_twd,
                        'amount_usd': amount_usd,
                        'amount_fiat': amount_usd,
                        'fiat_currency': 'USD',
                        'estimated_crypto': float(estimate_response),
                        'crypto_currency': 'USDT',
                        'currency_from': 'usd',
                        'currency_to': 'usdt',
                        'status': 'waiting_payment',
                        'created_at': datetime.now(),
                        'payment_method': 'fiat_to_crypto',
                        'receiving_address': receiving_address,
                        'expires_at': datetime.now() + timedelta(hours=2),
                        'payment_type': 'credit_card',
                        'is_fiat_exchange': True,
                        'payment_address': result.get('address_from'),  # SimpleSwap 提供的付款地址
                        'guardarian_url': result.get('guardarian_url'),  # Guardarian 付款 URL
                        'redirect_url': result.get('redirect_url')  # 重定向 URL
                    }
                    
                    self.save_exchange_record(exchange_id, exchange_record)
                    
                    # 構建付款URL
                    # 根據文檔，如果是 fiat 交換，API 會返回 Guardarian 的鏈接
                    if result.get('guardarian_url'):
                        payment_url = result['guardarian_url']
                    elif result.get('redirect_url'):
                        payment_url = result['redirect_url']
                    else:
                        # 使用我們的信用卡付款頁面
                        base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
                        payment_url = f"{base_url}/payment/credit-card/{exchange_id}"
                    
                    return {
                        'success': True,
                        'exchange_id': exchange_id,
                        'order_id': order_id,
                        'payment_url': payment_url,
                        'amount_usd': amount_usd,
                        'amount_twd': amount_twd,
                        'amount_fiat': amount_usd,
                        'fiat_currency': 'USD',
                        'estimated_crypto': float(estimate_response),
                        'crypto_currency': 'USDT',
                        'expires_at': exchange_record['expires_at'].isoformat(),
                        'payment_method': 'credit_card',
                        'is_fiat_exchange': True
                    }
                else:
                    logger.error(f"SimpleSwap API 回應中沒有 exchange ID: {result}")
                    return {'success': False, 'error': 'API 回應格式錯誤'}
                    
            elif response.status_code == 422:
                logger.error(f"SimpleSwap API 參數錯誤: {response.text}")
                return {'success': False, 'error': 'API 參數錯誤，可能不支援此法幣組合'}
                
            elif response.status_code == 401:
                logger.error("API Key 無效或沒有 Fiat 權限")
                return {'success': False, 'error': 'API Key 無效或沒有 Fiat 權限'}
                
            else:
                logger.error(f"SimpleSwap API 請求失敗: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'API 請求失敗: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"創建 Fiat-to-Crypto 交換失敗: {str(e)}", exc_info=True)
            return {'success': False, 'error': '系統錯誤'}
    
    def get_fiat_estimate(self, fiat_currency: str, crypto_currency: str, amount: float):
        """獲取 Fiat-to-Crypto 估算"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_estimated",
                params={
                    'api_key': self.api_key,
                    'currency_from': fiat_currency,
                    'currency_to': crypto_currency,
                    'amount': amount,
                    'fixed': 'false'
                },
                timeout=30
            )
            
            logger.info(f"估算請求: {fiat_currency}/{crypto_currency}, 金額: {amount}")
            logger.info(f"估算回應: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                try:
                    result_text = response.text.strip().strip('"')
                    if result_text and result_text != 'null':
                        estimated_amount = float(result_text)
                        logger.info(f"✅ Fiat 估算成功: {fiat_currency}/{crypto_currency} = {estimated_amount}")
                        return estimated_amount
                    else:
                        logger.warning(f"估算結果為空: {response.text}")
                        return None
                except (ValueError, TypeError) as e:
                    logger.error(f"解析估算結果失敗: {response.text} - {e}")
                    return None
            else:
                logger.warning(f"Fiat 估算失敗: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Fiat 估算錯誤: {str(e)}")
            return None
    
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
                logger.error(f"獲取交換狀態失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"獲取交換狀態錯誤: {str(e)}")
            return None
    
    def save_exchange_record(self, exchange_id: str, exchange_data: Dict):
        """保存交換記錄"""
        try:
            self.db.collection('fiat_crypto_exchanges').document(exchange_id).set(exchange_data)
            logger.info(f"Fiat-to-Crypto 交換記錄已保存: {exchange_id}")
        except Exception as e:
            logger.error(f"保存交換記錄失敗: {str(e)}")
    
    def get_exchange_record(self, exchange_id: str) -> Optional[Dict]:
        """獲取交換記錄"""
        try:
            doc = self.db.collection('fiat_crypto_exchanges').document(exchange_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"獲取交換記錄失敗: {str(e)}")
            return None
    
    def update_exchange_status(self, exchange_id: str, status: str):
        """更新交換狀態"""
        try:
            self.db.collection('fiat_crypto_exchanges').document(exchange_id).update({
                'status': status,
                'updated_at': datetime.now()
            })
            logger.info(f"Fiat-to-Crypto 交換狀態已更新: {exchange_id} -> {status}")
        except Exception as e:
            logger.error(f"更新交換狀態失敗: {str(e)}")
    
    def handle_webhook(self, webhook_data: Dict) -> Tuple[bool, Optional[str]]:
        """處理 Webhook"""
        try:
            logger.info(f"收到 Fiat-to-Crypto Webhook: {webhook_data}")
            
            exchange_id = webhook_data.get('id')
            status = webhook_data.get('status')
            
            if not exchange_id:
                logger.error("Webhook 中缺少 exchange_id")
                return False, None
            
            exchange_record = self.get_exchange_record(exchange_id)
            if not exchange_record:
                logger.error(f"找不到交換記錄: {exchange_id}")
                return False, None
            
            if status == 'finished' or status == 'completed':
                return self.process_successful_fiat_exchange(exchange_id, webhook_data)
            elif status in ['confirming', 'processing', 'paid']:
                self.update_exchange_status(exchange_id, 'processing')
                return True, None
            elif status == 'failed':
                self.update_exchange_status(exchange_id, 'failed')
                return True, None
            else:
                logger.info(f"Fiat 交換狀態更新: {exchange_id} -> {status}")
                self.update_exchange_status(exchange_id, status)
                return True, None
                
        except Exception as e:
            logger.error(f"處理 Fiat Webhook 失敗: {str(e)}")
            return False, None
    
    def process_successful_fiat_exchange(self, exchange_id: str, webhook_data: Dict) -> Tuple[bool, Optional[str]]:
        """處理成功的 Fiat-to-Crypto 交換"""
        try:
            self.update_exchange_status(exchange_id, 'completed')
            user_uuid = self.create_user_account(exchange_id)
            
            if user_uuid:
                exchange_record = self.get_exchange_record(exchange_id)
                if exchange_record:
                    self.send_license_email(
                        exchange_record['user_email'],
                        exchange_record['user_name'],
                        user_uuid,
                        exchange_record['plan_name'],
                        exchange_record['plan_period']
                    )
                
                logger.info(f"✅ Fiat-to-Crypto 交換處理完成: {exchange_id}, 用戶序號: {user_uuid}")
                return True, user_uuid
            else:
                logger.error(f"❌ 創建用戶帳號失敗: {exchange_id}")
                return False, None
                
        except Exception as e:
            logger.error(f"處理成功 Fiat 交換失敗: {str(e)}")
            return False, None
    
    def create_user_account(self, exchange_id: str) -> Optional[str]:
        """根據交換記錄創建用戶帳號"""
        try:
            exchange_record = self.get_exchange_record(exchange_id)
            if not exchange_record:
                return None
            
            user_uuid = f"artale_fiat_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d')}"
            uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
            
            plan_periods = {'trial_7': 7, 'monthly_30': 30, 'quarterly_90': 90}
            days = plan_periods.get(exchange_record['plan_id'], 30)
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            
            user_data = {
                "original_uuid": user_uuid,
                "display_name": exchange_record['user_name'],
                "permissions": {"script_access": True, "config_modify": True},
                "active": True,
                "created_at": datetime.now(),
                "created_by": "fiat_to_crypto_exchange",
                "login_count": 0,
                "expires_at": expires_at,
                "exchange_id": exchange_id,
                "payment_method": "credit_card_to_crypto",
                "payment_status": "completed",
                "notes": f"信用卡付款創建 - {exchange_record['plan_name']} (Fiat-to-Crypto)"
            }
            
            self.db.collection('authorized_users').document(uuid_hash).set(user_data)
            self.db.collection('fiat_crypto_exchanges').document(exchange_id).update({
                'user_uuid': user_uuid,
                'user_created': True,
                'user_created_at': datetime.now()
            })
            
            logger.info(f"Fiat-to-Crypto 用戶帳號已創建: {user_uuid}")
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
            from_display_name = "Scrilab"
            msg['From'] = f"{from_display_name} <{email_user}>"
            msg['To'] = email
            msg['Subject'] = f"Scrilab Artale 服務序號 - {plan_name}"
            
            support_email = os.environ.get('SUPPORT_EMAIL', email_user)
            msg['Reply-To'] = f"Scrilab Support <{support_email}>"
            
            body = f"""
親愛的 {name}，

感謝您使用信用卡購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
💳 付款方式：信用卡 (SimpleSwap + Guardarian)
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
- 您的信用卡付款已通過 SimpleSwap 安全處理

再次感謝您選擇信用卡付款方式！

Scrilab 技術團隊
{datetime.now().strftime('%Y年%m月%d日')}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Fiat-to-Crypto 序號 Email 已發送至: {email}")
            return True
            
        except Exception as e:
            logger.error(f"發送 Email 失敗: {str(e)}")
            return False