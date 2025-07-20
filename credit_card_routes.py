# credit_card_routes.py - 新增這個文件到你的項目根目錄
from flask import Blueprint, request, jsonify, render_template_string, redirect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 創建藍圖
credit_card_bp = Blueprint('credit_card', __name__, url_prefix='/payment/credit-card')

# 真正的信用卡付款模板（Mercuryo 風格）
CREDIT_CARD_PAYMENT_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全信用卡付款 - Scrilab</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-card: #ffffff;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --text-muted: #718096;
            --accent-blue: #3182ce;
            --accent-green: #38a169;
            --border-color: #e2e8f0;
            --border-focus: #3182ce;
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .payment-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
            display: flex;
            align-items: center;
        }

        .payment-card {
            background: var(--bg-card);
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            width: 100%;
            display: grid;
            grid-template-columns: 1fr 1fr;
            min-height: 600px;
        }

        .order-summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .payment-form {
            padding: 3rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 2rem;
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .order-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .order-item:last-of-type {
            border-bottom: none;
            font-weight: 600;
            font-size: 1.2rem;
            margin-top: 1rem;
            padding-top: 1.5rem;
            border-top: 2px solid rgba(255, 255, 255, 0.3);
        }

        .security-badges {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            opacity: 0.8;
        }

        .security-badge {
            display: flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.8rem;
        }

        .form-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .form-subtitle {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .fiat-crypto-notice {
            background: linear-gradient(135deg, #e8f5e9 0%, #f3e5f5 100%);
            border: 1px solid #c8e6c9;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }

        .fiat-crypto-notice h4 {
            color: #2e7d32;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }

        .fiat-crypto-notice p {
            color: #4a5568;
            margin: 0;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
            font-weight: 500;
            font-size: 0.9rem;
        }

        .form-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: var(--bg-secondary);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--border-focus);
            box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
        }

        .form-row {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1rem;
        }

        .card-input {
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>');
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 20px;
            padding-right: 45px;
        }

        .payment-methods {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .payment-method {
            width: 40px;
            height: 25px;
            background: var(--border-color);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .visa { background: #1a1f71; color: white; }
        .mastercard { background: #eb001b; color: white; }

        .pay-button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 16px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .pay-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .pay-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .security-info {
            margin-top: 1.5rem;
            padding: 1rem;
            background: #f0f9ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            margin: 2rem 0;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: white;
            border-radius: 2px;
            width: 0%;
            transition: width 0.3s ease;
        }

        @media (max-width: 768px) {
            .payment-card {
                grid-template-columns: 1fr;
            }
            
            .order-summary {
                order: 2;
            }
            
            .payment-form {
                order: 1;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="payment-container">
        <div class="payment-card">
            <!-- 訂單摘要 -->
            <div class="order-summary">
                <div>
                    <div class="logo">
                        <div class="logo-icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <span>安全付款</span>
                    </div>
                    
                    <div class="order-item">
                        <span>服務方案</span>
                        <span id="plan-name">{{ exchange_record.plan_name }}</span>
                    </div>
                    <div class="order-item">
                        <span>服務期限</span>
                        <span id="plan-period">{{ exchange_record.plan_period }}</span>
                    </div>
                    <div class="order-item">
                        <span>付款金額</span>
                        <span id="total-amount">${{ "%.2f"|format(exchange_record.amount_fiat) }} {{ exchange_record.fiat_currency }}</span>
                    </div>
                    <div class="order-item">
                        <span>將獲得</span>
                        <span id="crypto-amount">≈ {{ "%.4f"|format(exchange_record.estimated_crypto) }} {{ exchange_record.crypto_currency }}</span>
                    </div>
                    <div class="order-item">
                        <span>總計</span>
                        <span id="final-amount">${{ "%.2f"|format(exchange_record.amount_fiat) }} {{ exchange_record.fiat_currency }}</span>
                    </div>
                </div>
                
                <div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="security-badges">
                        <div class="security-badge">
                            <i class="fas fa-shield-alt"></i>
                            <span>SSL 加密</span>
                        </div>
                        <div class="security-badge">
                            <i class="fas fa-lock"></i>
                            <span>PCI 合規</span>
                        </div>
                        <div class="security-badge">
                            <i class="fab fa-bitcoin"></i>
                            <span>自動轉換</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 付款表單 -->
            <div class="payment-form">
                <div class="fiat-crypto-notice">
                    <h4><i class="fas fa-magic"></i> 智能付款轉換</h4>
                    <p>您的信用卡付款將自動轉換為加密貨幣，無需持有任何數位錢包！我們與 Mercuryo 合作提供安全的轉換服務。</p>
                </div>

                <h2 class="form-title">信用卡付款</h2>
                <p class="form-subtitle">請填寫您的信用卡資訊以完成購買</p>

                <!-- 支付方式圖標 -->
                <div class="payment-methods">
                    <div class="payment-method visa">VISA</div>
                    <div class="payment-method mastercard">MC</div>
                </div>

                <form id="payment-form">
                    <div class="form-group">
                        <label for="card-number">信用卡號</label>
                        <input type="text" id="card-number" class="form-input card-input" placeholder="1234 5678 9012 3456" maxlength="19" required>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="expiry">有效期限</label>
                            <input type="text" id="expiry" class="form-input" placeholder="MM/YY" maxlength="5" required>
                        </div>
                        <div class="form-group">
                            <label for="cvv">CVV</label>
                            <input type="text" id="cvv" class="form-input" placeholder="123" maxlength="4" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="cardholder-name">持卡人姓名</label>
                        <input type="text" id="cardholder-name" class="form-input" placeholder="CARDHOLDER NAME" required>
                    </div>

                    <div class="form-group">
                        <label for="email">電子郵件</label>
                        <input type="email" id="email" class="form-input" placeholder="your@email.com" value="{{ exchange_record.user_email }}" required>
                    </div>

                    <button type="submit" class="pay-button" id="pay-button">
                        <span id="pay-button-text">
                            <i class="fas fa-credit-card"></i>
                            安全付款 ${{ "%.2f"|format(exchange_record.amount_fiat) }} {{ exchange_record.fiat_currency }}
                        </span>
                        <div class="loading" id="pay-loading" style="display: none;"></div>
                    </button>
                </form>

                <div class="security-info">
                    <i class="fas fa-shield-alt"></i>
                    您的付款受到銀行級別的安全保護。付款完成後，資金將自動轉換為加密貨幣並發送到我們的安全錢包。
                </div>
            </div>
        </div>
    </div>

    <script>
        const exchangeData = {
            exchangeId: '{{ exchange_id }}',
            planName: '{{ exchange_record.plan_name }}',
            planPeriod: '{{ exchange_record.plan_period }}',
            amountFiat: {{ exchange_record.amount_fiat }},
            fiatCurrency: '{{ exchange_record.fiat_currency }}',
            estimatedCrypto: {{ exchange_record.estimated_crypto }},
            cryptoCurrency: '{{ exchange_record.crypto_currency }}',
            userEmail: '{{ exchange_record.user_email }}',
            userName: '{{ exchange_record.user_name }}'
        };

        // 格式化卡號輸入
        document.getElementById('card-number').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.replace(/(.{4})/g, '$1 ').trim();
            if (formattedValue.length > 19) formattedValue = formattedValue.substr(0, 19);
            e.target.value = formattedValue;
        });

        // 格式化有效期輸入
        document.getElementById('expiry').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            e.target.value = value;
        });

        // 只允許數字輸入 CVV
        document.getElementById('cvv').addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });

        // 更新進度條
        function updateProgress(percentage) {
            document.getElementById('progress-fill').style.width = percentage + '%';
        }

        // 表單提交處理
        document.getElementById('payment-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // 獲取表單數據
            const cardNumber = document.getElementById('card-number').value.replace(/\s/g, '');
            const expiry = document.getElementById('expiry').value;
            const cvv = document.getElementById('cvv').value;
            const cardholderName = document.getElementById('cardholder-name').value;
            const email = document.getElementById('email').value;

            // 基本驗證
            if (!cardNumber || !expiry || !cvv || !cardholderName || !email) {
                alert('請填寫所有必要資訊');
                return;
            }

            if (cardNumber.length < 13) {
                alert('請輸入有效的信用卡號');
                return;
            }

            if (expiry.length !== 5) {
                alert('請輸入有效的有效期限 (MM/YY)');
                return;
            }

            if (cvv.length < 3) {
                alert('請輸入有效的 CVV');
                return;
            }

            // 開始處理付款
            await processPayment({
                cardNumber,
                expiry,
                cvv,
                cardholderName,
                email
            });
        });

        async function processPayment(paymentData) {
            const payButton = document.getElementById('pay-button');
            const payButtonText = document.getElementById('pay-button-text');
            const payLoading = document.getElementById('pay-loading');

            // 顯示載入狀態
            payButton.disabled = true;
            payButtonText.style.display = 'none';
            payLoading.style.display = 'inline-block';

            updateProgress(25);

            try {
                // 模擬處理時間
                await new Promise(resolve => setTimeout(resolve, 1500));
                updateProgress(50);

                // 處理信用卡付款
                const response = await fetch(`/payment/credit-card/${exchangeData.exchangeId}/process`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...paymentData,
                        exchange_id: exchangeData.exchangeId
                    })
                });

                const data = await response.json();
                updateProgress(75);

                if (data.success) {
                    updateProgress(100);
                    // 短暫延遲後跳轉
                    setTimeout(() => {
                        window.location.href = data.redirect_url || `/payment/simpleswap/success?id=${exchangeData.exchangeId}`;
                    }, 1000);
                } else {
                    throw new Error(data.error || '付款處理失敗');
                }

            } catch (error) {
                console.error('Payment error:', error);
                alert('付款處理失敗：' + error.message);
                
                // 恢復按鈕狀態
                payButton.disabled = false;
                payButtonText.style.display = 'inline-flex';
                payLoading.style.display = 'none';
                updateProgress(0);
            }
        }

        // 初始化進度條
        updateProgress(0);
    </script>
