import disnake
from disnake import OptionType, File, utils
from disnake import Option, AppCommandInteraction, ApplicationCommandInteraction, OptionChoice
from disnake.ext import commands

import random
from random import randint
import aiohttp
import re
from urllib.parse import urlparse
from utils.client import BotCore
from traceback import print_exc


# Something xamlul

def gen_error_embed(error_msg: str):
    embed = disnake.Embed(title="❌ Đã xảy ra lỗi khi tạo emoji",
                          description=f"```{error_msg}```",
                          color=disnake.Color.red())
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1172052818501308427/1176426375704498257/1049220311318540338.png?ex=656ed370&is=655c5e70&hm=11d80b14a3ca28d04f7ac48d3a39b0c6d5947d20c9ae78cee9a4e511ce65f301&")
    return embed

async def check_duplicate_emoji(ctx: disnake.AppCommandInter, name: str):
        if not any(emoji.name == name for emoji in ctx.guild.emojis):
            return {
                "status": "success"
            }
        else:
            await ctx.send(embed=gen_error_embed("Tên emoji đã tồn tại"), ephemeral=True)
            print(f"[CMD - LOG : ERROR]{ctx.guild.name} - {ctx.guild.id} - {ctx.author.name} - {ctx.author.id} - {name} - Duplicate emoji")
            return {
                "status": "error"
            }   


    
    
