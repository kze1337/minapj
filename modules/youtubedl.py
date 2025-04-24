import asyncio

from disnake.ext import commands
from disnake import Embed, File, Option, OptionType, AppCommandInteraction, ApplicationCommandType, ButtonStyle
from disnake.ui import Button,View
from utils.client import BotCore
from tools.youtube_downloader import download_audio, FileTooLargeError
from asgiref.sync import sync_to_async
import os
import pathlib
from urllib.parse import urlparse, parse_qs
from utils.music.converters import YOUTUBE_VIDEO_REG

status = {
    0: "<:waitt:1364952189654536232>",
    1: "<a:aloading:1229108110577107077>",
    2: "✅",
    3: "❌"
}

image_links = {
    "stamp0837": "https://i.ibb.co/0b34vSs/stamp0837.png",
    "stamp0234-4598": "https://i.ibb.co/LdFpHBkT/stamp0234-4598.png",
    "stamp0238": "https://i.ibb.co/VYc8pVDN/stamp0238.png",
    "stamp0415-5033": "https://i.ibb.co/3mhhGSMT/stamp0415-5033.png",
    "stamp0636-5696": "https://i.ibb.co/8LJMVrPQ/stamp0636-5696.png",
    "stamp0787": "https://i.ibb.co/gLggt8VZ/stamp0787.png"
}

class YoutubeTools(commands.Cog):
    def __init__(self, bot: BotCore):
        self.bot = bot
        self.download_limitsize = {
            0: 10 * 1024 * 1024,
            1: 10 * 1024 * 1024,
            2: 35 * 1024 * 1024,
            3: 75 * 1024 * 1024
        }
        self.downloaded = None

    @staticmethod
    def render_embed(stat1 = status.get(0), stat2 = status.get(0), stat3 = status.get(0), error = None, image = image_links.get("stamp0787")) -> Embed:

        embed = Embed(title="Downloading data...", color=0x00ff00)
        embed.description = f"""
                                ## <:api:1249300230336155719> Đang tải dữ liệu từ api về...
                                > {stat1} Đang lấy dữ liệu
                                > {stat2} Đang tải về...
                                > {stat3} Xử lí những bước cuối cùng...
                                {"> Đã xảy ra lỗi: " + error if error else ""}
                                """

        if image:
            embed.set_thumbnail(image)

        if error:
            embed.set_thumbnail(url=image_links.get("stamp0238"))

        return embed

    @staticmethod
    def parse_discord_url(url) -> int:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        ex_hex = query_params.get('ex', [None])[0]
        if not ex_hex:
            return 0
        try:
            timestamp = int(ex_hex, 16)
            return timestamp
        except ValueError:
            return 0

    async def get_file(self, url: str, guild_id, user_id, boost_tier, ctx: AppCommandInteraction):
        limit = self.download_limitsize.get(boost_tier, 10)
        download_folder = pathlib.Path(f'./downloads/{guild_id}/{user_id}')
        download_folder.mkdir(parents=True, exist_ok=True)
        try:
            await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                        stat2=status.get(1),
                                                                        stat3=status.get(0)))
            await sync_to_async(download_audio)(url, download_folder, 'mp3', 192, limit)
        except FileTooLargeError:
            await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                    stat2=status.get(3),
                                                                    stat3=status.get(3),
                                                                    error=f"Video bạn gửi có phần âm thanh nặng vượt quá khả năng upload của máy chủ này ({self.download_limitsize.get(ctx.guild.premium_tier)})."))
            return
        except Exception:
            await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                        stat2=status.get(3),
                                                                        stat3=status.get(3)))
            return None

        return download_folder


    @commands.slash_command(name="getaudio", description="Download audio from a YouTube video", options=[Option(name="url",
                                                                                                                description="YouTube video URL",
                                                                                                                type=OptionType.string,
                                                                                                                required=True)])
    async def get_audio(self, ctx: AppCommandInteraction, url: str):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        boost_tier = ctx.guild.premium_tier
        file = None
        await ctx.response.defer()

        if not YOUTUBE_VIDEO_REG.match(url):
            await ctx.edit_original_response(f"❌ URL này không hợp lệ hoặc không phải là link youtube.")
            return

        await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2)))

        download_folder = await self.get_file(url, guild_id, user_id, boost_tier, ctx)

        if download_folder is None or len(os.listdir(download_folder)) == 0:
            await ctx.edit_original_response(f"Đã xảy ra lỗi trong quá trình tải video. Vui lòng thử lại sau.")
            return

        await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                    stat2=status.get(2),
                                                                    stat3=status.get(1)))

        await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                    stat2=status.get(2),
                                                                    stat3=status.get(2)))

        await asyncio.sleep(1)

        for file in os.listdir(download_folder):
            file_path = os.path.join(download_folder, file)
            if os.path.isfile(file_path):
                file = await ctx.edit_original_response(file=File(file_path), embed=None)
                os.remove(file_path)

        attachment = file.attachments[0].url
        self.downloaded = attachment
        timestamp = self.parse_discord_url(attachment)
        txt = ""
        cmd = f"</play:" + str(self.bot.get_global_command_named("play", cmd_type=ApplicationCommandType.chat_input).id) + ">"

        embed = Embed(title="Video của bạn đã được tải về", color=0x00ff00)
        txt += f"> 📹 **Video**: {url}\n"
        txt += f"> <:timeout:1155781760571949118> Video sẽ hết hạn sau <t:{timestamp}:R>\n"
        txt += f"> <:star3:1155781751914889236> Sao chép link video sau đó dán vào lệnh {cmd} để phát bài hát này\n"
        txt += f"```{attachment}```"
        embed.description = txt
        embed.set_thumbnail(image_links.get("stamp0234-4598"))
        btn = Button(label="Phát ngay", custom_id="ytdl-playnow-btn", style=ButtonStyle.green, disabled=True)
        await ctx.edit_original_response(embed=embed, view=View(timeout=70).add_item(btn))




def setup(bot: BotCore):
    bot.add_cog(YoutubeTools(bot))