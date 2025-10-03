# templates.py - 專業高級版本
PROFESSIONAL_PRODUCTS_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scrilab - Python 遊戲技術服務</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
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
            background: #1a1a1a; /* 深灰色外層背景 - 改回正常顏色 */
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* 主要內容容器 - 浮動卡片效果 */
        .main-wrapper {
            max-width: 1200px; /* 改小讓更多螢幕能看到分層 */
            margin: 0 auto;
            background: var(--bg-primary); /* 純黑色內容區 */
            border-left: 1px solid rgba(255, 255, 255, 0.05);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 0 80px rgba(0, 0, 0, 0.8);
        }

        /* Navigation - 固定在頂部，跨越全寬 */
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 26, 0.95); /* 配合外層背景 */
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
            max-width: 1200px; /* 配合 main-wrapper */
            height: 1px;
            background: var(--border);
        }

        .nav-container {
            max-width: 1200px; /* 配合 main-wrapper */
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

        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 0 3rem;
        }

        .hero-content {
            max-width: 1200px;
            margin: 0 auto;
            padding-top: 4rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
        }

        .hero-text {
            /* 左側文字區 */
        }

        .hero-visual {
            /* 右側視覺區 */
            position: relative;
            height: 500px;
        }

        /* 程式碼終端機效果 */
        .code-terminal {
            background: #0d1117;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--radius);
            padding: 1.5rem;
            height: 100%;
            overflow: hidden;
            position: relative;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .code-terminal::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 40px;
            background: #161b22;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .terminal-header {
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }

        .terminal-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ff5f57;
        }

        .terminal-dot:nth-child(2) {
            background: #febc2e;
        }

        .terminal-dot:nth-child(3) {
            background: #28c840;
        }

        .terminal-title {
            margin-left: auto;
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: 'Courier New', monospace;
        }

        .code-content {
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            line-height: 1.8;
            color: #c9d1d9;
        }

        .code-line {
            display: block;
            white-space: pre;
            opacity: 0;
            animation: fadeInLine 0.3s ease-out forwards;
        }

        @keyframes fadeInLine {
            from {
                opacity: 0;
                transform: translateX(-10px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        /* 語法高亮 */
        .keyword { color: #ff7b72; }
        .function { color: #d2a8ff; }
        .string { color: #a5d6ff; }
        .comment { color: #8b949e; }
        .number { color: #79c0ff; }
        .class { color: #ffa657; }

        /* 游標閃爍 */
        .cursor {
            display: inline-block;
            width: 8px;
            height: 16px;
            background: var(--primary);
            margin-left: 2px;
            animation: blink 1s step-end infinite;
        }

        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }

        .hero h1 {
            font-size: clamp(2.5rem, 6vw, 4rem);
            font-weight: 700;
            margin-bottom: 1.5rem;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }

        .hero .highlight {
            color: var(--primary);
        }

        .hero p {
            font-size: 1.125rem;
            color: var(--text-secondary);
            margin-bottom: 2.5rem;
            max-width: 600px;
            line-height: 1.7;
        }

        .hero-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        /* 按鈕系統 - 簡化版 */
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.875rem;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
            cursor: pointer;
            border: none;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            border-color: var(--border-hover);
            background: var(--bg-elevated);
        }

        /* Sections */
        .section {
            padding: 6rem 3rem;
        }

        .section-alt {
            background: var(--bg-secondary);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .section-header {
            text-align: center;
            margin-bottom: 4rem;
        }

        .section-badge {
            display: inline-block;
            background: var(--primary-light);
            border: 1px solid var(--primary-border);
            color: var(--primary);
            padding: 0.375rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }

        .section-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }

        .section-description {
            font-size: 1.125rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }

        /* Games Grid */
        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }

        .game-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            transition: var(--transition);
            cursor: pointer;
        }

        .game-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .game-card.coming-soon {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .game-card.coming-soon:hover {
            transform: none;
        }

        .game-image {
            position: relative;
            width: 100%;
            height: 200px;
            overflow: hidden;
            background: var(--bg-elevated);
        }

        .game-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: var(--transition);
        }

        .game-card:hover .game-image img {
            transform: scale(1.02);
        }

        .game-info {
            padding: 1.5rem;
        }

        .game-info h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .game-subtitle {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .game-description {
            color: var(--text-secondary);
            font-size: 0.9375rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
            padding: 0.375rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }

        .status-badge.active {
            background: var(--success-light);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-badge.coming {
            background: var(--warning-light);
            color: var(--warning);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .enter-game-btn {
            width: 100%;
            background: var(--primary);
            color: white;
            padding: 0.875rem;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.9375rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: var(--transition);
            border: none;
            cursor: pointer;
        }

        .enter-game-btn:hover {
            background: var(--primary-hover);
        }

        /* Resources Section */
        .resources-section {
            margin: 3rem 0 4rem;
        }

        .resources-title {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }

        .resources-subtitle {
            text-align: center;
            font-size: 1rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .resources-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
        }

        .resource-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            text-align: center;
            transition: var(--transition);
            text-decoration: none;
            display: block;
        }

        .resource-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }

        .resource-icon {
            width: 48px;
            height: 48px;
            background: var(--primary-light);
            border: 1px solid var(--primary-border);
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.25rem;
            color: var(--primary);
        }

        .resource-card h3 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .resource-card p {
            color: var(--text-secondary);
            font-size: 0.875rem;
            line-height: 1.5;
        }

        /* Service Cards */
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
        }

        .service-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            transition: var(--transition);
        }

        .service-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }

        .service-header {
            padding: 2rem 1.5rem 1.5rem;
            background: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
        }

        .service-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .service-subtitle {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 1.5rem;
        }

        .service-price {
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .service-price .currency {
            font-size: 1rem;
            color: var(--text-secondary);
        }

        .service-price .amount {
            font-size: 2.5rem;
            font-weight: 700;
        }

        .service-price .period {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .payment-info {
            background: var(--primary-light);
            border: 1px solid var(--primary-border);
            border-radius: var(--radius);
            padding: 0.75rem;
            margin-top: 1rem;
            font-size: 0.8125rem;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .service-body {
            padding: 1.5rem;
        }

        .service-features {
            list-style: none;
            margin-bottom: 1.5rem;
        }

        .service-features li {
            padding: 0.75rem 0;
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.875rem;
        }

        .service-features li:last-child {
            border-bottom: none;
        }

        .feature-check {
            color: var(--success);
            font-size: 1rem;
            flex-shrink: 0;
            margin-top: 0.125rem;
        }

        .service-button {
            width: 100%;
            padding: 0.875rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 0.9375rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .service-button:hover {
            background: var(--primary-hover);
        }

        /* Footer */
        .footer {
            background: var(--bg-primary);
            border-top: 1px solid var(--border);
            padding: 3rem 2rem 2rem;
        }

        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
        }

        .footer h3 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }

        .contact-methods {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .contact-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.875rem;
            padding: 0.75rem 1.25rem;
            border-radius: var(--radius);
            background: var(--bg-card);
            border: 1px solid var(--border);
            transition: var(--transition);
        }

        .contact-link:hover {
            border-color: var(--border-hover);
            color: var(--text-primary);
        }

        .footer-note {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-bottom: 2rem;
        }

        .footer-bottom {
            border-top: 1px solid var(--border);
            padding-top: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }

        .footer-links {
            margin-bottom: 1rem;
        }

        .footer-links a {
            color: var(--text-muted);
            text-decoration: none;
            margin: 0 1rem;
            transition: var(--transition);
        }

        .footer-links a:hover {
            color: var(--text-primary);
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(4px);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }

        .modal-content {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            max-width: 480px;
            width: 100%;
            padding: 2rem;
            position: relative;
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
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-close:hover {
            color: var(--text-primary);
        }

        .modal h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }

        .plan-info {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .plan-info h4 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .plan-info p {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 1rem;
        }

        .plan-price {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .plan-period {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .modal-notice {
            background: var(--primary-light);
            border: 1px solid var(--primary-border);
            border-radius: var(--radius);
            padding: 0.875rem;
            margin-bottom: 1rem;
            font-size: 0.8125rem;
            color: var(--primary);
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            line-height: 1.5;
        }

        .modal-notice i {
            flex-shrink: 0;
            margin-top: 0.125rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            cursor: pointer;
            font-size: 0.875rem;
            line-height: 1.5;
        }

        .form-group input[type="checkbox"] {
            margin-top: 0.25rem;
            accent-color: var(--primary);
            cursor: pointer;
        }

        .form-group a {
            color: var(--primary);
            text-decoration: none;
        }

        .form-group a:hover {
            text-decoration: underline;
        }

        .modal-buttons {
            display: flex;
            gap: 0.75rem;
        }

        .btn-cancel {
            flex: 1;
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border);
            padding: 0.875rem;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            transition: var(--transition);
        }

        .btn-cancel:hover {
            border-color: var(--border-hover);
            color: var(--text-primary);
        }

        .btn-submit {
            flex: 2;
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.875rem;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn-submit:hover {
            background: var(--primary-hover);
        }

        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .main-wrapper {
                box-shadow: none;
            }

            .nav-links {
                display: none;
            }

            .nav-container,
            .hero,
            .section {
                padding-left: 1.5rem;
                padding-right: 1.5rem;
            }

            .hero-content {
                grid-template-columns: 1fr;
                gap: 2rem;
            }

            .hero-visual {
                height: 300px;
            }

            .hero h1 {
                font-size: 2rem;
            }

            .section-title {
                font-size: 2rem;
            }

            .games-grid,
            .services-grid,
            .resources-grid {
                grid-template-columns: 1fr;
            }

            .contact-methods {
                flex-direction: column;
                gap: 1rem;
            }

            .modal-buttons {
                flex-direction: column;
            }

            .btn-cancel,
            .btn-submit {
                flex: 1;
            }
        }

        /* 背景程式碼效果 - 精簡版 */
        @keyframes float-code {
            0%, 100% { opacity: 0; transform: translateY(0); }
            10%, 90% { opacity: 0.05; }
            50% { transform: translateY(-20px); }
        }

        .code-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            overflow: hidden;
            font-family: 'Courier New', monospace;
            color: var(--primary);
            font-size: 12px;
            line-height: 1.8;
            opacity: 0.05;
        }

    </style>
</head>
<body>
    <!-- 主要內容包裹器 - 創造浮動卡片效果 -->
    <div class="main-wrapper">

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
                <li><a href="/payment-guide">付款說明</a></li>
                <li><a href="#contact">聯絡我們</a></li>
                <li><a href="/disclaimer">免責聲明</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>專業的<span class="highlight">遊戲技術服務</span><br>為您量身打造</h1>
                <p>Scrilab 提供高效能的自動化遊戲技術服務，協助玩家提升遊戲體驗。透過先進的視覺識別與多線程技術，為您打造個人化的解決方案。</p>
                <div class="hero-buttons">
                    <a href="#games" class="btn btn-primary">
                        <span>瀏覽服務</span>
                        <i class="fas fa-arrow-right"></i>
                    </a>
                    <a href="#contact" class="btn btn-secondary">
                        <i class="fas fa-headset"></i>
                        <span>技術支援</span>
                    </a>
                </div>
            </div>
            
            <div class="hero-visual">
                <div class="code-terminal">
                    <div class="terminal-header">
                        <div class="terminal-dot"></div>
                        <div class="terminal-dot"></div>
                        <div class="terminal-dot"></div>
                        <div class="terminal-title">game_automation.py</div>
                    </div>
                    <div class="code-content" id="code-display">
                        <!-- 程式碼將由 JavaScript 動態生成 -->
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Games Section -->
    <section id="games" class="section section-alt">
        <div class="container">
            <div class="section-header">
                <div class="section-badge">遊戲服務</div>
                <h2 class="section-title">選擇您的遊戲</h2>
                <p class="section-description">我們為各類遊戲提供專業的技術服務方案</p>
            </div>
            
            <div class="games-grid">
                <!-- MapleStory Worlds - Artale -->
                <div class="game-card" onclick="showGamePlans('artale')">
                    <div class="game-image">
                        <img src="/static/images/artale-cover.jpg" alt="MapleStory Worlds - Artale">
                    </div>
                    <div class="game-info">
                        <h3>MapleStory Worlds - Artale</h3>
                        <p class="game-subtitle">繁體中文版</p>
                        <p class="game-description">專為 Artale 玩家設計的全自動化技術服務，提供完整的功能與個人化設定。</p>
                        <span class="status-badge active">
                            <i class="fas fa-circle"></i>
                            服務中
                        </span>
                        <button class="enter-game-btn">
                            <span>查看服務方案</span>
                            <i class="fas fa-arrow-right"></i>
                        </button>
                    </div>
                </div>

                <!-- Coming Soon Games -->
                <div class="game-card coming-soon">
                    <div class="game-image">
                        <img src="/static/images/coming-soon.jpg" alt="更多遊戲即將推出">
                    </div>
                    <div class="game-info">
                        <h3>更多遊戲</h3>
                        <p class="game-subtitle">即將推出</p>
                        <p class="game-description">我們正在為更多遊戲開發專業的技術服務方案。</p>
                        <span class="status-badge coming">
                            <i class="fas fa-clock"></i>
                            開發中
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section id="services" class="section" style="display: none;">
        <div class="container">
            <div class="section-header">
                <button class="btn btn-secondary" onclick="backToGames()" style="margin-bottom: 2rem;">
                    <i class="fas fa-arrow-left"></i>
                    <span>返回遊戲列表</span>
                </button>
                <div class="section-badge">服務方案</div>
                <h2 class="section-title" id="game-plans-title">MapleStory Worlds - Artale</h2>
                <p class="section-description">透過 Gumroad 付款，支援信用卡與 Apple Pay。如不方便使用信用卡，請至 Discord 聯絡管理員使用其他匯款方式。</p>
            </div>
            
            <!-- 資源快捷列 -->
            <div class="resources-section">
                <h3 class="resources-title">遊戲資源</h3>
                <p class="resources-subtitle">查看操作手冊、基本介紹與下載連結</p>
                <div class="resources-grid">
                    <a href="/intro" class="resource-card">
                        <div class="resource-icon">
                            <i class="fas fa-info-circle"></i>
                        </div>
                        <h3>基本介紹</h3>
                        <p>了解服務功能與特色</p>
                    </a>
                    
                    <a href="/manual" class="resource-card">
                        <div class="resource-icon">
                            <i class="fas fa-book"></i>
                        </div>
                        <h3>操作手冊</h3>
                        <p>詳細的使用說明與設定</p>
                    </a>
                    
                    <a href="/download" class="resource-card">
                        <div class="resource-icon">
                            <i class="fas fa-download"></i>
                        </div>
                        <h3>下載連結</h3>
                        <p>取得最新版本的服務程式</p>
                    </a>
                </div>
            </div>
            
            <div class="services-grid">
                <!-- 體驗方案 -->
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-title">體驗服務</div>
                        <div class="service-subtitle">適合新手玩家體驗</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>
                            <span class="amount">199</span>
                            <span class="period">/ 7+1 天</span>
                        </div>
                        <div class="payment-info">
                            <i class="fas fa-shield-alt"></i>
                            <span>透過 Gumroad 安全付款</span>
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
                                <span>技術支援</span>
                            </li>
                        </ul>
                        <button class="service-button" onclick="selectPlan('trial_7')">
                            <span>選擇方案</span>
                        </button>
                    </div>
                </div>

                <!-- 標準方案 -->
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-title">標準服務</div>
                        <div class="service-subtitle">最受歡迎的選擇</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>
                            <span class="amount">399</span>
                            <span class="period">/ 30+3 天</span>
                        </div>
                        <div class="payment-info">
                            <i class="fas fa-shield-alt"></i>
                            <span>透過 Gumroad 安全付款</span>
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
                                <span>技術支援</span>
                            </li>
                        </ul>
                        <button class="service-button" onclick="selectPlan('monthly_30')">
                            <span>選擇方案</span>
                        </button>
                    </div>
                </div>

                <!-- 最佳方案 -->
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-title">最佳服務</div>
                        <div class="service-subtitle">長期使用推薦</div>
                        <div class="service-price">
                            <span class="currency">NT$</span>
                            <span class="amount">999</span>
                            <span class="period">/ 90+10 天</span>
                        </div>
                        <div class="payment-info">
                            <i class="fas fa-shield-alt"></i>
                            <span>透過 Gumroad 安全付款</span>
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
                                <span>技術支援</span>
                            </li>
                        </ul>
                        <button class="service-button" onclick="selectPlan('quarterly_90')">
                            <span>選擇方案</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer id="contact" class="footer">
        <div class="footer-content">
            <h3>聯絡我們</h3>
            <div class="contact-methods">
                <a href="https://discord.gg/nmMmm9gZDC" target="_blank" class="contact-link">
                    <i class="fab fa-discord"></i>
                    <span>Discord 技術支援</span>
                </a>
                <a href="mailto:scrilabstaff@gmail.com" class="contact-link">
                    <i class="fas fa-envelope"></i>
                    <span>scrilabstaff@gmail.com</span>
                </a>
            </div>
            <p class="footer-note">所有技術支援與客服諮詢，請優先透過 Discord 聯繫我們</p>
            
            <div class="footer-bottom">
                <div class="footer-links">
                    <a href="/disclaimer">免責聲明</a>
                </div>
                <p>&copy; 2025 Scrilab. All rights reserved. Made in Taiwan 🇹🇼</p>
            </div>
        </div>
    </footer>

    </div>
    <!-- 結束 main-wrapper -->

    <!-- Purchase Modal -->
    <div id="purchase-modal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <h3>確認購買</h3>
            
            <div id="selected-plan-info" class="plan-info">
                <!-- Plan info will be inserted here -->
            </div>
            
            <div class="modal-notice">
                <i class="fas fa-shield-alt"></i>
                <span>將跳轉至 Gumroad 完成付款，支援信用卡與 Apple Pay</span>
            </div>
            
            <div class="modal-notice">
                <i class="fab fa-discord"></i>
                <span>不方便使用信用卡？請至 Discord 聯絡管理員使用其他匯款方式</span>
            </div>
            
            <div class="modal-notice">
                <i class="fas fa-info-circle"></i>
                <span>購買完成後，序號將自動發送至您的信箱（請同時檢查垃圾郵件）</span>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="agree-terms" required>
                    <span>
                        我已閱讀並同意 <a href="/disclaimer" target="_blank">免責聲明與服務條款</a>，理解使用本服務的風險，並自願承擔相關責任。
                    </span>
                </label>
            </div>
            
            <div class="modal-buttons">
                <button class="btn-cancel" onclick="closeModal()">取消</button>
                <button class="btn-submit" onclick="submitPayment()" id="payment-btn">
                    <span id="payment-btn-text">
                        <span>前往付款</span>
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
                price_twd: 199,
                period: '7+1 天',
                description: '適合新手玩家體驗的基礎技術服務'
            },
            'monthly_30': {
                name: '標準服務',
                price_twd: 399,
                period: '30+3 天',
                description: '最受歡迎的完整技術服務方案'
            },
            'quarterly_90': {
                name: '最佳服務',
                price_twd: 999,
                period: '90+10 天',
                description: '長期使用推薦的全功能技術服務'
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
                <h4>${plan.name}</h4>
                <p>${plan.description}</p>
                <div class="plan-price">NT$ ${plan.price_twd.toLocaleString()}</div>
                <div class="plan-period">服務期限：${plan.period}</div>
            `;
            
            document.getElementById('purchase-modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('purchase-modal').style.display = 'none';
            document.getElementById('agree-terms').checked = false;
            resetPaymentButton();
        }

        function submitPayment() {
            const agreeTerms = document.getElementById('agree-terms').checked;
            
            if (!agreeTerms) {
                alert('請先閱讀並同意免責聲明與服務條款');
                return;
            }
            
            document.getElementById('payment-btn-text').style.display = 'none';
            document.getElementById('payment-loading').style.display = 'inline-block';
            
            submitGumroadPayment();
        }

        async function submitGumroadPayment() {
            try {
                const response = await fetch('/gumroad/create-payment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        plan_id: selectedPlan,
                        user_info: {
                            name: 'Gumroad User',
                            email: 'gumroad@placeholder.com',
                            phone: ''
                        }
                    })
                });

                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.purchase_url;
                } else {
                    alert('付款創建失敗: ' + data.error);
                    resetPaymentButton();
                }
            } catch (error) {
                alert('系統錯誤: ' + error.message);
                resetPaymentButton();
            }
        }

        function resetPaymentButton() {
            document.getElementById('payment-btn-text').style.display = 'inline-flex';
            document.getElementById('payment-loading').style.display = 'none';
        }

        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });

        // Navbar scroll effect
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(0, 0, 0, 0.95)';
            } else {
                navbar.style.background = 'rgba(0, 0, 0, 0.8)';
            }
        });

        // Close modal on outside click
        document.getElementById('purchase-modal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });

        // Hero Code Terminal Animation
        const codeSnippets = [
            `<span class="keyword">import</span> cv2
<span class="keyword">import</span> numpy <span class="keyword">as</span> np
<span class="keyword">import</span> threading
<span class="keyword">from</span> PIL <span class="keyword">import</span> Image

<span class="keyword">class</span> <span class="class">GameBot</span>:
    <span class="keyword">def</span> <span class="function">__init__</span>(self):
        self.running = <span class="keyword">True</span>
        self.config = self.<span class="function">load_config</span>()
    
    <span class="keyword">async def</span> <span class="function">detect_target</span>(self, frame):
        <span class="comment"># 視覺識別處理</span>
        hsv = cv2.<span class="function">cvtColor</span>(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.<span class="function">inRange</span>(hsv, lower, upper)
        <span class="keyword">return</span> <span class="function">len</span>(contours) > <span class="number">0</span>`,
            
            `<span class="keyword">def</span> <span class="function">optimize_performance</span>(self):
    <span class="comment"># 多線程優化</span>
    threads = []
    <span class="keyword">for</span> i <span class="keyword">in</span> <span class="function">range</span>(self.thread_count):
        t = threading.<span class="function">Thread</span>(
            target=self.<span class="function">process_task</span>,
            args=(i,)
        )
        threads.<span class="function">append</span>(t)
        t.<span class="function">start</span>()
    
    <span class="keyword">for</span> t <span class="keyword">in</span> threads:
        t.<span class="function">join</span>()`,

            `<span class="keyword">class</span> <span class="class">AutomationEngine</span>:
    <span class="keyword">def</span> <span class="function">execute_action</span>(self):
        <span class="comment"># 完全隨機性演算法</span>
        delay = random.<span class="function">uniform</span>(<span class="number">0.1</span>, <span class="number">0.3</span>)
        time.<span class="function">sleep</span>(delay)
        
        <span class="keyword">if</span> self.<span class="function">verify_state</span>():
            self.<span class="function">perform_action</span>()
            <span class="keyword">return</span> <span class="keyword">True</span>
        <span class="keyword">return</span> <span class="keyword">False</span>`
        ];

        let currentSnippet = 0;
        
        function displayCode() {
            const codeDisplay = document.getElementById('code-display');
            if (!codeDisplay) return;
            
            const snippet = codeSnippets[currentSnippet];
            const lines = snippet.split('\n');
            
            codeDisplay.innerHTML = '';
            
            lines.forEach((line, index) => {
                setTimeout(() => {
                    const lineElement = document.createElement('span');
                    lineElement.className = 'code-line';
                    lineElement.innerHTML = line;
                    lineElement.style.animationDelay = `${index * 0.1}s`;
                    codeDisplay.appendChild(lineElement);
                    codeDisplay.appendChild(document.createElement('br'));
                    
                    // 在最後一行添加游標
                    if (index === lines.length - 1) {
                        setTimeout(() => {
                            const cursor = document.createElement('span');
                            cursor.className = 'cursor';
                            codeDisplay.appendChild(cursor);
                        }, 100);
                    }
                }, index * 150);
            });
            
            // 循環播放
            currentSnippet = (currentSnippet + 1) % codeSnippets.length;
            setTimeout(displayCode, lines.length * 150 + 4000);
        }

        // 頁面載入後開始動畫
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', displayCode);
        } else {
            displayCode();
        }
    </script>
</body>
</html>
"""

# 付款成功頁面模板（保持不變）
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
            --accent-itchio: #fa5c5c;
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
            border: 2px solid var(--accent-itchio);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .uuid-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--accent-itchio);
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
            border-color: var(--accent-itchio);
        }

        .email-notice {
            background: rgba(250, 92, 92, 0.1);
            border: 1px solid rgba(250, 92, 92, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            font-size: 0.95rem;
            color: var(--accent-itchio);
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
            color: var(--accent-itchio);
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
                <span class="info-value">NT$ {{ payment_record.amount_twd if payment_record else 'N/A' }}</span>
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
            <span>序號已發送至您的信箱，請查收（請同時檢查垃圾郵件）</span>
        </div>
        
        <div class="contact-info">
            <h3 class="contact-title">需要協助？</h3>
            <div class="contact-methods">
                <a href="https://discord.gg/nmMmm9gZDC" target="_blank" class="contact-link">
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
                    setTimeout(() => {
                        btn.innerHTML = originalText;
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
            const amount = "{{ payment_record.amount_twd if payment_record else 'N/A' }}";
            
            const content = `Scrilab Artale 服務購買成功

服務方案：${planName}
服務期限：${planPeriod}
付款金額：NT$ ${amount}
專屬序號：${uuid}

請妥善保管您的序號，避免外洩給他人使用。

操作手冊：請訪問 /manual 查看詳細使用說明

技術支援：
- Discord：https://discord.gg/nmMmm9gZDC
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

# 付款取消頁面模板（保持不變）
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
            border-color: var(--accent-orange);
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
        <p class="cancel-subtitle">您已取消付款流程，如需購買服務，請重新選擇方案。</p>
        
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
        
        <p class="footer-note">如有任何問題，歡迎透過 Discord 或 Email 聯繫我們。</p>
    </div>
</body>
</html>
"""
