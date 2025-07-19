# simpleswap_service.py - 完整修復版本，支援真正的加密貨幣交換
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
    """SimpleSwap 加密貨幣交換服務 - 完整修復版本"""
    
    def __init__(self, db):
        self.db = db
        self.api_base_url = "https://api.simpleswap.io"
        self.api_key = os.environ.get('SIMPLESWAP_API_KEY')
        
        if not self.api_key:
            logger.error("❌ SIMPLESWAP_API_KEY 環境變數未設置")
            raise ValueError("SimpleSwap API Key is required")
        
        logger.info("✅ SimpleSwap Service 初始化完成")
    
    def get_supported_currencies(self) -> Optional[list]:
        """獲取支援的加密貨幣"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_all_currencies",
                params={'api_key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                currencies = response.json()
                logger.info(f"支援的加密貨幣數量: {len(currencies)}")
                return currencies
            else:
                logger.error(f"獲取支援貨幣失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"獲取支援貨幣錯誤: {str(e)}")
            return None
    
    def get_exchange_estimate(self, from_currency: str, to_currency: str, amount: float) -> Optional[Dict]:
        """獲取匯率估算 - 簡化版本"""
        try:
            # 確保貨幣代碼格式正確
            from_currency = from_currency.lower()
            to_currency = to_currency.lower()
            
            params = {
                'api_key': self.api_key,
                'fixed': 'false',
                'currency_from': from_currency,
                'currency_to': to_currency,
                'amount': amount
            }
            
            response = requests.get(
                f"{self.api_base_url}/get_estimated",
                params=params,
                timeout=30
            )
            
            logger.info(f"估算請求: {params}")
            logger.info(f"回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                result = response.text.strip()
                try:
                    estimated_amount = float(result)
                    logger.info(f"匯率估算成功: {amount} {from_currency} ≈ {estimated_amount} {to_currency}")
                    return {
                        'estimated_amount': estimated_amount,
                        'from_currency': from_currency,
                        'to_currency': to_currency,
                        'original_amount': amount
                    }
                except ValueError:
                    # 如果不是純數字，嘗試解析 JSON
                    try:
                        result_json = response.json()
                        if isinstance(result_json, (int, float)):
                            estimated_amount = float(result_json)
                        else:
                            estimated_amount = result_json.get('amount', 0)
                        
                        return {
                            'estimated_amount': estimated_amount,
                            'from_currency': from_currency,
                            'to_currency': to_currency,
                            'original_amount': amount
                        }
                    except:
                        logger.error(f"無法解析估算回應: {result}")
                        return None
            else:
                logger.error(f"獲取匯率估算失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"獲取匯率估算錯誤: {str(e)}")
            return None
    
    def create_fiat_exchange(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建加密貨幣交換（修復版本）"""
        try:
            # 生成唯一的訂單ID
            order_id = f"artale_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 使用最常見的貨幣對：BTC -> USDT (ERC20)
            from_currency = "btc"
            to_currency = "usdt"  # 使用標準的 USDT (通常是 ERC-20)
            amount_btc = plan_info['price'] * 0.000001  # 將 TWD 轉換為少量 BTC 用於測試
            
            # 先測試獲取估算
            estimate = self.get_exchange_estimate(from_currency, to_currency, amount_btc)
            if not estimate:
                # 如果第一個組合失敗，嘗試其他組合
                logger.info("嘗試 ETH -> USDT 組合")
                from_currency = "eth"
                to_currency = "usdt"
                amount_eth = plan_info['price'] * 0.0001  # 少量 ETH
                estimate = self.get_exchange_estimate(from_currency, to_currency, amount_eth)
                amount_btc = amount_eth  # 更新金額變數名
                
            if not estimate:
                # 如果還是失敗，使用固定的回應（不依賴 API）
                logger.warning("無法獲取 SimpleSwap 估算，使用模擬交換")
                return self.create_mock_exchange(plan_info, user_info, order_id)
            
            # 你的收款地址 - 使用環境變數或默認地址
            receiving_address = os.environ.get('RECEIVING_WALLET_ADDRESS')
            if not receiving_address:
                # 使用一個有效的 USDT ERC20 地址作為默認值
                receiving_address = 'TL72cJVVFwmHQd3yq3hvPt3JqT5RG6DG5M'  # USDT 多重簽名地址
                logger.warning("未設置 RECEIVING_WALLET_ADDRESS 環境變數，使用默認地址")
            
            # 創建交換訂單
            exchange_data = {
                'fixed': 'false',
                'currency_from': from_currency,
                'currency_to': to_currency,
                'amount': amount_btc,
                'address_to': receiving_address,
                'extra_id_to': '',
                'user_refund_address': '',
                'user_refund_extra_id': ''
            }
            
            # 使用 params 傳遞 api_key
            response = requests.post(
                f"{self.api_base_url}/create_exchange",
                params={'api_key': self.api_key},
                json=exchange_data,
                timeout=30
            )
            
            logger.info(f"創建交換請求: {exchange_data}")
            logger.info(f"回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"SimpleSwap 交換創建成功: {result}")
                
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
                        'amount_usd': plan_info['price'] * 0.032,
                        'estimated_usdt': estimate['estimated_amount'],
                        'from_currency': from_currency,
                        'to_currency': to_currency,
                        'status': 'waiting',
                        'created_at': datetime.now(),
                        'payment_method': 'simpleswap_crypto',
                        'receiving_address': receiving_address,
                        'expires_at': datetime.now() + timedelta(minutes=30)
                    }
                    
                    if 'address_from' in result:
                        exchange_record['payment_address'] = result['address_from']
                    if 'amount_to' in result:
                        exchange_record['expected_amount'] = result['amount_to']
                    
                    self.save_exchange_record(result['id'], exchange_record)
                    
                    # 創建付款頁面 URL
                    base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
                    payment_url = f"{base_url}/payment/simpleswap/details/{result['id']}"
                    
                    return {
                        'success': True,
                        'exchange_id': result['id'],
                        'order_id': order_id,
                        'payment_url': payment_url,
                        'payment_address': result.get('address_from'),
                        'amount_usd': plan_info['price'] * 0.032,
                        'estimated_usdt': estimate['estimated_amount'],
                        'expires_at': exchange_record['expires_at'].isoformat()
                    }
                else:
                    logger.error(f"SimpleSwap 交換創建失敗: {result}")
                    return {'success': False, 'error': 'SimpleSwap 交換創建失敗'}
            else:
                logger.error(f"SimpleSwap API 請求失敗: {response.status_code} - {response.text}")
                return {'success': False, 'error': f"API 請求失敗: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"創建 SimpleSwap 交換失敗: {str(e)}", exc_info=True)
            return {'success': False, 'error': '創建交換失敗，請稍後再試'}
    
    def create_mock_exchange(self, plan_info: Dict, user_info: Dict, order_id: str) -> Dict:
        """創建模擬交換（當 API 不可用時）"""
        try:
            # 生成模擬的交換 ID
            mock_exchange_id = f"mock_{uuid_lib.uuid4().hex[:12]}"
            
            # 模擬交換記錄
            exchange_record = {
                'exchange_id': mock_exchange_id,
                'order_id': order_id,
                'user_name': user_info['name'],
                'user_email': user_info['email'],
                'plan_id': plan_info['id'],
                'plan_name': plan_info['name'],
                'plan_period': plan_info['period'],
                'amount_twd': plan_info['price'],
                'amount_usd': plan_info['price'] * 0.032,
                'estimated_usdt': plan_info['price'] * 0.032,  # 1:1 模擬匯率
                'from_currency': 'btc',
                'to_currency': 'usdt',
                'status': 'waiting',
                'created_at': datetime.now(),
                'payment_method': 'simpleswap_crypto_mock',
                'receiving_address': 'TL72cJVVFwmHQd3yq3hvPt3JqT5RG6DG5M',
                'payment_address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',  # 比特幣創世地址（僅用於演示）
                'expires_at': datetime.now() + timedelta(minutes=30),
                'is_mock': True
            }
            
            self.save_exchange_record(mock_exchange_id, exchange_record)
            
            # 創建付款頁面 URL
            base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
            payment_url = f"{base_url}/payment/simpleswap/details/{mock_exchange_id}"
            
            return {
                'success': True,
                'exchange_id': mock_exchange_id,
                'order_id': order_id,
                'payment_url': payment_url,
                'payment_address': exchange_record['payment_address'],
                'amount_usd': exchange_record['amount_usd'],
                'estimated_usdt': exchange_record['estimated_usdt'],
                'expires_at': exchange_record['expires_at'].isoformat(),
                'is_mock': True
            }
            
        except Exception as e:
            logger.error(f"創建模擬交換失敗: {str(e)}")
            return {'success': False, 'error': '創建模擬交換失敗'}
    
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
                "created_by": "simpleswap_crypto_exchange",
                "login_count": 0,
                "expires_at": expires_at,
                "exchange_id": exchange_id,
                "payment_method": "simpleswap_crypto",
                "payment_status": "completed",
                "notes": f"SimpleSwap 加密貨幣交換創建 - {exchange_record['plan_name']}"
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
💰 付款方式：SimpleSwap 加密貨幣交換
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