"""
manual_routes.py - 操作手冊路由處理（序號驗證版）
"""
from flask import Blueprint, render_template_string, request, jsonify
import hashlib
import logging

logger = logging.getLogger(__name__)

# 創建操作手冊藍圖
manual_bp = Blueprint('manual', __name__, url_prefix='/manual')

# 驗證用戶序號的函數
def verify_user_uuid(uuid_string):
    """驗證用戶UUID是否有效"""
    try:
        from app import db
        if not db:
            return False, "認證服務不可用"
        
        uuid_hash = hashlib.sha256(uuid_string.encode()).hexdigest()
        user_ref = db.collection('authorized_users').document(uuid_hash)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return False, "序號無效"
        
        user_data = user_doc.to_dict()
        
        # 檢查用戶狀態
        if not user_data.get('active', False):
            return False, "帳號已被停用"
        
        # 檢查有效期（如果有的話）
        if 'expires_at' in user_data:
            from datetime import datetime
            expires_at = user_data['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', ''))
            elif hasattr(expires_at, 'timestamp'):
                expires_at = datetime.fromtimestamp(expires_at.timestamp())
            
            if datetime.now() > expires_at:
                return False, "帳號已過期"
        
        return True, "驗證成功"
        
    except Exception as e:
        logger.error(f"UUID驗證錯誤: {str(e)}")
        return False, "驗證服務錯誤"

