"""
gumroad_routes.py - 修復版本
"""
from flask import Blueprint, request, jsonify, redirect, render_template_string
import logging
import json
import os
import time
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 創建藍圖
gumroad_bp = Blueprint('gumroad', __name__, url_prefix='/gumroad')

# 添加這個安全檢查類
class SimpleWebhookSecurity:
    def __init__(self, db, access_token):
        self.db = db
        self.access_token = access_token
        self.webhook_token = os.environ.get('WEBHOOK_SECRET_TOKEN')
        self.enable_security = os.environ.get('ENABLE_WEBHOOK_SECURITY', 'false').lower() == 'true'
        self.enable_sale_verification = os.environ.get('ENABLE_SALE_VERIFICATION', 'false').lower() == 'true'
        self.rate_limit_cache = {}
        
        logger.info(f"🔒 安全設置: Security={self.enable_security}, Verification={self.enable_sale_verification}")
    
    def verify_webhook_token(self, request):
        """檢查 URL 中的 token"""
        if not self.enable_security or not self.webhook_token:
            return True, "Security disabled"
        
        token = request.args.get('token')  # 從 URL ?token=xxx 獲取
        if not token or token != self.webhook_token:
            return False, "Invalid token"
        
        return True, "Token OK"
    
    def check_rate_limit(self, client_ip):
        """簡單速率限制"""
        if not self.enable_security:
            return True
        
        now = time.time()
        
        # 清理過期記錄
        if client_ip not in self.rate_limit_cache:
            self.rate_limit_cache[client_ip] = []
        
        # 保留最近5分鐘的請求
        self.rate_limit_cache[client_ip] = [t for t in self.rate_limit_cache[client_ip] if t > now - 300]
        
        # 檢查是否超過限制（5分鐘內最多10個請求）
        if len(self.rate_limit_cache[client_ip]) > 10:
            return False
        
        # 記錄這次請求
        self.rate_limit_cache[client_ip].append(now)
        return True
    
    def verify_sale(self, sale_data):
        """通過 API 驗證銷售真實性"""
        if not self.enable_sale_verification:
            return True, "Verification disabled"
        
        sale_id = sale_data.get('sale_id')
        if not sale_id:
            return False, "Missing sale_id"
        
        # 檢查是否重複處理
        try:
            doc = self.db.collection('processed_sales').document(sale_id).get()
            if doc.exists:
                return False, "Already processed"
        except:
            pass
        
        # 通過 Gumroad API 驗證
        try:
            url = f"https://api.gumroad.com/v2/sales/{sale_id}"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                api_data = response.json()
                if api_data.get('success'):
                    api_sale = api_data.get('sale', {})
                    
                    # 簡單驗證：email 是否匹配
                    webhook_email = sale_data.get('email', '').lower()
                    api_email = api_sale.get('email', '').lower()
                    
                    if webhook_email == api_email:
                        # 標記為已處理
                        try:
                            self.db.collection('processed_sales').document(sale_id).set({
                                'processed_at': datetime.now(),
                                'expires_at': datetime.now() + timedelta(days=30)
                            })
                        except:
                            pass
                        
                        logger.info(f"✅ 銷售驗證通過: {sale_id}")
                        return True, "Sale verified"
                    else:
                        logger.warning(f"❌ 銷售數據不匹配: {sale_id}")
                        return False, "Data mismatch"
            
            return False, "API verification failed"
                
        except Exception as e:
            logger.error(f"銷售驗證失敗: {str(e)}")
            return False, f"Verification error"

