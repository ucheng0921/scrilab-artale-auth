"""
gumroad_routes.py - Gumroad 路由處理器
"""
from flask import Blueprint, request, jsonify, redirect, render_template_string
import logging
import json
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

# 創建藍圖
gumroad_bp = Blueprint('gumroad', __name__, url_prefix='/gumroad')

class GumroadRoutes:
    """Gumroad 路由處理器"""
    
    def __init__(self, gumroad_service):
        self.gumroad_service = gumroad_service
        logger.info("✅ GumroadRoutes 已初始化")
    
    def create_payment(self):
        """創建 Gumroad 付款"""
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
        """處理 Gumroad webhook"""
        try:
            # 獲取請求數據
            content_type = request.headers.get('Content-Type', '')
            
            if 'application/x-www-form-urlencoded' in content_type:
                # Gumroad 發送的是 form-urlencoded 格式
                payload = request.get_data(as_text=True)
                webhook_data = dict(parse_qs(payload, keep_blank_values=True))
                
                # 轉換為單值字典（去掉列表包裝）
                webhook_data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                              for k, v in webhook_data.items()}
            else:
                # 嘗試解析 JSON
                try:
                    webhook_data = request.get_json()
                    payload = json.dumps(webhook_data) if webhook_data else ''
                except:
                    payload = request.get_data(as_text=True)
                    webhook_data = {}
            
            # 獲取簽名
            signature = request.headers.get('X-Gumroad-Signature', '')
            
            logger.info(f"收到 Gumroad webhook: {len(payload)} 字節")
            logger.debug(f"Webhook 數據: {webhook_data}")
            
            # 驗證簽名（如果設置了密鑰）
            if not self.gumroad_service.verify_webhook_signature(payload, signature):
                logger.warning("Gumroad webhook 簽名驗證失敗")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # 處理 webhook
            result = self.gumroad_service.process_webhook(webhook_data)
            
            if result['success']:
                logger.info(f"Gumroad webhook 處理成功: {result.get('payment_id')}")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"Gumroad webhook 處理失敗: {result['error']}")
                return jsonify({'error': result['error']}), 400
                
        except Exception as e:
            logger.error(f"Gumroad webhook 處理錯誤: {str(e)}")
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
    
    def webhook_test(self):
        """測試 webhook 端點"""
        try:
            # 獲取測試數據
            test_data = {
                'seller_id': 'test_seller',
                'product_id': 'test_product',
                'email': 'test@example.com',
                'sale_id': 'test_sale_123',
                'order_number': '999999',
                'price': '2999',  # 29.99 USD in cents
                'currency': 'usd',
                'purchaser_name': 'Test User'
            }
            
            logger.info("處理測試 webhook")
            
            # 處理測試 webhook
            result = self.gumroad_service.process_webhook(test_data)
            
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

@gumroad_bp.route('/test-webhook', methods=['POST'])
def test_webhook():
    """測試 webhook 端點"""
    if not gumroad_routes:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    return gumroad_routes.webhook_test()

@gumroad_bp.route('/emergency-debug', methods=['GET'])
def emergency_debug():
    """緊急調試 - 獲取產品的真實購買鏈接"""
    if not gumroad_routes or not gumroad_routes.gumroad_service:
        return jsonify({
            'success': False,
            'error': 'Gumroad 服務未初始化'
        }), 503
    
    try:
        # 使用調試方法獲取所有產品
        result = gumroad_routes.gumroad_service.debug_all_products()
        
        if result.get('success'):
            products = result.get('products', [])
            
            # 映射我們的產品 ID
            our_product_ids = {
                '27M21oDD__7HRLfycCIKiQ': 'trial_7',
                'KBeLX9NDOECb4hpr5YD_9g': 'monthly_30', 
                '4ibYDgcsoi8_DPDacdNzpA': 'quarterly_90'
            }
            
            matched_products = {}
            for product in products:
                product_id = product.get('id')
                if product_id in our_product_ids:
                    plan_id = our_product_ids[product_id]
                    matched_products[plan_id] = {
                        **product,
                        'plan_id': plan_id,
                        'correct_purchase_url': product.get('short_url'),
                        'current_env_product_id': product_id
                    }
            
            return jsonify({
                'success': True,
                'debug_info': {
                    'all_products': products,
                    'our_products': matched_products,
                    'total_products_found': len(products),
                    'our_products_matched': len(matched_products)
                },
                'next_steps': [
                    "查看 'our_products' 中每個產品的 'correct_purchase_url'",
                    "這些就是正確的購買鏈接格式",
                    "如果 short_url 存在，使用它；否則產品可能未發布"
                ]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'API 調用失敗',
                'details': result.get('error')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'調試失敗: {str(e)}'
        }), 500