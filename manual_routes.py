"""
manual_routes.py - 操作手冊路由處理
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

        /* Config Panel Visual */
        .config-panel-visual {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }

        .config-section {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
        }

        .config-section h4 {
            color: var(--accent-blue);
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }

        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
        }

        .config-label {
            color: var(--text-secondary);
        }

        .config-value {
            color: var(--accent-green);
            font-weight: 500;
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
                        <div class="mock-tab active">即時日誌</div>
                        <div class="mock-tab">進階設定</div>
                    </div>
                    <div class="mock-log">
                        [12:34:56] 歡迎使用 Artale Script GUI<br>
                        [12:34:56] 認證系統已就緒<br>
                        [12:34:56] 請輸入您的授權 UUID 以開始使用<br>
                        [12:34:56] 提示: 只有授權用戶才能使用腳本功能<br>
                        [12:34:56] 登入後確保遊戲視窗已開啟，然後點擊開始腳本<br>
                        [12:34:56] 怪物下載功能已整合至進階設定中
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

            <div class="step-container">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-title">啟動程式</div>
                    <div class="step-content">
                        <p>下載並執行 Artale Script GUI 程式，首次啟動時程式會自動初始化認證系統。</p>
                        <div class="step-visual">
                            <div class="visual-icon">
                                <i class="fas fa-rocket"></i>
                            </div>
                            <div class="visual-content">
                                <div class="visual-title">啟動提示</div>
                                <div class="visual-desc">程式啟動後會顯示「認證系統已就緒」的訊息，表示可以開始登入。</div>
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
                進階設定
            </h2>

            <p style="margin-bottom: 2rem; color: var(--text-secondary);">
                進階設定面板提供豐富的自定義選項，讓您調整腳本行為以符合個人需求。
            </p>

            <div class="config-panel-visual">
                <div class="config-section">
                    <h4>怪物檢測與攻擊</h4>
                    <div class="config-item">
                        <span class="config-label">攻擊按鍵</span>
                        <span class="config-value">z</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">跳躍按鍵</span>
                        <span class="config-value">alt</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">攻擊範圍</span>
                        <span class="config-value">100px</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">啟用怪物</span>
                        <span class="config-value">3個</span>
                    </div>
                </div>

                <div class="config-section">
                    <h4>被動技能系統</h4>
                    <div class="config-item">
                        <span class="config-label">啟用被動技能</span>
                        <span class="config-value">開啟</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">技能1按鍵</span>
                        <span class="config-value">q</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">技能1冷卻</span>
                        <span class="config-value">30秒</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">啟用技能數</span>
                        <span class="config-value">2個</span>
                    </div>
                </div>

                <div class="config-section">
                    <h4>血量監控</h4>
                    <div class="config-item">
                        <span class="config-label">啟用監控</span>
                        <span class="config-value">開啟</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">HP閾值</span>
                        <span class="config-value">30%</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">MP閾值</span>
                        <span class="config-value">20%</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">補血按鍵</span>
                        <span class="config-value">home</span>
                    </div>
                </div>

                <div class="config-section">
                    <h4>移動系統</h4>
                    <div class="config-item">
                        <span class="config-label">跳躍移動</span>
                        <span class="config-value">開啟</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">位移技能</span>
                        <span class="config-value">開啟</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">爬繩功能</span>
                        <span class="config-value">開啟</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">下跳功能</span>
                        <span class="config-value">開啟</span>
                    </div>
                </div>
            </div>

            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-save"></i>
                    </div>
                    <div class="feature-title">保存設定</div>
                    <div class="feature-desc">
                        點擊「保存設定」按鈕將配置保存到外部文件，下次啟動時會自動載入。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-sync"></i>
                    </div>
                    <div class="feature-title">重置默認</div>
                    <div class="feature-desc">
                        「重置默認」按鈕會將所有設定恢復為原始值，清除自定義配置。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-check"></i>
                    </div>
                    <div class="feature-title">應用更改</div>
                    <div class="feature-desc">
                        「應用更改」按鈕會立即將設定套用到運行中的腳本，無需重啟。
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
                工具功能
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
                                <div class="visual-title">擷取角色ID</div>
                                <div class="visual-desc">點擊「📸 開始擷取角色ID」按鈕，選擇角色下方的名稱區域。</div>
                            </div>
                        </div>
                        <div class="tip-box">
                            <div class="box-title">
                                <i class="fas fa-lightbulb"></i>
                                使用技巧
                            </div>
                            建議在角色站立不動時進行擷取，選擇包含完整角色名稱的矩形區域。
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
                                <i class="fas fa-image"></i>
                            </div>
                            <div class="visual-content">
                                <div class="visual-title">繩子圖片管理</div>
                                <div class="visual-desc">支援多個繩子圖片，可預覽、刪除和新增繩子截圖。</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-title">怪物搜尋下載</div>
                    <div class="step-content">
                        <p>從官方API下載怪物圖片，支援搜尋和批量下載功能。</p>
                        <div class="step-visual">
                            <div class="visual-icon">
                                <i class="fas fa-download"></i>
                            </div>
                            <div class="visual-content">
                                <div class="visual-title">怪物圖片下載</div>
                                <div class="visual-desc">搜尋怪物名稱，勾選需要的怪物後點擊下載，會自動生成翻轉版本。</div>
                            </div>
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
                            <li>檢查是否有系統管理員權限</li>
                            <li>確認遊戲視窗名稱正確</li>
                            <li>重新啟動程式嘗試</li>
                        </ul>
                        <div class="warning-box">
                            <div class="box-title">
                                <i class="fas fa-exclamation-triangle"></i>
                                注意
                            </div>
                            遊戲必須處於前台且未被其他視窗遮蔽，腳本才能正常檢測遊戲畫面。
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
                            <li>確認遊戲處於視窗模式</li>
                            <li>檢查螢幕解析度設定</li>
                            <li>確保遊戲畫面完整可見</li>
                            <li>嘗試重新擷取截圖</li>
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
                </ul>
            </div>
        </section>
    </div>

    <script>
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