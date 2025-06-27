from flask import Blueprint, request, jsonify, render_template_string
import os
import hashlib
import uuid as uuid_lib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# 創建藍圖
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理界面 HTML 模板
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Artale Script 用戶管理</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: #1976d2; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .user-table { width: 100%; border-collapse: collapse; }
        .user-table th, .user-table td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px; }
        .user-table th { background-color: #4CAF50; color: white; }
        .user-table tr:nth-child(even) { background-color: #f2f2f2; }
        .btn { background: #4CAF50; color: white; padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 2px; font-size: 12px; }
        .btn:hover { background: #45a049; }
        .btn-danger { background: #f44336; }
        .btn-danger:hover { background: #da190b; }
        .btn-warning { background: #ff9800; }
        .btn-warning:hover { background: #e68900; }
        .btn-info { background: #2196F3; }
        .btn-info:hover { background: #1976D2; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; font-weight: bold; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { margin: 0; font-size: 2em; color: #1976d2; }
        .form-row { display: flex; gap: 20px; }
        .form-row .form-group { flex: 1; }
        .search-box { width: 300px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-left: 10px; }
        .tabs { display: flex; background: #f1f1f1; border-radius: 8px; margin-bottom: 20px; }
        .tab { padding: 15px 30px; cursor: pointer; background: #e0e0e0; margin-right: 2px; border-radius: 8px 8px 0 0; }
        .tab.active { background: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .uuid-generator { background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        .uuid-preview { background: #333; color: #0f0; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; }
        .payment-section { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .payment-info { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; padding: 15px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Artale Script 用戶管理系統</h1>
            <p>管理所有授權用戶、權限和有效期 | 🔗 綠界金流整合</p>
        </div>
        
        <!-- 統計資訊 -->
        <div class="stats">
            <div class="stat-card">
                <h3 id="total-users">-</h3>
                <p>總用戶數</p>
            </div>
            <div class="stat-card">
                <h3 id="active-users">-</h3>
                <p>活躍用戶</p>
            </div>
            <div class="stat-card">
                <h3 id="expired-users">-</h3>
                <p>已過期</p>
            </div>
            <div class="stat-card">
                <h3 id="total-revenue">-</h3>
                <p>總收益 (NT$)</p>
            </div>
        </div>
        
        <!-- 分頁標籤 -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('user-management')">👥 用戶管理</div>
            <div class="tab" onclick="switchTab('payment-management')">💳 付款管理</div>
            <div class="tab" onclick="switchTab('uuid-generator')">🔧 UUID 生成器</div>
        </div>
        
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
                </div>
                <table class="user-table" id="users-table">
                    <thead>
                        <tr>
                            <th>顯示名稱</th>
                            <th>UUID</th>
                            <th>狀態</th>
                            <th>到期時間</th>
                            <th>登入次數</th>
                            <th>創建時間</th>
                            <th>付款狀態</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="users-tbody">
                        <tr><td colspan="8" style="text-align: center;" id="loading-message">載入中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
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
                
                <div class="section">
                    <h3>📝 UUID 規則說明</h3>
                    <ul>
                        <li><strong>格式:</strong> [前綴]_[編號]_[日期]</li>
                        <li><strong>前綴:</strong> 區分用戶類型 (artale, artale_vip, artale_trial, artale_premium)</li>
                        <li><strong>編號:</strong> 用戶唯一識別碼，可自訂或自動生成 8 位隨機字符</li>
                        <li><strong>日期:</strong> 創建日期，支援多種格式</li>
                        <li><strong>範例:</strong> artale_a1b2c3d4_20241217</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- 付款管理分頁 -->
        <div id="payment-management" class="tab-content">
            <div class="payment-section">
                <h2>💳 綠界金流整合</h2>
                <div class="payment-info">
                    <h4>🚀 即將推出功能:</h4>
                    <ul>
                        <li>✅ 自動付款處理</li>
                        <li>✅ 付款成功自動發放序號</li>
                        <li>✅ 訂單狀態追蹤</li>
                        <li>✅ 退款處理</li>
                        <li>✅ 收益統計</li>
                    </ul>
                </div>
                
                <!-- 訂單列表 (預留) -->
                <div class="section">
                    <h3>📋 訂單管理</h3>
                    <p style="text-align: center; color: #666; padding: 40px;">
                        綠界 API 整合開發中...<br>
                        <small>將支援信用卡、ATM轉帳、超商付款等多種支付方式</small>
                    </p>
                </div>
                
                <!-- 收益統計 (預留) -->
                <div class="section">
                    <h3>📊 收益分析</h3>
                    <div class="stats">
                        <div class="stat-card">
                            <h3>NT$ 0</h3>
                            <p>今日收益</p>
                        </div>
                        <div class="stat-card">
                            <h3>NT$ 0</h3>
                            <p>本月收益</p>
                        </div>
                        <div class="stat-card">
                            <h3>0</h3>
                            <p>待處理訂單</p>
                        </div>
                        <div class="stat-card">
                            <h3>0</h3>
                            <p>成功交易</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let allUsers = [];
        let currentGeneratedUUID = '';
        let ADMIN_TOKEN = '';
        
        // 檢查是否已有儲存的 token
        const savedToken = localStorage.getItem('admin_token');
        if (savedToken) {
            ADMIN_TOKEN = savedToken;
        } else {
            // 先嘗試預設密碼
            ADMIN_TOKEN = 'your-secret-admin-token';
        }
        
        // 測試 token 是否有效
        async function validateToken() {
            try {
                const response = await fetch('/admin/users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                if (response.status === 401) {
                    // Token 無效，要求用戶輸入
                    const userToken = prompt('管理員密碼錯誤，請輸入正確的管理員密碼:');
                    if (!userToken) {
                        alert('需要管理員權限');
                        window.location.href = '/';
                        return false;
                    }
                    ADMIN_TOKEN = userToken;
                    localStorage.setItem('admin_token', ADMIN_TOKEN);
                    
                    // 再次測試
                    const retestResponse = await fetch('/admin/users', {
                        headers: { 'Admin-Token': ADMIN_TOKEN }
                    });
                    
                    if (retestResponse.status === 401) {
                        alert('密碼仍然錯誤，請聯繫管理員');
                        localStorage.removeItem('admin_token');
                        window.location.href = '/';
                        return false;
                    }
                }
                return true;
            } catch (error) {
                console.error('驗證 token 失敗:', error);
                return false;
            }
        }

        // 分頁切換
        function switchTab(tabId) {
            // 隱藏所有分頁內容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 顯示選中的分頁
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }

        // UUID 生成器功能
        function generateUUID() {
            const prefix = document.getElementById('uuid-prefix').value;
            const customId = document.getElementById('uuid-custom-id').value.trim();
            const dateFormat = document.getElementById('uuid-date-format').value;
            
            // 生成用戶ID
            let userId;
            if (customId) {
                userId = customId.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
            } else {
                userId = Math.random().toString(36).substring(2, 10);
            }
            
            // 生成日期
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
            // 切換到用戶管理分頁
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

        // 載入用戶列表
        async function loadUsers() {
            try {
                console.log('開始載入用戶列表...');
                const response = await fetch('/admin/users', {
                    headers: { 'Admin-Token': ADMIN_TOKEN }
                });
                
                console.log('Response status:', response.status);
                
                if (response.status === 401) {
                    alert('管理員密碼錯誤，請重新輸入');
                    localStorage.removeItem('admin_token');
                    location.reload();
                    return;
                }
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (data.success) {
                    allUsers = data.users;
                    renderUsers(allUsers);
                    updateStats(allUsers);
                    console.log('載入成功，用戶數量:', allUsers.length);
                } else {
                    console.error('載入失敗:', data.error);
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
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">暫無用戶數據</td></tr>';
                return;
            }
            
            users.forEach(user => {
                const row = document.createElement('tr');
                const isActive = user.active;
                const isExpired = user.expires_at && new Date(user.expires_at) < new Date();
                
                row.innerHTML = `
                    <td>${user.display_name || 'Unknown'}</td>
                    <td><code style="font-size: 11px;">${user.uuid_preview || 'N/A'}</code></td>
                    <td class="${isActive ? 'status-active' : 'status-inactive'}">
                        ${isActive ? '✅ 啟用' : '❌ 停用'}
                        ${isExpired ? ' (已過期)' : ''}
                    </td>
                    <td>${user.expires_at || '永久'}</td>
                    <td>${user.login_count || 0}</td>
                    <td>${user.created_at || 'Unknown'}</td>
                    <td>${user.payment_status || '手動創建'}</td>
                    <td>
                        <button onclick="editUser('${user.document_id}', '${user.display_name}')" class="btn">編輯</button>
                        <button onclick="toggleUser('${user.document_id}', ${!isActive})" class="btn btn-warning">
                            ${isActive ? '停用' : '啟用'}
                        </button>
                        <button onclick="deleteUser('${user.document_id}', '${user.display_name}')" class="btn btn-danger">刪除</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // 搜尋過濾
        function filterUsers() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const filteredUsers = allUsers.filter(user => 
                user.display_name.toLowerCase().includes(searchTerm) ||
                user.uuid_preview.toLowerCase().includes(searchTerm)
            );
            renderUsers(filteredUsers);
        }

        // 更新統計
        function updateStats(users) {
            const total = users.length;
            const active = users.filter(u => u.active).length;
            const expired = users.filter(u => u.expires_at && new Date(u.expires_at) < new Date()).length;
            
            document.getElementById('total-users').textContent = total;
            document.getElementById('active-users').textContent = active;
            document.getElementById('expired-users').textContent = expired;
            document.getElementById('total-revenue').textContent = '0'; // 待綠界整合
        }

        // 匯出 CSV
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
            ].join('\n');
            
            const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `artale_users_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
        }

        // 創建用戶
        document.getElementById('create-user-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
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
                    document.getElementById('create-user-form').reset();
                    loadUsers();
                } else {
                    alert('創建失敗: ' + data.error);
                }
            } catch (error) {
                alert('創建錯誤: ' + error.message);
            }
        });

        // 編輯用戶
        async function editUser(documentId, currentName) {
            const newName = prompt('新的顯示名稱:', currentName);
            if (!newName || newName === currentName) return;
            
            const newDays = prompt('延長有效期天數:', '30');
            if (!newDays) return;
            
            try {
                const response = await fetch(`/admin/users/${documentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Admin-Token': ADMIN_TOKEN
                    },
                    body: JSON.stringify({
                        display_name: newName,
                        extend_days: parseInt(newDays)
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('用戶更新成功!');
                    loadUsers();
                } else {
                    alert('更新失敗: ' + data.error);
                }
            } catch (error) {
                alert('更新錯誤: ' + error.message);
            }
        }

        // 啟用/停用用戶
        async function toggleUser(documentId, newStatus) {
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

        // 刪除用戶
        async function deleteUser(documentId, displayName) {
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

        // 調試功能
        async function showDebugInfo() {
            try {
                const response = await fetch('/admin/debug');
                const data = await response.json();
                
                const debugInfo = `
調試信息：
- Admin Token 已設定: ${data.admin_token_set}
- Token 預覽: ${data.admin_token_value}
- 預設值: ${data.expected_default}
- 當前使用 Token: ${ADMIN_TOKEN.substring(0, 8)}...
                `;
                
                alert(debugInfo);
            } catch (error) {
                alert('獲取調試信息失敗: ' + error.message);
            }
        }
        
        function clearToken() {
            localStorage.removeItem('admin_token');
            location.reload();
        }
        
        // 頁面載入時自動驗證並載入用戶
        async function initializePage() {
            const tokenValid = await validateToken();
            if (tokenValid) {
                loadUsers();
            }
        }
        
        // 頁面載入時執行
        initializePage();
    </script>
</body>
</html>
"""

def check_admin_token(request):
    """驗證管理員權限"""
    admin_token = request.headers.get('Admin-Token')
    expected_token = os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token')
    return admin_token == expected_token

def generate_secure_uuid(prefix='artale', custom_id=None, date_format='YYYYMMDD'):
    """生成安全的UUID"""
    if custom_id:
        import re
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
    """管理員面板"""
    return render_template_string(ADMIN_TEMPLATE)

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
            
            # 生成顯示用的 UUID (前16位)
            original_uuid = user_data.get('original_uuid', 'Unknown')
            uuid_preview = original_uuid[:16] + '...' if len(original_uuid) > 16 else original_uuid
            
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
                'payment_status': user_data.get('payment_status', '手動創建')
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

@admin_bp.route('/debug', methods=['GET'])
def admin_debug():
    """調試端點 - 檢查環境變數設定"""
    admin_token = os.environ.get('ADMIN_TOKEN', 'NOT_SET')
    return jsonify({
        'admin_token_set': admin_token != 'NOT_SET',
        'admin_token_value': admin_token[:8] + '...' if len(admin_token) > 8 else admin_token,
        'expected_default': 'your-secret-admin-token'
    })

@admin_bp.route('/test-auth', methods=['POST'])
def test_auth():
    """測試認證端點"""
    provided_token = request.headers.get('Admin-Token', '')
    expected_token = os.environ.get('ADMIN_TOKEN', 'your-secret-admin-token')
    
    return jsonify({
        'success': provided_token == expected_token,
        'provided_token_length': len(provided_token),
        'expected_token_length': len(expected_token),
        'tokens_match': provided_token == expected_token,
        'provided_preview': provided_token[:8] + '...' if len(provided_token) > 8 else provided_token,
        'expected_preview': expected_token[:8] + '...' if len(expected_token) > 8 else expected_token
    })
def generate_uuid_api():
    """API 生成 UUID"""
    if not check_admin_token(request):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        prefix = data.get('prefix', 'artale')
        custom_id = data.get('custom_id', '')
        date_format = data.get('date_format', 'YYYYMMDD')
        
        # 生成 UUID
        new_uuid = generate_secure_uuid(prefix, custom_id, date_format)
        
        # 檢查是否已存在
        from app import db
        if db is not None:
            uuid_hash = hashlib.sha256(new_uuid.encode()).hexdigest()
            user_ref = db.collection('authorized_users').document(uuid_hash)
            exists = user_ref.get().exists
        else:
            exists = False
        
        return jsonify({
            'success': True,
            'uuid': new_uuid,
            'exists': exists
        })
        
    except Exception as e:
        logger.error(f"Generate UUID API error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
