"""
payment_guide_routes.py - 付款說明頁面路由
"""
from flask import Blueprint, render_template_string

# 創建付款說明藍圖
payment_guide_bp = Blueprint('payment_guide', __name__, url_prefix='/payment-guide')

# 付款說明頁面 HTML 模板
PAYMENT_GUIDE_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>付款說明 - Scrilab</title>
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

        .nav-links a:hover, .nav-links a.active {
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

        .page-header {
            text-align: center;
            margin-bottom: 4rem;
            padding: 3rem 0;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }

        .page-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: var(--gradient-accent);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .page-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .highlight-badge {
            display: inline-block;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            color: var(--accent-blue);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        /* Steps Container */
        .steps-container {
            display: grid;
            gap: 3rem;
            margin-bottom: 4rem;
        }

        .step-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2.5rem;
            position: relative;
            transition: var(--transition);
        }

        .step-card:hover {
            border-color: var(--accent-blue);
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .step-number {
            position: absolute;
            top: -15px;
            left: 2.5rem;
            width: 40px;
            height: 40px;
            background: var(--gradient-accent);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            color: white;
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        }

        .step-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
            padding-top: 1rem;
        }

        .step-description {
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-bottom: 2rem;
            line-height: 1.7;
        }

        .step-image {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
            border: 2px solid var(--border-color);
            transition: var(--transition);
        }

        .step-image:hover {
            border-color: var(--accent-blue);
            transform: scale(1.02);
        }

        .step-image img {
            width: 100%;
            height: auto;
            display: block;
        }

        /* Warning/Info Boxes */
        .info-box, .warning-box, .success-box {
            border-radius: 12px;
            padding: 1.5rem;
            margin: 2rem 0;
            border-left: 4px solid;
            position: relative;
        }

        .info-box {
            background: rgba(0, 212, 255, 0.1);
            border-left-color: var(--accent-blue);
            border: 1px solid rgba(0, 212, 255, 0.3);
        }

        .warning-box {
            background: rgba(245, 158, 11, 0.1);
            border-left-color: var(--accent-orange);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .success-box {
            background: rgba(16, 185, 129, 0.1);
            border-left-color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
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

        /* Support Section */
        .support-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 3rem;
            text-align: center;
            margin-top: 4rem;
        }

        .support-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .support-description {
            color: var(--text-secondary);
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }

        .support-methods {
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .support-link {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 1.1rem;
            transition: var(--transition);
            padding: 1rem 2rem;
            border-radius: 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            min-width: 180px;
            justify-content: center;
        }

        .support-link:hover {
            color: var(--accent-blue);
            border-color: var(--accent-blue);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        /* Quick Actions */
        .quick-actions {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            margin: 2rem 0;
        }

        .quick-actions h3 {
            color: var(--text-primary);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }

        .action-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .action-btn {
            background: var(--gradient-accent);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .page-title {
                font-size: 2rem;
            }
            
            .nav-links {
                display: none;
            }
            
            .step-card {
                padding: 2rem;
            }
            
            .step-number {
                left: 2rem;
            }
            
            .support-methods {
                flex-direction: column;
                align-items: center;
            }
            
            .action-buttons {
                flex-direction: column;
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
                <li><a href="/payment-guide" class="active">付款說明</a></li>
                <li><a href="/products#contact">聯絡我們</a></li>
                <li><a href="/disclaimer">免責聲明</a></li>
            </ul>
            <a href="/products" class="back-btn">
                <i class="fas fa-arrow-left"></i>
                <span>返回首頁</span>
            </a>
        </div>
    </nav>

    <div class="container">
        <!-- Header -->
        <div class="page-header">
            <h1 class="page-title">付款說明</h1>
            <p class="page-subtitle">透過 Gumroad 安全付款，支援多種付款方式</p>
            <span class="highlight-badge">
                <i class="fas fa-shield-alt"></i>
                安全便捷的國際付款平台
            </span>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
            <h3><i class="fas fa-rocket"></i> 快速開始</h3>
            <div class="action-buttons">
                <a href="/products#games" class="action-btn">
                    <i class="fas fa-shopping-cart"></i>
                    立即選購服務
                </a>
                <a href="#step1" class="action-btn" style="background: var(--bg-tertiary); border: 1px solid var(--border-color);">
                    <i class="fas fa-book"></i>
                    查看付款步驟
                </a>
            </div>
        </div>

        <!-- Payment Steps -->
        <div class="steps-container">
            <!-- Step 1 -->
            <div class="step-card" id="step1">
                <div class="step-number">1</div>
                <h2 class="step-title">選擇服務方案</h2>
                <p class="step-description">
                    在我們的產品頁面中選擇適合您的服務方案。我們提供體驗版（7天）、標準版（30天）和季度版（90天）三種選擇，
                    每種方案都包含完整的遊戲技術服務功能。
                </p>
                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-lightbulb"></i>
                        選購建議
                    </div>
                    <div class="box-content">
                        新用戶建議先選擇體驗版了解服務內容，滿意後再升級到更長期的方案。季度版提供最佳的性價比！
                    </div>
                </div>
                <div class="step-image">
                    <img src="/static/images/payment-step1.jpg" alt="選擇服務方案" loading="lazy">
                </div>
            </div>

            <!-- Step 2 -->
            <div class="step-card" id="step2">
                <div class="step-number">2</div>
                <h2 class="step-title">點擊 Gumroad 付款</h2>
                <p class="step-description">
                    選擇方案後，點擊「Gumroad 付款」按鈕。系統會自動跳轉到 Gumroad 的安全付款頁面。
                    Gumroad 是國際知名的數位產品銷售平台，提供安全可靠的付款環境。
                </p>
                <div class="success-box">
                    <div class="box-title">
                        <i class="fas fa-shield-alt"></i>
                        安全保障
                    </div>
                    <div class="box-content">
                        Gumroad 使用 SSL 加密技術保護您的付款資訊，支援全球主要的付款方式，讓您安心購買。
                    </div>
                </div>
                <div class="step-image">
                    <img src="/static/images/payment-step2.jpg" alt="點擊 Gumroad 付款" loading="lazy">
                </div>
            </div>

            <!-- Step 3 -->
            <div class="step-card" id="step3">
                <div class="step-number">3</div>
                <h2 class="step-title">選擇付款方式</h2>
                <p class="step-description">
                    在 Gumroad 付款頁面，您可以選擇多種付款方式：信用卡、PayPal、Apple Pay、Google Pay 等。
                    填寫必要的付款資訊，確認購買金額和服務內容。
                </p>
                <div class="info-box">
                    <div class="box-title">
                        <i class="fas fa-credit-card"></i>
                        支援的付款方式
                    </div>
                    <div class="box-content">
                        • 信用卡（Visa、Mastercard、American Express）<br>
                        • PayPal 帳戶<br>
                        • Apple Pay（iOS 設備）<br>
                        • Google Pay（Android 設備）<br>
                        • 其他當地付款方式
                    </div>
                </div>
                <div class="step-image">
                    <img src="/static/images/payment-step3.jpg" alt="選擇付款方式" loading="lazy">
                </div>
            </div>

            <!-- Step 4 -->
            <div class="step-card" id="step4">
                <div class="step-number">4</div>
                <h2 class="step-title">完成付款流程</h2>
                <p class="step-description">
                    確認所有資訊無誤後，點擊完成付款。Gumroad 會處理您的付款並發送確認郵件。
                    整個付款過程通常在幾分鐘內完成，您會收到付款成功的通知。
                </p>
                <div class="warning-box">
                    <div class="box-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        注意事項
                    </div>
                    <div class="box-content">
                        請確保您的郵箱地址正確，因為我們會將服務序號發送到您的信箱。同時請檢查垃圾郵件資料夾。
                    </div>
                </div>
                <div class="step-image">
                    <img src="/static/images/payment-step4.jpg" alt="完成付款流程" loading="lazy">
                </div>
            </div>

            <!-- Step 5 -->
            <div class="step-card" id="step5">
                <div class="step-number">5</div>
                <h2 class="step-title">接收服務序號</h2>
                <p class="step-description">
                    付款成功後，系統會自動生成您的專屬服務序號，並發送到您的郵箱。
                    您也可以在付款成功頁面直接查看和複製序號。請妥善保管您的序號。
                </p>
                <div class="success-box">
                    <div class="box-title">
                        <i class="fas fa-check-circle"></i>
                        序號說明
                    </div>
                    <div class="box-content">
                        您的序號格式類似：artale_gumroad_xxx_20240101<br>
                        這是您使用 Scrilab Artale 服務的唯一憑證，請勿分享給他人。
                    </div>
                </div>
                <div class="step-image">
                    <img src="/static/images/payment-step5.jpg" alt="接收服務序號" loading="lazy">
                </div>
            </div>
        </div>

        <!-- Support Section -->
        <div class="support-section">
            <h2 class="support-title">需要協助？</h2>
            <p class="support-description">
                如果您在付款過程中遇到任何問題，或需要技術支援，歡迎透過以下方式聯繫我們
            </p>
            <div class="support-methods">
                <a href="https://discord.gg/HPzNrQmN" target="_blank" class="support-link">
                    <i class="fab fa-discord"></i>
                    <span>Discord 即時支援</span>
                </a>
                <a href="mailto:scrilabstaff@gmail.com" class="support-link">
                    <i class="fas fa-envelope"></i>
                    <span>Email 客服</span>
                </a>
                <a href="/manual" class="support-link">
                    <i class="fas fa-book"></i>
                    <span>查看操作手冊</span>
                </a>
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

        // Image lazy loading fallback
        document.addEventListener('DOMContentLoaded', function() {
            const images = document.querySelectorAll('img[loading="lazy"]');
            
            // 如果瀏覽器不支援 lazy loading，使用 Intersection Observer
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.src; // 觸發載入
                            img.classList.remove('lazy');
                            imageObserver.unobserve(img);
                        }
                    });
                });

                images.forEach(img => {
                    img.classList.add('lazy');
                    imageObserver.observe(img);
                });
            }
        });
    </script>
</body>
</html>
"""

# 路由定義
@payment_guide_bp.route('', methods=['GET'])
def payment_guide():
    """付款說明主頁"""
    return render_template_string(PAYMENT_GUIDE_TEMPLATE)

@payment_guide_bp.route('/', methods=['GET'])
def payment_guide_slash():
    """付款說明主頁（帶斜槓）"""
    return render_template_string(PAYMENT_GUIDE_TEMPLATE)

# 確保正確導出
__all__ = ['payment_guide_bp']