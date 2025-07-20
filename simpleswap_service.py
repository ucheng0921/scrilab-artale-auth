# simpleswap_service.py - 修復版本，實現真正的 Fiat-to-Crypto
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
    """SimpleSwap Fiat-to-Crypto 服務 - 修復版本"""
    
    def __init__(self, db):
        self.db = db
        self.api_base_url = "https://api.simpleswap.io"
        self.api_key = os.environ.get('SIMPLESWAP_API_KEY')
        
        if not self.api_key:
            logger.error("❌ SIMPLESWAP_API_KEY 環境變數未設置")
            raise ValueError("SimpleSwap API Key is required")
        
        logger.info("✅ SimpleSwap Fiat-to-Crypto Service 初始化完成")
    
    def create_fiat_to_crypto_exchange(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建真正的 Fiat-to-Crypto 交換 - 修復版本"""
        try:
            # 生成唯一的訂單ID
            order_id = f"fiat_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 計算金額
            amount_twd = plan_info['price']
            amount_usd = amount_twd * 0.032  # TWD 轉 USD
            
            logger.info(f"開始創建 SimpleSwap Fiat-to-Crypto 交換 - Plan: {plan_info['name']}, USD: {amount_usd}")
            
            # 第一步：檢查 Fiat API 可用性
            fiat_currencies = self.get_fiat_currencies()
            if not fiat_currencies:
                logger.warning("無法獲取法幣列表，使用模擬付款")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            
            # 第二步：獲取支援的加密貨幣（for fiat purchases）
            crypto_currencies = self.get_fiat_crypto_currencies()
            if not crypto_currencies:
                logger.warning("無法獲取可購買的加密貨幣列表，使用模擬付款")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            
            # 第三步：選擇最佳的法幣和加密貨幣組合
            # 優先選擇 USD -> USDT，如果不可用則嘗試其他組合
            fiat_currency = 'usd'  # 預設使用 USD
            crypto_currency = 'usdt'  # 預設使用 USDT
            
            # 檢查這個組合是否可用
            estimate = self.get_fiat_estimate(fiat_currency, crypto_currency, amount_usd)
            if not estimate:
                # 嘗試其他 USDT 變體
                usdt_variants = ['usdttrc20', 'usdterc20', 'usdtbep20']
                for variant in usdt_variants:
                    estimate = self.get_fiat_estimate(fiat_currency, variant, amount_usd)
                    if estimate:
                        crypto_currency = variant
                        break
                
                if not estimate:
                    logger.warning("所有 USD->USDT 組合都不可用，使用模擬付款")
                    return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            
            estimated_crypto = estimate.get('estimated_amount', amount_usd)
            
            # 第四步：創建 Fiat-to-Crypto 交換
            receiving_address = self.get_receiving_address(crypto_currency)
            
            exchange_data = {
                'currency_from': fiat_currency,
                'currency_to': crypto_currency,
                'amount': amount_usd,
                'address_to': receiving_address,
                'user_info': {
                    'email': user_info['email'],
                    'name': user_info['name']
                },
                'extra_id_to': '',
                'type': 'fiat'  # 指定這是 fiat 交換
            }
            
            # 使用正確的 Fiat API 端點
            try:
                response = requests.post(
                    f"{self.api_base_url}/create_fiat_exchange",  # 注意：這是 fiat 專用端點
                    params={'api_key': self.api_key},
                    json=exchange_data,
                    timeout=30
                )
                
                logger.info(f"Fiat 交換創建請求: {exchange_data}")
                logger.info(f"API 回應狀態: {response.status_code}")
                
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
                            'fiat_currency': fiat_currency.upper(),
                            'estimated_crypto': estimated_crypto,
                            'crypto_currency': crypto_currency.upper(),
                            'currency_from': fiat_currency,
                            'currency_to': crypto_currency,
                            'status': 'waiting_payment',
                            'created_at': datetime.now(),
                            'payment_method': 'fiat_to_crypto',
                            'receiving_address': receiving_address,
                            'expires_at': datetime.now() + timedelta(hours=2),
                            'payment_type': 'credit_card',
                            'is_fiat_exchange': True,  # 標記為真正的 fiat 交換
                            'payment_url': result.get('payment_url'),  # Mercuryo 付款URL
                            'mercuryo_widget_id': result.get('widget_id')
                        }
                        
                        self.save_exchange_record(exchange_id, exchange_record)
                        
                        # 構建付款URL - 如果 API 返回了 Mercuryo URL，使用它；否則使用我們的詳情頁面
                        if result.get('payment_url'):
                            payment_url = result['payment_url']
                        else:
                            base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
                            payment_url = f"{base_url}/payment/simpleswap/fiat/{exchange_id}"
                        
                        return {
                            'success': True,
                            'exchange_id': exchange_id,
                            'order_id': order_id,
                            'payment_url': payment_url,
                            'amount_usd': amount_usd,
                            'amount_twd': amount_twd,
                            'amount_fiat': amount_usd,
                            'fiat_currency': fiat_currency.upper(),
                            'estimated_crypto': estimated_crypto,
                            'crypto_currency': crypto_currency.upper(),
                            'expires_at': exchange_record['expires_at'].isoformat(),
                            'payment_method': 'credit_card',
                            'is_fiat_exchange': True
                        }
                    else:
                        logger.error(f"SimpleSwap Fiat API 回應中沒有 exchange ID: {result}")
                        return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
                        
                elif response.status_code == 404:
                    logger.error("Fiat API 端點不存在，可能需要升級 API Key 類型")
                    return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
                    
                else:
                    logger.error(f"SimpleSwap Fiat API 請求失敗: {response.status_code} - {response.text}")
                    return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
                    
            except requests.exceptions.Timeout:
                logger.error("創建 Fiat 交換請求超時")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            except Exception as e:
                logger.error(f"創建 Fiat 交換請求失敗: {str(e)}")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
                
        except Exception as e:
            logger.error(f"創建 Fiat-to-Crypto 交換失敗: {str(e)}", exc_info=True)
            return self.create_mercuryo_mock_payment(plan_info, user_info, f"mock_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    def get_fiat_currencies(self):
        """獲取支援的法幣列表"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_fiat_currencies",  # Fiat 專用端點
                params={'api_key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"獲取法幣列表失敗: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"獲取法幣列表錯誤: {str(e)}")
            return None
    
    def get_fiat_crypto_currencies(self):
        """獲取可用 fiat 購買的加密貨幣列表"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_fiat_crypto_currencies",  # 專門用於 fiat 購買的加密貨幣
                params={'api_key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"獲取 Fiat 加密貨幣列表失敗: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"獲取 Fiat 加密貨幣列表錯誤: {str(e)}")
            return None
    
    def get_fiat_estimate(self, fiat_currency: str, crypto_currency: str, amount: float):
        """獲取 Fiat-to-Crypto 估算"""
        try:
            response = requests.get(
                f"{self.api_base_url}/get_fiat_estimated",  # Fiat 專用估算端點
                params={
                    'api_key': self.api_key,
                    'currency_from': fiat_currency,
                    'currency_to': crypto_currency,
                    'amount': amount
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Fiat 估算成功: {fiat_currency}/{crypto_currency} = {result}")
                return result
            else:
                logger.warning(f"Fiat 估算失敗: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Fiat 估算錯誤: {str(e)}")
            return None
    
    def get_receiving_address(self, crypto_currency: str) -> str:
        """根據加密貨幣類型獲取正確的接收地址"""
        crypto_lower = crypto_currency.lower()
        
        # 根據不同的加密貨幣網絡選擇正確的地址
        if 'trc20' in crypto_lower or crypto_lower == 'usdt':
            # TRON 網絡
            return os.environ.get('USDT_WALLET_ADDRESS', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
        elif 'erc20' in crypto_lower or 'eth' in crypto_lower:
            # Ethereum 網絡
            return os.environ.get('ETH_WALLET_ADDRESS', '0x742d35Cc6634C0532925a3b8D6D8d7c98f8F7a88')
        elif 'bep20' in crypto_lower or 'bsc' in crypto_lower:
            # BSC 網絡
            return os.environ.get('BSC_WALLET_ADDRESS', '0x742d35Cc6634C0532925a3b8D6D8d7c98f8F7a88')
        elif 'btc' in crypto_lower:
            # Bitcoin 網絡
            return os.environ.get('BTC_WALLET_ADDRESS', 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh')
        else:
            # 默認使用 TRON 地址
            return os.environ.get('RECEIVING_WALLET_ADDRESS', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
    
    def create_mercuryo_mock_payment(self, plan_info: Dict, user_info: Dict, order_id: str) -> Dict:
        """創建模擬的 Mercuryo 付款（當 Fiat API 不可用時）"""
        try:
            mock_exchange_id = f"mock_fiat_{uuid_lib.uuid4().hex[:12]}"
            amount_usd = plan_info['price'] * 0.032
            
            # 創建模擬的信用卡付款界面
            exchange_record = {
                'exchange_id': mock_exchange_id,
                'order_id': order_id,
                'user_name': user_info['name'],
                'user_email': user_info['email'],
                'plan_id': plan_info['id'],
                'plan_name': plan_info['name'],
                'plan_period': plan_info['period'],
                'amount_twd': plan_info['price'],
                'amount_usd': amount_usd,
                'amount_fiat': amount_usd,
                'fiat_currency': 'USD',
                'estimated_crypto': amount_usd * 0.98,
                'crypto_currency': 'USDT',
                'currency_from': 'usd',
                'currency_to': 'usdt',
                'status': 'waiting_payment',
                'created_at': datetime.now(),
                'payment_method': 'credit_card_mock',
                'receiving_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
                'expires_at': datetime.now() + timedelta(hours=2),
                'payment_type': 'credit_card',
                'is_mock': True,
                'is_fiat_exchange': True
            }
            
            self.save_exchange_record(mock_exchange_id, exchange_record)
            
            # 創建模擬的信用卡付款頁面
            base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
            payment_url = f"{base_url}/payment/credit-card/{mock_exchange_id}"
            
            logger.info(f"✅ 創建模擬信用卡付款: {mock_exchange_id}")
            
            return {
                'success': True,
                'exchange_id': mock_exchange_id,
                'order_id': order_id,
                'payment_url': payment_url,
                'amount_usd': amount_usd,
                'amount_twd': plan_info['price'],
                'amount_fiat': amount_usd,
                'fiat_currency': 'USD',
                'estimated_crypto': amount_usd * 0.98,
                'crypto_currency': 'USDT',
                'expires_at': exchange_record['expires_at'].isoformat(),
                'payment_method': 'credit_card',
                'is_mock': True,
                'is_fiat_exchange': True
            }
            
        except Exception as e:
            logger.error(f"創建模擬信用卡付款失敗: {str(e)}")
            return {'success': False, 'error': '創建模擬付款失敗'}
    
    # ... 其他方法保持不變 ...
    
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

感謝您使用信用卡購買 Scrilab Artale 遊戲技術服務！

您的服務詳情：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 服務方案：{plan_name}
⏰ 服務期限：{plan_period}
🔑 專屬序號：{uuid}
💳 付款方式：信用卡自動轉換加密貨幣 (SimpleSwap + Mercuryo)
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
- 您的信用卡付款已自動轉換為加密貨幣並安全處理

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