# 專業軟體服務頁面 HTML 模板 - 修復版本，恢復打字機特效和遊戲圖片
PROFESSIONAL_PRODUCTS_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scrilab - Python 遊戲技術服務</title>
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
            --bg-tertiary: #2a2a2a;
            --bg-card: #1e1e1e;
            --bg-hover: #333333;
            
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-muted: #808080;
            
            --accent-blue: #00d4ff;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            
            --border-color: #333333;
            --border-hover: #555555;
            
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-accent: linear-gradient(135deg, #00d4ff 0%, #8b5cf6 100%);
            --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 25px rgba(0, 0, 0, 0.25);
            --shadow-lg: 0 15px 35px rgba(0, 0, 0, 0.35);
            --shadow-glow: 0 0 30px rgba(0, 212, 255, 0.3);
            
            --border-radius: 16px;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
        }

        /* 恢復打字機代碼背景特效 CSS */
        @keyframes typewriter {
            0% { width: 0; }
            90% { width: 100%; }
            100% { width: 100%; }
        }

        @keyframes blink-cursor {
            0%, 50% { border-right: 2px solid #00d4ff; }
            51%, 100% { border-right: 2px solid transparent; }
        }

        @keyframes fade-out {
            0% { opacity: 0.15; }
            70% { opacity: 0.15; }
            100% { opacity: 0; }
        }

        /* 增強版背景動效 */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 1;
        }

        .bg-animation::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(16, 185, 129, 0.04) 0%, transparent 50%),
                linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.02) 50%, transparent 70%);
            animation: float 20s ease-in-out infinite;
        }

        .bg-animation::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                conic-gradient(from 0deg at 70% 30%, transparent, rgba(139, 92, 246, 0.03), transparent),
                conic-gradient(from 180deg at 30% 70%, transparent, rgba(0, 212, 255, 0.02), transparent);
            animation: rotate 30s linear infinite;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(30px, -30px) rotate(1deg); }
            66% { transform: translate(-20px, 20px) rotate(-1deg); }
        }

        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
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

        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            position: relative;
            background: var(--bg-primary);
            overflow: hidden;
        }

        .hero-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            z-index: 2;
            position: relative;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.2);
            color: var(--accent-blue);
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 2rem;
            animation: slideInUp 1s ease-out;
        }

        .hero h1 {
            font-size: clamp(3rem, 8vw, 5.5rem);
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.1;
            animation: slideInUp 1s ease-out 0.2s both;
        }

        .hero .highlight {
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero p {
            font-size: 1.3rem;
            color: var(--text-secondary);
            margin-bottom: 3rem;
            max-width: 700px;
            line-height: 1.7;
            animation: slideInUp 1s ease-out 0.4s both;
        }

        .hero-buttons {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            animation: slideInUp 1s ease-out 0.6s both;
        }

        .btn-primary {
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
            border: none;
            cursor: pointer;
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-glow);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-primary);
            padding: 1rem 2rem;
            border: 2px solid var(--border-color);
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
        }

        .btn-secondary:hover {
            border-color: var(--accent-blue);
            color: var(--accent-blue);
            transform: translateY(-3px);
        }

        /* Games Section */
        .games {
            padding: 8rem 2rem;
            background: var(--bg-secondary);
            position: relative;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .section-header {
            text-align: center;
            margin-bottom: 5rem;
        }

        .section-badge {
            display: inline-block;
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.2);
            color: var(--accent-purple);
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
        }

        .section-description {
            font-size: 1.2rem;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.7;
        }

        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 3rem;
            margin-top: 4rem;
        }

        .game-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            overflow: hidden;
            transition: var(--transition);
            cursor: pointer;
            position: relative;
        }

        .game-card.active:hover {
            transform: translateY(-5px);
            border-color: var(--accent-blue);
            box-shadow: var(--shadow-lg);
        }

        .game-card.coming-soon {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .game-image {
            position: relative;
            width: 100%;
            height: 200px;
            overflow: hidden;
            background: var(--bg-tertiary);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .game-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: var(--transition);
        }

        .game-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: var(--transition);
        }

        .game-card.active:hover .game-overlay {
            opacity: 1;
        }

        .game-overlay i {
            font-size: 2.5rem;
            color: var(--accent-blue);
        }

        .game-info {
            padding: 2rem;
        }

        .game-info h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .game-subtitle {
            color: var(--accent-blue);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }

        .game-description {
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        .game-status {
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            align-items: center;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .status-badge.active {
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-badge.coming {
            background: rgba(245, 158, 11, 0.1);
            color: var(--accent-orange);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .manual-btn {
            background: var(--gradient-accent);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }

        .manual-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        }

        /* Services Section */
        .services {
            padding: 8rem 2rem;
            background: var(--bg-primary);
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 3rem;
            margin-top: 5rem;
        }

        .service-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            overflow: hidden;
            transition: var(--transition);
            position: relative;
        }

        .service-card:hover {
            transform: translateY(-5px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-lg);
        }

        .service-header {
            padding: 2.5rem 2rem 1.5rem;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border-color);
            position: relative;
        }

        .popular-badge {
            position: absolute;
            top: -12px;
            right: 2rem;
            background: var(--gradient-accent);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            box-shadow: var(--shadow-md);
        }

        .service-title {
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .service-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .service-price {
            font-size: 2.8rem;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .service-price .currency {
            font-size: 1.2rem;
            vertical-align: top;
        }

        .service-price .period {
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 400;
        }

        .crypto-info {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 8px;
            padding: 0.8rem;
            margin: 1rem 0;
            font-size: 0.9rem;
            color: var(--accent-blue);
        }

        .service-body {
            padding: 2rem;
        }

        .service-features {
            list-style: none;
            margin-bottom: 2.5rem;
        }

        .service-features li {
            padding: 0.8rem 0;
            display: flex;
            align-items: flex-start;
            gap: 0.8rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .service-features li:last-child {
            border-bottom: none;
        }

        .feature-check {
            color: var(--accent-green);
            font-size: 1.1rem;
            margin-top: 0.1rem;
            flex-shrink: 0;
        }

        .service-button {
            width: 100%;
            padding: 1rem;
            background: var(--gradient-accent);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .service-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        /* Footer */
        .footer {
            background: var(--bg-primary);
            border-top: 1px solid var(--border-color);
            padding: 4rem 2rem 2rem;
        }

        .footer-simple {
            text-align: center;
            margin-bottom: 3rem;
        }

        .contact-methods {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 3rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .discord-link, .email-link {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 1.1rem;
            transition: var(--transition);
            padding: 0.8rem 1.5rem;
            border-radius: 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
        }

        .discord-link:hover {
            color: #5865F2;
            border-color: #5865F2;
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(88, 101, 242, 0.3);
        }

        .email-link:hover {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
        }

        /* Purchase Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(10px);
        }

        .modal-content {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            max-width: 500px;
            width: 90%;
            padding: 2.5rem;
            text-align: center;
            position: relative;
            animation: modalSlideIn 0.4s ease-out;
        }

        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: scale(0.8) translateY(-50px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        .modal-close {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            transition: var(--transition);
        }

        .modal-close:hover {
            color: var(--text-primary);
        }

        .plan-info {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }

        .crypto-notice {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
            color: var(--accent-blue);
        }

        .form-group {
            margin: 1.5rem 0;
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

        .modal-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
        }

        .btn-cancel {
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: var(--transition);
        }

        .btn-cancel:hover {
            color: var(--text-primary);
            border-color: var(--border-hover);
        }

        .loading {
            display: inline-block;
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

        /* Responsive Design */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }

            .hero h1 {
                font-size: 2.5rem;
            }

            .hero-buttons {
                flex-direction: column;
                align-items: flex-start;
            }

            .games-grid,
            .services-grid {
                grid-template-columns: 1fr;
            }

            .section-title {
                font-size: 2.2rem;
            }

            .contact-methods {
                flex-direction: column;
                gap: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>

    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="#home" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-code"></i>
                </div>
                <span>Scrilab</span>
            </a>
            <ul class="nav-links">
                <li><a href="#home">首頁</a></li>
                <li><a href="#games">遊戲服務</a></li>
                <li><a href="#contact">聯絡我們</a></li>
                <li><a href="/disclaimer">免責聲明</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="hero-content">
            <div class="hero-badge">
                <i class="fab fa-bitcoin"></i>
                <span>支援加密貨幣付款</span>
            </div>
            <h1>自動化<span class="highlight">遊戲技術服務</span><br>與個人化解決方案</h1>
            <p>Scrilab 為遊戲愛好者提供專業的遊戲技術服務，現已支援加密貨幣付款！透過我們的技術團隊為您量身打造個人化的遊戲效率提升方案。我們專注於為客戶提供安全、穩定的遊戲體驗優化服務。</p>
            <div class="hero-buttons">
                <a href="#games" class="btn-primary">
                    <i class="fas fa-gamepad"></i>
                    <span>瀏覽遊戲服務</span>
                </a>
                <a href="#contact" class="btn-secondary">
                    <i class="fas fa-book"></i>
                    <span>聯絡我們</span>
                </a>
            </div>
        </div>
    </section>

    <!-- Games Section -->
    <section id="games" class="games">
        <div class="container">
            <div class="section-header">
                <div class="section-badge">遊戲服務</div>
                <h2 class="section-title">選擇您的遊戲</h2>
                <p class="section-description">選擇適合您的服務方案，享受最佳遊戲體驗，現已支援加密貨幣付款</p>
            </div>
            
            <div class="games-grid">
                <!-- MapleStory Worlds - Artale -->
                <div class="game-card active" onclick="showGamePlans('artale')">
                    <div class="game-info">
                        <h3>MapleStory Worlds - Artale</h3>
                        <p class="game-subtitle">繁體中文版 | 支援加密貨幣</p>
                        <p class="game-description">專為 Artale 玩家打造的自動化遊戲方案，現已支援 USDT 等加密貨幣付款</p>
                        <div class="game-status">
                            <span class="status-badge active">服務中</span>
                            <div class="game-buttons">
                                <a href="/intro" class="manual-btn intro-btn">
                                    <i class="fas fa-info-circle"></i>
                                    基本介紹
                                </a>
                                <a href="/manual" class="manual-btn">
                                    <i class="fas fa-book"></i>
                                    操作手冊
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Coming Soon Games -->
                <div class="game-card coming-soon">
                    <div class="game-image">
                        <img src="/static/images/coming-soon.jpg" alt="Coming Soon Games" style="width: 100%; height: 100%; object-fit: cover;">
                        <div class="game-overlay">
                            <i class="fas fa-clock"></i>
                        </div>
                    </div>
                    <div class="game-info">
                        <h3>更多遊戲</h3>
                        <p class="game-subtitle">即將推出</p>
                        <p class="game-description">我們正在開發更多遊戲的優化解決方案，敬請期待</p>
                        <div class="game-status">
                            <span class="status-badge coming">開發中</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section id="services" class="services" style="display: none;">
        <div class="container">
            <div class="section-header">
                <button class="btn-secondary" onclick="backToGames()" style="margin-bottom: 2rem;">
                    <i class="fas fa-arrow-left"></i>
                    <span>返回遊戲列表</span>
                </button>
                <div class="section-badge">服務方案</div>
                <h2 class="section-title" id="game-plans-title">MapleStory Worlds - Artale 專屬方案</h2>
                <p class="section-description">一次購買越久享受更優惠的價格，所有方案均提供完整的技術服務，現已支援加密貨幣付款</p>
            </div>
            
            <div class="services-grid">
                <!-- 體驗方案 -->
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-title">體驗服務</div>
                        <div class="service-subtitle">適合新手玩家體驗</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>5
                            <span class="period">/7天</span>
                        </div>
                        <div class="crypto-info">
                            <i class="fab fa-bitcoin"></i>
                            <span>約 0.16 USDT | 支援多種加密貨幣</span>
                        </div>
                    </div>
                    <div class="service-body">
                        <ul class="service-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整技術服務功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多線程處理技術</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>視覺識別與截圖分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完全隨機性演算法</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高度自定義設定</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>24/7技術支援</span>
                            </li>
                        </ul>
                        <div class="payment-options">
                            <button class="service-button" onclick="selectPaymentMethod('trial_7', 'smart_pay')" style="margin-bottom: 0.5rem;">
                                <i class="fas fa-credit-card"></i>
                                <span>智能付款（推薦）</span>
                            </button>
                            <button class="service-button" onclick="selectPaymentMethod('trial_7', 'direct_crypto')" style="background: rgba(0, 212, 255, 0.1); color: var(--accent-blue); border: 1px solid var(--accent-blue);">
                                <i class="fab fa-bitcoin"></i>
                                <span>直接加密貨幣</span>
                            </button>
                        </div>                       
                    </div>
                </div>

                <!-- 標準方案 -->
                <div class="service-card">
                    <div class="service-header">
                        <div class="popular-badge">最受歡迎</div>
                        <div class="service-title">標準服務</div>
                        <div class="service-subtitle">最佳性價比選擇</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>599
                            <span class="period">/30天</span>
                        </div>
                        <div class="crypto-info">
                            <i class="fab fa-bitcoin"></i>
                            <span>約 19.17 USDT | 支援多種加密貨幣</span>
                        </div>
                    </div>
                    <div class="service-body">
                        <ul class="service-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整技術服務功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多線程處理技術</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>視覺識別與截圖分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完全隨機性演算法</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高度自定義設定</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>24/7技術支援</span>
                            </li>
                        </ul>
                        <div class="payment-options">
                            <button class="service-button" onclick="selectPaymentMethod('monthly_30', 'smart_pay')" style="margin-bottom: 0.5rem;">
                                <i class="fas fa-credit-card"></i>
                                <span>智能付款（推薦）</span>
                            </button>
                            <button class="service-button" onclick="selectPaymentMethod('monthly_30', 'direct_crypto')" style="background: rgba(0, 212, 255, 0.1); color: var(--accent-blue); border: 1px solid var(--accent-blue);">
                                <i class="fab fa-bitcoin"></i>
                                <span>直接加密貨幣</span>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 季度方案 -->
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-title">季度服務</div>
                        <div class="service-subtitle">長期使用最划算</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>1,499
                            <span class="period">/90天</span>
                        </div>
                        <div class="crypto-info">
                            <i class="fab fa-bitcoin"></i>
                            <span>約 47.97 USDT | 支援多種加密貨幣</span>
                        </div>
                    </div>
                    <div class="service-body">
                        <ul class="service-features">
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完整技術服務功能</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>多線程處理技術</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>視覺識別與截圖分析</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>完全隨機性演算法</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>高度自定義設定</span>
                            </li>
                            <li>
                                <i class="fas fa-check feature-check"></i>
                                <span>24/7技術支援</span>
                            </li>
                        </ul>
                        <div class="payment-options">
                            <button class="service-button" onclick="selectPaymentMethod('quarterly_90', 'smart_pay')" style="margin-bottom: 0.5rem;">
                                <i class="fas fa-credit-card"></i>
                                <span>智能付款（推薦）</span>
                            </button>
                            <button class="service-button" onclick="selectPaymentMethod('quarterly_90', 'direct_crypto')" style="background: rgba(0, 212, 255, 0.1); color: var(--accent-blue); border: 1px solid var(--accent-blue);">
                                <i class="fab fa-bitcoin"></i>
                                <span>直接加密貨幣</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer id="contact" class="footer">
        <div class="container">
            <div class="footer-simple">
                <h3 style="font-size: 1.2rem; margin-bottom: 1.5rem; color: var(--text-primary); font-weight: 600;">聯絡我們</h3>
                <div class="contact-methods">
                    <a href="https://discord.gg/HPzNrQmN" target="_blank" class="discord-link">
                        <i class="fab fa-discord"></i>
                        <span>Discord 技術支援</span>
                    </a>
                    <a href="mailto:scrilabstaff@gmail.com" class="email-link">
                        <i class="fas fa-envelope"></i>
                        <span>scrilabstaff@gmail.com</span>
                    </a>
                </div>
                <p style="color: var(--text-muted); font-size: 0.95rem;">現已支援加密貨幣付款，所有技術支援與客服諮詢，請優先透過 Discord 聯繫我們</p>
            </div>
            <div style="border-top: 1px solid var(--border-color); padding-top: 2rem; text-align: center; color: var(--text-muted);">
                <p style="margin-bottom: 1rem;">
                    <a href="/disclaimer" style="color: var(--text-muted); text-decoration: none; margin-right: 2rem; transition: color 0.3s ease;" onmouseover="this.style.color='var(--accent-blue)'" onmouseout="this.style.color='var(--text-muted)'">免責聲明</a>
                </p>
                <p>&copy; 2025 Scrilab. All rights reserved. Powered by OxaPay.</p>
            </div>
        </div>
    </footer>

    <!-- Purchase Modal -->
    <div id="purchase-modal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">加密貨幣付款</h3>
            <div id="selected-plan-info" class="plan-info">
                <!-- Plan info will be inserted here -->
            </div>
            <div class="crypto-notice">
                <i class="fab fa-bitcoin"></i>
                <span>我們透過 OxaPay 提供安全的加密貨幣付款服務，支援 USDT、Bitcoin 等多種加密貨幣</span>
            </div>
            <div class="form-group">
                <label for="user-name">用戶名稱</label>
                <input type="text" id="user-name" placeholder="請輸入您的用戶名稱(暱稱)" class="form-input" required>
            </div>
            <div class="form-group">
                <label for="contact-email">聯絡信箱</label>
                <input type="email" id="contact-email" placeholder="請輸入用於接收序號的信箱" class="form-input" required>
            </div>
            <div class="form-group">
                <label for="contact-phone">備用信箱（選填）</label>
                <input type="tel" id="contact-phone" placeholder="請輸入備用信箱" class="form-input">
            </div>
            <div class="form-group" style="text-align: left;">
                <label style="display: flex; align-items: flex-start; gap: 0.8rem; cursor: pointer;">
                    <input type="checkbox" id="agree-terms" required style="margin-top: 0.2rem; accent-color: var(--accent-blue);">
                    <span style="font-size: 0.95rem; line-height: 1.5;">
                        我已閱讀並同意 <a href="/disclaimer" target="_blank" style="color: var(--accent-blue); text-decoration: none;">免責聲明與服務條款</a>，
                        理解使用本服務的風險，並自願承擔相關責任。
                    </span>
                </label>
            </div>
            <div class="modal-buttons">
                <button class="btn-cancel" onclick="closeModal()">取消</button>
                <button class="btn-primary" onclick="submitPayment()" id="payment-btn">
                    <span id="payment-btn-text">
                        <i class="fab fa-bitcoin"></i>
                        立即付款
                    </span>
                    <div class="loading" id="payment-loading" style="display: none;"></div>
                </button>
            </div>
        </div>
    </div>

    <script>
        // Service plans data
        const servicePlans = {
            'trial_7': {
                name: '體驗服務',
                price: 5,
                period: '7天',
                description: '適合新手玩家體驗的基礎技術服務',
                crypto_price: '0.16 USDT'
            },
            'monthly_30': {
                name: '標準服務',
                price: 599,
                period: '30天',
                description: '最受歡迎的完整技術服務方案',
                crypto_price: '19.17 USDT'
            },
            'quarterly_90': {
                name: '季度服務',
                price: 1499,
                period: '90天',
                description: '長期使用最划算的全功能技術服務',
                crypto_price: '47.97 USDT'
            }
        };

        let selectedPlan = null;

        // Game Selection
        function showGamePlans(gameId) {
            if (gameId === 'artale') {
                document.getElementById('games').style.display = 'none';
                document.getElementById('services').style.display = 'block';
                document.getElementById('services').scrollIntoView({ behavior: 'smooth' });
            }
        }

        function backToGames() {
            document.getElementById('services').style.display = 'none';
            document.getElementById('games').style.display = 'block';
            document.getElementById('games').scrollIntoView({ behavior: 'smooth' });
        }

        function selectPlan(planId) {
            selectedPlan = planId;
            const plan = servicePlans[planId];
            
            document.getElementById('selected-plan-info').innerHTML = `
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">${plan.name}</h4>
                <p style="margin: 0 0 1rem 0; color: var(--text-secondary);">${plan.description}</p>
                <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 1rem;">
                    <div style="font-size: 1.3rem; font-weight: bold; color: var(--text-primary);">
                        NT$ ${plan.price.toLocaleString()}
                    </div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: var(--accent-blue); font-family: 'Courier New', monospace;">
                        ≈ ${plan.crypto_price}
                    </div>
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">
                    服務期限：${plan.period}
                </div>
            `;
            
            document.getElementById('purchase-modal').style.display = 'flex';
        }

        function selectPaymentMethod(planId, paymentType) {
            if (paymentType === 'smart_pay') {
                // 跳轉到自定義付款頁面（信用卡界面）
                window.location.href = `/payment/custom/page?plan_id=${planId}`;
            } else if (paymentType === 'direct_crypto') {
                // 使用原有的直接加密貨幣付款
                selectPlan(planId);
            }
        }

        function closeModal() {
            document.getElementById('purchase-modal').style.display = 'none';
            // Clear form
            document.getElementById('user-name').value = '';
            document.getElementById('contact-email').value = '';
            document.getElementById('contact-phone').value = '';
            document.getElementById('agree-terms').checked = false;
            // Reset button
            document.getElementById('payment-btn-text').style.display = 'inline-flex';
            document.getElementById('payment-loading').style.display = 'none';
        }

        function submitPayment() {
            const userName = document.getElementById('user-name').value.trim();
            const contactEmail = document.getElementById('contact-email').value.trim();
            const contactPhone = document.getElementById('contact-phone').value.trim();
            const agreeTerms = document.getElementById('agree-terms').checked;
            
            if (!userName || !contactEmail) {
                alert('請填寫必要資訊（姓名、聯絡信箱）');
                return;
            }
            
            if (!validateEmail(contactEmail)) {
                alert('請輸入有效的電子郵件地址');
                return;
            }
            
            if (!agreeTerms) {
                alert('請先閱讀並同意免責聲明與服務條款');
                return;
            }
            
            // Show loading
            document.getElementById('payment-btn-text').style.display = 'none';
            document.getElementById('payment-loading').style.display = 'inline-block';
            
            // 創建 OxaPay 付款
            fetch('/api/create-oxapay-payment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    plan_id: selectedPlan,
                    user_info: {
                        name: userName,
                        email: contactEmail,
                        phone: contactPhone
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 重定向到 OxaPay 付款頁面
                    window.location.href = data.payment_url;
                } else {
                    alert('付款創建失敗: ' + data.error);
                    document.getElementById('payment-btn-text').style.display = 'inline-flex';
                    document.getElementById('payment-loading').style.display = 'none';
                }
            })
            .catch(error => {
                alert('系統錯誤: ' + error.message);
                document.getElementById('payment-btn-text').style.display = 'inline-flex';
                document.getElementById('payment-loading').style.display = 'none';
            });
        }

        function validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        }

        // Smooth scrolling
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

        // Close modal when clicking outside
        document.getElementById('purchase-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });

        // Escape key to close modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });

        // =============================================
        // 恢復打字機代碼背景特效
        // =============================================

        // 創建打字機效果的代碼背景
        function createCodeBackground() {
            const codeContainer = document.createElement('div');
            codeContainer.id = 'code-background';
            codeContainer.style.cssText = `
                position: fixed; 
                top: 10%; 
                left: 5%; 
                width: 90%; 
                height: 80%; 
                pointer-events: none; 
                z-index: 1; 
                opacity: 1; 
                font-family: 'Courier New', monospace; 
                color: #00d4ff;
                overflow: hidden; 
                font-size: 14px; 
                font-weight: 400;
                line-height: 1.6;
            `;
            
            document.body.appendChild(codeContainer);
            console.log('Code background container created');
            
            // 開始第一個打字循環
            startTypingCycle();
        }

        function startTypingCycle() {
            const container = document.getElementById('code-background');
            if (!container) return;
            
            const codeSnippets = [
                'import cv2',
                'import numpy as np', 
                'import threading',
                'import time',
                'import random',
                'from selenium import webdriver',
                'from PIL import Image',
                '',
                'def optimize_game():',
                '    while True:',
                '        screenshot = cv2.imread("game.png")',
                '        if detect_target(screenshot):',
                '            execute_action()',
                '        time.sleep(random.uniform(0.1, 0.3))',
                '',
                'class GameBot:',
                '    def __init__(self):',
                '        self.running = True',
                '        self.thread_pool = []',
                '        self.config = load_config()',
                '',
                '    async def process_frame(self):',
                '        frame = await self.capture_screen()',
                '        result = self.analyze_frame(frame)',
                '        return result',
                '',
                '    def detect_enemy(self, frame):',
                '        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)',
                '        mask = cv2.inRange(hsv, lower_red, upper_red)',
                '        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)',
                '        return len(contours) > 0',
                '',
                'def main():',
                '    bot = GameBot()',
                '    try:',
                '        bot.start()',
                '    except KeyboardInterrupt:',
                '        bot.stop()',
                '        print("Bot stopped safely")',
                '',
                'if __name__ == "__main__":',
                '    main()'
            ];
            
            let currentLine = 0;
            let lineHeight = 22; // 行高
            
            function typeLine() {
                if (currentLine >= codeSnippets.length) {
                    // 清空容器，重新開始
                    setTimeout(() => {
                        container.innerHTML = '';
                        currentLine = 0;
                        typeLine();
                    }, 3000);
                    return;
                }
                
                const line = codeSnippets[currentLine];
                const lineElement = document.createElement('div');
                
                lineElement.style.cssText = `
                    position: absolute;
                    left: 0;
                    top: ${currentLine * lineHeight}px;
                    white-space: pre;
                    overflow: hidden;
                    opacity: 0.12;
                    width: 0;
                    animation: 
                        typewriter ${1.5 + (line.length * 0.05)}s steps(${Math.max(line.length, 1)}) 1 forwards,
                        blink-cursor 1s step-end infinite,
                        fade-out ${6 + Math.random() * 2}s ease-in-out ${2 + Math.random()}s forwards;
                `;
                
                lineElement.textContent = line;
                container.appendChild(lineElement);
                
                currentLine++;
                
                // 下一行的延遲
                setTimeout(typeLine, 400 + Math.random() * 600);
            }
            
            typeLine();
        }

        // 添加浮動粒子效果
        function createFloatingParticles() {
            const particlesContainer = document.createElement('div');
            particlesContainer.style.cssText = `
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%; 
                pointer-events: none; 
                z-index: -1;
            `;
            
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.style.cssText = `
                    position: absolute; 
                    width: 2px; 
                    height: 2px; 
                    background: var(--accent-blue); 
                    border-radius: 50%; 
                    opacity: 0.3; 
                    animation: float-particle ${10 + Math.random() * 10}s linear infinite; 
                    left: ${Math.random() * 100}%; 
                    top: ${Math.random() * 100}%; 
                    animation-delay: ${Math.random() * 10}s;
                `;
                particlesContainer.appendChild(particle);
            }
            
            document.body.appendChild(particlesContainer);
        }

        // 添加粒子動畫 CSS
        const particleStyle = document.createElement('style');
        particleStyle.textContent = `
            @keyframes float-particle { 
                0% { transform: translateY(0) translateX(0); opacity: 0; } 
                10% { opacity: 0.3; } 
                90% { opacity: 0.3; } 
                100% { transform: translateY(-100vh) translateX(${Math.random() * 200 - 100}px); opacity: 0; } 
            }
        `;
        document.head.appendChild(particleStyle);

        // 初始化增強背景效果
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing background effects');
            createCodeBackground();
            createFloatingParticles();
        });

        // 如果 DOMContentLoaded 已經觸發，立即執行
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                createCodeBackground();
                createFloatingParticles();
            });
        } else {
            createCodeBackground();
            createFloatingParticles();
        }
    </script>
