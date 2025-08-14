"""
app.py - 修復版本，正確支援 Gumroad 付款和 Discord 機器人，並加強安全防護
"""
from flask import Flask, redirect, request, jsonify, render_template_string, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
from datetime import datetime
import logging
import threading
import schedule
import time as time_module

# 導入模組
from common.admin_panel import admin_bp
from products.artale.manual_routes import manual_bp
from common.disclaimer_routes import disclaimer_bp
from core.session_manager import session_manager, init_session_manager
from core.route_handlers import RouteHandlers
from core.gumroad_service import GumroadService  # 修復後的 Gumroad 服務
from core.gumroad_routes import gumroad_bp, init_gumroad_routes  # 修復後的 Gumroad 路由
from common.templates import PROFESSIONAL_PRODUCTS_TEMPLATE, PAYMENT_CANCEL_TEMPLATE
from products.artale.intro_routes import intro_bp
from common.payment_guide_routes import payment_guide_bp
from products.artale.download_routes import download_bp

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 應用初始化
app = Flask(__name__)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY', 'dev-key-change-in-production')

# CORS 配置
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# =====【新增】速率限制配置 =====
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"  # 使用記憶體存儲，適合 Render 平台
)

# =====【新增】安全配置 =====
# 封鎖的IP列表 (從環境變數讀取)
BLOCKED_IPS = set(os.environ.get('BLOCKED_IPS', '34.217.207.71').split(','))

# 可疑路徑列表
SUSPICIOUS_PATHS = {
    "/administrator/", "/.env", "/wp-admin/", "/phpmyadmin/", 
    "/admin.php", "/config.php", "/.git/", "/backup/",
    "/joomla.xml", "/wordpress/", "/xmlrpc.php",
    "/wp-config.php", "/database/", "/.htaccess"
}

# 可疑 User-Agent 關鍵字
SUSPICIOUS_USER_AGENTS = {
    'scanner', 'bot', 'crawl', 'spider', 'curl', 'wget', 'nikto', 
    'sqlmap', 'nmap', 'masscan', 'zap', 'burp'
}

# 合法爬蟲 User-Agent
LEGITIMATE_USER_AGENTS = {
    'googlebot', 'facebookexternalhit', 'twitterbot', 'linkedinbot',
    'slackbot', 'discordbot', 'whatsapp', 'telegrambot'
}

# 註冊藍圖
app.register_blueprint(admin_bp)
app.register_blueprint(manual_bp)
app.register_blueprint(disclaimer_bp)
app.register_blueprint(intro_bp)
app.register_blueprint(gumroad_bp)
app.register_blueprint(payment_guide_bp)
app.register_blueprint(download_bp)

# 全局變數
db = None
firebase_initialized = False
gumroad_service = None
route_handlers = None
initialization_in_progress = False