class emoji(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot

    @commands.slash_command(name="emoji", description="Nhóm lệnh quản lý emoji trên server của bạn")
    async def emoji(self, ctx): pass

    @emoji.sub_command(name="create",
                       description="Tạo emoji mới",
                       options=[
                            Option(name="url", description="Đường dẫn ảnh để tạo emoji", type=OptionType.string, required=True),
                            Option(name="name", description="Tên emoji", type=OptionType.string, required=False), 
                            disnake.Option(name="private", description="Chế độ riêng tư", type=OptionType.boolean, required=False, choices=[
                OptionChoice(name="Bật", value=True),
                OptionChoice(name="Tắt", value=False)
            ])
                          ])
    async def emoji_create(self, ctx: ApplicationCommandInteraction, url: str = None, name: str = None, private: bool = False):
        await ctx.response.defer(ephemeral=private)  # Defer the response to avoid "This interaction failed" error
        if url is None:
            embed = disnake.Embed(title="❌ Bạn phải cung cấp tham số `url`", color=disnake.Color.red())
            await ctx.edit_original_message(embed=embed)
            return
        
        list_emoji = []

        if name is None: name = f"emoji_{str(randint(1000, 9999)).zfill(4)}"

        if url is not None:
            list_url = url.split(' ')
            async def check_url(url):
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            for items in list_url:
                items = items.split('?')[0]
                if await check_url(items) and items.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    list_emoji.append({
                        "name": f"emoji_{random.randint(1000, 9999)}" if name is None else name,
                        "url": items
                        })
                    
        if len(list_emoji) == 0:
            embed = disnake.Embed(
                title="<:AyakaAnnoyed:1135418690632957993> Không tìm thấy emoji nào trong yêu cầu của bạn",
                color=disnake.Color.red()
            )
            await ctx.edit_original_response(embed=embed)
            return
        
        try: # Func for add emoji by url
            for i in range(len(list_emoji)):
                emoji = list_emoji[i]
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji["url"]) as resp:
                        if resp.status != 200:
                            embed = disnake.Embed(
                                title="<:AyakaAnnoyed:1135418690632957993> Đã xảy ra lỗi!",
                                color=disnake.Colour.red(),
                            )
                            await ctx.edit_original_response(embed=embed)
                            return
                        img = await resp.read()
        except:
            embed = disnake.Embed(
                title="<:AyakaAnnoyed:1135418690632957993> Đã xảy ra lỗi!",
                color=disnake.Colour.red(),
            )
            await ctx.edit_original_response(embed=embed)
            print_exc()
            return

        try:
            await ctx.guild.create_custom_emoji(name=name, image=img, reason=f"{ctx.author.name} tạo emoji này")
            embed = disnake.Embed(title=f"<a:a_emoji169:1204063046717145128> Đã tạo emoji thành công [:{name}:]",
                                  color=disnake.Color.green())
            await ctx.edit_original_message(embed=embed)
        except Exception as e:
            if "Maximum number of emojis reached" in str(e):
                await ctx.edit_original_response("Số lượng emoji đã đạt giới hạn tối đa")
            elif "File cannot be larger than 256.0 kB" in str(e):
                await ctx.edit_original_response("Kích thước ảnh không được lớn hơn 256kb")
            else:
                embed = disnake.Embed(title="❌ Đã xảy ra lỗi khi tạo emoji",
                                    description=f"```{e}```",
                                    color=disnake.Color.red())
            await ctx.edit_original_message(embed=embed)
            
    # @commands.bot_has_guild_permissions(manage_emojis=True)
    @commands.slash_command(
        name="add_emoji",
        description="Thêm emoji vào server",
        options = [disnake.Option(
            name = "emoji",
            description = "Từ emoji mà bạn có thể sử dụng",
            type = OptionType.string,
            required = True
            ),
            disnake.Option(name="private", description="Chế độ riêng tư (Yêu cầu bạn phải bật nếu bạn ở trên kênh chat chính)", type=OptionType.boolean, required=False, choices=[
                OptionChoice(name="Bật", value=True),
                OptionChoice(name="Tắt", value=False)
            ])
            ])
    async def add_emoji(ctx: disnake.ApplicationCommandInteraction, emoji: str = None, private: bool = False):
        await ctx.response.defer(ephemeral=private)
        if emoji is None:
            embed = disnake.Embed(
                title="<:AyakaAnnoyed:1135418690632957993> Bạn phải cung cấp ít nhất một trong hai tham số `emoji` hoặc `url`",
                color=disnake.Color.red()
            )
            await ctx.edit_original_response(embed=embed)
            return
        list_emoji = []
        if emoji is not None:
            emoji_pattern = re.compile(r'<(a?:.*?:\d+)>')
            emoji_list = emoji_pattern.findall(emoji)
            for items in emoji_list:
                emoji_name = items.split(':')[1]
                emoji_id = items.split(':')[2]
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if items.startswith('a') else 'png'}"
                list_emoji.append({
                    "name": emoji_name,
                    "url": emoji_url
                    })
        
        from utils.music.errors import GenericError

        try:    
            check_emoji = await check_duplicate_emoji(ctx, list_emoji[0]["name"])
            if check_emoji["status"] == "error":
                return
        except IndexError:
            raise GenericError("Đã xảy ra lỗi khi thêm emoji, vui lòng thử lại :E")
            return
     
        
        
        if len(list_emoji) == 0:
            embed = disnake.Embed(
                title="<:AyakaAnnoyed:1135418690632957993> Không tìm thấy emoji nào trong yêu cầu của bạn",
                color=disnake.Color.red()
            )
            await ctx.edit_original_response(embed=embed)
            return
        try:
            for i in range(len(list_emoji)):
                emoji = list_emoji[i]
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji["url"]) as resp:
                        if resp.status != 200:
                            embed = disnake.Embed(
                                title="<:AyakaAnnoyed:1135418690632957993> Đã xảy ra lỗi!",
                                color=disnake.Colour.red(),
                            )
                            await ctx.edit_original_response(embed=embed)
                            return
                        img = await resp.read()

                await ctx.guild.create_custom_emoji(
                    name=emoji["name"],
                    image=img, reason=f"{ctx.author.name} đã copy emoji này :E"
                )
                embed = disnake.Embed(
                    title=f"<a:a_emoji169:1204063046717145128> Đã thêm emoji thành công! {i+1}/{len(list_emoji)}",
                    color=disnake.Colour.green(),
                )
                embed.set_author(
                    name=emoji["name"],
                    icon_url=emoji["url"]
                )
                embed.set_thumbnail(
                    url=emoji["url"]
                )
                await ctx.edit_original_response(embed=embed)
        except Exception as e:
            if "Missing Permissions" in str(e):
                await ctx.edit_original_response("Tớ thiếu quyền, hãy đảm bảo bạn đã bật 2 quyền sau trong role của tớ :< \n https://cdn.discordapp.com/attachments/1159485783800025230/1203882561940627476/image.png?ex=65d2b601&is=65c04101&hm=94f294ba1360bc97a6124e1e96c40f77c81b57050d1d99cb4185055f9f4b792e&")
                return

            if "Maximum number of emojis reached" in str(e):
                await ctx.edit_original_response("Server của cậu hết slot rồi, xóa bớt trước khi thêm lại nhé :<")
                return

            embed = disnake.Embed(
                title="<:AyakaAnnoyed:1135418690632957993> Đã xảy ra lỗi!",
                description=e,
                color=disnake.Colour.red(),
            )
            await ctx.edit_original_response(embed=embed)

def setup(bot: BotCore):
    bot.add_cog(emoji(bot))