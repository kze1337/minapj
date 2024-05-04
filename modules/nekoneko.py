import disnake
from disnake.ext import commands
from nekos.errors import NothingFound

from nekos import img


async def nekoneko():
    try:
        nekoimg = img("neko")
        
        return {
            "status": "Fetch_done",
            "neko_img": nekoimg
        }
    except NothingFound:
        return {
            "status": "Found_Nothing",
            "neko_img": None
        }
        
    
    
class MeoMeo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="neko", description="Lấy một hình ảnh mèo alimi ngẫu nhiên")
    async def neko(self, ctx: disnake.AppCommandInteraction):
        
        img = await nekoneko()
        if img["status"] != "Fetch_done":
            await ctx.edit_original_response("Api bị lỗi, không trả về kết quả nào")
            return        
        
        embed = disnake.Embed(description="neko neko nya")
        embed.set_image(img["neko_img"])
        await ctx.send(embed=embed)
        
def setup(bot: commands.Cog):
    bot.add_cog(MeoMeo(bot))
        