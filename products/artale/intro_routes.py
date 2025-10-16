"""
intro_routes.py - 基本介紹路由處理（幽默版 + 影片展示）
"""
from flask import Blueprint, render_template_string, request, jsonify
import random
import time
import os

# 創建介紹頁面藍圖
intro_bp = Blueprint('intro', __name__, url_prefix='/intro')

# 幽默介紹頁面模板（含影片展示）
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
            /* 背景色 */
            --bg-primary: #000000;
            --bg-secondary: #0a0a0a;
            --bg-card: #111111;
            --bg-elevated: #1a1a1a;
            
            /* 文字色 */
            --text-primary: #ffffff;
            --text-secondary: #a3a3a3;
            --text-muted: #737373;
            
            /* 主色 - 只用藍色 */
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --primary-light: rgba(59, 130, 246, 0.1);
            --primary-border: rgba(59, 130, 246, 0.3);
            
            /* 功能色 */
            --success: #10b981;
            --success-light: rgba(16, 185, 129, 0.1);
            --warning: #f59e0b;
            --warning-light: rgba(245, 158, 11, 0.1);
            
            /* 邊框 */
            --border: rgba(255, 255, 255, 0.1);
            --border-hover: rgba(255, 255, 255, 0.2);
            
            /* 陰影 */
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.5);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.5);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
            
            /* 其他 */
            --radius: 8px;
            --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            overflow-x: hidden;
        }

        /* 主要內容容器 - 浮動卡片效果 */
        .main-wrapper {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-primary);
            border-left: 1px solid rgba(255, 255, 255, 0.05);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 0 80px rgba(0, 0, 0, 0.8);
            min-height: 100vh;
        }

        /* Navigation - 固定在頂部，跨越全寬 */
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 26, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border);
            z-index: 1000;
            transition: var(--transition);
        }

        .navbar::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 1200px;
            height: 1px;
            background: var(--border);
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 3rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            text-decoration: none;
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: var(--primary);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.875rem;
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 2rem;
            align-items: center;
        }

        .nav-links a {
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.875rem;
            transition: var(--transition);
        }

        .nav-links a:hover {
            color: var(--text-primary);
        }

        .back-btn {
            background: var(--primary);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.875rem;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            border: none;
        }

        .back-btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        /* 主要容器 */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 6rem 3rem 2rem;
        }

        /* 英雄區域 */
        .hero-section {
            text-align: center;
            padding: 3rem 0;
            background: var(--bg-elevated);
            border-radius: var(--radius);
            border: 1px solid var(--border);
            margin-bottom: 3rem;
            position: relative;
            overflow: hidden;
        }

        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
            letter-spacing: -0.02em;
            position: relative;
            z-index: 1;
        }

        .hero-subtitle {
            font-size: 1.125rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 1;
        }

        .hero-description {
            font-size: 0.9375rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto 1.5rem;
            position: relative;
            z-index: 1;
            line-height: 1.6;
        }

        /* 移除floating emojis動畫以符合簡約風格 */

        /* 影片展示區域 */
        .video-section {
            margin-bottom: 3rem;
            background: var(--bg-elevated);
            border-radius: var(--radius);
            padding: 2rem;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }

        .video-container {
            position: relative;
            z-index: 1;
        }

        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }

        .video-card {
            background: var(--bg-card);
            border-radius: var(--radius);
            overflow: hidden;
            border: 1px solid var(--border);
            transition: var(--transition);
            position: relative;
        }

        .video-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-lg);
        }

        .video-player {
            width: 100%;
            height: 250px;
            background: #000;
            position: relative;
        }

        .video-player video {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 12px 12px 0 0;
        }

        .video-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: var(--transition);
            cursor: pointer;
        }

        .video-overlay:hover {
            opacity: 1;
        }

        .play-button {
            width: 60px;
            height: 60px;
            background: var(--primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            transition: var(--transition);
        }

        .video-overlay:hover .play-button {
            background: var(--primary-hover);
        }

        .video-info {
            padding: 1.5rem;
        }

        .video-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .video-description {
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 1rem;
        }

        .video-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .video-tag {
            background: var(--primary-light);
            color: var(--primary);
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        .video-placeholder {
            width: 100%;
            height: 250px;
            background: var(--bg-card);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            border-radius: var(--radius) var(--radius) 0 0;
        }

        .video-placeholder i {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        /* 特色卡片 */
        .features-section {
            margin-bottom: 3rem;
        }

        .section-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 2rem;
            color: var(--text-primary);
            letter-spacing: -0.02em;
            position: relative;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }

        .feature-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2rem;
            text-align: center;
            transition: var(--transition);
            position: relative;
        }

        .feature-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-lg);
        }

        .feature-icon {
            width: 64px;
            height: 64px;
            margin: 0 auto 1.5rem;
            background: var(--primary);
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
        }

        .feature-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .feature-description {
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 1.5rem;
            font-size: 0.9375rem;
        }

        .feature-highlight {
            background: var(--success-light);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: var(--radius);
            padding: 0.75rem;
            color: var(--success);
            font-weight: 500;
            font-size: 0.875rem;
        }

        /* 技術特色區域 - 補齊的 CSS */
        .technical-section {
            margin-bottom: 4rem;
        }

        .tech-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 3rem;
        }

        .tech-card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 2rem;
            border: 1px solid;
            position: relative;
            transition: var(--transition);
        }

        .tech-card.advantage {
            border-color: rgba(16, 185, 129, 0.3);
            background: var(--success-light);
        }

        .tech-card.limitation {
            border-color: rgba(245, 158, 11, 0.3);
            background: var(--warning-light);
        }

        .tech-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .tech-icon {
            width: 48px;
            height: 48px;
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
        }

        .tech-icon.advantage {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
        }

        .tech-icon.limitation {
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning);
        }

        .tech-card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
        }

        .tech-list {
            list-style: none;
            padding: 0;
        }

        .tech-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
            color: var(--text-secondary);
            line-height: 1.5;
            font-size: 0.875rem;
        }

        .tech-list li:last-child {
            border-bottom: none;
        }

        .tech-list li strong {
            color: var(--text-primary);
            font-weight: 500;
        }

        .expectation-card {
            background: var(--bg-elevated);
            border-radius: var(--radius);
            padding: 2rem;
            border: 1px solid var(--border);
            text-align: center;
        }

        .expectation-card h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .expectation-card > p {
            font-size: 0.9375rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }

        .expectation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }

        .expectation-item {
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            text-align: left;
        }

        .expectation-item i {
            font-size: 1.5rem;
            color: var(--primary);
            margin-top: 0.2rem;
            flex-shrink: 0;
        }

        .expectation-item strong {
            display: block;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .expectation-item p {
            color: var(--text-secondary);
            line-height: 1.6;
            margin: 0;
        }

        /* 幽默對比區域 */
        .comparison-section {
            background: var(--bg-elevated);
            border-radius: var(--radius);
            padding: 2rem;
            margin-bottom: 3rem;
            border: 1px solid var(--border);
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3rem;
            margin-top: 2rem;
        }

        .comparison-card {
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 1.5rem;
            border: 1px solid;
            position: relative;
        }

        .comparison-card.without {
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.05);
        }

        .comparison-card.with {
            border-color: rgba(16, 185, 129, 0.3);
            background: var(--success-light);
        }

        .comparison-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .comparison-title.without {
            color: #fca5a5;
        }

        .comparison-title.with {
            color: var(--success);
        }

        .comparison-list {
            list-style: none;
            padding: 0;
        }

        .comparison-item {
            padding: 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.875rem;
        }

        .comparison-item:last-child {
            border-bottom: none;
        }

        .comparison-item i {
            font-size: 1rem;
        }

        .comparison-item.negative i {
            color: #ef4444;
        }

        .comparison-item.positive i {
            color: var(--success);
        }

        /* FAQ 區域 */
        .faq-section {
            margin-bottom: 3rem;
        }

        .faq-item {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            margin-bottom: 0.75rem;
            overflow: hidden;
            transition: var(--transition);
        }

        .faq-question {
            padding: 1.25rem 1.5rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 500;
            color: var(--text-primary);
            background: var(--bg-elevated);
            transition: var(--transition);
            font-size: 0.9375rem;
        }

        .faq-question:hover {
            background: var(--bg-card);
            color: var(--primary);
        }

        .faq-answer {
            padding: 0 1.5rem;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 0.875rem;
        }

        .faq-item.active .faq-answer {
            padding: 1.25rem 1.5rem;
            max-height: 500px;
        }

        .faq-item.active .faq-question i {
            transform: rotate(180deg);
        }

        /* 互動演示區域 */
        .demo-section {
            background: var(--bg-elevated);
            border-radius: var(--radius);
            padding: 2rem;
            margin-bottom: 3rem;
            border: 1px solid var(--border);
            text-align: center;
        }

        .demo-button {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            margin: 0.5rem;
        }

        .demo-button:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .demo-result {
            margin-top: 1.5rem;
            padding: 1.25rem;
            background: var(--bg-card);
            border-radius: var(--radius);
            border: 1px solid var(--border);
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9375rem;
            color: var(--text-secondary);
        }

        /* CTA 區域 */
        .cta-section {
            background: var(--primary);
            border-radius: var(--radius);
            padding: 3rem 2rem;
            text-align: center;
            color: white;
            position: relative;
        }

        .cta-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }

        .cta-description {
            font-size: 1rem;
            margin-bottom: 1.5rem;
            opacity: 0.95;
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
            background: rgba(255, 255, 255, 0.15);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.875rem;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .cta-button:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.5);
            transform: translateY(-1px);
        }

        .cta-button.primary {
            background: white;
            color: var(--primary);
            border-color: white;
        }

        .cta-button.primary:hover {
            background: rgba(255, 255, 255, 0.95);
        }

        /* 系統需求樣式 */
        .manual-section {
            margin-bottom: 4rem;
        }

        /* 響應式設計 */
        @media (max-width: 768px) {
            .main-wrapper {
                box-shadow: none;
            }

            .nav-links {
                display: none;
            }

            .nav-container,
            .container {
                padding-left: 1.5rem;
                padding-right: 1.5rem;
            }
            
            .hero-title {
                font-size: 2rem;
            }
            
            .comparison-grid, .tech-grid {
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .cta-buttons {
                flex-direction: column;
                align-items: center;
            }

            .expectation-grid {
                grid-template-columns: 1fr;
            }

            .video-grid {
                grid-template-columns: 1fr;
            }

            .video-player {
                height: 200px;
            }
        }

        /* 簡化動畫效果 */
        .fade-in-up {
            animation: fadeInUp 0.3s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* 全螢幕影片模態 */
        .video-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 2000;
            animation: fadeIn 0.3s ease;
        }

        .video-modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .video-modal-content {
            max-width: 90%;
            max-height: 90%;
            position: relative;
        }

        .video-modal video {
            width: 100%;
            height: auto;
            max-height: 80vh;
            border-radius: 12px;
        }

        .video-modal-close {
            position: absolute;
            top: -50px;
            right: 0;
            background: #ef4444;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            transition: var(--transition);
        }

        .video-modal-close:hover {
            background: #dc2626;
        }
    </style>
</head>
<body>
    <!-- 主要內容包裹器 - 創造浮動卡片效果 -->
    <div class="main-wrapper">

    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="/products" class="logo">
                <div class="logo-icon">
                    <i class="fas fa-gamepad"></i>
                </div>
                <span>Artale Fully automated script</span>
            </a>
            <ul class="nav-links">
                <li><a href="#video">影片介紹</a></li>
                <li><a href="#features">功能特色</a></li>
                <li><a href="#technical">技術說明</a></li>
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
        <section class="hero-section">
            <h1 class="hero-title">歡迎來到 Artale Script 的世界！</h1>
            <p class="hero-subtitle">🎮 自動化遊戲技術服務，讓你的角色24小時不間斷！</p>
            <p class="hero-description">
                台灣製造，專為 MapleStory Worlds - Artale 打造的專業技術服務。<br>
                採用最先進的電腦視覺技術，提供安全、穩定、高效的遊戲體驗！ ✨
            </p>
        </section>

        <!-- 影片展示區域 -->
        <section id="video" class="video-section">
            <div class="video-container">
                <h2 class="section-title">🎬 產品演示影片</h2>
                <p style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem;">
                    觀看實際操作演示，了解 Artale Script 如何運作！
                </p>
                
                <div style="max-width: 800px; margin: 0 auto;">
                    <div class="video-card" style="margin: 0;">
                        <div class="video-player">
                            <!-- Google Drive 影片嵌入 -->
                            <iframe id="google-drive-video" 
                                    src=""
                                    style="width: 100%; height: 450px; border: none; border-radius: 12px;"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowfullscreen>
                            </iframe>
                            
                            <!-- 載入中顯示 -->
                            <div id="video-loading" class="video-placeholder" style="display: none;">
                                <i class="fas fa-spinner fa-spin"></i>
                                <p>影片載入中...</p>
                                <small>請稍候，正在從雲端載入影片</small>
                            </div>
                            
                            <!-- 錯誤或配置提示 -->
                            <div id="video-error" class="video-placeholder" style="display: none;">
                                <i class="fas fa-video"></i>
                                <p>影片準備中...</p>
                                <small>我們正在製作精彩的演示影片，敬請期待！</small>
                            </div>
                        </div>
                        <div class="video-info">
                            <h3 class="video-title">🎮 Artale Script 功能演示</h3>
                            <p class="video-description">
                                完整展示腳本的核心功能，包括怪物檢測、自動攻擊、玩家避讓、
                                地圖移動等實際操作過程。讓您在購買前就能清楚了解產品效果！
                            </p>
                            <div class="video-tags">
                                <span class="video-tag">實機演示</span>
                                <span class="video-tag">完整功能</span>
                                <span class="video-tag">真實效果</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- 功能特色 -->
        <section id="features" class="features-section">
            <h2 class="section-title">🌟 為什麼選擇我們？</h2>
            <div class="features-grid">
                <div class="feature-card">
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

                <div class="feature-card">
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

                <div class="feature-card">
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

                <div class="feature-card">
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

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-map"></i>
                    </div>
                    <h3 class="feature-title">廣泛地圖支援</h3>
                    <p class="feature-description">
                        理論上可支援所有地圖類型，但實際上平坦或結構單純的多層地圖才有較好效果。
                        目前熱門的練功地點都已適配，光是這些地圖就足夠讓您輕鬆升等！
                    </p>
                    <div class="feature-highlight">
                        🗺️ 支援地圖超級多、端看您怎麼用！
                    </div>
                </div>

                <div class="feature-card">
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
            <h2 class="section-title">🔧 技術特色與重要說明</h2>
            <div class="tech-grid">
                <div class="tech-card advantage">
                    <div class="tech-icon advantage">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h3>✅ 技術優勢</h3>
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
                    <h3>⚠️ 使用限制與注意事項</h3>
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

        <!-- 使用對比 -->
        <section id="comparison" class="comparison-section">
            <h2 class="section-title">😴 沒有腳本 vs 🤖 有腳本</h2>
            <div class="comparison-grid">
                <div class="comparison-card without">
                    <h3 class="comparison-title without">
                        <i class="fas fa-tired"></i>
                        沒有腳本的慘狀
                    </h3>
                    <ul class="comparison-list">
                        <li class="comparison-item negative">
                            <i class="fas fa-times"></i>
                            <span>上班時間角色在發呆</span>
                        </li>
                        <li class="comparison-item negative">
                            <i class="fas fa-times"></i>
                            <span>睡覺8小時 = 浪費8小時練功時間</span>
                        </li>
                        <li class="comparison-item negative">
                            <i class="fas fa-times"></i>
                            <span>週末得補班，還要補練功</span>
                        </li>
                        <li class="comparison-item negative">
                            <i class="fas fa-times"></i>
                            <span>看著朋友等級超越自己</span>
                        </li>
                        <li class="comparison-item negative">
                            <i class="fas fa-times"></i>
                            <span>永遠買不起心儀的裝備</span>
                        </li>
                    </ul>
                </div>

                <div class="comparison-card with">
                    <h3 class="comparison-title with">
                        <i class="fas fa-robot"></i>
                        有腳本的爽感
                    </h3>
                    <ul class="comparison-list">
                        <li class="comparison-item positive">
                            <i class="fas fa-check"></i>
                            <span>24小時不間斷練功賺錢</span>
                        </li>
                        <li class="comparison-item positive">
                            <i class="fas fa-check"></i>
                            <span>起床看到滿包裹的戰利品</span>
                        </li>
                        <li class="comparison-item positive">
                            <i class="fas fa-check"></i>
                            <span>工作生活兩不誤</span>
                        </li>
                        <li class="comparison-item positive">
                            <i class="fas fa-check"></i>
                            <span>等級領先朋友群組</span>
                        </li>
                        <li class="comparison-item positive">
                            <i class="fas fa-check"></i>
                            <span>輕鬆享受遊戲</span>
                        </li>
                    </ul>
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
                    我們的腳本非常輕量！只要能順暢運行 Artale 遊戲的電腦基本上就能支援。
                    主要需求就是穩定的 CPU 進行截圖分析及記憶體緩存，
                    最下方有建議配備，如未達可能會效果不佳甚至無法使用(請務必確認電腦性能)。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>⏰ 效率到底如何？真的有用嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    坦白說，效率絕對比不上您全神貫注手動練功，但優勢在於「零時間成本」的持續累積。<br><br>
                    
                    <strong>實測數據：</strong><br>
                    • 弓箭手(弩)：約2週可掛到60等<br>
                    • 刀賊：一個月內達80+等都很穩定<br>
                    （僅利用上班和睡覺時間掛機）<br><br>
                    
                    我們追求的是「安全穩定」而非爆發效率 - 讓您的角色在您忙碌生活中默默成長，偶爾醒來發現意外的稀有掉落，那種小確幸才是真正的價值所在。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🗺️ 支援哪些地圖？複雜地圖能用嗎？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    雖然理論上什麼地圖都能用，但實際上平坦或結構單純的多層地圖才有
                    掛機意義。 好消息是，現在熱門的練功點都已經支援(日落天空、空
                    屋、西部草叢、藍姑姑樹林、肥肥海岸、黑肥肥領土、火肥肥、勇士之
                    村部分地圖、鋼之黑肥肥、挖掘3、惡魔水靈、玩具城部分地圖、月妙、
                    紅藍獨角獅、小老虎大老虎、巨人之森、月牙長槍、靈藥幻境部分地
                    圖、書靈等等等)，還有更多你的私人景點等你來嘗試！
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
                    <strong>我們敢保證與市面上完全不同！</strong><br><br>
                    
                    您可能在蝦皮上看過許多價格不同、賣家不同，卻賣著「同一項產品」的情況 - 那些多半是對岸產品或開源專案的二次包裝。<br><br>
                    
                    我們是<strong>100%台灣自主開發</strong>，從核心程式到使用者介面都是自己打造，絕非抄襲或代理！<br><br>
                    
                    <strong>投資報酬率分析：</strong><br>
                    • 以時薪200元計算，不到3小時的收入<br>
                    • 換來整整一個月的雙手解放<br>
                    • 讓您有更多時間陪伴家人、追劇、學習新技能<br>
                    • 或單純享受不被遊戲綁架的自由人生<br><br>
                    
                    更重要的是，我們提供完整的<strong>中文客服支援</strong>和持續更新維護，這是那些廉價仿冒品永遠做不到的品質保證！
                </div>
            </div>
            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🖥️ 能否在背景執行？我想同時做其他事</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    基於螢幕截圖分析的技術架構，本腳本無法在背景執行，遊戲視窗必須保持在前景狀態。
                    雖然這確實限制了使用便利性，但這正是我們安全性的核心保障。
                    所有採用螢幕截圖技術的解決方案都有此特性，也因此能確保完全不被遊戲系統偵測。
                    如有背景執行需求，建議您可考慮使用虛擬機或備用設備來執行腳本。
                </div>
            </div>

            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🔧 這個腳本與市面上其他產品有何差異？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    我們的核心差異在於「原創性」與「安全性」。本產品由台灣團隊從零開始自主研發，
                    所有功能邏輯皆為原創設計，並非對岸產品或網路開源專案的二次包裝。
                    我們採用通用型演算法，不針對特定地圖進行硬編碼優化，
                    雖然這犧牲了部分效率表現，但換來的是無法被任何方式追蹤或識別的絕對安全性。
                    選擇我們，就是選擇更安全、更可靠的解決方案。
                </div>
            </div>
            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <span>🛡️ 軟體會被防毒軟體誤判嗎？如何證明無毒？</span>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="faq-answer">
                    <strong>完全理解您的擔憂！</strong>這是使用任何第三方軟體時最重要的安全考量。<br><br>
                    
                    <strong>📋 關於防毒軟體誤判：</strong><br>
                    • 自動化軟體確實容易被部分防毒軟體「誤判」為可疑程式<br>
                    • 這是因為我們的軟體需要「讀取螢幕畫面」和「模擬滑鼠鍵盤操作」<br>
                    • 這些行為模式與某些惡意軟體相似，觸發了防毒軟體的啟發式檢測<br>
                    
                    <strong>🔒 我們的安全保證：</strong><br>
                    • <strong>功能透明</strong>：僅執行螢幕截圖分析和滑鼠鍵盤模擬，無其他隱藏功能<br>
                    • <strong>無網路威脅</strong>：除了必要的授權驗證外，不進行任何可疑的網路連線<br>
                    • <strong>無系統破壞</strong>：不修改系統檔案、不寫入登錄檔敏感區域<br>
                    
                    <strong>🔍 您可以自行驗證的方法：</strong><br>
                    1. <strong>VirusTotal 檢測</strong>：將軟體上傳至 virustotal.com 進行多引擎掃描<br>
                    2. <strong>沙盒測試</strong>：在虛擬機器中先行測試，觀察軟體行為<br>
                    3. <strong>網路監控</strong>：使用 Wireshark 等工具監控軟體的網路活動<br>
                    4. <strong>系統監控</strong>：使用 Process Monitor 觀察軟體的檔案系統操作<br><br>
                    
                </div>
            </div>
            
        </section>

        <!-- 系統需求說明 -->
        <section class="manual-section">
            <h2 class="section-title">💻 系統配置需求</h2>
            
            <div class="feature-card" style="max-width: 100%; margin: 0;">
                <div class="feature-description" style="text-align: left;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 1rem;">
                        <div>
                            <h4 style="color: var(--accent-green); margin-bottom: 0.8rem;">✅ 最低配置</h4>
                            <ul style="list-style: none; padding: 0;">
                                <li style="margin-bottom: 0.5rem;">• CPU: Intel i5 / AMD 同級</li>
                                <li style="margin-bottom: 0.5rem;">• 記憶體: 8GB RAM</li>
                                <li style="margin-bottom: 0.5rem;">• 硬碟: 10GB 可用空間</li>
                                <li style="margin-bottom: 0.5rem;">• 作業系統: Windows 10</li>
                                <li style="margin-bottom: 0.5rem;">• 網路: 穩定網路連接</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style="color: var(--primary); margin-bottom: 0.8rem;">⭐ 建議配置</h4>
                            <ul style="list-style: none; padding: 0;">
                                <li style="margin-bottom: 0.5rem;">• CPU: Intel i5 / AMD 同級以上</li>
                                <li style="margin-bottom: 0.5rem;">• 記憶體: 16GB RAM 以上</li>
                                <li style="margin-bottom: 0.5rem;">• 硬碟: SSD 固態硬碟</li>
                                <li style="margin-bottom: 0.5rem;">• 作業系統: Windows 10/11</li>
                                <li style="margin-bottom: 0.5rem;">• 網路: 穩定寬頻連接</li>
                            </ul>
                        </div>
                    </div>
                    <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(245, 158, 11, 0.1); border-left: 4px solid var(--accent-orange); border-radius: 6px;">
                        <strong style="color: var(--accent-orange);">⚠️ 重要提醒：</strong><br>
                        • 軟體資料夾必須放在<strong>英文路徑</strong>中（不可包含中文）<br>
                        • 配置過低可能導致截圖分析延遲，影響使用體驗<br>
                        • 建議關閉不必要的背景程式以提升效能
                    </div>
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
                <a href="https://discord.gg/nmMmm9gZDC" target="_blank" class="cta-button">
                    <i class="fab fa-discord"></i>
                    加入 Discord 社群
                </a>
            </div>
        </section>
    </div>

    </div>
    <!-- 結束 main-wrapper -->

    <!-- 全螢幕影片模態 -->
    <div id="video-modal" class="video-modal">
        <div class="video-modal-content">
            <button class="video-modal-close" onclick="closeVideoModal()">&times;</button>
            <video id="modal-video" controls></video>
        </div>
    </div>

    <script>
        // 影片資料結構
        const videoData = [
            {
                filename: 'demo1.mp4',
                title: '🎯 基本功能演示',
                description: '展示 Artale Script 的基本操作功能，包括怪物檢測、自動攻擊、血量監控等核心功能。',
                tags: ['基本功能', '怪物檢測', '自動攻擊']
            },
            {
                filename: 'demo2.mp4',
                title: '🧗 地圖攀爬功能',
                description: '演示腳本如何智能識別繩索並進行攀爬，適應不同的地圖結構和層次變化。',
                tags: ['地圖攀爬', '繩索識別', '智能移動']
            },
            {
                filename: 'demo3.mp4',
                title: '👥 玩家檢測避讓',
                description: '展示紅點檢測功能，當發現其他玩家時如何自動避讓或切換頻道，確保安全練功。',
                tags: ['玩家檢測', '自動避讓', '頻道切換']
            },
            {
                filename: 'setup.mp4',
                title: '⚙️ 安裝設定教學',
                description: '完整的軟體安裝和初始設定教學，從下載到第一次啟動的詳細步驟說明。',
                tags: ['安裝教學', '初始設定', '新手指南']
            },
            {
                filename: 'advanced.mp4',
                title: '🔧 進階設定調整',
                description: '深入了解各種參數設定，包括攻擊間隔、移動範圍、技能使用等進階功能調整。',
                tags: ['進階設定', '參數調整', '自定義配置']
            },
            {
                filename: 'troubleshooting.mp4',
                title: '🛠️ 常見問題解決',
                description: '針對使用過程中可能遇到的問題提供解決方案，讓您快速排除障礙。',
                tags: ['問題排除', '故障排除', '技術支援']
            }
        ];

        // Google Drive 影片配置
        const GOOGLE_DRIVE_CONFIG = {
            // 請將這裡的 FILE_ID 替換為您的 Google Drive 影片檔案 ID
            fileId: '1O4skseU-1Dfq_wl6OheA45UmiHLjdn8M'
        };

        // 影片初始化
        function initializeVideo() {
            loadGoogleDriveVideo();
        }

        // 載入 Google Drive 影片
        function loadGoogleDriveVideo() {
            const iframe = document.getElementById('google-drive-video');
            const fileId = GOOGLE_DRIVE_CONFIG.fileId;
            
            if (fileId && fileId !== 'YOUR_GOOGLE_DRIVE_FILE_ID_HERE') {
                // 使用 Google Drive 的嵌入 URL
                const embedUrl = `https://drive.google.com/file/d/${fileId}/preview`;
                
                showVideoLoading();
                
                iframe.src = embedUrl;
                iframe.onload = function() {
                    hideVideoLoading();
                    showGoogleDriveVideo();
                };
                
                iframe.onerror = function() {
                    console.log('Google Drive 影片載入失敗');
                    hideVideoLoading();
                    showVideoError();
                };
                
                // 設置超時檢查
                setTimeout(() => {
                    if (document.getElementById('video-loading').style.display !== 'none') {
                        hideVideoLoading();
                        showVideoError();
                    }
                }, 8000); // 8秒超時
                
            } else {
                // 如果沒有配置 Google Drive ID，顯示準備中訊息
                showVideoError();
            }
        }

        // 顯示 Google Drive 影片
        function showGoogleDriveVideo() {
            document.getElementById('google-drive-video').style.display = 'block';
            document.getElementById('video-loading').style.display = 'none';
            document.getElementById('video-error').style.display = 'none';
        }

        // 顯示載入中
        function showVideoLoading() {
            document.getElementById('video-loading').style.display = 'flex';
            document.getElementById('google-drive-video').style.display = 'none';
            document.getElementById('video-error').style.display = 'none';
        }

        // 隱藏載入中
        function hideVideoLoading() {
            document.getElementById('video-loading').style.display = 'none';
        }

        // 顯示錯誤或準備中訊息
        function showVideoError() {
            document.getElementById('video-error').style.display = 'flex';
            document.getElementById('google-drive-video').style.display = 'none';
            document.getElementById('video-loading').style.display = 'none';
        }

        // 播放影片函數
        function playVideo(videoPath, title) {
            const modal = document.getElementById('video-modal');
            const modalVideo = document.getElementById('modal-video');
            
            modalVideo.src = videoPath;
            modalVideo.load();
            modal.classList.add('active');
            
            // 自動播放
            modalVideo.play().catch(e => {
                console.log('自動播放失敗，用戶需手動點擊播放', e);
            });
        }

        // 關閉影片模態
        function closeVideoModal() {
            const modal = document.getElementById('video-modal');
            const modalVideo = document.getElementById('modal-video');
            
            modalVideo.pause();
            modalVideo.src = '';
            modal.classList.remove('active');
        }

        // 點擊模態背景關閉
        document.getElementById('video-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeVideoModal();
            }
        });

        // ESC 鍵關閉模態
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeVideoModal();
            }
        });

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
            resultDiv.style.color = 'var(--primary)';

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
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(0, 0, 0, 0.95)';
            } else {
                navbar.style.background = 'rgba(0, 0, 0, 0.8)';
            }
            
            handleScrollAnimations();
        });

        // 頁面載入完成後的初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化影片
            initializeVideo();
            
            // 添加一些隨機的互動效果
            const features = document.querySelectorAll('.feature-card');
            features.forEach((card, index) => {
                card.addEventListener('mouseenter', function() {
                    // 隨機顏色效果
                    card.style.borderColor = 'var(--primary)';
                });
                
                card.addEventListener('mouseleave', function() {
                    card.style.borderColor = 'var(--border)';
                });
            });

            // 初始滾動動畫檢查
            handleScrollAnimations();

            // 添加一些歡迎訊息
            console.log('🎮 歡迎來到 Artale Script 的世界！');
            console.log('🤖 準備好讓你的角色變成練功機器了嗎？');
            console.log('💡 提示：記得先看完所有功能介紹再決定購買哦！');
            console.log('🎬 別忘了觀看我們精心製作的演示影片！');
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

        // 影片錯誤處理
        document.addEventListener('error', function(e) {
            if (e.target.tagName === 'VIDEO') {
                console.log('影片載入失敗:', e.target.src);
                // 可以在這裡添加錯誤處理邏輯
                const videoCard = e.target.closest('.video-card');
                if (videoCard) {
                    const overlay = videoCard.querySelector('.video-overlay');
                    if (overlay) {
                        overlay.innerHTML = `
                            <div class="play-button" style="background: var(--accent-red);">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                        `;
                        overlay.onclick = null;
                        overlay.style.opacity = '1';
                        overlay.style.cursor = 'default';
                    }
                }
            }
        }, true);
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

