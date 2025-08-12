"""
Discord 機器人模組
"""
from .bot import DiscordBot, setup_bot_commands
from .config import DISCORD_TOKEN

def create_discord_bot(firebase_db):
    """創建並配置 Discord 機器人"""
    bot = DiscordBot(firebase_db)
    setup_bot_commands(bot)
    return bot