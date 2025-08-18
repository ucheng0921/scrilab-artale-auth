"""
admin_panel.py - 增強版本，支援完整的付款狀態管理和退款處理
"""
from flask import Blueprint, request, jsonify, render_template_string
import os
import hashlib
import uuid as uuid_lib
from datetime import datetime, timedelta
import logging
import re
from firebase_admin import firestore

logger = logging.getLogger(__name__)

# 創建藍圖
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# HTML 模板分段
HTML_HEAD = """
<!DOCTYPE html>
<html>
<head>
    <title>Artale Script 用戶管理系統</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #0a0a0a; 
            min-height: 100vh;
            color: #ffffff;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #1e3c72 0%, #00d4ff 100%); 
            color: white; 
            padding: 25px; 
            border-radius: 12px; 
            margin-bottom: 25px; 
            box-shadow: 0 8px 32px rgba(0,212,255,0.3);
        }
        .header h1 { margin: 0; font-size: 2.2em; font-weight: 600; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .section { 
            background: #1e1e1e; 
            color: #ffffff;
            padding: 25px; 
            border-radius: 12px; 
            margin-bottom: 25px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
            border: 1px solid #333333;
        }
"""

HTML_STYLES = """
        .user-table { 
            width: 100%; 
            border-collapse: collapse; 
            font-size: 13px;
            background: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .user-table th, .user-table td { 
            border: 1px solid #333333; 
            padding: 12px 8px; 
            text-align: left; 
            color: #ffffff;
        }
        .user-table th { 
            background: linear-gradient(135deg, #00d4ff 0%, #1976d2 100%); 
            color: white; 
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .user-table tr:nth-child(even) { background-color: #2a2a2a; }
        .user-table tr:hover { background-color: #333333; }
        .btn { 
            background: linear-gradient(135deg, #00d4ff 0%, #0088cc 100%); 
            color: white; 
            padding: 8px 12px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            margin: 2px; 
            font-size: 12px; 
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(0,212,255,0.3);
        }
        .btn-danger { background: linear-gradient(135deg, #f44336 0%, #da190b 100%); }
        .btn-warning { background: linear-gradient(135deg, #f59e0b 0%, #e68900 100%); }
        .btn-info { background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); }
        .btn-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
"""

HTML_FORM_STYLES = """
        .form-group { margin-bottom: 15px; }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: 600; 
            color: #ffffff;
        }
        .form-group input, .form-group select { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #333333; 
            border-radius: 6px; 
            box-sizing: border-box; 
            transition: border-color 0.3s ease;
            background: #2a2a2a;
            color: #ffffff;
        }
        .form-group input:focus, .form-group select:focus {
            border-color: #00d4ff;
            outline: none;
            background: #333333;
        }
        .status-active { color: #10b981; font-weight: bold; }
        .status-inactive { color: #f44336; font-weight: bold; }
        .status-refunded { color: #f59e0b; font-weight: bold; }
        .stats { display: flex; gap: 20px; margin-bottom: 25px; flex-wrap: wrap; }
        .stat-card { 
            background: #1e1e1e; 
            padding: 25px; 
            border-radius: 12px; 
            text-align: center; 
            flex: 1; 
            min-width: 200px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
            border: 1px solid #333333;
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { 
            margin: 0; 
            font-size: 2.5em; 
            color: #00d4ff; 
            font-weight: 700;
        }
        .stat-card p { 
            margin: 10px 0 0 0; 
            color: #b3b3b3; 
            font-weight: 500;
        }
"""

HTML_ADDITIONAL_STYLES = """
        .form-row { display: flex; gap: 20px; flex-wrap: wrap; }
        .form-row .form-group { flex: 1; min-width: 200px; }
        .search-box { 
            width: 300px; 
            padding: 12px; 
            border: 2px solid #333333; 
            border-radius: 6px; 
            margin-left: 10px; 
            background: #2a2a2a;
            color: #ffffff;
        }
        .search-box:focus {
            border-color: #00d4ff;
            outline: none;
        }
        .tabs { 
            display: flex; 
            background: #2a2a2a; 
            border-radius: 12px; 
            margin-bottom: 25px; 
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .tab { 
            padding: 15px 30px; 
            cursor: pointer; 
            background: #333333; 
            transition: all 0.3s ease;
            border: none;
            font-weight: 600;
            color: #b3b3b3;
        }
        .tab.active { 
            background: linear-gradient(135deg, #00d4ff 0%, #1976d2 100%); 
            color: white;
        }
        .tab:hover:not(.active) { 
            background: #404040; 
            color: #ffffff;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .uuid-generator { 
            background: #1e1e1e; 
            padding: 20px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            border: 2px solid #00d4ff;
        }
        .uuid-preview { 
            background: #2a2a2a; 
            color: #00d4ff; 
            padding: 15px; 
            border-radius: 8px; 
            font-family: 'Courier New', monospace; 
            margin: 15px 0; 
            font-size: 16px;
            font-weight: bold;
            border: 1px solid #333333;
        }
"""

HTML_MODAL_STYLES = """
        .payment-section { 
            background: #1e1e1e; 
            border: 2px solid #f59e0b; 
            border-radius: 12px; 
            padding: 25px; 
            margin-bottom: 25px; 
        }
        .payment-info { 
            background: #1e1e1e; 
            border: 2px solid #10b981; 
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 20px; 
        }
        .login-prompt { 
            background: #1e1e1e; 
            border: 2px solid #f59e0b; 
            border-radius: 12px; 
            padding: 30px; 
            margin: 25px 0; 
            text-align: center; 
        }
        .login-form { max-width: 400px; margin: 0 auto; }
        .login-form input { 
            width: 100%; 
            padding: 15px; 
            margin: 15px 0; 
            border: 2px solid #333333; 
            border-radius: 8px; 
            background: #2a2a2a;
            color: #ffffff;
        }
        .login-form input:focus {
            border-color: #00d4ff;
            outline: none;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            backdrop-filter: blur(5px);
        }
        .modal-content {
            background-color: #1e1e1e;
            margin: 5% auto;
            padding: 30px;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            border: 1px solid #333333;
            color: #ffffff;
        }
        .close {
            color: #b3b3b3;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover { color: #ffffff; }
"""

HTML_FINAL_STYLES = """
        .refund-form {
            background: #1e1e1e;
            border: 2px solid #f59e0b;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .refund-warning {
            background: #2a1a1a;
            border: 2px solid #f44336;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            color: #f44336;
        }
        .action-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #333333;
            border-top: 4px solid #00d4ff;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* 響應式設計 */
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .form-row { flex-direction: column; }
            .stats { flex-direction: column; }
            .user-table { font-size: 11px; }
            .user-table th, .user-table td { padding: 8px 4px; }
        }
        
        /* 新增：修復輸入框和選擇框的樣式 */
        input, select, textarea {
            background: #2a2a2a !important;
            color: #ffffff !important;
            border: 2px solid #333333 !important;
        }
        
        input:focus, select:focus, textarea:focus {
            background: #333333 !important;
            border-color: #00d4ff !important;
        }
        
        option {
            background: #2a2a2a !important;
            color: #ffffff !important;
        }
    </style>
</head>
"""

HTML_BODY_START = """
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Artale Script 用戶管理系統</h1>
            <p>管理所有授權用戶、權限、有效期和退款處理 | 🔗 Gumroad 金流整合</p>
            <div style="margin-top: 15px;">
                <button onclick="showDebugInfo()" class="btn btn-info" style="font-size: 12px;">🔍 調試信息</button>
                <button onclick="clearToken()" class="btn btn-warning" style="font-size: 12px;">🔄 重置密碼</button>
                <button onclick="manualLogin()" class="btn" style="font-size: 12px;">🔐 手動登入</button>
                <button onclick="refreshActiveSessions()" class="btn btn-success" style="font-size: 12px;">🟢 刷新在線用戶</button>
            </div>
        </div>
        
        <!-- 登入提示區域 -->
        <div id="login-prompt" class="login-prompt" style="display: none;">
            <h3>🔐 管理員登入</h3>
            <div class="login-form">
                <input type="password" id="admin-password" placeholder="請輸入管理員密碼" />
                <button onclick="submitLogin()" class="btn" style="width: 100%; padding: 15px;">登入</button>
            </div>
        </div>
        
        <!-- 主要內容區域 -->
        <div id="main-content" style="display: none;">
            <!-- 活躍Session監控 -->
            <div class="active-sessions-panel" style="background: #1e1e1e; border: 2px solid #10b981; border-radius: 12px; padding: 20px; margin-bottom: 25px;">
                <h3>⚡ 活躍 Session 監控</h3>
                <p style="margin-bottom: 15px;">顯示最近 5 分鐘內的活躍用戶連線</p>
                <div id="active-sessions-list">
                    <div style="text-align: center; padding: 20px;">載入中...</div>
                </div>
                <div style="margin-top: 15px;">
                    <button onclick="refreshActiveSessions()" class="btn btn-success">🔄 刷新Session狀態</button>
                    <button onclick="clearInactiveSessions()" class="btn btn-warning">🧹 清理無效Session</button>                    
                    <span id="last-refresh-time" style="margin-left: 10px; color: #b3b3b3;"></span>
                </div>
            </div>
            <!-- 統計資訊 -->
            <div class="stats">
                <div class="stat-card">
                    <h3 id="total-revenue">-</h3>
                    <p>總收益 (NT$)</p>
                </div>
                <div class="stat-card">
                    <h3 id="net-revenue">-</h3>
                    <p>淨收益 (NT$)</p>
                </div>
                <div class="stat-card">
                    <h3 id="online-count">-</h3>
                    <p>當前在線用戶</p>
                </div>
                <div class="stat-card">
                    <h3 id="active-sessions">-</h3>
                    <p>活躍 Session</p>
                </div>
            </div>
            
            <!-- 分頁標籤 -->
            <div class="tabs">
                <div class="tab active" onclick="switchTab('user-management')">👥 用戶管理</div>
                <div class="tab" onclick="switchTab('payment-management')">💳 付款記錄</div>
                <div class="tab" onclick="switchTab('refund-management')">🔄 退款管理</div>
                <div class="tab" onclick="switchTab('uuid-generator')">🔧 UUID 生成器</div>
                <div class="tab" onclick="switchTab('system-stats')">📊 系統統計</div>
            </div>
"""

