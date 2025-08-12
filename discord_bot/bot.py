"""
Discord 機器人主程式 - 專注於序號驗證
"""
import discord
from discord.ext import commands
import logging
from .config import *
from .verification import verify_user_uuid, is_rate_limited, record_failed_attempt
import asyncio

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self, firebase_db):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)
        self.db = firebase_db

    async def setup_hook(self):
        """機器人啟動時的設置"""
        try:
            # 同步斜線命令
            synced = await self.tree.sync()
            logger.info(f"✅ 已同步 {len(synced)} 個斜線命令")
            
            # 設置機器人狀態
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.watching, 
                    name="序號驗證 | 使用 /verify"
                )
            )
            
        except Exception as e:
            logger.error(f"❌ 機器人設置失敗: {e}")

    async def on_ready(self):
        """機器人準備就緒"""
        logger.info(f'✅ {self.user} 已成功連線到 Discord！')
        logger.info(f'📊 已連接到 {len(self.guilds)} 個伺服器')
        
        # 檢查必要的角色是否存在
        for guild in self.guilds:
            await self.setup_guild_roles(guild)

    async def setup_guild_roles(self, guild):
        """設置伺服器角色"""
        try:
            # 檢查已驗證角色
            verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
            if not verified_role:
                verified_role = await guild.create_role(
                    name=VERIFIED_ROLE_NAME,
                    color=discord.Color.green(),
                    reason="自動創建驗證角色",
                    mentionable=False
                )
                logger.info(f"✅ 已在 {guild.name} 創建驗證角色")
            
            # 可選：創建未驗證角色（用於限制訪問）
            unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
            if not unverified_role:
                unverified_role = await guild.create_role(
                    name=UNVERIFIED_ROLE_NAME,
                    color=discord.Color.light_grey(),
                    reason="自動創建未驗證角色",
                    mentionable=False
                )
                logger.info(f"✅ 已在 {guild.name} 創建未驗證角色")
                
        except discord.Forbidden:
            logger.error(f"❌ 機器人在 {guild.name} 沒有管理角色權限")
        except Exception as e:
            logger.error(f"❌ 設置 {guild.name} 角色時出錯: {e}")

    async def on_member_join(self, member):
        """新成員加入時自動給予未驗證角色"""
        try:
            guild = member.guild
            unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
            
            if unverified_role:
                await member.add_roles(unverified_role, reason="新成員自動角色")
                logger.info(f"👋 {member.name} 加入 {guild.name}，已給予未驗證角色")
            
            # 發送歡迎私訊
            try:
                embed = discord.Embed(
                    title="🎉 歡迎加入！",
                    description=f"歡迎來到 **{guild.name}**！\n\n"
                               "🔐 請使用 `/verify` 命令驗證您的序號以獲得完整訪問權限。\n"
                               "💡 序號可在購買確認郵件中找到。",
                    color=0x00d4ff
                )
                await member.send(embed=embed)
            except discord.Forbidden:
                # 如果無法發送私訊，忽略錯誤
                pass
                
        except Exception as e:
            logger.error(f"❌ 處理新成員加入時出錯: {e}")

class VerificationModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="🔐 序號驗證", timeout=300)
        self.bot = bot
    
    uuid_input = discord.ui.TextInput(
        label="請輸入您的序號",
        placeholder="例如: ABC123-DEF456-GHI789...",
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
                description="⏰ 驗證失敗次數過多，請 **10 分鐘**後再試。",
                color=0xff4444
            )
            embed.add_field(
                name="💡 小提示", 
                value="請仔細檢查您的序號格式是否正確", 
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 驗證序號
            is_valid, result = await verify_user_uuid(uuid, self.bot.db)
            
            if is_valid:
                # 驗證成功 - 添加/移除角色
                guild = interaction.guild
                member = interaction.user
                
                verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
                unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
                
                # 確保驗證角色存在
                if not verified_role:
                    verified_role = await guild.create_role(
                        name=VERIFIED_ROLE_NAME,
                        color=discord.Color.green(),
                        reason="驗證成功時自動創建"
                    )
                
                # 添加驗證角色
                await member.add_roles(verified_role, reason="序號驗證成功")
                
                # 移除未驗證角色（如果有的話）
                if unverified_role and unverified_role in member.roles:
                    await member.remove_roles(unverified_role, reason="驗證成功")
                
                # 成功回應
                user_data = result
                plan_type = user_data.get('plan_type', '未知方案')
                expires_info = ""
                
                if 'expires_at' in user_data:
                    expires_at = user_data['expires_at']
                    if hasattr(expires_at, 'strftime'):
                        expires_info = f"\n⏰ 到期時間: {expires_at.strftime('%Y-%m-%d')}"
                
                embed = discord.Embed(
                    title="✅ 驗證成功！",
                    description=f"🎉 恭喜 {member.mention}！您的帳號驗證成功！\n\n"
                               f"📦 方案類型: **{plan_type}**{expires_info}\n\n"
                               f"🔓 您現在可以訪問所有會員專區了！",
                    color=0x00ff88
                )
                embed.add_field(
                    name="🚀 接下來可以做什麼？",
                    value="• 查看專屬頻道\n• 下載軟體資源\n• 參與討論",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"✅ {member.name}#{member.discriminator} 驗證成功 ({plan_type})")
                
            else:
                # 驗證失敗
                record_failed_attempt(user_id)
                
                embed = discord.Embed(
                    title="❌ 驗證失敗",
                    description=f"**錯誤原因:** {result}",
                    color=0xff4444
                )
                embed.add_field(
                    name="🔍 常見問題",
                    value="• 請檢查序號是否完整\n• 確認沒有多餘的空格\n• 序號區分大小寫\n• 確認帳號未過期",
                    inline=False
                )
                embed.add_field(
                    name="💬 需要幫助？",
                    value="如果問題持續，請聯繫客服",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.warning(f"❌ {interaction.user.name} 驗證失敗: {result}")
                
        except Exception as e:
            logger.error(f"❌ 驗證過程出錯: {str(e)}")
            embed = discord.Embed(
                title="⚠️ 系統錯誤",
                description="驗證系統暫時無法使用，請稍後再試。\n\n如果問題持續，請聯繫管理員。",
                color=0xffaa00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # 持久化視圖
        self.bot = bot
    
    @discord.ui.button(
        label='開始驗證', 
        style=discord.ButtonStyle.primary, 
        emoji='🔐',
        custom_id='verify_button'
    )
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 檢查是否已經驗證
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if verified_role and verified_role in interaction.user.roles:
            embed = discord.Embed(
                title="✅ 您已經通過驗證",
                description="無需重複驗證，您已經擁有會員權限！",
                color=0x00ff88
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 開始驗證流程
        await interaction.response.send_modal(VerificationModal(self.bot))

def setup_bot_commands(bot):
    """設置機器人命令"""
    
    @bot.tree.command(name="verify", description="🔐 開始序號驗證流程")
    async def verify_command(interaction: discord.Interaction):
        """序號驗證命令"""
        # 檢查是否已經驗證
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if verified_role and verified_role in interaction.user.roles:
            embed = discord.Embed(
                title="✅ 您已經通過驗證",
                description="您已經擁有會員權限，無需重複驗證！",
                color=0x00ff88
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 創建驗證介面
        embed = discord.Embed(
            title="🔐 序號驗證系統",
            description="點擊下方按鈕開始驗證您的序號\n\n"
                       "🛒 **如何獲得序號？**\n"
                       "購買我們的產品後，序號會發送到您的郵箱\n\n"
                       "❓ **驗證後可以做什麼？**\n"
                       "• 訪問專屬頻道\n"
                       "• 下載軟體資源\n"
                       "• 獲得技術支援",
            color=0x00d4ff
        )
        embed.add_field(
            name="⚠️ 注意事項",
            value="• 每個序號只能驗證一次\n• 序號區分大小寫\n• 請確保序號完整無誤",
            inline=False
        )
        
        view = VerificationView(bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @bot.tree.command(name="status", description="📊 查看您的驗證狀態")
    async def status_command(interaction: discord.Interaction):
        """查看驗證狀態"""
        member = interaction.user
        guild = interaction.guild
        
        verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        is_verified = verified_role and verified_role in member.roles
        
        if is_verified:
            embed = discord.Embed(
                title="✅ 驗證狀態：已驗證",
                description=f"🎉 {member.mention} 您已經是認證會員！",
                color=0x00ff88
            )
            embed.add_field(name="🔓 權限", value="擁有所有會員權限", inline=True)
            embed.add_field(name="⏰ 驗證時間", value="查看角色獲得時間", inline=True)
        else:
            embed = discord.Embed(
                title="❌ 驗證狀態：未驗證",
                description="您尚未通過序號驗證",
                color=0xff4444
            )
            embed.add_field(
                name="🔐 如何驗證？",
                value="使用 `/verify` 命令開始驗證",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 管理員命令（可選）
    @bot.tree.command(name="setup_verification", description="🛠️ 設置驗證面板（僅管理員）")
    @discord.app_commands.default_permissions(administrator=True)
    async def setup_verification_panel(interaction: discord.Interaction):
        """設置驗證面板（管理員專用）"""
        embed = discord.Embed(
            title="🔐 會員驗證中心",
            description="**歡迎來到會員驗證中心！**\n\n"
                       "🛒 購買我們的產品後，您會收到一個唯一的序號\n"
                       "🔐 使用序號驗證後即可獲得會員權限\n\n"
                       "**驗證後您可以：**\n"
                       "• 🗣️ 參與會員專屬討論\n"
                       "• 📥 下載專屬軟體資源\n"
                       "• 🎯 獲得優先技術支援\n"
                       "• 📢 接收最新產品資訊",
            color=0x00d4ff
        )
        embed.add_field(
            name="🚀 開始驗證",
            value="點擊下方 **開始驗證** 按鈕",
            inline=False
        )
        embed.add_field(
            name="❓ 需要幫助？",
            value="如有問題請聯繫管理員",
            inline=False
        )
        embed.set_footer(text="※ 每個序號只能使用一次")
        
        view = VerificationView(bot)
        await interaction.response.send_message(embed=embed, view=view)
        
        # 儲存持久化視圖
        bot.add_view(view)