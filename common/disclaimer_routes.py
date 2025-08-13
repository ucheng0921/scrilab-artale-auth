"""
disclaimer_routes.py - 免責聲明路由處理
"""
from flask import Blueprint, render_template_string

# 創建免責聲明藍圖
disclaimer_bp = Blueprint('disclaimer', __name__, url_prefix='/disclaimer')

# 免責聲明 HTML 模板
DISCLAIMER_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>免責聲明 - Scrilab</title>
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
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }

        .disclaimer-header {
            text-align: center;
            margin-bottom: 4rem;
            padding: 3rem 0;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }

        .disclaimer-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .disclaimer-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .last-updated {
            display: inline-block;
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: var(--accent-orange);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        /* Content Sections */
        .disclaimer-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 3rem;
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
            width: 40px;
            height: 40px;
            background: var(--gradient-accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.1rem;
        }

        .section-content {
            color: var(--text-secondary);
            line-height: 1.8;
        }

        .section-content h4 {
            color: var(--text-primary);
            font-size: 1.2rem;
            font-weight: 600;
            margin: 2rem 0 1rem 0;
        }

        .section-content p {
            margin-bottom: 1.5rem;
        }

        .section-content ul, .section-content ol {
            margin: 1.5rem 0;
            padding-left: 2rem;
        }

        .section-content li {
            margin-bottom: 0.8rem;
        }

        /* Warning boxes */
        .warning-box, .info-box, .important-box {
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
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

        .important-box {
            background: rgba(245, 158, 11, 0.1);
            border-left-color: var(--accent-orange);
            color: #fbbf24;
        }

        .box-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: inherit;
        }

        .box-content {
            line-height: 1.6;
        }

        /* Table styles */
        .content-table {
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
            background: var(--bg-tertiary);
            border-radius: 8px;
            overflow: hidden;
        }

        .content-table th,
        .content-table td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        .content-table th {
            background: var(--bg-secondary);
            color: var(--accent-blue);
            font-weight: 600;
        }

        .content-table tr:last-child td {
            border-bottom: none;
        }

        /* Contact section - 修正樣式問題 */
        .contact-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            text-align: center;
            margin-top: 3rem;
            max-width: 100%; /* 限制最大寬度 */
        }

        .contact-section h3 {
            color: var(--text-primary);
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .contact-section p {
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            font-size: 1rem;
        }

        .contact-methods {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin: 1.5rem 0;
            flex-wrap: wrap;
        }

        .contact-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.95rem;
            transition: var(--transition);
            padding: 0.8rem 1.2rem;
            border-radius: 8px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            min-width: 140px;
            justify-content: center;
        }

        .contact-link:hover {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
            transform: translateY(-2px);
        }

        .contact-footer {
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
        }

        .contact-footer p {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin: 0;
            line-height: 1.4;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .disclaimer-title {
                font-size: 2rem;
            }
            
            .nav-links {
                display: none;
            }
            
            .disclaimer-section {
                padding: 2rem;
            }
            
            .contact-methods {
                flex-direction: column;
                align-items: center;
                gap: 1rem;
            }
            
            .contact-link {
                min-width: 200px;
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
                <li><a href="/products#games">遊戲服務</a></li>
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
        <!-- Header -->
        <div class="disclaimer-header">
            <h1 class="disclaimer-title">免責聲明</h1>
            <p class="disclaimer-subtitle">服務條款與法律聲明</p>
            <span class="last-updated">最後更新：2025年7月29日</span>
        </div>

        <!-- 1. 軟體性質與技術說明 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-cog"></i>
                </div>
                軟體性質與技術說明
            </h2>
            <div class="section-content">
                <div class="important-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        軟體定義
                    </div>
                    <div class="box-content">
                        本服務所提供之軟體程式為「智能遊戲輔助工具」，採用純本地運算技術，專為提升使用者遊戲體驗而設計。
                    </div>
                </div>

                <h4>核心技術架構</h4>
                <p>本網站 (scrilab.com) 所提供、銷售之軟體程式，基於以下先進技術實現：</p>
                <ul>
                    <li><strong>計算機視覺技術：</strong>運用深度學習算法進行畫面識別與分析</li>
                    <li><strong>本地數據處理：</strong>僅在使用者電腦內進行數據讀取與計算處理</li>
                    <li><strong>智能決策系統：</strong>基於AI算法提供遊戲策略建議與操作優化</li>
                    <li><strong>視覺輔助渲染：</strong>在本地畫面上疊加輔助資訊與視覺提示</li>
                    <li><strong>自動化腳本引擎：</strong>提供可自定義的操作自動化功能</li>
                </ul>

                <h4>技術特性說明</h4>
                <p>本軟體採用完全本地化的技術架構，具有以下核心特性：</p>
                <ol>
                    <li><strong>本地運算：</strong>所有功能均在使用者電腦上獨立運行</li>
                    <li><strong>純粹輔助：</strong>提供資訊輔助與操作建議，不修改遊戲數據</li>
                    <li><strong>視覺增強：</strong>透過畫面疊加技術提供額外視覺資訊</li>
                    <li><strong>智能分析：</strong>運用AI技術分析遊戲狀況並提供優化建議</li>
                    <li><strong>個人化設定：</strong>支援使用者自定義功能參數與使用偏好</li>
                </ol>

                <h4>技術邊界與限制</h4>
                <p>為確保技術的合法性與安全性，本軟體嚴格遵循以下技術邊界：</p>
                <ul>
                    <li><strong>無網路交互：</strong>不與遊戲伺服器進行任何形式的通訊或交互</li>
                    <li><strong>無數據修改：</strong>不對遊戲檔案、記憶體數據或網路封包進行修改</li>
                    <li><strong>無系統入侵：</strong>不利用任何系統漏洞或進行未授權的系統存取</li>
                    <li><strong>無惡意行為：</strong>不包含病毒、木馬或其他惡意程式碼</li>
                    <li><strong>透明運作：</strong>所有功能對使用者完全透明，無隱藏或後門程式</li>
                </ul>

                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-shield-alt"></i>
                        安全性保證
                    </div>
                    <div class="box-content">
                        本軟體經過嚴格的安全測試，不含任何惡意程式碼，不會損害使用者電腦或洩露個人資訊。所有功能均為合法的技術實現，符合軟體工程的最佳實踐標準。
                    </div>
                </div>
            </div>
        </section>

        <!-- 2. 使用風險與責任承擔 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-shield-alt"></i>
                </div>
                使用風險與責任承擔
            </h2>
            <div class="section-content">
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        風險警告
                    </div>
                    <div class="box-content">
                        任何第三方輔助軟體都存在被遊戲工作室檢測並違反服務條款的風險。使用前請仔細評估個人風險承受能力。
                    </div>
                </div>

                <h4>使用者風險認知</h4>
                <p>使用者需明確了解並接受以下風險：</p>
                <ul>
                    <li><strong>帳號處罰風險：</strong>可能面臨遊戲帳號被警告、暫停或永久封禁</li>
                    <li><strong>服務條款違反：</strong>可能違反遊戲工作室的使用者條款或服務協議</li>
                    <li><strong>檢測技術進步：</strong>遊戲工作室反作弊技術持續升級，檢測能力不斷增強</li>
                    <li><strong>法律法規變化：</strong>相關法律法規可能隨時調整，影響軟體合法性</li>
                </ul>

                <h4>責任歸屬聲明</h4>
                <p>若您選擇使用本軟體，即表示您：</p>
                <ol>
                    <li><strong>完全理解風險：</strong>已充分了解使用第三方輔助軟體的所有潛在風險</li>
                    <li><strong>自行承擔後果：</strong>因使用本軟體導致的任何損失或法律爭議，由使用者自行承擔</li>
                    <li><strong>購買即同意：</strong>購買並使用本軟體即表示同意承擔所有相關風險</li>
                    <li><strong>遵守行為準則：</strong>不得利用軟體功能進行任何違法或不當行為</li>
                </ol>

                <h4>建議使用方式</h4>
                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-lightbulb"></i>
                        最佳實踐建議
                    </div>
                    <div class="box-content">
                        建議使用者將本軟體主要用於學習計算機技術和了解自動化原理。如作為遊戲輔助使用，建議在測試環境中短期試用，並隨時做好承擔風險的心理準備。
                    </div>
                </div>

                <h4>禁止行為清單</h4>
                <p>使用者嚴格禁止利用本軟體進行以下行為：</p>
                <ul>
                    <li>對他人進行侮辱、暴力、霸凌或騷擾行為</li>
                    <li>進行詐欺、欺騙或其他違法犯罪活動</li>
                    <li>惡意破壞遊戲環境或影響他人遊戲體驗</li>
                    <li>將軟體用於商業營利或大規模作弊行為</li>
                    <li>違反當地法律法規或社會公德的行為</li>
                </ul>
                <p>若因違反上述規定產生糾紛，本工作室有權不經催告立即終止服務合約。</p>
            </div>
        </section>

        <!-- 3. 服務條款與使用限制 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-file-contract"></i>
                </div>
                服務條款與使用限制
            </h2>
            <div class="section-content">
                <h4>軟體更新與維護</h4>
                <p>本軟體可能因以下情況需要更新或暫停服務：</p>
                <ul>
                    <li><strong>目標遊戲更新：</strong>遊戲版本升級導致軟體功能需要調整</li>
                    <li><strong>系統維護需求：</strong>遊戲官方進行系統維護或安全修復</li>
                    <li><strong>反作弊升級：</strong>遊戲工作室加強反作弊檢測機制</li>
                    <li><strong>技術改進：</strong>為提升功能穩定性和安全性進行升級</li>
                    <li><strong>法規遵循：</strong>配合法律法規要求進行調整</li>
                </ul>
                <p>上述情況可能導致軟體暫時或永久無法使用，更新處理需要時間，本工作室將盡力減少服務中斷，但不保證服務的持續可用性。</p>

                <h4>數位內容交易特性</h4>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        退款政策聲明
                    </div>
                    <div class="box-content">
                        根據消費者保護法第十九條第二項規定，本服務為數位內容或一經提供即為完成之線上服務，不適用七天鑑賞期。軟體售出後一般情況下不提供退貨退款服務。
                    </div>
                </div>

                <h4>特殊情況退款處理</h4>
                <p>在以下特殊情況下，本工作室可能考慮提供退款：</p>
                <ul>
                    <li><strong>技術無法實現：</strong>因技術限制導致軟體完全無法運行</li>
                    <li><strong>重大功能缺失：</strong>軟體核心功能與描述嚴重不符</li>
                    <li><strong>服務提前終止：</strong>因不可抗力或工作室決策導致服務提前結束</li>
                    <li><strong>系統相容性：</strong>軟體與使用者系統完全不相容且無法解決</li>
                </ul>

                <h4>價格與交易規範</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>資料類型</th>
                            <th>保留期限</th>
                            <th>刪除條件</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>帳號基本資訊</td>
                            <td>服務期滿後30天</td>
                            <td>用於處理可能的售後服務需求</td>
                        </tr>
                        <tr>
                            <td>使用行為記錄</td>
                            <td>服務期滿後90天</td>
                            <td>用於服務改進和問題追蹤</td>
                        </tr>
                        <tr>
                            <td>交易付款記錄</td>
                            <td>5年</td>
                            <td>符合稅務法規和會計準則要求</td>
                        </tr>
                        <tr>
                            <td>技術日誌資料</td>
                            <td>6個月</td>
                            <td>用於故障診斷和安全監控</td>
                        </tr>
                    </tbody>
                </table>

                <h4>使用者權利</h4>
                <p>根據個人資料保護法，使用者享有以下權利：</p>
                <ul>
                    <li><strong>查詢權：</strong>查詢個人資料被收集、處理、利用的情況</li>
                    <li><strong>請求停止權：</strong>請求停止收集、處理或利用個人資料</li>
                    <li><strong>請求刪除權：</strong>請求刪除個人資料（法律要求保留除外）</li>
                    <li><strong>請求更正權：</strong>發現個人資料錯誤時請求更正</li>
                </ul>

                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        權利行使方式
                    </div>
                    <div class="box-content">
                        如需行使上述權利，請透過Discord社群聯繫我們，我們將在15個工作日內回應您的請求。
                    </div>
                </div>
            </div>
        </section>

        <!-- 4. 隱私權政策與資料保護 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-user-shield"></i>
                </div>
                隱私權政策與資料保護
            </h2>
            <div class="section-content">
                <h4>資料收集範圍</h4>
                <p>為提供服務品質並維護系統安全，我們可能收集以下資訊：</p>
                <ul>
                    <li><strong>帳號資訊：</strong>使用者序號、顯示名稱、服務期限、註冊時間</li>
                    <li><strong>聯絡資訊：</strong>Discord用戶資訊（選填）</li>
                    <li><strong>使用記錄：</strong>登入時間、使用頻率、功能使用統計</li>
                    <li><strong>技術資訊：</strong>IP位址、設備識別碼、作業系統版本</li>
                    <li><strong>交易資訊：</strong>透過Gumroad平台處理的付款記錄</li>
                </ul>

                <h4>資料使用目的</h4>
                <p>收集的個人資訊僅用於以下合法目的：</p>
                <ol>
                    <li><strong>服務提供：</strong>驗證身份、開通服務、維護帳號安全</li>
                    <li><strong>技術支援：</strong>提供客戶服務、解決技術問題</li>
                    <li><strong>服務改善：</strong>分析使用情況、優化產品功能</li>
                    <li><strong>安全防護：</strong>防範詐欺、濫用和安全威脅</li>
                    <li><strong>法律遵循：</strong>遵守相關法律法規要求</li>
                </ol>

                <h4>資料保護措施</h4>
                <p>我們採取以下技術與管理措施保護使用者資料：</p>
                <ul>
                    <li>使用SSL加密技術保護資料傳輸過程</li>
                    <li>實施存取控制，限制員工對資料的存取權限</li>
                    <li>定期進行安全性檢查和系統更新</li>
                    <li>建立資料備份和災難恢復機制</li>
                    <li>絕不將個人資料出售或提供給無關第三方</li>
                </ul>

                <h4>資料保留與刪除</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>資料類型</th>
                            <th>保留期限</th>
                            <th>刪除條件</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>帳號基本資訊</td>
                            <td>服務期滿後30天</td>
                            <td>用於處理可能的售後服務需求</td>
                        </tr>
                        <tr>
                            <td>使用行為記錄</td>
                            <td>服務期滿後90天</td>
                            <td>用於服務改進和問題追蹤</td>
                        </tr>
                        <tr>
                            <td>交易付款記錄</td>
                            <td>5年</td>
                            <td>符合稅務法規和會計準則要求</td>
                        </tr>
                        <tr>
                            <td>技術日誌資料</td>
                            <td>6個月</td>
                            <td>用於故障診斷和安全監控</td>
                        </tr>
                    </tbody>
                </table>

                <h4>使用者權利</h4>
                <p>根據個人資料保護法，使用者享有以下權利：</p>
                <ul>
                    <li><strong>查詢權：</strong>查詢個人資料被收集、處理、利用的情況</li>
                    <li><strong>請求停止權：</strong>請求停止收集、處理或利用個人資料</li>
                    <li><strong>請求刪除權：</strong>請求刪除個人資料（法律要求保留除外）</li>
                    <li><strong>請求更正權：</strong>發現個人資料錯誤時請求更正</li>
                </ul>

                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        權利行使方式
                    </div>
                    <div class="box-content">
                        如需行使上述權利，請透過Discord社群聯繫我們，我們將在15個工作日內回應您的請求。
                    </div>
                </div>

                <h4>第三方服務整合</h4>
                <p>本服務可能整合以下第三方服務，請注意其隱私政策：</p>
                <ul>
                    <li><strong>支付處理商：</strong>Gumroad平台處理付款和交易</li>
                    <li><strong>通訊服務：</strong>Discord社群平台</li>
                    <li><strong>分析工具：</strong>網站流量分析、使用行為統計（僅匿名資料）</li>
                    <li><strong>雲端服務：</strong>資料儲存、備份服務（均採用加密傳輸）</li>
                </ul>

                <h4>隱私政策修訂</h4>
                <p>本隱私政策可能因法規變化或服務調整而修訂：</p>
                <ol>
                    <li>重大修改將提前30天在官網顯著位置公告</li>
                    <li>在Discord社群發布更新通知</li>
                    <li>修改後的政策自公告日起生效</li>
                    <li>繼續使用服務視為同意修改後的隱私政策</li>
                </ol>

                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        資料安全提醒
                    </div>
                    <div class="box-content">
                        請妥善保管您的帳號資訊，不要與他人分享序號或登入憑證。如發現帳號異常使用，請立即聯繫客服處理。我們不會主動要求您提供密碼或敏感資訊。
                    </div>
                </div>

                <h4>跨境資料傳輸</h4>
                <p>基於服務需要，部分資料可能需要跨境傳輸：</p>
                <ul>
                    <li>僅在必要時進行跨境傳輸</li>
                    <li>確保接收方具備適當的資料保護措施</li>
                    <li>傳輸過程使用加密技術保護</li>
                    <li>遵守台灣個人資料保護法相關規定</li>
                </ul>

                <h4>資料外洩應變</h4>
                <p>如發生資料安全事件，我們將：</p>
                <ol>
                    <li>立即啟動應變程序，控制事件影響範圍</li>
                    <li>在72小時內評估事件嚴重程度</li>
                    <li>如有重大風險，將立即通知受影響使用者</li>
                    <li>配合主管機關調查並提交必要報告</li>
                    <li>檢討改善資安措施，防止類似事件再次發生</li>
                </ol>
            </div>
        </section>

        <!-- 5. 技術支援與客戶服務 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-headset"></i>
                </div>
                技術支援與客戶服務
            </h2>
            <div class="section-content">
                <h4>支援服務範圍</h4>
                <p>我們提供以下技術支援與客戶服務：</p>
                <ul>
                    <li><strong>安裝與配置：</strong>協助軟體正確安裝和初始設定</li>
                    <li><strong>使用指導：</strong>提供詳細操作教學和功能說明</li>
                    <li><strong>故障排除：</strong>協助診斷和解決技術問題</li>
                    <li><strong>帳號服務：</strong>處理序號驗證、登入授權等帳號問題</li>
                    <li><strong>更新通知：</strong>及時通知軟體更新和重要資訊</li>
                    <li><strong>使用諮詢：</strong>回答功能使用和最佳實踐相關問題</li>
                </ul>

                <h4>聯繫管道與回應時間</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>聯繫方式</th>
                            <th>服務時間</th>
                            <th>預期回應時間</th>
                            <th>適用情況</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Discord即時客服</td>
                            <td>每日 09:00 - 23:00</td>
                            <td>通常5-15分鐘</td>
                            <td>緊急技術問題、即時諮詢</td>
                        </tr>
                        <tr>
                            <td>線上操作手冊</td>
                            <td>24小時開放</td>
                            <td>即時查閱</td>
                            <td>自助解決常見問題</td>
                        </tr>
                    </tbody>
                </table>

                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        主要聯繫資訊
                    </div>
                    <div class="box-content">
                        <strong>Discord社群：</strong>https://discord.gg/HPzNrQmN（推薦使用，回應最快）<br>
                        <strong>操作手冊：</strong>/manual（詳細使用說明文檔）
                    </div>
                </div>

                <h4>技術支援限制</h4>
                <p>以下情況可能無法提供完整技術支援：</p>
                <ul>
                    <li>因違反遊戲服務條款導致的帳號處罰問題</li>
                    <li>使用者自行修改軟體代碼導致的故障</li>
                    <li>與本軟體無直接關聯的電腦或遊戲問題</li>
                    <li>已超過服務期限的過期帳號</li>
                    <li>使用盜版或非法取得的軟體副本</li>
                    <li>在不支援的作業系統或硬體環境中使用</li>
                </ul>

                <h4>服務品質承諾</h4>
                <p>我們承諾提供專業、及時、友善的客戶服務：</p>
                <ol>
                    <li>耐心回答使用者的合理諮詢</li>
                    <li>提供準確的技術指導和解決方案</li>
                    <li>尊重使用者隱私，保護個人資訊</li>
                    <li>持續改進服務品質和響應效率</li>
                </ol>
            </div>
        </section>

        <!-- 6. 法律責任與免責條款 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-balance-scale"></i>
                </div>
                法律責任與免責條款
            </h2>
            <div class="section-content">
                <h4>責任範圍限制</h4>
                <p>在法律允許的最大範圍內，Scrilab及其關聯方對以下情況不承擔任何責任：</p>
                <ul>
                    <li><strong>帳號處罰：</strong>因使用本軟體導致的遊戲帳號警告、暫停、封鎖或其他處罰措施</li>
                    <li><strong>虛擬資產損失：</strong>遊戲角色、裝備、貨幣、等級或其他虛擬財產的損失</li>
                    <li><strong>經濟損失：</strong>因服務中斷、帳號處罰等導致的直接或間接經濟損失</li>
                    <li><strong>法律糾紛：</strong>因使用本軟體而產生的任何法律爭議、訴訟或法律後果</li>
                    <li><strong>第三方行為：</strong>遊戲工作室、其他使用者或第三方的行為導致的損失</li>
                    <li><strong>技術風險：</strong>軟體bug、相容性問題或其他技術缺陷</li>
                </ul>

                <h4>服務提供基礎</h4>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        「現狀」提供聲明
                    </div>
                    <div class="box-content">
                        本軟體按「現狀」(AS IS) 提供，不提供任何明示或暗示的保證，包括但不限於適銷性、特定用途適用性、不侵權性或持續可用性的保證。
                    </div>
                </div>

                <h4>損害賠償限制</h4>
                <p>即使在承擔責任的情況下，我們的賠償責任也受到以下限制：</p>
                <ol>
                    <li><strong>賠償上限：</strong>任何情況下的賠償金額不超過使用者已支付的服務費用</li>
                    <li><strong>間接損害免責：</strong>不承擔任何間接、偶然、特殊、懲罰性或後果性損害</li>
                    <li><strong>營業損失免責：</strong>不承擔因無法使用服務導致的營業中斷或利潤損失</li>
                    <li><strong>資料損失免責：</strong>不承擔資料丟失、損壞或洩露的責任</li>
                </ol>

                <h4>使用者同意與確認</h4>
                <p>使用者在購買和使用本軟體時，即表示已經：</p>
                <ul>
                    <li>詳細閱讀並完全理解本免責聲明的全部內容</li>
                    <li>明確知曉使用輔助軟體面臨的所有風險和法律後果</li>
                    <li>理解並接受本軟體的技術局限性和使用限制</li>
                    <li>同意承擔使用過程中可能發生的全部風險和責任</li>
                    <li>願意遵守本免責聲明和服務條款的所有規定</li>
                    <li>確認具有完全民事行為能力並有權簽署本協議</li>
                </ul>

                <h4>管轄法律與爭議解決</h4>
                <p>本免責聲明的解釋、效力及爭議解決適用中華民國（台灣）法律。如發生爭議：</p>
                <ol>
                    <li><strong>協商解決：</strong>雙方應首先透過友好協商方式解決爭議</li>
                    <li><strong>調解程序：</strong>協商不成時，可申請相關調解機構進行調解</li>
                    <li><strong>司法管轄：</strong>調解失敗的，任何一方均可向台北地方法院提起訴訟</li>
                    <li><strong>法律費用：</strong>敗訴方承擔勝訴方的合理法律費用</li>
                </ol>

                <div class="important-box">
                    <div class="box-title">
                        <i class="fas fa-gavel"></i>
                        最終解釋權與條款分離
                    </div>
                    <div class="box-content">
                        本免責聲明的最終解釋權歸Scrilab所有。如有任何條款被法院認定無效或不可執行，該無效條款將被視為從本聲明中分離，但不影響其他條款的效力和可執行性。
                    </div>
                </div>
            </div>
        </section>

        <!-- 7. 服務變更與終止條款 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-sync-alt"></i>
                </div>
                服務變更與終止條款
            </h2>
            <div class="section-content">
                <h4>服務變更權利</h4>
                <p>本工作室保留隨時修改、暫停或終止全部或部分服務的權利，變更原因包括但不限於：</p>
                <ul>
                    <li><strong>技術升級需要：</strong>為提升服務品質、安全性或效能進行技術改進</li>
                    <li><strong>法規合規要求：</strong>配合法律法規變化或政府部門要求</li>
                    <li><strong>商業策略調整：</strong>基於商業考量調整產品方向或服務範圍</li>
                    <li><strong>不可抗力因素：</strong>自然災害、戰爭、政策變化等不可預見情況</li>
                    <li><strong>安全威脅應對：</strong>應對網路攻擊、資料安全威脅等緊急情況</li>
                    <li><strong>第三方影響：</strong>合作夥伴、供應商或平台方的變化影響</li>
                </ul>

                <h4>變更通知機制</h4>
                <p>重大服務變更將透過以下方式提前通知使用者：</p>
                <ol>
                    <li><strong>官方網站公告：</strong>在scrilab.com首頁發布重要通知</li>
                    <li><strong>Discord社群公告：</strong>在官方Discord伺服器置頂發布公告</li>
                    <li><strong>軟體內通知：</strong>透過軟體啟動時的通知功能告知使用者</li>
                </ol>

                <p>一般變更將提前7天通知，重大變更將提前30天通知，緊急安全變更可能無法提前通知。</p>

                <h4>服務終止情況與處理</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>終止原因</th>
                            <th>通知期間</th>
                            <th>退款政策</th>
                            <th>資料處理</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>使用者違規行為</td>
                            <td>立即終止</td>
                            <td>不予退款</td>
                            <td>立即刪除所有帳號資料</td>
                        </tr>
                        <tr>
                            <td>技術無法實現</td>
                            <td>提前14天通知</td>
                            <td>按剩餘時間比例退款</td>
                            <td>保留30天後安全刪除</td>
                        </tr>
                        <tr>
                            <td>法律法規要求</td>
                            <td>依法律規定</td>
                            <td>依相關法規處理</td>
                            <td>依法律要求處理</td>
                        </tr>
                        <tr>
                            <td>商業決策終止</td>
                            <td>提前30天通知</td>
                            <td>可申請比例退款</td>
                            <td>保留90天後刪除</td>
                        </tr>
                        <tr>
                            <td>不可抗力因素</td>
                            <td>盡快通知</td>
                            <td>視情況決定</td>
                            <td>盡力保護使用者資料</td>
                        </tr>
                    </tbody>
                </table>

                <h4>使用者權利保障</h4>
                <p>在服務變更或終止過程中，我們將盡力保障使用者權利：</p>
                <ul>
                    <li>提供充分的事前通知和說明</li>
                    <li>協助使用者轉移或備份重要資料</li>
                    <li>在合理範圍內提供替代解決方案</li>
                    <li>按照承諾處理退款和補償事宜</li>
                    <li>維持客戶服務直至服務完全終止</li>
                </ul>

                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        服務連續性承諾
                    </div>
                    <div class="box-content">
                        我們將盡最大努力維持服務的穩定性和連續性，並在面臨服務變更時優先考慮使用者利益和體驗。任何非緊急變更都將提供合理的過渡期。
                    </div>
                </div>
            </div>
        </section>

        <!-- 8. 最終聲明與生效條款 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-certificate"></i>
                </div>
                最終聲明與生效條款
            </h2>
            <div class="section-content">
                <h4>聲明生效時機</h4>
                <p>本免責聲明自使用者進行以下任一行為時即對其產生法律約束力：</p>
                <ol>
                    <li><strong>網站訪問：</strong>訪問scrilab.com網站的任何頁面</li>
                    <li><strong>軟體下載：</strong>下載本工作室提供的任何軟體或相關檔案</li>
                    <li><strong>試用體驗：</strong>使用任何形式的試用版本或演示功能</li>
                    <li><strong>購買行為：</strong>完成任何付款購買流程</li>
                    <li><strong>帳號註冊：</strong>註冊或建立使用者帳號</li>
                    <li><strong>軟體執行：</strong>安裝、配置或運行本軟體</li>
                </ol>

                <h4>使用者理解與承諾確認</h4>
                <p>使用者透過上述任一行為確認並承諾：</p>
                <ul>
                    <li><strong>完整閱讀：</strong>已詳細閱讀本免責聲明的全部內容，無任何遺漏</li>
                    <li><strong>充分理解：</strong>完全理解聲明中涉及的所有條款、風險和法律後果</li>
                    <li><strong>風險認知：</strong>明確知曉使用輔助軟體可能面臨的所有潛在風險</li>
                    <li><strong>技術理解：</strong>理解本軟體的技術原理、功能限制和運作方式</li>
                    <li><strong>責任承擔：</strong>同意承擔使用過程中可能發生的全部責任和後果</li>
                    <li><strong>條款遵守：</strong>願意嚴格遵守本聲明和相關服務條款的所有規定</li>
                    <li><strong>法律能力：</strong>確認具有完全民事行為能力並有權簽署本協議</li>
                    <li><strong>真實意思：</strong>確認以上同意係出於真實意思表示，非受脅迫或欺騙</li>
                </ul>

                <h4>聲明修改與更新</h4>
                <p>本免責聲明的修改程序和生效機制：</p>
                <ol>
                    <li><strong>修改權利：</strong>本工作室保留隨時修改本聲明任何條款的權利</li>
                    <li><strong>重大修改通知：</strong>涉及使用者重要權益的修改將提前30天公告</li>
                    <li><strong>一般修改通知：</strong>文字調整、格式優化等一般修改將提前7天公告</li>
                    <li><strong>公告管道：</strong>修改通知將透過官網、Discord等管道發布</li>
                    <li><strong>生效時間：</strong>修改後的聲明自公告指定日期起生效</li>
                    <li><strong>同意推定：</strong>繼續使用服務視為同意修改後的條款</li>
                    <li><strong>異議處理：</strong>不同意修改者可在生效前停止使用服務</li>
                </ol>

                <h4>條款效力與法律地位</h4>
                <div class="important-box">
                    <div class="box-title">
                        <i class="fas fa-gavel"></i>
                        法律約束力確認
                    </div>
                    <div class="box-content">
                        本免責聲明構成使用者與Scrilab之間具有完全法律約束力的協議，與正式書面合約具有同等法律效力。任何口頭承諾或非正式溝通均不能修改本聲明的內容。
                    </div>
                </div>

                <h4>條款分離與完整性</h4>
                <p>關於本聲明的完整性和可執行性：</p>
                <ul>
                    <li><strong>條款分離：</strong>如任何條款被法院認定無效，該條款將被分離，但不影響其他條款效力</li>
                    <li><strong>替代條款：</strong>無效條款將由最接近原意且合法有效的條款替代</li>
                    <li><strong>完整協議：</strong>本聲明構成雙方就服務使用達成的完整協議</li>
                    <li><strong>補充說明：</strong>本聲明未盡事宜，雙方可另行協商補充</li>
                </ul>

                <h4>特別風險提醒</h4>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        最後風險提醒
                    </div>
                    <div class="box-content">
                        <strong>請再次確認：</strong>使用任何第三方輔助軟體都存在不可預測的風險<br>
                        <strong>理性決策：</strong>請根據個人風險承受能力做出理性決定<br>
                        <strong>學習優先：</strong>建議優先將軟體用於技術學習和研究目的<br>
                        <strong>法律遵循：</strong>請始終遵守當地法律法規和相關服務條款<br>
                        <strong>自我保護：</strong>使用過程中請注意保護個人資訊和帳號安全
                    </div>
                </div>

                <h4>聲明解釋權與聯繫方式</h4>
                <p>本免責聲明的最終解釋權歸Scrilab所有。在法律允許的範圍內，本工作室對聲明內容的解釋為最終解釋。如對本聲明有任何疑問或需要澄清，請透過以下方式聯繫我們：</p>
                <ul>
                    <li><strong>一般服務問題：</strong>Discord社群 (https://discord.gg/nmMmm9gZDC)</li>
                    <li><strong>官方網站：</strong>https://scrilab.com</li>
                </ul>
            </div>
        </section>

        <!-- 聯繫資訊 -->
        <div class="contact-section">
            <h3>有問題嗎？聯繫我們</h3>
            <p>如果您對免責聲明有任何疑問，歡迎隨時聯繫我們的客服團隊</p>
            <div class="contact-methods">
                <a href="https://discord.gg/nmMmm9gZDC" target="_blank" class="contact-link">
                    <i class="fab fa-discord"></i>
                    <span>Discord 社群</span>
                </a>
            </div>
            <div class="contact-footer">
                <p>
                    <strong>最後更新：</strong>2025年7月29日 | 
                    <strong>版本：</strong>v3.1 | 
                    <strong>適用範圍：</strong>所有 Scrilab 服務
                </p>
            </div>
        </div>
    </div>

    <script>
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

        // Smooth scrolling for anchor links
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
    </script>
</body>
</html>
"""

# 路由定義
@disclaimer_bp.route('', methods=['GET'])
def disclaimer_home():
    """免責聲明主頁"""
    return render_template_string(DISCLAIMER_TEMPLATE)

@disclaimer_bp.route('/terms', methods=['GET'])
def terms_of_service():
    """服務條款頁面（重定向到免責聲明）"""
    return render_template_string(DISCLAIMER_TEMPLATE)

@disclaimer_bp.route('/privacy', methods=['GET'])
def privacy_policy():
    """隱私政策頁面（重定向到免責聲明）"""
    return render_template_string(DISCLAIMER_TEMPLATE)

# 確保正確導出
__all__ = ['disclaimer_bp']