</body>
</html>
"""

# 付款成功頁面模板
PAYMENT_SUCCESS_TEMPLATE = r"""
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
            --border-color: #333333;
            --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
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
        
        <h1 class="success-title">付款成功！</h1>
        <p class="success-subtitle">感謝您購買 Scrilab Artale 遊戲技術服務</p>
        
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
                <span class="info-value">NT$ {{ payment_record.amount if payment_record else 'N/A' }}</span>
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
        
        <p class="footer-note">請妥善保管您的序號，避免外洩給他人使用。</p>
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
            const amount = "{{ payment_record.amount if payment_record else 'N/A' }}";
            
            const content = `Scrilab Artale 服務購買成功

服務方案：${planName}
服務期限：${planPeriod}
付款金額：NT$ ${amount}
專屬序號：${uuid}

請妥善保管您的序號，避免外洩給他人使用。

操作手冊：請訪問 /manual 查看詳細使用說明

技術支援：
- Discord：https://discord.gg/HPzNrQmN
- Email：scrilabstaff@gmail.com

Scrilab 技術團隊
${new Date().toLocaleDateString('zh-TW')}`;

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Scrilab_服務訊息_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""

# 付款取消頁面模板
PAYMENT_CANCEL_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>付款取消 - Scrilab</title>
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
            --bg-card: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-muted: #808080;
            --accent-orange: #f59e0b;
            --accent-blue: #00d4ff;
            --border-color: #333333;
            --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
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

        .cancel-container {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            max-width: 500px;
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

        .cancel-icon {
            width: 80px;
            height: 80px;
            background: var(--gradient-warning);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 2rem;
            font-size: 2.5rem;
            color: white;
        }

        .cancel-title {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            color: var(--accent-orange);
        }

        .cancel-subtitle {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 2.5rem;
        }

        .btn {
            padding: 1rem 2rem;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1rem;
            border: none;
            margin: 0 0.5rem;
        }

        .btn-primary {
            background: var(--gradient-warning);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(245, 158, 11, 0.3);
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

        .footer-note {
            margin-top: 2rem;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        @media (max-width: 600px) {
            .cancel-container {
                padding: 2rem;
            }
            
            .cancel-title {
                font-size: 1.8rem;
            }
            
            .btn {
                margin: 0.5rem 0;
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="cancel-container">
        <div class="cancel-icon">
            <i class="fas fa-times"></i>
        </div>
        
        <h1 class="cancel-title">付款已取消</h1>
        <p class="cancel-subtitle">您已取消付款流程，如果需要購買服務，請重新選擇方案。</p>
        
        <div style="margin-top: 2rem;">
            <a href="/products" class="btn btn-primary">
                <i class="fas fa-shopping-cart"></i>
                <span>重新選購</span>
            </a>
            <a href="/products" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
        
        <p class="footer-note">如有任何問題，歡迎透過 Discord 或 Email 聯繫我們，或查看操作手冊了解更多資訊。</p>
    </div>
</body>
</html>
"""