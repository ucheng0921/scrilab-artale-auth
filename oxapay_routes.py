# oxapay_routes.py - OxaPay 路由實現
from flask import request, jsonify, render_template_string, redirect
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class OxaPayRoutes:
    """OxaPay 路由處理器"""
    
    def __init__(self, oxapay_service):
        self.oxapay_service = oxapay_service
    
    def create_payment(self):
        """創建 OxaPay 付款"""
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
                    'price': 5,  # 降低體驗價格
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
            
            # 創建付款
            payment_result = self.oxapay_service.create_payment(plan_info, user_info)
            
            if payment_result and payment_result['success']:
                return jsonify({
                    'success': True,
                    'payment_url': payment_result['payment_url'],
                    'track_id': payment_result['track_id'],
                    'order_id': payment_result['order_id'],
                    'amount_usdt': payment_result['amount_usdt'],
                    'expires_at': payment_result['expires_at']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '付款創建失敗，請稍後再試'
                }), 500
                
        except Exception as e:
            logger.error(f"創建 OxaPay 付款錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤，請稍後再試'
            }), 500
    
    def payment_callback(self):
        """OxaPay 付款回調處理"""
        try:
            # 獲取回調數據
            if request.content_type == 'application/json':
                callback_data = request.get_json()
            else:
                callback_data = request.form.to_dict()
            
            logger.info(f"收到 OxaPay 回調: {callback_data}")
            
            # 處理回調
            success, user_uuid = self.oxapay_service.handle_callback(callback_data)
            
            if success:
                # 回調成功，返回 OK 狀態
                return jsonify({
                    'status': 'ok',
                    'message': 'Callback processed successfully'
                }), 200
            else:
                logger.error("回調處理失敗")
                return jsonify({
                    'status': 'error',
                    'message': 'Callback processing failed'
                }), 400
                
        except Exception as e:
            logger.error(f"處理 OxaPay 回調錯誤: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500
    
    def payment_success(self):
        """OxaPay 付款成功頁面"""
        try:
            provider = request.args.get('provider')
            track_id = request.args.get('trackId')
            
            if provider != 'oxapay':
                return redirect('/products?error=invalid_provider')
            
            if not track_id:
                return redirect('/products?error=missing_track_id')
            
            # 查詢付款記錄
            payment_record = self.oxapay_service.get_payment_record(track_id)
            
            if not payment_record:
                return redirect('/products?error=payment_not_found')
            
            # 檢查付款狀態
            if payment_record['status'] != 'completed':
                # 查詢最新狀態
                payment_info = self.oxapay_service.get_payment_info(track_id)
                if payment_info and payment_info.get('status') == 'Paid':
                    # 處理成功付款
                    success, user_uuid = self.oxapay_service.process_successful_payment(track_id, payment_info)
                    if success:
                        payment_record['user_uuid'] = user_uuid
                        payment_record['status'] = 'completed'
                    else:
                        return redirect('/products?error=payment_processing_failed')
                else:
                    return redirect('/products?error=payment_not_completed')
            
            # 渲染成功頁面
            return render_template_string(
                OXAPAY_SUCCESS_TEMPLATE,
                success=True,
                user_uuid=payment_record.get('user_uuid'),
                payment_record=payment_record
            )
            
        except Exception as e:
            logger.error(f"處理付款成功頁面錯誤: {str(e)}")
            return redirect('/products?error=system_error')
    
    def check_payment_status(self):
        """檢查付款狀態 API"""
        try:
            data = request.get_json()
            track_id = data.get('track_id')
            
            if not track_id:
                return jsonify({
                    'success': False,
                    'error': '缺少 track_id'
                }), 400
            
            # 查詢付款狀態
            payment_info = self.oxapay_service.get_payment_info(track_id)
            payment_record = self.oxapay_service.get_payment_record(track_id)
            
            if not payment_record:
                return jsonify({
                    'success': False,
                    'error': '找不到付款記錄'
                }), 404
            
            # 更新狀態
            if payment_info:
                status_mapping = {
                    'Waiting': 'pending',
                    'Confirming': 'confirming',
                    'Paid': 'completed',
                    'Expired': 'expired'
                }
                
                new_status = status_mapping.get(payment_info.get('status'), 'unknown')
                
                if new_status != payment_record.get('status'):
                    self.oxapay_service.update_payment_status(track_id, new_status)
                
                return jsonify({
                    'success': True,
                    'status': new_status,
                    'payment_info': payment_info,
                    'user_uuid': payment_record.get('user_uuid')
                })
            else:
                return jsonify({
                    'success': True,
                    'status': payment_record.get('status', 'unknown'),
                    'user_uuid': payment_record.get('user_uuid')
                })
                
        except Exception as e:
            logger.error(f"檢查付款狀態錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '系統錯誤'
            }), 500
    
    def get_exchange_rate(self):
        """獲取匯率 API"""
        try:
            from_currency = request.args.get('from', 'TWD')
            to_currency = request.args.get('to', 'USDT')
            
            rate = self.oxapay_service.get_exchange_rate(from_currency, to_currency)
            
            return jsonify({
                'success': True,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': rate,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"獲取匯率錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'error': '獲取匯率失敗'
            }), 500

