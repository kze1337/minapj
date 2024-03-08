import disnake
from disnake.ext import commands    
import random
import asyncio
from utils.GenEMBED import Embed
from utils.client import BotCore as Client
from utils.others import CustomContext

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

class CoinFlip(commands.Cog):

    emoji = "🎮"
    name = "Minigame"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: Client):
        self.bot = bot

    @commands.cooldown(1, 15, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Coin flip", aliases=["cf"])
    async def coinflip(self, ctx: CustomContext, cuoc: int = None, choice: str = "heads"):
            if cuoc is None:
                await ctx.channel.send("Hãy nhập số tiền cược!")
                return
            if cuoc < 0:
                await ctx.channel.send("Số tiền cược không hợp lệ!")
                return
            if choice not in ["heads", "tails"]:
                return            
            
            user_info = await check_user(self.bot, ctx, ctx.author.id)
            if not user_info: return
            coin = await self.bot.db_handler.fetch_money(ctx.author.id)
            if coin == 0:
                await ctx.channel.send("Bạn không có đủ tiền để chơi!")
                return
            if cuoc > coin:
                cuoc == coin    

            rand = random.randint(0, 2)
            if rand == 0:
                result = "heads"
                _emoji = "<:head:1215646268353806356>"
            elif rand == 1:
                result = "tails"
                _emoji = "<:tail:1215646566879338527>"
            elif rand == 2:
                result = "Đang tung đồng xu thì đồng xu rơi xuống đất và biến mất..."
            msg = await ctx.channel.send(f"Đang tung đồng xu... <a:coinflip:1215646423262175243>")
            await asyncio.sleep(3)
            if result == choice:
                await self.bot.db_handler.transaction(ctx.author.id, cuoc*2, 0, reason="Coinflip")
                await msg.edit(f"Kết quả: {_emoji}! Bạn đã thắng {cuoc*2} Mora!")

            elif "Đang tung đồng xu thì đồng xu rơi xuống đất và biến mất..." in result:
                await msg.edit(f"{result} <a:dead:1215647824654508083>, Bạn mất {cuoc} Mora!")
                await self.bot.db_handler.transaction(ctx.author.id, 0 - cuoc, 0, reason="Bị bet scam")

            else:
                await self.bot.db_handler.transaction(ctx.author.id, 0 - cuoc, 0, reason="Coinflip")
                await msg.edit(f"Kết quả: {_emoji}! Bạn đã thua {cuoc} Mora!")

def setup(bot):
    bot.add_cog(CoinFlip(bot))