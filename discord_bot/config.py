"""
Discord 機器人配置
"""
import os
import logging

# Discord 設定
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')

# 角色名稱
VERIFIED_ROLE_NAME = "已驗證用戶"

# 頻道名稱
VERIFICATION_CHANNEL = "驗證"
WELCOME_CHANNEL = "歡迎"

# 日誌設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if DISCORD_TOKEN:
    logger.info("✅ Discord Token 已設定")
else:
    logger.warning("⚠️ Discord Token 未設定")

if GUILD_ID:
    logger.info(f"✅ Discord Guild ID: {GUILD_ID}")
else:
    logger.warning("⚠️ Discord Guild ID 未設定")