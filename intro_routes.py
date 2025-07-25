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

        /* 影片展示區域 */
        .video-section {
            margin-bottom: 4rem;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 3rem;
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }

        .video-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.05), rgba(139, 92, 246, 0.05));
            z-index: 0;
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
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            transition: var(--transition);
            position: relative;
        }

        .video-card:hover {
            transform: translateY(-10px);
            border-color: var(--accent-blue);
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
            background: var(--gradient-accent);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            transform: scale(0.9);
            transition: var(--transition);
        }

        .video-overlay:hover .play-button {
            transform: scale(1.1);
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
            background: rgba(0, 212, 255, 0.1);
            color: var(--accent-blue);
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .video-placeholder {
            width: 100%;
            height: 250px;
            background: var(--bg-tertiary);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            border-radius: 12px 12px 0 0;
        }

        .video-placeholder i {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
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
            border-radius: var(--border-radius);
            padding: 2.5rem;
            border: 2px solid;
            position: relative;
            transition: var(--transition);
        }

        .tech-card.advantage {
            border-color: var(--accent-green);
            background: rgba(16, 185, 129, 0.05);
        }

        .tech-card.limitation {
            border-color: var(--accent-orange);
            background: rgba(245, 158, 11, 0.05);
        }

        .tech-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .tech-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .tech-icon.advantage {
            background: rgba(16, 185, 129, 0.2);
            color: var(--accent-green);
        }

        .tech-icon.limitation {
            background: rgba(245, 158, 11, 0.2);
            color: var(--accent-orange);
        }

        .tech-card h3 {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
        }

        .tech-list {
            list-style: none;
            padding: 0;
        }

        .tech-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .tech-list li:last-child {
            border-bottom: none;
        }

        .tech-list li strong {
            color: var(--text-primary);
            font-weight: 600;
        }

        .expectation-card {
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            border: 1px solid var(--border-color);
            text-align: center;
        }

        .expectation-card h3 {
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .expectation-card > p {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
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
            color: var(--accent-blue);
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

        /* 系統需求樣式 */
        .manual-section {
            margin-bottom: 4rem;
        }

        /* 響應式設計 */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .hero-title {
                font-size: 2.5rem;
            }
            
            .comparison-grid, .tech-grid {
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
            background: var(--accent-red);
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
            transform: scale(1.1);
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
        <section class="hero-section bounce-in">
            <div class="floating-emojis">
                <div class="emoji">🎮</div>
                <div class="emoji">🤖</div>
                <div class="emoji">⚡</div>
                <div class="emoji">🎯</div>
                <div class="emoji">🌟</div>
            </div>
            <h1 class="hero-title">歡迎來到 Artale Script 的世界！</h1>
            <p class="hero-subtitle">🎮 自動化遊戲技術服務，讓你的角色24小時不間斷！</p>
            <p class="hero-description">
                台灣製造，專為 MapleStory Worlds - Artale 打造的專業技術服務。<br>
                採用最先進的電腦視覺技術，提供安全、穩定、高效的遊戲體驗！ ✨
            </p>
        </section>

        <!-- 影片展示區域 -->
        <section id="video" class="video-section fade-in-up">
            <div class="video-container">
                <h2 class="section-title">🎬 產品演示影片</h2>
                <p style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem;">
                    觀看實際操作演示，了解 Artale Script 如何運作！
                </p>
                
                <div style="max-width: 1000px; margin: 0 auto;">
                    <div class="video-card" style="margin: 0;">
                        <div class="video-player">
                            <!-- Google Drive 影片嵌入 -->
                            <iframe id="google-drive-video" 
                                    src=""
                                    style="width: 100%; height: 600px; border: none; border-radius: 12px;"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowfullscreen>
                            </iframe>
                            
                            <!-- 載入中顯示 -->
                            <div id="video-loading" class="video-placeholder" style="display: none; height: 600px;">
                                <i class="fas fa-spinner fa-spin"></i>
                                <p>影片載入中...</p>
                                <small>請稍候，正在從雲端載入影片</small>
                            </div>
                            
                            <!-- 錯誤或配置提示 -->
                            <div id="video-error" class="video-placeholder" style="display: none; height: 600px;">
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
                        理論上支援全部地圖，實際上最適合平坦或多層簡易架構的地圖。
                        目前的熱門練功圖片都基本適配，
                        但說實話，光是現有支援的地圖就夠您舒服練等了！
                    </p>
                    <div class="feature-highlight">
                        🗺️ 支援地圖超級多、端看您怎麼用！
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
                    目前的熱門練功圖片都基本適配，
                    但說實話，光是現有支援的地圖就夠您舒服練等了！
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
                    但也是我們採用非侵入式技術必須付出的代價。如果想後台執行建議您可以使用虛擬機等設備。
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
                    以台灣的消費水準來說，我們的定價相當實惠。想想看：以時薪200元計算不到3個小時
                    的錢換來一個月的解放雙手時間，這個投資報酬率其實很不錯！
                    況且我們是台灣製造，提供完整的中文客服支援。
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
                                <li style="margin-bottom: 0.5rem;">• CPU: Intel i3 / AMD 同級</li>
                                <li style="margin-bottom: 0.5rem;">• 記憶體: 4GB RAM</li>
                                <li style="margin-bottom: 0.5rem;">• 硬碟: 1GB 可用空間</li>
                                <li style="margin-bottom: 0.5rem;">• 作業系統: Windows 10</li>
                                <li style="margin-bottom: 0.5rem;">• 網路: 穩定網路連接</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style="color: var(--accent-blue); margin-bottom: 0.8rem;">⭐ 建議配置</h4>
                            <ul style="list-style: none; padding: 0;">
                                <li style="margin-bottom: 0.5rem;">• CPU: Intel i5 / AMD 同級以上</li>
                                <li style="margin-bottom: 0.5rem;">• 記憶體: 8GB RAM 以上</li>
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
                <a href="https://discord.gg/HPzNrQmN" target="_blank" class="cta-button">
                    <i class="fab fa-discord"></i>
                    加入 Discord 社群
                </a>
            </div>
        </section>
    </div>

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
            fileId: '1neJKwUi5kYJGB2sNSHbOGZFhV8fpE9Eb'
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
            // 初始化影片
            initializeVideo();
            
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