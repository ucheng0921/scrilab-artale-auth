"""
disclaimer_routes.py - 免責聲明路由處理
"""
from flask import Blueprint, render_template_string

# 創建免責聲明藍圖 - 移到文件開頭
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

        /* Contact section */
        .contact-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            text-align: center;
            margin-top: 3rem;
        }

        .contact-methods {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }

        .contact-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 1rem;
            transition: var(--transition);
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
        }

        .contact-link:hover {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
            transform: translateY(-2px);
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
            <span class="last-updated">最後更新：2025年1月</span>
        </div>

        <!-- 服務性質說明 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-info-circle"></i>
                </div>
                軟體性質與技術說明
            </h2>
            <div class="section-content">
                <div class="important-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        重要聲明
                    </div>
                    <div class="box-content">
                        本服務所提供之軟體程式為「人工智慧娛樂性輔助軟體」，非傳統意義上的外掛程式。
                    </div>
                </div>

                <h4>軟體技術原理</h4>
                <p>本網站 (scrilab.com) 所提供、銷售之軟體程式，其實現原理包括但不限於：</p>
                <ul>
                    <li><strong>圖像AI識別技術：</strong>透過電腦視覺技術識別遊戲畫面元素</li>
                    <li><strong>內存讀取：</strong>僅讀取電腦記憶體中的公開資料，不進行修改</li>
                    <li><strong>模擬操作：</strong>透過CPU、GPU、RAM計算實現按鍵腳本精靈般的操作</li>
                    <li><strong>繪製線圈：</strong>在本地電腦上繪製輔助線圈，不修改遊戲資料</li>
                    <li><strong>系統權限利用：</strong>可能利用作業系統或遊戲軟體本身的漏洞實現功能</li>
                </ul>

                <h4>非侵入性聲明</h4>
                <p>本軟體的所有操作均在使用者的PC電腦上執行，具有以下特性：</p>
                <ol>
                    <li>不會修改、入侵或攻擊遊戲伺服器</li>
                    <li>不會篡改遊戲核心數據或資料庫</li>
                    <li>不會進行網路攻擊或惡意行為</li>
                    <li>僅在本地環境中提供輔助功能</li>
                </ol>

                <h4>術語澄清</h4>
                <p>本網站所稱之「外掛」並非傳統意義上的外掛程式，而是「輔助軟體」的另一種稱呼。本軟體屬於輔助性工具，並非非法行為的軟體。</p>

                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        風險提醒
                    </div>
                    <div class="box-content">
                        儘管本軟體採用非侵入性技術，但任何第三方輔助軟體都可能違反遊戲公司的服務條款。使用前請仔細評估風險。
                    </div>
                </div>
            </div>
        </section>

        <!-- 使用風險與責任 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-shield-alt"></i>
                </div>
                使用風險與責任承擔
            </h2>
            <div class="section-content">
                <h4>帳號風險聲明</h4>
                <p>全世界任何輔助軟體，但凡有可能被遊戲公司檢測到，皆有可能違反遊戲公司相關條款規章。使用者需明確了解：</p>
                <ul>
                    <li>使用任何第三方輔助軟體都存在帳號被封禁的風險</li>
                    <li>遊戲公司有權根據其服務條款對使用者進行處罰</li>
                    <li>不同遊戲對輔助軟體的容忍度不同</li>
                    <li>檢測技術會隨時間發展而變化</li>
                </ul>

                <h4>使用者責任</h4>
                <p>若您選擇使用本軟體，即表示您：</p>
                <ol>
                    <li><strong>完全理解風險：</strong>明確了解使用第三方輔助軟體的所有風險</li>
                    <li><strong>自行承擔後果：</strong>因使用本軟體導致的帳號損失或法律爭議，請自行承擔</li>
                    <li><strong>購買即同意：</strong>購買本軟體即表示同意承擔帳號被封禁之風險</li>
                    <li><strong>遵守使用規範：</strong>不得利用軟體功能進行侮辱、暴力、霸凌、詐欺等行為</li>
                </ol>

                <h4>建議使用方式</h4>
                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        學習目的使用建議
                    </div>
                    <div class="box-content">
                        建議使用者將本軟體視為學習計算機技術的參考工具，建議在使用後24小時內刪除，僅供研究和學習用途。
                    </div>
                </div>

                <h4>行為規範</h4>
                <p>使用者承諾不得利用本軟體的功能或便利性，進行以下行為：</p>
                <ul>
                    <li>對他人進行侮辱、暴力、霸凌行為</li>
                    <li>進行詐欺或其他非法活動</li>
                    <li>對他人造成損害或困擾</li>
                    <li>違反當地法律法規的行為</li>
                </ul>
                <p>若因此產生糾紛，本公司有權不經催告逕行終止合約及服務。</p>
            </div>
        </section>

        <!-- 服務條款與限制 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-file-contract"></i>
                </div>
                服務條款與使用限制
            </h2>
            <div class="section-content">
                <h4>軟體更新與維護</h4>
                <p>本軟體可能因以下情況需要更新或維護：</p>
                <ul>
                    <li><strong>遊戲更新：</strong>目標遊戲版本更新導致功能失效</li>
                    <li><strong>系統維護：</strong>遊戲官方進行系統維護或修復</li>
                    <li><strong>針對性阻擋：</strong>遊戲公司加強反作弊檢測</li>
                    <li><strong>技術升級：</strong>為提升功能穩定性進行技術改進</li>
                </ul>
                <p>上述情況可能導致軟體暫時無法使用，更新處理需要時間，本公司將不另行補償服務中斷期間的損失。</p>

                <h4>數位內容特性</h4>
                <p>根據消費者保護法第十九條第二項規定：</p>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        退款政策
                    </div>
                    <div class="box-content">
                        本服務為數位內容或一經提供即為完成之線上服務，不適用七天鑑賞期，售後不提供退貨服務，不予以退費。
                    </div>
                </div>

                <h4>定價與交易</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>情況</th>
                            <th>處理方式</th>
                            <th>說明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>價格BUG</td>
                            <td>封禁處理</td>
                            <td>利用價格錯誤購買，有權封禁卡號或帳號</td>
                        </tr>
                        <tr>
                            <td>騙卡行為</td>
                            <td>封卡封端</td>
                            <td>使用後不付錢、詐騙等行為</td>
                        </tr>
                        <tr>
                            <td>漏洞利用</td>
                            <td>封禁停權</td>
                            <td>利用系統漏洞進行非法購買</td>
                        </tr>
                        <tr>
                            <td>正常購買</td>
                            <td>正常服務</td>
                            <td>按照正常流程購買並付款</td>
                        </tr>
                    </tbody>
                </table>

                <h4>服務終止條件</h4>
                <p>以下情況本公司有權終止服務：</p>
                <ol>
                    <li>違反本免責聲明或服務條款</li>
                    <li>進行詐欺、騙卡或其他非法行為</li>
                    <li>利用系統漏洞進行非法操作</li>
                    <li>對他人造成傷害或損失</li>
                    <li>長期未使用服務（超過一年）</li>
                </ol>
            </div>
        </section>

        <!-- 法律責任與免責 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-balance-scale"></i>
                </div>
                法律責任與免責條款
            </h2>
            <div class="section-content">
                <h4>責任範圍限制</h4>
                <p>在法律允許的最大範圍內，Scrilab 及其關聯方對以下情況不承擔任何責任：</p>
                <ul>
                    <li><strong>帳號處罰：</strong>因使用本軟體導致的遊戲帳號被暫停、封鎖或其他處罰</li>
                    <li><strong>資料損失：</strong>遊戲角色、物品、等級或其他虛擬資產的損失</li>
                    <li><strong>經濟損失：</strong>因服務中斷、帳號封禁等導致的經濟損失</li>
                    <li><strong>法律糾紛：</strong>因使用本軟體而產生的任何法律爭議或訴訟</li>
                    <li><strong>間接損害：</strong>任何間接、偶然、特殊或後果性損害</li>
                </ul>

                <h4>使用者同意聲明</h4>
                <p>使用者在試用及購買時即視為：</p>
                <ol>
                    <li>已詳細閱讀並完全理解本免責聲明內容</li>
                    <li>明確知曉使用輔助軟體的所有風險</li>
                    <li>願意承擔使用過程中的所有責任和後果</li>
                    <li>同意本免責聲明與服務利用規約的全部內容</li>
                </ol>

                <h4>適用法律</h4>
                <p>本免責聲明適用中華民國（台灣）法律。如發生爭議，雙方應優先透過友好協商解決。協商不成的，任何一方均可向台北地方法院提起訴訟。</p>

                <div class="important-box">
                    <div class="box-title">
                        <i class="fas fa-gavel"></i>
                        最終解釋權
                    </div>
                    <div class="box-content">
                        本免責聲明的最終解釋權歸 Scrilab 所有。如有部分條款被認定無效，不影響其他條款的效力。
                    </div>
                </div>
            </div>
        </section>

        <!-- 隱私權與資料保護 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-user-shield"></i>
                </div>
                隱私權政策與資料保護
            </h2>
            <div class="section-content">
                <h4>資料收集範圍</h4>
                <p>為提供服務，我們可能收集以下資訊：</p>
                <ul>
                    <li><strong>帳號資訊：</strong>使用者序號、顯示名稱、服務期限</li>
                    <li><strong>聯絡資訊：</strong>Email地址、電話號碼（選填）</li>
                    <li><strong>使用記錄：</strong>登入時間、使用頻率、功能使用情況</li>
                    <li><strong>技術資訊：</strong>IP位址、設備資訊、系統版本</li>
                    <li><strong>付款資訊：</strong>透過第三方支付平台處理的交易記錄</li>
                </ul>

                <h4>資料使用目的</h4>
                <p>收集的資訊僅用於以下目的：</p>
                <ol>
                    <li>提供和維護軟體服務</li>
                    <li>驗證使用者身份和授權</li>
                    <li>處理付款和開通服務</li>
                    <li>提供技術支援服務</li>
                    <li>改善服務品質和使用者體驗</li>
                    <li>防範詐欺和濫用行為</li>
                </ol>

                <h4>資料保護措施</h4>
                <p>我們採取以下措施保護使用者資料：</p>
                <ul>
                    <li>使用加密技術保護敏感資料</li>
                    <li>限制員工對資料的存取權限</li>
                    <li>定期進行安全性檢查和更新</li>
                    <li>不會將個人資料出售給第三方</li>
                </ul>

                <h4>資料保留期限</h4>
                <p>使用者資料的保留期限如下：</p>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>資料類型</th>
                            <th>保留期限</th>
                            <th>說明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>帳號資訊</td>
                            <td>服務期滿後30天</td>
                            <td>用於處理可能的售後問題</td>
                        </tr>
                        <tr>
                            <td>使用記錄</td>
                            <td>服務期滿後90天</td>
                            <td>用於統計分析和服務改進</td>
                        </tr>
                        <tr>
                            <td>付款記錄</td>
                            <td>5年</td>
                            <td>符合稅務和會計法規要求</td>
                        </tr>
                        <tr>
                            <td>技術日誌</td>
                            <td>6個月</td>
                            <td>用於故障排除和安全監控</td>
                        </tr>
                    </tbody>
                </table>

                <h4>隱私權政策修訂</h4>
                <p>本公司保留隨時修改隱私權政策的權利。當政策發生修改時：</p>
                <ol>
                    <li>將在官方網站顯著位置公告</li>
                    <li>透過Email通知現有使用者</li>
                    <li>在Discord社群發布更新通知</li>
                    <li>修改後的政策自公告日起生效</li>
                </ol>
            </div>
        </section>

        <!-- 技術支援與客服 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-headset"></i>
                </div>
                技術支援與客戶服務
            </h2>
            <div class="section-content">
                <h4>服務範圍</h4>
                <p>我們提供以下技術支援服務：</p>
                <ul>
                    <li><strong>軟體安裝指導：</strong>協助使用者正確安裝和配置軟體</li>
                    <li><strong>使用教學：</strong>提供詳細的操作說明和使用技巧</li>
                    <li><strong>故障排除：</strong>協助解決軟體運行中的技術問題</li>
                    <li><strong>帳號問題：</strong>處理序號驗證、登入等帳號相關問題</li>
                    <li><strong>更新通知：</strong>及時通知軟體更新和維護資訊</li>
                </ul>

                <h4>支援管道</h4>
                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        主要聯繫方式
                    </div>
                    <div class="box-content">
                        <strong>Discord社群：</strong>https://discord.gg/HPzNrQmN（推薦，回應最快）<br>
                        <strong>Email客服：</strong>pink870921aa@gmail.com（24小時內回覆）<br>
                        <strong>操作手冊：</strong>/manual（詳細使用說明）
                    </div>
                </div>

                <h4>服務時間</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>支援管道</th>
                            <th>服務時間</th>
                            <th>回應時間</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Discord即時客服</td>
                            <td>每日 09:00 - 23:00</td>
                            <td>通常5分鐘內回應</td>
                        </tr>
                        <tr>
                            <td>Email客服</td>
                            <td>24小時接收</td>
                            <td>24小時內回覆</td>
                        </tr>
                        <tr>
                            <td>操作手冊</td>
                            <td>24小時開放</td>
                            <td>即時查閱</td>
                        </tr>
                    </tbody>
                </table>

                <h4>支援限制</h4>
                <p>以下情況可能無法提供技術支援：</p>
                <ul>
                    <li>因違反遊戲條款導致的帳號封禁</li>
                    <li>使用者自行修改軟體導致的問題</li>
                    <li>與本軟體無關的電腦或遊戲問題</li>
                    <li>已超過服務期限的過期帳號</li>
                </ul>
            </div>
        </section>

        <!-- 服務變更與終止 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-sync-alt"></i>
                </div>
                服務變更與終止條款
            </h2>
            <div class="section-content">
                <h4>服務變更權利</h4>
                <p>本公司保留隨時修改、暫停或終止服務的權利，原因包括但不限於：</p>
                <ul>
                    <li><strong>技術升級：</strong>為提升服務品質進行技術改進</li>
                    <li><strong>法規遵循：</strong>配合法律法規變化調整服務內容</li>
                    <li><strong>商業決策：</strong>基於商業策略考量調整服務方向</li>
                    <li><strong>不可抗力：</strong>因天災、戰爭、政策等不可抗力因素</li>
                    <li><strong>安全考量：</strong>為保護使用者安全暫停或調整服務</li>
                </ul>

                <h4>變更通知機制</h4>
                <p>重大服務變更將透過以下方式通知使用者：</p>
                <ol>
                    <li><strong>官網公告：</strong>在網站首頁發布重要通知</li>
                    <li><strong>Email通知：</strong>向註冊使用者發送變更通知</li>
                    <li><strong>Discord公告：</strong>在官方Discord社群置頂公告</li>
                    <li><strong>軟體內通知：</strong>透過軟體彈窗或通知功能告知</li>
                </ol>

                <h4>服務終止情況</h4>
                <p>以下情況可能導致服務終止：</p>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        終止條件
                    </div>
                    <div class="box-content">
                        <strong>使用者行為：</strong>違反服務條款、進行詐欺或騙卡行為<br>
                        <strong>技術原因：</strong>目標遊戲重大更新導致技術無法實現<br>
                        <strong>法律要求：</strong>接到主管機關或法院的停止服務要求<br>
                        <strong>商業考量：</strong>基於成本效益考量停止特定服務
                    </div>
                </div>

                <h4>終止後處理</h4>
                <p>服務終止後的處理方式：</p>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>終止原因</th>
                            <th>退款政策</th>
                            <th>資料處理</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>使用者違規</td>
                            <td>不予退款</td>
                            <td>立即刪除帳號資料</td>
                        </tr>
                        <tr>
                            <td>技術無法實現</td>
                            <td>按剩餘時間比例退款</td>
                            <td>保留30天後刪除</td>
                        </tr>
                        <tr>
                            <td>法律要求</td>
                            <td>依法律規定處理</td>
                            <td>依法律規定處理</td>
                        </tr>
                        <tr>
                            <td>商業決策</td>
                            <td>提前30天通知，可申請退款</td>
                            <td>保留90天後刪除</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>示的保證，包括但不限於：</p>
                <ul>
                    <li>服務的可用性、穩定性或持續性</li>
                    <li>服務結果的準確性或可靠性</li>
                    <li>服務不會被中斷或出現錯誤</li>
                    <li>服務滿足使用者的特定需求</li>
                </ul>

                <h4>付款與退款</h4>
                <table class="content-table">
                    <thead>
                        <tr>
                            <th>情況</th>
                            <th>退款政策</th>
                            <th>說明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>技術故障</td>
                            <td>可申請退款</td>
                            <td>服務端技術問題導致無法使用</td>
                        </tr>
                        <tr>
                            <td>使用者原因</td>
                            <td>不予退款</td>
                            <td>設定錯誤、操作不當等</td>
                        </tr>
                        <tr>
                            <td>帳號封鎖</td>
                            <td>不予退款</td>
                            <td>第三方遊戲處罰措施</td>
                        </tr>
                        <tr>
                            <td>服務變更</td>
                            <td>按比例退款</td>
                            <td>服務內容重大變更</td>
                        </tr>
                    </tbody>
                </table>

                <h4>知識產權</h4>
                <p>本服務涉及的所有技術內容、文檔、代碼等均受知識產權法保護。使用者僅獲得有限的使用授權，不得：</p>
                <ul>
                    <li>逆向工程、反編譯或反彙編</li>
                    <li>複製、分發或轉售服務內容</li>
                    <li>移除或修改任何版權聲明</li>
                    <li>用於商業目的或盈利活動</li>
                </ul>
            </div>
        </section>

        <!-- 隱私與數據 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-shield-alt"></i>
                </div>
                隱私與數據保護
            </h2>
            <div class="section-content">
                <h4>數據收集</h4>
                <p>為提供服務，我們可能收集以下資訊：</p>
                <ul>
                    <li>帳號註冊資訊（序號、顯示名稱）</li>
                    <li>使用記錄（登入時間、使用頻率）</li>
                    <li>技術資訊（IP 地址、設備資訊）</li>
                    <li>付款資訊（透過第三方支付平台）</li>
                </ul>

                <h4>數據使用</h4>
                <p>收集的資訊僅用於：</p>
                <ol>
                    <li>提供和維護服務</li>
                    <li>驗證使用者身份</li>
                    <li>改善服務品質</li>
                    <li>處理技術支援請求</li>
                </ol>

                <h4>數據保護</h4>
                <p>我們採取合理的技術和管理措施保護使用者資訊，但無法保證絕對安全。使用者應：</p>
                <ul>
                    <li>妥善保管序號和登入資訊</li>
                    <li>不與他人分享帳號</li>
                    <li>發現異常時立即聯繫客服</li>
                </ul>

                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-info-circle"></i>
                        數據保留
                    </div>
                    <div class="box-content">
                        使用者資料將在服務期滿後保留 30 天，之後將被安全刪除。
                    </div>
                </div>
            </div>
        </section>

        <!-- 服務變更與終止 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-sync-alt"></i>
                </div>
                服務變更與終止
            </h2>
            <div class="section-content">
                <h4>服務變更</h4>
                <p>我們保留隨時修改、暫停或終止服務的權利，包括但不限於：</p>
                <ul>
                    <li>技術升級或維護</li>
                    <li>法律法規要求</li>
                    <li>商業策略調整</li>
                    <li>不可抗力因素</li>
                </ul>

                <h4>提前通知</h4>
                <p>重大服務變更我們將提前通知使用者：</p>
                <ol>
                    <li>透過 Email 發送通知</li>
                    <li>在 Discord 社群公告</li>
                    <li>官方網站發布聲明</li>
                    <li>應用內推播訊息</li>
                </ol>

                <h4>帳號終止</h4>
                <p>在以下情況下，我們可能終止使用者帳號：</p>
                <ul>
                    <li>違反服務條款</li>
                    <li>從事非法或不當行為</li>
                    <li>長期未使用（超過1年）</li>
                    <li>惡意攻擊服務系統</li>
                </ul>
            </div>
        </section>

        <!-- 爭議解決 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-handshake"></i>
                </div>
                爭議解決
            </h2>
            <div class="section-content">
                <h4>適用法律</h4>
                <p>本免責聲明及服務條款適用中華民國（台灣）法律。</p>

                <h4>爭議處理</h4>
                <p>如發生爭議，雙方應優先透過友好協商解決。協商不成的，任何一方均可向台北地方法院提起訴訟。</p>

                <h4>聯繫方式</h4>
                <p>如對本聲明有任何疑問，請透過以下方式聯繫我們：</p>
                <ul>
                    <li>技術支援：Discord 社群</li>
                    <li>商務洽詢：pink870921aa@gmail.com</li>
                    <li>法律事務：請透過 Email 聯繫</li>
                </ul>

                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        最終解釋權
                    </div>
                    <div class="box-content">
                        本免責聲明的最終解釋權歸 Scrilab 所有。如有部分條款被認定無效，不影響其他條款的效力。
                    </div>
                </div>
            </div>
        </section>

        <!-- 最終聲明 -->
        <section class="disclaimer-section">
            <h2 class="section-title">
                <div class="section-icon">
                    <i class="fas fa-certificate"></i>
                </div>
                最終聲明與生效條款
            </h2>
            <div class="section-content">
                <h4>聲明生效</h4>
                <p>本免責聲明自使用者進行以下任一行為時即生效：</p>
                <ol>
                    <li><strong>瀏覽本網站：</strong>訪問 scrilab.com 任何頁面</li>
                    <li><strong>試用服務：</strong>下載或使用任何試用版本</li>
                    <li><strong>購買服務：</strong>完成付款購買任何服務方案</li>
                    <li><strong>使用軟體：</strong>安裝、配置或運行本軟體</li>
                </ol>

                <h4>完整理解確認</h4>
                <p>使用者確認並承諾已經：</p>
                <ul>
                    <li>詳細閱讀並完全理解本免責聲明的全部內容</li>
                    <li>明確知曉使用輔助軟體可能面臨的所有風險</li>
                    <li>理解本軟體的技術原理和運作方式</li>
                    <li>同意承擔使用過程中的全部責任和後果</li>
                    <li>願意遵守所有服務條款和使用規範</li>
                </ul>

                <h4>條款修改</h4>
                <p>本免責聲明的修改程序如下：</p>
                <ol>
                    <li>本公司保留隨時修改本聲明的權利</li>
                    <li>重大修改將提前30天在官網公告</li>
                    <li>修改後的聲明自公告日起生效</li>
                    <li>繼續使用服務視為同意修改後的條款</li>
                </ol>

                <h4>效力與執行</h4>
                <div class="important-box">
                    <div class="box-title">
                        <i class="fas fa-gavel"></i>
                        法律效力
                    </div>
                    <div class="box-content">
                        本免責聲明構成使用者與 Scrilab 之間具有法律約束力的協議。如有任何條款被認定無效或不可執行，其餘條款仍然有效。
                    </div>
                </div>

                <h4>特別提醒</h4>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        重要提醒
                    </div>
                    <div class="box-content">
                        <strong>風險自負：</strong>使用任何第三方輔助軟體都存在風險，請謹慎評估<br>
                        <strong>學習目的：</strong>建議將軟體用於技術學習和研究目的<br>
                        <strong>遵守法律：</strong>請遵守當地法律法規和遊戲公司條款<br>
                        <strong>理性使用：</strong>請根據自身情況理性選擇是否使用
                    </div>
                </div>

                <h4>最終解釋權</h4>
                <p>本免責聲明的最終解釋權歸 Scrilab 所有。在法律允許的範圍內，本公司對本聲明的解釋為最終解釋。</p>
            </div>
        </section>

        <!-- 聯繫資訊 -->
        <div class="contact-section">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">有問題嗎？聯繫我們</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">如果您對免責聲明有任何疑問，歡迎隨時聯繫我們的客服團隊</p>
            <div class="contact-methods">
                <a href="https://discord.gg/HPzNrQmN" target="_blank" class="contact-link">
                    <i class="fab fa-discord"></i>
                    <span>Discord 社群</span>
                </a>
                <a href="mailto:pink870921aa@gmail.com" class="contact-link">
                    <i class="fas fa-envelope"></i>
                    <span>Email 客服</span>
                </a>
                <a href="/manual" class="contact-link">
                    <i class="fas fa-book"></i>
                    <span>操作手冊</span>
                </a>
            </div>
            <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color);">
                <p style="color: var(--text-muted); font-size: 0.9rem;">
                    <strong>最後更新：</strong>2025年1月 | 
                    <strong>版本：</strong>v2.0 | 
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