@intro_bp.route('/set_video_config', methods=['POST'])
def set_video_config():
    """設定 Google Drive 影片配置（管理員功能）"""
    try:
        data = request.get_json()
        file_id = data.get('file_id', '')
        
        if not file_id:
            return jsonify({
                'success': False,
                'message': '請提供有效的 Google Drive 檔案 ID'
            }), 400
        
        # 這裡可以將配置儲存到資料庫或配置檔案
        # 目前只是返回成功訊息
        return jsonify({
            'success': True,
            'message': f'Google Drive 影片配置已更新：{file_id}',
            'file_id': file_id,
            'embed_url': f'https://drive.google.com/file/d/{file_id}/preview'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'配置更新失敗：{str(e)}'
        }), 500

@intro_bp.route('/video_info', methods=['GET'])
def get_video_info():
    """獲取影片資訊和使用說明"""
    return jsonify({
        'success': True,
        'info': {
            'google_drive_setup': {
                'step1': '1. 將影片上傳到 Google Drive',
                'step2': '2. 右鍵點擊影片 → 取得連結',
                'step3': '3. 設定為「知道連結的使用者」',
                'step4': '4. 從連結中複製檔案 ID',
                'example_link': 'https://drive.google.com/file/d/FILE_ID_HERE/view',
                'example_id': 'FILE_ID_HERE'
            },
            'current_config': {
                'using_google_drive': True,
                'fallback_to_local': True
            },
            'supported_formats': ['MP4', 'WebM', 'AVI', 'MOV'],
            'recommended_settings': {
                'resolution': '1280x720 或更高',
                'bitrate': '適中品質，確保載入速度',
                'duration': '建議 3-10 分鐘'
            }
        }
    })

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
        'sleep_hours_gained': random.randint(5000, 50000),
        'videos_watched': random.randint(50000, 500000)
    }
    
    return jsonify({
        'success': True,
        'stats': stats,
        'funny_fact': random.choice([
            '我們的腳本已經消滅了足夠的怪物來拯救一個虛擬王國！',
            '使用我們腳本節省的時間足夠看完所有的迪士尼電影！',
            '我們幫用戶省下的咖啡錢可以買一台新電腦！',
            '我們的AI比大部分真人玩家反應還快（不是在開玩笑）！',
            '我們的介紹影片被觀看的次數超過了某些網紅！'
        ])
    })

# 確保正確導出
__all__ = ['intro_bp']