class GumroadRoutes:
    """Gumroad 路由處理器 - 修復版本"""
    
    def __init__(self, gumroad_service):
        self.gumroad_service = gumroad_service
        
        # 添加這一行：初始化安全檢查
        self.security = SimpleWebhookSecurity(
            gumroad_service.db, 
            os.environ.get('GUMROAD_ACCESS_TOKEN')
        )
        
        logger.info("✅ GumroadRoutes 已初始化（含安全防護）")
    
    def create_payment(self):
        """創建 Gumroad 付款 - 修復版本"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': '缺少請求數據'
                }), 400
            
            plan_id = data.get('plan_id')
            user_info = data.get('user_info', {})
            
            # 驗證必要欄位
            if not plan_id:
                return jsonify({
                    'success': False,
                    'error': '缺少方案 ID'
                }), 400
            
            if not user_info.get('name') or not user_info.get('email'):
                return jsonify({
                    'success': False,
                    'error': '缺少用戶姓名或郵箱'
                }), 400
            
            # 創建付款
            result = self.gumroad_service.create_purchase_url(plan_id, user_info)
            
            if result['success']:
                logger.info(f"Gumroad 付款創建成功: {result['payment_id']}")
                return jsonify({
                    'success': True,
                    'purchase_url': result['purchase_url'],
                    'payment_id': result['payment_id'],
                    'plan_name': result['plan']['name'],
                    'amount_twd': result['plan']['price_twd'],
                    'amount_usd': result['plan']['price_usd']
                })
            else:
                logger.error(f"Gumroad 付款創建失敗: {result['error']}")
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 500
                
        except Exception as e:
            logger.error(f"創建 Gumroad 付款錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤，請稍後再試'
            }), 500
    
    def webhook_handler(self):
        """安全版 webhook 處理"""
        try:
            # 獲取客戶端 IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip and ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            logger.info(f"📨 收到 webhook from {client_ip}")
            
            # 1. 檢查 token（從 URL ?token=xxx）
            token_ok, token_msg = self.security.verify_webhook_token(request)
            if not token_ok:
                logger.warning(f"❌ Token 驗證失敗: {token_msg}")
                return jsonify({'error': token_msg}), 401
            
            # 2. 速率限制
            if not self.security.check_rate_limit(client_ip):
                logger.warning(f"❌ 速率限制: {client_ip}")
                return jsonify({'error': 'Too many requests'}), 429
            
            # 3. 解析數據（原有的邏輯）
            content_type = request.headers.get('Content-Type', '').lower()
            
            if 'application/json' in content_type:
                webhook_data = request.get_json()
            elif 'application/x-www-form-urlencoded' in content_type:
                webhook_data = request.form.to_dict()
            else:
                try:
                    raw_data = request.get_data()
                    webhook_data = json.loads(raw_data.decode('utf-8'))
                except:
                    webhook_data = request.form.to_dict()
            
            if not webhook_data:
                logger.error("❌ 無法解析數據")
                return jsonify({'error': 'Invalid data'}), 400
            
            # 4. 銷售驗證（只對銷售事件）
            if webhook_data.get('sale_id'):
                sale_ok, sale_msg = self.security.verify_sale(webhook_data)
                if not sale_ok:
                    logger.warning(f"❌ 銷售驗證失敗: {sale_msg}")
                    return jsonify({'error': sale_msg}), 403
            
            logger.info("✅ 安全檢查通過")
            
            # 5. 使用原有的處理邏輯
            result = self.gumroad_service.process_webhook(webhook_data)
            
            if result['success']:
                logger.info(f"✅ Webhook 處理成功")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"❌ 處理失敗: {result['error']}")
                return jsonify({'error': result['error']}), 400
                
        except Exception as e:
            logger.error(f"❌ Webhook 錯誤: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def payment_success(self):
        """付款成功頁面"""
        try:
            payment_id = request.args.get('payment_id')
            sale_id = request.args.get('sale_id')
            
            # 如果有 sale_id，轉換為我們的 payment_id 格式
            if sale_id and not payment_id:
                payment_id = f"gumroad_{sale_id}"
            
            if not payment_id:
                return redirect('/products?error=missing_payment_id')
            
            # 獲取付款記錄
            payment_record = self.gumroad_service.get_payment_record(payment_id)
            
            if not payment_record:
                return redirect('/products?error=payment_not_found')
            
            # 檢查付款狀態
            if payment_record.get('status') != 'completed':
                return redirect('/products?error=payment_not_completed')
            
            user_uuid = payment_record.get('user_uuid')
            
            # 導入成功頁面模板
            from templates import PAYMENT_SUCCESS_TEMPLATE
            
            return render_template_string(
                PAYMENT_SUCCESS_TEMPLATE,
                payment_record=payment_record,
                user_uuid=user_uuid
            )
            
        except Exception as e:
            logger.error(f"付款成功頁面錯誤: {str(e)}")
            return redirect('/products?error=system_error')
    
    def check_payment_status(self):
        """檢查付款狀態"""
        try:
            data = request.get_json()
            payment_id = data.get('payment_id') if data else None
            
            if not payment_id:
                return jsonify({
                    'success': False,
                    'error': '缺少付款 ID'
                }), 400
            
            # 獲取付款記錄
            payment_record = self.gumroad_service.get_payment_record(payment_id)
            
            if not payment_record:
                return jsonify({
                    'success': False,
                    'error': '找不到付款記錄'
                }), 404
            
            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'status': payment_record.get('status'),
                'user_uuid': payment_record.get('user_uuid'),
                'plan_name': payment_record.get('plan_name'),
                'amount_twd': payment_record.get('amount_twd'),
                'created_at': payment_record.get('created_at').isoformat() if payment_record.get('created_at') else None
            })
            
        except Exception as e:
            logger.error(f"檢查付款狀態錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤'
            }), 500
    
    def get_purchase_stats(self):
        """獲取購買統計"""
        try:
            stats = self.gumroad_service.get_purchase_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"獲取購買統計錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤'
            }), 500
    
    def get_service_plans(self):
        """獲取服務方案列表"""
        try:
            plans = self.gumroad_service.get_service_plans()
            return jsonify({
                'success': True,
                'plans': plans
            })
            
        except Exception as e:
            logger.error(f"獲取服務方案錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤'
            }), 500
    
    def debug_products(self):
        """調試：獲取所有產品信息"""
        try:
            result = self.gumroad_service.debug_all_products()
            
            if result.get('success'):
                products = result.get('products', [])
                
                # 映射我們的產品 ID
                our_product_mapping = {
                    os.environ.get('GUMROAD_TRIAL_PRODUCT_ID'): 'trial_7',
                    os.environ.get('GUMROAD_MONTHLY_PRODUCT_ID'): 'monthly_30',
                    os.environ.get('GUMROAD_QUARTERLY_PRODUCT_ID'): 'quarterly_90'
                }
                
                matched_products = {}
                for product in products:
                    product_id = product.get('id')
                    if product_id in our_product_mapping:
                        plan_id = our_product_mapping[product_id]
                        matched_products[plan_id] = {
                            **product,
                            'plan_id': plan_id,
                            'purchase_url': product.get('short_url') or f"https://gumroad.com/l/{product_id}",
                            'env_product_id': product_id
                        }
                
                return jsonify({
                    'success': True,
                    'debug_info': {
                        'all_products': products,
                        'our_products': matched_products,
                        'total_products_found': len(products),
                        'our_products_matched': len(matched_products),
                        'environment_mapping': our_product_mapping
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'API 調用失敗',
                    'details': result.get('error')
                }), 500
                
        except Exception as e:
            logger.error(f"調試產品錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'調試失敗: {str(e)}'
            }), 500

# 全局路由處理器實例
gumroad_routes = None

def init_gumroad_routes(gumroad_service):
    """初始化 Gumroad 路由"""
    global gumroad_routes
    gumroad_routes = GumroadRoutes(gumroad_service)
    logger.info("✅ Gumroad 路由已初始化")

# 註冊路由端點
@gumroad_bp.route('/create-payment', methods=['POST'])
def create_payment():
    """創建 Gumroad 付款"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    return gumroad_routes.create_payment()

