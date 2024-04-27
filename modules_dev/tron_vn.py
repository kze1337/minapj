import disnake
from disnake.ext import commands
import datetime
from utils.others import CustomContext
class Tron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("nitro")
    async def nitro_legacy(self, ctx: CustomContext):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.nitro.callback(self, ctx)

    @commands.slash_command(name="nitro", description="(J4F) Nitro free")
    async def nitro(self, ctx: disnake.AppCommandInteraction):
        embed = disnake.Embed(title="Món quà từ rừng xanh đây!", description=f"Nitro\n Hết hạn sau 48 giờ.", color=0x2F3136)
        embed.set_thumbnail("https://media.discordapp.net/attachments/899647915339972641/904326176909176882/EmSIbDzXYAAb4R7.png?ex=65ed94e2&is=65db1fe2&hm=1f84ca22e37acf8500d75c53ef78dd5abe55c98c08747412c184e78cc2208a8a&=&format=webp&quality=lossless")
        view = disnake.ui.View()
        button = view.add_item(disnake.ui.Button(label="Claim", custom_id="claim", style=disnake.ButtonStyle.green))
        button.timeout = 172800
        await ctx.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if interaction.author.bot:
            return
        button_id = interaction.component.custom_id
        if button_id == "claim":
            await interaction.response.send_message(f"{interaction.author.mention} Tưởng tượng cách anh bạn có thể nhận nitro free =)) \n https://tenor.com/view/hd-rickroll-rick-astley-4k-gif-23699798", ephemeral=True)


def setup(bot):
    bot.add_cog(Tron(bot))