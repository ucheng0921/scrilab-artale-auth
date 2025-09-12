"""
download_routes.py - 下載頁面路由（需序號驗證）
"""
from flask import Blueprint, render_template_string, request, jsonify, send_file
import hashlib
import logging
from collections import defaultdict
import time
import os
import tempfile

# 簡單的驗證失敗計數器
failed_attempts = defaultdict(list)

def is_rate_limited(ip):
    """檢查是否超過速率限制"""
    now = time.time()
    # 清理5分鐘前的記錄
    failed_attempts[ip] = [t for t in failed_attempts[ip] if now - t < 300]
    
    # 5分鐘內超過5次失敗就封鎖
    return len(failed_attempts[ip]) >= 5

def record_failed_attempt(ip):
    """記錄失敗嘗試"""
    failed_attempts[ip].append(time.time())

logger = logging.getLogger(__name__)

# 創建下載頁面藍圖
download_bp = Blueprint('download', __name__, url_prefix='/download')

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

# 下載頁面 HTML 模板（需序號驗證）
DOWNLOAD_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artale Script 下載中心 - 專業版下載</title>
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

        .download-header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }

        .download-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .download-subtitle {
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

        /* Purchase Prompt */
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

        /* Download Content */
        .download-content {
            display: none;
        }

        .download-content.show {
            display: block;
        }

        .download-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 2rem;
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

        .download-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }

        .download-card {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            transition: var(--transition);
            position: relative;
        }

        .download-card:hover {
            border-color: var(--accent-blue);
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .download-card-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .download-icon {
            width: 50px;
            height: 50px;
            background: var(--gradient-accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.3rem;
        }

        .download-info h3 {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.3rem;
        }

        .download-version {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .download-description {
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }

        .download-features {
            list-style: none;
            margin-bottom: 1.5rem;
        }

        .download-features li {
            padding: 0.3rem 0;
            color: var(--text-secondary);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .feature-check {
            color: var(--accent-green);
            font-size: 0.8rem;
        }

        .download-button {
            width: 100%;
            padding: 1rem;
            background: var(--gradient-accent);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;  
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .download-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .warning-box {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
            border-left: 4px solid var(--accent-red);
        }

        .warning-box .box-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #fca5a5;
        }

        .info-box {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
            border-left: 4px solid var(--accent-blue);
        }

        .info-box .box-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #7dd3fc;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .download-title {
                font-size: 2rem;
            }
            
            .nav-links {
                display: none;
            }
            
            .download-section {
                padding: 2rem;
            }
            
            .download-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="/products" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-download"></i>
                </div>
                <span>Artale Script</span>
            </a>
            <ul class="nav-links">
                <li><a href="/products#games">遊戲服務</a></li>
                <li><a href="/intro">基本介紹</a></li>
                <li><a href="/manual">操作手冊</a></li>
                <li><a href="/products#contact">聯絡我們</a></li>
            </ul>
            <a href="/products" class="back-btn">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
    </nav>

    <div class="container">
        <!-- Download Header -->
        <div class="download-header">
            <h1 class="download-title">Artale Script 下載中心</h1>
            <p class="download-subtitle">專業版軟體下載 - 僅供授權用戶使用</p>
            <span class="version-badge">最新版本 v1.5.9</span>
        </div>

        <!-- Auth Section -->
        <div class="auth-section" id="auth-section">
            <h2 class="auth-title">
                <div class="auth-icon">
                    <i class="fas fa-key"></i>
                </div>
                授權驗證
            </h2>
            <p class="auth-description">
                下載功能僅供已購買服務的用戶使用。<br>
                請輸入您的授權序號以解鎖下載功能。
            </p>
            <div class="auth-form">
                <div class="form-group">
                    <label for="uuid-input">授權序號</label>
                    <input type="password" id="uuid-input" class="form-input" placeholder="請輸入您的授權序號">
                </div>
                <button class="verify-btn" onclick="verifyUUID()">
                    <span id="verify-text">驗證並解鎖下載</span>
                    <div class="loading" id="verify-loading"></div>
                </button>
                <div class="error-message" id="error-message"></div>
                <div class="success-message" id="success-message"></div>
            </div>
        </div>

        <!-- Purchase Prompt -->
        <div class="purchase-prompt">
            <h3>
                <i class="fas fa-shopping-cart"></i>
                還沒有序號嗎？
            </h3>
            <p>
                立即購買 Artale Script 服務，獲得專業版軟體下載權限。<br>
                我們提供多種方案供您選擇，價格實惠，服務專業。
            </p>
            <a href="/products#services" class="purchase-btn">
                <i class="fas fa-star"></i>
                <span>立即購買</span>
            </a>
        </div>

        <!-- Download Content (需要驗證後才能查看) -->
        <div class="download-content" id="download-content">
            <!-- 系統需求 -->
            <section class="download-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-desktop"></i>
                    </div>
                    系統需求
                </h2>
                
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        重要提醒
                    </div>
                    <strong>請確保您的系統符合以下最低需求：</strong><br>
                    • 作業系統：Windows 10 或更新版本<br>
                    • 處理器：Intel i5 或 AMD 同級以上<br>
                    • 記憶體：8GB RAM（建議 16GB）<br>
                    • 硬碟空間：至少 10GB 可用空間<br>
                    • 網路：穩定的網路連接<br>
                    • 重要：軟體資料夾必須放在<strong>英文路徑</strong>中
                </div>
            </section>

            <!-- 下載區域 -->
            <section class="download-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-download"></i>
                    </div>
                    軟體下載
                </h2>

                <div class="download-grid">
                    <!-- 主程式下載 -->
                    <div class="download-card">
                        <div class="download-card-header">
                            <div class="download-icon">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="download-info">
                                <h3>Artale Script 主程式</h3>
                                <div class="download-version">版本 v1.5.9 | 完整版本</div>
                            </div>
                        </div>
                        
                        <div class="download-description">
                            完整的 Artale Script 主程式，包含圖形化界面和所有核心功能。
                        </div>
                        
                        <ul class="download-features">
                            <li><i class="fas fa-check feature-check"></i> 圖形化 GUI 界面</li>
                            <li><i class="fas fa-check feature-check"></i> 怪物檢測與攻擊系統</li>
                            <li><i class="fas fa-check feature-check"></i> 被動技能自動管理</li>
                            <li><i class="fas fa-check feature-check"></i> 紅點檢測避人功能</li>
                            <li><i class="fas fa-check feature-check"></i> 攀爬繩索功能</li>
                            <li><i class="fas fa-check feature-check"></i> 血量監控系統</li>
                            <li><i class="fas fa-check feature-check"></i> 自動解除測謊</li>
                        </ul>
                        
                        <a href="https://drive.google.com/drive/folders/1Cm85uYGr2xaZmw4pRamAz_JAZ6WjUEfw?usp=drive_link" 
                        target="_blank" 
                        class="download-button">
                            <i class="fas fa-download"></i>
                            <span>下載主程式</span>
                        </a>
                    </div>
                </div>
            </section>

            <!-- 安裝說明 -->
            <section class="download-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    安裝說明
                </h2>
                
                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-lightbulb"></i>
                        安裝步驟
                    </div>
                    <strong>請按照以下步驟進行安裝：</strong><br>
                    1. 下載主程式壓縮檔案<br>
                    2. 解壓縮到<strong>英文路徑</strong>的資料夾中（如：C:\ArtaleScript\）<br>
                    3. 運行 ArtaleScript.exe 主程式<br>
                    4. 輸入您的授權序號進行登入<br>
                    5. 參考操作手冊進行詳細設定
                </div>

                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-shield-alt"></i>
                        安全提醒
                    </div>
                    • 請從官方管道下載，避免使用來源不明的軟體<br>
                    • 首次運行可能被防毒軟體誤報，請加入白名單<br>
                    • 使用前請確保遊戲設定為 1280x720 視窗模式<br>
                    • 軟體僅供個人使用，請勿分享給他人<br>
                    • 如遇問題請聯繫技術支援
                </div>
            </section>

            <!-- 技術支援 -->
            <section class="download-section">
                <h2 class="section-title">
                    <div class="section-icon">
                        <i class="fas fa-headset"></i>
                    </div>
                    技術支援
                </h2>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                    <div style="background: var(--bg-tertiary); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <h4 style="color: var(--accent-blue); margin-bottom: 1rem;">
                            <i class="fab fa-discord"></i> Discord 即時支援
                        </h4>
                        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                            加入我們的 Discord 社群獲得即時技術支援和使用交流。
                        </p>
                        <a href="https://discord.gg/nmMmm9gZDC" target="_blank" style="color: var(--accent-blue); text-decoration: none;">
                            discord.gg/HPzNrQmN
                        </a>
                    </div>
                    
                    <div style="background: var(--bg-tertiary); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <h4 style="color: var(--accent-blue); margin-bottom: 1rem;">
                            <i class="fas fa-envelope"></i> Email 客服
                        </h4>
                        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                            如需詳細技術支援或帳號相關問題，請透過 Email 聯繫。
                        </p>
                        <a href="mailto:scrilabstaff@gmail.com" style="color: var(--accent-blue); text-decoration: none;">
                            scrilabstaff@gmail.com
                        </a>
                    </div>
                </div>
            </section>
        </div>
    </div>

    <script>
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
                const response = await fetch('/download/verify-uuid', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ uuid: uuid })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess('驗證成功！正在解鎖下載功能...');
                    
                    // 隱藏驗證區域，顯示下載內容
                    setTimeout(() => {
                        document.getElementById('auth-section').style.display = 'none';
                        document.getElementById('download-content').classList.add('show');
                        
                        // 平滑滾動到下載內容
                        document.getElementById('download-content').scrollIntoView({ 
                            behavior: 'smooth' 
                        });
                    }, 1500);
                    
                } else {
                    if (data.rate_limited) {
                        showError('🚫 驗證失敗次數過多，請5分鐘後再試');
                        verifyBtn.disabled = true;
                        setTimeout(() => {
                            verifyBtn.disabled = false;
                            hideMessages();
                        }, 300000);
                    } else {
                        showError(data.message || '驗證失敗，請檢查序號是否正確');
                    }                    
                }
                
            } catch (error) {
                showError('網路錯誤，請稍後再試');
                console.error('驗證錯誤:', error);
            } finally {
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

        // 下載功能
        async function downloadFile(type) {
            const button = event.target.closest('.download-button');
            const originalText = button.innerHTML;
            
            // 顯示下載中狀態
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>準備下載...</span>';
            button.disabled = true;
            
            try {
                const response = await fetch(`/download/file/${type}`, {
                    method: 'GET',
                });
                
                if (response.ok) {
                    // 獲取檔案名稱
                    const contentDisposition = response.headers.get('Content-Disposition');
                    let filename = 'download.zip';
                    
                    if (contentDisposition) {
                        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                        if (filenameMatch) {
                            filename = filenameMatch[1];
                        }
                    }
                    
                    // 創建下載連結
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    // 顯示成功狀態
                    button.innerHTML = '<i class="fas fa-check"></i><span>下載完成</span>';
                    button.style.background = 'var(--gradient-success)';
                    
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.style.background = 'var(--gradient-accent)';
                        button.disabled = false;
                    }, 3000);
                    
                } else {
                    throw new Error('下載失敗');
                }
                
            } catch (error) {
                console.error('下載錯誤:', error);
                button.innerHTML = '<i class="fas fa-exclamation-triangle"></i><span>下載失敗</span>';
                button.style.background = 'var(--accent-red)';
                
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.style.background = 'var(--gradient-accent)';
                    button.disabled = false;
                }, 3000);
            }
        }

        // Enter 鍵支援
        document.addEventListener('DOMContentLoaded', function() {
            const uuidInput = document.getElementById('uuid-input');
            if (uuidInput) {
                uuidInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        verifyUUID();
                    }
                });
            }
        });

        // 導航欄滾動效果
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
    </script>