@gumroad_bp.route('/webhook', methods=['POST'])
def webhook():
    """Gumroad webhook 處理"""
    if not gumroad_routes:
        return jsonify({'error': 'Service not available'}), 503
    
    return gumroad_routes.webhook_handler()

@gumroad_bp.route('/success', methods=['GET'])
def payment_success():
    """付款成功頁面"""
    if not gumroad_routes:
        return redirect('/products?error=service_unavailable')
    
    return gumroad_routes.payment_success()

@gumroad_bp.route('/check-status', methods=['POST'])
def check_payment_status():
    """檢查付款狀態"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    return gumroad_routes.check_payment_status()

@gumroad_bp.route('/stats', methods=['GET'])
def purchase_stats():
    """獲取購買統計"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    return gumroad_routes.get_purchase_stats()

@gumroad_bp.route('/plans', methods=['GET'])
def service_plans():
    """獲取服務方案列表"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    return gumroad_routes.get_service_plans()

@gumroad_bp.route('/debug/products', methods=['GET'])
def debug_products():
    """調試：獲取產品信息"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    return gumroad_routes.debug_products()

@gumroad_bp.route('/test-webhook', methods=['POST'])
def test_webhook():
    """測試 webhook 端點"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    try:
        # 模擬測試數據
        test_data = {
            'sale_id': 'test_sale_123456',
            'product_id': os.environ.get('GUMROAD_TRIAL_PRODUCT_ID', 'test_product'),
            'email': 'test@example.com',
            'purchaser_name': 'Test User',
            'price': '500',  # 5.00 USD in cents
            'currency': 'usd',
            'seller_id': 'test_seller'
        }
        
        logger.info("處理測試 webhook")
        result = gumroad_routes.gumroad_service.process_webhook(test_data)
        
        return jsonify({
            'success': True,
            'message': 'Test webhook processed',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"測試 webhook 錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