# OxaPay 付款成功頁面模板
OXAPAY_SUCCESS_TEMPLATE = r"""
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
            --accent-crypto: #f7931a;
            --border-color: #333333;
            --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --gradient-crypto: linear-gradient(135deg, #f7931a 0%, #d97706 100%);
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

        .crypto-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--gradient-crypto);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 2rem;
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

        .crypto-amount {
            color: var(--accent-crypto);
            font-family: 'Courier New', monospace;
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
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            font-size: 0.95rem;
            color: var(--accent-blue);
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
        
        <div class="crypto-badge">
            <i class="fab fa-bitcoin"></i>
            <span>加密貨幣付款</span>
        </div>
        
        <h1 class="success-title">付款成功！</h1>
        <p class="success-subtitle">感謝您使用加密貨幣購買 Scrilab Artale 遊戲技術服務</p>
        
        <div class="purchase-info">
            <div class="info-row">
                <span class="info-label">服務方案</span>
                <span class="info-value">{{ payment_record.plan_name if payment_record else 'N/A' }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">服務期限</span>
                <span class="info-value">{{ payment_record.plan_period if payment_record else 'N/A' }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">付款金額</span>
                <span class="info-value">
                    <span class="crypto-amount">{{ "%.4f"|format(payment_record.amount_usdt) if payment_record else 'N/A' }} USDT</span>
                    <small style="color: var(--text-muted); margin-left: 0.5rem;">
                        (≈ NT$ {{ payment_record.amount_twd if payment_record else 'N/A' }})
                    </small>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">付款方式</span>
                <span class="info-value">OxaPay 加密貨幣</span>
            </div>
            <div class="info-row">
                <span class="info-label">付款時間</span>
                <span class="info-value">{{ payment_record.created_at.strftime('%Y-%m-%d %H:%M') if payment_record and payment_record.created_at else 'N/A' }}</span>
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
            感謝您選擇加密貨幣付款！請妥善保管您的序號，避免外洩給他人使用。
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
            const planName = "{{ payment_record.plan_name if payment_record else 'N/A' }}";
            const planPeriod = "{{ payment_record.plan_period if payment_record else 'N/A' }}";
            const amountUsdt = "{{ '%.4f'|format(payment_record.amount_usdt) if payment_record else 'N/A' }}";
            const amountTwd = "{{ payment_record.amount_twd if payment_record else 'N/A' }}";
            
            const content = `Scrilab Artale 服務購買成功

服務方案：${planName}
服務期限：${planPeriod}
付款金額：${amountUsdt} USDT (≈ NT$ ${amountTwd})
付款方式：OxaPay 加密貨幣
專屬序號：${uuid}

請妥善保管您的序號，避免外洩給他人使用。

操作手冊：請訪問 /manual 查看詳細使用說明

技術支援：
- Discord：https://discord.gg/HPzNrQmN
- Email：scrilabstaff@gmail.com

感謝您選擇加密貨幣付款方式！

Scrilab 技術團隊
${new Date().toLocaleDateString('zh-TW')}`;

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Scrilab_加密貨幣付款_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""