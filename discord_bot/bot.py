"""
Discord 機器人主程式
"""
import discord
from discord.ext import commands
import logging
from .config import *
from .verification import verify_user_uuid, is_rate_limited, record_failed_attempt

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self, firebase_db):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)
        self.db = firebase_db  # 使用你現有的 Firebase 連接

    async def setup_hook(self):
        await self.tree.sync()
        print(f'{self.user} Discord 機器人已上線！')

class VerificationModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="序號驗證")
        self.bot = bot
    
    uuid_input = discord.ui.TextInput(
        label="請輸入您的授權序號",
        placeholder="輸入購買時獲得的序號...",
        style=discord.TextStyle.short,
        max_length=100,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        uuid = self.uuid_input.value.strip()
        
        # 檢查速率限制
        if is_rate_limited(user_id):
            embed = discord.Embed(
                title="🚫 驗證失敗",
                description="驗證失敗次數過多，請10分鐘後再試。",
                color=0xff4444
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 使用你現有的驗證邏輯
            is_valid, result = await verify_user_uuid(uuid, self.bot.db)
            
            if is_valid:
                # 驗證成功 - 添加角色
                guild = interaction.guild
                verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
                
                if not verified_role:
                    verified_role = await guild.create_role(
                        name=VERIFIED_ROLE_NAME,
                        color=discord.Color.green(),
                        reason="自動創建驗證角色"
                    )
                
                await interaction.user.add_roles(verified_role)
                
                embed = discord.Embed(
                    title="✅ 驗證成功！",
                    description=f"歡迎 {interaction.user.mention}！\n\n您現在可以訪問會員專區了！",
                    color=0x00ff88
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            else:
                record_failed_attempt(user_id)
                embed = discord.Embed(
                    title="❌ 驗證失敗",
                    description=f"錯誤：{result}",
                    color=0xff4444
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"驗證錯誤: {str(e)}")
            embed = discord.Embed(
                title="⚠️ 系統錯誤",
                description="驗證系統暫時無法使用。",
                color=0xffaa00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
    
    @discord.ui.button(label='開始驗證', style=discord.ButtonStyle.primary, emoji='🔐')
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerificationModal(self.bot))

def setup_bot_commands(bot):
    """設置機器人命令"""
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} 已連線到 Discord！')

    @bot.tree.command(name="verify", description="開始序號驗證")
    async def verify_command(interaction: discord.Interaction):
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if verified_role in interaction.user.roles:
            embed = discord.Embed(
                title="✅ 您已經通過驗證",
                description="無需重複驗證。",
                color=0x00ff88
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔐 序號驗證",
            description="點擊下方按鈕開始驗證",
            color=0x00d4ff
        )
        view = VerificationView(bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)