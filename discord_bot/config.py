"""
Discord 機器人配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord 設定
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))  # 你的伺服器 ID

# 角色名稱
VERIFIED_ROLE_NAME = "已驗證用戶"
UNVERIFIED_ROLE_NAME = "未驗證"

# 頻道名稱
VERIFICATION_CHANNEL = "驗證"
WELCOME_CHANNEL = "歡迎"
DOWNLOAD_CHANNEL = "軟體下載"