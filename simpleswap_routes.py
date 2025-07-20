# 在 simpleswap_routes.py 文件中

# 首先，在文件頂部（其他模板定義之後）添加 SIMPLESWAP_WIDGET_TEMPLATE
# 在 simpleswap_routes.py 中修復 SIMPLESWAP_WIDGET_TEMPLATE

SIMPLESWAP_WIDGET_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>信用卡付款 - Scrilab</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* 保持原有樣式 */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0a; color: #ffffff; min-height: 100vh; display: flex; flex-direction: column; }
        .header { background: #1a1a1a; padding: 1.5rem 2rem; border-bottom: 1px solid #333; text-align: center; }
        .header h1 { font-size: 1.5rem; font-weight: 600; color: #00d4ff; }
        .container { flex: 1; max-width: 1200px; width: 100%; margin: 0 auto; padding: 2rem; }
        .payment-info { background: #1e1e1e; border: 1px solid #333; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; }
        .info-row { display: flex; justify-content: space-between; padding: 0.8rem 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        .info-row:last-child { border-bottom: none; }
        .widget-container { background: white; border-radius: 16px; padding: 2px; min-height: 600px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.35); }
        .loading { display: flex; align-items: center; justify-content: center; height: 600px; font-size: 1.2rem; color: #666; }
        .back-link { display: inline-flex; align-items: center; gap: 0.5rem; color: #00d4ff; text-decoration: none; margin-top: 2rem; padding: 0.8rem 1.5rem; border: 1px solid #333; border-radius: 8px; transition: all 0.3s; }
        .back-link:hover { border-color: #00d4ff; background: rgba(0, 212, 255, 0.1); }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-shield-alt"></i> Scrilab 安全付款</h1>
    </div>

    <div class="container">
        <div class="payment-info">
            <h2 style="margin-bottom: 1rem;">訂單詳情</h2>
            <div class="info-row">
                <span>服務方案</span>
                <span>{{ exchange_record.plan_name }}</span>
            </div>
            <div class="info-row">
                <span>服務期限</span>
                <span>{{ exchange_record.plan_period }}</span>
            </div>
            <div class="info-row">
                <span>付款金額</span>
                <span>${{ "%.2f"|format(exchange_record.amount_fiat) }} USD (≈ NT$ {{ exchange_record.amount_twd }})</span>
            </div>
            <div class="info-row">
                <span>預計獲得</span>
                <span>{{ "%.4f"|format(exchange_record.estimated_crypto) }} USDT</span>
            </div>
        </div>

        <div class="widget-container">
            <div class="loading" id="loading">
                <i class="fas fa-spinner fa-spin"></i>&nbsp; 正在載入付款界面...
            </div> 
            <!-- 修復後的正確 Widget URL -->
            <iframe 
                id="simpleswap-widget"
                src="https://simpleswap.io/widget?from=usd&to=usdt&amount={{ exchange_record.amount_fiat }}&variant=fiat&theme=dark&partner_id={{ api_key }}"
                width="100%" 
                height="600"
                frameborder="0"
                style="border-radius: 14px; display: none;"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
            ></iframe>
        </div>

        <a href="/products" class="back-link">
            <i class="fas fa-arrow-left"></i>
            返回商品頁面
        </a>
    </div>

    <script>
        // 當 iframe 載入完成後
        document.getElementById('simpleswap-widget').onload = function() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('simpleswap-widget').style.display = 'block';
        };

        // 設置超時檢查
        setTimeout(() => {
            const iframe = document.getElementById('simpleswap-widget');
            const loading = document.getElementById('loading');
            if (iframe.style.display === 'none') {
                loading.innerHTML = `
                    <div style="text-align: center;">
                        <i class="fas fa-exclamation-triangle" style="color: #f59e0b; font-size: 3rem; margin-bottom: 1rem;"></i>
                        <h3 style="color: #f59e0b; margin-bottom: 1rem;">Widget 載入超時</h3>
                        <p style="margin-bottom: 2rem;">SimpleSwap Widget 可能暫時不可用</p>
                        <a href="/payment/credit-card/{{ exchange_id }}" style="background: #00d4ff; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                            <i class="fas fa-credit-card"></i> 使用備用付款方式
                        </a>
                    </div>
                `;
            }
        }, 15000);

        // 監聽 Widget 消息
        window.addEventListener('message', function(event) {
            console.log('Widget message:', event.data);
            
            // 處理交換完成事件
            if (event.data && (event.data.type === 'exchange-created' || event.data.exchangeId)) {
                const exchangeId = event.data.exchangeId || event.data.id;
                if (exchangeId) {
                    // 通知後端交換已創建
                    fetch('/payment/simpleswap/webhook', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: exchangeId,
                            status: 'waiting',
                            internal_id: '{{ exchange_id }}'
                        })
                    }).then(() => {
                        // 延遲重定向到成功頁面
                        setTimeout(() => {
                            window.location.href = `/payment/simpleswap/success?id={{ exchange_id }}`;
                        }, 2000);
                    });
                }
            }
        });
    </script>
</body>
</html>
"""

# SimpleSwap 付款詳情頁面模板
SIMPLESWAP_PAYMENT_DETAILS_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>完成付款 - Scrilab</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-card: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-muted: #808080;
            --accent-blue: #00d4ff;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --border-color: #333333;
            --gradient-brand: linear-gradient(135deg, #8b5cf6 0%, #00d4ff 100%);
            --shadow-lg: 0 15px 35px rgba(0, 0, 0, 0.35);
            --border-radius: 16px;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .payment-container {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            max-width: 600px;
            width: 100%;
            padding: 3rem;
            text-align: center;
            box-shadow: var(--shadow-lg);
        }

        .step-indicator {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .step {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            border: 2px solid var(--border-color);
            color: var(--text-muted);
        }

        .step.active {
            background: var(--gradient-brand);
            border-color: var(--accent-blue);
            color: white;
        }

        .step.completed {
            background: var(--accent-green);
            border-color: var(--accent-green);
            color: white;
        }

        .payment-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .payment-subtitle {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .payment-info {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .crypto-address {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            margin: 1rem 0;
            color: var(--accent-green);
        }

        .warning-box {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            color: var(--accent-orange);
        }

        .btn {
            padding: 1rem 2rem;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1rem;
            border: none;
            margin: 0.5rem;
        }

        .btn-primary {
            background: var(--gradient-brand);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .status-pending {
            color: var(--accent-orange);
        }

        .status-completed {
            color: var(--accent-green);
        }

        @media (max-width: 600px) {
            .payment-container {
                padding: 2rem;
            }
            
            .payment-title {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="payment-container">
        <div class="step-indicator">
            <div class="step completed">1</div>
            <div style="width: 2rem; height: 2px; background: var(--accent-green);"></div>
            <div class="step active">2</div>
            <div style="width: 2rem; height: 2px; background: var(--border-color);"></div>
            <div class="step">3</div>
        </div>
        
        <h1 class="payment-title">完成您的付款</h1>
        <p class="payment-subtitle">請按照以下說明完成加密貨幣付款</p>
        
        <div class="payment-info">
            <div class="info-row">
                <span>服務方案</span>
                <span>{{ exchange_record.plan_name }}</span>
            </div>
            <div class="info-row">
                <span>付款金額</span>
                <span>{{ "%.2f"|format(exchange_record.amount_fiat if exchange_record.amount_fiat else exchange_record.amount_usd) }} {{ exchange_record.fiat_currency if exchange_record.fiat_currency else 'USD' }}</span>
            </div>
            <div class="info-row">
                <span>預計收到</span>
                <span>{{ "%.4f"|format(exchange_record.estimated_crypto) }} {{ exchange_record.crypto_currency if exchange_record.crypto_currency else 'USDT' }}</span>
            </div>
            <div class="info-row">
                <span>付款狀態</span>
                <span class="status-pending">
                    <i class="fas fa-clock"></i>
                    等待付款
                </span>
            </div>
        </div>
        
        <div class="payment-instructions">
            <h3 style="margin-bottom: 1rem; color: var(--accent-blue);">
                <i class="fab fa-bitcoin"></i>
                付款說明
            </h3>
            
            {% if exchange_record.payment_address %}
            <p style="margin-bottom: 1rem;">請發送 <strong>{{ "%.6f"|format(exchange_record.amount_btc if exchange_record.amount_btc else 0.001) }} {{ exchange_record.currency_from.upper() }}</strong> 到以下地址：</p>
            
            <div class="crypto-address">
                {{ exchange_record.payment_address }}
                <button onclick="copyAddress()" style="margin-left: 1rem; padding: 0.5rem; background: var(--accent-blue); border: none; border-radius: 4px; color: white; cursor: pointer;">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
            {% endif %}
            
            <div class="warning-box">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>重要提醒：</strong>
                <ul style="margin-top: 0.5rem; text-align: left;">
                    <li>請確保發送正確的金額和貨幣類型</li>
                    <li>付款後通常需要 10-30 分鐘確認</li>
                    <li>確認後您將收到序號郵件</li>
                </ul>
            </div>
        </div>
        
        <div style="margin-top: 2rem;">
            <button class="btn btn-primary" onclick="checkPaymentStatus()">
                <i class="fas fa-refresh"></i>
                <span>檢查付款狀態</span>
            </button>
            <a href="/products" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
        
        <div style="margin-top: 2rem; font-size: 0.9rem; color: var(--text-muted);">
            <p>付款將通過 SimpleSwap 安全處理，支持多種加密貨幣。</p>
        </div>
    </div>

    <script>
        const exchangeId = "{{ exchange_id }}";
        
        function copyAddress() {
            const address = "{{ exchange_record.payment_address }}";
            navigator.clipboard.writeText(address).then(() => {
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            });
        }
        
        async function checkPaymentStatus() {
            try {
                const response = await fetch('/api/check-simpleswap-payment-status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ exchange_id: exchangeId })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (data.status === 'completed' && data.user_uuid) {
                        window.location.href = `/payment/simpleswap/success?id=${exchangeId}`;
                    } else if (data.status === 'processing') {
                        alert('付款正在處理中，請稍候...');
                    } else {
                        alert('尚未收到付款，請確認是否已完成轉帳');
                    }
                } else {
                    alert('查詢付款狀態失敗');
                }
            } catch (error) {
                alert('查詢失敗，請稍後再試');
            }
        }
        
        // 自動輪詢付款狀態
        setInterval(() => {
            checkPaymentStatus();
        }, 30000); // 每30秒檢查一次
    </script>
</body>
</html>
"""

# 在文件最後添加這個模板
MERCURYO_MOCK_PAYMENT_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>信用卡付款 - Mercuryo</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem; }
        .payment-container { background: white; border-radius: 16px; max-width: 500px; width: 100%; padding: 2.5rem; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2); }
        .mercuryo-logo { text-align: center; margin-bottom: 2rem; }
        .mercuryo-logo h1 { font-size: 1.8rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem; }
        .payment-info { background: #f8f9fa; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 0.8rem; }
        .form-group { margin-bottom: 1.5rem; }
        .form-input { width: 100%; padding: 12px 16px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 1rem; }
        .form-row { display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; }
        .pay-button { width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 16px; font-size: 1rem; font-weight: 600; cursor: pointer; }
        .loading { display: none; text-align: center; padding: 2rem; }
        .spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="payment-container">
        <div class="mercuryo-logo">
            <h1><i class="fas fa-shield-alt"></i> Mercuryo</h1>
            <p>安全的加密貨幣付款處理</p>
        </div>

        <div class="payment-info">
            <div class="info-row"><span>商家</span><span>Scrilab</span></div>
            <div class="info-row"><span>服務</span><span>{{ exchange_record.plan_name }}</span></div>
            <div class="info-row"><span>付款金額</span><span>{{ "%.2f"|format(exchange_record.amount_fiat if exchange_record.amount_fiat else exchange_record.amount_usd) }} {{ exchange_record.fiat_currency if exchange_record.fiat_currency else 'USD' }}</span></div>
            <div class="info-row"><span>將獲得</span><span>{{ "%.4f"|format(exchange_record.estimated_crypto) }} {{ exchange_record.crypto_currency if exchange_record.crypto_currency else 'USDT' }}</span></div>
        </div>

        <form id="payment-form">
            <div class="form-group">
                <label>信用卡號</label>
                <input type="text" class="form-input" placeholder="1234 5678 9012 3456" maxlength="19" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>有效期限</label>
                    <input type="text" class="form-input" placeholder="MM/YY" maxlength="5" required>
                </div>
                <div class="form-group">
                    <label>CVV</label>
                    <input type="text" class="form-input" placeholder="123" maxlength="4" required>
                </div>
            </div>
            <div class="form-group">
                <label>持卡人姓名</label>
                <input type="text" class="form-input" placeholder="CARDHOLDER NAME" required>
            </div>
            <button type="submit" class="pay-button">
                <i class="fas fa-lock"></i> 安全付款 {{ "%.2f"|format(exchange_record.amount_fiat if exchange_record.amount_fiat else exchange_record.amount_usd) }} {{ exchange_record.fiat_currency if exchange_record.fiat_currency else 'USD' }}
            </button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>正在處理您的付款...</p>
            <p style="font-size: 0.8rem; margin-top: 0.5rem;">信用卡付款將自動轉換為加密貨幣</p>
        </div>
    </div>

    <script>
        const exchangeId = "{{ exchange_id }}";
        document.getElementById('payment-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            document.querySelector('.payment-container > :not(.loading)').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            
            setTimeout(async () => {
                try {
                    const response = await fetch(`/payment/mercuryo/mock/${exchangeId}/process`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ card_number: 'mock_card', amount: {{ exchange_record.amount_fiat if exchange_record.amount_fiat else exchange_record.amount_usd if exchange_record else 0 }} })
                    });
                    const data = await response.json();
                    if (data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        alert('付款失敗: ' + data.error);
                        location.reload();
                    }
                } catch (error) {
                    alert('付款處理錯誤: ' + error.message);
                    location.reload();
                }
            }, 3000);
        });
    </script>