</body>
</html>
"""

# 路由定義
@download_bp.route('', methods=['GET'])
def download_home():
    """下載頁面主頁"""
    return render_template_string(DOWNLOAD_TEMPLATE)

@download_bp.route('/verify-uuid', methods=['POST'])
def verify_uuid():
    """驗證UUID端點"""
    try:
        # 獲取客戶端 IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).split(',')[0].strip()
        
        # 檢查是否被限制
        if is_rate_limited(client_ip):
            return jsonify({
                'success': False,
                'message': '驗證失敗次數過多，請5分鐘後再試',
                'rate_limited': True
            }), 429
        
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
            # 成功時清除失敗記錄
            if client_ip in failed_attempts:
                del failed_attempts[client_ip]
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            # 失敗時記錄
            record_failed_attempt(client_ip)
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

@download_bp.route('/file/<file_type>', methods=['GET'])
def download_file(file_type):
    """檔案下載端點"""
    try:
        # 模擬檔案下載 - 在實際應用中，這裡應該驗證用戶權限
        # 並從安全的儲存位置提供真實的檔案
        
        file_configs = {
            'main': {
                'filename': 'ArtaleScript_v1.2.3_Main.zip',
                'content': 'This is a simulated main program download file.',
                'content_type': 'application/zip'
            },
            'tools': {
                'filename': 'ArtaleScript_v1.0.2_Tools.zip', 
                'content': 'This is a simulated tools download file.',
                'content_type': 'application/zip'
            },
            'manual': {
                'filename': 'ArtaleScript_Manual_v1.0.pdf',
                'content': 'This is a simulated manual download file.',
                'content_type': 'application/pdf'
            }
        }
        
        if file_type not in file_configs:
            return jsonify({'error': 'Invalid file type'}), 400
        
        config = file_configs[file_type]
        
        # 在實際應用中，您應該：
        # 1. 驗證用戶是否已通過UUID驗證
        # 2. 從安全的檔案儲存位置讀取真實檔案
        # 3. 記錄下載日誌
        
        # 創建模擬檔案內容
        import io
        file_content = io.BytesIO(config['content'].encode('utf-8'))
        
        return send_file(
            file_content,
            as_attachment=True,
            download_name=config['filename'],
            mimetype=config['content_type']
        )
        
    except Exception as e:
        logger.error(f"檔案下載錯誤: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500

# 確保正確導出
__all__ = ['download_bp']
