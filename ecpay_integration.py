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

def get_base_url():
    """
    取得當前網站的基礎URL
    """
    # 優先使用環境變數
    base_url = os.environ.get('BASE_URL')
    if base_url:
        return base_url.rstrip('/')
    
    # 自動偵測（適用於Render）
    if 'RENDER' in os.environ:
        service_name = os.environ.get('RENDER_SERVICE_NAME', 'scrilab-artale-auth')
        return f"https://{service_name}.onrender.com"
    
    # 本地開發環境
    return "http://localhost:5000"

# 綠界設定
ECPAY_CONFIG = {
    'MERCHANT_ID': os.environ.get('ECPAY_MERCHANT_ID'),  # 移除預設值
    'HASH_KEY': os.environ.get('ECPAY_HASH_KEY'),        # 移除預設值
    'HASH_IV': os.environ.get('ECPAY_HASH_IV'),          # 移除預設值
    'ACTION_URL': os.environ.get('ECPAY_ACTION_URL'),    # 移除預設值
    'RETURN_URL': os.environ.get('RETURN_URL', f"{get_base_url()}/payment/return"),
    'CLIENT_BACK_URL': os.environ.get('CLIENT_BACK_URL', f"{get_base_url()}/payment/return"),
    'ORDER_RESULT_URL': os.environ.get('ORDER_RESULT_URL', f"{get_base_url()}/payment/notify")
}

# 添加驗證檢查（可選，但建議加上）
if not ECPAY_CONFIG['MERCHANT_ID']:
    logger.error("❌ 請設定 ECPAY_MERCHANT_ID 環境變數")
if not ECPAY_CONFIG['HASH_KEY']:
    logger.error("❌ 請設定 ECPAY_HASH_KEY 環境變數")
if not ECPAY_CONFIG['HASH_IV']:
    logger.error("❌ 請設定 ECPAY_HASH_IV 環境變數")
if not ECPAY_CONFIG['ACTION_URL']:
    logger.error("❌ 請設定 ECPAY_ACTION_URL 環境變數")

# 商品方案設定
PRODUCT_PLANS = {
    'trial_7': {
        'name': '7天體驗版',
        'price': 5,
        'days': 7,
        'description': 'Artale Script 7天體驗版'
    },
    'monthly_30': {
        'name': '30天月費版',
        'price': 5,
        'days': 30,
        'description': 'Artale Script 30天月費版'
    },
    'quarterly_90': {
        'name': '90天季費版',
        'price': 5,
        'days': 90,
        'description': 'Artale Script 90天季費版'
    },
    'yearly_365': {
        'name': '365天年費版',
        'price': 5,
        'days': 365,
        'description': 'Artale Script 365天年費版'
    }
}

def generate_check_mac_value(params, hash_key, hash_iv):
    """
    生成綠界檢查碼 - 完全符合綠界規範的版本
    """
    try:
        # 1. 移除空值和CheckMacValue參數
        filtered_params = {}
        for key, value in params.items():
            if key != 'CheckMacValue' and value is not None and str(value).strip() != '':
                filtered_params[key] = str(value).strip()
        
        # 2. 按Key值英文字母順序排序（區分大小寫）
        sorted_params = dict(sorted(filtered_params.items()))
        
        # 3. 組合成查詢字串格式
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
        
        # 4. 前後加上HashKey和HashIV
        raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
        
        # 5. URL Encode (注意：綠界要求特定的編碼方式)
        encoded_string = urllib.parse.quote_plus(raw_string, safe='')
        
        # 6. 轉換為小寫
        encoded_string = encoded_string.lower()
        
        # 7. SHA256加密並轉大寫
        check_mac_value = hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
        
        # 調試輸出
        logger.info(f"檢查碼計算過程:")
        logger.info(f"1. 排序後參數: {sorted_params}")
        logger.info(f"2. 查詢字串: {query_string}")
        logger.info(f"3. 原始字串: {raw_string}")
        logger.info(f"4. 編碼字串: {encoded_string}")
        logger.info(f"5. 檢查碼: {check_mac_value}")
        
        return check_mac_value
        
    except Exception as e:
        logger.error(f"檢查碼計算失敗: {str(e)}")
        raise