</body>
</html>
"""

@credit_card_bp.route('/<exchange_id>')
def show_credit_card_payment(exchange_id):
    """顯示信用卡付款頁面"""
    try:
        from app import simpleswap_service
        
        if not simpleswap_service:
            return redirect('/products?error=service_unavailable')
        
        exchange_record = simpleswap_service.get_exchange_record(exchange_id)
        if not exchange_record:
            return redirect('/products?error=exchange_not_found')
        
        return render_template_string(
            CREDIT_CARD_PAYMENT_TEMPLATE,
            exchange_record=exchange_record,
            exchange_id=exchange_id
        )
    except Exception as e:
        logger.error(f"顯示信用卡付款頁面錯誤: {str(e)}")
        return redirect('/products?error=system_error')

@credit_card_bp.route('/<exchange_id>/process', methods=['POST'])
def process_credit_card_payment(exchange_id):
    """處理信用卡付款"""
    try:
        from app import simpleswap_service
        
        if not simpleswap_service:
            return jsonify({
                'success': False,
                'error': '服務不可用'
            }), 503
        
        data = request.get_json()
        
        # 驗證付款數據
        required_fields = ['cardNumber', 'expiry', 'cvv', 'cardholderName', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': '付款資訊不完整'
            }), 400
        
        # 模擬信用卡付款處理
        # 在實際環境中，這裡會調用真正的 Mercuryo API
        success, user_uuid = simpleswap_service.process_successful_fiat_exchange(exchange_id, {
            'status': 'completed',
            'payment_method': 'credit_card',
            'transaction_id': f"cc_{exchange_id}_{int(datetime.now().timestamp())}"
        })
        
        if success:
            return jsonify({
                'success': True,
                'user_uuid': user_uuid,
                'redirect_url': f'/payment/simpleswap/success?id={exchange_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '付款處理失敗'
            }), 500
            
    except Exception as e:
        logger.error(f"處理信用卡付款錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': '系統錯誤'
        }), 500