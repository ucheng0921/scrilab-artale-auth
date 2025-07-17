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
    <title>Artale 操作手冊 - Scrilab</title>
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
            margin-bottom: 4rem;
            padding: 3rem 0;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }

        .manual-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .manual-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .version-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-green);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        /* Table of Contents */
        .toc {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            margin-bottom: 3rem;
            position: sticky;
            top: 100px;
            z-index: 100;
        }

        .toc h3 {
            font-size: 1.4rem;
            margin-bottom: 1.5rem;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .toc-list {
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }

        .toc-item {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            transition: var(--transition);
        }

        .toc-item:hover {
            border-color: var(--accent-blue);
            transform: translateY(-2px);
        }

        .toc-link {
            display: block;
            padding: 1rem;
            color: var(--text-primary);
            text-decoration: none;
            font-weight: 500;
        }

        .toc-link:hover {
            color: var(--accent-blue);
        }

        /* Content Sections */
        .manual-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 3rem;
            margin-bottom: 2rem;
            scroll-margin-top: 100px;
        }

        .section-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .section-icon {
            width: 50px;
            height: 50px;
            background: var(--gradient-accent);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.3rem;
        }

        .step-container {
            display: grid;
            gap: 2rem;
            margin-top: 2rem;
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
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            margin-top: 0.5rem;
            color: var(--text-primary);
        }

        .step-content {
            color: var(--text-secondary);
            line-height: 1.7;
        }

        /* Code blocks */
        .code-block {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            font-family: 'Courier New', monospace;
            color: var(--accent-green);
            font-size: 0.95rem;
            overflow-x: auto;
            position: relative;
        }

        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .code-title {
            color: var(--accent-blue);
            font-weight: 600;
            font-size: 0.9rem;
        }

        .copy-btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            padding: 0.3rem 0.8rem;
            border-radius: 4px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: var(--transition);
        }

        .copy-btn:hover {
            background: var(--accent-purple);
        }

        /* Warning boxes */
        .warning-box, .info-box, .tip-box {
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1.5rem 0;
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

        /* Feature grid */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }

        .feature-card {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            transition: var(--transition);
        }

        .feature-card:hover {
            border-color: var(--accent-blue);
            transform: translateY(-5px);
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            background: var(--gradient-accent);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            font-size: 1.5rem;
            color: white;
        }

        .feature-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
            color: var(--text-primary);
        }

        .feature-desc {
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .manual-title {
                font-size: 2rem;
            }
            
            .toc-list {
                grid-template-columns: 1fr;
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
                    <i class="fas fa-code"></i>
                </div>
                <span>Scrilab</span>
            </a>
            <ul class="nav-links">
                <li><a href="/products#home">首頁</a></li>
                <li><a href="/products#features">服務特色</a></li>
                <li><a href="/products#games">遊戲服務</a></li>
                <li><a href="/products#contact">聯絡我們</a></li>
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
            <h1 class="manual-title">Artale 操作手冊</h1>
            <p class="manual-subtitle">MapleStory Worlds - Artale 遊戲技術服務完整操作指南</p>
            <span class="version-badge">版本 v2.1.0</span>
        </div>

        <!-- Table of Contents -->
        <div class="toc">
            <h3>
                <i class="fas fa-list"></i>
                目錄導航
            </h3>
            <ul class="toc-list">
                <li class="toc-item">
                    <a href="#installation" class="toc-link">
                        <i class="fas fa-download" style="margin-right: 0.5rem; color: var(--accent-green);"></i>
                        安裝與設置
                    </a>
                </li>
                <li class="toc-item">
                    <a href="#login" class="toc-link">
                        <i class="fas fa-sign-in-alt" style="margin-right: 0.5rem; color: var(--accent-blue);"></i>
                        登入與認證
                    </a>
                </li>
                <li class="toc-item">
                    <a href="#features" class="toc-link">
                        <i class="fas fa-cogs" style="margin-right: 0.5rem; color: var(--accent-purple);"></i>
                        功能介紹
                    </a>
                </li>
                <li class="toc-item">
                    <a href="#configuration" class="toc-link">
                        <i class="fas fa-sliders-h" style="margin-right: 0.5rem; color: var(--accent-orange);"></i>
                        參數設定
                    </a>
                </li>
                <li class="toc-item">
                    <a href="#troubleshooting" class="toc-link">
                        <i class="fas fa-wrench" style="margin-right: 0.5rem; color: var(--accent-red);"></i>
                        常見問題
                    </a>
                </li>
                <li class="toc-item">
                    <a href="#support" class="toc-link">
                        <i class="fas fa-life-ring" style="margin-right: 0.5rem; color: var(--accent-green);"></i>
                        技術支援
                    </a>
                </li>
            </ul>
        </div>

        <!-- Installation Section -->
        <section id="installation" class="manual-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-download"></i>
                </div>
                安裝與設置
            </h2>
            
            <div class="warning-box">
                <div class="box-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    重要提醒
                </div>
                使用前請確認您已購買合法序號，並且電腦符合最低系統需求。
            </div>

            <div class="step-container">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-title">系統需求檢查</div>
                    <div class="step-content">
                        <p>在開始安裝前，請確認您的系統符合以下需求：</p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>作業系統：Windows 10/11 (64位元)</li>
                            <li>記憶體：至少 4GB RAM</li>
                            <li>硬碟空間：500MB 可用空間</li>
                            <li>網路：穩定的網際網路連線</li>
                            <li>權限：系統管理員權限</li>
                        </ul>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-title">下載客戶端</div>
                    <div class="step-content">
                        <p>請從官方指定管道下載最新版本的客戶端程式。</p>
                        <div class="info-box">
                            <div class="box-title">
                                <i class="fas fa-info-circle"></i>
                                下載資訊
                            </div>
                            下載連結將在購買完成後透過 Email 提供，或透過 Discord 客服獲取。
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-title">安裝程式</div>
                    <div class="step-content">
                        <p>解壓縮下載的檔案，並以系統管理員身分執行安裝程式：</p>
                        <div class="code-block">
                            <div class="code-header">
                                <span class="code-title">安裝步驟</span>
                                <button class="copy-btn" onclick="copyCode(this)">複製</button>
                            </div>
                            <pre>1. 右鍵點選安裝檔案
2. 選擇「以系統管理員身分執行」
3. 依照安裝精靈指示完成安裝
4. 安裝完成後重新啟動電腦</pre>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Login Section -->
        <section id="login" class="manual-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-sign-in-alt"></i>
                </div>
                登入與認證
            </h2>

            <div class="step-container">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-title">啟動程式</div>
                    <div class="step-content">
                        <p>從桌面或開始選單啟動 Scrilab Artale 客戶端。首次啟動可能需要較長時間進行初始化。</p>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-title">輸入序號</div>
                    <div class="step-content">
                        <p>在登入畫面輸入您購買時獲得的專屬序號：</p>
                        <div class="code-block">
                            <div class="code-header">
                                <span class="code-title">序號格式範例</span>
                                <button class="copy-btn" onclick="copyCode(this)">複製</button>
                            </div>
                            <pre>artale_paid_a1b2c3d4e5f6_20241217</pre>
                        </div>
                        <div class="tip-box">
                            <div class="box-title">
                                <i class="fas fa-lightbulb"></i>
                                小提示
                            </div>
                            建議複製貼上序號以避免輸入錯誤。序號區分大小寫。
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-title">完成認證</div>
                    <div class="step-content">
                        <p>點擊「登入」按鈕，系統將自動驗證您的序號。認證成功後即可開始使用服務。</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section id="features" class="manual-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-cogs"></i>
                </div>
                功能介紹
            </h2>

            <p style="margin-bottom: 2rem; color: var(--text-secondary);">
                Scrilab Artale 提供多種先進的遊戲優化功能，以下是主要功能的詳細說明：
            </p>

            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-eye"></i>
                    </div>
                    <div class="feature-title">視覺識別系統</div>
                    <div class="feature-desc">
                        採用先進的圖像識別技術，能夠精確識別遊戲畫面中的各種元素，提供智能化的環境感知能力。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-random"></i>
                    </div>
                    <div class="feature-title">隨機性演算法</div>
                    <div class="feature-desc">
                        內建先進的隨機演算法系統，確保每次執行都具有獨特性，提供最自然的遊戲體驗。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-layer-group"></i>
                    </div>
                    <div class="feature-title">多線程處理</div>
                    <div class="feature-desc">
                        支援多線程並行處理，確保在各種複雜環境下都能穩定運行，提供流暢的使用體驗。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <div class="feature-title">安全保護機制</div>
                    <div class="feature-desc">
                        採用多層次加密保護，確保使用過程的安全性，保護您的帳號和個人資料安全。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-sliders-h"></i>
                    </div>
                    <div class="feature-title">自定義設定</div>
                    <div class="feature-desc">
                        提供豐富的參數調整選項，支援完全客製化設定，滿足不同玩家的個人化需求。
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="feature-title">效能監控</div>
                    <div class="feature-desc">
                        即時監控系統效能和運行狀態，提供詳細的統計數據和優化建議。
                    </div>
                </div>
            </div>
        </section>

        <!-- Configuration Section -->
        <section id="configuration" class="manual-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-sliders-h"></i>
                </div>
                參數設定
            </h2>

            <div class="step-container">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-title">基本設定</div>
                    <div class="step-content">
                        <p>在主介面點擊「設定」按鈕，進入參數設定頁面。基本設定包括：</p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li><strong>執行間隔：</strong>調整動作執行的時間間隔（建議 100-300ms）</li>
                            <li><strong>隨機延遲：</strong>開啟隨機延遲以增加自然性</li>
                            <li><strong>視窗模式：</strong>選擇全螢幕或視窗模式運行</li>
                            <li><strong>自動暫停：</strong>設定自動暫停的條件</li>
                        </ul>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-title">進階設定</div>
                    <div class="step-content">
                        <p>進階設定適合有經驗的使用者調整：</p>
                        <div class="code-block">
                            <div class="code-header">
                                <span class="code-title">設定檔範例</span>
                                <button class="copy-btn" onclick="copyCode(this)">複製</button>
                            </div>
                            <pre>{
  "execution_interval": 150,
  "random_delay": true,
  "max_random_delay": 50,
  "auto_pause_on_player": true,
  "detection_sensitivity": 0.8,
  "multi_thread_enabled": true,
  "thread_count": 2
}</pre>
                        </div>
                        <div class="warning-box">
                            <div class="box-title">
                                <i class="fas fa-exclamation-triangle"></i>
                                注意事項
                            </div>
                            請勿隨意修改進階設定，錯誤的設定可能導致程式無法正常運行。
                        </div>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-title">熱鍵設定</div>
                    <div class="step-content">
                        <p>自定義熱鍵來快速控制程式運行：</p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li><strong>F1：</strong>開始/暫停功能</li>
                            <li><strong>F2：</strong>停止所有功能</li>
                            <li><strong>F3：</strong>顯示/隱藏主介面</li>
                            <li><strong>F4：</strong>緊急停止</li>
                        </ul>
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
                常見問題與解決方案
            </h2>

            <div class="step-container">
                <div class="step">
                    <div class="step-number">Q1</div>
                    <div class="step-title">程式無法啟動</div>
                    <div class="step-content">
                        <p><strong>可能原因：</strong></p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>防毒軟體阻擋</li>
                            <li>缺少系統管理員權限</li>
                            <li>缺少必要的執行檔</li>
                        </ul>
                        <p><strong>解決方法：</strong></p>
                        <ol style="margin: 1rem 0; padding-left: 2rem;">
                            <li>將程式加入防毒軟體白名單</li>
                            <li>以系統管理員身分執行</li>
                            <li>重新安裝最新版本</li>
                        </ol>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">Q2</div>
                    <div class="step-title">序號驗證失敗</div>
                    <div class="step-content">
                        <p><strong>可能原因：</strong></p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>序號輸入錯誤</li>
                            <li>序號已過期</li>
                            <li>網路連線問題</li>
                        </ul>
                        <p><strong>解決方法：</strong></p>
                        <ol style="margin: 1rem 0; padding-left: 2rem;">
                            <li>檢查序號拼寫，建議複製貼上</li>
                            <li>確認服務是否仍在有效期內</li>
                            <li>檢查網路連線並重試</li>
                        </ol>
                    </div>
                </div>

                <div class="step">
                    <div class="step-number">Q3</div>
                    <div class="step-title">功能無法正常運作</div>
                    <div class="step-content">
                        <p><strong>可能原因：</strong></p>
                        <ul style="margin: 1rem 0; padding-left: 2rem;">
                            <li>遊戲版本更新</li>
                            <li>螢幕解析度問題</li>
                            <li>設定參數錯誤</li>
                        </ul>
                        <p><strong>解決方法：</strong></p>
                        <ol style="margin: 1rem 0; padding-left: 2rem;">
                            <li>確認使用最新版本客戶端</li>
                            <li>調整螢幕解析度至建議設定</li>
                            <li>重置設定至預設值</li>
                        </ol>
                    </div>
                </div>
            </div>

            <div class="info-box">
                <div class="box-title">
                    <i class="fas fa-info-circle"></i>
                    找不到解決方案？
                </div>
                如果以上方法都無法解決您的問題，請透過 Discord 或 Email 聯繫我們的技術支援團隊。
            </div>
        </section>

        <!-- Support Section -->
        <section id="support" class="manual-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-life-ring"></i>
                </div>
                技術支援
            </h2>

            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fab fa-discord"></i>
                    </div>
                    <div class="feature-title">Discord 即時支援</div>
                    <div class="feature-desc">
                        加入我們的 Discord 伺服器，獲得即時的技術支援和與其他用戶交流的機會。
                        <br><br>
                        <a href="https://discord.gg/HPzNrQmN" target="_blank" style="color: var(--accent-blue); text-decoration: none;">
                            <i class="fas fa-external-link-alt"></i> 立即加入 Discord
                        </a>
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-envelope"></i>
                    </div>
                    <div class="feature-title">Email 客服</div>
                    <div class="feature-desc">
                        透過 Email 與我們聯繫，我們會在 24 小時內回覆您的問題。
                        <br><br>
                        <a href="mailto:pink870921aa@gmail.com" style="color: var(--accent-blue); text-decoration: none;">
                            <i class="fas fa-envelope"></i> pink870921aa@gmail.com
                        </a>
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="feature-title">服務時間</div>
                    <div class="feature-desc">
                        <strong>Discord 即時支援：</strong><br>
                        週一至週日 09:00 - 23:00<br><br>
                        <strong>Email 回覆：</strong><br>
                        24 小時內回覆（節假日可能延遲）
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-file-alt"></i>
                    </div>
                    <div class="feature-title">提交問題時請提供</div>
                    <div class="feature-desc">
                        <ul style="list-style: none; padding: 0;">
                            <li>• 您的序號（前8位即可）</li>
                            <li>• 問題發生的詳細描述</li>
                            <li>• 錯誤訊息截圖</li>
                            <li>• 您的作業系統版本</li>
                            <li>• 遊戲版本資訊</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="tip-box">
                <div class="box-title">
                    <i class="fas fa-lightbulb"></i>
                    獲得更快支援的秘訣
                </div>
                詳細描述您的問題，包含錯誤訊息和操作步驟，可以讓我們更快速地為您解決問題。
            </div>

            <div class="warning-box">
                <div class="box-title">
                    <i class="fas fa-shield-alt"></i>
                    隱私保護
                </div>
                請勿在公開場合分享您的完整序號。我們的客服人員絕不會要求您提供完整序號或密碼。
            </div>
        </section>
    </div>

    <script>
        // Smooth scrolling for TOC links
        document.querySelectorAll('.toc-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Copy code functionality
        function copyCode(button) {
            const codeBlock = button.closest('.code-block');
            const code = codeBlock.querySelector('pre').textContent;
            
            navigator.clipboard.writeText(code).then(() => {
                const originalText = button.textContent;
                button.textContent = '已複製';
                button.style.background = 'var(--accent-green)';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = 'var(--accent-blue)';
                }, 2000);
            }).catch(err => {
                console.error('複製失敗:', err);
                alert('複製失敗，請手動選取文字複製');
            });
        }

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

        // Highlight current section in TOC
        window.addEventListener('scroll', function() {
            const sections = document.querySelectorAll('.manual-section');
            const tocLinks = document.querySelectorAll('.toc-link');
            
            let currentSection = '';
            sections.forEach(section => {
                const rect = section.getBoundingClientRect();
                if (rect.top <= 150 && rect.bottom >= 150) {
                    currentSection = section.id;
                }
            });
            
            tocLinks.forEach(link => {
                const href = link.getAttribute('href').substring(1);
                if (href === currentSection) {
                    link.style.color = 'var(--accent-blue)';
                    link.closest('.toc-item').style.borderColor = 'var(--accent-blue)';
                } else {
                    link.style.color = 'var(--text-primary)';
                    link.closest('.toc-item').style.borderColor = 'var(--border-color)';
                }
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