def verify_ecpay_callback_robust(params):
    """
    強化版綠界回調驗證 - 處理中英文 RtnMsg 差異
    """
    try:
        # 複製參數以避免修改原始數據
        verify_params = params.copy()
        received_check_mac = verify_params.pop('CheckMacValue', '')
        
        logger.info("=== 綠界回調驗證調試 ===")
        logger.info(f"收到的檢查碼: {received_check_mac}")
        logger.info(f"原始 RtnMsg: {verify_params.get('RtnMsg', 'N/A')}")
        
        # 獲取原始 RtnMsg
        original_rtn_msg = verify_params.get('RtnMsg', '')
        
        # 如果是成功狀態，嘗試兩種可能的 RtnMsg 值
        if original_rtn_msg in ['交易成功', 'Succeeded', 'Success', '1']:
            possible_messages = ['交易成功', 'Succeeded']
            
            for test_msg in possible_messages:
                test_params = verify_params.copy()
                test_params['RtnMsg'] = test_msg
                
                # 計算檢查碼
                calculated_check_mac = generate_check_mac_value(
                    test_params, 
                    ECPAY_CONFIG['HASH_KEY'], 
                    ECPAY_CONFIG['HASH_IV']
                )
                
                logger.info(f"測試 RtnMsg='{test_msg}' -> 計算檢查碼: {calculated_check_mac}")
                
                # 比較檢查碼 (忽略大小寫)
                if received_check_mac.upper() == calculated_check_mac.upper():
                    logger.info(f"✅ 驗證成功! 使用 RtnMsg='{test_msg}'")
                    return True
                else:
                    logger.info(f"❌ 驗證失敗 RtnMsg='{test_msg}'")
            
            # 如果兩種標準值都失敗，嘗試原始值
            logger.info(f"嘗試原始 RtnMsg 值: '{original_rtn_msg}'")
            calculated_check_mac = generate_check_mac_value(
                verify_params, 
                ECPAY_CONFIG['HASH_KEY'], 
                ECPAY_CONFIG['HASH_IV']
            )
            
            logger.info(f"原始值計算檢查碼: {calculated_check_mac}")
            if received_check_mac.upper() == calculated_check_mac.upper():
                logger.info("✅ 使用原始 RtnMsg 值驗證成功!")
                return True
            
            logger.error("❌ 所有 RtnMsg 嘗試都失敗")
            return False
        else:
            # 非成功狀態，直接使用原始值驗證
            calculated_check_mac = generate_check_mac_value(
                verify_params, 
                ECPAY_CONFIG['HASH_KEY'], 
                ECPAY_CONFIG['HASH_IV']
            )
            
            logger.info(f"非成功狀態驗證 - 計算檢查碼: {calculated_check_mac}")
            result = received_check_mac.upper() == calculated_check_mac.upper()
            logger.info(f"驗證結果: {'✅ 成功' if result else '❌ 失敗'}")
            return result
            
    except Exception as e:
        logger.error(f"驗證綠界回調異常: {str(e)}")
        return False

def verify_ecpay_callback(params):
    """原始驗證函數 - 保持向後兼容"""
    return verify_ecpay_callback_robust(params)

