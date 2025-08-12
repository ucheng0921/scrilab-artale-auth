"""
Discord 機器人模組
"""
import logging

logger = logging.getLogger(__name__)
logger.info("✅ discord_bot 模組已載入")

def create_discord_bot(firebase_db):
    """創建並配置 Discord 機器人"""
    try:
        from .bot import DiscordBot, setup_bot_commands
        logger.info("✅ 導入 Discord 機器人模組成功")
        
        bot = DiscordBot(firebase_db)
        setup_bot_commands(bot)
        logger.info("✅ Discord 機器人創建成功")
        return bot
    except Exception as e:
        logger.error(f"❌ Discord 機器人創建失敗: {str(e)}")
        raise