"""
Discord 機器人主程式
"""
import discord
from discord.ext import commands
import logging
from .config import VERIFIED_ROLE_NAME, DISCORD_TOKEN, GUILD_ID
from .verification import verify_user_uuid, is_rate_limited, record_failed_attempt, record_verification

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self, firebase_db):
        # 設定機器人意圖
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.db = firebase_db
        logger.info("🤖 Discord 機器人實例創建完成")

    async def setup_hook(self):
        """機器人啟動後的設置"""
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ 同步了 {len(synced)} 個斜線命令")
        except Exception as e:
            logger.error(f"❌ 命令同步失敗: {str(e)}")

class VerificationModal(discord.ui.Modal):
    """驗證模態框"""
    def __init__(self, bot):
        super().__init__(title="🔐 序號驗證")
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
        
        logger.info(f"用戶 {interaction.user} 嘗試驗證")
        
        # 檢查速率限制
        if is_rate_limited(user_id):
            logger.warning(f"用戶 {user_id} 觸發速率限制")
            embed = discord.Embed(
                title="🚫 驗證失敗",
                description="驗證失敗次數過多，請10分鐘後再試。",
                color=0xff4444
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 使用現有的驗證邏輯
            is_valid, result = await verify_user_uuid(uuid, self.bot.db)
            
            if is_valid:
                logger.info(f"用戶 {interaction.user} 驗證成功")
                
                # 驗證成功 - 添加角色
                guild = interaction.guild
                verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
                
                if not verified_role:
                    logger.info("創建驗證角色")
                    verified_role = await guild.create_role(
                        name=VERIFIED_ROLE_NAME,
                        color=discord.Color.green(),
                        reason="自動創建驗證角色"
                    )
                
                await interaction.user.add_roles(verified_role)
                logger.info(f"已為用戶 {interaction.user} 添加驗證角色")
                
                # 記錄驗證
                await record_verification(user_id, uuid, result, self.bot.db)
                
                embed = discord.Embed(
                    title="✅ 驗證成功！",
                    description=f"歡迎 {interaction.user.mention}！\n\n🎉 您現在可以訪問：\n• 🔒 會員專屬頻道\n• 📚 軟體下載資源\n• 💬 技術支援討論",
                    color=0x00ff88
                )
                embed.set_footer(text="感謝您的支持！")
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # 發送歡迎訊息到歡迎頻道
                welcome_channel = discord.utils.get(guild.channels, name="歡迎")
                if welcome_channel:
                    welcome_embed = discord.Embed(
                        title="🎉 新用戶驗證成功",
                        description=f"歡迎 {interaction.user.mention} 加入我們的會員群組！",
                        color=0x00d4ff
                    )
                    await welcome_channel.send(embed=welcome_embed)
                
            else:
                logger.warning(f"用戶 {interaction.user} 驗證失敗: {result}")
                record_failed_attempt(user_id)
                
                embed = discord.Embed(
                    title="❌ 驗證失敗",
                    description=f"**錯誤原因：** {result}\n\n**常見問題：**\n• 確認序號輸入正確\n• 檢查序號是否已過期\n• 確認帳號狀態正常",
                    color=0xff4444
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"驗證過程錯誤: {str(e)}")
            embed = discord.Embed(
                title="⚠️ 系統錯誤",
                description="驗證系統暫時無法使用，請稍後再試。",
                color=0xffaa00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VerificationView(discord.ui.View):
    """驗證按鈕視圖"""
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
    
    @discord.ui.button(label='開始驗證', style=discord.ButtonStyle.primary, emoji='🔐')
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerificationModal(self.bot))

def setup_bot_commands(bot):
    """設置機器人命令和事件"""
    
    @bot.event
    async def on_ready():
        logger.info(f'✅ {bot.user} 已連線到 Discord！')
        logger.info(f'機器人 ID: {bot.user.id}')
        if GUILD_ID:
            guild = bot.get_guild(int(GUILD_ID))
            if guild:
                logger.info(f'已連接到伺服器: {guild.name}')
            else:
                logger.warning(f'找不到伺服器 ID: {GUILD_ID}')

    @bot.event
    async def on_member_join(member):
        """新用戶加入事件"""
        logger.info(f"新用戶加入: {member}")
        
        # 檢查是否已驗證過
        if bot.db:
            try:
                verification_ref = bot.db.collection('discord_verifications').document(str(member.id))
                verification_doc = verification_ref.get()
                
                if verification_doc.exists:
                    # 用戶之前已驗證，自動添加角色
                    guild = member.guild
                    verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
                    if verified_role:
                        await member.add_roles(verified_role)
                        logger.info(f"自動恢復用戶 {member} 的驗證角色")
                        return
            except Exception as e:
                logger.error(f"檢查用戶驗證狀態錯誤: {str(e)}")
        
        # 發送驗證引導
        try:
            embed = discord.Embed(
                title="🔐 歡迎來到 Artale Script 社群！",
                description="**您需要先進行序號驗證才能訪問會員功能**\n\n➤ 點擊下方按鈕開始驗證\n➤ 輸入您購買時獲得的授權序號\n➤ 驗證成功後即可使用所有功能",
                color=0x00d4ff
            )
            embed.add_field(
                name="📋 驗證後可獲得",
                value="• 軟體下載權限\n• 技術支援服務\n• 會員專屬討論\n• 最新更新通知",
                inline=False
            )
            embed.set_footer(text="如遇問題請聯繫管理員")
            
            view = VerificationView(bot)
            await member.send(embed=embed, view=view)
            logger.info(f"已發送驗證指引給 {member}")
            
        except discord.Forbidden:
            # 無法私訊用戶，在驗證頻道發送
            verification_channel = discord.utils.get(member.guild.channels, name="驗證")
            if verification_channel:
                embed.description = f"{member.mention}\n\n" + embed.description
                await verification_channel.send(embed=embed, view=VerificationView(bot))
                logger.info(f"在驗證頻道發送指引給 {member}")

    @bot.tree.command(name="verify", description="開始序號驗證流程")
    async def verify_command(interaction: discord.Interaction):
        """驗證斜線命令"""
        # 檢查是否已驗證
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if verified_role in interaction.user.roles:
            embed = discord.Embed(
                title="✅ 您已經通過驗證",
                description="您已經是會員了，無需重複驗證。",
                color=0x00ff88
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔐 序號驗證",
            description="點擊下方按鈕開始驗證流程",
            color=0x00d4ff
        )
        view = VerificationView(bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @bot.tree.command(name="status", description="檢查驗證狀態")
    async def status_command(interaction: discord.Interaction):
        """檢查驗證狀態"""
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        
        if verified_role in interaction.user.roles:
            # 獲取驗證詳情
            verification_info = "無法獲取詳細信息"
            if bot.db:
                try:
                    verification_ref = bot.db.collection('discord_verifications').document(str(interaction.user.id))
                    verification_doc = verification_ref.get()
                    if verification_doc.exists:
                        data = verification_doc.to_dict()
                        verified_at = data.get('verified_at')
                        if verified_at:
                            verification_info = f"驗證時間: {verified_at.strftime('%Y-%m-%d %H:%M:%S')}"
                except Exception as e:
                    logger.error(f"獲取驗證信息錯誤: {str(e)}")
            
            embed = discord.Embed(
                title="✅ 驗證狀態：已驗證",
                description=f"您是已驗證的會員用戶\n\n{verification_info}",
                color=0x00ff88
            )
        else:
            embed = discord.Embed(
                title="❌ 驗證狀態：未驗證",
                description="您尚未通過序號驗證\n使用 `/verify` 命令開始驗證",
                color=0xff4444
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="unverify", description="移除用戶驗證狀態（管理員專用）")
    @discord.app_commands.describe(user="要移除驗證的用戶")
    async def unverify_command(interaction: discord.Interaction, user: discord.Member):
        """移除驗證（管理員命令）"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 您沒有權限使用此命令。", ephemeral=True)
            return
        
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if verified_role in user.roles:
            await user.remove_roles(verified_role)
            
            # 從數據庫移除記錄
            if bot.db:
                try:
                    verification_ref = bot.db.collection('discord_verifications').document(str(user.id))
                    verification_ref.delete()
                    logger.info(f"管理員 {interaction.user} 移除了 {user} 的驗證")
                except Exception as e:
                    logger.error(f"刪除驗證記錄錯誤: {str(e)}")
            
            embed = discord.Embed(
                title="✅ 移除驗證成功",
                description=f"已移除 {user.mention} 的驗證狀態。",
                color=0x00ff88
            )
        else:
            embed = discord.Embed(
                title="ℹ️ 用戶未驗證",
                description=f"{user.mention} 尚未通過驗證。",
                color=0xffaa00
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)