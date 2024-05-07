
import time

import traceback

import disnake
from disnake.ext import commands
from disnake import OptionType, OptionChoice

from utils.client import BotCore
from utils.GenEMBED import Embed
from utils.music.checks import can_send_message_check, can_send_message
from utils.ai.chatgpt import chatgpt, create_thread
from utils.ai.rsnApi import gemini
import datetime

import os
import dotenv

from asgiref.sync import sync_to_async

dotenv.load_dotenv()

desc_prefix = "⚡[AI]⚡"

model_info = {
    "gpt-3.5-turbo": {"name": "OpenAI GPT-3.5", "icon": "https://cdn.discordapp.com/attachments/1117362735911538768/1131924844603265054/img-1190-removebg-preview.png"},
    "gemini": {"name": "Gemini Ai", "icon": "https://www.gstatic.com/lamda/images/sparkle_resting_v2_darkmode_2bdb7df2724e450073ede.gif"},
}

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
            await ctx.send(embed=Embed.gen_error_embed("Tính năng này chỉ dành cho người dùng Premium"))
            return False
        return {"status": "success", "premium": premium}


class ChatGPT(commands.Cog):
    def __init__(self, bot: BotCore) -> None:
        self.bot: commands.Bot = bot
        self.debugging = True
    
    @can_send_message_check()
    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.slash_command(
        name="ai",
        description=f"{desc_prefix} Tính năng AI của bot"
    )
    async def ai(self, ctx: disnake.ApplicationCommandInteraction):
        return
    @ai.sub_command(
        name="chat",
        description=f"{desc_prefix} Chat với một trong các model chatbot AI",
        options = [
            disnake.Option(name="content", description="Nội dung chat", type=OptionType.string, required=True),
            disnake.Option(name="model", description="Model chatbot", type=OptionType.string, required=True, choices=[
                OptionChoice(name="GPT-3.5", value="gpt-3.5-turbo"),
                OptionChoice(name="Gemini", value="gemini")
            ]),
            disnake.Option(name="private", description="Chế độ riêng tư (Yêu cầu bạn phải bật nếu bạn ở trên kênh chat chính)", type=OptionType.boolean, required=False, choices=[
                OptionChoice(name="Bật", value=True),
                
            ])
        ])
    async def chat(self, ctx: disnake.ApplicationCommandInteraction, content: str, model: str, private: bool = False):
            can_send_message(ctx.channel, ctx.bot.user)
            await ctx.response.defer(ephemeral=private)
            if len(content) > 2000:
                await ctx.edit_original_response(embed=Embed.gen_error_embed(message="Câu hỏi dài quá, hãy thử chia nó ra nhé"))
                return
            else:
                pass
            userinfo = await check_user(self.bot, ctx, ctx.author.id)
            if not userinfo: return
            else:
                try: 
                    premium = userinfo["premium"]
                    embed = disnake.Embed(
                        title="<a:aloading:1229108110577107077> Vui lòng chờ.\n Tùy vào nội dung, quá trình xử lý có thể kéo dài đến 1-2 phút...",
                        color=disnake.Color.yellow()
                    )
                    await ctx.edit_original_response(embed=embed)
                    if model == "gpt-3.5-turbo": # GPT 3.5 (FREE)
                        # response = await sync_to_async(chatgpt)(content, ctx.author.id if premium else None)
                        await ctx.send("Hiện tại thằng Aris đang lười mua thêm chatGPT 3.5, nên model này không hoạt động <:Nerdpixel:1230475354003476531>", delete_after=(10 if not private else None), components=None)
                        return
                    if model == "gemini": # GEMINI AI (NEW)
                        response = await gemini(content)
                    if response["status"] == "error":
                        await ctx.edit_original_response(embed=Embed.gen_error_embed(response["message"]))
                        return
                    else:
                        use = await self.bot.db_handler.use(ctx.author.id, model, premium)
                        if use["status"] == "failed":
                            await ctx.edit_original_response(embed=Embed.gen_error_embed(use["reason"]))
                            return
                        used, left = use["used"], use["left"]

                except Exception:
                    await ctx.edit_original_response("Đã xảy ra lỗi :<", embed=None, delete_after=5)
                    traceback.print_exc()
                    return
                    
                if len(response["message"]) <= 1850:
                    message = f"> ### Trả lời cho {ctx.author.mention} câu hỏi {content}:\n\n" + response["message"]
                    try:
                        embed = disnake.Embed(
                        title=f"Được cung cấp bởi {model_info[model]['name']}",
                        description=f"⚡ Thời gian phản hồi: {datetime.timedelta(milliseconds=response['response_time']).seconds} giây\n"
                        f"```Các thông tin được đưa ra có thể không chính xác và cần được xác nhận``` \n"
                                    f"{'👑' if premium else '<:verify:1134033164151566460>'} Bạn đã sử dụng {used} lần, còn lại {left} lần",
                        color=disnake.Color.green()
                    )
                    except KeyError:
                        embed = disnake.Embed(
                        title=f"Được cung cấp bởi {model_info[model]['name']}",
                        description=
                        f"```Các thông tin được đưa ra có thể không chính xác và cần được xác nhận``` \n"
                                    f"{'👑' if premium else '<:verify:1134033164151566460>'} Bạn đã sử dụng {used} lần, còn lại {left} lần",
                        color=disnake.Color.green()
                    )
                    embed.set_footer(icon_url=ctx.author.avatar.url,text="Tính năng thử nghiệm")
                    embed.set_thumbnail(url=model_info[model]["icon"])
                    if self.debugging:
                        await ctx.edit_original_response(content=message,embed=embed)
                    else:
                        await ctx.edit_original_response(content=message)
                else:
                    try:
                        embed = disnake.Embed(
                        title=f"Được cung cấp bởi {model_info[model]['name']}",
                        description=f"⚡ Thời gian phản hồi: {datetime.timedelta(milliseconds=response['response_time']).seconds} giây\n"
                                    f"```Các thông tin được đưa ra có thể không chính xác và cần được xác nhận``` \n"
                                    f"{'👑' if premium else '<:verify:1134033164151566460>'} Bạn đã sử dụng {used} lần, còn lại {left} lần",
                        color=disnake.Color.green()
                    )   
                    except KeyError:
                        embed = disnake.Embed(
                        title=f"Được cung cấp bởi {model_info[model]['name']}",
                        description=
                        f"```Các thông tin được đưa ra có thể không chính xác và cần được xác nhận``` \n"
                                    f"{'👑' if premium else '<:verify:1134033164151566460>'} Bạn đã sử dụng {used} lần, còn lại {left} lần",
                        color=disnake.Color.green()
                    )
                    with open("response.txt", "w", encoding="utf-8") as f:
                        f.write(response["message"])
                    if self.debugging:
                        await ctx.edit_original_response(content=f"> ### Trả lời cho {ctx.author.mention} câu hỏi {content}:\n\n"
                                                        f"Câu trả lời hơi dài, tớ cho vào file giúp cậu nhé", file=disnake.File("response.txt"), embed=embed)  
                    else:
                        await ctx.edit_original_response(content=f"> ### Trả lời cho {ctx.author.mention} câu hỏi {content}: \n\n"
                                                        f"Câu trả lời hơi dài, tớ cho vào file giúp cậu nhé", file=disnake.File("response.txt"))
                        
                    time.sleep(5)
                    os.remove("response.txt")              

    @ai.sub_command(
        name="newchat",
        description=f"{desc_prefix} Tạo đoạn chat mới. Hê thống sẽ liên kết nội dung các câu hỏi trước cho bạn (👑Premium)",
        options = [
            disnake.Option(name="prompt", description="Điều bạn muốn chatbot đóng vai.", type=OptionType.string, required=False)
        ])
    async def newchat(self, ctx: disnake.ApplicationCommandInteraction, prompt: str = None):
            await ctx.response.defer(ephemeral=True)
            userinfo = await check_user(self.bot, ctx, ctx.author.id, premium_check=True)
            if not userinfo: return
            else:
                create_thread(ctx.author.id, sys_message=prompt)
                embed = disnake.Embed(
                    title="Đã tạo đoạn chat mới",
                    description="Hãy sử dụng lệnh `/ai chat` để bắt đầu chat với chatbot",
                    color=disnake.Color.green()
                )
                await ctx.edit_original_response(embed=embed)

def setup(bot: BotCore):
    bot.add_cog(ChatGPT(bot))
