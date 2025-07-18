"""
intro_routes.py - 基本介紹路由處理（幽默版）
"""
from flask import Blueprint, render_template_string, request, jsonify
import random
import time

# 創建介紹頁面藍圖
intro_bp = Blueprint('intro', __name__, url_prefix='/intro')

# 幽默介紹頁面模板
INTRO_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artale Script - 基本介紹 | 讓你的角色像AI一樣聰明！</title>
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
            --accent-pink: #ec4899;
            --border-color: #333333;
            --border-hover: #555555;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-accent: linear-gradient(135deg, #00d4ff 0%, #8b5cf6 100%);
            --gradient-rainbow: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57, #ff9ff3);
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
            overflow-x: hidden;
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
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
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
            transform: translateY(-2px);
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

        /* 主要容器 */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* 英雄區域 */
        .hero-section {
            text-align: center;
            padding: 4rem 0;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            margin-bottom: 3rem;
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: var(--gradient-rainbow);
            opacity: 0.05;
            animation: rotate 20s linear infinite;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .hero-title {
            font-size: 3.5rem;
            font-weight: 900;
            margin-bottom: 1rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
        }

        .hero-subtitle {
            font-size: 1.3rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            position: relative;
            z-index: 1;
        }

        .hero-description {
            font-size: 1.1rem;
            color: var(--text-muted);
            max-width: 800px;
            margin: 0 auto 2rem;
            position: relative;
            z-index: 1;
        }

        .floating-emojis {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        }

        .emoji {
            position: absolute;
            font-size: 2rem;
            opacity: 0.1;
            animation: float 6s ease-in-out infinite;
        }

        .emoji:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
        .emoji:nth-child(2) { top: 30%; right: 15%; animation-delay: 1s; }
        .emoji:nth-child(3) { bottom: 30%; left: 20%; animation-delay: 2s; }
        .emoji:nth-child(4) { bottom: 20%; right: 10%; animation-delay: 3s; }
        .emoji:nth-child(5) { top: 60%; left: 50%; animation-delay: 4s; }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(5deg); }
        }

        /* 特色卡片 */
        .features-section {
            margin-bottom: 4rem;
        }

        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 3rem;
            color: var(--text-primary);
            position: relative;
        }

        .section-title::after {
            content: '';
            display: block;
            width: 100px;
            height: 4px;
            background: var(--gradient-accent);
            margin: 1rem auto;
            border-radius: 2px;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }

        .feature-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            text-align: center;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s;
        }

        .feature-card:hover {
            transform: translateY(-10px);
            border-color: var(--accent-blue);
            box-shadow: var(--shadow-lg);
        }

        .feature-card:hover::before {
            left: 100%;
        }

        .feature-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            background: var(--gradient-accent);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: white;
            position: relative;
            z-index: 1;
        }

        .feature-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .feature-description {
            color: var(--text-secondary);
            line-height: 1.7;
            margin-bottom: 1.5rem;
        }

        .feature-highlight {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 1rem;
            color: var(--accent-green);
            font-weight: 600;
            font-size: 0.9rem;
        }

        /* 幽默對比區域 */
        .comparison-section {
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 3rem;
            margin-bottom: 4rem;
            border: 1px solid var(--border-color);
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3rem;
            margin-top: 2rem;
        }

        .comparison-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            border: 2px solid;
            position: relative;
        }

        .comparison-card.without {
            border-color: var(--accent-red);
            background: rgba(239, 68, 68, 0.05);
        }

        .comparison-card.with {
            border-color: var(--accent-green);
            background: rgba(16, 185, 129, 0.05);
        }

        .comparison-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .comparison-title.without {
            color: #fca5a5;
        }

        .comparison-title.with {
            color: #6ee7b7;
        }

        .comparison-list {
            list-style: none;
            padding: 0;
        }

        .comparison-item {
            padding: 0.8rem 0;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            border-bottom: 1px solid var(--border-color);
        }

        .comparison-item:last-child {
            border-bottom: none;
        }

        .comparison-item i {
            font-size: 1.2rem;
        }

        .comparison-item.negative i {
            color: var(--accent-red);
        }

        .comparison-item.positive i {
            color: var(--accent-green);
        }

        /* FAQ 區域 */
        .faq-section {
            margin-bottom: 4rem;
        }

        .faq-item {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1rem;
            overflow: hidden;
            transition: var(--transition);
        }

        .faq-question {
            padding: 1.5rem 2rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            color: var(--text-primary);
            background: var(--bg-tertiary);
            transition: var(--transition);
        }

        .faq-question:hover {
            background: var(--bg-card);
            color: var(--accent-blue);
        }

        .faq-answer {
            padding: 0 2rem;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
            color: var(--text-secondary);
            line-height: 1.7;
        }

        .faq-item.active .faq-answer {
            padding: 1.5rem 2rem;
            max-height: 500px;
        }

        .faq-item.active .faq-question i {
            transform: rotate(180deg);
        }

        /* 互動演示區域 */
        .demo-section {
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 3rem;
            margin-bottom: 4rem;
            border: 1px solid var(--border-color);
            text-align: center;
        }

        .demo-button {
            background: var(--gradient-accent);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            margin: 0.5rem;
        }

        .demo-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .demo-result {
            margin-top: 2rem;
            padding: 1.5rem;
            background: var(--bg-card);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            color: var(--text-secondary);
        }

        /* CTA 區域 */
        .cta-section {
            background: var(--gradient-accent);
            border-radius: var(--border-radius);
            padding: 4rem 3rem;
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
        }

        .cta-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="white" opacity="0.1"/></svg>') repeat;
            animation: sparkle 3s linear infinite;
        }

        @keyframes sparkle {
            0% { transform: translateY(0); }
            100% { transform: translateY(-100px); }
        }

        .cta-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }

        .cta-description {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }

        .cta-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
            position: relative;
            z-index: 1;
        }

        .cta-button {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            padding: 1rem 2rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            transition: var(--transition);
            backdrop-filter: blur(10px);
        }

        .cta-button:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.6);
            transform: translateY(-3px);
        }

        .cta-button.primary {
            background: white;
            color: var(--bg-primary);
            border-color: white;
        }

        .cta-button.primary:hover {
            background: rgba(255, 255, 255, 0.9);
            color: var(--bg-primary);
        }

        /* 響應式設計 */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .hero-title {
                font-size: 2.5rem;
            }
            
            .comparison-grid {
                grid-template-columns: 1fr;
                gap: 2rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .nav-links {
                display: none;
            }
            
            .cta-buttons {
                flex-direction: column;
                align-items: center;
            }
        }

        /* 新增動畫效果 */
        .bounce-in {
            animation: bounceIn 1s ease-out;
        }

        @keyframes bounceIn {
            0% { opacity: 0; transform: scale(0.3); }
            50% { opacity: 1; transform: scale(1.05); }
            70% { transform: scale(0.9); }
            100% { opacity: 1; transform: scale(1); }
        }

        .fade-in-up {
            opacity: 0;
            transform: translateY(30px);
            animation: fadeInUp 0.8s ease-out forwards;
        }

        @keyframes fadeInUp {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* 延遲動畫 */
        .delay-1 { animation-delay: 0.2s; }
        .delay-2 { animation-delay: 0.4s; }
        .delay-3 { animation-delay: 0.6s; }
        .delay-4 { animation-delay: 0.8s; }
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
                <li><a href="#features">功能特色</a></li>
                <li><a href="#comparison">使用對比</a></li>
                <li><a href="#faq">常見問題</a></li>
                <li><a href="#demo">互動演示</a></li>
            </ul>
            <a href="/products" class="back-btn">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
    </nav>

    <div class="container">
        <!-- 英雄區域 -->
        <section class="hero-section bounce-in">
            <div class="floating-emojis">
                <div class="emoji">🎮</div>
                <div class="emoji">🤖</div>
                <div class="emoji">⚡</div>
                <div class="emoji">🎯</div>
                <div class="emoji">🌟</div>
            </div>
            <h1 class="hero-title">歡迎來到 Artale Script 的世界！</h1>
            <p class="hero-subtitle">🎮 專業級遊戲技術服務，讓你的角色擁有AI級別的智能！</p>
            <p class="hero-description">
                台灣製造，專為 MapleStory Worlds - Artale 打造的專業技術服務。<br>
                採用最先進的電腦視覺技術，提供安全、穩定、高效的遊戲體驗！ ✨
            </p>
        </section>

        <!-- 功能特色 -->
        <section id="features" class="features-section">
            <h2 class="section-title fade-in-up">🌟 為什麼選擇我們？</h2>
            <div class="features-grid">
                <div class="feature-card fade-in-up delay-1">
                    <div class="feature-icon">
                        <i class="fas fa-eye"></i>
                    </div>
                    <h3 class="feature-title">先進電腦視覺技術</h3>
                    <p class="feature-description">
                        採用最新的螢幕截圖技術進行即時分析，智能識別遊戲場景、<br>
                        怪物位置、角色狀態等資訊，提供精準的自動化操作。
                    </p>
                    <div class="feature-highlight">
                        🎯 精準度：99%+ 的目標識別率
                    </div>
                </div>

                <div class="feature-card fade-in-up delay-2">
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h3 class="feature-title">非侵入式安全技術</h3>
                    <p class="feature-description">
                        完全不讀取遊戲記憶體或修改任何檔案，純粹基於視覺分析，<br>
                        確保您的帳號安全，符合綠色軟體標準。
                    </p>
                    <div class="feature-highlight">
                        🛡️ 安全等級：軍用級加密保護
                    </div>
                </div>

                <div class="feature-card fade-in-up delay-3">
                    <div class="feature-icon">
                        <i class="fas fa-random"></i>
                    </div>
                    <h3 class="feature-title">全隨機演算法</h3>
                    <p class="feature-description">
                        所有操作都經過隨機化處理，移動路徑、攻擊時機、休息間隔<br>
                        都模擬真實玩家行為，讓檢測系統難以識別。
                    </p>
                    <div class="feature-highlight">
                        🎲 隨機性：接近真人的自然行為模式
                    </div>
                </div>

                <div class="feature-card fade-in-up delay-4">
                    <div class="feature-icon">
                        <i class="fas fa-desktop"></i>
                    </div>
                    <h3 class="feature-title">超直觀 GUI 介面</h3>
                    <p class="feature-description">
                        台灣團隊精心設計的圖形化介面，一鍵啟動，即時監控，<br>
                        詳細日誌顯示，讓您輕鬆掌控每個細節。
                    </p>
                    <div class="feature-highlight">
                        👨‍💻 易用性：3分鐘上手，無需技術背景
                    </div>
                </div>

                <div class="feature-card fade-in-up delay-1">
                    <div class="feature-icon">
                        <i class="fas fa-map"></i>
                    </div>
                    <h3 class="feature-title">廣泛地圖支援</h3>
                    <p class="feature-description">
                        理論上支援全部地圖，實際上完美適配平坦及多層簡易架構地圖，<br>
                        足夠您從新手村練到滿級都不會無聊。
                    </p>
                    <div class="feature-highlight">
                        🗺️ 支援地圖：200+ 個主流練功地點
                    </div>
                </div>

                <div class="feature-card fade-in-up delay-2">
                    <div class="feature-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <h3 class="feature-title">24/7 不間斷運行</h3>
                    <p class="feature-description">
                        上班時、睡覺時、出門時，讓腳本為您持續練功，<br>
                        回來就能看到滿滿的經驗值和戰利品！
                    </p>
                    <div class="feature-highlight">
                        ⏰ 目標：起床看到耳敏或香菇的小確幸
                    </div>
                </div>
            </div>
        </section>

        <!-- 技術特色與注意事項 -->
        <section id="technical" class="technical-section">
            <h2 class="section-title">技術特色與重要說明</h2>
            <div class="tech-grid">
                <div class="tech-card advantage">
                    <div class="tech-icon advantage">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h3>技術優勢</h3>
                    <ul class="tech-list">
                        <li><strong>台灣製造</strong> - 本土團隊開發，了解玩家需求</li>
                        <li><strong>直觀GUI介面</strong> - 圖形化操作，3分鐘上手</li>
                        <li><strong>全功能整合</strong> - 怪物檢測、攀爬、補血、避人一應俱全</li>
                        <li><strong>即時日誌監控</strong> - 清楚掌握腳本運行狀態</li>
                        <li><strong>高度自定義</strong> - 數十種參數可調整</li>
                        <li><strong>智能紅點檢測</strong> - 自動避開其他玩家</li>
                        <li><strong>被動技能管理</strong> - 智能CD管理，效率最大化</li>
                        <li><strong>多層地圖支援</strong> - 自動攀爬繩索，適應複雜地形</li>
                        <li><strong>血藍量監控</strong> - 智能補給，永不死亡</li>
                        <li><strong>完全隨機化</strong> - 模擬真人行為，降低檢測風險</li>
                    </ul>
                </div>
                
                <div class="tech-card limitation">
                    <div class="tech-icon limitation">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h3>使用限制與注意事項</h3>
                    <ul class="tech-list">
                        <li><strong>必須保持前景</strong> - 使用螢幕截圖技術，遊戲視窗不能被遮蔽</li>
                        <li><strong>固定解析度</strong> - 需設定為1280x720視窗模式</li>
                        <li><strong>爬繩流暢度</strong> - 非侵入式設計導致爬繩動作不如真人流暢</li>
                        <li><strong>效率取捨</strong> - 全隨機移動確保安全，但效率會低於手動操作</li>
                        <li><strong>地圖限制</strong> - 最適合平坦或多層簡易架構地圖</li>
                        <li><strong>網路需求</strong> - 需要穩定的網路連接進行授權驗證</li>
                    </ul>
                </div>
            </div>
            
            <div class="expectation-card">
                <h3>📈 效率期待值設定</h3>
                <p>我們的設計理念：<strong>「安全第一，效率第二」</strong></p>
                <div class="expectation-grid">
                    <div class="expectation-item">
                        <i class="fas fa-target"></i>
                        <div>
                            <strong>目標設定</strong>
                            <p>上班時、睡覺時掛機，起床能看到一張耳敏或一顆香菇的小確幸</p>
                        </div>
                    </div>
                    <div class="expectation-item">
                        <i class="fas fa-balance-scale"></i>
                        <div>
                            <strong>效率平衡</strong>
                            <p>犧牲部分效率換取更高的安全性，讓您能長期穩定使用</p>
                        </div>
                    </div>
                    <div class="expectation-item">
                        <i class="fas fa-clock"></i>
                        <div>
                            <strong>時間價值</strong>
                            <p>解放雙手，把時間投資在更有意義的事情上</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- 互動演示 -->
        <section id="demo" class="demo-section">
            <h2 class="section-title">🎮 互動演示</h2>
            <p style="margin-bottom: 2rem; color: var(--text-secondary);">
                點擊下面的按鈕，體驗一下我們腳本的「智慧」反應！
            </p>
            <div>
                <button class="demo-button" onclick="demoAction('monster')">
                    <i class="fas fa-dragon"></i> 發現怪物
                </button>
                <button class="demo-button" onclick="demoAction('player')">
                    <i class="fas fa-user"></i> 檢測到玩家
                </button>
                <button class="demo-button" onclick="demoAction('lowHP')">
                    <i class="fas fa-heart-broken"></i> 血量不足
                </button>
                <button class="demo-button" onclick="demoAction('levelUp')">
                    <i class="fas fa-star"></i> 升級了！
                </button>
            </div>
            <div id="demo-result" class="demo-result">
                點擊上方按鈕看看我們的腳本會如何反應～
            </div>
        </section>

        <!-- 常見問題 -->
        <section id="faq" class="faq-section">
            <h2 class="section-title">❓ 常見問題（都是大家真實的疑惑）</h2>
            
            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🤔 這個腳本真的安全嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    我們的腳本採用完全非侵入式技術，純粹基於螢幕截圖進行分析，
                    不讀取遊戲記憶體、不修改任何檔案、不進行網路封包攔截。
                    這就像您請了一個朋友在旁邊看著螢幕幫您操作滑鼠鍵盤一樣自然！
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🛡️ 使用腳本會被封號嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    我們採用全隨機演算法，所有操作都經過隨機化處理，
                    移動路徑、攻擊時機、技能使用都模擬真實玩家行為。
                    但仍建議您理性使用，任何第三方工具都存在一定風險，請自行評估。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>💻 我的電腦配置很低，能跑得動嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    我們的腳本非常輕量！只要能順暢運行 Artale 遊戲的電腦就能完美支援。
                    主要需求就是穩定的 CPU 進行截圖分析，記憶體需求很低，
                    甚至比很多瀏覽器佔用的資源還少。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>⏰ 效率到底如何？真的有用嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    老實說，效率肯定比不上您專心手動練功。我們的設計理念是「安全第一，效率第二」。
                    目標是讓您在上班、睡覺時能持續獲得經驗值，起床看到一張耳敏或一顆香菇的小確幸。
                    把它當作「被動收入」的概念，而不是高效率練功工具。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🗺️ 支援哪些地圖？複雜地圖能用嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    理論上支援全部地圖，實際上最適合平坦或多層簡易架構的地圖。
                    像是各種蘑菇地圖、史萊姆系列地圖都很完美。複雜的迷宮型地圖可能會讓角色迷路，
                    但說實話，光是現有支援的地圖就夠您從新手練到滿級了！
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🎮 遊戲視窗一定要保持前景嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    是的，由於我們使用螢幕截圖技術進行分析，遊戲視窗必須保持可見且不被遮蔽。
                    同時需要設定為 1280x720 視窗模式。這確實是個限制，
                    但也是我們採用非侵入式技術必須付出的代價。建議您準備一台專門的電腦來跑腳本。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🧗 為什麼爬繩動作看起來不太流暢？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    這是因為我們堅持不讀取遊戲內部資料所導致的。腳本只能透過視覺判斷角色位置和繩索位置，
                    所以爬繩時需要多次修正方向，看起來確實不如真人那麼流暢。
                    但功能是正常的，只是美觀度稍差，請多包涵！
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>💰 價格會不會太貴？值得嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    以台灣的消費水準來說，我們的定價相當實惠。想想看：一頓便當的錢換來一週的自動練功，
                    一杯手搖飲的錢換來一個月的解放雙手時間，這個投資報酬率其實很不錯！
                    況且我們是台灣製造，提供完整的中文客服支援。
                </div>
            </div>
        </section>

        <!-- CTA 區域 -->
        <section class="cta-section">
            <h2 class="cta-title">🚀 準備好體驗專業級遊戲技術服務了嗎？</h2>
            <p class="cta-description">
                台灣製造，專業品質，完整支援<br>
                加入我們，讓您的 Artale 之旅更加輕鬆愉快！
            </p>
            <div class="cta-buttons">
                <a href="/products#services" class="cta-button primary">
                    <i class="fas fa-shopping-cart"></i>
                    立即選購服務
                </a>
                <a href="/manual" class="cta-button">
                    <i class="fas fa-book"></i>
                    查看詳細教學
                </a>
                <a href="https://discord.gg/HPzNrQmN" target="_blank" class="cta-button">
                    <i class="fab fa-discord"></i>
                    加入 Discord 社群
                </a>
            </div>
        </section>
    </div>

    <script>
        // FAQ 切換功能
        function toggleFAQ(element) {
            const faqItem = element.parentElement;
            const isActive = faqItem.classList.contains('active');
            
            // 關閉所有其他 FAQ
            document.querySelectorAll('.faq-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // 如果當前項目不是激活狀態，則激活它
            if (!isActive) {
                faqItem.classList.add('active');
            }
        }

        // 演示功能
        function demoAction(action) {
            const resultDiv = document.getElementById('demo-result');
            const responses = {
                monster: [
                    "🎯 檢測到怪物！立即鎖定目標...",
                    "⚡ 0.01秒反應時間，攻擊開始！",
                    "💥 怪物已被消滅！經驗值 +1337",
                    "🤖 繼續搜索下一個目標..."
                ],
                player: [
                    "🚨 警報！檢測到紅點（其他玩家）",
                    "👻 啟動隱身模式...",
                    "🌀 正在切換頻道...",
                    "✅ 成功脫離，繼續安全練功"
                ],
                lowHP: [
                    "❤️ 血量偵測：30%，低於安全線！",
                    "🍶 自動使用HP恢復藥水",
                    "💪 血量已恢復至 100%",
                    "😎 健康狀態良好，繼續戰鬥！"
                ],
                levelUp: [
                    "🌟 等級提升！當前等級：42",
                    "📈 屬性點已自動分配",
                    "🎉 恭喜！你變強了！",
                    "😴 你甚至不用醒來就升級了"
                ]
            };

            const messages = responses[action];
            let currentIndex = 0;

            // 清空並開始顯示訊息
            resultDiv.textContent = '';
            resultDiv.style.color = 'var(--accent-blue)';

            function showNextMessage() {
                if (currentIndex < messages.length) {
                    resultDiv.textContent = messages[currentIndex];
                    currentIndex++;
                    setTimeout(showNextMessage, 1000);
                } else {
                    setTimeout(() => {
                        resultDiv.textContent = '點擊上方按鈕看看我們的腳本會如何反應～';
                        resultDiv.style.color = 'var(--text-secondary)';
                    }, 2000);
                }
            }

            showNextMessage();
        }

        // 滾動動畫
        function handleScrollAnimations() {
            const elements = document.querySelectorAll('.fade-in-up');
            
            elements.forEach(element => {
                const elementTop = element.getBoundingClientRect().top;
                const elementVisible = 150;
                
                if (elementTop < window.innerHeight - elementVisible) {
                    element.classList.add('fade-in-up');
                }
            });
        }

        // 平滑滾動
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
            
            handleScrollAnimations();
        });

        // 頁面載入完成後的初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 添加一些隨機的互動效果
            const features = document.querySelectorAll('.feature-card');
            features.forEach((card, index) => {
                card.addEventListener('mouseenter', function() {
                    // 隨機顏色效果
                    const colors = ['--accent-blue', '--accent-purple', '--accent-green', '--accent-orange', '--accent-pink'];
                    const randomColor = colors[Math.floor(Math.random() * colors.length)];
                    card.style.borderColor = `var(${randomColor})`;
                });
                
                card.addEventListener('mouseleave', function() {
                    card.style.borderColor = 'var(--border-color)';
                });
            });

            // 初始滾動動畫檢查
            handleScrollAnimations();

            // 添加一些歡迎訊息
            console.log('🎮 歡迎來到 Artale Script 的世界！');
            console.log('🤖 準備好讓你的角色變成練功機器了嗎？');
            console.log('💡 提示：記得先看完所有功能介紹再決定購買哦！');
        });

        // 有趣的彩蛋功能
        let clickCount = 0;
        document.addEventListener('click', function() {
            clickCount++;
            if (clickCount === 42) {
                // 生命、宇宙和一切的答案
                alert('🎉 恭喜你發現了彩蛋！你真是個有耐心的用戶！42 是生命、宇宙和一切的答案！');
                clickCount = 0;
            }
        });

        // Konami Code 彩蛋
        let konamiCode = [];
        const konami = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65]; // ↑↑↓↓←→←→BA
        
        document.addEventListener('keydown', function(e) {
            konamiCode.push(e.keyCode);
            if (konamiCode.length > konami.length) {
                konamiCode.shift();
            }
            
            if (konamiCode.join(',') === konami.join(',')) {
                // 秘密模式啟動
                document.body.style.filter = 'hue-rotate(180deg)';
                alert('🌈 秘密彩虹模式啟動！恭喜你知道經典的 Konami Code！');
                setTimeout(() => {
                    document.body.style.filter = '';
                }, 5000);
                konamiCode = [];
            }
        });
    </script>
