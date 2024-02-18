import disnake
from disnake.ext import commands


from utils.client import BotCore


class Ping(commands.Cog):
    def __init__(self, bot: BotCore):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        embed = disnake.Embed(
            title="Pong!",
            description=f"Độ trễ API: {round(self.bot.latency * 100)}ms"
                        f"\nĐộ trễ Websocket: {round(self.bot.ws.latency * 100)}ms",
            color=disnake.Color.green()
        )
        await ctx.send(embed=embed)

def setup(bot: BotCore):
    bot.add_cog(Ping(bot))