def process_payment_notification_safe(params):
    """
    安全的付款通知處理 - 防重複處理
    """
    try:
        merchant_trade_no = params.get('MerchantTradeNo')
        rtn_code = params.get('RtnCode')
        
        logger.info(f"處理付款通知: 訂單={merchant_trade_no}, 狀態碼={rtn_code}")
        
        if not merchant_trade_no:
            logger.error("缺少訂單編號")
            return "0|ERROR"
        
        from app import db
        if db is None:
            logger.error("數據庫不可用")
            return "0|ERROR"
        
        # 獲取訂單
        order_ref = db.collection('orders').document(merchant_trade_no)
        order_doc = order_ref.get()
        
        if not order_doc.exists:
            logger.error(f"訂單不存在: {merchant_trade_no}")
            return "0|ERROR"
        
        order_data = order_doc.to_dict()
        current_status = order_data.get('status', 'pending')
        
        # 防重複處理
        if current_status == 'paid' and rtn_code == '1':
            logger.info(f"訂單 {merchant_trade_no} 已處理過，返回成功")
            return "1|OK"
        
        # 處理付款成功
        if rtn_code == '1':
            # 更新訂單狀態
            update_data = {
                'status': 'paid',
                'payment_date': params.get('PaymentDate'),
                'trade_amount': params.get('TradeAmt'),
                'rtn_code': rtn_code,
                'rtn_msg': params.get('RtnMsg'),
                'ecpay_response': params,
                'updated_at': datetime.now(),
                'processed_count': order_data.get('processed_count', 0) + 1
            }
            
            order_ref.update(update_data)
            logger.info(f"訂單 {merchant_trade_no} 狀態已更新為 paid")
            
            # 生成用戶 UUID (如果尚未生成)
            if not order_data.get('uuid_generated', False):
                try:
                    success = auto_generate_user_uuid(order_data)
                    if success:
                        order_ref.update({
                            'uuid_generated': True,
                            'uuid_generated_at': datetime.now()
                        })
                        logger.info(f"已為訂單 {merchant_trade_no} 生成用戶")
                    else:
                        logger.error(f"為訂單 {merchant_trade_no} 生成用戶失敗")
                except Exception as e:
                    logger.error(f"生成用戶過程異常: {str(e)}")
            
            return "1|OK"
            
        else:
            # 付款失敗
            order_ref.update({
                'status': 'failed',
                'rtn_code': rtn_code,
                'rtn_msg': params.get('RtnMsg'),
                'ecpay_response': params,
                'updated_at': datetime.now()
            })
            logger.warning(f"訂單 {merchant_trade_no} 付款失敗，代碼: {rtn_code}")
            return "1|OK"
            
    except Exception as e:
        logger.error(f"處理付款通知異常: {str(e)}")
        return "0|ERROR"

