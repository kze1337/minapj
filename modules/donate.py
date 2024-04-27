import disnake
from disnake.ext import commands

class Donate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(name="donate", description="Ủng hộ bot bằng cách donate")
    async def donate(self, ctx: disnake.ApplicationCommandInteraction):
        embed =  disnake.Embed()
        embed.title = "Ủng hộ bot"
        embed.description = "Ủng hộ bot của tui ở đây: [TOPGG](https://top.gg/bot/1119870633468235817)\n Hoặc bạn có thể hỗ trợ thằng chủ chút kinh phí host bot ở đây [MOMO](https://me.momo.vn/JeIJCztot4IEU1UlC5sd)"
        embed.set_thumbnail("https://media.discordapp.net/attachments/781481778795118612/1171808831211327578/received_1519324505305020.gif?ex=66042404&is=65f1af04&hm=e87cb8841c4399230fee80bb9485b7f1e605e3ed92f43c350d60afad42746a74&")

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Donate(bot))