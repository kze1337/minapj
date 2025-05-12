import asyncio
import os
import pathlib
import re

from disnake.ext import commands
from disnake import Embed, File, Option, OptionType, AppCommandInteraction, ApplicationCommandType, ButtonStyle, \
    MessageInteraction
from disnake.ui import Button,View

from utils.client import BotCore
from utils.music.spotify import spotify_regex
from utils.music.converters import YOUTUBE_VIDEO_REG
from utils.music.checks import check_voice

from tools.youtube_downloader import YoutubeDownloader, FileTooLargeError
from tools.spotify.spotify_url_resolver import Spotify_Worker

from asgiref.sync import sync_to_async
from urllib.parse import urlparse, parse_qs

sound_cloud_regex = re.compile(r"https?:\/\/(?:www\.)?soundcloud\.com\/[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)?\/?(?:[\?#].*)?$")

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
        self.yt_dlp_client = YoutubeDownloader()

    @staticmethod
    def render_embed(stat1 = status.get(0),
                        stat2 = status.get(0), stat3 = status.get(0),
                        error = None,
                        image = image_links.get("stamp0787"),
                        is_resolve_spotify = False) -> Embed:
        if not is_resolve_spotify:
            embed = Embed(title="Downloading data...", color=0x00ff00)
            embed.description = f"""
                                    ## <:api:1249300230336155719> Đang tải dữ liệu từ api về...
                                    > {stat1} Đang lấy dữ liệu
                                    > {stat2} Đang tải về...
                                    > {stat3} Xử lí những bước cuối cùng...
                                    {"> Đã xảy ra lỗi: " + error if error else ""}
                                    """
        else:
            embed = Embed(title="Resolving data...", color=0x00ff00)
            embed.description = f"""
                                    ## <:api:1249300230336155719> Đang phân tích dữ liệu từ api...
                                    > {stat1} Đang lấy dữ liệu
                                    > {stat2} Đang phân tích...
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
            await sync_to_async(self.yt_dlp_client.download_audio)(url, download_folder, 'mp3', limit)
        except FileTooLargeError:
            await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                    stat2=status.get(3),
                                                                    stat3=status.get(3),
                                                                    error=f"Video bạn gửi có phần âm thanh nặng vượt quá khả năng upload của máy chủ này ({self.download_limitsize.get(ctx.guild.premium_tier)})."))
            return None
        except Exception as e:
            await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                        stat2=status.get(3),
                                                                        stat3=status.get(3), error=str(e)))
            return None

        return download_folder

    @commands.cooldown(1, 25, commands.BucketType.user)
    @check_voice()
    @commands.guild_only()
    @commands.slash_command(name="getaudio", description="Download audio from a video / spotify links", options=[Option(name="url",
                                                                                                                description="YouTube video URL",
                                                                                                                type=OptionType.string,
                                                                                                                required=True)])
    async def get_audio(self, ctx: AppCommandInteraction, url: str):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        boost_tier = ctx.guild.premium_tier
        file = None
        await ctx.response.defer()

        if spotify_regex.match(url):
            await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                        stat2=status.get(1),
                                                                        stat3=status.get(0), is_resolve_spotify=True))
            url = await sync_to_async(self.bot.spotify_client.resolve_url)(url)

        if sound_cloud_regex.match(url):
            txt = ""
            cmd = f"</play:" + str(self.bot.get_global_command_named("play", cmd_type=ApplicationCommandType.chat_input).id) + ">"

            embed = Embed(title="Đã lấy được audio...", color=0x00ff00)
            txt += f"> 📹 **Spotify link**: {url}\n"
            txt += f"> <:star3:1155781751914889236> Sao chép link video sau đó dán vào lệnh {cmd} để phát bài hát này\n"
            txt += f"```{url}```"
            embed.description = txt
            embed.set_thumbnail(image_links.get("stamp0234-4598"))
            btn_mobile_view = Button(label="Copy bằng điện thoại", custom_id="ytdl-mobile-view-btn", style=ButtonStyle.primary)
            view = View(timeout=30)
            view.add_item(btn_mobile_view)
            await ctx.edit_original_response(embed=embed, view=view)
            return

        if not YOUTUBE_VIDEO_REG.match(url):
            await ctx.edit_original_response(f"❌ URL này không hợp lệ hoặc không phải là link youtube.")
            return

        await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2)))

        download_folder = await self.get_file(url, guild_id, user_id, boost_tier, ctx)

        if download_folder is None or len(os.listdir(download_folder)) == 0:
            return

        await ctx.edit_original_response(embed=self.render_embed(stat1=status.get(2),
                                                                    stat2=status.get(2),
                                                                    stat3=status.get(1)))

        await asyncio.sleep(1)

        for file in os.listdir(download_folder):
            file_path = os.path.join(download_folder, file)
            if os.path.isfile(file_path):
                file = await ctx.edit_original_response(file=File(file_path), embed=self.render_embed(stat1=status.get(2),
                                                                                                        stat2=status.get(2),
                                                                                                        stat3=status.get(2)))
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
        btn_mobile_view = Button(label="Copy bằng điện thoại", custom_id="ytdl-mobile-view-btn", style=ButtonStyle.primary)
        view = View(timeout=30)
        view.add_item(btn_mobile_view)
        await ctx.edit_original_response(embed=embed, view=view)

    @commands.Cog.listener("on_button_click")
    async def handle_button_action(self, interaction: MessageInteraction):
        if interaction.author.bot:
            return
        action_btn_custom_id = interaction.component.custom_id
        if not action_btn_custom_id.startswith("ytdl-"):
            return

        if action_btn_custom_id == "ytdl-mobile-view-btn":
            await interaction.send(self.downloaded)
        

def setup(bot: BotCore):
    bot.add_cog(YoutubeTools(bot))