</body>
</html>
"""
# simpleswap_routes.py - 修復版本，統一使用新的欄位名稱
import os
from flask import request, jsonify, render_template_string, redirect
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleSwapRoutes:
    """SimpleSwap 路由處理器"""
    
    def __init__(self, simpleswap_service):
        self.simpleswap_service = simpleswap_service
    

    def show_mercuryo_mock_payment(self, exchange_id):
        """顯示模擬的 Mercuryo 信用卡付款頁面"""
        try:
            exchange_record = self.simpleswap_service.get_exchange_record(exchange_id)
            if not exchange_record:
                return redirect('/products?error=exchange_not_found')
            
            return render_template_string(
                MERCURYO_MOCK_PAYMENT_TEMPLATE,
                exchange_record=exchange_record,
                exchange_id=exchange_id
            )
        except Exception as e:
            logger.error(f"顯示模擬付款頁面錯誤: {str(e)}")
            return redirect('/products?error=system_error')

    def process_mock_payment(self, exchange_id):
        """處理模擬付款"""
        try:
            success, user_uuid = self.simpleswap_service.process_successful_fiat_exchange(exchange_id, {
                'status': 'completed',
                'transaction_id': f"mock_tx_{exchange_id}"
            })
            
            if success:
                return jsonify({
                    'success': True,
                    'user_uuid': user_uuid,
                    'redirect_url': f'/payment/simpleswap/success?id={exchange_id}'
                })
            else:
                return jsonify({'success': False, 'error': '模擬付款處理失敗'}), 500
        except Exception as e:
            logger.error(f"處理模擬付款錯誤: {str(e)}")
            return jsonify({'success': False, 'error': '系統錯誤'}), 500

    def create_payment(self):
        """創建 SimpleSwap 信用卡付款"""
        try:
            data = request.get_json()
            plan_id = data.get('plan_id')
            user_info = data.get('user_info')
            
            # 驗證資料
            if not plan_id or not user_info:
                return jsonify({
                    'success': False,
                    'error': '缺少必要資料'
                }), 400
            
            if not user_info.get('name') or not user_info.get('email'):
                return jsonify({
                    'success': False,
                    'error': '請填寫姓名和信箱'
                }), 400
            
            # 方案資料
            plans = {
                'trial_7': {
                    'id': 'trial_7',
                    'name': '體驗服務',
                    'price': 5,
                    'period': '7天'
                },
                'monthly_30': {
                    'id': 'monthly_30',
                    'name': '標準服務',
                    'price': 599,
                    'period': '30天'
                },
                'quarterly_90': {
                    'id': 'quarterly_90',
                    'name': '季度服務',
                    'price': 1499,
                    'period': '90天'
                }
            }
            
            plan_info = plans.get(plan_id)
            if not plan_info:
                return jsonify({
                    'success': False,
                    'error': '無效的方案'
                }), 400
            
            # 創建 SimpleSwap 交換
            exchange_result = self.simpleswap_service.create_fiat_to_crypto_exchange(plan_info, user_info)
            if exchange_result and exchange_result['success']:
                return jsonify({
                    'success': True,
                    'payment_url': exchange_result['payment_url'],
                    'exchange_id': exchange_result['exchange_id'],
                    'order_id': exchange_result['order_id'],
                    'amount_usd': exchange_result['amount_usd'],
                    'amount_twd': exchange_result['amount_twd'],
                    'amount_fiat': exchange_result.get('amount_fiat', exchange_result['amount_usd']),
                    'fiat_currency': exchange_result.get('fiat_currency', 'USD'),
                    'estimated_crypto': exchange_result.get('estimated_crypto', exchange_result['amount_usd']),
                    'crypto_currency': exchange_result.get('crypto_currency', 'USDT'),
                    'expires_at': exchange_result['expires_at'],
                    'payment_method': 'credit_card_to_crypto'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '付款創建失敗，請稍後再試'
                }), 500
                
        except Exception as e:
            logger.error(f"創建 SimpleSwap 付款錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤，請稍後再試'
            }), 500
    
    def webhook_handler(self):
        """SimpleSwap Webhook 處理"""
        try:
            # 獲取 Webhook 數據
            if request.content_type == 'application/json':
                webhook_data = request.get_json()
            else:
                webhook_data = request.form.to_dict()
            
            logger.info(f"收到 SimpleSwap Webhook: {webhook_data}")
            
            # 處理 Webhook
            success, user_uuid = self.simpleswap_service.handle_webhook(webhook_data)
            
            if success:
                return jsonify({
                    'status': 'ok',
                    'message': 'Webhook processed successfully'
                }), 200
            else:
                logger.error("Webhook 處理失敗")
                return jsonify({
                    'status': 'error',
                    'message': 'Webhook processing failed'
                }), 400
                
        except Exception as e:
            logger.error(f"處理 SimpleSwap Webhook 錯誤: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500
    
    def payment_success(self):
        """SimpleSwap 付款成功頁面"""
        try:
            exchange_id = request.args.get('id')
            
            if not exchange_id:
                return redirect('/products?error=missing_exchange_id')
            
            # 查詢交換記錄
            exchange_record = self.simpleswap_service.get_exchange_record(exchange_id)
            
            if not exchange_record:
                return redirect('/products?error=exchange_not_found')
            
            # 檢查交換狀態
            if exchange_record['status'] != 'completed':
                # 查詢最新狀態
                exchange_info = self.simpleswap_service.get_exchange_status(exchange_id)
                if exchange_info and exchange_info.get('status') == 'finished':
                    # 處理成功交換
                    success, user_uuid = self.simpleswap_service.process_successful_fiat_exchange(exchange_id, exchange_info)
                    if success:
                        exchange_record['user_uuid'] = user_uuid
                        exchange_record['status'] = 'completed'
                    else:
                        return redirect('/products?error=exchange_processing_failed')
                else:
                    return redirect('/products?error=exchange_not_completed')
            
            # 渲染成功頁面
            return render_template_string(
                SIMPLESWAP_SUCCESS_TEMPLATE,
                success=True,
                user_uuid=exchange_record.get('user_uuid'),
                exchange_record=exchange_record
            )
            
        except Exception as e:
            logger.error(f"處理付款成功頁面錯誤: {str(e)}")
            return redirect('/products?error=system_error')
    
    def check_payment_status(self):
        """檢查付款狀態 API"""
        try:
            data = request.get_json()
            exchange_id = data.get('exchange_id')
            
            if not exchange_id:
                return jsonify({
                    'success': False,
                    'error': '缺少 exchange_id'
                }), 400
            
            # 查詢交換狀態
            exchange_info = self.simpleswap_service.get_exchange_status(exchange_id)
            exchange_record = self.simpleswap_service.get_exchange_record(exchange_id)
            
            if not exchange_record:
                return jsonify({
                    'success': False,
                    'error': '找不到交換記錄'
                }), 404
            
            # 更新狀態
            if exchange_info:
                status_mapping = {
                    'waiting': 'pending',
                    'confirming': 'confirming',
                    'exchanging': 'processing',
                    'finished': 'completed',
                    'failed': 'failed'
                }
                
                new_status = status_mapping.get(exchange_info.get('status'), 'unknown')
                
                if new_status != exchange_record.get('status'):
                    self.simpleswap_service.update_exchange_status(exchange_id, new_status)
                
                return jsonify({
                    'success': True,
                    'status': new_status,
                    'exchange_info': exchange_info,
                    'user_uuid': exchange_record.get('user_uuid')
                })
            else:
                return jsonify({
                    'success': True,
                    'status': exchange_record.get('status', 'unknown'),
                    'user_uuid': exchange_record.get('user_uuid')
                })
                
        except Exception as e:
            logger.error(f"檢查付款狀態錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤'
            }), 500

    def debug_currencies(self):
        """調試端點 - 獲取支援的貨幣列表"""
        try:
            currencies = self.simpleswap_service.get_supported_currencies()
            if currencies:
                # 查找 USDT 相關的貨幣
                usdt_currencies = [c for c in currencies if 'usdt' in c.get('symbol', '').lower()]
                btc_currencies = [c for c in currencies if c.get('symbol', '').lower() == 'btc']
                
                return jsonify({
                    'success': True,
                    'total_currencies': len(currencies),
                    'usdt_currencies': usdt_currencies[:10],  # 前 10 個 USDT 相關貨幣
                    'btc_currencies': btc_currencies,
                    'sample_currencies': currencies[:20]  # 前 20 個貨幣作為樣本
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '無法獲取貨幣列表'
                })
        except Exception as e:
            logger.error(f"調試貨幣列表錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤'
            }), 500

    def payment_details(self, exchange_id):
        """顯示付款詳情頁面"""
        try:
            # 查詢交換記錄
            exchange_record = self.simpleswap_service.get_exchange_record(exchange_id)
            
            if not exchange_record:
                return redirect('/products?error=exchange_not_found')
            
            # 渲染付款詳情頁面
            return render_template_string(
                SIMPLESWAP_PAYMENT_DETAILS_TEMPLATE,
                exchange_record=exchange_record,
                exchange_id=exchange_id
            )
            
        except Exception as e:
            logger.error(f"顯示付款詳情錯誤: {str(e)}")
            return redirect('/products?error=system_error')

    def show_widget_payment(self, exchange_id):
        """顯示 SimpleSwap Widget 付款頁面"""
        try:
            exchange_record = self.simpleswap_service.get_exchange_record(exchange_id)
            if not exchange_record:
                return redirect('/products?error=exchange_not_found')
            
            api_key = os.environ.get('SIMPLESWAP_API_KEY')
            
            return render_template_string(
                SIMPLESWAP_WIDGET_TEMPLATE,
                exchange_record=exchange_record,
                exchange_id=exchange_id,
                api_key=api_key
            )
        except Exception as e:
            logger.error(f"顯示 Widget 付款頁面錯誤: {str(e)}")
            return redirect('/products?error=system_error')

# SimpleSwap 付款成功頁面模板
SIMPLESWAP_SUCCESS_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>付款成功 - Scrilab</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-card: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-muted: #808080;
            --accent-green: #10b981;
            --accent-blue: #00d4ff;
            --accent-purple: #8b5cf6;
            --border-color: #333333;
            --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --gradient-brand: linear-gradient(135deg, #8b5cf6 0%, #00d4ff 100%);
            --shadow-lg: 0 15px 35px rgba(0, 0, 0, 0.35);
            --border-radius: 16px;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .success-container {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            max-width: 600px;
            width: 100%;
            padding: 3rem;
            text-align: center;
            box-shadow: var(--shadow-lg);
            animation: slideIn 0.6s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .success-icon {
            width: 80px;
            height: 80px;
            background: var(--gradient-success);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 2rem;
            font-size: 2.5rem;
            color: white;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .payment-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--gradient-brand);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 2rem;
        }

        .success-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            color: var(--accent-green);
        }

        .success-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 2.5rem;
        }

        .purchase-info {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2.5rem;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 1rem;
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            color: var(--text-secondary);
            font-weight: 500;
        }

        .info-value {
            color: var(--text-primary);
            font-weight: 600;
        }

        .uuid-section {
            background: var(--bg-primary);
            border: 2px solid var(--accent-blue);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .uuid-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--accent-blue);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .uuid-code {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 1.1rem;
            color: var(--accent-green);
            word-break: break-all;
            margin-bottom: 1rem;
        }

        .uuid-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }

        .btn {
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.95rem;
            border: none;
        }

        .btn-primary {
            background: var(--gradient-success);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.3);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            color: var(--text-primary);
            border-color: var(--accent-blue);
        }

        .email-notice {
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            font-size: 0.95rem;
            color: var(--accent-purple);
        }

        .contact-info {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 2rem;
        }

        .contact-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .contact-methods {
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .contact-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.95rem;
            transition: color 0.3s ease;
        }

        .contact-link:hover {
            color: var(--accent-blue);
        }

        .footer-note {
            margin-top: 2rem;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        @media (max-width: 600px) {
            .success-container {
                padding: 2rem;
            }
            
            .success-title {
                font-size: 2rem;
            }
            
            .uuid-actions {
                flex-direction: column;
            }
            
            .contact-methods {
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="success-container">
        <div class="success-icon">
            <i class="fas fa-check"></i>
        </div>
        
        <div class="payment-badge">
            <i class="fas fa-credit-card"></i>
            <span>SimpleSwap 信用卡付款</span>
        </div>
        
        <h1 class="success-title">付款成功！</h1>
        <p class="success-subtitle">感謝您使用信用卡購買 Scrilab Artale 遊戲技術服務</p>
        
        <div class="purchase-info">
            <div class="info-row">
                <span class="info-label">服務方案</span>
                <span class="info-value">{{ exchange_record.plan_name if exchange_record else 'N/A' }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">服務期限</span>
                <span class="info-value">{{ exchange_record.plan_period if exchange_record else 'N/A' }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">付款金額</span>
                <span class="info-value">
                    {{ "%.2f"|format(exchange_record.amount_fiat) if exchange_record.amount_fiat else "%.2f"|format(exchange_record.amount_usd) }} 
                    {{ exchange_record.fiat_currency if exchange_record.fiat_currency else 'USD' }}
                    <small style="color: var(--text-muted); margin-left: 0.5rem;">
                        (≈ NT$ {{ exchange_record.amount_twd if exchange_record else 'N/A' }})
                    </small>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">收到金額</span>
                <span class="info-value">
                    <span style="color: var(--accent-green); font-family: 'Courier New', monospace;">
                        {{ "%.4f"|format(exchange_record.estimated_crypto) if exchange_record else 'N/A' }} 
                        {{ exchange_record.crypto_currency if exchange_record.crypto_currency else 'USDT' }}
                    </span>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">付款方式</span>
                <span class="info-value">SimpleSwap 信用卡自動轉換</span>
            </div>
            <div class="info-row">
                <span class="info-label">付款時間</span>
                <span class="info-value">{{ exchange_record.created_at.strftime('%Y-%m-%d %H:%M') if exchange_record and exchange_record.created_at else 'N/A' }}</span>
            </div>
        </div>
        
        <div class="uuid-section">
            <div class="uuid-title">
                <i class="fas fa-key"></i>
                <span>您的專屬序號</span>
            </div>
            <div class="uuid-code">{{ user_uuid if user_uuid else 'N/A' }}</div>
            <div class="uuid-actions">
                <button class="btn btn-primary" onclick="copyUUID()">
                    <i class="fas fa-copy"></i>
                    <span>複製序號</span>
                </button>
                <button class="btn btn-secondary" onclick="downloadInfo()">
                    <i class="fas fa-download"></i>
                    <span>下載訊息</span>
                </button>
            </div>
        </div>
        
        <div class="email-notice">
            <i class="fas fa-envelope"></i>
            <span>詳細的服務訊息和序號已發送至您的信箱，請查收。</span>
        </div>
        
        <div class="contact-info">
            <h3 class="contact-title">需要協助？</h3>
            <div class="contact-methods">
                <a href="https://discord.gg/HPzNrQmN" target="_blank" class="contact-link">
                    <i class="fab fa-discord"></i>
                    <span>Discord 技術支援</span>
                </a>
                <a href="mailto:scrilabstaff@gmail.com" class="contact-link">
                    <i class="fas fa-envelope"></i>
                    <span>Email 客服</span>
                </a>
                <a href="/manual" class="contact-link">
                    <i class="fas fa-book"></i>
                    <span>查看操作手冊</span>
                </a>
            </div>
        </div>
        
        <div style="margin-top: 2rem;">
            <a href="/products" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
        
        <p class="footer-note">
            感謝您選擇信用卡付款！您的付款已通過 SimpleSwap 安全處理並自動轉換為加密貨幣。
        </p>
    </div>

    <script>
        function copyUUID() {
            const uuid = "{{ user_uuid if user_uuid else '' }}";
            if (uuid) {
                navigator.clipboard.writeText(uuid).then(() => {
                    const btn = event.target.closest('button');
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<i class="fas fa-check"></i><span>已複製</span>';
                    btn.style.background = 'var(--gradient-success)';
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.style.background = 'var(--gradient-success)';
                    }, 2000);
                }).catch(err => {
                    alert('複製失敗，請手動複製序號');
                });
            }
        }

        function downloadInfo() {
            const uuid = "{{ user_uuid if user_uuid else '' }}";
            const planName = "{{ exchange_record.plan_name if exchange_record else 'N/A' }}";
            const planPeriod = "{{ exchange_record.plan_period if exchange_record else 'N/A' }}";
            const amountFiat = "{{ '%.2f'|format(exchange_record.amount_fiat) if exchange_record and exchange_record.amount_fiat else '%.2f'|format(exchange_record.amount_usd) if exchange_record else 'N/A' }}";
            const fiatCurrency = "{{ exchange_record.fiat_currency if exchange_record and exchange_record.fiat_currency else 'USD' }}";
            const amountTwd = "{{ exchange_record.amount_twd if exchange_record else 'N/A' }}";
            const estimatedCrypto = "{{ '%.4f'|format(exchange_record.estimated_crypto) if exchange_record else 'N/A' }}";
            const cryptoCurrency = "{{ exchange_record.crypto_currency if exchange_record and exchange_record.crypto_currency else 'USDT' }}";
            
            const content = `Scrilab Artale 服務購買成功

服務方案：${planName}
服務期限：${planPeriod}
付款金額：${amountFiat} ${fiatCurrency} (≈ NT$ ${amountTwd})
收到金額：${estimatedCrypto} ${cryptoCurrency}
付款方式：SimpleSwap 信用卡自動轉換
專屬序號：${uuid}

請妥善保管您的序號，避免外洩給他人使用。

操作手冊：請訪問 /manual 查看詳細使用說明

技術支援：
- Discord：https://discord.gg/
const content = `Scrilab Artale 服務購買成功

服務方案：${planName}
服務期限：${planPeriod}
付款金額：${amountFiat} ${fiatCurrency} (≈ NT$ ${amountTwd})
收到金額：${estimatedCrypto} ${cryptoCurrency}
付款方式：SimpleSwap 信用卡自動轉換
專屬序號：${uuid}

請妥善保管您的序號，避免外洩給他人使用。

操作手冊：請訪問 /manual 查看詳細使用說明

技術支援：
- Discord：https://discord.gg/HPzNrQmN
- Email：scrilabstaff@gmail.com

感謝您選擇信用卡付款方式！

Scrilab 技術團隊
${new Date().toLocaleDateString('zh-TW')}`;

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Scrilab_信用卡付款_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""