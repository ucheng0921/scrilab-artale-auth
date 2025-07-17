"""
manual_routes.py - 操作手冊路由處理（更新版）
"""
from flask import Blueprint, render_template_string

# 創建操作手冊藍圖 - 移到文件開頭
manual_bp = Blueprint('manual', __name__, url_prefix='/manual')

# 操作手冊 HTML 模板
MANUAL_TEMPLATE = r"""
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

        /* Interface Screenshot */
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

        /* Mock settings styles */
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

        /* Advanced config styles */
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

        /* Section Styles */
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

        /* Feature Cards */
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

        /* Warning/Info boxes */
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

        /* Keyboard key styling */
        kbd {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.2rem 0.4rem;
            font-size: 0.8rem;
            color: var(--text-primary);
            font-weight: 600;
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
            
            .config-param-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }
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

        <!-- Interface Preview -->
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
                    </div>
                    <div class="panel-section">
                        <div class="panel-title">腳本控制</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem;">腳本狀態: 未運行</div>
                        <button class="mock-button green">開始</button>
                        <button class="mock-button red">停止</button>
                        <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">運行時間: 00:00:00</div>
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
                        [12:34:56] 提示: 只有授權用戶才能使用腳本功能<br>
                        [12:34:56] 登入後確保遊戲視窗已開啟，然後點擊開始腳本<br>
                        [12:34:56] 怪物下載功能已整合至進階設定中
                    </div>
                    <div class="mock-settings" id="mock-settings-tab" style="display: none;">
                        <div class="mock-settings-category">
                            <h4>怪物檢測與攻擊配置</h4>
                            <div class="mock-setting-item">
                                <span>攻擊按鍵:</span>
                                <input type="text" value="z" style="width: 30px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px;">
                            </div>
                            <div class="mock-setting-item">
                                <span>攻擊範圍:</span>
                                <input type="text" value="100" style="width: 50px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px;">
                            </div>
                        </div>
                        <div class="mock-settings-category">
                            <h4>被動技能系統</h4>
                            <div class="mock-setting-item">
                                <span>啟用被動技能:</span>
                                <input type="checkbox" checked>
                            </div>
                            <div class="mock-setting-item">
                                <span>技能1按鍵:</span>
                                <input type="text" value="q" style="width: 30px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px;">
                            </div>
                        </div>
                        <div class="mock-settings-category">
                            <h4>血量監控配置</h4>
                            <div class="mock-setting-item">
                                <span>HP補血閾值:</span>
                                <input type="text" value="0.3" style="width: 50px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px;">
                            </div>
                            <div class="mock-setting-item">
                                <span>補血按鍵:</span>
                                <input type="text" value="home" style="width: 50px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px;">
                            </div>
                        </div>
                        <button class="mock-button" style="margin-top: 10px;">保存設定</button>
                    </div>
                </div>
            </div>
        </div>

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
                1. 進入遊戲後，按 <kbd>Alt</kbd> 鍵打開遊戲選單<br>
                2. 點擊「選項」→「圖形」<br>
                3. 將「解析度」設定為 <strong>1280x720</strong><br>
                4. 確認「視窗模式」已勾選 ✓<br>
                5. 點擊「確定」套用設定<br><br>
                <strong>為什麼要使用 1280x720？</strong><br>
                • 這是腳本最佳化的解析度，檢測精確度最高<br>
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
                                <div class="visual-desc">確認遊戲視窗可見且未被遮蔽，解析度為 1280x720。</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-title">輸入授權 UUID</div>
                    <div class="step-content">
                        <p>在左側面板的「登入驗證」區域中，將您購買時獲得的 UUID 輸入到文字框中。</p>
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
                            建議使用複製貼上方式輸入 UUID，避免輸入錯誤。UUID 區分大小寫。
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
                            遊戲視窗必須可見且未被其他視窗遮蔽，腳本才能正常運作。
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

            <!-- 怪物檢測與攻擊配置 -->
            <div class="config-section-detailed">
                <h3 class="config-category-title">
                    <i class="fas fa-crosshairs"></i>
                    怪物檢測與攻擊配置
                </h3>
                
                <div class="config-param-grid">
                    <div class="config-param-card">
                        <div class="param-name">攻擊按鍵 (ATTACK_KEY)</div>
                        <div class="param-range">預設值：z</div>
                        <div class="param-desc">主要攻擊技能的按鍵，支援單字符或特殊按鍵名稱（如 alt、ctrl、space）</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">次要攻擊按鍵 (SECONDARY_ATTACK_KEY)</div>
                        <div class="param-range">預設值：x</div>
                        <div class="param-desc">次要攻擊技能的按鍵，可用於群體攻擊或特殊技能</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">攻擊範圍 (ATTACK_RANGE_X)</div>
                        <div class="param-range">範圍：50-300 像素</div>
                        <div class="param-desc">角色攻擊範圍的橫向距離，數值越大檢測範圍越廣</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">主要攻擊機率 (PRIMARY_ATTACK_CHANCE)</div>
                        <div class="param-range">範圍：0.0-1.0</div>
                        <div class="param-desc">使用主要攻擊的機率，0.8表示80%機率使用主要攻擊</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">次要攻擊機率 (SECONDARY_ATTACK_CHANCE)</div>
                        <div class="param-range">範圍：0.0-1.0</div>
                        <div class="param-desc">使用次要攻擊的機率，0.2表示20%機率使用次要攻擊</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">跳躍攻擊模式 (JUMP_ATTACK_MODE)</div>
                        <div class="param-range">選項：original、mage、disabled</div>
                        <div class="param-desc">
                            • original: 原始模式，適合戰士、盜賊等職業<br>
                            • mage: 法師模式，適合法師職業<br>
                            • disabled: 禁用跳躍攻擊
                        </div>
                    </div>
                </div>
            </div>

            <!-- 被動技能系統配置 -->
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
                        <div class="param-range">預設值：q, w, e, r</div>
                        <div class="param-desc">四個被動技能的按鍵設定，支援任意按鍵配置</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">技能冷卻時間 (PASSIVE_SKILL_1~4_COOLDOWN)</div>
                        <div class="param-range">範圍：1.0-300.0 秒</div>
                        <div class="param-desc">每個技能的冷卻時間，建議根據實際技能冷卻設定</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">隨機延遲 (PASSIVE_SKILL_RANDOM_DELAY)</div>
                        <div class="param-range">最小值：0.0-5.0 秒<br>最大值：0.0-10.0 秒</div>
                        <div class="param-desc">技能使用間的隨機延遲，讓行為更自然</div>
                    </div>
                </div>
            </div>

            <!-- 移動系統配置 -->
            <div class="config-section-detailed">
                <h3 class="config-category-title">
                    <i class="fas fa-running"></i>
                    移動系統配置
                </h3>
                
                <div class="config-param-grid">
                    <div class="config-param-card">
                        <div class="param-name">跳躍移動 (ENABLE_JUMP_MOVEMENT)</div>
                        <div class="param-range">選項：開啟/關閉</div>
                        <div class="param-desc">啟用後角色會偶爾跳躍移動，增加移動的自然性</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">跳躍移動機率 (JUMP_MOVEMENT_CHANCE)</div>
                        <div class="param-range">範圍：0.0-1.0</div>
                        <div class="param-desc">跳躍移動的觸發機率，0.3表示30%機率跳躍</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">位移技能 (ENABLE_DASH_MOVEMENT)</div>
                        <div class="param-range">選項：開啟/關閉</div>
                        <div class="param-desc">啟用位移技能自動使用，適合有閃現類技能的職業</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">位移技能按鍵 (DASH_SKILL_KEY)</div>
                        <div class="param-range">預設值：shift</div>
                        <div class="param-desc">位移技能的按鍵，如閃現、衝刺等</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">位移技能冷卻 (DASH_SKILL_COOLDOWN)</div>
                        <div class="param-range">範圍：1.0-60.0 秒</div>
                        <div class="param-desc">位移技能的冷卻時間，根據實際技能設定</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">隨機下跳 (ENABLE_DOWN_JUMP)</div>
                        <div class="param-range">選項：開啟/關閉</div>
                        <div class="param-desc">啟用後角色會偶爾下跳，增加移動多樣性</div>
                    </div>
                </div>
            </div>

            <!-- 攀爬系統配置 -->
            <div class="config-section-detailed">
                <h3 class="config-category-title">
                    <i class="fas fa-grip-lines"></i>
                    攀爬系統配置
                </h3>
                
                <div class="config-param-grid">
                    <div class="config-param-card">
                        <div class="param-name">啟用爬繩 (ENABLE_ROPE_CLIMBING)</div>
                        <div class="param-range">選項：開啟/關閉</div>
                        <div class="param-desc">啟用自動爬繩功能，角色會自動檢測並使用繩索</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">爬繩最小距離 (ROPE_MIN_DISTANCE)</div>
                        <div class="param-range">範圍：10-200 像素</div>
                        <div class="param-desc">角色開始爬繩時離繩索的最小距離</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">爬繩最大距離 (ROPE_MAX_DISTANCE)</div>
                        <div class="param-range">範圍：20-300 像素</div>
                        <div class="param-desc">角色檢測繩索的最大距離範圍</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">爬繩冷卻時間 (ROPE_COOLDOWN_TIME)</div>
                        <div class="param-range">範圍：1.0-10.0 秒</div>
                        <div class="param-desc">爬繩動作間的冷卻時間，避免頻繁觸發</div>
                    </div>
                </div>
            </div>

            <!-- 血量監控配置 -->
            <div class="config-section-detailed">
                <h3 class="config-category-title">
                    <i class="fas fa-heart"></i>
                    血量監控配置
                </h3>
                
                <div class="config-param-grid">
                    <div class="config-param-card">
                        <div class="param-name">啟用血量監控 (ENABLE_HEALTH_MONITOR)</div>
                        <div class="param-range">選項：開啟/關閉</div>
                        <div class="param-desc">啟用後會自動監控血量和藍量，自動補血補藍</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">HP補血閾值 (HEALTH_MONITOR_HP_THRESHOLD)</div>
                        <div class="param-range">範圍：0.0-1.0</div>
                        <div class="param-desc">血量低於此比例時自動補血，0.3表示血量低於30%時補血</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">MP補藍閾值 (HEALTH_MONITOR_MP_THRESHOLD)</div>
                        <div class="param-range">範圍：0.0-1.0</div>
                        <div class="param-desc">藍量低於此比例時自動補藍，0.2表示藍量低於20%時補藍</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">補血按鍵 (HEALTH_MONITOR_HEAL_KEY)</div>
                        <div class="param-range">預設值：home</div>
                        <div class="param-desc">補血藥水或技能的按鍵，需要先設定好快捷鍵</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">補藍按鍵 (HEALTH_MONITOR_MP_KEY)</div>
                        <div class="param-range">預設值：end</div>
                        <div class="param-desc">補藍藥水或技能的按鍵，需要先設定好快捷鍵</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">補血冷卻時間 (HEALTH_MONITOR_HEAL_COOLDOWN)</div>
                        <div class="param-range">範圍：1.0-10.0 秒</div>
                        <div class="param-desc">補血動作間的冷卻時間，避免頻繁使用</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">補藍冷卻時間 (HEALTH_MONITOR_MP_COOLDOWN)</div>
                        <div class="param-range">範圍：1.0-10.0 秒</div>
                        <div class="param-desc">補藍動作間的冷卻時間，避免頻繁使用</div>
                    </div>
                </div>
            </div>

            <!-- 紅點偵測配置 -->
            <div class="config-section-detailed">
                <h3 class="config-category-title">
                    <i class="fas fa-eye"></i>
                    紅點偵測與換頻道配置
                </h3>
                
                <div class="config-param-grid">
                    <div class="config-param-card">
                        <div class="param-name">啟用紅點偵測 (ENABLE_RED_DOT_DETECTION)</div>
                        <div class="param-range">選項：開啟/關閉</div>
                        <div class="param-desc">啟用後會檢測螢幕上的紅點，發現時自動換頻道</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">紅點檢測最小時間 (RED_DOT_MIN_TIME)</div>
                        <div class="param-range">範圍：1.0-10.0 秒</div>
                        <div class="param-desc">檢測到紅點後的最小等待時間，避免誤判</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">紅點檢測最大時間 (RED_DOT_MAX_TIME)</div>
                        <div class="param-range">範圍：5.0-30.0 秒</div>
                        <div class="param-desc">檢測到紅點後的最大等待時間，超過即觸發換頻道</div>
                    </div>
                </div>
            </div>

            <!-- 效能優化配置 -->
            <div class="config-section-detailed">
                <h3 class="config-category-title">
                    <i class="fas fa-tachometer-alt"></i>
                    效能優化配置
                </h3>
                
                <div class="config-param-grid">
                    <div class="config-param-card">
                        <div class="param-name">檢測間隔 (DETECTION_INTERVAL)</div>
                        <div class="param-range">範圍：0.01-0.1 秒</div>
                        <div class="param-desc">主循環的檢測間隔，數值越小反應越快但CPU使用率越高</div>
                    </div>
                    
                    <div class="config-param-card">
                        <div class="param-name">血量監控更新頻率 (HEALTH_MONITOR_FPS_LIMIT)</div>
                        <div class="param-range">範圍：1-60 FPS</div>
                        <div class="param-desc">血量監控的更新頻率，建議設為10-30以平衡效能</div>
                    </div>
                </div>
            </div>

            <div class="tip-box">
                <div class="box-title">
                    <i class="fas fa-lightbulb"></i>
                    參數調整建議
                </div>
                <ul style="list-style: none; padding-left: 0;">
                    <li>• <strong>新手建議：</strong>先使用預設值，熟悉後再調整</li>
                    <li>• <strong>效能優化：</strong>檢測間隔可調整為0.05-0.08秒</li>
                    <li>• <strong>職業適配：</strong>根據職業特性調整攻擊模式和技能設定</li>
                    <li>• <strong>安全考量：</strong>建議保持一定的隨機延遲，避免過於機械化</li>
                </ul>
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
                    <div class="step-title">繩子定位工具</div>
                    <div class="step-content">
                        <p>擷取繩子圖片以優化爬繩功能的檢測精度。</p>
                        <div class="step-visual">
                            <div class="visual-icon">
                                <i class="fas fa-grip-lines"></i>
                            </div>
                            <div class="visual-content">
                                <div class="visual-title">操作說明</div>
                                <div class="visual-desc">
                                    1. 點擊「📸 新增繩子截圖」<br>
                                    2. 在截圖界面中框選繩子區域<br>
                                    3. 系統會自動命名並保存（rope_1.png, rope_2.png...）<br>
                                    4. 可在列表中預覽、管理已保存的繩子圖片
                                </div>
                            </div>
                        </div>
                        <div class="info-box">
                            <div class="box-title">
                                <i class="fas fa-info-circle"></i>
                                繩子管理功能
                            </div>
                            <strong>支援的操作：</strong><br>
                            • 點擊繩子名稱可預覽圖片<br>
                            • 勾選多個繩子後點擊「🗑️ 刪除選中」<br>
                            • 使用搜尋功能快速找到特定繩子<br>
                            • 支援全選/全不選操作
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-title">怪物搜尋下載系統</div>
                    <div class="step-content">
                        <p>從官方API下載怪物圖片，支援搜尋和批量下載功能。</p>
                        
                        <div class="config-section-detailed">
                            <h4>🔍 搜尋功能使用方法</h4>
                            
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
                                • 搜尋支援部分匹配，如搜尋「史萊姆」會找到所有史萊姆類怪物<br>
                                • 如果結果太多，請使用更具體的搜尋條件
                            </div>
                        </div>
                        
                        <div class="config-section-detailed">
                            <h4>📥 下載功能使用方法</h4>
                            
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-download"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">下載步驟</div>
                                    <div class="visual-desc">
                                        1. 勾選想要下載的怪物（支援多選）<br>
                                        2. 確認「跳過死亡動畫」是否勾選<br>
                                        3. 點擊「📥 下載勾選怪物」開始下載<br>
                                        4. 觀察下載日誌了解進度和結果
                                    </div>
                                </div>
                            </div>
                            
                            <div class="tip-box">
                                <div class="box-title">
                                    <i class="fas fa-lightbulb"></i>
                                    下載優化建議
                                </div>
                                <strong>下載設定：</strong><br>
                                • 建議勾選「跳過死亡動畫」減少無用圖片<br>
                                • 每次下載建議不超過20個怪物<br>
                                • 系統會自動生成水平翻轉版本（適應左右移動）<br>
                                • 下載的圖片會自動命名為安全的英文檔名
                            </div>
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-title">已下載怪物管理</div>
                    <div class="step-content">
                        <p>管理已下載的怪物圖片，選擇要啟用的怪物類型。</p>
                        
                        <div class="config-section-detailed">
                            <h4>✅ 怪物啟用方法</h4>
                            
                            <div class="step-visual">
                                <div class="visual-icon">
                                    <i class="fas fa-check-square"></i>
                                </div>
                                <div class="visual-content">
                                    <div class="visual-title">啟用步驟</div>
                                    <div class="visual-desc">
                                        1. 切換到「已下載」選項卡<br>
                                        2. 勾選想要腳本檢測的怪物<br>
                                        3. 點擊「應用更改」或「保存設定」<br>
                                        4. 重啟腳本使設定生效
                                    </div>
                                </div>
                            </div>
                            
                            <div class="info-box">
                                <div class="box-title">
                                    <i class="fas fa-info-circle"></i>
                                    怪物顯示格式
                                </div>
                                <strong>顯示格式：</strong><br>
                                <code>中文名稱 -> 英文名稱 (等級: xxx) - N 張圖片</code><br><br>
                                <strong>例如：</strong><br>
                                <code>綠水靈 -> Green Slime (等級: 15) - 4 張圖片</code><br><br>
                                圖片數量包含原始圖片和翻轉版本
                            </div>
                        </div>
                        
                        <div class="config-section-detailed">
                            <h4>🔧 管理功能</h4>
                            
                            <div class="feature-grid">
                                <div class="feature-card">
                                    <div class="feature-icon">
                                        <i class="fas fa-search"></i>
                                    </div>
                                    <div class="feature-title">搜尋功能</div>
                                    <div class="feature-desc">
                                        可搜尋中文名稱或英文檔名，支援即時過濾顯示
                                    </div>
                                </div>

                                <div class="feature-card">
                                    <div class="feature-icon">
                                        <i class="fas fa-check-double"></i>
                                    </div>
                                    <div class="feature-title">批量操作</div>
                                    <div class="feature-desc">
                                        支援全選/全不選功能，可快速管理大量怪物
                                    </div>
                                </div>

                                <div class="feature-card">
                                    <div class="feature-icon">
                                        <i class="fas fa-sync"></i>
                                    </div>
                                    <div class="feature-title">即時更新</div>
                                    <div class="feature-desc">
                                        下載完成後會自動刷新列表，顯示最新的怪物
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="warning-box">
                            <div class="box-title">
                                <i class="fas fa-exclamation-triangle"></i>
                                效能考量
                            </div>
                            <strong>建議啟用怪物數量：</strong><br>
                            • 一般練功：啟用3-5種怪物即可<br>
                            • 混合地圖：可啟用5-10種怪物<br>
                            • 避免啟用過多怪物影響檢測速度<br>
                            • 只啟用當前地圖會出現的怪物
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Interface Details Section -->
        <section id="interface" class="manual-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-desktop"></i>
                </div>
                界面詳細介紹
            </h2>

            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-user-shield"></i>
                    </div>
                    <div class="feature-title">左側控制面板</div>
                    <div class="feature-desc">
                        <strong>登入驗證區域：</strong><br>
                        • UUID 輸入框（隱藏顯示）<br>
                        • 登入/登出按鈕<br>
                        • 用戶信息顯示<br><br>
                        <strong>腳本控制區域：</strong><br>
                        • 開始/停止按鈕<br>
                        • 運行時間顯示<br>
                        • 腳本狀態指示
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-terminal"></i>
                    </div>
                    <div class="feature-title">即時日誌選項卡</div>
                    <div class="feature-desc">
                        <strong>日誌功能：</strong><br>
                        • 即時顯示腳本運行狀態<br>
                        • 怪物檢測和攻擊信息<br>
                        • 錯誤和警告訊息<br><br>
                        <strong>控制選項：</strong><br>
                        • 清空日誌按鈕<br>
                        • 自動滾動開關
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-sliders-h"></i>
                    </div>
                    <div class="feature-title">進階設定選項卡</div>
                    <div class="feature-desc">
                        <strong>配置分類：</strong><br>
                        • 怪物檢測與攻擊配置<br>
                        • 被動技能系統配置<br>
                        • 血量監控配置<br>
                        • 移動系統配置<br><br>
                        <strong>操作按鈕：</strong><br>
                        • 保存設定、重置默認<br>
                        • 應用更改
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="feature-title">底部狀態欄</div>
                    <div class="feature-desc">
                        <strong>狀態信息：</strong><br>
                        • 左側：當前操作狀態<br>
                        • 中間：登入用戶信息<br>
                        • 右側：程式版本信息<br><br>
                        提供快速的狀態概覽，方便了解當前程式狀態。
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
                        <p><strong>問題現象：</strong>輸入UUID後顯示「認證失敗」</p>
                        <p><strong>解決方案：</strong></p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>檢查UUID是否正確（建議複製貼上）</li>
                            <li>確認網路連接正常</li>
                            <li>檢查防火牆是否阻擋程式</li>
                            <li>確認授權未過期</li>
                        </ul>
                        <div class="info-box">
                            <div class="box-title">
                                <i class="fas fa-info-circle"></i>
                                提示
                            </div>
                            程式會自動驗證UUID，如果多次失敗請聯繫客服確認授權狀態。
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
                            遊戲必須處於1280x720視窗模式且未被其他視窗遮蔽，腳本才能正常檢測遊戲畫面。
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">Q3</div>
                    <div class="step-title">設定無法保存</div>
                    <div class="step-content">
                        <p><strong>問題現象：</strong>修改設定後無法成功保存</p>
                        <p><strong>解決方案：</strong></p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>確認程式資料夾有寫入權限</li>
                            <li>檢查設定值是否在有效範圍內</li>
                            <li>先點擊「應用更改」再「保存設定」</li>
                            <li>關閉防毒軟體的即時保護</li>
                        </ul>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">Q4</div>
                    <div class="step-title">工具功能無法使用</div>
                    <div class="step-content">
                        <p><strong>問題現象：</strong>角色定位或繩子定位工具無法正常運作</p>
                        <p><strong>解決方案：</strong></p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>確認遊戲處於1280x720視窗模式</li>
                            <li>檢查螢幕解析度設定</li>
                            <li>確保遊戲畫面完整可見</li>
                            <li>嘗試重新擷取截圖</li>
                        </ul>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">Q5</div>
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
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="feature-title">時間設定參考</div>
                    <div class="feature-desc">
                        <strong>檢測間隔：</strong><br>
                        • 主循環：0.05秒<br>
                        • 怪物檢測：0.05秒<br>
                        • 繩索檢測：1.0秒<br><br>
                        <strong>冷卻時間：</strong><br>
                        • 被動技能：30秒<br>
                        • 補血冷卻：3.0秒<br>
                        • 補藍冷卻：2.0秒
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-percentage"></i>
                    </div>
                    <div class="feature-title">閾值設定參考</div>
                    <div class="feature-desc">
                        <strong>血量監控：</strong><br>
                        • HP閾值：30%<br>
                        • MP閾值：20%<br><br>
                        <strong>移動機率：</strong><br>
                        • 跳躍移動：30%<br>
                        • 位移技能：20%<br>
                        • 下跳功能：10%<br><br>
                        <strong>攻擊機率：</strong><br>
                        • 主要攻擊：80%<br>
                        • 次要攻擊：20%
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
                    <li>• 首次使用建議先熟悉基本操作，再進行進階設定</li>
                    <li>• 定期備份自定義配置，避免意外丟失</li>
                    <li>• 遇到問題時先查看即時日誌，通常會有詳細的錯誤信息</li>
                    <li>• 建議在測試環境中調整設定，確認無誤後再正式使用</li>
                    <li>• 務必使用1280x720視窗模式以獲得最佳體驗</li>
                </ul>
            </div>
        </section>
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

        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
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

        // Highlight current section in navigation
        window.addEventListener('scroll', function() {
            const sections = document.querySelectorAll('.manual-section');
            const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
            
            let currentSection = '';
            sections.forEach(section => {
                const rect = section.getBoundingClientRect();
                if (rect.top <= 150 && rect.bottom >= 150) {
                    currentSection = section.id;
                }
            });
            
            navLinks.forEach(link => {
                const href = link.getAttribute('href').substring(1);
                if (href === currentSection) {
                    link.style.color = 'var(--accent-blue)';
                } else {
                    link.style.color = 'var(--text-secondary)';
                }
            });
        });

        // Add interactive effects to feature cards
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.boxShadow = '0 10px 30px rgba(0, 212, 255, 0.1)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'none';
            });
        });

        // Mock GUI interactions
        document.querySelectorAll('.mock-button').forEach(button => {
            button.addEventListener('click', function() {
                const originalText = this.textContent;
                this.textContent = '執行中...';
                setTimeout(() => {
                    this.textContent = originalText;
                }, 1000);
            });
        });

        document.querySelectorAll('.mock-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                document.querySelectorAll('.mock-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    </script>
</body>
</html>
"""

# 路由定義
@manual_bp.route('', methods=['GET'])
def manual_home():
    """操作手冊主頁"""
    return render_template_string(MANUAL_TEMPLATE)

@manual_bp.route('/artale', methods=['GET'])
def artale_manual():
    """Artale 專用操作手冊"""
    return render_template_string(MANUAL_TEMPLATE)

# 確保正確導出
__all__ = ['manual_bp']