def create_ecpay_order(plan_id, user_email, return_url=None):
    """
    創建綠界訂單 - 完全符合綠界API規範
    """
    if plan_id not in PRODUCT_PLANS:
        raise ValueError(f"Invalid plan_id: {plan_id}")
    
    plan = PRODUCT_PLANS[plan_id]
    
    # 生成符合綠界規範的訂單編號（英數字，長度20字元內）
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(3).upper()  # 6位隨機碼
    order_id = f"AT{timestamp}{random_suffix}"  # 格式：AT20250705131128ABC123
    
    # 確保訂單編號不超過20字元
    if len(order_id) > 20:
        order_id = order_id[:20]
    
    # 取得當前部署的網域
    base_url = get_base_url()
    
    # 準備綠界參數（按照綠界API文件）
    params = {
        'MerchantID': ECPAY_CONFIG['MERCHANT_ID'],
        'MerchantTradeNo': order_id,
        'MerchantTradeDate': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        'PaymentType': 'aio',
        'TotalAmount': int(plan['price']),  # 必須是整數
        'TradeDesc': plan['description'],  # 不要URL編碼，讓綠界自己處理
        'ItemName': plan['name'],  # 不要URL編碼
        'ReturnURL': f"{base_url}/payment/notify",
        'ChoosePayment': 'ALL',
        'ClientBackURL': f"{base_url}/payment/return",
        'ItemURL': base_url,
        'Remark': f"User: {user_email}",
        'OrderResultURL': f"{base_url}/payment/notify",
        'NeedExtraPaidInfo': 'N',
        'InvoiceMark': 'N',
        'CustomField1': plan_id,
        'CustomField2': user_email[:50],  # 限制長度
        'CustomField3': '',
        'CustomField4': '',
        'EncryptType': 1  # 數字，不是字串
    }
    
    # 移除空值
    clean_params = {k: v for k, v in params.items() if v != ''}
    
    # 生成檢查碼
    try:
        check_mac_value = generate_check_mac_value(clean_params, 
                                                 ECPAY_CONFIG['HASH_KEY'], 
                                                 ECPAY_CONFIG['HASH_IV'])
        clean_params['CheckMacValue'] = check_mac_value
        
        logger.info(f"綠界訂單創建成功:")
        logger.info(f"訂單編號: {order_id}")
        logger.info(f"金額: {plan['price']}")
        logger.info(f"商品: {plan['name']}")
        logger.info(f"檢查碼: {check_mac_value}")
        
        return order_id, clean_params
        
    except Exception as e:
        logger.error(f"創建綠界訂單失敗: {str(e)}")
        raise

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
    """創建訂單並跳轉到綠界 - 修復版本"""
    try:
        plan_id = request.form.get('plan')
        user_email = request.form.get('email', '').strip()
        user_name = request.form.get('name', '').strip()
        
        # 驗證輸入
        if not plan_id or plan_id not in PRODUCT_PLANS:
            logger.error(f"無效的方案: {plan_id}")
            return jsonify({'success': False, 'error': '無效的方案'}), 400
        
        if not user_email:
            logger.error("缺少電子郵件")
            return jsonify({'success': False, 'error': '請提供電子郵件地址'}), 400
        
        # 創建綠界訂單
        try:
            order_id, ecpay_params = create_ecpay_order(plan_id, user_email)
        except Exception as e:
            logger.error(f"創建綠界訂單失敗: {str(e)}")
            return f"<h1>訂單創建失敗</h1><p>錯誤: {str(e)}</p><a href='/payment'>返回</a>", 500
        
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
                    'uuid_generated': False,
                    'ecpay_params': ecpay_params  # 保存參數供調試
                }
                
                db.collection('orders').document(order_id).set(order_data)
                logger.info(f"訂單已存入資料庫: {order_id}")
                
            except Exception as e:
                logger.error(f"存儲訂單失敗: {str(e)}")
                # 繼續執行，不中斷付款流程
        
        # 生成提交表單HTML（調試版本）
        form_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>跳轉到綠界付款...</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background: #f0f2f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .loading {{ margin: 30px 0; }}
                .spinner {{ 
                    border: 4px solid #f3f3f3; 
                    border-top: 4px solid #3498db;
                    border-radius: 50%; 
                    width: 50px; 
                    height: 50px;
                    animation: spin 1s linear infinite; 
                    margin: 0 auto 20px auto;
                }}
                @keyframes spin {{ 
                    0% {{ transform: rotate(0deg); }} 
                    100% {{ transform: rotate(360deg); }} 
                }}
                .debug {{ 
                    text-align: left; 
                    background: #f8f9fa; 
                    padding: 15px; 
                    border-radius: 4px;
                    margin: 20px 0;
                    font-family: monospace;
                    font-size: 12px;
                    max-height: 200px;
                    overflow-y: auto;
                }}
                .btn {{
                    background: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="loading">
                    <div class="spinner"></div>
                    <h2>正在跳轉到綠界付款頁面...</h2>
                    <p>訂單編號: <strong>{order_id}</strong></p>
                    <p>金額: <strong>NT$ {PRODUCT_PLANS[plan_id]['price']}</strong></p>
                    <p>方案: <strong>{PRODUCT_PLANS[plan_id]['name']}</strong></p>
                </div>
                
                <div class="debug">
                    <strong>調試資訊:</strong><br>
                    目標網址: {ECPAY_CONFIG['ACTION_URL']}<br>
                    商店代號: {ecpay_params.get('MerchantID')}<br>
                    檢查碼: {ecpay_params.get('CheckMacValue', 'ERROR')[:16]}...<br>
                    參數數量: {len(ecpay_params)}
                </div>
                
                <form id="ecpay-form" method="post" action="{ECPAY_CONFIG['ACTION_URL']}">
        """
        
        # 添加所有參數為隱藏欄位
        for key, value in ecpay_params.items():
            # 確保值是字串且已編碼
            encoded_value = str(value).replace('"', '&quot;')
            form_html += f'                    <input type="hidden" name="{key}" value="{encoded_value}">\n'
        
        form_html += f"""
                </form>
                
                <button onclick="submitForm()" class="btn">手動提交 (如果沒有自動跳轉)</button>
                <button onclick="showParams()" class="btn">顯示參數</button>
                
                <div id="params" style="display:none;" class="debug">
                    <strong>完整參數:</strong><br>
        """
        
        # 顯示所有參數供調試
        for key, value in ecpay_params.items():
            form_html += f"                    {key}: {value}<br>\n"
        
        form_html += """
                </div>
            </div>
            
            <script>
                let autoSubmitted = false;
                
                function submitForm() {
                    if (!autoSubmitted) {
                        document.getElementById('ecpay-form').submit();
                        autoSubmitted = true;
                    }
                }
                
                function showParams() {
                    const params = document.getElementById('params');
                    params.style.display = params.style.display === 'none' ? 'block' : 'none';
                }
                
                // 3秒後自動提交
                setTimeout(function() {
                    if (!autoSubmitted) {
                        console.log('Auto submitting form...');
                        submitForm();
                    }
                }, 3000);
            </script>
        </body>
        </html>
        """
        
        return form_html
        
    except Exception as e:
        logger.error(f"創建訂單失敗: {str(e)}")
        return f"""
        <h1>系統錯誤</h1>
        <p>錯誤詳情: {str(e)}</p>
        <a href="/payment">返回付款頁面</a>
        """, 500

@ecpay_bp.route('/notify', methods=['POST'])
def payment_notify():
    """綠界付款結果通知 (後端) - 修復版本"""
    try:
        # 獲取綠界回傳的參數
        params = dict(request.form)
        logger.info(f"收到綠界通知: {params}")
        
        # 使用強化版驗證
        if not verify_ecpay_callback_robust(params):
            logger.error("❌ 綠界回調驗證失敗")
            # 記錄失敗詳情但仍返回成功避免重複發送
            return "1|OK"  # 改為返回成功，避免綠界重複發送
        
        logger.info("✅ 綠界回調驗證成功")
        
        # 安全處理付款通知
        return process_payment_notification_safe(params)
        
    except Exception as e:
        logger.error(f"處理綠界通知失敗: {str(e)}")
        return "0|ERROR"

@ecpay_bp.route('/return', methods=['POST', 'GET'])
def payment_return():
    """綠界付款完成返回頁面 - 修復版本"""
    try:
        # 獲取參數 (可能是 POST 或 GET)
        if request.method == 'POST':
            params = dict(request.form)
        else:
            params = dict(request.args)
        
        merchant_trade_no = params.get('MerchantTradeNo', '')
        rtn_code = params.get('RtnCode', '0')
        
        logger.info(f"Payment return: order={merchant_trade_no}, code={rtn_code}")
        
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
                    logger.info(f"Order found: {order_status}")
                else:
                    logger.warning(f"Order not found: {merchant_trade_no}")
            except Exception as e:
                logger.error(f"查詢訂單狀態失敗: {str(e)}")
        
        # 返回結果頁面
        if rtn_code == '1':  # 綠界回傳成功
            if order_info:
                return render_payment_success_page(order_info)
            else:
                # 即使找不到訂單，也顯示成功頁面但不顯示序號
                return render_payment_success_page({
                    'order_id': merchant_trade_no,
                    'plan_name': '未知方案'
                })
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
    """檢查訂單狀態 API - 修復版本"""
    try:
        if not order_id or order_id.strip() == '':
            return jsonify({'success': False, 'error': '缺少訂單ID'}), 400
            
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        order_ref = db.collection('orders').document(order_id)
        order_doc = order_ref.get()
        
        if not order_doc.exists:
            logger.warning(f"Order not found: {order_id}")
            return jsonify({'success': False, 'error': '訂單不存在'}), 404
        
        order_data = order_doc.to_dict()
        
        # 格式化創建時間
        created_at = order_data.get('created_at', '')
        if hasattr(created_at, 'isoformat'):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = str(created_at)
        
        response_data = {
            'success': True,
            'order_id': order_id,
            'status': order_data.get('status', 'unknown'),
            'plan_name': order_data.get('plan_name', ''),
            'amount': order_data.get('amount', 0),
            'created_at': created_at_str,
            'uuid_generated': order_data.get('uuid_generated', False),
            'user_uuid': order_data.get('generated_uuid', '') if order_data.get('uuid_generated') else ''
        }
        
        logger.info(f"Order status check: {order_id} -> {response_data['status']}")
        return jsonify(response_data)
        
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
    """渲染付款成功頁面 - 修復版本"""
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
            .loading-message {
                color: #4299e1;
                font-style: italic;
                margin: 10px 0;
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
                {% if not uuid %}
                <div class="loading-message" id="loading-status">
                    ⏳ 系統正在為您生成專屬序號，請稍候...
                </div>
                {% endif %}
                <button class="btn" onclick="copyUUID()" id="copy-btn" 
                        {% if not uuid %}style="display:none;"{% endif %}>
                    📋 複製序號
                </button>
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
                    }).catch(err => {
                        // 如果 clipboard API 不支援，使用舊方法
                        const textArea = document.createElement('textarea');
                        textArea.value = uuid;
                        document.body.appendChild(textArea);
                        textArea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textArea);
                        alert('序號已複製到剪貼簿！');
                    });
                } else {
                    alert('序號尚未生成完成，請稍後再試');
                }
            }
            
            // 檢查序號生成狀態 - 修復版本
            const orderId = '{{ order_id or "" }}';
            const uuidDisplay = document.getElementById('uuid-display');
            const loadingStatus = document.getElementById('loading-status');
            const copyBtn = document.getElementById('copy-btn');
            
            if (orderId && uuidDisplay.textContent.includes('正在生成中')) {
                let checkCount = 0;
                const maxChecks = 20; // 最多檢查20次 (1分鐘)
                
                const checkStatus = setInterval(() => {
                    checkCount++;
                    
                    if (checkCount > maxChecks) {
                        clearInterval(checkStatus);
                        if (loadingStatus) {
                            loadingStatus.innerHTML = '⚠️ 序號生成時間較長，請稍後刷新頁面查看';
                            loadingStatus.style.color = '#e53e3e';
                        }
                        return;
                    }
                    
                    // 修復：確保 URL 包含訂單ID
                    fetch(`/payment/check-order/${orderId}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.success && data.uuid_generated && data.user_uuid) {
                                uuidDisplay.textContent = data.user_uuid;
                                if (loadingStatus) loadingStatus.style.display = 'none';
                                if (copyBtn) copyBtn.style.display = 'inline-block';
                                clearInterval(checkStatus);
                            } else if (loadingStatus) {
                                loadingStatus.innerHTML = `⏳ 正在生成序號... (${checkCount}/${maxChecks})`;
                            }
                        })
                        .catch(error => {
                            console.error('檢查狀態失敗:', error);
                            if (checkCount > 5) { // 5次失敗後停止
                                clearInterval(checkStatus);
                                if (loadingStatus) {
                                    loadingStatus.innerHTML = '⚠️ 無法檢查生成狀態，請刷新頁面或聯繫客服';
                                    loadingStatus.style.color = '#e53e3e';
                                }
                            }
                        });
                }, 3000); // 每3秒檢查一次
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