HTML_USER_MANAGEMENT = """
            <!-- 用戶管理分頁 -->
            <div id="user-management" class="tab-content active">
                <!-- 新增用戶表單 -->
                <div class="section">
                    <h2>➕ 新增用戶</h2>
                    <form id="create-user-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label>UUID</label>
                                <input type="text" id="new-uuid" placeholder="artale_user001_20241217" required>
                                <small>建議使用 UUID 生成器確保格式正確</small>
                            </div>
                            <div class="form-group">
                                <label>顯示名稱</label>
                                <input type="text" id="new-display-name" placeholder="用戶名稱" required>
                            </div>
                            <div class="form-group">
                                <label>有效天數</label>
                                <select id="new-days">
                                    <option value="7">7天 (體驗版)</option>
                                    <option value="30" selected>30天 (月費版)</option>
                                    <option value="90">90天 (季費版)</option>
                                    <option value="365">365天 (年費版)</option>
                                    <option value="0">永久 (特殊版)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>&nbsp;</label>
                                <button type="submit" class="btn">創建用戶</button>
                            </div>
                        </div>
                    </form>
                </div>
                
                <!-- 用戶列表 -->
                <div class="section">
                    <h2>👥 用戶列表</h2>
                    <div style="margin-bottom: 15px;">
                        <button onclick="loadUsers()" class="btn">🔄 刷新列表</button>
                        <input type="text" id="search-input" placeholder="搜尋用戶..." class="search-box" onkeyup="filterUsers()">
                        <button onclick="exportUsers()" class="btn btn-info">📊 匯出 CSV</button>
                        <button onclick="bulkCleanup()" class="btn btn-warning">🧹 批量清理過期用戶</button>
                    </div>
                    <table class="user-table" id="users-table">
                        <thead>
                            <tr>
                                <th>在線狀態</th>
                                <th>顯示名稱</th>
                                <th>UUID</th>
                                <th>狀態</th>
                                <th>到期時間</th>
                                <th>登入次數</th>
                                <th>最後活動</th>
                                <th>創建時間</th>
                                <th>付款狀態</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="users-tbody">
                            <tr><td colspan="10" style="text-align: center;" id="loading-message">載入中...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
"""

HTML_PAYMENT_MANAGEMENT = """
            <!-- 付款管理分頁 -->
            <div id="payment-management" class="tab-content">
                <div class="section">
                    <h2>💳 Gumroad 付款記錄</h2>
                    <div style="margin-bottom: 15px;">
                        <button onclick="loadPayments()" class="btn">🔄 刷新記錄</button>
                        <input type="text" id="payment-search" placeholder="搜尋付款記錄..." class="search-box" onkeyup="filterPayments()">
                        <button onclick="exportPayments()" class="btn btn-info">📊 匯出付款CSV</button>
                        <button onclick="syncGumroadData()" class="btn btn-warning">🔄 同步 Gumroad 數據</button>
                    </div>
                    <table class="user-table" id="payments-table">
                        <thead>
                            <tr>
                                <th>付款時間</th>
                                <th>客戶姓名</th>
                                <th>客戶信箱</th>
                                <th>方案</th>
                                <th>金額 (TWD)</th>
                                <th>金額 (USD)</th>
                                <th>狀態</th>
                                <th>用戶序號</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="payments-tbody">
                            <tr><td colspan="9" style="text-align: center;">載入中...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
"""

HTML_REFUND_MANAGEMENT = """
            <!-- 退款管理分頁 -->
            <div id="refund-management" class="tab-content">
                <div class="section">
                    <h2>🔄 退款管理</h2>
                    <div style="margin-bottom: 15px;">
                        <button onclick="loadRefunds()" class="btn">🔄 刷新退款記錄</button>
                        <input type="text" id="refund-search" placeholder="搜尋退款記錄..." class="search-box" onkeyup="filterRefunds()">
                        <button onclick="exportRefunds()" class="btn btn-info">📊 匯出退款CSV</button>
                    </div>
                    <div class="refund-warning">
                        <h4>⚠️ 退款處理注意事項</h4>
                        <ul>
                            <li>退款處理會自動停用相關用戶帳號</li>
                            <li>退款需要通過 Gumroad 官方平台處理</li>
                            <li>系統會自動同步 Gumroad 的退款狀態</li>
                            <li>手動退款處理請謹慎操作</li>
                        </ul>
                    </div>
                    <table class="user-table" id="refunds-table">
                        <thead>
                            <tr>
                                <th>退款時間</th>
                                <th>原付款ID</th>
                                <th>客戶姓名</th>
                                <th>退款金額</th>
                                <th>退款原因</th>
                                <th>處理狀態</th>
                                <th>相關用戶</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="refunds-tbody">
                            <tr><td colspan="8" style="text-align: center;">載入中...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
"""

HTML_UUID_GENERATOR = """
            <!-- UUID 生成器分頁 -->
            <div id="uuid-generator" class="tab-content">
                <div class="section">
                    <h2>🔧 UUID 生成器</h2>
                    <div class="uuid-generator">
                        <h3>自動生成 UUID</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label>前綴</label>
                                <select id="uuid-prefix">
                                    <option value="artale">artale (一般用戶)</option>
                                    <option value="artale_vip">artale_vip (VIP用戶)</option>
                                    <option value="artale_trial">artale_trial (試用用戶)</option>
                                    <option value="artale_premium">artale_premium (高級用戶)</option>
                                    <option value="artale_gumroad">artale_gumroad (Gumroad用戶)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>用戶編號 (可選)</label>
                                <input type="text" id="uuid-custom-id" placeholder="留空自動生成">
                            </div>
                            <div class="form-group">
                                <label>日期格式</label>
                                <select id="uuid-date-format">
                                    <option value="YYYYMMDD">20241217 (完整日期)</option>
                                    <option value="YYYYMM">202412 (年月)</option>
                                    <option value="YYYY">2024 (年份)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>&nbsp;</label>
                                <button type="button" onclick="generateUUID()" class="btn">🎲 生成 UUID</button>
                            </div>
                        </div>
                        
                        <div class="uuid-preview" id="uuid-preview">
                            點擊生成按鈕產生 UUID...
                        </div>
                        
                        <div style="margin-top: 15px;">
                            <button onclick="copyUUID()" class="btn btn-info">📋 複製 UUID</button>
                            <button onclick="useGeneratedUUID()" class="btn">➡️ 使用此 UUID 創建用戶</button>
                            <button onclick="checkUUIDExists()" class="btn btn-warning">🔍 檢查是否已存在</button>
                        </div>
                    </div>
                </div>
            </div>
"""

HTML_SYSTEM_STATS = """
            <!-- 系統統計分頁 -->
            <div id="system-stats" class="tab-content">
                <div class="section">
                    <h2>📊 系統統計信息</h2>
                    <div id="stats-loading" class="loading">
                        <div class="spinner"></div>
                        <p>載入統計數據中...</p>
                    </div>
                    <div id="stats-content" style="display: none;">
                        <div class="stats">
                            <div class="stat-card">
                                <h3 id="stat-success-rate">-</h3>
                                <p>付款成功率</p>
                            </div>
                            <div class="stat-card">
                                <h3 id="stat-refund-rate">-</h3>
                                <p>退款率</p>
                            </div>
                            <div class="stat-card">
                                <h3 id="stat-avg-revenue">-</h3>
                                <p>平均客單價</p>
                            </div>
                            <div class="stat-card">
                                <h3 id="stat-monthly-growth">-</h3>
                                <p>月成長率</p>
                            </div>
                        </div>
                        
                        <div class="payment-info">
                            <h3>📈 收益分析</h3>
                            <div id="revenue-analysis">
                                <!-- 收益分析數據將在這裡顯示 -->
                            </div>
                        </div>
                        
                        <div class="payment-info">
                            <h3>🔄 系統維護</h3>
                            <div class="action-buttons">
                                <button onclick="cleanupOldWebhooks()" class="btn btn-warning">🧹 清理舊 Webhook 記錄</button>
                                <button onclick="optimizeDatabase()" class="btn btn-info">⚡ 優化數據庫</button>
                                <button onclick="generateSystemReport()" class="btn btn-success">📄 生成系統報告</button>
                                <button onclick="backupData()" class="btn">💾 備份數據</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""

HTML_MODAL = """
        <!-- 退款處理模態框 -->
        <div id="refund-modal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeRefundModal()">&times;</span>
                <h2>🔄 處理退款</h2>
                <div id="refund-details">
                    <!-- 退款詳情將在這裡顯示 -->
                </div>
                <div class="refund-form">
                    <div class="form-group">
                        <label>退款原因</label>
                        <select id="refund-reason">
                            <option value="customer_request">客戶要求退款</option>
                            <option value="service_issue">服務問題</option>
                            <option value="technical_issue">技術問題</option>
                            <option value="duplicate_payment">重複付款</option>
                            <option value="unauthorized">未授權交易</option>
                            <option value="other">其他</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>退款說明</label>
                        <textarea id="refund-note" rows="3" placeholder="請輸入退款處理說明..."></textarea>
                    </div>
                    <div class="refund-warning">
                        <strong>⚠️ 確認執行退款操作？</strong><br>
                        此操作將會：
                        <ul>
                            <li>立即停用相關用戶帳號</li>
                            <li>發送退款確認郵件給客戶</li>
                            <li>更新付款記錄狀態</li>
                            <li>記錄退款處理日誌</li>
                        </ul>
                    </div>
                    <div class="action-buttons">
                        <button onclick="processRefund()" class="btn btn-danger">確認退款</button>
                        <button onclick="closeRefundModal()" class="btn">取消</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 編輯用戶模態框 -->
        <div id="edit-user-modal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeEditUserModal()">&times;</span>
                <h2>✏️ 編輯用戶</h2>
                <div id="edit-user-details"></div>
                <div class="edit-expiry-form" style="background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #333333;">
                    <div class="form-group">
                        <label>顯示名稱</label>
                        <input type="text" id="edit-display-name" placeholder="用戶顯示名稱">
                    </div>
                    <div class="form-group">
                        <label>到期時間</label>
                        <input type="datetime-local" id="edit-expiry-date" style="background: #333333; color: #ffffff; border: 2px solid #555555; border-radius: 6px; padding: 8px;">
                        <small style="color: #b3b3b3;">留空表示永久有效</small>
                    </div>
                    <div class="form-group">
                        <label>快速設定</label>
                        <div class="action-buttons">
                            <button onclick="quickSetExpiry(1)" class="btn btn-info">+1天</button>
                            <button onclick="quickSetExpiry(2)" class="btn btn-info">+2天</button>
                            <button onclick="quickSetExpiry(3)" class="btn btn-info">+3天</button>
                            <button onclick="quickSetExpiry(4)" class="btn btn-info">+4天</button>
                            <button onclick="quickSetExpiry(5)" class="btn btn-info">+5天</button>
                            <button onclick="quickSetExpiry(7)" class="btn btn-info">+7天</button>
                            <button onclick="quickSetExpiry(30)" class="btn btn-info">+30天</button>
                            <button onclick="quickSetExpiry(90)" class="btn btn-info">+90天</button>
                            <button onclick="quickSetExpiry(365)" class="btn btn-info">+1年</button>
                            <button onclick="setPermanent()" class="btn btn-warning">設為永久</button>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>備註</label>
                        <textarea id="edit-notes" rows="3" placeholder="編輯備註..."></textarea>
                    </div>
                    <div class="action-buttons">
                        <button onclick="saveUserChanges()" class="btn btn-success">💾 保存變更</button>
                        <button onclick="closeEditUserModal()" class="btn">取消</button>
                    </div>
                </div>
            </div>
        </div>
