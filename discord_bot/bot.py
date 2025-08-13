"""
Discord 機器人主程式 - 專業驗證體驗版本
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
        self.verification_panel_sent = False

    async def setup_hook(self):
        """機器人啟動時的設置"""
        try:
            # 同步斜線命令
            synced = await self.tree.sync()
            logger.info(f"✅ 已同步 {len(synced)} 個斜線命令")
            
        except Exception as e:
            logger.error(f"❌ 機器人設置失敗: {e}")

    async def on_ready(self):
        """機器人準備就緒"""
        logger.info(f'✅ {self.user} 已成功連線到 Discord！')
        logger.info(f'📊 已連接到 {len(self.guilds)} 個伺服器')
        
        # 設置機器人狀態
        try:
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.watching, 
                    name="會員驗證 | 點擊按鈕驗證"
                )
            )
            logger.info("✅ 機器人狀態設置成功")
        except Exception as status_error:
            logger.warning(f"⚠️ 無法設置機器人狀態: {status_error}")
        
        # 檢查並設置伺服器
        for guild in self.guilds:
            logger.info(f"🏠 伺服器: {guild.name} (ID: {guild.id})")
            await self.setup_guild_roles(guild)
            await self.setup_verification_panel(guild)

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
            else:
                logger.info(f"✅ {guild.name} 中已存在驗證角色")
            
            # 創建未驗證角色
            unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
            if not unverified_role:
                unverified_role = await guild.create_role(
                    name=UNVERIFIED_ROLE_NAME,
                    color=discord.Color.light_grey(),
                    reason="自動創建未驗證角色",
                    mentionable=False
                )
                logger.info(f"✅ 已在 {guild.name} 創建未驗證角色")
            else:
                logger.info(f"✅ {guild.name} 中已存在未驗證角色")
                
        except discord.Forbidden:
            logger.error(f"❌ 機器人在 {guild.name} 沒有管理角色權限")
        except Exception as e:
            logger.error(f"❌ 設置 {guild.name} 角色時出錯: {e}")

    async def setup_verification_panel(self, guild):
        """自動設置驗證面板"""
        try:
            # 尋找驗證頻道
            verification_channel = discord.utils.get(guild.channels, name=VERIFICATION_CHANNEL)
            
            if not verification_channel:
                logger.warning(f"⚠️ 在 {guild.name} 中找不到 #{VERIFICATION_CHANNEL} 頻道")
                return
            
            # 檢查頻道中是否已有驗證面板
            async for message in verification_channel.history(limit=50):
                if (message.author == self.user and 
                    message.embeds and 
                    "會員驗證中心" in message.embeds[0].title):
                    logger.info(f"✅ {guild.name} 驗證面板已存在")
                    # 重新添加持久化視圖
                    view = PersistentVerificationView(self)
                    self.add_view(view)
                    return
            
            # 創建新的驗證面板
            await self.send_verification_panel(verification_channel)
            
        except Exception as e:
            logger.error(f"❌ 設置驗證面板時出錯: {e}")

    async def send_verification_panel(self, channel):
        """發送驗證面板到指定頻道"""
        try:
            embed = discord.Embed(
                title="🔐 會員驗證中心",
                description="**✨ 購買感謝**\n感謝您購買 ScriLab 產品！請按照以下步驟完成驗證：\n\n"
                           "**🎯 驗證流程**\n"
                           "1️⃣ 點擊下方 **🔓 開始驗證** 按鈕\n"
                           "2️⃣ 在彈出視窗中輸入您的序號\n"
                           "3️⃣ 系統自動驗證並授予權限\n"
                           "4️⃣ 即可訪問所有會員專區！\n\n"
                           "**💡 序號在哪裡？**\n"
                           "• 購買確認郵件中\n"
                           "• Gumroad 下載頁面\n"
                           "• 格式：ABC123-DEF456-GHI789",
                color=0x00d4ff
            )
            
            embed.add_field(
                name="🚨 注意事項",
                value="• 每個序號只能使用一次\n• 序號區分大小寫\n• 輸入時請確保沒有多餘空格",
                inline=False
            )
            
            embed.add_field(
                name="⏰ 驗證成功後您將獲得",
                value="🎯 會員專屬頻道訪問權\n📥 軟體下載權限\n🆘 優先技術支援\n💎 VIP 專屬內容",
                inline=False
            )
            
            embed.add_field(
                name="❓ 遇到問題？",
                value="• 序號無效：請檢查格式是否正確\n• 驗證失敗：請聯繫客服支援\n• 其他問題：查看常見問題",
                inline=False
            )
            
            embed.set_footer(text="ScriLab Official • 自動驗證系統")
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/🔐.png")
            
            view = PersistentVerificationView(self)
            message = await channel.send(embed=embed, view=view)
            
            # 添加持久化視圖
            self.add_view(view)
            
            logger.info(f"✅ 驗證面板已發送到 #{channel.name}")
            
        except Exception as e:
            logger.error(f"❌ 發送驗證面板失敗: {e}")

    async def on_member_join(self, member):
        """新成員加入時的處理"""
        try:
            guild = member.guild
            logger.info(f"👋 新成員 {member.name} 加入 {guild.name}")
            
            # 給予未驗證角色
            unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
            if unverified_role:
                await member.add_roles(unverified_role, reason="新成員自動角色")
                logger.info(f"✅ 已給予 {member.name} 未驗證角色")
            
            # 發送歡迎私訊
            try:
                embed = discord.Embed(
                    title="🎉 歡迎加入 ScriLab 官方社群！",
                    description=f"親愛的 {member.mention}，歡迎來到我們的官方 Discord 社群！\n\n"
                               "**🔐 下一步該做什麼？**\n"
                               f"請前往 <#{discord.utils.get(guild.channels, name=VERIFICATION_CHANNEL).id}> 驗證您的購買序號\n\n"
                               "**💡 序號從哪裡獲得？**\n"
                               "購買完成後，序號會發送到您的郵箱中\n\n"
                               "**🎯 驗證後可以享受：**\n"
                               "• 會員專屬頻道\n"
                               "• 軟體下載權限\n"
                               "• 優先技術支援\n"
                               "• VIP 專屬內容",
                    color=0x00ff88
                )
                embed.set_footer(text="感謝您選擇 ScriLab 產品！")
                await member.send(embed=embed)
                logger.info(f"✅ 已發送歡迎私訊給 {member.name}")
            except discord.Forbidden:
                logger.info(f"⚠️ 無法發送私訊給 {member.name}")
                
        except Exception as e:
            logger.error(f"❌ 處理新成員加入時出錯: {e}")

    async def on_message(self, message):
        """監控驗證頻道訊息"""
        # 如果不是在驗證頻道，忽略
        if message.channel.name != VERIFICATION_CHANNEL:
            return
        
        # 如果是機器人訊息，忽略
        if message.author.bot:
            return
        
        # 刪除用戶在驗證頻道的訊息（保持頻道整潔）
        try:
            await message.delete()
            
            # 發送提示訊息
            embed = discord.Embed(
                title="💡 請使用驗證按鈕",
                description=f"{message.author.mention} 請點擊上方的 **🔓 開始驗證** 按鈕進行驗證，而不是直接發送訊息。",
                color=0xffaa00
            )
            
            temp_message = await message.channel.send(embed=embed)
            
            # 10秒後刪除提示訊息
            await asyncio.sleep(10)
            await temp_message.delete()
            
        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"❌ 處理驗證頻道訊息時出錯: {e}")

class AdvancedVerificationModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="🔐 ScriLab 會員驗證", timeout=600)
        self.bot = bot
    
    uuid_input = discord.ui.TextInput(
        label="請輸入您的購買序號",
        placeholder="格式：ABC123-DEF456-GHI789（請確保格式正確）",
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
                title="🚫 驗證次數限制",
                description="⏰ 您的驗證嘗試次數過多，請 **10 分鐘**後再試。\n\n"
                           "這是為了防止惡意嘗試而設置的安全機制。",
                color=0xff4444
            )
            embed.add_field(
                name="💡 小提示", 
                value="請仔細確認您的序號格式，避免重複錯誤嘗試", 
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 顯示驗證中狀態
        embed = discord.Embed(
            title="⏳ 正在驗證中...",
            description="請稍候，系統正在驗證您的序號...",
            color=0xffaa00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        try:
            # 驗證序號
            is_valid, result = await verify_user_uuid(uuid, self.bot.db)
            
            if is_valid:
                # 驗證成功處理
                await self.handle_successful_verification(interaction, result)
            else:
                # 驗證失敗處理
                await self.handle_failed_verification(interaction, result, user_id)
                
        except Exception as e:
            logger.error(f"❌ 驗證過程出錯: {str(e)}")
            await self.handle_verification_error(interaction)

    async def handle_successful_verification(self, interaction, user_data):
        """處理驗證成功"""
        try:
            guild = interaction.guild
            member = interaction.user
            
            # 角色管理
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
            
            # 移除未驗證角色
            if unverified_role and unverified_role in member.roles:
                await member.remove_roles(unverified_role, reason="驗證成功")
            
            # 準備成功訊息
            plan_type = user_data.get('plan_type', '標準會員')
            expires_info = ""
            
            if 'expires_at' in user_data:
                expires_at = user_data['expires_at']
                if hasattr(expires_at, 'strftime'):
                    expires_info = f"\n📅 有效期至：{expires_at.strftime('%Y年%m月%d日')}"
            
            # 發送成功訊息
            embed = discord.Embed(
                title="🎉 驗證成功！歡迎加入會員！",
                description=f"恭喜 {member.mention}！您的帳號已成功驗證！\n\n"
                           f"**📦 您的方案：** {plan_type}{expires_info}\n"
                           f"**🔓 解鎖內容：** 所有會員專區現已開放！",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎯 您現在可以：",
                value="• 🗣️ 參與會員專屬討論\n"
                      "• 📥 下載專屬軟體資源\n"
                      "• 🆘 獲得優先技術支援\n"
                      "• 💎 查看 VIP 專屬內容",
                inline=False
            )
            
            embed.add_field(
                name="🚀 建議您接下來：",
                value="• 查看 <#軟體下載> 獲取最新版本\n"
                      "• 閱讀 <#使用教學> 快速上手\n"
                      "• 加入 <#會員聊天> 與其他用戶交流",
                inline=False
            )
            
            embed.set_footer(text="感謝您對 ScriLab 的支持！")
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/🎉.png")
            
            await interaction.edit_original_response(embed=embed)
            logger.info(f"✅ {member.name}#{member.discriminator} 驗證成功 ({plan_type})")
            
        except Exception as e:
            logger.error(f"❌ 處理驗證成功時出錯: {e}")
            await self.handle_verification_error(interaction)

    async def handle_failed_verification(self, interaction, error_message, user_id):
        """處理驗證失敗"""
        record_failed_attempt(user_id)
        
        embed = discord.Embed(
            title="❌ 驗證失敗",
            description=f"**錯誤原因：** {error_message}",
            color=0xff4444
        )
        
        embed.add_field(
            name="🔍 常見問題排查",
            value="• **格式錯誤**：確認序號包含所有字符\n"
                  "• **大小寫**：序號區分大小寫\n"
                  "• **空格**：確認沒有多餘的空格\n"
                  "• **已使用**：每個序號只能使用一次",
            inline=False
        )
        
        embed.add_field(
            name="💬 需要協助？",
            value="• 檢查購買確認郵件中的序號\n"
                  "• 確認您購買的是正確的產品\n"
                  "• 如問題持續，請聯繫客服支援",
            inline=False
        )
        
        embed.set_footer(text="請仔細檢查序號後重試")
        
        await interaction.edit_original_response(embed=embed)
        logger.warning(f"❌ {interaction.user.name} 驗證失敗: {error_message}")

    async def handle_verification_error(self, interaction):
        """處理驗證系統錯誤"""
        embed = discord.Embed(
            title="⚠️ 系統暫時無法使用",
            description="驗證系統目前暫時無法使用，請稍後再試。\n\n"
                       "如果問題持續，請聯繫管理員協助處理。",
            color=0xffaa00
        )
        embed.add_field(
            name="🔄 建議操作",
            value="• 等待 5-10 分鐘後重試\n• 確認網路連接正常\n• 聯繫技術支援",
            inline=False
        )
        
        try:
            await interaction.edit_original_response(embed=embed)
        except:
            await interaction.followup.send(embed=embed, ephemeral=True)

class PersistentVerificationView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # 持久化視圖，永不過期
        self.bot = bot
    
    @discord.ui.button(
        label='🔓 開始驗證', 
        style=discord.ButtonStyle.success, 
        emoji='🔐',
        custom_id='verification_button_persistent'
    )
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 檢查是否在正確的頻道
        if interaction.channel.name != VERIFICATION_CHANNEL:
            embed = discord.Embed(
                title="⚠️ 錯誤的頻道",
                description=f"請在 <#{discord.utils.get(interaction.guild.channels, name=VERIFICATION_CHANNEL).id}> 頻道進行驗證",
                color=0xffaa00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 檢查是否已經驗證
        verified_role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if verified_role and verified_role in interaction.user.roles:
            embed = discord.Embed(
                title="✅ 您已經是認證會員",
                description="您已經通過驗證，擁有所有會員權限！\n\n"
                           "**🎯 您可以前往：**\n"
                           "• <#軟體下載> 獲取最新版本\n"
                           "• <#會員聊天> 與其他會員交流\n"
                           "• <#技術支援> 獲得專業協助",
                color=0x00ff88
            )
            embed.set_footer(text="感謝您的支持！")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 開始驗證流程
        await interaction.response.send_modal(AdvancedVerificationModal(self.bot))
        logger.info(f"🔐 {interaction.user.name} 開始驗證流程")

def setup_bot_commands(bot):
    """設置機器人命令"""
    
    # 管理員專用命令
    @bot.tree.command(name="admin_panel", description="🛠️ 管理員控制面板")
    @discord.app_commands.default_permissions(administrator=True)
    async def admin_panel(interaction: discord.Interaction):
        """管理員控制面板"""
        embed = discord.Embed(
            title="🛠️ ScriLab 管理員控制面板",
            description="選擇您要執行的管理操作：",
            color=0x5865f2
        )
        
        view = AdminPanelView(bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @bot.tree.command(name="verify_status", description="📊 檢查驗證統計")
    @discord.app_commands.default_permissions(administrator=True)
    async def verify_status(interaction: discord.Interaction):
        """檢查驗證統計"""
        guild = interaction.guild
        
        verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
        
        verified_count = len(verified_role.members) if verified_role else 0
        unverified_count = len(unverified_role.members) if unverified_role else 0
        total_members = guild.member_count
        
        embed = discord.Embed(
            title="📊 會員驗證統計",
            color=0x00d4ff
        )
        
        embed.add_field(name="👥 總成員數", value=f"`{total_members}`", inline=True)
        embed.add_field(name="✅ 已驗證", value=f"`{verified_count}`", inline=True)
        embed.add_field(name="⏳ 未驗證", value=f"`{unverified_count}`", inline=True)
        
        verification_rate = (verified_count / max(total_members - 1, 1)) * 100  # 排除機器人
        embed.add_field(name="📈 驗證率", value=f"`{verification_rate:.1f}%`", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="reset_verification", description="🔄 重新發送驗證面板")
    @discord.app_commands.default_permissions(administrator=True)
    async def reset_verification(interaction: discord.Interaction):
        """重新發送驗證面板"""
        verification_channel = discord.utils.get(interaction.guild.channels, name=VERIFICATION_CHANNEL)
        
        if not verification_channel:
            await interaction.response.send_message(
                f"❌ 找不到 `#{VERIFICATION_CHANNEL}` 頻道", 
                ephemeral=True
            )
            return
        
        # 清理舊的驗證面板
        async for message in verification_channel.history(limit=50):
            if message.author == bot.user:
                await message.delete()
        
        # 發送新的驗證面板
        await bot.send_verification_panel(verification_channel)
        
        await interaction.response.send_message(
            f"✅ 已在 {verification_channel.mention} 重新發送驗證面板", 
            ephemeral=True
        )
        logger.info(f"🔄 管理員 {interaction.user.name} 重置了驗證面板")

class AdminPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
    
    @discord.ui.button(label='📊 查看統計', style=discord.ButtonStyle.primary)
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
        
        verified_count = len(verified_role.members) if verified_role else 0
        unverified_count = len(unverified_role.members) if unverified_role else 0
        
        embed = discord.Embed(title="📊 詳細統計", color=0x00d4ff)
        embed.add_field(name="已驗證會員", value=verified_count, inline=True)
        embed.add_field(name="未驗證用戶", value=unverified_count, inline=True)
        embed.add_field(name="總成員", value=guild.member_count, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='🔄 重置面板', style=discord.ButtonStyle.secondary)
    async def reset_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        verification_channel = discord.utils.get(interaction.guild.channels, name=VERIFICATION_CHANNEL)
        
        if verification_channel:
            # 清理並重新發送
            async for message in verification_channel.history(limit=50):
                if message.author == self.bot.user:
                    await message.delete()
            
            await self.bot.send_verification_panel(verification_channel)
            await interaction.response.send_message("✅ 驗證面板已重置", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 找不到驗證頻道", ephemeral=True)
    
    @discord.ui.button(label='🧹 清理頻道', style=discord.ButtonStyle.danger)
    async def cleanup_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        verification_channel = discord.utils.get(interaction.guild.channels, name=VERIFICATION_CHANNEL)
        
        if verification_channel:
            deleted = 0
            async for message in verification_channel.history(limit=100):
                if not (message.author == self.bot.user and message.embeds and 
                       "會員驗證中心" in message.embeds[0].title):
                    await message.delete()
                    deleted += 1
            
            await interaction.response.send_message(f"🧹 已清理 {deleted} 條訊息", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 找不到驗證頻道", ephemeral=True)
