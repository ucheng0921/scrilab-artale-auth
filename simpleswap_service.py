# simpleswap_service.py - 修復地址驗證問題的版本
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
    """SimpleSwap Fiat-to-Crypto 服務 - 修復地址驗證問題"""
    
    def __init__(self, db):
        self.db = db
        self.api_base_url = "https://api.simpleswap.io"
        self.api_key = os.environ.get('SIMPLESWAP_API_KEY')
        
        if not self.api_key:
            logger.error("❌ SIMPLESWAP_API_KEY 環境變數未設置")
            raise ValueError("SimpleSwap API Key is required")
        
        logger.info("✅ SimpleSwap Fiat-to-Crypto Service 初始化完成")

    def get_valid_address_for_currency(self, currency: str) -> str:
        """獲取指定貨幣的有效地址"""
        # 預設的有效地址映射
        default_addresses = {
            'usdt': 'TQXf7bBjJzCMCCJP4uxNhLjXVc8YBxo9yL',  # USDT TRC20 地址
            'usdttrc20': 'TQXf7bBjJzCMCCJP4uxNhLjXVc8YBxo9yL',  # USDT TRC20
            'usdterc20': '0x742d35Cc6635C0532925a3b8D0A4E5a8f3e0e5d8',  # USDT ERC20
            'btc': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',  # Bitcoin 地址
            'eth': '0x742d35Cc6635C0532925a3b8D0A4E5a8f3e0e5d8',  # Ethereum 地址
            'trx': 'TQXf7bBjJzCMCCJP4uxNhLjXVc8YBxo9yL'  # TRON 地址
        }
        
        # 從環境變數獲取自定義地址
        env_key = f'{currency.upper()}_WALLET_ADDRESS'
        custom_address = os.environ.get(env_key)
        
        if custom_address:
            logger.info(f"使用自定義地址 {currency}: {custom_address}")
            return custom_address
        
        # 使用預設地址
        address = default_addresses.get(currency.lower(), default_addresses['usdt'])
        logger.info(f"使用預設地址 {currency}: {address}")
        return address

    def create_fiat_to_crypto_exchange(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建法幣到加密貨幣交換 - 正確的 Fiat API 實現"""
        try:
            order_id = f"fiat_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            amount_twd = plan_info['price']
            amount_usd = amount_twd * 0.032
            
            logger.info(f"開始創建 SimpleSwap Fiat-to-Crypto 交換 - Plan: {plan_info['name']}, USD: {amount_usd}")
            
            # 對於 fiat 交換，不需要 address_to，且會重定向到 Guardarian
            exchange_data = {
                'currency_from': 'usd',  # 法幣
                'currency_to': 'usdt',   # 目標加密貨幣
                'amount': amount_usd,
                'fixed': False
                # 注意：fiat 交換不需要 address_to, extra_id_to 等參數
            }
            
            logger.info(f"創建 Fiat 交換請求: {exchange_data}")
            
            response = requests.post(
                f"{self.api_base_url}/create_exchange",
                params={'api_key': self.api_key},
                json=exchange_data,
                timeout=30
            )
            
            logger.info(f"API 回應狀態: {response.status_code}")
            logger.info(f"API 回應內容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ SimpleSwap Fiat 交換創建成功: {result}")
                
                if 'id' in result:
                    exchange_id = result['id']
                    estimated_crypto = amount_usd * 0.9505  # 扣除 4.95% 手續費
                    
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
                        'estimated_crypto': estimated_crypto,
                        'crypto_currency': 'USDT',
                        'currency_from': 'usd',
                        'currency_to': 'usdt',
                        'status': 'waiting_payment',
                        'created_at': datetime.now(),
                        'payment_method': 'fiat_to_crypto',
                        'expires_at': datetime.now() + timedelta(hours=2),
                        'payment_type': 'credit_card',
                        'is_fiat_exchange': True,
                        'simpleswap_data': result
                    }
                    
                    self.save_exchange_record(exchange_id, exchange_record)
                    
                    # 尋找 Guardarian 連結
                    payment_url = None
                    for url_field in ['guardarian_url', 'redirect_url', 'payment_url', 'url']:
                        if result.get(url_field):
                            payment_url = result[url_field]
                            logger.info(f"找到 Guardarian 付款 URL: {payment_url}")
                            break
                    
                    # 如果沒有找到連結，可能需要檢查 API Key 類型
                    if not payment_url:
                        logger.warning("未找到 Guardarian 連結，請檢查是否使用 Fiat API Key")
                        return {'success': False, 'error': '請確認您的 API Key 支援 Fiat 交換功能'}
                    
                    return {
                        'success': True,
                        'exchange_id': exchange_id,
                        'order_id': order_id,
                        'payment_url': payment_url,
                        'amount_usd': amount_usd,
                        'amount_twd': amount_twd,
                        'amount_fiat': amount_usd,
                        'fiat_currency': 'USD',
                        'estimated_crypto': estimated_crypto,
                        'crypto_currency': 'USDT',
                        'expires_at': exchange_record['expires_at'].isoformat(),
                        'payment_method': 'credit_card',
                        'is_fiat_exchange': True,
                        'fee_info': '4.95% (Mercuryo 3.95% + SimpleSwap 1%)'
                    }
                else:
                    logger.error(f"API 回應中沒有 exchange ID: {result}")
                    return {'success': False, 'error': '交換創建失敗：回應格式錯誤'}
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"API 請求失敗: {response.status_code} - {error_data}")
                return {'success': False, 'error': f'API 錯誤：{error_data.get("description", "未知錯誤")}'}
                
        except Exception as e:
            logger.error(f"創建 Fiat-to-Crypto 交換失敗: {str(e)}", exc_info=True)
            return {'success': False, 'error': '系統錯誤，請稍後再試'}

    def select_best_usdt_currency(self, currencies) -> str:
        """選擇最佳的 USDT 貨幣"""
        if not currencies:
            return 'usdt'
        
        # 優先級列表
        usdt_priorities = ['usdttrc20', 'usdt', 'usdterc20', 'usdtbep20']
        
        available_currencies = [c.get('symbol', '').lower() for c in currencies]
        
        for preferred in usdt_priorities:
            if preferred in available_currencies:
                logger.info(f"選擇 USDT 貨幣: {preferred}")
                return preferred
        
        # 如果沒有找到，使用第一個包含 usdt 的貨幣
        for currency in currencies:
            symbol = currency.get('symbol', '').lower()
            if 'usdt' in symbol:
                logger.info(f"選擇備用 USDT 貨幣: {symbol}")
                return symbol
        
        # 最後回退
        logger.warning("未找到合適的 USDT 貨幣，使用預設")
        return 'usdt'

    def get_estimate(self, currency_from: str, currency_to: str, amount: float) -> Optional[Dict]:
        """獲取交換估算"""
        try:
            params = {
                'api_key': self.api_key,
                'fixed': 'false',
                'currency_from': currency_from,
                'currency_to': currency_to,
                'amount': amount
            }
            
            response = requests.get(
                f"{self.api_base_url}/get_estimated",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.debug(f"估算失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.debug(f"估算錯誤: {str(e)}")
            return None

    def process_successful_exchange_creation(self, result: Dict, order_id: str, plan_info: Dict, 
                                           user_info: Dict, amount_twd: float, amount_usd: float, 
                                           target_currency: str) -> Dict:
        """處理成功的交換創建"""
        exchange_id = result['id']
        estimated_crypto = amount_usd * 0.9505  # 扣除手續費
        
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
            'estimated_crypto': estimated_crypto,
            'crypto_currency': target_currency.upper(),
            'currency_from': result.get('currency_from', 'usd'),
            'currency_to': result.get('currency_to', target_currency),
            'status': 'waiting_payment',
            'created_at': datetime.now(),
            'payment_method': 'fiat_to_crypto',
            'receiving_address': result.get('address_to'),
            'payment_address': result.get('address_from'),
            'expires_at': datetime.now() + timedelta(hours=2),
            'payment_type': 'credit_card',
            'is_fiat_exchange': True,
            'simpleswap_data': result
        }
        
        self.save_exchange_record(exchange_id, exchange_record)
        
        # 檢查是否有外部付款 URL
        payment_url = self.extract_payment_url(result, exchange_id)
        
        return {
            'success': True,
            'exchange_id': exchange_id,
            'order_id': order_id,
            'payment_url': payment_url,
            'amount_usd': amount_usd,
            'amount_twd': amount_twd,
            'amount_fiat': amount_usd,
            'fiat_currency': 'USD',
            'estimated_crypto': estimated_crypto,
            'crypto_currency': target_currency.upper(),
            'expires_at': exchange_record['expires_at'].isoformat(),
            'payment_method': 'credit_card',
            'is_fiat_exchange': True,
            'fee_info': '4.95% (Mercuryo 3.95% + SimpleSwap 1%)'
        }

    def extract_payment_url(self, result: Dict, exchange_id: str) -> str:
        """提取付款 URL"""
        # 檢查各種可能的 URL 欄位
        for url_field in ['mercuryo_url', 'redirect_url', 'payment_url', 'guardarian_url', 'url']:
            if result.get(url_field):
                logger.info(f"找到付款 URL ({url_field}): {result[url_field]}")
                return result[url_field]
        
        # 如果沒有找到外部付款 URL，使用我們的信用卡頁面
        base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
        payment_url = f"{base_url}/payment/credit-card/{exchange_id}"
        logger.info(f"使用內部信用卡頁面: {payment_url}")
        return payment_url

    def create_mock_exchange(self, order_id: str, plan_info: Dict, user_info: Dict, 
                           amount_twd: float, amount_usd: float) -> Dict:
        """創建模擬交換（當 API 不可用時）"""
        try:
            # 生成模擬的 exchange_id
            exchange_id = f"mock_{uuid_lib.uuid4().hex[:12]}"
            estimated_crypto = amount_usd * 0.95  # 假設 5% 手續費
            
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
                'estimated_crypto': estimated_crypto,
                'crypto_currency': 'USDT',
                'currency_from': 'usd',
                'currency_to': 'usdt',
                'status': 'waiting_payment',
                'created_at': datetime.now(),
                'payment_method': 'fiat_to_crypto_mock',
                'receiving_address': 'TQXf7bBjJzCMCCJP4uxNhLjXVc8YBxo9yL',
                'expires_at': datetime.now() + timedelta(hours=2),
                'payment_type': 'credit_card',
                'is_fiat_exchange': True,
                'is_mock': True
            }
            
            self.save_exchange_record(exchange_id, exchange_record)
            
            # 使用我們的信用卡頁面
            base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
            payment_url = f"{base_url}/payment/credit-card/{exchange_id}"
            
            logger.info(f"✅ 模擬交換創建成功: {exchange_id}")
            
            return {
                'success': True,
                'exchange_id': exchange_id,
                'order_id': order_id,
                'payment_url': payment_url,
                'amount_usd': amount_usd,
                'amount_twd': amount_twd,
                'amount_fiat': amount_usd,
                'fiat_currency': 'USD',
                'estimated_crypto': estimated_crypto,
                'crypto_currency': 'USDT',
                'expires_at': exchange_record['expires_at'].isoformat(),
                'payment_method': 'credit_card',
                'is_fiat_exchange': True,
                'is_mock': True,
                'fee_info': 'Mock Exchange - 5% fee'
            }
            
        except Exception as e:
            logger.error(f"創建模擬交換失敗: {str(e)}")
            return {'success': False, 'error': '系統錯誤，請稍後再試'}
    
    def get_supported_currencies(self):
        """獲取支援的貨幣列表"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_all_currencies",
                params={'api_key': self.api_key},
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"獲取貨幣列表失敗: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"獲取貨幣列表錯誤: {str(e)}")
            return None
    
    def get_exchange_status(self, exchange_id: str) -> Optional[Dict]:
        """獲取交換狀態"""
        try:
            # 檢查是否為模擬交換
            exchange_record = self.get_exchange_record(exchange_id)
            if exchange_record and exchange_record.get('is_mock'):
                # 模擬交換，返回模擬狀態
                return {
                    'id': exchange_id,
                    'status': 'waiting',
                    'type': 'mock'
                }
            
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
            logger.info(f"交換狀態已更新: {exchange_id} -> {status}")
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
                logger.info(f"交換狀態更新: {exchange_id} -> {status}")
                self.update_exchange_status(exchange_id, status)
                return True, None
                
        except Exception as e:
            logger.error(f"處理 Webhook 失敗: {str(e)}")
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
            msg['From'] = f"Scrilab <{email_user}>"
            msg['To'] = email
            msg['Subject'] = f"Scrilab Artale 服務序號 - {plan_name}"
            
            body = f"""
親愛的 {name}，

感謝您使用信用卡購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
💳 付款方式：信用卡 (SimpleSwap + Mercuryo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 如何使用：
1. 下載 Scrilab Artale 客戶端
2. 在登入界面輸入您的專屬序號
3. 開始享受專業的遊戲技術服務

📞 技術支援：
- Discord：https://discord.gg/HPzNrQmN
- Email：scrilabstaff@gmail.com

感謝您的信任！

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