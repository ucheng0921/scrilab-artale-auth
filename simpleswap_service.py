# simpleswap_service.py - 修正 API 端點版本
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
    """SimpleSwap Fiat-to-Crypto 服務 - 修正 API 端點"""
    
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
            # 測試基本 API 連接
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
            elif test_response.status_code == 401:
                logger.error("❌ API Key 無效或未授權")
                return False, None
            else:
                logger.error(f"❌ API 連接失敗: {test_response.status_code} - {test_response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ API 連接測試異常: {str(e)}")
            return False, None
    
    def create_fiat_to_crypto_exchange(self, plan_info: Dict, user_info: Dict) -> Optional[Dict]:
        """創建 Fiat-to-Crypto 交換（信用卡 → USDT）- 修正版"""
        try:
            # 生成唯一的訂單ID
            order_id = f"fiat_{uuid_lib.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 計算金額
            amount_twd = plan_info['price']
            amount_usd = amount_twd * 0.032  # TWD 轉 USD
            
            logger.info(f"開始創建 SimpleSwap 交換 - Plan: {plan_info['name']}, USD: {amount_usd}")
            
            # 先測試 API 連接
            api_working, currencies = self.test_api_connection()
            
            if not api_working:
                logger.warning("API 連接失敗，使用模擬付款")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            
            # 查找可用的 USDT 貨幣
            usdt_currencies = []
            if currencies:
                usdt_currencies = [c for c in currencies if 'usdt' in c.get('symbol', '').lower()]
                logger.info(f"找到 USDT 相關貨幣: {[c.get('symbol') for c in usdt_currencies[:5]]}")
            
            # 嘗試不同的貨幣組合（基於實際可用貨幣）
            currency_pairs = [
                ('eur', 'usdt'),  # EUR to USDT
                ('usd', 'usdt'),   # USD to USDT
            ]
            
            # 如果找到了具體的 USDT 變體，添加到測試列表
            if usdt_currencies:
                for usdt_currency in usdt_currencies[:3]:
                    symbol = usdt_currency.get('symbol', '').lower()
                    currency_pairs.extend([
                        ('eur', symbol),
                        ('usd', symbol)
                    ])
            
            successful_pair = None
            estimated_crypto = amount_usd  # 默認值
            
            for from_currency, to_currency in currency_pairs:
                try:
                    # 調整金額（如果是 EUR，轉換匯率）
                    if from_currency == 'eur':
                        fiat_amount = amount_usd * 0.85  # USD to EUR 大概匯率
                    else:
                        fiat_amount = amount_usd
                    
                    # 獲取估算 - 使用正確的端點
                    estimate_params = {
                        'api_key': self.api_key,
                        'fixed': 'false',
                        'currency_from': from_currency,
                        'currency_to': to_currency,
                        'amount': fiat_amount
                    }
                    
                    estimate_response = requests.get(
                        f"{self.api_base_url}/get_estimated",
                        params=estimate_params,
                        timeout=30
                    )
                    
                    logger.info(f"測試貨幣對 {from_currency}/{to_currency}: {estimate_response.status_code}")
                    
                    if estimate_response.status_code == 200:
                        try:
                            estimated_crypto = float(estimate_response.text.strip())
                            successful_pair = (from_currency, to_currency, fiat_amount)
                            logger.info(f"✅ 找到可用貨幣對: {from_currency}/{to_currency}, 估算: {estimated_crypto}")
                            break
                        except ValueError as e:
                            logger.warning(f"無法解析估算結果: {estimate_response.text}")
                            continue
                    elif estimate_response.status_code == 422:
                        logger.info(f"貨幣對 {from_currency}/{to_currency} 不支援")
                        continue
                    else:
                        logger.warning(f"估算請求失敗: {estimate_response.status_code}")
                        continue
                    
                except Exception as e:
                    logger.warning(f"測試貨幣對 {from_currency}/{to_currency} 失敗: {e}")
                    continue
            
            if not successful_pair:
                logger.warning("所有貨幣對都不可用，使用模擬付款")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            
            from_currency, to_currency, fiat_amount = successful_pair
            
            # 你的收款地址（根據幣種選擇）
            if 'btc' in to_currency.lower():
                receiving_address = os.environ.get('BTC_WALLET_ADDRESS', 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh')
            else:
                receiving_address = os.environ.get('RECEIVING_WALLET_ADDRESS', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
            
            # 創建交換請求
            exchange_data = {
                'currency_from': from_currency,
                'currency_to': to_currency,
                'amount': fiat_amount,
                'address_to': receiving_address,
                'fixed': False,
                'extra_id_to': '',
                'user_refund_address': '',
                'user_refund_extra_id': ''
            }
            
            # 創建交換
            response = requests.post(
                f"{self.api_base_url}/create_exchange",
                params={'api_key': self.api_key},
                json=exchange_data,
                timeout=30
            )
            
            logger.info(f"創建交換請求: {exchange_data}")
            logger.info(f"API 回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ SimpleSwap 交換創建成功: {result}")
                
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
                        'amount_fiat': fiat_amount,
                        'fiat_currency': from_currency.upper(),
                        'estimated_crypto': estimated_crypto,
                        'crypto_currency': to_currency.upper(),
                        'currency_from': from_currency,
                        'currency_to': to_currency,
                        'status': 'waiting_payment',
                        'created_at': datetime.now(),
                        'payment_method': 'fiat_to_crypto',
                        'receiving_address': receiving_address,
                        'expires_at': datetime.now() + timedelta(hours=2),
                        'payment_type': 'credit_card'
                    }
                    
                    # 如果 API 返回了付款地址或 URL
                    if 'address_from' in result:
                        exchange_record['payment_address'] = result['address_from']
                    if 'payment_url' in result:
                        exchange_record['payment_url'] = result['payment_url']
                    
                    self.save_exchange_record(exchange_id, exchange_record)
                    
                    # 決定付款 URL
                    base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
                    
                    if 'payment_url' in result:
                        payment_url = result['payment_url']
                    elif from_currency in ['eur', 'usd']:
                        # Fiat 付款，重定向到 Mercuryo
                        payment_url = f"https://widget.mercuryo.io/?type=buy&currency={to_currency.upper()}&amount={estimated_crypto}&address={receiving_address}&theme=dark"
                    else:
                        # 加密貨幣付款，使用我們的詳情頁面
                        payment_url = f"{base_url}/payment/simpleswap/details/{exchange_id}"
                    
                    return {
                        'success': True,
                        'exchange_id': exchange_id,
                        'order_id': order_id,
                        'payment_url': payment_url,
                        'amount_usd': amount_usd,
                        'amount_twd': amount_twd,
                        'amount_fiat': fiat_amount,
                        'fiat_currency': from_currency.upper(),
                        'estimated_crypto': estimated_crypto,
                        'crypto_currency': to_currency.upper(),
                        'expires_at': exchange_record['expires_at'].isoformat(),
                        'payment_method': 'credit_card_to_crypto'
                    }
                else:
                    logger.error(f"SimpleSwap 回應中沒有 exchange ID: {result}")
                    return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
            else:
                logger.error(f"SimpleSwap API 請求失敗: {response.status_code} - {response.text}")
                return self.create_mercuryo_mock_payment(plan_info, user_info, order_id)
                
        except Exception as e:
            logger.error(f"創建 Fiat-to-Crypto 交換失敗: {str(e)}", exc_info=True)
            return self.create_mercuryo_mock_payment(plan_info, user_info, f"mock_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    # 其他方法保持不變...
    def create_mercuryo_mock_payment(self, plan_info: Dict, user_info: Dict, order_id: str) -> Dict:
        """創建模擬的 Mercuryo 付款（當 API 不可用時）"""
        try:
            mock_exchange_id = f"mock_fiat_{uuid_lib.uuid4().hex[:12]}"
            amount_usd = plan_info['price'] * 0.032
            amount_eur = amount_usd * 0.85  # USD to EUR
            
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
                'amount_usd': amount_usd,
                'amount_fiat': amount_eur,
                'fiat_currency': 'EUR',
                'estimated_crypto': amount_usd * 0.98,
                'crypto_currency': 'USDT',
                'currency_from': 'eur',
                'currency_to': 'usdt',
                'status': 'waiting_payment',
                'created_at': datetime.now(),
                'payment_method': 'fiat_to_crypto_mock',
                'receiving_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
                'expires_at': datetime.now() + timedelta(hours=2),
                'payment_type': 'credit_card',
                'is_mock': True
            }
            
            self.save_exchange_record(mock_exchange_id, exchange_record)
            
            # 創建模擬的 Mercuryo 付款頁面 URL
            base_url = os.environ.get('BASE_URL', 'https://scrilab.onrender.com')
            payment_url = f"{base_url}/payment/mercuryo/mock/{mock_exchange_id}"
            
            logger.info(f"✅ 創建模擬 Mercuryo 付款: {mock_exchange_id}")
            
            return {
                'success': True,
                'exchange_id': mock_exchange_id,
                'order_id': order_id,
                'payment_url': payment_url,
                'amount_usd': amount_usd,
                'amount_twd': plan_info['price'],
                'amount_fiat': amount_eur,
                'fiat_currency': 'EUR',
                'estimated_crypto': amount_usd * 0.98,
                'crypto_currency': 'USDT',
                'expires_at': exchange_record['expires_at'].isoformat(),
                'payment_method': 'credit_card_to_crypto',
                'is_mock': True
            }
            
        except Exception as e:
            logger.error(f"創建模擬 Mercuryo 付款失敗: {str(e)}")
            return {'success': False, 'error': '創建模擬付款失敗'}
    
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