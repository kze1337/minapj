import disnake
from gtts import gTTS
from disnake.ext import commands
from disnake import FFmpegPCMAudio
import asyncio
import re

import traceback

import os
from utils.client import BotCore as Client
from utils.others import CommandArgparse, pool_command, CustomContext
from utils.music.checks import check_voice



async def check_lang(lang):
    pattern = r"^[a-z]{2}$"
    return bool(re.match(pattern, lang))

async def process_tts(text, guild_id, channel_id, lang):
    tts = gTTS(text, lang=lang)
    if not os.path.exists(f'./data_tts/{guild_id}'):
        os.makedirs(f'./data_tts/{guild_id}')
    tts.save(f'./data_tts/{guild_id}/{channel_id}_tts.mp3')

class TTS(commands.Cog):
    emoji = "🔊"
    name = "TTS"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: Client):
        self.bot = bot

    say_flags = CommandArgparse()
    say_flags.add_argument("text", nargs="*", help="Văn bản cần chuyển thành âm thanh")
    say_flags.add_argument("-lang", '-lg', type=str, default="vi", help="Ngôn ngữ cần chuyển, mặc định là tiếng việt")

    @check_voice()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.member, wait=False)
    @pool_command(description=f"{desc_prefix}Tạo âm thanh từ văn bản", extras={"flags": say_flags})
    async def say(self, ctx: CustomContext, *, flags: str = ""):

        FFMPEG_OPTIONS = {
        'before_options': '', 'options': '-vn'}

        args, unknown = ctx.command.extras['flags'].parse_known_args(flags.split())
        text = " ".join(args.text + unknown)
        
        if text.lower() == "gay":
            _gayvc = ctx.author.voice.channel
            try:
                vc = await _gayvc.connect()
            except Exception as e:
                if "Already connected to a voice channel" in str(e):
                    vc = ctx.author.guild.voice_client
                else:
                    vc = ctx.author.guild.voice_client
            try:
                vc.play(FFmpegPCMAudio(source="./Funny_sound/gay.mp3", **FFMPEG_OPTIONS))
                while vc.is_playing():
                    await asyncio.sleep(2)
            except Exception:
                traceback.print_exc()
                await ctx.channel.send(f"Có thể bot đang phát nhạc, vui lòng tắt nhạc và thử lại :>")
                return
        else:
        
            # Save TTS file
            try:
                check = await check_lang(args.lang)
                if check == False:
                    await ctx.channel.send("Ngôn ngữ không được hỗ trợ, nếu bạn muốn xài ngôn ngữ khác hãy chắc chắn là nó là 2 kí tự đầu của ngôn ngữ đó, tham khảo trang web sau: [WEB](https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages)")
                    return
                
                await process_tts(text, ctx.guild.id, ctx.channel.id, args.lang)
            except Exception as e:
                if "Language not supported" in str(e):
                    await ctx.channel.send("Ngôn ngữ không được hỗ trợ, nếu bạn muốn xài ngôn ngữ khác hãy chắc chắn là nó là 2 kí tự đầu của ngôn ngữ đó, ví dụ: \njapan: ja.")
                    return
            
            
            channel = ctx.author.voice.channel
            
            try:
                vc = await channel.connect()
            except Exception as e:
                if "Already connected to a voice channel" in str(e):
                    vc = ctx.author.guild.voice_client
                else:
                    vc = ctx.author.guild.voice_client

            try:
                vc.play(FFmpegPCMAudio(f"./data_tts/{ctx.guild.id}/{ctx.channel.id}_tts.mp3", **FFMPEG_OPTIONS))
                
                while vc.is_playing():
                    await asyncio.sleep(3)
            except Exception:
                traceback.print_exc()
                await ctx.channel.send(f"Có thể bot đang phát nhạc, vui lòng tắt nhạc và thử lại :>")
                return
            

    @check_voice()
    @commands.command(description=f"{desc_prefix}Ngắt kết nối với kênh thoại")
    async def tts_stop(self, ctx: disnake.ApplicationCommandInteraction):
        vc = ctx.author.guild.voice_client
        if vc:
            await vc.disconnect()
            await ctx.channel.send("Đã ngắt kết nối với kênh thoại.")
            os.remove(f"./data_tts/{ctx.guild.id}/{ctx.channel.id}_tts.mp3")
        else:
            await ctx.channel.send("Tôi đang không kết nối với kênh thoại nào.")

def setup(bot: Client):
    bot.add_cog(TTS(bot))
