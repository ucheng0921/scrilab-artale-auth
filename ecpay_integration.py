from flask import Blueprint, request, jsonify, render_template_string, redirect
import os
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
import logging
import secrets
import uuid as uuid_lib
import json

logger = logging.getLogger(__name__)

# 創建綠界金流藍圖
ecpay_bp = Blueprint('ecpay', __name__, url_prefix='/payment')

# 綠界設定
ECPAY_CONFIG = {
    'MERCHANT_ID': os.environ.get('ECPAY_MERCHANT_ID', '2000132'),  # 測試商店代號
    'HASH_KEY': os.environ.get('ECPAY_HASH_KEY', '5294y06JbISpM5x9'),  # 測試 HashKey
    'HASH_IV': os.environ.get('ECPAY_HASH_IV', 'v77hoKGq4kWxNNIS'),   # 測試 HashIV
    'ACTION_URL': os.environ.get('ECPAY_ACTION_URL', 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'),  # 測試環境
    'RETURN_URL': os.environ.get('RETURN_URL', 'https://your-domain.com/payment/return'),
    'CLIENT_BACK_URL': os.environ.get('CLIENT_BACK_URL', 'https://your-domain.com/payment/success'),
    'ORDER_RESULT_URL': os.environ.get('ORDER_RESULT_URL', 'https://your-domain.com/payment/notify')
}

# 商品方案設定
PRODUCT_PLANS = {
    'trial_7': {
        'name': '7天體驗版',
        'price': 99,
        'days': 7,
        'description': 'Artale Script 7天體驗版'
    },
    'monthly_30': {
        'name': '30天月費版',
        'price': 299,
        'days': 30,
        'description': 'Artale Script 30天月費版'
    },
    'quarterly_90': {
        'name': '90天季費版',
        'price': 799,
        'days': 90,
        'description': 'Artale Script 90天季費版'
    },
    'yearly_365': {
        'name': '365天年費版',
        'price': 2999,
        'days': 365,
        'description': 'Artale Script 365天年費版'
    }
}

def generate_check_mac_value(params, hash_key, hash_iv):
    """生成綠界檢查碼"""
    # 1. 移除空值參數
    filtered_params = {k: v for k, v in params.items() if v is not None and v != ''}
    
    # 2. 按照 Key 值英文字母順序排序
    sorted_params = dict(sorted(filtered_params.items()))
    
    # 3. 組合參數字串
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
    
    # 4. 前後加上 HashKey 和 HashIV
    raw_string = f"HashKey={hash_key}&{param_string}&HashIV={hash_iv}"
    
    # 5. URL encode (小寫)
    encoded_string = urllib.parse.quote_plus(raw_string).lower()
    
    # 6. SHA256 加密並轉大寫
    check_mac_value = hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
    
    return check_mac_value

def create_ecpay_order(plan_id, user_email, return_url=None):
    """創建綠界訂單"""
    if plan_id not in PRODUCT_PLANS:
        raise ValueError(f"Invalid plan_id: {plan_id}")
    
    plan = PRODUCT_PLANS[plan_id]
    
    # 生成訂單編號
    order_id = f"ARTALE_{datetime.now().strftime('%Y%m%d')}_{secrets.token_hex(8).upper()}"
    
    # 設定訂單參數
    params = {
        'MerchantID': ECPAY_CONFIG['MERCHANT_ID'],
        'MerchantTradeNo': order_id,
        'MerchantTradeDate': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        'PaymentType': 'aio',
        'TotalAmount': plan['price'],
        'TradeDesc': plan['description'],
        'ItemName': plan['name'],
        'ReturnURL': ECPAY_CONFIG['ORDER_RESULT_URL'],
        'ChoosePayment': 'ALL',
        'ClientBackURL': return_url or ECPAY_CONFIG['CLIENT_BACK_URL'],
        'ItemURL': 'https://your-domain.com',
        'Remark': f'Artale Script {plan["name"]} - {user_email}',
        'ChooseSubPayment': '',
        'OrderResultURL': ECPAY_CONFIG['ORDER_RESULT_URL'],
        'NeedExtraPaidInfo': 'N',
        'DeviceSource': '',
        'IgnorePayment': '',
        'PlatformID': '',
        'InvoiceMark': 'N',
        'CustomField1': plan_id,  # 存儲方案 ID
        'CustomField2': user_email,  # 存儲用戶郵箱
        'CustomField3': '',
        'CustomField4': '',
        'EncryptType': 1
    }
    
    # 生成檢查碼
    check_mac_value = generate_check_mac_value(params, ECPAY_CONFIG['HASH_KEY'], ECPAY_CONFIG['HASH_IV'])
    params['CheckMacValue'] = check_mac_value
    
    return order_id, params

def verify_ecpay_callback(params):
    """驗證綠界回調數據"""
    try:
        # 取出檢查碼
        received_check_mac = params.pop('CheckMacValue', '')
        
        # 重新計算檢查碼
        calculated_check_mac = generate_check_mac_value(params, ECPAY_CONFIG['HASH_KEY'], ECPAY_CONFIG['HASH_IV'])
        
        # 比對檢查碼
        return received_check_mac.upper() == calculated_check_mac.upper()
    except Exception as e:
        logger.error(f"驗證綠界回調失敗: {str(e)}")
        return False

# 付款頁面 HTML 模板
PAYMENT_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Artale Script - 付款頁面</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0; padding: 20px; min-height: 100vh;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card { 
            background: white; border-radius: 16px; padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #2d3748; margin: 0; font-size: 2.5em; }
        .header p { color: #718096; margin: 10px 0 0 0; }
        .plan-card { 
            border: 2px solid #e2e8f0; border-radius: 12px; 
            padding: 20px; margin: 15px 0; cursor: pointer;
            transition: all 0.2s ease;
        }
        .plan-card:hover, .plan-card.selected { 
            border-color: #4299e1; background: #ebf8ff;
            transform: translateY(-2px);
        }
        .plan-title { font-size: 1.4em; font-weight: bold; color: #2d3748; }
        .plan-price { font-size: 2em; font-weight: bold; color: #4299e1; margin: 10px 0; }
        .plan-desc { color: #718096; }
        .form-group { margin: 20px 0; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: bold; color: #2d3748; }
        .form-group input { 
            width: 100%; padding: 12px; border: 2px solid #e2e8f0; 
            border-radius: 8px; font-size: 16px;
            transition: border-color 0.2s ease;
        }
        .form-group input:focus { 
            outline: none; border-color: #4299e1;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }
        .btn-primary { 
            background: linear-gradient(135deg, #4299e1, #3182ce);
            color: white; padding: 15px 30px; border: none; 
            border-radius: 8px; font-size: 18px; font-weight: bold;
            width: 100%; cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn-primary:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(66, 153, 225, 0.3);
        }
        .btn-primary:disabled { 
            background: #cbd5e0; cursor: not-allowed;
            transform: none; box-shadow: none;
        }
        .features { 
            background: #f7fafc; border-radius: 8px; 
            padding: 20px; margin: 20px 0;
        }
        .features h3 { margin-top: 0; color: #2d3748; }
        .features ul { margin: 0; padding-left: 20px; }
        .features li { margin: 8px 0; color: #4a5568; }
        .security-info { 
            text-align: center; margin-top: 20px; 
            padding: 15px; background: #edf2f7; border-radius: 8px;
        }
        .security-info small { color: #718096; }
        .loading { display: none; text-align: center; margin: 20px 0; }
        .spinner { 
            border: 3px solid #f3f3f3; border-top: 3px solid #4299e1;
            border-radius: 50%; width: 30px; height: 30px;
            animation: spin 1s linear infinite; margin: 0 auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>🎮 Artale Script</h1>
                <p>選擇您的授權方案</p>
            </div>
            
            <form id="payment-form" method="post" action="/payment/create-order">
                <div id="plans-section">
                    <div class="plan-card" data-plan="trial_7">
                        <div class="plan-title">7天體驗版</div>
                        <div class="plan-price">NT$ 99</div>
                        <div class="plan-desc">適合新手體驗，功能完整</div>
                    </div>
                    
                    <div class="plan-card selected" data-plan="monthly_30">
                        <div class="plan-title">30天月費版 🔥</div>
                        <div class="plan-price">NT$ 299</div>
                        <div class="plan-desc">最受歡迎，性價比最高</div>
                    </div>
                    
                    <div class="plan-card" data-plan="quarterly_90">
                        <div class="plan-title">90天季費版</div>
                        <div class="plan-price">NT$ 799</div>
                        <div class="plan-desc">省20%，長期使用推薦</div>
                    </div>
                    
                    <div class="plan-card" data-plan="yearly_365">
                        <div class="plan-title">365天年費版</div>
                        <div class="plan-price">NT$ 2999</div>
                        <div class="plan-desc">省50%，最划算選擇</div>
                    </div>
                </div>
                
                <div class="features">
                    <h3>✨ 功能特色</h3>
                    <ul>
                        <li>🚀 自動化腳本執行</li>
                        <li>🎯 智能任務調度</li>
                        <li>📊 即時數據監控</li>
                        <li>🔒 安全加密保護</li>
                        <li>📱 多平台支援</li>
                        <li>🆘 24/7 技術支援</li>
                    </ul>
                </div>
                
                <div class="form-group">
                    <label for="user-email">電子郵件地址 *</label>
                    <input type="email" id="user-email" name="email" required 
                           placeholder="your@email.com">
                </div>
                
                <div class="form-group">
                    <label for="user-name">姓名 (可選)</label>
                    <input type="text" id="user-name" name="name" 
                           placeholder="您的姓名">
                </div>
                
                <input type="hidden" id="selected-plan" name="plan" value="monthly_30">
                
                <button type="submit" class="btn-primary" id="submit-btn">
                    立即付款 - NT$ 299
                </button>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>正在處理您的訂單...</p>
                </div>
            </form>
            
            <div class="security-info">
                <small>
                    🔒 由綠界科技提供安全支付服務<br>
                    支援信用卡、ATM轉帳、超商付款等多種方式
                </small>
            </div>
        </div>
    </div>

    <script>
        const plans = {
            'trial_7': { name: '7天體驗版', price: 99 },
            'monthly_30': { name: '30天月費版', price: 299 },
            'quarterly_90': { name: '90天季費版', price: 799 },
            'yearly_365': { name: '365天年費版', price: 2999 }
        };

        // 方案選擇
        document.querySelectorAll('.plan-card').forEach(card => {
            card.addEventListener('click', function() {
                // 移除所有選中狀態
                document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('selected'));
                
                // 選中當前方案
                this.classList.add('selected');
                const planId = this.dataset.plan;
                const plan = plans[planId];
                
                // 更新表單
                document.getElementById('selected-plan').value = planId;
                document.getElementById('submit-btn').textContent = `立即付款 - NT$ ${plan.price}`;
            });
        });

        // 表單提交
        document.getElementById('payment-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('user-email').value.trim();
            if (!email) {
                alert('請輸入電子郵件地址');
                return;
            }
            
            // 顯示載入狀態
            document.getElementById('submit-btn').disabled = true;
            document.getElementById('loading').style.display = 'block';
            
            // 提交表單
            this.submit();
        });
    </script>
</body>
</html>
"""

# ===== 路由定義 =====

@ecpay_bp.route('', methods=['GET'])
def payment_page():
    """付款頁面"""
    return render_template_string(PAYMENT_PAGE_TEMPLATE)

@ecpay_bp.route('/create-order', methods=['POST'])
def create_order():
    """創建訂單並跳轉到綠界"""
    try:
        plan_id = request.form.get('plan')
        user_email = request.form.get('email', '').strip()
        user_name = request.form.get('name', '').strip()
        
        if not plan_id or plan_id not in PRODUCT_PLANS:
            return jsonify({'success': False, 'error': '無效的方案'}), 400
        
        if not user_email:
            return jsonify({'success': False, 'error': '請提供電子郵件地址'}), 400
        
        # 創建綠界訂單
        order_id, ecpay_params = create_ecpay_order(plan_id, user_email)
        
        # 存儲訂單到資料庫
        from app import db
        if db is not None:
            try:
                order_data = {
                    'order_id': order_id,
                    'plan_id': plan_id,
                    'plan_name': PRODUCT_PLANS[plan_id]['name'],
                    'amount': PRODUCT_PLANS[plan_id]['price'],
                    'days': PRODUCT_PLANS[plan_id]['days'],
                    'user_email': user_email,
                    'user_name': user_name,
                    'status': 'pending',
                    'created_at': datetime.now(),
                    'merchant_trade_no': order_id,
                    'uuid_generated': False
                }
                
                db.collection('orders').document(order_id).set(order_data)
                logger.info(f"訂單已創建: {order_id} - {user_email} - {plan_id}")
                
            except Exception as e:
                logger.error(f"存儲訂單失敗: {str(e)}")
        
        # 生成綠界付款表單 HTML
        form_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>跳轉到付款頁面...</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .loading {{ margin: 50px 0; }}
                .spinner {{ 
                    border: 4px solid #f3f3f3; border-top: 4px solid #3498db;
                    border-radius: 50%; width: 50px; height: 50px;
                    animation: spin 1s linear infinite; margin: 0 auto;
                }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="loading">
                <div class="spinner"></div>
                <h2>正在跳轉到付款頁面...</h2>
                <p>請稍候，系統正在處理您的訂單</p>
            </div>
            
            <form id="ecpay-form" method="post" action="{ECPAY_CONFIG['ACTION_URL']}">
        """
        
        # 添加所有參數為隱藏欄位
        for key, value in ecpay_params.items():
            form_html += f'<input type="hidden" name="{key}" value="{value}">\n'
        
        form_html += """
            </form>
            
            <script>
                // 自動提交表單
                document.getElementById('ecpay-form').submit();
            </script>
        </body>
        </html>
        """
        
        return form_html
        
    except Exception as e:
        logger.error(f"創建訂單失敗: {str(e)}")
        return jsonify({'success': False, 'error': '訂單創建失敗'}), 500

@ecpay_bp.route('/notify', methods=['POST'])
def payment_notify():
    """綠界付款結果通知 (後端)"""
    try:
        # 獲取綠界回傳的參數
        params = dict(request.form)
        logger.info(f"收到綠界通知: {params}")
        
        # 驗證資料完整性
        if not verify_ecpay_callback(params):
            logger.error("綠界回調驗證失敗")
            return "0|ERROR"
        
        # 取得訂單資訊
        merchant_trade_no = params.get('MerchantTradeNo')
        rtn_code = params.get('RtnCode')
        payment_date = params.get('PaymentDate')
        trade_amt = params.get('TradeAmt')
        
        if not merchant_trade_no:
            logger.error("缺少訂單編號")
            return "0|ERROR"
        
        # 更新訂單狀態
        from app import db
        if db is not None:
            try:
                order_ref = db.collection('orders').document(merchant_trade_no)
                order_doc = order_ref.get()
                
                if not order_doc.exists:
                    logger.error(f"訂單不存在: {merchant_trade_no}")
                    return "0|ERROR"
                
                order_data = order_doc.to_dict()
                
                # 檢查付款是否成功
                if rtn_code == '1':  # 付款成功
                    # 更新訂單狀態
                    order_ref.update({
                        'status': 'paid',
                        'payment_date': payment_date,
                        'trade_amount': trade_amt,
                        'rtn_code': rtn_code,
                        'ecpay_response': params,
                        'updated_at': datetime.now()
                    })
                    
                    # 自動生成並發放 UUID
                    if not order_data.get('uuid_generated', False):
                        success = auto_generate_user_uuid(order_data)
                        if success:
                            order_ref.update({
                                'uuid_generated': True,
                                'uuid_generated_at': datetime.now()
                            })
                            logger.info(f"已為訂單 {merchant_trade_no} 自動生成用戶")
                        else:
                            logger.error(f"為訂單 {merchant_trade_no} 生成用戶失敗")
                    
                    logger.info(f"訂單付款成功: {merchant_trade_no}")
                    return "1|OK"
                    
                else:  # 付款失敗
                    order_ref.update({
                        'status': 'failed',
                        'rtn_code': rtn_code,
                        'ecpay_response': params,
                        'updated_at': datetime.now()
                    })
                    logger.warning(f"訂單付款失敗: {merchant_trade_no}, Code: {rtn_code}")
                    return "1|OK"
                    
            except Exception as e:
                logger.error(f"處理訂單狀態更新失敗: {str(e)}")
                return "0|ERROR"
        
        return "1|OK"
        
    except Exception as e:
        logger.error(f"處理綠界通知失敗: {str(e)}")
        return "0|ERROR"

@ecpay_bp.route('/return', methods=['POST', 'GET'])
def payment_return():
    """綠界付款完成返回頁面"""
    try:
        # 獲取參數 (可能是 POST 或 GET)
        if request.method == 'POST':
            params = dict(request.form)
        else:
            params = dict(request.args)
        
        merchant_trade_no = params.get('MerchantTradeNo', '')
        rtn_code = params.get('RtnCode', '0')
        
        # 查詢訂單狀態
        order_status = 'unknown'
        order_info = None
        
        from app import db
        if db is not None and merchant_trade_no:
            try:
                order_ref = db.collection('orders').document(merchant_trade_no)
                order_doc = order_ref.get()
                
                if order_doc.exists:
                    order_info = order_doc.to_dict()
                    order_status = order_info.get('status', 'unknown')
            except Exception as e:
                logger.error(f"查詢訂單狀態失敗: {str(e)}")
        
        # 返回結果頁面
        if rtn_code == '1' and order_status == 'paid':
            return render_payment_success_page(order_info)
        else:
            return render_payment_failed_page(merchant_trade_no, rtn_code)
            
    except Exception as e:
        logger.error(f"處理返回頁面失敗: {str(e)}")
        return render_payment_failed_page('', 'ERROR')

@ecpay_bp.route('/success')
def payment_success():
    """付款成功頁面 (用戶返回)"""
    order_id = request.args.get('order_id', '')
    return render_payment_success_page({'order_id': order_id})

@ecpay_bp.route('/check-order/<order_id>')
def check_order_status(order_id):
    """檢查訂單狀態 API"""
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        order_ref = db.collection('orders').document(order_id)
        order_doc = order_ref.get()
        
        if not order_doc.exists:
            return jsonify({'success': False, 'error': '訂單不存在'}), 404
        
        order_data = order_doc.to_dict()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'status': order_data.get('status', 'unknown'),
            'plan_name': order_data.get('plan_name', ''),
            'amount': order_data.get('amount', 0),
            'created_at': order_data.get('created_at', '').isoformat() if hasattr(order_data.get('created_at'), 'isoformat') else str(order_data.get('created_at', '')),
            'uuid_generated': order_data.get('uuid_generated', False),
            'user_uuid': order_data.get('generated_uuid', '') if order_data.get('uuid_generated') else ''
        })
        
    except Exception as e:
        logger.error(f"檢查訂單狀態失敗: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ===== 輔助函數 =====

def auto_generate_user_uuid(order_data):
    """自動生成用戶 UUID 並創建用戶"""
    try:
        from app import db
        import re
        
        if db is None:
            logger.error("Database not available")
            return False
        
        # 生成 UUID
        plan_id = order_data.get('plan_id', 'monthly_30')
        
        # 根據方案類型選擇前綴
        if 'trial' in plan_id:
            prefix = 'artale_trial'
        elif 'yearly' in plan_id:
            prefix = 'artale_premium'
        else:
            prefix = 'artale'
        
        # 生成唯一 UUID
        max_attempts = 10
        for attempt in range(max_attempts):
            # 直接生成 UUID（不需要呼叫 admin_panel 的函數）
            user_id = uuid_lib.uuid4().hex[:8]
            now = datetime.now()
            date_str = now.strftime('%Y%m%d')
            new_uuid = f"{prefix}_{user_id}_{date_str}"
            
            # 檢查是否已存在
            uuid_hash = hashlib.sha256(new_uuid.encode()).hexdigest()
            user_ref = db.collection('authorized_users').document(uuid_hash)
            
            if not user_ref.get().exists:
                break
                
            if attempt == max_attempts - 1:
                logger.error("無法生成唯一 UUID")
                return False
        
        # 計算有效期
        days = order_data.get('days', 30)
        expires_at = None
        if days > 0:
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
        
        # 創建用戶
        user_data = {
            "original_uuid": new_uuid,
            "display_name": f"付費用戶 - {order_data.get('user_email', 'Unknown')}",
            "permissions": {
                "script_access": True,
                "config_modify": True
            },
            "active": True,
            "created_at": datetime.now(),
            "created_by": "ecpay_auto_system",
            "login_count": 0,
            "notes": f"綠界付款自動創建 - 訂單: {order_data.get('order_id')}",
            "payment_status": "已付款",
            "order_id": order_data.get('order_id'),
            "plan_id": plan_id,
            "plan_name": order_data.get('plan_name'),
            "user_email": order_data.get('user_email'),
            "amount_paid": order_data.get('amount')
        }
        
        if expires_at:
            user_data["expires_at"] = expires_at
        
        # 保存用戶
        user_ref.set(user_data)
        
        # 更新訂單記錄
        order_ref = db.collection('orders').document(order_data.get('order_id'))
        order_ref.update({
            'generated_uuid': new_uuid,
            'user_created_at': datetime.now()
        })
        
        logger.info(f"自動創建用戶成功: {new_uuid} - 訂單: {order_data.get('order_id')}")
        
        # 發送通知郵件 (可選)
        try:
            send_uuid_notification_email(order_data, new_uuid)
        except Exception as e:
            logger.warning(f"發送通知郵件失敗: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"自動生成用戶失敗: {str(e)}")
        return False

def send_uuid_notification_email(order_data, uuid):
    """發送 UUID 通知郵件 (預留功能)"""
    # TODO: 整合郵件服務 (如 SendGrid, AWS SES 等)
    logger.info(f"應發送 UUID 通知郵件到 {order_data.get('user_email')}: {uuid}")
    pass

def render_payment_success_page(order_info):
    """渲染付款成功頁面"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>付款成功 - Artale Script</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh;
                display: flex; align-items: center; justify-content: center;
            }
            .card { 
                background: white; border-radius: 16px; padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center; max-width: 500px; width: 100%;
            }
            .success-icon { font-size: 4em; color: #48bb78; margin-bottom: 20px; }
            h1 { color: #2d3748; margin: 0 0 10px 0; }
            p { color: #718096; margin: 10px 0; }
            .uuid-box { 
                background: #f7fafc; border: 2px dashed #e2e8f0;
                border-radius: 8px; padding: 20px; margin: 20px 0;
            }
            .uuid-code { 
                font-family: monospace; font-size: 1.2em; 
                background: #2d3748; color: #00ff00; 
                padding: 15px; border-radius: 8px; 
                word-break: break-all; margin: 10px 0;
            }
            .btn { 
                background: #4299e1; color: white; 
                padding: 12px 24px; border: none; border-radius: 8px;
                text-decoration: none; display: inline-block;
                margin: 10px; cursor: pointer;
            }
            .btn:hover { background: #3182ce; }
            .info-box { 
                background: #ebf8ff; border: 1px solid #bee3f8;
                border-radius: 8px; padding: 15px; margin: 20px 0;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="success-icon">✅</div>
            <h1>付款成功！</h1>
            <p>感謝您購買 Artale Script，您的序號已自動生成</p>
            
            <div class="uuid-box">
                <h3>🎟️ 您的專屬序號</h3>
                <div class="uuid-code" id="uuid-display">
                    {{ uuid or '正在生成中...' }}
                </div>
                <button class="btn" onclick="copyUUID()">📋 複製序號</button>
            </div>
            
            <div class="info-box">
                <h4>📋 使用說明</h4>
                <ul>
                    <li>請妥善保存您的序號</li>
                    <li>序號用於登入 Artale Script 系統</li>
                    <li>有效期限：{{ plan_name or '30天' }}</li>
                    <li>如有問題請聯繫客服</li>
                </ul>
            </div>
            
            <div>
                <a href="/payment" class="btn">🛒 再次購買</a>
                <a href="https://discord.gg/your-server" class="btn">💬 加入Discord</a>
            </div>
            
            <p style="margin-top: 30px;">
                <small>訂單編號: {{ order_id or 'N/A' }}</small>
            </p>
        </div>
        
        <script>
            function copyUUID() {
                const uuid = document.getElementById('uuid-display').textContent.trim();
                if (uuid && uuid !== '正在生成中...') {
                    navigator.clipboard.writeText(uuid).then(() => {
                        alert('序號已複製到剪貼簿！');
                    });
                } else {
                    alert('序號尚未生成完成，請稍後再試');
                }
            }
            
            // 如果序號還在生成中，定期檢查狀態
            const uuidDisplay = document.getElementById('uuid-display');
            if (uuidDisplay.textContent.includes('正在生成中')) {
                const checkStatus = setInterval(() => {
                    fetch('/payment/check-order/{{ order_id or "" }}')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.uuid_generated && data.user_uuid) {
                                uuidDisplay.textContent = data.user_uuid;
                                clearInterval(checkStatus);
                            }
                        })
                        .catch(console.error);
                }, 3000);
                
                // 10分鐘後停止檢查
                setTimeout(() => clearInterval(checkStatus), 600000);
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(template, 
                                 uuid=order_info.get('generated_uuid', ''),
                                 order_id=order_info.get('order_id', ''),
                                 plan_name=order_info.get('plan_name', ''))

def render_payment_failed_page(order_id, error_code):
    """渲染付款失敗頁面"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>付款失敗 - Artale Script</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #fc8181 0%, #f56565 100%);
                margin: 0; padding: 20px; min-height: 100vh;
                display: flex; align-items: center; justify-content: center;
            }
            .card { 
                background: white; border-radius: 16px; padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center; max-width: 500px; width: 100%;
            }
            .error-icon { font-size: 4em; color: #e53e3e; margin-bottom: 20px; }
            h1 { color: #2d3748; margin: 0 0 10px 0; }
            p { color: #718096; margin: 10px 0; }
            .btn { 
                background: #4299e1; color: white; 
                padding: 12px 24px; border: none; border-radius: 8px;
                text-decoration: none; display: inline-block;
                margin: 10px; cursor: pointer;
            }
            .btn:hover { background: #3182ce; }
            .error-info { 
                background: #fed7d7; border: 1px solid #feb2b2;
                border-radius: 8px; padding: 15px; margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="error-icon">❌</div>
            <h1>付款失敗</h1>
            <p>很抱歉，您的付款未能成功完成</p>
            
            <div class="error-info">
                <p><strong>錯誤代碼:</strong> {{ error_code }}</p>
                <p><strong>訂單編號:</strong> {{ order_id or '無' }}</p>
            </div>
            
            <div>
                <a href="/payment" class="btn">🔄 重新購買</a>
                <a href="mailto:support@example.com" class="btn">📧 聯繫客服</a>
            </div>
            
            <p style="margin-top: 30px;">
                <small>如需協助，請提供上述錯誤信息給客服人員</small>
            </p>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(template, order_id=order_id, error_code=error_code)