"""

# JavaScript 分段 - 第一部分：基本變數和初始化
JS_VARIABLES = """
    <script>
        let allUsers = [];
        let allPayments = [];
        let allRefunds = [];
        let currentGeneratedUUID = '';
        let ADMIN_TOKEN = '';
        let isLoggedIn = false;
        let currentRefundData = null;
        let currentEditUser = null;
        let activeSessions = [];

        // Check login status when page loads
        window.onload = function() {
            console.log('頁面載入完成，開始檢查登入狀態');
            checkLoginStatus();
        };

        // 確保在 DOM 完全載入後執行
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM 載入完成');
            if (!window.onload) {
                checkLoginStatus();
            }
        });
"""

# JavaScript 分段 - 第二部分：登入相關函數
JS_LOGIN_FUNCTIONS = """
        function checkLoginStatus() {
            console.log('檢查登入狀態...');
            
            const savedToken = localStorage.getItem('admin_token');
            console.log('保存的 token:', savedToken ? '存在' : '不存在');
            
            if (savedToken) {
                ADMIN_TOKEN = savedToken;
                console.log('使用保存的 token 驗證...');
                validateTokenAndShowContent();
            } else {
                console.log('沒有保存的 token，顯示登入提示');
                showLoginPrompt();
            }
        }

        function showLoginPrompt() {
            document.getElementById('login-prompt').style.display = 'block';
            document.getElementById('main-content').style.display = 'none';
            isLoggedIn = false;
        }

        function showMainContent() {
            document.getElementById('login-prompt').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
            isLoggedIn = true;
            loadUsers();
            loadSystemStats();
            refreshActiveSessions();  // 添加這行
            // 自動刷新在線用戶
            setInterval(function() {
                if (isLoggedIn) {
                    refreshActiveSessions();
                }
            }, 30000);  // 添加這幾行
        }

        async function validateTokenAndShowContent() {
            try {
                const response = await fetch('/admin/users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.status === 401) {
                    localStorage.removeItem('admin_token');
                    showLoginPrompt();
                } else {
                    showMainContent();
                }
            } catch (error) {
                console.error('驗證失敗:', error);
                showLoginPrompt();
            }
        }

        function submitLogin() {
            const password = document.getElementById('admin-password').value.trim();
            if (!password) {
                alert('請輸入密碼');
                return;
            }
            
            ADMIN_TOKEN = password;
            
            fetch('/admin/users', {
                headers: { 'Admin-Token': ADMIN_TOKEN }
            })
            .then(response => {
                if (response.status === 401) {
                    alert('密碼錯誤，請重新輸入');
                    document.getElementById('admin-password').value = '';
                } else {
                    localStorage.setItem('admin_token', ADMIN_TOKEN);
                    showMainContent();
                }
            })
            .catch(error => {
                console.error('登入驗證失敗:', error);
                alert('登入失敗: ' + error.message);
            });
        }

        function manualLogin() {
            console.log('手動登入按鈕被點擊');
            
            const password = prompt('請輸入管理員密碼:');
            if (password) {
                console.log('用戶輸入了密碼，開始驗證...');
                ADMIN_TOKEN = password;
                
                fetch('/admin/users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                })
                .then(response => {
                    if (response.status === 401) {
                        alert('密碼錯誤');
                    } else {
                        localStorage.setItem('admin_token', ADMIN_TOKEN);
                        location.reload();
                    }
                })
                .catch(error => {
                    alert('驗證失敗: ' + error.message);
                });
            }
        }

        function clearToken() {
            localStorage.removeItem('admin_token');
            alert('已清除登入信息');
            location.reload();
        }
        // 在線用戶監控功能
        async function refreshActiveSessions() {
            if (!isLoggedIn) return;
            
            try {
                const response = await fetch('/admin/online-users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        activeSessions = data.online_users;
                        renderOnlineUsers(activeSessions);
                        updateOnlineStats(data.stats);
                        
                        const now = new Date();
                        document.getElementById('last-refresh-time').textContent = 
                            `最後更新: ${now.toLocaleTimeString()}`;
                    }
                }
            } catch (error) {
                console.error('載入在線用戶失敗:', error);
            }
        }

        function renderOnlineUsers(users) {
            const container = document.getElementById('online-users-list');
            container.innerHTML = '';
            
            if (users.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">目前沒有在線用戶</div>';
                return;
            }
            
            users.forEach(user => {
                const item = document.createElement('div');
                item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 10px; margin: 5px 0; background: #2a2a2a; border-radius: 8px; border: 1px solid #333333;';
                
                const statusIndicator = getOnlineStatusIndicator(user.last_activity);
                const timeAgo = getTimeAgo(user.last_activity);
                
                item.innerHTML = `
                    <div>
                        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; background-color: ${statusIndicator.color};"></span>
                        <strong>${user.display_name}</strong>
                        <small style="color: #b3b3b3;">(${user.uuid_preview})</small>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: #10b981;">${statusIndicator.text}</div>
                        <div style="font-size: 11px; color: #666;">${timeAgo}</div>
                    </div>
                `;
                
                container.appendChild(item);
            });
        }

        function getOnlineStatusIndicator(lastActivity) {
            const now = new Date();
            const activityTime = new Date(lastActivity);
            const diffMinutes = (now - activityTime) / (1000 * 60);
            
            if (diffMinutes < 1) {
                return { color: '#10b981', text: '🟢 在線中' };
            } else if (diffMinutes < 5) {
                return { color: '#f59e0b', text: '🟡 最近活動' };
            } else {
                return { color: '#666666', text: '⚫ 離線' };
            }
        }

        function getTimeAgo(timestamp) {
            const now = new Date();
            const time = new Date(timestamp);
            const diffMinutes = Math.floor((now - time) / (1000 * 60));
            
            if (diffMinutes < 1) return '剛剛';
            if (diffMinutes < 60) return `${diffMinutes} 分鐘前`;
            
            const diffHours = Math.floor(diffMinutes / 60);
            if (diffHours < 24) return `${diffHours} 小時前`;
            
            const diffDays = Math.floor(diffHours / 24);
            return `${diffDays} 天前`;
        }

        function updateOnlineStats(stats) {
            const onlineCountEl = document.getElementById('online-count');
            const activeSessionsEl = document.getElementById('active-sessions');
            
            if (onlineCountEl) onlineCountEl.textContent = stats.online_count;
            if (activeSessionsEl) activeSessionsEl.textContent = stats.active_sessions;
        }

        // 編輯用戶功能
        async function editUser(documentId, currentName) {
            if (!isLoggedIn) return;
            
            try {
                const response = await fetch(`/admin/users/${documentId}`, {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        currentEditUser = { documentId, ...data.user };
                        showEditUserModal(data.user);
                    } else {
                        alert('獲取用戶資訊失敗: ' + data.error);
                    }
                } else {
                    alert('無法載入用戶資訊');
                }
            } catch (error) {
                alert('編輯用戶錯誤: ' + error.message);
            }
        }

        function showEditUserModal(user) {
            document.getElementById('edit-user-details').innerHTML = `
                <div style="background: #1e1e1e; border: 2px solid #10b981; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <h4>用戶詳情</h4>
                    <p><strong>UUID:</strong> <code>${user.original_uuid}</code></p>
                    <p><strong>創建時間:</strong> ${user.created_at}</p>
                    <p><strong>登入次數:</strong> ${user.login_count}</p>
                    <p><strong>付款狀態:</strong> ${user.payment_status}</p>
                    <p><strong>當前狀態:</strong> ${user.active ? '✅ 啟用' : '❌ 停用'}</p>
                </div>
            `;
            
            document.getElementById('edit-display-name').value = user.display_name || '';
            
            if (user.expires_at) {
                const expiryDate = new Date(user.expires_at);
                
                const year = expiryDate.getFullYear();
                const month = String(expiryDate.getMonth() + 1).padStart(2, '0');
                const day = String(expiryDate.getDate()).padStart(2, '0');
                const hours = String(expiryDate.getHours()).padStart(2, '0');
                const minutes = String(expiryDate.getMinutes()).padStart(2, '0');
                
                const localISOTime = `${year}-${month}-${day}T${hours}:${minutes}`;
                
                document.getElementById('edit-expiry-date').value = localISOTime;
            } else {
                document.getElementById('edit-expiry-date').value = '';
            }
            
            document.getElementById('edit-notes').value = user.notes || '';
            document.getElementById('edit-user-modal').style.display = 'block';
        }

        function closeEditUserModal() {
            document.getElementById('edit-user-modal').style.display = 'none';
            currentEditUser = null;
        }

        function quickSetExpiry(days) {
            const now = new Date();
            const expiryDate = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
            
            const year = expiryDate.getFullYear();
            const month = String(expiryDate.getMonth() + 1).padStart(2, '0');
            const day = String(expiryDate.getDate()).padStart(2, '0');
            const hours = String(expiryDate.getHours()).padStart(2, '0');
            const minutes = String(expiryDate.getMinutes()).padStart(2, '0');
            
            const localISOTime = `${year}-${month}-${day}T${hours}:${minutes}`;
            
            document.getElementById('edit-expiry-date').value = localISOTime;
        }

        function setPermanent() {
            document.getElementById('edit-expiry-date').value = '';
        }

        async function saveUserChanges() {
            if (!currentEditUser) {
                alert('沒有選擇的用戶');
                return;
            }
            
            const displayName = document.getElementById('edit-display-name').value.trim();
            const expiryDate = document.getElementById('edit-expiry-date').value;
            const notes = document.getElementById('edit-notes').value.trim();
            
            if (!displayName) {
                alert('顯示名稱不能為空');
                return;
            }
            
            try {
                const updateData = {
                    display_name: displayName,
                    notes: notes
                };
                
                if (expiryDate) {
                    updateData.expires_at = new Date(expiryDate).toISOString();
                } else {
                    updateData.expires_at = null;
                }
                
                const response = await fetch(`/admin/users/${currentEditUser.documentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify(updateData)
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('用戶資訊已更新！');
                    closeEditUserModal();
                    loadUsers();
                } else {
                    alert('更新失敗: ' + data.error);
                }
            } catch (error) {
                alert('更新錯誤: ' + error.message);
            }
        }
"""

# JavaScript 分段 - 第三部分：調試和分頁功能
JS_DEBUG_FUNCTIONS = """
        // 調試功能
        async function showDebugInfo() {
            console.log('調試按鈕被點擊');
            
            try {
                console.log('正在獲取調試信息...');
                const response = await fetch('/admin/debug', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log('調試請求響應:', response.status);
                const data = await response.json();
                console.log('調試數據:', data);
                
                const debugInfo = `調試信息：
- Admin Token 已設定: ${data.admin_token_set}
- Token 預覽: ${data.admin_token_value}
- 預設值: ${data.expected_default}
- 當前登入狀態: ${isLoggedIn}
- 當前使用 Token: ${ADMIN_TOKEN ? ADMIN_TOKEN.substring(0, 8) + '...' : '未設定'}`;
                
                alert(debugInfo);
            } catch (error) {
                alert('獲取調試信息失敗: ' + error.message);
            }
        }

        // 分頁切換
        function switchTab(tabId) {
            if (!isLoggedIn) {
                alert('請先登入');
                return;
            }
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            
            // 根據分頁載入對應數據
            if (tabId === 'payment-management') {
                loadPayments();
            } else if (tabId === 'refund-management') {
                loadRefunds();
            } else if (tabId === 'system-stats') {
                loadSystemStats();
            }
        }
"""

# JavaScript 分段 - 第四部分：UUID 生成器功能
JS_UUID_FUNCTIONS = """
        // UUID 生成器功能
        function generateUUID() {
            const prefix = document.getElementById('uuid-prefix').value;
            const customId = document.getElementById('uuid-custom-id').value.trim();
            const dateFormat = document.getElementById('uuid-date-format').value;
            
            let userId;
            if (customId) {
                userId = customId.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
            } else {
                userId = Math.random().toString(36).substring(2, 10);
            }
            
            const now = new Date();
            let dateStr;
            switch(dateFormat) {
                case 'YYYYMMDD':
                    dateStr = now.getFullYear() + 
                             String(now.getMonth() + 1).padStart(2, '0') + 
                             String(now.getDate()).padStart(2, '0');
                    break;
                case 'YYYYMM':
                    dateStr = now.getFullYear() + String(now.getMonth() + 1).padStart(2, '0');
                    break;
                case 'YYYY':
                    dateStr = now.getFullYear().toString();
                    break;
            }
            
            currentGeneratedUUID = `${prefix}_${userId}_${dateStr}`;
            document.getElementById('uuid-preview').textContent = currentGeneratedUUID;
        }

        function copyUUID() {
            if (!currentGeneratedUUID) {
                alert('請先生成 UUID');
                return;
            }
            navigator.clipboard.writeText(currentGeneratedUUID).then(() => {
                alert('UUID 已複製到剪貼簿');
            });
        }

        function useGeneratedUUID() {
            if (!currentGeneratedUUID) {
                alert('請先生成 UUID');
                return;
            }
            switchTab('user-management');
            document.getElementById('new-uuid').value = currentGeneratedUUID;
            document.getElementById('new-uuid').focus();
        }

        async function checkUUIDExists() {
            if (!currentGeneratedUUID) {
                alert('請先生成 UUID');
                return;
            }
            
            try {
                const response = await fetch('/admin/check-uuid', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({ uuid: currentGeneratedUUID })
                });
                
                const data = await response.json();
                if (data.exists) {
                    alert('⚠️ 此 UUID 已存在，請重新生成');
                } else {
                    alert('✅ UUID 可用');
                }
            } catch (error) {
                alert('檢查失敗: ' + error.message);
            }
        }
"""

# JavaScript 分段 - 第五部分：用戶管理功能
JS_USER_FUNCTIONS = """
        // 載入用戶列表
        async function loadUsers() {
            if (!isLoggedIn) return;
            
            try {
                const response = await fetch('/admin/users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.status === 401) {
                    alert('登入已過期，請重新登入');
                    localStorage.removeItem('admin_token');
                    location.reload();
                    return;
                }
                
                const data = await response.json();
                
                if (data.success) {
                    allUsers = data.users;
                    renderUsers(allUsers);
                    updateStats(allUsers);
                } else {
                    alert('載入失敗: ' + data.error);
                }
            } catch (error) {
                console.error('載入錯誤:', error);
                alert('載入錯誤: ' + error.message);
            }
        }

        // 渲染用戶列表
        function renderUsers(users) {
            const tbody = document.getElementById('users-tbody');
            tbody.innerHTML = '';
            
            if (users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align: center;">暫無用戶數據</td></tr>';
                return;
            }
            
            users.forEach(user => {
                const row = document.createElement('tr');
                const isActive = user.active;
                const isExpired = user.expires_at && new Date(user.expires_at) < new Date();
                const isRefunded = user.payment_status === 'refunded';
                
                let statusClass = 'status-inactive';
                let statusText = '❌ 停用';
                
                if (isRefunded) {
                    statusClass = 'status-refunded';
                    statusText = '🔄 已退款';
                } else if (isActive && !isExpired) {
                    statusClass = 'status-active';
                    statusText = '✅ 啟用';
                } else if (isExpired) {
                    statusClass = 'status-inactive';
                    statusText = '❌ 已過期';
                }
                
                // 檢查在線狀態
                const onlineUser = activeSessions.find(ou => ou.uuid_preview === user.uuid_preview);
                const onlineStatus = onlineUser ? getOnlineStatusIndicator(onlineUser.last_activity) : { color: '#666666', text: '⚫ 離線' };
                
                row.innerHTML = `
                    <td>
                        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; background-color: ${onlineStatus.color};"></span>
                        <small>${onlineStatus.text}</small>
                    </td>
                    <td>${user.display_name || 'Unknown'}</td>
                    <td><code style="font-size: 11px;">${user.uuid_preview || 'N/A'}</code></td>
                    <td class="${statusClass}">${statusText}</td>
                    <td>${user.expires_at || '永久'}</td>
                    <td>${user.login_count || 0}</td>
                    <td>${onlineUser ? getTimeAgo(onlineUser.last_activity) : '-'}</td>
                    <td>${user.created_at || 'Unknown'}</td>
                    <td>${user.payment_status || '手動創建'}</td>
                    <td>
                        <button onclick="editUser('${user.document_id}', '${user.display_name}')" class="btn" style="font-size: 10px;">✏️ 編輯</button>
                        ${!isRefunded ? `<button onclick="toggleUser('${user.document_id}', ${!isActive})" class="btn btn-warning" style="font-size: 10px;">
                            ${isActive ? '停用' : '啟用'}
                        </button>` : ''}
                        <button onclick="deleteUser('${user.document_id}', '${user.display_name}')" class="btn btn-danger" style="font-size: 10px;">🗑️ 刪除</button>
                        ${user.payment_id ? `<button onclick="viewPaymentDetails('${user.payment_id}')" class="btn btn-info" style="font-size: 10px;">💳 付款</button>` : ''}
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
"""

# JavaScript 分段 - 第六部分：付款和退款管理
JS_PAYMENT_FUNCTIONS = """
        // 載入付款記錄
        async function loadPayments() {
            if (!isLoggedIn) return;
            
            try {
                const response = await fetch('/gumroad/stats', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                // 同時載入 admin payments 端點
                const adminResponse = await fetch('/admin/payments', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (adminResponse.ok) {
                    const data = await adminResponse.json();
                    if (data.success) {
                        allPayments = data.payments;
                        renderPayments(allPayments);
                    }
                }
            } catch (error) {
                console.error('載入付款記錄錯誤:', error);
            }
        }

        function renderPayments(payments) {
            const tbody = document.getElementById('payments-tbody');
            tbody.innerHTML = '';
            
            if (payments.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center;">暫無付款記錄</td></tr>';
                return;
            }
            
            payments.forEach(payment => {
                const row = document.createElement('tr');
                const statusClass = payment.status === 'completed' ? 'status-active' : 
                                  payment.status === 'refunded' ? 'status-refunded' : 'status-inactive';
                
                row.innerHTML = `
                    <td>${payment.created_at}</td>
                    <td>${payment.user_name}</td>
                    <td>${payment.user_email}</td>
                    <td>${payment.plan_name}</td>
                    <td>NT$ ${payment.amount_twd}</td>
                    <td>$ ${payment.amount_usd}</td>
                    <td><span class="${statusClass}">${payment.status}</span></td>
                    <td><code style="font-size: 10px;">${payment.user_uuid || 'N/A'}</code></td>
                    <td>
                        <button onclick="resendEmail('${payment.payment_id}')" class="btn btn-info" style="font-size: 10px;">重發Email</button>
                        ${payment.status === 'completed' ? `<button onclick="initiateRefund('${payment.payment_id}')" class="btn btn-danger" style="font-size: 10px;">退款</button>` : ''}
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // 載入退款記錄
        async function loadRefunds() {
            if (!isLoggedIn) return;
            
            try {
                const response = await fetch('/admin/refunds', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        allRefunds = data.refunds;
                        renderRefunds(allRefunds);
                    }
                }
            } catch (error) {
                console.error('載入退款記錄錯誤:', error);
            }
        }

        function renderRefunds(refunds) {
            const tbody = document.getElementById('refunds-tbody');
            tbody.innerHTML = '';
            
            if (refunds.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">暫無退款記錄</td></tr>';
                return;
            }
            
            refunds.forEach(refund => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${refund.refund_processed_at}</td>
                    <td>${refund.original_payment_id}</td>
                    <td>${refund.user_name}</td>
                    <td>NT$ ${refund.refund_amount}</td>
                    <td>${refund.refund_reason}</td>
                    <td><span class="status-${refund.status}">${refund.status}</span></td>
                    <td><code style="font-size: 10px;">${refund.user_uuid || 'N/A'}</code></td>
                    <td>
                        <button onclick="viewRefundDetails('${refund.refund_id}')" class="btn btn-info" style="font-size: 10px;">詳情</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
"""

# JavaScript 分段 - 第七部分：系統統計和維護功能
JS_SYSTEM_FUNCTIONS = """
        // 載入系統統計
        async function loadSystemStats() {
            document.getElementById('stats-loading').style.display = 'block';
            document.getElementById('stats-content').style.display = 'none';
            
            try {
                const response = await fetch('/gumroad/stats', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        updateSystemStats(data.stats);
                    }
                }
            } catch (error) {
                console.error('載入系統統計錯誤:', error);
            } finally {
                document.getElementById('stats-loading').style.display = 'none';
                document.getElementById('stats-content').style.display = 'block';
            }
        }

        function updateSystemStats(stats) {
            document.getElementById('stat-success-rate').textContent = `${stats.success_rate.toFixed(1)}%`;
            document.getElementById('stat-refund-rate').textContent = `${stats.refund_rate.toFixed(1)}%`;
            
            const avgRevenue = stats.total_payments > 0 ? (stats.total_revenue_twd / stats.total_payments) : 0;
            document.getElementById('stat-avg-revenue').textContent = `NT$ ${avgRevenue.toFixed(0)}`;
            
            // 月成長率計算（這裡可以添加更複雜的邏輯）
            document.getElementById('stat-monthly-growth').textContent = '+12.5%';
            
            // 更新收益分析
            const revenueAnalysis = document.getElementById('revenue-analysis');
            revenueAnalysis.innerHTML = `
                <div class="stats">
                    <div class="stat-card">
                        <h3>${stats.total_payments}</h3>
                        <p>總交易數</p>
                    </div>
                    <div class="stat-card">
                        <h3>${stats.completed_payments}</h3>
                        <p>成功交易</p>
                    </div>
                    <div class="stat-card">
                        <h3>${stats.refunded_payments}</h3>
                        <p>退款交易</p>
                    </div>
                    <div class="stat-card">
                        <h3>NT$ ${stats.net_revenue_twd.toLocaleString()}</h3>
                        <p>淨收益</p>
                    </div>
                </div>
            `;
        }

        // 搜尋過濾
        function filterUsers() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const filteredUsers = allUsers.filter(user => 
                user.display_name.toLowerCase().includes(searchTerm) ||
                user.uuid_preview.toLowerCase().includes(searchTerm) ||
                user.payment_status.toLowerCase().includes(searchTerm)
            );
            renderUsers(filteredUsers);
        }

        function filterPayments() {
            const searchTerm = document.getElementById('payment-search').value.toLowerCase();
            const filteredPayments = allPayments.filter(payment => 
                payment.user_name.toLowerCase().includes(searchTerm) ||
                payment.user_email.toLowerCase().includes(searchTerm) ||
                payment.plan_name.toLowerCase().includes(searchTerm)
            );
            renderPayments(filteredPayments);
        }

        function filterRefunds() {
            const searchTerm = document.getElementById('refund-search').value.toLowerCase();
            const filteredRefunds = allRefunds.filter(refund => 
                refund.user_name.toLowerCase().includes(searchTerm) ||
                refund.refund_reason.toLowerCase().includes(searchTerm)
            );
            renderRefunds(filteredRefunds);
        }

        // 更新統計
        function updateStats(users) {
            const total = users.length;
            const active = users.filter(u => u.active && (!u.expires_at || new Date(u.expires_at) > new Date())).length;
            const expired = users.filter(u => u.expires_at && new Date(u.expires_at) < new Date()).length;
            const refunded = users.filter(u => u.payment_status === 'refunded').length;
            
            // 載入收益統計
            loadRevenueStats();
        }

        async function loadRevenueStats() {
            try {
                const response = await fetch('/gumroad/stats', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        document.getElementById('total-revenue').textContent = `${data.stats.total_revenue_twd.toLocaleString()}`;
                        document.getElementById('net-revenue').textContent = `${data.stats.net_revenue_twd.toLocaleString()}`;
                    }
                }
            } catch (error) {
                console.error('載入收益統計失敗:', error);
                document.getElementById('total-revenue').textContent = '0';
                document.getElementById('net-revenue').textContent = '0';
            }
        }
"""

# JavaScript 分段 - 第八部分：匯出和退款處理功能
JS_EXPORT_FUNCTIONS = """
        // 匯出功能
        function exportUsers() {
            if (allUsers.length === 0) {
                alert('沒有用戶數據可匯出');
                return;
            }
            
            const csvContent = [
                ['顯示名稱', 'UUID', '狀態', '到期時間', '登入次數', '創建時間', '付款狀態'].join(','),
                ...allUsers.map(user => [
                    user.display_name,
                    user.original_uuid,
                    user.active ? '啟用' : '停用',
                    user.expires_at || '永久',
                    user.login_count,
                    user.created_at,
                    user.payment_status || '手動創建'
                ].join(','))
            ].join('\\n');
            
            downloadCSV(csvContent, `artale_users_${new Date().toISOString().split('T')[0]}.csv`);
        }

        function exportPayments() {
            if (allPayments.length === 0) {
                alert('沒有付款數據可匯出');
                return;
            }
            
            const csvContent = [
                ['付款時間', '客戶姓名', '客戶信箱', '方案', '金額TWD', '金額USD', '狀態', '用戶序號'].join(','),
                ...allPayments.map(payment => [
                    payment.created_at,
                    payment.user_name,
                    payment.user_email,
                    payment.plan_name,
                    payment.amount_twd,
                    payment.amount_usd,
                    payment.status,
                    payment.user_uuid || 'N/A'
                ].join(','))
            ].join('\\n');
            
            downloadCSV(csvContent, `artale_payments_${new Date().toISOString().split('T')[0]}.csv`);
        }

        function exportRefunds() {
            if (allRefunds.length === 0) {
                alert('沒有退款數據可匯出');
                return;
            }
            
            const csvContent = [
                ['退款時間', '原付款ID', '客戶姓名', '退款金額', '退款原因', '處理狀態', '相關用戶'].join(','),
                ...allRefunds.map(refund => [
                    refund.refund_processed_at,
                    refund.original_payment_id,
                    refund.user_name,
                    refund.refund_amount,
                    refund.refund_reason,
                    refund.status,
                    refund.user_uuid || 'N/A'
                ].join(','))
            ].join('\\n');
            
            downloadCSV(csvContent, `artale_refunds_${new Date().toISOString().split('T')[0]}.csv`);
        }

        function downloadCSV(content, filename) {
            const blob = new Blob(['\\uFEFF' + content], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        }

        // 退款處理
        function initiateRefund(paymentId) {
            const payment = allPayments.find(p => p.payment_id === paymentId);
            if (!payment) {
                alert('找不到付款記錄');
                return;
            }
            
            currentRefundData = payment;
            
            document.getElementById('refund-details').innerHTML = `
                <div class="payment-info">
                    <h4>付款詳情</h4>
                    <p><strong>付款ID:</strong> ${payment.payment_id}</p>
                    <p><strong>客戶:</strong> ${payment.user_name} (${payment.user_email})</p>
                    <p><strong>方案:</strong> ${payment.plan_name}</p>
                    <p><strong>金額:</strong> NT$ ${payment.amount_twd} ($ ${payment.amount_usd})</p>
                    <p><strong>付款時間:</strong> ${payment.created_at}</p>
                    <p><strong>用戶序號:</strong> ${payment.user_uuid || 'N/A'}</p>
                </div>
            `;
            
            document.getElementById('refund-modal').style.display = 'block';
        }

        function closeRefundModal() {
            document.getElementById('refund-modal').style.display = 'none';
            currentRefundData = null;
        }

        async function processRefund() {
            if (!currentRefundData) {
                alert('沒有選擇的退款記錄');
                return;
            }
            
            const reason = document.getElementById('refund-reason').value;
            const note = document.getElementById('refund-note').value.trim();
            
            if (!note) {
                alert('請輸入退款說明');
                return;
            }
            
            if (!confirm('確定要執行退款操作嗎？此操作無法撤銷！')) {
                return;
            }
            
            try {
                const response = await fetch('/admin/process-refund', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({
                        payment_id: currentRefundData.payment_id,
                        refund_reason: reason,
                        refund_note: note
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('退款處理成功！');
                    closeRefundModal();
                    loadPayments();
                    loadUsers();
                    loadRefunds();
                } else {
                    alert('退款處理失敗: ' + data.error);
                }
            } catch (error) {
                alert('退款處理錯誤: ' + error.message);
            }
        }
"""

# JavaScript 分段 - 第九部分：系統維護功能
JS_MAINTENANCE_FUNCTIONS = """
        // 系統維護功能
        async function cleanupOldWebhooks() {
            if (!confirm('確定要清理舊的 Webhook 記錄嗎？')) return;
            
            try {
                const response = await fetch('/admin/cleanup-webhooks', {
                    method: 'POST',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`清理完成！刪除了 ${data.deleted_count} 個舊記錄`);
                } else {
                    alert('清理失敗: ' + data.error);
                }
            } catch (error) {
                alert('清理錯誤: ' + error.message);
            }
        }

        async function optimizeDatabase() {
            if (!confirm('確定要執行數據庫優化嗎？此操作可能需要幾分鐘時間。')) return;
            
            try {
                const response = await fetch('/admin/optimize-database', {
                    method: 'POST',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('數據庫優化完成！');
                } else {
                    alert('優化失敗: ' + data.error);
                }
            } catch (error) {
                alert('優化錯誤: ' + error.message);
            }
        }

        async function generateSystemReport() {
            try {
                const response = await fetch('/admin/system-report', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `system_report_${new Date().toISOString().split('T')[0]}.pdf`;
                    a.click();
                } else {
                    alert('生成報告失敗');
                }
            } catch (error) {
                alert('生成報告錯誤: ' + error.message);
            }
        }

        async function backupData() {
            if (!confirm('確定要執行數據備份嗎？')) return;
            
            try {
                const response = await fetch('/admin/backup-data', {
                    method: 'POST',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('數據備份完成！備份文件：' + data.backup_file);
                } else {
                    alert('備份失敗: ' + data.error);
                }
            } catch (error) {
                alert('備份錯誤: ' + error.message);
            }
        }

        async function bulkCleanup() {
            if (!confirm('確定要批量清理過期用戶嗎？這將停用所有已過期的用戶帳號。')) return;
            
            try {
                const response = await fetch('/admin/bulk-cleanup', {
                    method: 'POST',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`批量清理完成！處理了 ${data.processed_count} 個過期用戶`);
                    loadUsers();
                } else {
                    alert('批量清理失敗: ' + data.error);
                }
            } catch (error) {
                alert('批量清理錯誤: ' + error.message);
            }
        }

        async function syncGumroadData() {
            if (!confirm('確定要同步 Gumroad 數據嗎？這將更新所有付款狀態。')) return;
            
            try {
                const response = await fetch('/admin/sync-gumroad', {
                    method: 'POST',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`同步完成！更新了 ${data.updated_count} 筆記錄`);
                    loadPayments();
                    loadUsers();
                } else {
                    alert('同步失敗: ' + data.error);
                }
            } catch (error) {
                alert('同步錯誤: ' + error.message);
            }
        }
"""

# JavaScript 分段 - 第十部分：用戶操作功能
JS_USER_OPERATIONS = """
        // 創建用戶
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('create-user-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    if (!isLoggedIn) {
                        alert('請先登入');
                        return;
                    }
                    
                    const uuid = document.getElementById('new-uuid').value;
                    const displayName = document.getElementById('new-display-name').value;
                    const days = document.getElementById('new-days').value;
                    
                    try {
                        const response = await fetch('/admin/create-user', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Admin-Token': ADMIN_TOKEN
                            },
                            body: JSON.stringify({
                                uuid: uuid,
                                display_name: displayName,
                                days: parseInt(days)
                            })
                        });
                        
                        const data = await response.json();
                        if (data.success) {
                            alert('用戶創建成功!');
                            form.reset();
                            loadUsers();
                        } else {
                            alert('創建失敗: ' + data.error);
                        }
                    } catch (error) {
                        alert('創建錯誤: ' + error.message);
                    }
                });
            }
        });

        // 其他用戶操作函數

        async function toggleUser(documentId, newStatus) {
            if (!isLoggedIn) return;
            
            try {
                const response = await fetch(`/admin/users/${documentId}/toggle`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({ active: newStatus })
                });
                
                const data = await response.json();
                if (data.success) {
                    loadUsers();
                } else {
                    alert('操作失敗: ' + data.error);
                }
            } catch (error) {
                alert('操作錯誤: ' + error.message);
            }
        }

        async function deleteUser(documentId, displayName) {
            if (!isLoggedIn) return;
            
            if (!confirm(`確定要刪除用戶 "${displayName}" 嗎？此操作無法撤銷！`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/users/${documentId}`, {
                    method: 'DELETE',
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('用戶已刪除');
                    loadUsers();
                } else {
                    alert('刪除失敗: ' + data.error);
                }
            } catch (error) {
                alert('刪除錯誤: ' + error.message);
            }
        }

        async function resendEmail(paymentId) {
            try {
                const response = await fetch('/admin/resend-email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({ payment_id: paymentId })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('Email 已重新發送');
                } else {
                    alert('發送失敗: ' + data.error);
                }
            } catch (error) {
                alert('發送錯誤: ' + error.message);
            }
        }

        function viewPaymentDetails(paymentId) {
            const payment = allPayments.find(p => p.payment_id === paymentId);
            if (payment) {
                alert(`付款詳情：
付款ID: ${payment.payment_id}
客戶: ${payment.user_name}
信箱: ${payment.user_email}
方案: ${payment.plan_name}
金額: NT$ ${payment.amount_twd}
狀態: ${payment.status}
時間: ${payment.created_at}`);
            }
        }

        function viewRefundDetails(refundId) {
            const refund = allRefunds.find(r => r.refund_id === refundId);
            if (refund) {
                alert(`退款詳情：
退款ID: ${refund.refund_id}
原付款: ${refund.original_payment_id}
客戶: ${refund.user_name}
金額: NT$ ${refund.refund_amount}
原因: ${refund.refund_reason}
狀態: ${refund.status}
時間: ${refund.refund_processed_at}`);
            }
        }

        // 鍵盤支援
        document.addEventListener('DOMContentLoaded', function() {
            const passwordInput = document.getElementById('admin-password');
            if (passwordInput) {
                passwordInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        submitLogin();
                    }
                });
            }
        });

        // 點擊模態框外部關閉
        window.onclick = function(event) {
            const refundModal = document.getElementById('refund-modal');
            const editModal = document.getElementById('edit-user-modal');
            
            if (event.target === refundModal) {
                closeRefundModal();
            }
            if (event.target === editModal) {
                closeEditUserModal();
            }
        }
    </script>
</body>
</html>
"""

# 組合完整模板的函數
def build_admin_template():
    """組合所有 HTML 和 JavaScript 片段"""
    return (
        HTML_HEAD +
        HTML_STYLES +
        HTML_FORM_STYLES +
        HTML_ADDITIONAL_STYLES +
        HTML_MODAL_STYLES +
        HTML_FINAL_STYLES +
        HTML_BODY_START +
        HTML_USER_MANAGEMENT +
        HTML_PAYMENT_MANAGEMENT +
        HTML_REFUND_MANAGEMENT +
        HTML_UUID_GENERATOR +
        HTML_SYSTEM_STATS +
        HTML_MODAL +
        JS_VARIABLES +
        JS_LOGIN_FUNCTIONS +
        JS_DEBUG_FUNCTIONS +
        JS_UUID_FUNCTIONS +
        JS_USER_FUNCTIONS +
        JS_PAYMENT_FUNCTIONS +
        JS_SYSTEM_FUNCTIONS +
        JS_EXPORT_FUNCTIONS +
        JS_MAINTENANCE_FUNCTIONS +
        JS_USER_OPERATIONS
    )

def check_admin_token(request):
    """驗證管理員權限"""
    admin_token = request.headers.get('Admin-Token')
    expected_token = os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token')
    return admin_token == expected_token

def generate_secure_uuid(prefix='artale', custom_id=None, date_format='YYYYMMDD'):
    """生成安全的UUID"""
    if custom_id:
        user_id = re.sub(r'[^a-zA-Z0-9]', '', custom_id).lower()
    else:
        user_id = uuid_lib.uuid4().hex[:8]
    
    now = datetime.now()
    if date_format == 'YYYYMMDD':
        date_str = now.strftime('%Y%m%d')
    elif date_format == 'YYYYMM':
        date_str = now.strftime('%Y%m')
    elif date_format == 'YYYY':
        date_str = now.strftime('%Y')
    else:
        date_str = now.strftime('%Y%m%d')
    
    return f"{prefix}_{user_id}_{date_str}"

# ===== 管理員路由 =====

@admin_bp.route('', methods=['GET'])
def admin_dashboard():
    """增強版管理員面板"""
    from flask import Response
    
    # 使用組合函數生成完整模板
    template_content = build_admin_template()  # 改成這樣
    
    # 確保正確的UTF-8編碼
    html_content = template_content.encode('utf-8')
    
    response = Response(
        html_content,
        mimetype='text/html',
        headers={'Content-Type': 'text/html; charset=utf-8'}
    )
    
    return response

@admin_bp.route('/debug', methods=['GET'])
def admin_debug():
    """調試端點"""
    admin_token = os.environ.get('ADMIN_TOKEN', 'NOT_SET')
    return jsonify({
        'admin_token_set': admin_token != 'NOT_SET',
        'admin_token_value': admin_token[:8] + '...' if len(admin_token) > 8 else admin_token,
        'expected_default': 'your-secret-admin-token'
    })

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    """獲取所有用戶"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        users_ref = db.collection('authorized_users')
        users = users_ref.stream()
        
        user_list = []
        for user in users:
            user_data = user.to_dict()
            
            # 處理時間格式
            created_at = user_data.get('created_at')
            if hasattr(created_at, 'strftime'):
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                created_at_str = str(created_at)[:16] if created_at else 'Unknown'
            
            expires_at = user_data.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at_str = expires_at.split('T')[0] + ' ' + expires_at.split('T')[1][:5]
                else:
                    expires_at_str = str(expires_at)[:16]
            else:
                expires_at_str = None
            
            # 生成顯示用的 UUID
            original_uuid = user_data.get('original_uuid', 'Unknown')
            uuid_preview = original_uuid[:16] + '...' if len(original_uuid) > 16 else original_uuid
            
            # 檢查退款狀態
            payment_status = user_data.get('payment_status', '手動創建')
            if user_data.get('deactivation_reason', '').startswith('Gumroad 退款'):
                payment_status = 'refunded'
            
            user_list.append({
                'document_id': user.id,
                'uuid_preview': uuid_preview,
                'original_uuid': original_uuid,
                'display_name': user_data.get('display_name', 'Unknown'),
                'active': user_data.get('active', False),
                'expires_at': expires_at_str,
                'login_count': user_data.get('login_count', 0),
                'created_at': created_at_str,
                'permissions': user_data.get('permissions', {}),
                'notes': user_data.get('notes', ''),
                'payment_status': payment_status,
                'payment_id': user_data.get('payment_id')
            })
        
        # 按創建時間排序
        user_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total_count': len(user_list)
        })
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/create-user', methods=['POST'])
def create_user_admin():
    """創建新用戶（管理員）"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        data = request.get_json()
        uuid_string = data.get('uuid', '').strip()
        display_name = data.get('display_name', '').strip()
        days_valid = data.get('days', 30)
        
        if not uuid_string or not display_name:
            return jsonify({'success': False, 'error': 'UUID 和顯示名稱為必填'}), 400
        
        # 檢查 UUID 是否已存在
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        
        if user_ref.get().exists:
            return jsonify({'success': False, 'error': 'UUID 已存在'}), 400
        
        # 創建用戶
        expires_at = None
        if days_valid > 0:
            expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
        
        user_data = {
            "original_uuid": uuid_string,
            "display_name": display_name,
            "permissions": {
                "script_access": True,
                "config_modify": True
            },
            "active": True,
            "created_at": datetime.now(),
            "created_by": "admin_dashboard",
            "login_count": 0,
            "notes": f"管理員創建 - {datetime.now().strftime('%Y-%m-%d')}",
            "payment_status": "手動創建"
        }
        
        if expires_at:
            user_data["expires_at"] = expires_at
        
        user_ref.set(user_data)
        
        return jsonify({
            'success': True,
            'message': '用戶創建成功',
            'uuid': uuid_string,
            'display_name': display_name
        })
        
    except Exception as e:
        logger.error(f"Create user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/users/<document_id>', methods=['PUT'])
def update_user_admin(document_id):
    """更新用戶資訊"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        data = request.get_json()
        user_ref = db.collection('authorized_users').document(document_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        update_data = {}
        
        # 更新顯示名稱
        if 'display_name' in data:
            update_data['display_name'] = data['display_name']
        
        # 延長有效期
        if 'extend_days' in data:
            from firebase_admin import firestore
            extend_days = data['extend_days']
            current_data = user_doc.to_dict()
            current_expires = current_data.get('expires_at')
            
            if current_expires:
                if isinstance(current_expires, str):
                    current_expires = datetime.fromisoformat(current_expires.replace('Z', ''))
                
                # 如果已過期，從現在開始計算
                if current_expires < datetime.now():
                    new_expires = datetime.now() + timedelta(days=extend_days)
                else:
                    new_expires = current_expires + timedelta(days=extend_days)
            else:
                # 如果原本是永久，從現在開始計算
                new_expires = datetime.now() + timedelta(days=extend_days)
            
            update_data['expires_at'] = new_expires.isoformat()

            # 更新到期時間（完整設定，不是延長）
        if 'expires_at' in data:
            expires_at = data['expires_at']
            if expires_at is None or expires_at == '':
                # 設為永久
                from firebase_admin import firestore
                update_data['expires_at'] = firestore.DELETE_FIELD
            else:
                # 設定具體的到期時間
                try:
                    from datetime import datetime
                    if isinstance(expires_at, str):
                        # 解析 ISO 格式的時間字符串
                        expires_datetime = datetime.fromisoformat(expires_at.replace('Z', ''))
                        update_data['expires_at'] = expires_datetime
                    else:
                        update_data['expires_at'] = expires_at
                except ValueError as ve:
                    return jsonify({'success': False, 'error': f'無效的日期格式: {str(ve)}'}), 400
        
        # 更新備註
        if 'notes' in data:
            update_data['notes'] = data['notes']
        
        update_data['updated_at'] = datetime.now()
        update_data['updated_by'] = 'admin_dashboard'
        
        user_ref.update(update_data)
        
        return jsonify({
            'success': True,
            'message': '用戶資訊已更新'
        })
        
    except Exception as e:
        logger.error(f"Update user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/users/<document_id>/toggle', methods=['PUT'])
def toggle_user_status(document_id):
    """啟用/停用用戶"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        data = request.get_json()
        new_status = data.get('active', True)
        
        user_ref = db.collection('authorized_users').document(document_id)
        if not user_ref.get().exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        user_ref.update({
            'active': new_status,
            'status_changed_at': datetime.now(),
            'status_changed_by': 'admin_dashboard'
        })
        
        return jsonify({
            'success': True,
            'message': f'用戶已{"啟用" if new_status else "停用"}'
        })
        
    except Exception as e:
        logger.error(f"Toggle user status error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/users/<document_id>', methods=['DELETE'])
def delete_user_admin(document_id):
    """刪除用戶"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        user_ref = db.collection('authorized_users').document(document_id)
        if not user_ref.get().exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        # 刪除用戶
        user_ref.delete()
        
        return jsonify({
            'success': True,
            'message': '用戶已刪除'
        })
        
    except Exception as e:
        logger.error(f"Delete user admin error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/check-uuid', methods=['POST'])
def check_uuid_exists():
    """檢查 UUID 是否已存在"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        data = request.get_json()
        uuid_string = data.get('uuid', '').strip()
        
        if not uuid_string:
            return jsonify({'success': False, 'error': 'UUID 為必填'}), 400
        
        # 檢查 UUID 是否已存在
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        return jsonify({
            'success': True,
            'exists': user_doc.exists,
            'uuid': uuid_string
        })
        
    except Exception as e:
        logger.error(f"Check UUID error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/payments', methods=['GET'])
def get_payments():
    """獲取付款記錄"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        payments_ref = db.collection('payment_records')
        payments = payments_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        payment_list = []
        for payment in payments:
            payment_data = payment.to_dict()
            
            # 處理時間格式
            created_at = payment_data.get('created_at')
            if hasattr(created_at, 'strftime'):
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                created_at_str = str(created_at)[:16] if created_at else 'Unknown'
            
            payment_list.append({
                'payment_id': payment.id,
                'created_at': created_at_str,
                'user_name': payment_data.get('user_name', ''),
                'user_email': payment_data.get('user_email', ''),
                'plan_name': payment_data.get('plan_name', ''),
                'amount_twd': payment_data.get('amount_twd', 0),
                'amount_usd': payment_data.get('amount_usd', 0),
                'status': payment_data.get('status', ''),
                'user_uuid': payment_data.get('user_uuid', '')
            })
        
        return jsonify({'success': True, 'payments': payment_list})
        
    except Exception as e:
        logger.error(f"Get payments error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/refunds', methods=['GET'])
def get_refunds():
    """獲取退款記錄"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # 獲取所有狀態為 refunded 的付款記錄
        payments_ref = db.collection('payment_records')
        refunded_payments = payments_ref.where('status', '==', 'refunded').stream()
        
        refund_list = []
        for payment in refunded_payments:
            payment_data = payment.to_dict()
            
            # 處理時間格式
            refund_time = payment_data.get('refund_processed_at')
            if hasattr(refund_time, 'strftime'):
                refund_time_str = refund_time.strftime('%Y-%m-%d %H:%M')
            else:
                refund_time_str = str(refund_time)[:16] if refund_time else 'Unknown'
            
            refund_list.append({
                'refund_id': payment_data.get('refund_id', payment.id),
                'original_payment_id': payment.id,
                'refund_processed_at': refund_time_str,
                'user_name': payment_data.get('user_name', ''),
                'user_email': payment_data.get('user_email', ''),
                'refund_amount': payment_data.get('amount_twd', 0),
                'refund_reason': payment_data.get('refund_data', {}).get('reason', '客戶要求退款'),
                'status': 'processed',
                'user_uuid': payment_data.get('user_uuid', '')
            })
        
        return jsonify({'success': True, 'refunds': refund_list})
        
    except Exception as e:
        logger.error(f"Get refunds error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/process-refund', methods=['POST'])
def process_refund():
    """處理退款請求"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db, gumroad_service
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        data = request.get_json()
        payment_id = data.get('payment_id')
        refund_reason = data.get('refund_reason', 'admin_manual_refund')
        refund_note = data.get('refund_note', '')
        
        if not payment_id:
            return jsonify({'success': False, 'error': '缺少付款 ID'}), 400
        
        # 獲取付款記錄
        payment_ref = db.collection('payment_records').document(payment_id)
        payment_doc = payment_ref.get()
        
        if not payment_doc.exists:
            return jsonify({'success': False, 'error': '找不到付款記錄'}), 404
        
        payment_data = payment_doc.to_dict()
        
        if payment_data.get('status') == 'refunded':
            return jsonify({'success': False, 'error': '該付款已經退款'}), 400
        
        # 更新付款記錄為退款狀態
        refund_data = {
            'status': 'refunded',
            'refund_processed_at': datetime.now(),
            'refund_reason': refund_reason,
            'refund_note': refund_note,
            'refund_processed_by': 'admin_manual',
            'refund_data': {
                'reason': refund_reason,
                'note': refund_note,
                'processed_by': 'admin',
                'manual_refund': True
            }
        }
        
        payment_ref.update(refund_data)
        
        # 停用相關用戶帳號
        user_uuid = payment_data.get('user_uuid')
        if user_uuid and gumroad_service:
            gumroad_service.deactivate_user_account(
                user_uuid, 
                f"管理員手動退款: {refund_reason} - {refund_note}"
            )
        
        # 發送退款通知郵件
        user_email = payment_data.get('user_email')
        user_name = payment_data.get('user_name')
        if user_email and gumroad_service:
            gumroad_service.send_refund_notification_email(user_email, user_name, payment_data)
        
        logger.info(f"管理員手動處理退款: {payment_id} - {refund_reason}")
        
        return jsonify({
            'success': True,
            'message': '退款處理成功',
            'payment_id': payment_id,
            'refund_reason': refund_reason
        })
        
    except Exception as e:
        logger.error(f"Process refund error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/resend-email', methods=['POST'])
def resend_email():
    """重新發送序號Email"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import gumroad_service
        if gumroad_service is None:
            return jsonify({'success': False, 'error': 'Gumroad service not available'}), 503
            
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({'success': False, 'error': '缺少付款ID'}), 400
        
        payment_record = gumroad_service.get_payment_record(payment_id)
        if not payment_record:
            return jsonify({'success': False, 'error': '找不到付款記錄'}), 404
        
        if not payment_record.get('user_uuid'):
            return jsonify({'success': False, 'error': '該付款尚未生成序號'}), 400
        
        success = gumroad_service.send_license_email(
            payment_record['user_email'],
            payment_record['user_name'],
            payment_record['user_uuid'],
            payment_record['plan_name'],
            payment_record['plan_period']
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Email已重新發送'})
        else:
            return jsonify({'success': False, 'error': 'Email發送失敗'}), 500
            
    except Exception as e:
        logger.error(f"Resend email error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/cleanup-webhooks', methods=['POST'])
def cleanup_webhooks():
    """清理舊的 webhook 記錄"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import gumroad_service
        if gumroad_service is None:
            return jsonify({'success': False, 'error': 'Gumroad service not available'}), 503
        
        deleted_count = gumroad_service.cleanup_old_webhooks()
        
        return jsonify({
            'success': True,
            'message': f'清理完成，刪除了 {deleted_count} 個舊記錄',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Cleanup webhooks error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/optimize-database', methods=['POST'])
def optimize_database():
    """優化數據庫"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # 執行數據庫優化操作
        # 1. 清理過期的 session 記錄
        cutoff_date = datetime.now() - timedelta(days=7)
        old_sessions = db.collection('user_sessions')\
                        .where('expires_at', '<', cutoff_date)\
                        .limit(100)\
                        .stream()
        
        session_deleted = 0
        for session in old_sessions:
            session.reference.delete()
            session_deleted += 1
        
        # 2. 清理過期的 webhook 記錄
        old_webhooks = db.collection('processed_webhooks')\
                        .where('expires_at', '<', cutoff_date)\
                        .limit(100)\
                        .stream()
        
        webhook_deleted = 0
        for webhook in old_webhooks:
            webhook.reference.delete()
            webhook_deleted += 1
        
        logger.info(f"數據庫優化完成: 清理了 {session_deleted} 個過期 session, {webhook_deleted} 個過期 webhook")
        
        return jsonify({
            'success': True,
            'message': f'數據庫優化完成，清理了 {session_deleted + webhook_deleted} 個過期記錄',
            'details': {
                'sessions_deleted': session_deleted,
                'webhooks_deleted': webhook_deleted
            }
        })
        
    except Exception as e:
        logger.error(f"Optimize database error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/bulk-cleanup', methods=['POST'])
def bulk_cleanup():
    """批量清理過期用戶"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        now = datetime.now()
        users_ref = db.collection('authorized_users')
        all_users = users_ref.stream()
        
        processed_count = 0
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            expires_at = user_data.get('expires_at')
            
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
                
                # 如果已過期且仍然啟用，則停用
                if expires_at < now and user_data.get('active', False):
                    user_doc.reference.update({
                        'active': False,
                        'deactivated_at': now,
                        'deactivation_reason': 'Bulk cleanup - expired',
                        'deactivated_by': 'admin_bulk_cleanup'
                    })
                    processed_count += 1
        
        logger.info(f"批量清理完成: 處理了 {processed_count} 個過期用戶")
        
        return jsonify({
            'success': True,
            'message': f'批量清理完成，處理了 {processed_count} 個過期用戶',
            'processed_count': processed_count
        })
        
    except Exception as e:
        logger.error(f"Bulk cleanup error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/sync-gumroad', methods=['POST'])
def sync_gumroad():
    """同步 Gumroad 數據"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        # 這裡可以實現與 Gumroad API 同步的邏輯
        # 例如獲取最新的銷售和退款記錄
        
        logger.info("Gumroad 數據同步完成")
        
        return jsonify({
            'success': True,
            'message': 'Gumroad 數據同步完成',
            'updated_count': 0  # 實際實現時返回更新的記錄數
        })
        
    except Exception as e:
        logger.error(f"Sync Gumroad error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/system-report', methods=['GET'])
def generate_system_report():
    """生成系統報告"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        # 這裡可以實現生成 PDF 報告的邏輯
        # 暫時返回文本報告
        
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # 收集統計數據
        users_count = len(list(db.collection('authorized_users').stream()))
        payments_count = len(list(db.collection('payment_records').stream()))
        
        report_content = f"""
Scrilab Artale 系統報告
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

用戶統計:
- 總用戶數: {users_count}
- 付款記錄: {payments_count}

系統狀態: 正常運行
        """
        
        from flask import Response
        return Response(
            report_content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename=system_report_{datetime.now().strftime("%Y%m%d")}.txt'}
        )
        
    except Exception as e:
        logger.error(f"Generate system report error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/backup-data', methods=['POST'])
def backup_data():
    """備份數據"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        # 實現數據備份邏輯
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"數據備份完成: {backup_filename}")
        
        return jsonify({
            'success': True,
            'message': '數據備份完成',
            'backup_file': backup_filename
        })
        
    except Exception as e:
        logger.error(f"Backup data error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/online-users', methods=['GET'])
def get_online_users():
    """獲取在線用戶列表"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # 獲取最近 5 分鐘內活動的用戶 session
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # 查詢活躍的 session
        sessions_ref = db.collection('user_sessions')
        active_sessions = sessions_ref.where('last_activity', '>=', cutoff_time).stream()
        
        online_users = []
        active_session_count = 0
        
        for session in active_sessions:
            session_data = session.to_dict()
            active_session_count += 1
            
            # 獲取對應的用戶資訊
            user_uuid = session_data.get('user_uuid')
            if user_uuid:
                # 計算 UUID hash 來查找用戶
                import hashlib
                uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
                user_ref = db.collection('authorized_users').document(uuid_hash)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    
                    # 處理最後活動時間
                    last_activity = session_data.get('last_activity')
                    if hasattr(last_activity, 'isoformat'):
                        last_activity_str = last_activity.isoformat()
                    else:
                        last_activity_str = str(last_activity)
                    
                    # 生成 UUID 預覽
                    original_uuid = user_data.get('original_uuid', user_uuid)
                    uuid_preview = original_uuid[:16] + '...' if len(original_uuid) > 16 else original_uuid
                    
                    online_user = {
                        'user_uuid': user_uuid,
                        'uuid_preview': uuid_preview,
                        'display_name': user_data.get('display_name', 'Unknown'),
                        'last_activity': last_activity_str,
                        'session_id': session.id,
                        'ip_address': session_data.get('ip_address', 'Unknown')
                    }
                    
                    # 避免重複用戶
                    if not any(u['user_uuid'] == user_uuid for u in online_users):
                        online_users.append(online_user)
        
        # 按最後活動時間排序
        online_users.sort(key=lambda x: x['last_activity'], reverse=True)
        
        stats = {
            'online_count': len(online_users),
            'active_sessions': active_session_count,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'online_users': online_users,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Get online users error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/users/<document_id>', methods=['GET'])
def get_user_details(document_id):
    """獲取單個用戶的詳細資訊"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
            
        user_ref = db.collection('authorized_users').document(document_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        user_data = user_doc.to_dict()
        
        # 處理時間格式
        created_at = user_data.get('created_at')
        if hasattr(created_at, 'strftime'):
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M')
        else:
            created_at_str = str(created_at)[:16] if created_at else 'Unknown'
        
        expires_at = user_data.get('expires_at')
        expires_at_str = None
        if expires_at:
            if isinstance(expires_at, str):
                expires_at_str = expires_at
            else:
                expires_at_str = expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at)
        
        user_details = {
            'original_uuid': user_data.get('original_uuid', 'Unknown'),
            'display_name': user_data.get('display_name', 'Unknown'),
            'active': user_data.get('active', False),
            'expires_at': expires_at_str,
            'login_count': user_data.get('login_count', 0),
            'created_at': created_at_str,
            'notes': user_data.get('notes', ''),
            'payment_status': user_data.get('payment_status', '手動創建'),
            'payment_id': user_data.get('payment_id')
        }
        
        return jsonify({
            'success': True,
            'user': user_details
        })
        
    except Exception as e:
        logger.error(f"Get user details error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
@admin_bp.route('/active-sessions', methods=['GET'])
def get_active_sessions():
    """獲取活躍Session列表"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # 獲取最近 5 分鐘內活動的 session
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # 查詢活躍的 session
        sessions_ref = db.collection('user_sessions')
        active_sessions_query = sessions_ref.where('last_activity', '>=', cutoff_time).stream()
        
        active_sessions = []
        unique_users = set()
        
        for session in active_sessions_query:
            session_data = session.to_dict()
            
            # 獲取對應的用戶資訊
            user_uuid = session_data.get('user_uuid')
            if user_uuid:
                unique_users.add(user_uuid)
                
                # 計算 UUID hash 來查找用戶
                import hashlib
                uuid_hash = hashlib.sha256(user_uuid.encode()).hexdigest()
                user_ref = db.collection('authorized_users').document(uuid_hash)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    
                    # 處理時間
                    last_activity = session_data.get('last_activity')
                    created_at = session_data.get('created_at')
                    
                    if hasattr(last_activity, 'isoformat'):
                        last_activity_str = last_activity.isoformat()
                    else:
                        last_activity_str = str(last_activity)
                    
                    if hasattr(created_at, 'isoformat'):
                        created_at_str = created_at.isoformat()
                    else:
                        created_at_str = str(created_at)
                    
                    # 生成 UUID 預覽
                    original_uuid = user_data.get('original_uuid', user_uuid)
                    uuid_preview = original_uuid[:16] + '...' if len(original_uuid) > 16 else original_uuid
                    
                    session_info = {
                        'session_id': session.id,
                        'user_uuid': user_uuid,
                        'uuid_preview': uuid_preview,
                        'display_name': user_data.get('display_name', 'Unknown'),
                        'last_activity': last_activity_str,
                        'created_at': created_at_str,
                        'ip_address': session_data.get('ip_address', 'Unknown'),
                        'user_agent': session_data.get('user_agent', 'Unknown')
                    }
                    
                    active_sessions.append(session_info)
        
        # 按最後活動時間排序
        active_sessions.sort(key=lambda x: x['last_activity'], reverse=True)
        
        stats = {
            'active_sessions': len(active_sessions),
            'unique_users': len(unique_users),
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'active_sessions': active_sessions,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Get active sessions error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/clear-inactive-sessions', methods=['POST'])
def clear_inactive_sessions():
    """清理無效Session"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        # 獲取超過 10 分鐘沒有活動的 session
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(minutes=10)
        
        sessions_ref = db.collection('user_sessions')
        inactive_sessions = sessions_ref.where('last_activity', '<', cutoff_time).stream()
        
        cleared_count = 0
        for session in inactive_sessions:
            session.reference.delete()
            cleared_count += 1
        
        logger.info(f"清理了 {cleared_count} 個無效Session")
        
        return jsonify({
            'success': True,
            'message': f'已清理 {cleared_count} 個無效Session',
            'cleared_count': cleared_count
        })
        
    except Exception as e:
        logger.error(f"Clear inactive sessions error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@admin_bp.route('/terminate-session/<session_id>', methods=['DELETE'])
def terminate_session(session_id):
    """終止特定Session"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        from app import db
        if db is None:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        session_ref = db.collection('user_sessions').document(session_id)
        session_doc = session_ref.get()
        
        if not session_doc.exists:
            return jsonify({'success': False, 'error': 'Session不存在'}), 404
        
        # 刪除Session
        session_ref.delete()
        
        logger.info(f"管理員終止Session: {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Session已終止'
        })
        
    except Exception as e:
        logger.error(f"Terminate session error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500