# 操作手冊 HTML 模板（序號驗證版）
MANUAL_TEMPLATE_WITH_AUTH = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artale GUI 操作手冊 - 圖文教學版</title>
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
            --bg-tertiary: #2a2a2a;
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-muted: #808080;
            --accent-blue: #00d4ff;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            --border-color: #333333;
            --border-hover: #555555;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-accent: linear-gradient(135deg, #00d4ff 0%, #8b5cf6 100%);
            --shadow-lg: 0 15px 35px rgba(0, 0, 0, 0.35);
            --border-radius: 16px;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding-top: 80px;
        }

        /* Navigation */
        .navbar {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(26, 26, 26, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
            z-index: 1000;
            transition: var(--transition);
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.2rem 2rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--text-primary);
            text-decoration: none;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: var(--gradient-accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 2.5rem;
            align-items: center;
        }

        .nav-links a {
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.95rem;
            transition: var(--transition);
            position: relative;
            padding: 0.5rem 0;
        }

        .nav-links a:hover {
            color: var(--accent-blue);
        }

        .back-btn {
            background: var(--gradient-accent);
            color: white;
            padding: 0.7rem 1.5rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .back-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        /* Main Content */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .manual-header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }

        .manual-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .manual-subtitle {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }

        .version-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-green);
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Auth Section */
        .auth-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 3rem;
            text-align: center;
        }

        .auth-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.8rem;
        }

        .auth-icon {
            width: 45px;
            height: 45px;
            background: var(--gradient-accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.2rem;
        }

        .auth-description {
            color: var(--text-secondary);
            margin-bottom: 2rem;
            line-height: 1.7;
        }

        .auth-form {
            max-width: 400px;
            margin: 0 auto;
        }

        .form-group {
            margin-bottom: 1.5rem;
            text-align: left;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .form-input {
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: var(--transition);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }

        .verify-btn {
            width: 100%;
            padding: 12px 16px;
            background: var(--gradient-accent);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .verify-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .verify-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
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

        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            display: none;
        }

        .success-message {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #6ee7b7;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            display: none;
        }

        /* Interface Preview */
        .interface-preview {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            margin-bottom: 3rem;
            text-align: center;
        }

        .interface-preview h3 {
            font-size: 1.4rem;
            margin-bottom: 1.5rem;
            color: var(--accent-blue);
        }

        .gui-mockup {
            background: var(--bg-tertiary);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0 auto;
            max-width: 800px;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 1rem;
            height: 500px;
        }

        .left-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .right-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
        }

        .panel-section {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.8rem;
            margin-bottom: 0.5rem;
        }

        .panel-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--accent-blue);
            margin-bottom: 0.5rem;
        }

        .mock-input {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.4rem 0.6rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        .mock-button {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            cursor: pointer;
            margin-bottom: 0.3rem;
        }

        .mock-button.green {
            background: var(--accent-green);
        }

        .mock-button.red {
            background: var(--accent-red);
        }

        .mock-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .mock-tab {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            cursor: pointer;
        }

        .mock-tab.active {
            background: var(--accent-blue);
            color: white;
        }

        .mock-log {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.8rem;
            font-family: monospace;
            font-size: 0.75rem;
            color: var(--accent-green);
            flex: 1;
            overflow-y: auto;
        }

        .mock-settings {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.8rem;
            font-family: inherit;
            font-size: 0.75rem;
            color: var(--text-secondary);
            flex: 1;
            overflow-y: auto;
        }

        .mock-settings-category {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }

        .mock-settings-category h4 {
            color: var(--accent-blue);
            font-size: 0.8rem;
            margin-bottom: 8px;
        }

        .mock-setting-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            font-size: 0.7rem;
        }

        .mock-setting-item span {
            color: var(--text-secondary);
        }

        /* Locked Content */
        .locked-content {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 3rem;
            margin-bottom: 2rem;
            text-align: center;
            opacity: 0.7;
            position: relative;
        }

        .locked-content::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to bottom, transparent 0%, rgba(10, 10, 10, 0.9) 70%, rgba(10, 10, 10, 1) 100%);
            border-radius: var(--border-radius);
            z-index: 1;
        }

        .locked-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 2;
            text-align: center;
        }

        .locked-icon {
            width: 60px;
            height: 60px;
            background: var(--gradient-accent);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.5rem;
            color: white;
        }

        .locked-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .locked-description {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        /* Authenticated Content */
        .authenticated-content {
            display: none;
        }

        .authenticated-content.show {
            display: block;
        }

        /* 原有的手冊樣式保持不變 */
        .manual-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 2rem;
            scroll-margin-top: 100px;
        }

        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .section-icon {
            width: 45px;
            height: 45px;
            background: var(--gradient-accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.2rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .manual-title {
                font-size: 2rem;
            }
            
            .gui-mockup {
                grid-template-columns: 1fr;
                height: auto;
            }
            
            .nav-links {
                display: none;
            }
            
            .manual-section {
                padding: 2rem;
            }
        }

        /* 購買提示 */
        .purchase-prompt {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 3rem;
            text-align: center;
        }

        .purchase-prompt h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--accent-blue);
        }

        .purchase-prompt p {
            color: var(--text-secondary);
            margin-bottom: 2rem;
            line-height: 1.7;
        }

        .purchase-btn {
            background: var(--gradient-accent);
            color: white;
            padding: 1rem 2rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
        }

        .purchase-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .purchase-prompt h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--accent-blue);
        }

        .purchase-prompt p {
            color: var(--text-secondary);
            margin-bottom: 2rem;
            line-height: 1.7;
        }

        .purchase-btn {
            background: var(--gradient-accent);
            color: white;
            padding: 1rem 2rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
        }

        .purchase-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        # ===== 在這裡添加新的CSS樣式 =====
        
        /* 進階設定改進樣式 */
        .mock-settings-header {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .mock-control-buttons {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        
        .mock-control-btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 0.7rem;
            cursor: pointer;
            font-weight: 500;
            min-width: 60px;
        }
        
        .mock-control-btn.save {
            background: #10b981;
        }
        
        .mock-control-btn.reset {
            background: #f59e0b;
        }
        
        .mock-control-btn.apply {
            background: var(--accent-blue);
        }
        
        .mock-settings-content {
            max-height: 280px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        .mock-settings-content::-webkit-scrollbar {
            width: 6px;
        }
        
        .mock-settings-content::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 3px;
        }
        
        .mock-settings-content::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }
        
        .mock-settings-content::-webkit-scrollbar-thumb:hover {
            background: var(--border-hover);
        }
        
        .mock-settings-category {
            margin-bottom: 15px;
            padding: 10px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
        }
        
        .mock-settings-category h4 {
            color: var(--accent-blue);
            font-size: 0.8rem;
            margin-bottom: 10px;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }
        
        .mock-setting-row {
            display: flex;
            gap: 10px;
            margin-bottom: 8px;
            flex-wrap: wrap;
        }
        
        .mock-setting-item {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 6px;
            font-size: 0.7rem;
            flex: 1;
            min-width: 140px;
        }
        
        .mock-setting-item span {
            color: var(--text-secondary);
            white-space: nowrap;
            min-width: 80px;
            font-size: 0.65rem;
        }
        
        .mock-setting-input {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 2px 4px;
            color: var(--text-primary);
            font-size: 0.65rem;
            width: 50px;
            min-width: 40px;
        }
        
        .mock-setting-select {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 2px 4px;
            color: var(--text-primary);
            font-size: 0.65rem;
            width: 80px;
        }
        
        .mock-setting-checkbox {
            transform: scale(0.8);
        }
        
        /* 角色定位工具樣式 */
        .mock-tool-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px;
            margin-bottom: 10px;
        }
        
        .mock-tool-title {
            color: var(--accent-blue);
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .mock-tool-content {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        
        .mock-tool-btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 0.7rem;
            cursor: pointer;
        }
        
        .mock-tool-status {
            color: #10b981;
            font-size: 0.65rem;
        }
        
        .mock-tool-preview {
            margin-top: 4px;
        }
        
        .mock-preview-box {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 6px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.65rem;
            min-height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* 技能網格樣式 */
        .mock-skill-grid {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            margin: 8px 0;
            overflow: hidden;
        }
        
        .mock-skill-header {
            background: var(--bg-tertiary);
            display: grid;
            grid-template-columns: 1fr 0.6fr 0.8fr 0.5fr;
            gap: 6px;
            padding: 6px;
            font-size: 0.65rem;
            font-weight: 600;
            color: var(--accent-blue);
            border-bottom: 1px solid var(--border-color);
        }
        
        .mock-skill-row {
            display: grid;
            grid-template-columns: 1fr 0.6fr 0.8fr 0.5fr;
            gap: 6px;
            padding: 6px;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.65rem;
        }
        
        .mock-skill-row:last-child {
            border-bottom: none;
        }
        
        .mock-skill-row span {
            color: var(--text-secondary);
        }
        
        .mock-skill-input {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 2px 4px;
            color: var(--text-primary);
            font-size: 0.65rem;
            width: 100%;
        }

        /* 新增的界面預覽樣式 */
        
        /* 用戶信息和統計區域 */
        .mock-user-info, .mock-stats-mini {
            margin-top: 0.5rem;
            padding: 0.3rem;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }
        
        /* 怪物管理標籤頁 */
        .mock-monster-tabs {
            display: flex;
            gap: 2px;
            margin-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .mock-monster-tab {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            padding: 4px 8px;
            font-size: 0.65rem;
            cursor: pointer;
            color: var(--text-secondary);
        }
        
        .mock-monster-tab.active {
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }
        
        .mock-monster-content {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 0 6px 6px 6px;
            padding: 8px;
            margin-bottom: 8px;
        }
        
        /* 怪物搜尋區域 */
        .mock-monster-search {
            display: flex;
            gap: 4px;
            margin-bottom: 6px;
        }
        
        .mock-search-input {
            flex: 1;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 3px 6px;
            color: var(--text-primary);
            font-size: 0.65rem;
        }
        
        .mock-search-btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 3px;
            padding: 3px 8px;
            font-size: 0.65rem;
            cursor: pointer;
        }
        
        /* 怪物控制區域 */
        .mock-monster-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            font-size: 0.65rem;
        }
        
        .mock-count {
            color: var(--text-secondary);
        }
        
        .mock-monster-ctrl-btns {
            display: flex;
            gap: 3px;
        }
        
        .mock-ctrl-btn {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            padding: 2px 6px;
            font-size: 0.6rem;
            cursor: pointer;
            color: var(--text-primary);
        }
        
        /* 怪物列表 */
        .mock-monster-list {
            max-height: 80px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 3px;
            background: var(--bg-secondary);
        }
        
        .mock-monster-item {
            padding: 3px 6px;
            font-size: 0.65rem;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .mock-monster-item:last-child {
            border-bottom: none;
        }
        
        .mock-monster-item input[type="checkbox"] {
            transform: scale(0.8);
        }
        
        /* 搜尋狀態 */
        .mock-search-status {
            text-align: center;
            padding: 8px;
            color: var(--accent-orange);
            font-size: 0.65rem;
            font-style: italic;
        }
        
        /* 下載控制區域 */
        .mock-download-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px solid var(--border-color);
        }
        
        .mock-download-btn {
            background: var(--accent-green);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 0.7rem;
            cursor: pointer;
            font-weight: 500;
        }
        
        .mock-checkbox-label {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 0.65rem;
            color: var(--text-secondary);
            cursor: pointer;
        }
        
        .mock-checkbox-label input[type="checkbox"] {
            transform: scale(0.8);
        }
        
        /* 繩子列表 */
        .mock-rope-list {
            max-height: 60px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 3px;
            background: var(--bg-secondary);
            margin-top: 6px;
        }
        
        .mock-rope-item {
            padding: 3px 6px;
            font-size: 0.65rem;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .mock-rope-item:last-child {
            border-bottom: none;
        }
        
        .mock-rope-item small {
            margin-left: auto;
            color: var(--text-muted);
            font-size: 0.6rem;
        }
        
        /* 工具描述 */
        .mock-tool-desc {
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 4px;
            font-style: italic;
        }
        
        /* 健康測試按鈕 */
        .mock-health-test-btns {
            display: flex;
            gap: 6px;
            margin-top: 8px;
            flex-wrap: wrap;
        }
        
        .mock-test-btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 3px 6px;
            font-size: 0.65rem;
            cursor: pointer;
            flex: 1;
            min-width: 70px;
        }
        
        /* 紅色按鈕變體 */
        .mock-tool-btn.red {
            background: var(--accent-red);
        }
        
        .mock-tool-btn.red:hover {
            background: darkred;
        }
        
        /* 滾動條樣式 */
        .mock-monster-list::-webkit-scrollbar,
        .mock-rope-list::-webkit-scrollbar {
            width: 4px;
        }
        
        .mock-monster-list::-webkit-scrollbar-track,
        .mock-rope-list::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 2px;
        }
        
        .mock-monster-list::-webkit-scrollbar-thumb,
        .mock-rope-list::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 2px;
        }
        
        /* 響應式調整 */
        @media (max-width: 768px) {
            .mock-monster-controls {
                flex-direction: column;
                gap: 4px;
                align-items: flex-start;
            }
            
            .mock-monster-ctrl-btns {
                align-self: stretch;
                justify-content: space-between;
            }
            
            .mock-download-controls {
                flex-direction: column;
                gap: 6px;
                align-items: stretch;
            }
            
            .mock-health-test-btns {
                flex-direction: column;
            }
            
            .mock-monster-tabs {
                flex-wrap: wrap;
            }
        }
        
        # ===== CSS樣式添加到這裡結束 =====
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="/products" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-gamepad"></i>
                </div>
                <span>Artale Script</span>
            </a>
            <ul class="nav-links">
                <li><a href="#interface">界面介紹</a></li>
                <li><a href="#login">登入教學</a></li>
                <li><a href="#basic-usage">基本操作</a></li>
                <li><a href="#advanced">進階設定</a></li>
                <li><a href="#tools">工具功能</a></li>
                <li><a href="#troubleshooting">常見問題</a></li>
            </ul>
            <a href="/products" class="back-btn">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
    </nav>

    <div class="container">
        <!-- Manual Header -->
        <div class="manual-header">
            <h1 class="manual-title">Artale Script GUI 操作手冊</h1>
            <p class="manual-subtitle">圖形化界面操作指南 - 快速上手必備教學</p>
            <span class="version-badge">GUI版本 v1.2.0</span>
        </div>

        <!-- 界面預覽部分 - 更完整版本 -->
        <div class="interface-preview">
            <h3>
                <i class="fas fa-desktop"></i>
                主界面預覽
            </h3>
            <div class="gui-mockup">
                <div class="left-panel">
                    <div class="panel-section">
                        <div class="panel-title">登入驗證</div>
                        <div class="mock-input">請輸入您的授權 UUID</div>
                        <button class="mock-button">登入</button>
                        <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">狀態: 未登入</div>
                        <div class="mock-user-info">
                            <div style="font-size: 0.65rem; color: var(--text-secondary); margin-top: 0.3rem;">
                                用戶信息將在登入後顯示
                            </div>
                        </div>
                    </div>
                    <div class="panel-section">
                        <div class="panel-title">腳本控制</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem;">腳本狀態: 未運行</div>
                        <div style="display: flex; gap: 0.3rem; margin-bottom: 0.5rem;">
                            <button class="mock-button green" style="flex: 1;">開始</button>
                            <button class="mock-button red" style="flex: 1;">停止</button>
                        </div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">運行時間: 00:00:00</div>
                        <div class="mock-stats-mini">
                            <div style="font-size: 0.65rem; color: var(--text-secondary); margin-top: 0.3rem;">
                                檢測次數: 0<br>
                                血量: 100% | 藍量: 100%<br>
                                被動技能: 4個啟用
                            </div>
                        </div>
                    </div>
                </div>
                <div class="right-panel">
                    <div class="mock-tabs">
                        <div class="mock-tab active" onclick="showMockTab('log')">即時日誌</div>
                        <div class="mock-tab" onclick="showMockTab('settings')">進階設定</div>
                    </div>
                    <div class="mock-log" id="mock-log-tab">
                        [12:34:56] 歡迎使用 Artale Script GUI<br>
                        [12:34:56] 認證系統已就緒<br>
                        [12:34:56] 請輸入您的授權 UUID 以開始使用<br>
                        [12:34:56] 配置管理器初始化完成<br>
                        [12:34:56] 腳本包裝器初始化完成<br>
                        [12:34:56] 提示: 只有授權用戶才能使用腳本功能<br>
                        [12:34:56] 登入後確保遊戲視窗已開啟，然後點擊開始腳本<br>
                        [12:34:56] 怪物下載功能已整合至進階設定中<br>
                        [12:34:57] 血量監控系統待命中<br>
                        [12:34:57] 紅點檢測系統待命中<br>
                        [12:34:57] 被動技能管理器待命中
                    </div>
                    <div class="mock-settings" id="mock-settings-tab" style="display: none;">
                        <!-- 頂部控制按鈕區域 -->
                        <div class="mock-settings-header">
                            <h4 style="color: var(--accent-blue); margin: 0 0 10px 0; font-size: 0.9rem;">配置設定</h4>
                            <div class="mock-control-buttons">
                                <button class="mock-control-btn save">保存設定</button>
                                <button class="mock-control-btn reset">重置默認</button>
                                <button class="mock-control-btn apply">應用更改</button>
                            </div>
                        </div>
                        
                        <!-- 可滾動的配置內容 -->
                        <div class="mock-settings-content">
                            <!-- 怪物檢測與攻擊配置 -->
                            <div class="mock-settings-category">
                                <h4>怪物檢測與攻擊配置</h4>
                                
                                <!-- 角色定位工具 -->
                                <div class="mock-tool-section">
                                    <div class="mock-tool-title">📸 角色定位工具</div>
                                    <div class="mock-tool-content">
                                        <button class="mock-tool-btn">開始擷取角色ID</button>
                                        <span class="mock-tool-status">狀態: 就緒</span>
                                    </div>
                                    <div class="mock-tool-preview">
                                        <div class="mock-preview-box">當前角色ID: 尚未擷取</div>
                                    </div>
                                    <div class="mock-tool-desc">
                                        用於擷取角色下方的ID圖片，提高腳本檢測精確度
                                    </div>
                                </div>
                                
                                <!-- 怪物管理區域 -->
                                <div class="mock-tool-section">
                                    <div class="mock-tool-title">🎯 怪物管理</div>
                                    <div class="mock-monster-tabs">
                                        <button class="mock-monster-tab active" onclick="showMockMonsterTab('downloaded')">已下載</button>
                                        <button class="mock-monster-tab" onclick="showMockMonsterTab('search')">怪物搜尋</button>
                                    </div>
                                    
                                    <!-- 已下載怪物 -->
                                    <div class="mock-monster-content" id="mock-downloaded-tab">
                                        <div class="mock-monster-search">
                                            <input type="text" placeholder="搜尋已下載的怪物..." class="mock-search-input">
                                            <button class="mock-search-btn">清除</button>
                                        </div>
                                        <div class="mock-monster-controls">
                                            <span class="mock-count">已下載: 12 個怪物</span>
                                            <div class="mock-monster-ctrl-btns">
                                                <button class="mock-ctrl-btn">全選</button>
                                                <button class="mock-ctrl-btn">全不選</button>
                                                <button class="mock-ctrl-btn">刷新</button>
                                            </div>
                                        </div>
                                        <div class="mock-monster-list">
                                            <div class="mock-monster-item">
                                                <input type="checkbox" checked> <span>綠色蝸牛 (green_snail) - 4 張圖片</span>
                                            </div>
                                            <div class="mock-monster-item">
                                                <input type="checkbox" checked> <span>橙色蘑菇 (orange_mushroom) - 6 張圖片</span>
                                            </div>
                                            <div class="mock-monster-item">
                                                <input type="checkbox"> <span>藍色史萊姆 (blue_slime) - 8 張圖片</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- 怪物搜尋 -->
                                    <div class="mock-monster-content" id="mock-search-tab" style="display: none;">
                                        <div class="mock-monster-search">
                                            <input type="text" placeholder="輸入怪物名稱..." class="mock-search-input">
                                            <button class="mock-search-btn">清除</button>
                                        </div>
                                        <div class="mock-search-status">載入中...</div>
                                        <div class="mock-monster-list">
                                            <div class="mock-monster-item">
                                                <input type="checkbox"> <span>紅色蝸牛 -> Red Snail (等級: 3)</span>
                                            </div>
                                            <div class="mock-monster-item">
                                                <input type="checkbox"> <span>石頭精靈 -> Stone Golem (等級: 45)</span>
                                            </div>
                                        </div>
                                        <div class="mock-download-controls">
                                            <button class="mock-download-btn">📥 下載勾選怪物</button>
                                            <label class="mock-checkbox-label">
                                                <input type="checkbox" checked> 跳過死亡動畫
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>攻擊按鍵:</span>
                                        <input type="text" value="z" class="mock-setting-input">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>次要攻擊按鍵:</span>
                                        <input type="text" value="x" class="mock-setting-input">
                                    </div>
                                </div>
                                
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>攻擊範圍:</span>
                                        <input type="text" value="100" class="mock-setting-input">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>主要攻擊機率:</span>
                                        <input type="text" value="0.8" class="mock-setting-input">
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 被動技能系統配置 -->
                            <div class="mock-settings-category">
                                <h4>被動技能系統配置</h4>
                                
                                <div class="mock-setting-item">
                                    <span>啟用被動技能系統:</span>
                                    <input type="checkbox" checked class="mock-setting-checkbox">
                                </div>
                                
                                <!-- 技能設定表格 -->
                                <div class="mock-skill-grid">
                                    <div class="mock-skill-header">
                                        <span>技能</span>
                                        <span>按鍵</span>
                                        <span>冷卻(秒)</span>
                                        <span>啟用</span>
                                    </div>
                                    <div class="mock-skill-row">
                                        <span>被動技能 1</span>
                                        <input type="text" value="q" class="mock-skill-input">
                                        <input type="text" value="30.0" class="mock-skill-input">
                                        <input type="checkbox" checked class="mock-setting-checkbox">
                                    </div>
                                    <div class="mock-skill-row">
                                        <span>被動技能 2</span>
                                        <input type="text" value="w" class="mock-skill-input">
                                        <input type="text" value="45.0" class="mock-skill-input">
                                        <input type="checkbox" checked class="mock-setting-checkbox">
                                    </div>
                                    <div class="mock-skill-row">
                                        <span>被動技能 3</span>
                                        <input type="text" value="e" class="mock-skill-input">
                                        <input type="text" value="60.0" class="mock-skill-input">
                                        <input type="checkbox" class="mock-setting-checkbox">
                                    </div>
                                </div>
                            </div>

                            <div class="mock-settings-category">
                                <h4>增強移動系統配置</h4>
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>啟用跳躍移動:</span>
                                        <input type="checkbox" checked class="mock-setting-checkbox">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>跳躍移動機率:</span>
                                        <input type="text" value="0.3" class="mock-setting-input">
                                    </div>
                                </div>
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>啟用位移技能移動:</span>
                                        <input type="checkbox" class="mock-setting-checkbox">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>位移技能按鍵:</span>
                                        <input type="text" value="shift" class="mock-setting-input">
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 攀爬配置 -->
                            <div class="mock-settings-category">
                                <h4>攀爬配置</h4>
                                
                                <!-- 繩子定位工具 -->
                                <div class="mock-tool-section">
                                    <div class="mock-tool-title">🧗 繩子定位工具</div>
                                    <div class="mock-tool-content">
                                        <button class="mock-tool-btn">新增繩子截圖</button>
                                        <button class="mock-tool-btn red">刪除選中</button>
                                        <span class="mock-tool-status">繩子數量: 3</span>
                                    </div>
                                    <div class="mock-rope-list">
                                        <div class="mock-rope-item">
                                            <input type="checkbox"> <span>rope_1</span> <small>建立: 2024-01-15</small>
                                        </div>
                                        <div class="mock-rope-item">
                                            <input type="checkbox"> <span>rope_2</span> <small>建立: 2024-01-15</small>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>啟用爬繩功能:</span>
                                        <input type="checkbox" checked class="mock-setting-checkbox">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>爬繩冷卻時間:</span>
                                        <input type="text" value="5.0" class="mock-setting-input">
                                    </div>
                                </div>
                            </div>

                            <div class="mock-settings-category">
                                <h4>紅點偵測與換頻道配置</h4>
                                <div class="mock-setting-item">
                                    <span>啟用紅點偵測:</span>
                                    <input type="checkbox" checked class="mock-setting-checkbox">
                                </div>
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>紅點檢測最小時間:</span>
                                        <input type="text" value="3.0" class="mock-setting-input">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>紅點檢測最大時間:</span>
                                        <input type="text" value="8.0" class="mock-setting-input">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mock-settings-category">
                                <h4>血量監控配置</h4>
                                <div class="mock-setting-item">
                                    <span>啟用血量監控:</span>
                                    <input type="checkbox" checked class="mock-setting-checkbox">
                                </div>
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>HP閾值:</span>
                                        <input type="text" value="0.3" class="mock-setting-input">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>MP閾值:</span>
                                        <input type="text" value="0.2" class="mock-setting-input">
                                    </div>
                                </div>
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>補血冷卻時間:</span>
                                        <input type="text" value="1.0" class="mock-setting-input">
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>自動檢測血條:</span>
                                        <input type="checkbox" checked class="mock-setting-checkbox">
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 效能優化配置 -->
                            <div class="mock-settings-category">
                                <h4>效能優化配置</h4>
                                
                                <div class="mock-setting-row">
                                    <div class="mock-setting-item">
                                        <span>主循環檢測間隔:</span>
                                        <input type="text" value="0.05" class="mock-setting-input">
                                        <span style="font-size: 0.6rem;">秒</span>
                                    </div>
                                    <div class="mock-setting-item">
                                        <span>監控更新頻率:</span>
                                        <input type="text" value="10" class="mock-setting-input">
                                        <span style="font-size: 0.6rem;">FPS</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        

        <!-- 序號驗證區域 -->
        <div class="auth-section" id="auth-section">
            <h2 class="auth-title">
                <div class="auth-icon">
                    <i class="fas fa-key"></i>
                </div>
                查看詳細教學
            </h2>
            <p class="auth-description">
                詳細的操作教學僅供已購買服務的用戶查看。<br>
                請輸入您的授權序號以解鎖完整教學內容。
            </p>
            <div class="auth-form">
                <div class="form-group">
                    <label for="uuid-input">授權序號</label>
                    <input type="password" id="uuid-input" class="form-input" placeholder="請輸入您的授權序號">
                </div>
                <button class="verify-btn" onclick="verifyUUID()">
                    <span id="verify-text">驗證並解鎖</span>
                    <div class="loading" id="verify-loading"></div>
                </button>
                <div class="error-message" id="error-message"></div>
                <div class="success-message" id="success-message"></div>
            </div>
        </div>

        <!-- 購買提示 -->
        <div class="purchase-prompt">
            <h3>
                <i class="fas fa-shopping-cart"></i>
                還沒有序號嗎？
            </h3>
            <p>
                立即購買 Artale Script 服務，獲得完整的操作教學和技術支援。<br>
                我們提供多種方案供您選擇，價格實惠，服務專業。
            </p>
            <a href="/products#services" class="purchase-btn">
                <i class="fas fa-star"></i>
                <span>立即購買</span>
            </a>
        </div>

        <!-- 詳細教學內容 - 需要驗證後才能查看 -->
        <div class="authenticated-content" id="authenticated-content">
            <!-- Login Section -->
            <section id="login" class="manual-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-sign-in-alt"></i>
                    </div>
                    登入教學
                </h2>

                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        遊戲視窗設定重要提醒
                    </div>
                    <strong>請務必將遊戲設定為 1280x720 視窗模式才能使用腳本！</strong><br><br>
                    <strong>設定步驟：</strong><br>
                    1. 進入遊戲後，按右上角 <kbd>...</kbd> 鍵打開遊戲選單<br>
                    2. 點擊「設定」→「圖形」<br>
                    3. 將「解析度」設定為 <strong>1280x720</strong><br>
                    4. 確認保持「視窗模式」 ✓<br>
                    <strong>為什麼要使用 1280x720？</strong><br>
                    • 這是腳本預設的解析度，檢測精確度最高<br>
                    • 視窗大小適中，方便操作和監控<br>
                    • 與腳本的圖像識別系統完美匹配<br>
                    • 效能負擔較輕，運行更穩定
                </div>

                <div class="step-container">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-title">準備工作</div>
                        <div class="step-content">
                            <p>確保遊戲已設定為 1280x720 視窗模式，然後啟動 Artale Script GUI 程式。</p>
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-desktop"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">視窗設定檢查</div>
                                    <div class="visual-desc">確認遊戲視窗可見且未被遮蔽並保持前景，解析度為 1280x720。</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-title">輸入授權序號</div>
                        <div class="step-content">
                            <p>在左側面板的「登入驗證」區域中，將您購買時獲得的序號輸入到文字框中。</p>
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-key"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">UUID 輸入框</div>
                                    <div class="visual-desc">UUID 為隱藏顯示，確保輸入正確後點擊「登入」按鈕。</div>
                                </div>
                            </div>
                            <div class="tip-box">
                                <div class="box-title">
                                    <i class="fas fa-lightbulb"></i>
                                    小提示
                                </div>
                                建議使用複製貼上方式輸入序號，避免輸入錯誤。序號區分大小寫。
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-title">認證成功</div>
                        <div class="step-content">
                            <p>登入成功後，左側面板會顯示用戶信息，「腳本控制」區域的按鈕會變為可用狀態。</p>
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-check-circle"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">登入成功指示</div>
                                    <div class="visual-desc">狀態變更為「已登入」，顯示用戶名稱和權限信息。</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Basic Usage Section -->
            <section id="basic-usage" class="manual-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-play"></i>
                    </div>
                    基本操作
                </h2>

                <div class="step-container">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-title">啟動遊戲</div>
                        <div class="step-content">
                            <p>在使用腳本前，請確保 MapleStory Worlds-Artale 遊戲已經開啟並處於遊戲畫面。</p>
                            <div class="warning-box">
                                <div class="box-title">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    重要提醒
                                </div>
                                遊戲視窗必須可見且未被其他視窗遮蔽並保持前景，腳本才能正常運作。
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-title">開始腳本</div>
                        <div class="step-content">
                            <p>點擊左側面板「腳本控制」區域的綠色「開始」按鈕，啟動腳本功能。</p>
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-power-off"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">控制按鈕</div>
                                    <div class="visual-desc">綠色「開始」按鈕啟動腳本，紅色「停止」按鈕停止腳本。</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-title">監控運行狀態</div>
                        <div class="step-content">
                            <p>右側面板的「即時日誌」選項卡會顯示腳本的運行狀態和檢測信息。</p>
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-chart-line"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">狀態監控</div>
                                    <div class="visual-desc">運行時間、檢測次數、腳本狀態等信息會即時更新。</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Advanced Settings Section -->
            <section id="advanced" class="manual-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-cogs"></i>
                    </div>
                    進階設定詳細說明
                </h2>

                <p style="margin-bottom: 2rem; color: var(--text-secondary);">
                    進階設定面板提供豐富的自定義選項，讓您調整腳本行為以符合個人需求。所有設定都會自動保存並在重啟時載入。
                </p>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-crosshairs"></i>
                        怪物檢測與攻擊配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">跳躍按鍵 (JUMP_KEY)</div>
                            <div class="param-range">預設值：z</div>
                            <div class="param-desc">跳躍的按鍵，支援單字符或特殊按鍵名稱（如 alt、ctrl、space）</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">主要攻擊按鍵 (ATTACK_KEY)</div>
                            <div class="param-range">預設值：z</div>
                            <div class="param-desc">主要攻擊技能的按鍵，支援單字符或特殊按鍵名稱（如 alt、ctrl、space）</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">次要攻擊按鍵 (SECONDARY_ATTACK_KEY)</div>
                            <div class="param-range">預設值：x</div>
                            <div class="param-desc">次要攻擊技能的按鍵，可用於群體攻擊或特殊技能</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">啟用次要攻擊按鍵 (ENABLE_SECONDARY_ATTACK)</div>
                            <div class="param-range">預設值：False</div>
                            <div class="param-desc">是否啟用次要攻擊，啟用則機率性觸發次要攻擊</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">主要攻擊機率 (PRIMARY_ATTACK_CHANCE)</div>
                            <div class="param-range">範圍：0.0-1.0</div>
                            <div class="param-desc">使用主要攻擊的機率，0.8表示80%機率使用主要攻擊</div>
                        <div class="config-param-card">
                            <div class="param-name">次要攻擊機率 (SECONDARY_ATTACK_CHANCE)</div>
                            <div class="param-range">範圍：0.0-1.0(若有開啟需主要攻擊機率+次要攻擊機率=1)</div>
                            <div class="param-desc">使用次要攻擊的機率，0.2表示20%機率使用主要攻擊</div>
                        <div class="config-param-card">
                            <div class="param-name">攻擊範圍X軸(像素) (ATTACK_RANGE_X)</div>
                            <div class="param-range">預設值：400(近戰建議~300、法師建議400~600、弓箭、鏢建議600~)</div>
                            <div class="param-desc">角色攻擊範圍的橫向距離，數值越大檢測範圍越廣</div>
                        </div>                            
                        <div class="config-param-card">
                            <div class="param-name">上跳攻擊模式 (JUMP_ATTACK_MOMDE)</div>
                            <div class="param-range">一般、法師、不啟用</div>
                            <div class="param-desc">上方怪物的處理:一般(跳+攻擊)、法師(順移+攻擊)、不啟用(直接攻擊)</div>
                        </div>
                    </div>
                </div>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-magic"></i>
                        被動技能系統配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">啟用被動技能 (ENABLE_PASSIVE_SKILLS)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">總開關，控制是否啟用被動技能自動使用功能</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">被動技能按鍵 (PASSIVE_SKILL_1~4_KEY)</div>
                            <div class="param-range">預設值：1, 2, 3, 4</div>
                            <div class="param-desc">四個被動技能的按鍵設定，支援任意按鍵配置</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">技能冷卻時間 (PASSIVE_SKILL_1~4_COOLDOWN)</div>
                            <div class="param-range">範圍：1.0-99999.0 秒</div>
                            <div class="param-desc">每個技能的冷卻時間，建議根據實際技能冷卻設定</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">隨機延遲 (PASSIVE_SKILL_RANDOM_DELAY)</div>
                            <div class="param-range">最小值：0.0-5.0 秒<br>最大值：0.0-10.0 秒</div>
                            <div class="param-desc">技能使用間的隨機延遲，讓行為更自然</div>
                        </div>
                    </div>
                </div>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-running"></i>
                        增強移動系統配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">啟用跳躍移動 (ENABLE_JUMP_MOVEMENT)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">允許角色在移動時隨機跳躍，適應具高差地圖</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">跳躍移動機率 (JUMP_MOVEMENT_CHANCE)</div>
                            <div class="param-range">範圍：0.0-1.0</div>
                            <div class="param-desc">移動時觸發跳躍的機率</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">啟用位移技能移動 (ENABLE_DASH_MOVEMENT)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">允許角色在移動時，同時按下位移技能鍵，增加移動效率</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">位移技能移動機率 (DASH_MOVEMENT_CHANCE)</div>
                            <div class="param-range">範圍：0.0-1.0</div>
                            <div class="param-desc">移動時觸發位移技能鍵的機率</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">位移技能按鍵 (DASH_SKILL_KEY)</div>
                            <div class="param-range">預設值：x</div>
                            <div class="param-desc">位移技能的按鍵</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">位移技能冷卻時間 (DASH_SKILL_COOLDOWN)</div>
                            <div class="param-range">預設值：3秒</div>
                            <div class="param-desc">再次觸發的冷卻時間</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">啟用隨機下跳功能 (ENABLE_DOWN_JUMP)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">允許角色在移動時隨機下跳</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">下跳觸發機率 (DOWN_JUMP_CHANCE)</div>
                            <div class="param-range">範圍：0.0-1.0</div>
                            <div class="param-desc">移動時觸發下跳的機率</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">下跳冷卻時間(秒) (ENABLE_JUMP_MOVEMENT)</div>
                            <div class="param-range">預設值：5秒</div>
                            <div class="param-desc">觸發下跳的冷卻時間</div>
                        </div>
                    </div>
                </div>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-climbing"></i>
                        攀爬配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">啟用爬繩功能 (ENABLE_ROPE_CLIMBING)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">啟用自動爬繩功能，清怪完畢後自動尋找並攀爬繩索</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">起跳離繩索(最小距離) (ROPE_MIN_DISTANCE)</div>
                            <div class="param-range">預設值：60</div>
                            <div class="param-desc">該值依據自身跳躍與移動值做設定(60~65為無任何加成最佳設定)</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">起跳離繩索(最大距離) (ROPE_MAX_DISTANCE)</div>
                            <div class="param-range">預設值：65</div>
                            <div class="param-desc">該值依據自身跳躍與移動值做設定(60~65為無任何加成最佳設定)</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">爬繩冷卻時間 (ROPE_COOLDOWN_TIME)</div>
                            <div class="param-range">預設值：60秒</div>
                            <div class="param-desc">爬繩與爬繩之間的冷卻時間，無論失敗與成功都會計算，多層地圖可將該值設小</div>
                        </div>
                    </div>
                </div>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-exclamation-circle"></i>
                        紅點偵測與換頻道配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">啟用紅點偵測 (ENABLE_RED_DOT_DETECTION)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">監控畫面中的紅點圖示，檢測到玩家時自動換頻道</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">紅點檢測最小時間(秒) (RED_DOT_MIN_TIME)</div>
                            <div class="param-range">預設值：5秒</div>
                            <div class="param-desc">紅點出現幾秒(最小)進行換頻</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">紅點檢測最大時間(秒) (RED_DOT_MAX_TIME)</div>
                            <div class="param-range">預設值：10秒</div>
                            <div class="param-desc">紅點出現幾秒(最大)進行換頻、設為1秒(最小)~1秒(最大)會秒換頻</div>
                        </div>                                                
                    </div>
                </div>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-heart"></i>
                        血量監控配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">啟用血量監控 (ENABLE_HEALTH_MONITOR)</div>
                            <div class="param-range">選項：開啟/關閉</div>
                            <div class="param-desc">即時監控角色血量和藍量，自動使用恢復道具</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">HP閥值</div>
                            <div class="param-range">預設值：0.5</div>
                            <div class="param-desc">HP閥值至50%時，進行補血</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">MP閥值</div>
                            <div class="param-range">預設值：0.5</div>
                            <div class="param-desc">MP閥值至50%時，進行補藍</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">補血按鍵</div>
                            <div class="param-range">預設值：pageup</div>
                            <div class="param-desc">補血按鍵</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">補藍按鍵</div>
                            <div class="param-range">預設值：pagedown</div>
                            <div class="param-desc">補藍按鍵</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">補血冷卻</div>
                            <div class="param-range">預設值：1秒</div>
                            <div class="param-desc">喝藥水的冷卻時間</div>
                        </div>
                        <div class="config-param-card">
                            <div class="param-name">補藍冷卻</div>
                            <div class="param-range">預設值：1秒</div>
                            <div class="param-desc">喝藥水的冷卻時間</div>
                        </div>
                    </div>
                </div>

                <div class="config-section-detailed">
                    <h3 class="config-category-title">
                        <i class="fas fa-heart"></i>
                        效能優化配置
                    </h3>
                    <div class="config-param-grid">
                        <div class="config-param-card">
                            <div class="param-name">主循環檢測間隔 (ENABLE_HEALTH_MONITOR)</div>
                            <div class="param-range">預設值：0.01</div>
                            <div class="param-desc">螢幕擷取畫面頻率，依據電腦效能設置，若太卡請設定0.05~</div>
                        </div>
                    </div>
                </div>                

            </section>

            <!-- Tools Section -->
            <section id="tools" class="manual-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-tools"></i>
                    </div>
                    工具功能詳細教學
                </h2>

                <div class="step-container">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-title">角色定位工具</div>
                        <div class="step-content">
                            <p>用於擷取角色下方的ID圖片，提高腳本檢測精確度。</p>
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-camera"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">使用步驟</div>
                                    <div class="visual-desc">
                                        1. 點擊「📸 開始擷取角色ID」按鈕<br>
                                        2. 程式會自動尋找並截取遊戲視窗<br>
                                        3. 在彈出的視窗中框選角色下方的名稱區域<br>
                                        4. 點擊「✅ 確認選擇」完成擷取
                                    </div>
                                </div>
                            </div>
                            <div class="tip-box">
                                <div class="box-title">
                                    <i class="fas fa-lightbulb"></i>
                                    使用技巧
                                </div>
                                <strong>最佳擷取時機：</strong><br>
                                • 角色站立不動時進行擷取<br>
                                • 選擇包含完整角色名稱的矩形區域<br>
                                • 避免選擇到背景或其他UI元素<br>
                                • 建議在明亮的地圖上進行擷取
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-title">怪物搜尋下載系統</div>
                        <div class="step-content">
                            <p>從官方API下載怪物圖片，支援搜尋和批量下載功能。</p>
                            
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-search"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">搜尋步驟</div>
                                    <div class="visual-desc">
                                        1. 在搜尋框中輸入怪物名稱（支援中文）<br>
                                        2. 系統會即時過濾顯示匹配的怪物<br>
                                        3. 每次最多顯示50個結果避免卡頓<br>
                                        4. 點擊「清除」可重置搜尋結果
                                    </div>
                                </div>
                            </div>
                            
                            <div class="warning-box">
                                <div class="box-title">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    搜尋注意事項
                                </div>
                                • 首次載入需要從API獲取怪物資料，請耐心等待<br>
                                • 搜尋支援部分匹配，如搜尋「寶」會找到嫩寶、紅寶等怪物<br>
                                • 如果結果太多，請使用更具體的搜尋條件
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-title">已下載怪物管理</div>
                        <div class="step-content">
                            <p>管理和選擇已下載的怪物圖片，控制腳本要檢測哪些怪物類型。</p>
                            
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-folder-open"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">已下載列表功能</div>
                                    <div class="visual-desc">
                                        1. 自動掃描並顯示已下載的怪物圖片<br>
                                        2. 顯示怪物的中文名稱和圖片數量<br>
                                        3. 支援即時搜尋功能，快速找到特定怪物<br>
                                        4. 提供勾選機制選擇要啟用的怪物進行檢測
                                    </div>
                                </div>
                            </div>
                            
                            <div class="warning-box">
                                <div class="box-title">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    效能優化重要提醒
                                </div>
                                <strong>建議只啟用當前地圖會出現的怪物！</strong><br><br>
                                <strong>原因說明：</strong><br>
                                • 啟用過多怪物會'顯著'影響檢測速度<br>
                                • 每個怪物圖片都需要進行模板匹配計算<br>
                                • 建議同時啟用的怪物不超過100張圖片<br>
                                • 切換練功地圖時記得更新怪物選擇<br>
                                • 只選擇外觀特徵明顯、不易混淆的怪物
                            </div>
                            
                            <div class="info-box">
                                <div class="box-title">
                                    <i class="fas fa-info-circle"></i>
                                    詳細操作說明
                                </div>
                                <strong>搜尋與過濾：</strong><br>
                                • 支援中文和英文名稱搜尋<br>
                                • 即時過濾，輸入關鍵字立即顯示匹配結果<br>
                                • 點擊「清除」按鈕重置搜尋，顯示所有怪物<br>
                                • 搜尋功能不區分大小寫<br><br>
                                
                                <strong>選擇與管理：</strong><br>
                                • ✅ 勾選想要啟用檢測的怪物<br>
                                • 🔲 取消勾選停用特定怪物檢測<br>
                                • 「全選」快速選擇目前顯示的所有怪物<br>
                                • 「全不選」快速取消所有選擇<br>
                                • 「刷新」重新掃描 assets/monsters 資料夾
                            </div>
                        </div>
                    </div>
                    
                </div>
            </section>

            <!-- Troubleshooting Section -->
            <section id="troubleshooting" class="manual-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-wrench"></i>
                    </div>
                    常見問題解決
                </h2>

                <div class="step-container">
                    <div class="step">
                        <div class="step-number">Q1</div>
                        <div class="step-title">登入認證失敗</div>
                        <div class="step-content">
                            <p><strong>問題現象：</strong>輸入序號後顯示「認證失敗」</p>
                            <p><strong>解決方案：</strong></p>
                            <ul style="margin: 1rem 0; padding-left: 2rem;">
                                <li>檢查序號是否正確（建議複製貼上）</li>
                                <li>確認網路連接正常</li>
                                <li>檢查防火牆是否阻擋程式</li>
                                <li>確認授權未過期</li>
                            </ul>
                            <div class="info-box">
                                <div class="box-title">
                                    <i class="fas fa-info-circle"></i>
                                    提示
                                </div>
                                程式會自動驗證序號，如果多次失敗請聯繫客服確認授權狀態。
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">Q2</div>
                        <div class="step-title">腳本無法啟動</div>
                        <div class="step-content">
                            <p><strong>問題現象：</strong>點擊開始按鈕後腳本無法正常啟動</p>
                            <p><strong>解決方案：</strong></p>
                            <ul style="margin: 1rem 0; padding-left: 2rem;">
                                <li>確認遊戲已啟動且視窗可見</li>
                                <li>檢查遊戲解析度是否為1280x720</li>
                                <li>確認遊戲處於視窗模式</li>
                                <li>檢查是否有系統管理員權限</li>
                                <li>重新啟動程式嘗試</li>
                            </ul>
                            <div class="warning-box">
                                <div class="box-title">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    注意
                                </div>
                                遊戲必須處於1280x720視窗模式且未被其他視窗遮蔽並保持前景，腳本才能正常檢測遊戲畫面。
                            </div>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">Q3</div>
                        <div class="step-title">怪物檢測不準確</div>
                        <div class="step-content">
                            <p><strong>問題現象：</strong>腳本無法正確檢測怪物或攻擊錯誤目標</p>
                            <p><strong>解決方案：</strong></p>
                            <ul style="margin: 1rem 0; padding-left: 2rem;">
                                <li>確認已下載並啟用正確的怪物圖片</li>
                                <li>只啟用當前地圖會出現的怪物</li>
                                <li>檢查攻擊範圍設定是否合理</li>
                                <li>重新擷取角色ID圖片</li>
                                <li>調整檢測間隔設定</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Quick Reference -->
            <section class="manual-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-bookmark"></i>
                    </div>
                    快速參考
                </h2>

                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-keyboard"></i>
                        </div>
                        <div class="feature-title">預設按鍵配置</div>
                        <div class="feature-desc">
                            <strong>基本操作：</strong><br>
                            • 攻擊按鍵：z<br>
                            • 跳躍按鍵：alt<br>
                            • 補血按鍵：home<br>
                            • 補藍按鍵：end<br><br>
                            <strong>技能按鍵：</strong><br>
                            • 被動技能1：q<br>
                            • 被動技能2：w<br>
                            • 位移技能：shift
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-life-ring"></i>
                        </div>
                        <div class="feature-title">技術支援</div>
                        <div class="feature-desc">
                            <strong>Discord 即時支援：</strong><br>
                            <a href="https://discord.gg/HPzNrQmN" target="_blank" style="color: var(--accent-blue);">
                                discord.gg/HPzNrQmN
                            </a><br><br>
                            <strong>Email 客服：</strong><br>
                            <a href="mailto:pink870921aa@gmail.com" style="color: var(--accent-blue);">
                                pink870921aa@gmail.com
                            </a><br><br>
                            <strong>服務時間：</strong><br>
                            週一至週日 09:00-23:00
                        </div>
                    </div>
                </div>

                <div class="tip-box">
                    <div class="box-title">
                        <i class="fas fa-lightbulb"></i>
                        使用建議
                    </div>
                    <ul style="list-style: none; padding-left: 0;">
                        <li>• 遇到問題時先查看即時日誌，通常會有詳細的錯誤信息</li>
                        <li>• 建議在測試環境中調整設定，確認無誤後再正式使用</li>
                        <li>• 務必使用1280x720視窗模式以獲得最佳體驗</li>
                    </ul>
                </div>
            </section>
        </div>
    </div>

    <script>
        // Show mock tab function
        function showMockTab(tabName) {
            // Hide all tabs
            document.getElementById('mock-log-tab').style.display = 'none';
            document.getElementById('mock-settings-tab').style.display = 'none';
            
            // Remove active class from all tabs
            document.querySelectorAll('.mock-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            if (tabName === 'log') {
                document.getElementById('mock-log-tab').style.display = 'block';
                document.querySelector('.mock-tab[onclick="showMockTab(\'log\')"]').classList.add('active');
            } else if (tabName === 'settings') {
                document.getElementById('mock-settings-tab').style.display = 'block';
                document.querySelector('.mock-tab[onclick="showMockTab(\'settings\')"]').classList.add('active');
            }
        }

        // 怪物標籤頁切換功能
        function showMockMonsterTab(tabName) {
            // 隱藏所有怪物內容
            const downloadedTab = document.getElementById('mock-downloaded-tab');
            const searchTab = document.getElementById('mock-search-tab');
            
            if (downloadedTab) downloadedTab.style.display = 'none';
            if (searchTab) searchTab.style.display = 'none';
            
            // 移除所有標籤的active類
            document.querySelectorAll('.mock-monster-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 顯示選中的標籤和內容
            if (tabName === 'downloaded' && downloadedTab) {
                downloadedTab.style.display = 'block';
                const tab = document.querySelector('.mock-monster-tab[onclick="showMockMonsterTab(\'downloaded\')"]');
                if (tab) tab.classList.add('active');
            } else if (tabName === 'search' && searchTab) {
                searchTab.style.display = 'block';
                const tab = document.querySelector('.mock-monster-tab[onclick="showMockMonsterTab(\'search\')"]');
                if (tab) tab.classList.add('active');
            }
        }
        
        // 模擬功能演示
        function mockControlDemo(action) {
            const statusLabels = document.querySelectorAll('.mock-tool-status');
            
            statusLabels.forEach(statusLabel => {
                switch(action) {
                    case 'save':
                        statusLabel.textContent = '狀態: 保存成功';
                        statusLabel.style.color = '#10b981';
                        setTimeout(() => {
                            statusLabel.textContent = '狀態: 就緒';
                            statusLabel.style.color = '#10b981';
                        }, 2000);
                        break;
                    case 'reset':
                        statusLabel.textContent = '狀態: 已重置為默認值';
                        statusLabel.style.color = '#f59e0b';
                        setTimeout(() => {
                            statusLabel.textContent = '狀態: 就緒';
                            statusLabel.style.color = '#10b981';
                        }, 2000);
                        break;
                    case 'apply':
                        statusLabel.textContent = '狀態: 配置已應用';
                        statusLabel.style.color = '#00d4ff';
                        setTimeout(() => {
                            statusLabel.textContent = '狀態: 就緒';
                            statusLabel.style.color = '#10b981';
                        }, 2000);
                        break;
                }
            });
        }

        // UUID 驗證功能
        async function verifyUUID() {
            const uuidInput = document.getElementById('uuid-input');
            const verifyBtn = document.querySelector('.verify-btn');
            const verifyText = document.getElementById('verify-text');
            const verifyLoading = document.getElementById('verify-loading');
            const errorMessage = document.getElementById('error-message');
            const successMessage = document.getElementById('success-message');
            
            const uuid = uuidInput.value.trim();
            
            if (!uuid) {
                showError('請輸入序號');
                return;
            }
            
            // 顯示載入狀態
            verifyBtn.disabled = true;
            verifyText.style.display = 'none';
            verifyLoading.style.display = 'inline-block';
            hideMessages();
            
            try {
                const response = await fetch('/manual/verify-uuid', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ uuid: uuid })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess('驗證成功！正在解鎖詳細教學內容...');
                    
                    // 隱藏驗證區域，顯示詳細內容
                    setTimeout(() => {
                        document.getElementById('auth-section').style.display = 'none';
                        document.getElementById('authenticated-content').classList.add('show');
                        
                        // 更新導航狀態
                        updateNavigationLocks();
                        
                        // 平滑滾動到內容區域
                        document.getElementById('authenticated-content').scrollIntoView({ 
                            behavior: 'smooth' 
                        });
                    }, 1500);
                    
                } else {
                    showError(data.message || '驗證失敗，請檢查序號是否正確');
                }
                
            } catch (error) {
                showError('網路錯誤，請稍後再試');
                console.error('驗證錯誤:', error);
            } finally {
                // 恢復按鈕狀態
                verifyBtn.disabled = false;
                verifyText.style.display = 'inline';
                verifyLoading.style.display = 'none';
            }
        }
        
        function showError(message) {
            const errorMessage = document.getElementById('error-message');
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
            document.getElementById('success-message').style.display = 'none';
        }
        
        function showSuccess(message) {
            const successMessage = document.getElementById('success-message');
            successMessage.textContent = message;
            successMessage.style.display = 'block';
            document.getElementById('error-message').style.display = 'none';
        }
        
        function hideMessages() {
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('success-message').style.display = 'none';
        }

        // 動態更新導航欄鎖定狀態
        function updateNavigationLocks() {
            const isAuthenticated = document.getElementById('authenticated-content').classList.contains('show');
            const lockedSections = ['login', 'basic-usage', 'advanced', 'tools', 'troubleshooting'];
            
            document.querySelectorAll('.nav-links a[href^="#"]').forEach(link => {
                const sectionId = link.getAttribute('href').substring(1);
                
                if (!isAuthenticated && lockedSections.includes(sectionId)) {
                    link.classList.add('locked');
                    link.style.opacity = '0.7';
                } else {
                    link.classList.remove('locked');
                    link.style.opacity = '1';
                }
            });
        }

        // 初始化時更新導航狀態
        document.addEventListener('DOMContentLoaded', function() {
            updateNavigationLocks();
            
            const uuidInput = document.getElementById('uuid-input');
            if (uuidInput) {
                uuidInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        verifyUUID();
                    }
                });
            }

        // 為控制按鈕添加點擊事件
        document.querySelectorAll('.mock-control-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const action = this.classList.contains('save') ? 'save' :
                              this.classList.contains('reset') ? 'reset' : 'apply';
                mockControlDemo(action);
            });
        });
        
        // 為測試按鈕添加點擊效果
        document.querySelectorAll('.mock-test-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const originalText = this.textContent;
                this.textContent = '測試中...';
                this.style.opacity = '0.7';
                
                setTimeout(() => {
                    this.textContent = originalText;
                    this.style.opacity = '1';
                }, 1500);
            });
        });
        
        // 為下載按鈕添加點擊效果
        const downloadBtn = document.querySelector('.mock-download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function() {
                const originalText = this.textContent;
                this.textContent = '⏳ 下載中...';
                this.style.opacity = '0.7';
                
                setTimeout(() => {
                    this.textContent = '✅ 下載完成';
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.style.opacity = '1';
                    }, 1000);
                }, 2000);
            });
        }

        });

        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                
                // 檢查是否已解鎖詳細內容
                const isAuthenticated = document.getElementById('authenticated-content').classList.contains('show');
                
                if (!isAuthenticated && ['login', 'basic-usage', 'advanced', 'tools', 'troubleshooting'].includes(targetId)) {
                    // 如果未解鎖且點擊的是需要驗證的章節，滾動到驗證區域
                    document.getElementById('auth-section').scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                    
                    // 高亮輸入框提示用戶
                    const uuidInput = document.getElementById('uuid-input');
                    uuidInput.focus();
                    uuidInput.style.borderColor = 'var(--accent-orange)';
                    uuidInput.style.boxShadow = '0 0 0 3px rgba(245, 158, 11, 0.2)';
                    
                    // 顯示提示訊息
                    showError('請先輸入序號解鎖詳細教學內容');
                    
                    // 3秒後恢復正常樣式
                    setTimeout(() => {
                        uuidInput.style.borderColor = 'var(--border-color)';
                        uuidInput.style.boxShadow = 'none';
                        hideMessages();
                    }, 3000);
                } else {
                    // 已解鎖或點擊公開內容，正常滾動
                    const target = document.querySelector('#' + targetId) || document.querySelector('#interface');
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });

        // Navbar scroll effect
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 100) {
                navbar.style.background = 'rgba(26, 26, 26, 0.98)';
                navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
            } else {
                navbar.style.background = 'rgba(26, 26, 26, 0.95)';
                navbar.style.boxShadow = 'none';
            }
        });

        // 添加更多樣式定義
        const additionalStyles = `
            .warning-box, .info-box, .tip-box {
                border-radius: 8px;
                padding: 1.2rem;
                margin: 1rem 0;
                border-left: 4px solid;
                position: relative;
            }

            .warning-box {
                background: rgba(239, 68, 68, 0.1);
                border-left-color: var(--accent-red);
                color: #fca5a5;
            }

            .info-box {
                background: rgba(0, 212, 255, 0.1);
                border-left-color: var(--accent-blue);
                color: #7dd3fc;
            }

            .tip-box {
                background: rgba(16, 185, 129, 0.1);
                border-left-color: var(--accent-green);
                color: #6ee7b7;
            }

            .box-title {
                font-weight: 600;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .step-container {
                display: grid;
                gap: 1.5rem;
                margin-top: 1.5rem;
            }

            .step {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 2rem;
                position: relative;
                border-left: 4px solid var(--accent-green);
            }

            .step-number {
                position: absolute;
                top: -15px;
                left: 20px;
                background: var(--accent-green);
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 0.9rem;
            }

            .step-title {
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
                margin-top: 0.5rem;
                color: var(--text-primary);
            }

            .step-content {
                color: var(--text-secondary);
                line-height: 1.7;
            }

            .step-visual {
                background: var(--bg-primary);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 1.5rem;
                margin: 1rem 0;
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .visual-icon {
                width: 50px;
                height: 50px;
                background: var(--gradient-accent);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.5rem;
                flex-shrink: 0;
            }

            .visual-content {
                flex: 1;
            }

            .visual-title {
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }

            .visual-desc {
                color: var(--text-secondary);
                font-size: 0.9rem;
            }

            .config-section-detailed {
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 2rem;
                margin-bottom: 2rem;
            }

            .config-category-title {
                display: flex;
                align-items: center;
                gap: 0.8rem;
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 1.5rem;
                color: var(--accent-blue);
            }

            .config-param-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 1.5rem;
            }

            .config-param-card {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 1.5rem;
                transition: var(--transition);
            }

            .config-param-card:hover {
                border-color: var(--accent-blue);
                transform: translateY(-2px);
            }

            .param-name {
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }

            .param-range {
                font-size: 0.9rem;
                color: var(--accent-green);
                margin-bottom: 0.8rem;
                font-weight: 500;
            }

            .param-desc {
                font-size: 0.9rem;
                color: var(--text-secondary);
                line-height: 1.4;
            }

            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }

            .feature-card {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 1.5rem;
                transition: var(--transition);
            }

            .feature-card:hover {
                border-color: var(--accent-blue);
                transform: translateY(-3px);
            }

            .feature-icon {
                width: 50px;
                height: 50px;
                background: var(--gradient-accent);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 1rem;
                font-size: 1.3rem;
                color: white;
            }

            .feature-title {
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 0.8rem;
                color: var(--text-primary);
            }

            .feature-desc {
                color: var(--text-secondary);
                font-size: 0.9rem;
                line-height: 1.5;
            }

            kbd {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                padding: 0.2rem 0.4rem;
                font-size: 0.8rem;
                color: var(--text-primary);
                font-weight: 600;
            }
        `;

        // 添加樣式到頁面
        const styleSheet = document.createElement('style');
        styleSheet.textContent = additionalStyles;
        document.head.appendChild(styleSheet);
    </script>
</body>
</html>
"""

# 路由定義
@manual_bp.route('', methods=['GET'])
def manual_home():
    """操作手冊主頁"""
    return render_template_string(MANUAL_TEMPLATE_WITH_AUTH)

@manual_bp.route('/verify-uuid', methods=['POST'])
def verify_uuid():
    """驗證UUID端點"""
    try:
        data = request.get_json()
        uuid = data.get('uuid', '').strip()
        
        if not uuid:
            return jsonify({
                'success': False,
                'message': '請輸入序號'
            }), 400
        
        # 驗證UUID
        is_valid, message = verify_user_uuid(uuid)
        
        if is_valid:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401
            
    except Exception as e:
        logger.error(f"UUID驗證錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': '驗證服務發生錯誤'
        }), 500

@manual_bp.route('/artale', methods=['GET'])
def artale_manual():
    """Artale 專用操作手冊"""
    return render_template_string(MANUAL_TEMPLATE_WITH_AUTH)

# 確保正確導出
__all__ = ['manual_bp']