import disnake
from disnake.ext import commands
import random
import asyncio
from utils.client import BotCore as Client
from utils.GenEMBED import Embed
from utils.music.checks import can_send_message_check

async def check_user(bot, ctx, uid, premium_check = False):
        userinfo = await bot.db_handler.get_userinfo(uid)
        if userinfo["status"] == "banned":
            await ctx.send(embed=Embed.gen_banned_embed(userinfo["time"], userinfo["ban_reason"]))
            return False
        if userinfo["status"] == "notfound":
            await ctx.send(embed=Embed.gen_nouser_embed(message="Không tìm thấy thông tin người dùng.\nHãy sử dụng lệnh `/register` để đăng ký."))
            return False
        if userinfo["status"] == "success":
            premium = userinfo["premium"] > int(disnake.utils.utcnow().timestamp())
            if premium_check and not premium:
                await ctx.send(embed=Embed.gen_error_embed("Tính năng này chỉ dành cho người dùng Premium."))
                return False
            return {"status": "success", "premium": premium}
        
class Minigame(commands.Cog):

    emoji = "🎮"
    name = "Minigame"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: Client):
         self.bot = bot

    @can_send_message_check()
    @commands.cooldown(1, 14400, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Nhận thưởng hằng ngày")
    async def daily(self, ctx: disnake.AppCommandInteraction):
        service = "daily"
        user_info = await check_user(self.bot, ctx, ctx.author.id)
        if not user_info: return
        premium = user_info["premium"]
        use = await self.bot.db_handler.use(ctx.author.id, service, premium)
        if use["status"] == "failed":
                            await ctx.channel.send(embed=Embed.gen_error_embed("Bạn đã điểm danh ngày hôm nay rồi!"))
                            return
        left = use["left"]
        await self.bot.db_handler.transaction(ctx.author.id, 5000, 10, reason="Nhận thưởng hằng ngày")
        if left > 0:
            await ctx.channel.send(f"Đã làm ủy thác ngày hôm nay, lần điểm danh tiếp theo của bạn là 4 tiếng nữa, số lần còn lại ngày hôm nay: {left} lần.")
            return
        await ctx.channel.send("Đã làm ủy thác thành công, bạn nhận được 5000 Mora và 10 Đá!")

def setup(bot: Client):
      bot.add_cog(Minigame(bot))