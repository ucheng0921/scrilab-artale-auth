"""
itchio_routes.py - itch.io 付款相關路由
"""
from flask import Blueprint, request, jsonify, redirect, render_template_string
import logging
import json

logger = logging.getLogger(__name__)

# 創建藍圖
itchio_bp = Blueprint('itchio', __name__, url_prefix='/itchio')

class ItchioRoutes:
    """itch.io 路由處理器"""
    
    def __init__(self, itchio_service):
        self.itchio_service = itchio_service
        logger.info("✅ ItchioRoutes 已初始化")
    
    def create_payment(self):
        """創建 itch.io 付款"""
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
            result = self.itchio_service.create_purchase_url(plan_id, user_info)
            
            if result['success']:
                logger.info(f"itch.io 付款創建成功: {result['payment_id']}")
                return jsonify({
                    'success': True,
                    'purchase_url': result['purchase_url'],
                    'payment_id': result['payment_id'],
                    'plan_name': result['plan']['name'],
                    'amount_twd': result['plan']['price_twd'],
                    'amount_usd': result['plan']['price_usd']
                })
            else:
                logger.error(f"itch.io 付款創建失敗: {result['error']}")
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 500
                
        except Exception as e:
            logger.error(f"創建 itch.io 付款錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤，請稍後再試'
            }), 500
    
    def webhook_handler(self):
        """處理 itch.io webhook"""
        try:
            # 獲取原始請求數據
            payload = request.get_data(as_text=True)
            signature = request.headers.get('X-Itch-Signature', '')
            
            logger.info(f"收到 itch.io webhook: {len(payload)} 字節")
            
            # 驗證簽名
            if not self.itchio_service.verify_webhook_signature(payload, signature):
                logger.warning("itch.io webhook 簽名驗證失敗")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # 解析 JSON 數據
            try:
                webhook_data = json.loads(payload)
            except json.JSONDecodeError as e:
                logger.error(f"解析 webhook JSON 失敗: {str(e)}")
                return jsonify({'error': 'Invalid JSON'}), 400
            
            # 處理 webhook
            result = self.itchio_service.process_webhook(webhook_data)
            
            if result['success']:
                logger.info(f"itch.io webhook 處理成功: {result.get('payment_id')}")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"itch.io webhook 處理失敗: {result['error']}")
                return jsonify({'error': result['error']}), 400
                
        except Exception as e:
            logger.error(f"itch.io webhook 處理錯誤: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def payment_success(self):
        """付款成功頁面"""
        try:
            payment_id = request.args.get('payment_id')
            
            if not payment_id:
                return redirect('/products?error=missing_payment_id')
            
            # 獲取付款記錄
            payment_record = self.itchio_service.get_payment_record(payment_id)
            
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
            payment_record = self.itchio_service.get_payment_record(payment_id)
            
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
            stats = self.itchio_service.get_purchase_stats()
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

# 全局路由處理器實例
itchio_routes = None

def init_itchio_routes(itchio_service):
    """初始化 itch.io 路由"""
    global itchio_routes
    itchio_routes = ItchioRoutes(itchio_service)
    logger.info("✅ itch.io 路由已初始化")

# 註冊路由端點
@itchio_bp.route('/create-payment', methods=['POST'])
def create_payment():
    """創建 itch.io 付款"""
    if not itchio_routes:
        return jsonify({
            'success': False,
            'error': 'itch.io 服務未初始化'
        }), 503
    
    return itchio_routes.create_payment()

@itchio_bp.route('/webhook', methods=['POST'])
def webhook():
    """itch.io webhook 處理"""
    if not itchio_routes:
        return jsonify({'error': 'Service not available'}), 503
    
    return itchio_routes.webhook_handler()

@itchio_bp.route('/success', methods=['GET'])
def payment_success():
    """付款成功頁面"""
    if not itchio_routes:
        return redirect('/products?error=service_unavailable')
    
    return itchio_routes.payment_success()

@itchio_bp.route('/check-status', methods=['POST'])
def check_payment_status():
    """檢查付款狀態"""
    if not itchio_routes:
        return jsonify({
            'success': False,
            'error': 'itch.io 服務未初始化'
        }), 503
    
    return itchio_routes.check_payment_status()

@itchio_bp.route('/stats', methods=['GET'])
def purchase_stats():
    """獲取購買統計"""
    if not itchio_routes:
        return jsonify({
            'success': False,
            'error': 'itch.io 服務未初始化'
        }), 503
    
    return itchio_routes.get_purchase_stats()