</body>
</html>
"""

# 路由定義
@intro_bp.route('', methods=['GET'])
def intro_home():
    """基本介紹主頁"""
    return render_template_string(INTRO_TEMPLATE)

@intro_bp.route('/features', methods=['GET'])
def intro_features():
    """功能介紹頁面"""
    return render_template_string(INTRO_TEMPLATE)

@intro_bp.route('/demo', methods=['POST'])
def demo_action():
    """演示動作API"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        
        # 模擬不同的演示回應
        responses = {
            'monster': {
                'success': True,
                'message': '怪物已被我們的AI消滅！',
                'details': '反應時間：0.01秒，準確度：100%'
            },
            'player': {
                'success': True,
                'message': '成功避開其他玩家！',
                'details': '隱身模式啟動，頻道切換完成'
            },
            'lowHP': {
                'success': True,
                'message': '血量已自動恢復！',
                'details': 'HP: 100%, MP: 100%'
            },
            'levelUp': {
                'success': True,
                'message': '恭喜升級！',
                'details': f'新等級：{random.randint(42, 99)}'
            }
        }
        
        return jsonify(responses.get(action, {
            'success': False,
            'message': '未知動作'
        }))
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'演示錯誤：{str(e)}'
        }), 500

@intro_bp.route('/stats', methods=['GET'])
def get_stats():
    """獲取一些有趣的統計數據"""
    stats = {
        'monsters_defeated': random.randint(999999, 9999999),
        'hours_saved': random.randint(10000, 99999),
        'happy_users': random.randint(1000, 9999),
        'coffee_cups_saved': random.randint(50000, 999999),
        'sleep_hours_gained': random.randint(5000, 50000)
    }
    
    return jsonify({
        'success': True,
        'stats': stats,
        'funny_fact': random.choice([
            '我們的腳本已經消滅了足夠的怪物來拯救一個虛擬王國！',
            '使用我們腳本節省的時間足夠看完所有的迪士尼電影！',
            '我們幫用戶省下的咖啡錢可以買一台新電腦！',
            '我們的AI比大部分真人玩家反應還快（不是在開玩笑）！'
        ])
    })

# 確保正確導出
__all__ = ['intro_bp']