def check_environment_variables():
    """檢查必要的環境變數"""
    required_vars = [
        'FIREBASE_CREDENTIALS_BASE64',
        'GUMROAD_ACCESS_TOKEN',
        'GUMROAD_TRIAL_PRODUCT_ID',
        'GUMROAD_MONTHLY_PRODUCT_ID',
        'GUMROAD_QUARTERLY_PRODUCT_ID',
        'WEBHOOK_BASE_URL'
    ]
    
    # 可選的環境變數
    optional_vars = [
        'GUMROAD_WEBHOOK_SECRET',
        'SMTP_SERVER',
        'SMTP_PORT',
        'EMAIL_USER',
        'EMAIL_PASSWORD',
        'SUPPORT_EMAIL',
        'DISCORD_BOT_TOKEN',
        'DISCORD_GUILD_ID',
        'BLOCKED_IPS',  # 新增的安全相關環境變數
        'ADMIN_ALLOWED_IPS'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ 缺少必要的環境變數: {missing_vars}")
        return False
    
    # 檢查可選變數
    missing_optional = [var for var in optional_vars if not os.environ.get(var)]
    if missing_optional:
        logger.warning(f"⚠️ 缺少可選的環境變數: {missing_optional}")
    
    logger.info("✅ 環境變數檢查通過")
    return True

# =====【新增】安全檢查函數 =====
def get_real_ip():
    """獲取真實客戶端IP"""
    # 處理代理和負載均衡器的情況
    forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        # 取第一個IP（客戶端真實IP）
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.environ.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip.strip()
    
    return request.remote_addr

def is_suspicious_user_agent(user_agent):
    """檢查是否為可疑的User-Agent"""
    if not user_agent:
        return True
    
    user_agent_lower = user_agent.lower()
    
    # 檢查是否為合法爬蟲
    if any(legitimate in user_agent_lower for legitimate in LEGITIMATE_USER_AGENTS):
        return False
    
    # 檢查是否為可疑工具
    return any(suspicious in user_agent_lower for suspicious in SUSPICIOUS_USER_AGENTS)

def log_security_event(event_type, details):
    """記錄安全事件"""
    client_ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    logger.warning(f"🚨 安全事件 [{event_type}] - IP: {client_ip} | 路徑: {request.path} | UA: {user_agent[:100]} | 詳情: {details}")

def init_firebase_with_retry(max_retries=3):
    """改進的 Firebase 初始化，包含重試機制"""
    global db, firebase_initialized, initialization_in_progress
    
    if initialization_in_progress:
        logger.info("Firebase 初始化已在進行中...")
        return firebase_initialized
    
    initialization_in_progress = True
    
    try:
        # 檢查環境變數
        if not check_environment_variables():
            return False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"嘗試初始化 Firebase (第 {attempt + 1}/{max_retries} 次)...")
                
                # 檢查是否已經初始化
                if firebase_admin._apps:
                    logger.info("Firebase 應用已存在，刪除後重新初始化")
                    firebase_admin.delete_app(firebase_admin.get_app())
                
                # 解析憑證
                credentials_base64 = os.environ['FIREBASE_CREDENTIALS_BASE64'].strip()
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                credentials_dict = json.loads(credentials_json)
                
                # 驗證憑證完整性
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not credentials_dict.get(field)]
                
                if missing_fields:
                    logger.error(f"憑證缺少必需字段: {missing_fields}")
                    if attempt == max_retries - 1:
                        return False
                    continue
                
                # 初始化 Firebase
                cred = credentials.Certificate(credentials_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase 應用初始化成功")
                
                # 初始化 Firestore
                db = firestore.client()
                logger.info("Firestore 客戶端創建成功")
                
                # 測試連接
                try:
                    test_collection = db.collection('connection_test')
                    test_doc_ref = test_collection.document('test_connection')
                    
                    # 測試寫入
                    test_doc_ref.set({
                        'timestamp': datetime.now(),
                        'test': True,
                        'message': f'Connection test - attempt {attempt + 1}',
                        'server_time': datetime.now().isoformat()
                    })
                    
                    # 測試讀取
                    test_doc = test_doc_ref.get()
                    if test_doc.exists:
                        logger.info("✅ Firestore 連接測試成功")
                        firebase_initialized = True
                        
                        # 初始化相關服務
                        init_services()
                        
                        logger.info("✅ Firebase 完全初始化成功")
                        return True
                    else:
                        raise Exception("無法讀取測試文檔")
                        
                except Exception as firestore_error:
                    logger.error(f"Firestore 連接測試失敗: {str(firestore_error)}")
                    if attempt == max_retries - 1:
                        raise firestore_error
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Firebase 初始化失敗 (嘗試 {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒後重試...")
                    time_module.sleep(wait_time)
                else:
                    firebase_initialized = False
                    db = None
                    return False
        
        return False
        
    finally:
        initialization_in_progress = False

def start_discord_bot():
    """啟動 Discord 機器人"""
    # 檢查 Discord 相關設定
    discord_token = os.environ.get('DISCORD_BOT_TOKEN')
    discord_guild_id = os.environ.get('DISCORD_GUILD_ID')
    
    logger.info(f"🔍 Discord Token 存在: {'是' if discord_token else '否'}")
    logger.info(f"🔍 Discord Guild ID: {discord_guild_id if discord_guild_id else '未設定'}")
    
    if discord_token and discord_guild_id:
        logger.info("🤖 準備啟動 Discord 機器人...")
        try:
            # 檢查模組是否存在
            import discord_bot
            logger.info("✅ discord_bot 模組導入成功")
            
            from discord_bot import create_discord_bot
            logger.info("✅ create_discord_bot 函數導入成功")
            
            def run_discord_bot():
                try:
                    logger.info("🚀 Discord 機器人線程開始...")
                    bot = create_discord_bot(db)  # 使用現有的 Firebase db
                    logger.info("✅ Discord 機器人實例創建成功")
                    logger.info("🔌 嘗試連接到 Discord...")
                    bot.run(discord_token)
                except Exception as e:
                    logger.error(f"❌ Discord 機器人執行失敗: {str(e)}", exc_info=True)
            
            # 在背景執行 Discord 機器人
            discord_thread = threading.Thread(target=run_discord_bot)
            discord_thread.daemon = True
            discord_thread.start()
            logger.info("✅ Discord 機器人線程已啟動")
            
        except ImportError as e:
            logger.error(f"❌ Discord 模組導入失敗: {str(e)}")
            logger.error("請確認 discord_bot 資料夾和相關檔案是否存在")
        except Exception as e:
            logger.error(f"❌ Discord 機器人設定失敗: {str(e)}", exc_info=True)
    else:
        if not discord_token:
            logger.warning("⚠️ 未設定 DISCORD_BOT_TOKEN，跳過 Discord 機器人啟動")
        if not discord_guild_id:
            logger.warning("⚠️ 未設定 DISCORD_GUILD_ID，跳過 Discord 機器人啟動")

def init_services():
    """初始化相關服務"""
    global gumroad_service, route_handlers
    
    try:
        # 初始化 Session Manager
        init_session_manager(db)
        logger.info("✅ Session Manager 已初始化")
        
        # 初始化 Gumroad 服務
        gumroad_service = GumroadService(db)
        logger.info("✅ Gumroad Service 已初始化")
        
        # 初始化 Gumroad 路由
        init_gumroad_routes(gumroad_service)
        logger.info("✅ Gumroad Routes 已初始化")
        
        # 初始化路由處理器
        route_handlers = RouteHandlers(db, session_manager)
        logger.info("✅ Route Handlers 已初始化")
        
        # 啟動後台清理任務
        start_background_tasks()
        
        # 啟動 Discord 機器人
        start_discord_bot()
        
    except Exception as e:
        logger.error(f"❌ 服務初始化失敗: {str(e)}")
        raise

def cleanup_expired_sessions():
    """定期清理過期會話"""
    try:
        if session_manager and firebase_initialized:
            deleted_count = session_manager.cleanup_expired_sessions()
            if deleted_count > 0:
                logger.info(f"🧹 定期清理：刪除了 {deleted_count} 個過期會話")
    except Exception as e:
        logger.error(f"❌ 定期清理失敗: {str(e)}")

def run_background_tasks():
    """運行後台任務"""
    # 每30分鐘清理一次過期會話
    schedule.every(30).minutes.do(cleanup_expired_sessions)
    
    while True:
        schedule.run_pending()
        time_module.sleep(60)  # 每分鐘檢查一次

def start_background_tasks():
    """啟動後台任務線程"""
    if os.environ.get('FLASK_ENV') != 'development':  # 只在生產環境運行
        background_thread = threading.Thread(target=run_background_tasks, daemon=True)
        background_thread.start()
        logger.info("🚀 後台清理任務已啟動")

# =====【修改】Flask 中間件 - 加強安全檢查 =====

@app.before_request
def security_checks():
    """加強版安全檢查：IP封鎖、路徑檢查、User-Agent檢查等"""
    client_ip = get_real_ip()
    
    # 1. IP 封鎖檢查
    if client_ip in BLOCKED_IPS:
        log_security_event("BLOCKED_IP_ACCESS", f"已封鎖的IP嘗試訪問")
        abort(403)
    
    # 2. 可疑路徑檢查
    request_path = request.path.lower()
    for suspicious_path in SUSPICIOUS_PATHS:
        if suspicious_path in request_path:
            log_security_event("SUSPICIOUS_PATH_ACCESS", f"嘗試訪問可疑路徑: {request.path}")
            abort(404)  # 返回404而不是403，避免洩露資訊
    
    # 3. User-Agent 檢查
    user_agent = request.headers.get('User-Agent', '')
    if is_suspicious_user_agent(user_agent):
        log_security_event("SUSPICIOUS_USER_AGENT", f"可疑User-Agent: {user_agent[:100]}")
        # 對於可疑User-Agent，我們記錄但不阻擋，避免誤殺
    
    # 4. 強制 HTTPS（生產環境）
    if (not request.is_secure and 
        request.headers.get('X-Forwarded-Proto') != 'https' and
        os.environ.get('FLASK_ENV') == 'production'):
        return redirect(request.url.replace('http://', 'https://'), code=301)
    
    # 5. 保護管理員路由
    protected_paths = [
        '/admin',
        '/session-stats', 
        '/cleanup-sessions',
        '/system/status'
    ]
    
    # 檢查是否是受保護的路徑
    if any(request.path.startswith(path) for path in protected_paths):
        # 檢查IP白名單
        allowed_ips = os.environ.get('ADMIN_ALLOWED_IPS', '').split(',')
        allowed_ips = [ip.strip() for ip in allowed_ips if ip.strip()]
        
        if allowed_ips and client_ip not in allowed_ips:
            log_security_event("UNAUTHORIZED_ADMIN_ACCESS", f"未授權的管理員訪問嘗試")
            return jsonify({'error': 'Not found'}), 404
    
    return None

@app.after_request
def after_request(response):
    """添加安全標頭"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # 記錄請求
    client_ip = get_real_ip()
    logger.info(f"{client_ip} - {request.method} {request.path} - {response.status_code}")
    
    return response

# =====【新增】速率限制錯誤處理 =====
@app.errorhandler(429)
def ratelimit_handler(e):
    """速率限制錯誤處理"""
    client_ip = get_real_ip()
    log_security_event("RATE_LIMIT_EXCEEDED", f"速率限制觸發")
    return jsonify({
        'error': 'Too many requests. Please slow down.',
        'retry_after': str(e.retry_after) if hasattr(e, 'retry_after') else '60'
    }), 429

# ===== 主要路由（添加速率限制） =====

@app.route('/', methods=['GET'])
@limiter.limit("30 per minute")  # 主頁速率限制
def root():
    """根路徑端點 - 直接重定向到產品頁面"""
    return redirect('/products', code=301)

@app.route('/system/status/<secret_key>', methods=['GET'])
@limiter.limit("10 per minute")  # 系統狀態查詢限制
def system_status(secret_key):
    """隱藏的系統狀態端點"""
    # 檢查密鑰
    expected_secret = os.environ.get('SYSTEM_STATUS_SECRET', 'default-secret-change-me')
    if secret_key != expected_secret:
        return jsonify({'error': 'Not found'}), 404
    
    if not firebase_initialized:
        # 嘗試重新初始化
        logger.info("嘗試重新初始化 Firebase...")
        init_firebase_with_retry()
    
    if route_handlers:
        return route_handlers.root()
    else:
        return jsonify({
            'service': 'Scrilab Artale Authentication Service',
            'status': 'initializing',
            'firebase_initialized': firebase_initialized,
            'gumroad_available': gumroad_service is not None,
            'message': 'Service is starting up, please wait...',
            'security_status': {
                'blocked_ips_count': len(BLOCKED_IPS),
                'rate_limiting_enabled': True
            }
        })

@app.route('/health', methods=['GET'])
@limiter.limit("60 per minute")  # 健康檢查較寬鬆的限制
def health_check():
    """健康檢查端點"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'artale-auth-service',
        'version': '3.1.1-security-enhanced',
        'checks': {}
    }
    
    # 檢查 Firebase 狀態
    if firebase_initialized and db:
        try:
            # 快速測試查詢
            test_ref = db.collection('connection_test').limit(1)
            list(test_ref.stream())
            health_status['checks']['firebase'] = 'healthy'
        except Exception as e:
            health_status['checks']['firebase'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
    else:
        health_status['checks']['firebase'] = 'not_initialized'
        health_status['status'] = 'degraded'
    
    # 檢查 Gumroad 服務
    if gumroad_service:
        health_status['checks']['gumroad_service'] = 'healthy'
    else:
        health_status['checks']['gumroad_service'] = 'not_initialized'
        health_status['status'] = 'degraded'
    
    # 檢查路由處理器
    if route_handlers:
        health_status['checks']['route_handlers'] = 'healthy'
    else:
        health_status['checks']['route_handlers'] = 'not_initialized'
        health_status['status'] = 'degraded'
    
    # 檢查 Session Manager
    if session_manager:
        try:
            stats = session_manager.get_session_stats()
            health_status['checks']['session_manager'] = 'healthy'
            health_status['session_stats'] = stats
        except Exception as e:
            health_status['checks']['session_manager'] = f'error: {str(e)}'
    else:
        health_status['checks']['session_manager'] = 'not_initialized'
    
    # 檢查 Discord 機器人狀態
    discord_token = os.environ.get('DISCORD_BOT_TOKEN')
    discord_guild_id = os.environ.get('DISCORD_GUILD_ID')
    
    if discord_token and discord_guild_id:
        health_status['checks']['discord_bot'] = 'configured'
    else:
        health_status['checks']['discord_bot'] = 'not_configured'
    
    # 安全狀態檢查
    health_status['checks']['security'] = {
        'rate_limiting': 'enabled',
        'blocked_ips_count': len(BLOCKED_IPS),
        'suspicious_paths_monitored': len(SUSPICIOUS_PATHS)
    }
    
    status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
    return jsonify(health_status), status_code

# ===== 用戶認證路由（添加速率限制） =====

@app.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # 登入嚴格限制
def login():
    """用戶登入端點"""
    if not firebase_initialized:
        logger.warning("Firebase 未初始化，嘗試重新初始化...")
        if not init_firebase_with_retry():
            return jsonify({
                'success': False,
                'error': 'Authentication service unavailable. Please try again later.',
                'code': 'SERVICE_UNAVAILABLE'
            }), 503
    
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready. Please try again later.',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.login()

@app.route('/auth/logout', methods=['POST'])
@limiter.limit("10 per minute")  # 登出限制
def logout():
    """用戶登出端點"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.logout()

@app.route('/auth/validate', methods=['POST'])
@limiter.limit("20 per minute")  # 驗證稍微寬鬆
def validate_session():
    """驗證會話令牌"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.validate_session()

@app.route('/session-stats', methods=['GET'])
@limiter.limit("10 per minute")  # 管理功能限制
def session_stats():
    """Session 統計信息"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.session_stats()

@app.route('/cleanup-sessions', methods=['POST'])
@limiter.limit("5 per minute")  # 清理功能嚴格限制
def manual_cleanup_sessions():
    """手動清理過期會話"""
    if not route_handlers:
        return jsonify({
            'success': False,
            'error': 'Service not ready',
            'code': 'SERVICE_NOT_READY'
        }), 503
    
    return route_handlers.manual_cleanup_sessions()

# ===== 付款相關路由（添加速率限制） =====

@app.route('/api/create-payment', methods=['POST'])
@limiter.limit("10 per minute")  # 付款創建限制
def create_payment():
    """創建付款（統一入口，主要使用 Gumroad）"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'gumroad')  # 預設使用 Gumroad
        
        if provider == 'gumroad':
            # 重定向到 Gumroad 付款創建
            return redirect('/gumroad/create-payment', code=307)
        else:
            return jsonify({
                'success': False,
                'error': f'不支援的付款提供者: {provider}'
            }), 400
            
    except Exception as e:
        logger.error(f"創建付款錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': '系統錯誤，請稍後再試'
        }), 500

@app.route('/payment/success', methods=['GET'])
@limiter.limit("20 per minute")  # 付款成功頁面限制
def payment_success():
    """付款成功頁面"""
    try:
        provider = request.args.get('provider', 'gumroad')  # 預設 Gumroad
        
        if provider == 'gumroad':
            # Gumroad 付款成功處理
            return redirect('/gumroad/success?' + request.query_string.decode())
        else:
            # 其他付款方式重定向到產品頁
            return redirect('/products?error=invalid_provider')
            
    except Exception as e:
        logger.error(f"付款成功處理錯誤: {str(e)}", exc_info=True)
        return redirect('/products?error=system_error')

@app.route('/payment/cancel', methods=['GET'])
@limiter.limit("20 per minute")  # 付款取消頁面限制
def payment_cancel():
    """付款取消回調"""
    return render_template_string(PAYMENT_CANCEL_TEMPLATE)

@app.route('/products', methods=['GET'])
@limiter.limit("30 per minute")  # 產品頁面限制
def products_page():
    """軟體服務展示頁面（支援 Gumroad）"""
    return render_template_string(PROFESSIONAL_PRODUCTS_TEMPLATE)

# =====【新增】特殊攻擊路徑直接阻擋 =====
@app.route('/.env')
@app.route('/administrator/<path:path>')
@app.route('/wp-admin/<path:path>')
@app.route('/phpmyadmin/<path:path>')
@app.route('/wp-config.php')
@app.route('/xmlrpc.php')
@app.route('/.git/<path:path>')
@app.route('/backup/<path:path>')
def block_common_attacks(path=None):
    """直接封鎖常見的攻擊路徑"""
    client_ip = get_real_ip()
    log_security_event("DIRECT_ATTACK_BLOCKED", f"直接攻擊路徑被阻擋: {request.path}")
    
    # 自動將此IP加入臨時封鎖列表（可選）
    # add_ip_to_temporary_blocklist(client_ip)
    
    abort(404)

# =====【新增】動態IP管理功能 =====
def add_ip_to_temporary_blocklist(ip_address, duration_minutes=60):
    """將IP加入臨時封鎖列表"""
    try:
        if db and firebase_initialized:
            # 記錄到 Firestore 中，設置過期時間
            from datetime import timedelta
            
            expire_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            db.collection('temporary_blocked_ips').document(ip_address).set({
                'ip': ip_address,
                'blocked_at': datetime.now(),
                'expires_at': expire_time,
                'reason': 'Suspicious activity detected',
                'auto_blocked': True
            })
            
            # 加入記憶體中的封鎖列表
            BLOCKED_IPS.add(ip_address)
            
            logger.warning(f"🚫 IP {ip_address} 已被自動加入臨時封鎖列表 ({duration_minutes} 分鐘)")
            
    except Exception as e:
        logger.error(f"❌ 添加臨時封鎖IP失敗: {str(e)}")

@app.route('/admin/security/unblock-ip', methods=['POST'])
@limiter.limit("5 per minute")
def unblock_ip():
    """手動解除IP封鎖"""
    try:
        data = request.get_json()
        ip_to_unblock = data.get('ip')
        
        if not ip_to_unblock:
            return jsonify({'success': False, 'error': '請提供要解除封鎖的IP'}), 400
        
        # 從記憶體列表移除
        BLOCKED_IPS.discard(ip_to_unblock)
        
        # 從 Firestore 移除（如果存在）
        if db and firebase_initialized:
            db.collection('temporary_blocked_ips').document(ip_to_unblock).delete()
        
        logger.info(f"✅ IP {ip_to_unblock} 已被手動解除封鎖")
        
        return jsonify({
            'success': True,
            'message': f'IP {ip_to_unblock} 已解除封鎖'
        })
        
    except Exception as e:
        logger.error(f"❌ 解除IP封鎖失敗: {str(e)}")
        return jsonify({'success': False, 'error': '系統錯誤'}), 500

@app.route('/admin/security/blocked-ips', methods=['GET'])
@limiter.limit("10 per minute")
def get_blocked_ips():
    """獲取當前封鎖的IP列表"""
    try:
        blocked_list = []
        
        # 從環境變數獲取的永久封鎖IP
        permanent_ips = set(os.environ.get('BLOCKED_IPS', '').split(','))
        for ip in permanent_ips:
            if ip.strip():
                blocked_list.append({
                    'ip': ip.strip(),
                    'type': 'permanent',
                    'reason': 'Manual configuration'
                })
        
        # 從 Firestore 獲取臨時封鎖IP
        if db and firebase_initialized:
            temp_blocked = db.collection('temporary_blocked_ips').stream()
            for doc in temp_blocked:
                data = doc.to_dict()
                blocked_list.append({
                    'ip': data.get('ip'),
                    'type': 'temporary',
                    'reason': data.get('reason', 'Unknown'),
                    'blocked_at': data.get('blocked_at'),
                    'expires_at': data.get('expires_at')
                })
        
        return jsonify({
            'success': True,
            'blocked_ips': blocked_list,
            'total_count': len(blocked_list)
        })
        
    except Exception as e:
        logger.error(f"❌ 獲取封鎖IP列表失敗: {str(e)}")
        return jsonify({'success': False, 'error': '系統錯誤'}), 500


# ===== 應用初始化 =====

# 模塊載入時初始化 Firebase
logger.info("🚀 開始初始化應用...")
try:
    success = init_firebase_with_retry()
    if success:
        logger.info(f"✅ 應用初始化成功，Gumroad 服務: {'已啟用' if gumroad_service else '未啟用'}")
        logger.info(f"🛡️ 安全功能已啟用 - 封鎖IP數量: {len(BLOCKED_IPS)}")
    else:
        logger.error(f"❌ 應用初始化失敗")
except Exception as e:
    logger.error(f"❌ 應用初始化異常: {str(e)}")

# 錯誤處理
@app.errorhandler(404)
def not_found(error):
    """統一的 404 處理"""
    # 記錄 404 錯誤，可能是掃描行為
    client_ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # 如果是可疑的404請求，記錄安全事件
    if any(suspicious in request.path.lower() for suspicious in SUSPICIOUS_PATHS):
        log_security_event("SUSPICIOUS_404", f"可疑的404請求")
    
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(403)
def forbidden(error):
    """將 403 偽裝成 404"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """內部錯誤處理"""
    logger.error(f"❌ 內部錯誤: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# 本地開發環境啟動
if __name__ == '__main__':
    logger.info("🏠 本地開發模式啟動")
    
    # 開發環境下的額外檢查
    if not firebase_initialized:
        logger.warning("⚠️ Firebase 未初始化，應用可能無法正常工作")
    
    if not gumroad_service:
        logger.warning("⚠️ Gumroad 服務未初始化，付款功能不可用")
    
    # 顯示安全配置
    logger.info(f"🛡️ 安全配置:")
    logger.info(f"   - 封鎖IP數量: {len(BLOCKED_IPS)}")
    logger.info(f"   - 監控的可疑路徑數量: {len(SUSPICIOUS_PATHS)}")
    logger.info(f"   - 速率限制: 已啟用")
    
    # 啟動 Flask 應用
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Flask 應用啟動於 port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)