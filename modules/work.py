import disnake
from disnake.ext import commands

from utils.client import BotCore as Client
from utils.GenEMBED import Embed
from utils.music.checks import can_send_message, can_send_message_check
import random


reasonList = [
    "Bạn vừa đi giật túi của người khác được {money} Mora!",
    "Bạn đi ăn xin được bố thí {money} Mora!",
    "Bạn đi phục vụ hộp đêm được tip {money} Mora!",
    "Bạn đang đi trên đường thì nhặt được {money} Mora. Bạn đã quyết định tạm thời bỏ túi luôn!",
    "Bạn vừa đòi nợ thằng bạn và lấy được {money} Mora!",
    "Bạn vừa đi đánh đề và thắng được {money} Mora!",
    "Bạn làm bartender đi lắc nước được {money} Mora!",
    "Bạn tạo kênh youtube được donate {money} Mora!",
    "Bạn đi ăn tết thì được {nguoithan} lì xì cho {money} Mora!",
    "Bạn vừa nhận lương tháng và được {money} Mora!",
    "Bạn đi làm thêm và kiếm được {money} Mora!",
    "Bạn vừa bán được một món đồ và thu được {money} Mora!",
    "Bạn vừa nhận tiền thưởng và được {money} Mora!",
    "Bạn vừa trúng số và nhận được {money} Mora!",
    "Bạn vừa bán được một món đồ quý hiếm và thu được {money} Mora!",
    "Bạn vừa hoàn thành một nhiệm vụ và nhận được {money} Mora!",
    "Bạn vừa bán được một món đồ và kiếm được {money} Mora!",
    "Bạn vừa nhận được quà tặng và được {money} Mora!",
    "Bạn vừa nhận được tiền thưởng và kiếm được {money} Mora!"
]

subtractReasonList = [
    "Bạn đang đứng đường thì bị công an bắt và bị phạt {money} Mora.",
    "Sau khi bạn phục vụ thì bị khách quỵt mất {money} Mora.",
    "Bạn vừa phát hiện khách bạn bị HIV, đi chữa mất {money} Mora.",
    "Đang phục vụ thì bị đưa đi cách ly bắt buộc, tốn mất {money} Mora.",
    "Bạn sau khi làm xong thì bị nhà nghỉ chém giá, lỗ mất {money} Mora.",
    "Đang đánh bài thì công an ập vô tóm, lỗ mất {money} Mora.",
    "Bạn vừa bị trộm cắp và mất đi {money} Mora.",
    "Bạn vừa mua một món đồ đắt tiền và bị trừ đi {money} Mora.",
    "Bạn vừa bị lừa đảo và mất đi {money} Mora.",
    "Bạn vừa đặt cược và thua {money} Mora.",
    "Bạn vừa mua một món đồ giả mạo và bị trừ đi {money} Mora.",
    "Bạn vừa bị phạt vì vi phạm luật và mất đi {money} Mora.",
    "Bạn vừa mua một món đồ không cần thiết và bị trừ đi {money} Mora.",
    "Bạn vừa bị trừ tiền phạt vì quên trả sách và mất đi {money} Mora.",
    "Bạn vừa mua một món đồ không hợp lý và bị trừ đi {money} Mora.",
    "Bạn vừa bị trừ tiền phạt vì quên trả phí gửi xe và mất đi {money} Mora."
]


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

class Work(commands.Cog):

    emoji = "🎮"
    name = "Minigame"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: Client):
        self.bot = bot

    
    @can_send_message_check()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Kiếm tiền!")
    async def work(self, ctx: disnake.AppCommandInteraction):
        random_tien = random.randint(500, 1000)
        user_info = await check_user(self.bot, ctx, ctx.author.id)
        if not user_info: return
        reason = random.choice(reasonList).replace('{money}', "<:m1_mora:1169483093233631304> " + f"{random_tien}")

        if "{nguoithan}" in reason:
            nguoithan = ["Cô", "Dì", "Chú", "Bác", "Ông", "Bà", "Bố", "Mẹ"]
            rand_nguoithan = random.choice(nguoithan)
            reason = reason.replace("{nguoithan}", rand_nguoithan)

        await self.bot.db_handler.transaction(ctx.author.id, random_tien, 0, reason=reason)

        await ctx.channel.send(reason)

    @can_send_message_check()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Kiếm tiền nhiều hơn lệnh `work` nhưng sẽ có tỉ lệ thua")
    async def slut(self, ctx: disnake.AppCommandInteraction):
        random_tien = random.randint(4000, 10000)
        user_info = await check_user(self.bot, ctx, ctx.author.id)
        if not user_info: return
        user_money = await self.bot.db_handler.get_userinfo(ctx.author.id)
        if user_money["coin"]==0:
            await ctx.channel.send(f"Bạn hết tiền r")
            return
        status = random.randint(0, 1)
        if status == 1:
            await self.bot.db_handler.transaction(ctx.author.id, random_tien, 0, reason="Nhận tiền từ việc chơi game")
            await ctx.channel.send(f"Bạn đã nhận được <:m1_mora:1169483093233631304> {random_tien} mora.")
        else:
            _random_tien = random.randint(2000, 500)
            if user_money["coin"] < _random_tien: 
                _random_tien == user_money["coin"]
            _reason = random.choice(subtractReasonList).replace('{money}', "<:m1_mora:1169483093233631304> " + f"{_random_tien}")
            await self.bot.db_handler.transaction(ctx.author.id, 
                                                        0 - _random_tien, 
                                                        0, 
                                                            reason=_reason)
            await ctx.channel.send(_reason)


def setup(bot: Client):
    bot.add_cog(Work(bot))



        
