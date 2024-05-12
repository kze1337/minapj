import disnake
from disnake.ext import commands
import datetime
from typing import Union
from utils.others import CustomContext
from utils.client import BotCore

def convert_tm(x: str) -> int:
    _input = x.lower().strip()
    valid = False
    _time = [0, 0, 0, 0] # [day, hours, minutes, seconds]
    buffer = ""
    for i in _input:
        if i.isnumeric():
            valid = True
            buffer += i
        elif i.isalpha():
            if not buffer.isnumeric(): continue
            if i in ["d"]: _time[0] = int(buffer)
            elif i in ["h"]:  _time[1] = int(buffer)
            elif i in ["m", "p"]: _time[2] = int(buffer)
            elif i in ["s"]: _time[3] = int(buffer)
            buffer = ""
    if buffer.isnumeric(): _time[3] = int(buffer)
    um = _time[0] * 86400 + _time[1] * 3600 + _time[2] * 60 + _time[3]
    return {
        "valid": True, 
        "tm": um
    } if valid else {
        "valid": False,
        "tm": None
    }

class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot: BotCore = bot

    emoji = "❗"
    name = "Moderator"
    desc_prefix = f"[{emoji} {name}] | "

    @commands.command(name="ban", description="Cấm người dùng khỏi server")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def ban(self, ctx: CustomContext, member: disnake.Member = None, *, reason: str = None):
        if ctx.author.bot:
            return
        
        if member is None:
            await ctx.send("Vui lòng đưa ra 1 cái tên")
        
        if member == ctx.guild.me:
            return
        
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự cấm mình", color=disnake.Color.red()))
            return
        elif ctx.author.id == ctx.guild.owner.id:
            pass
        elif member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể cấm chủ server", color=disnake.Color.red()))
            return
        elif member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể cấm người này", color=disnake.Color.red()))
            return
        elif member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể cấm người này", color=disnake.Color.red()))
            return


        if reason is None:
            reason = "Không có lý do"

        await member.ban(reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Đã cấm {member} khỏi server", color=disnake.Color.green()))

    @commands.command(name="unban", description="Bỏ cấm người dùng khỏi server")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def unban(self, ctx: CustomContext, member: disnake.User = None, *, reason: str = None):
        if ctx.author.bot:
            return
        if member is None:
            await ctx.send("Vui lòng đưa ra 1 cái tên")
        if reason is None:
            reason = "Không có lý do"
        await ctx.guild.unban(member, reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Đã bỏ cấm {member} khỏi server", color=disnake.Color.green()))

    @commands.command(name="kick", description="Đá người dùng khỏi server")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def kick(self, ctx: CustomContext, member: disnake.Member=None, *, reason: str = None):
        if ctx.author.bot:
            return
        if member is None:
            await ctx.send("Vui lòng đưa ra 1 cái tên")
        if member == ctx.guild.me:
            return
        
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự thực hiện việc này lên bản thân mình", color=disnake.Color.red()))
            return
        
        elif ctx.author.id == ctx.guild.owner_id:
            pass
        elif member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể hực hiện việc này lên chủ server", color=disnake.Color.red()))
            return
        elif member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        elif member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        
        if reason is None:
            reason = "Không có lý do"
        await member.kick(reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Đã đá {member} khỏi server", color=disnake.Color.green()))

    @commands.command(name="mute", description="Cấm người dùng nói chuyện trong server trong một khoảng thời gian nhất định")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def mute(self, ctx: CustomContext, member: disnake.Member = None, time: str = None, *, reason: str = None):
        if ctx.author.bot:
            return
        if member is None:
            await ctx.send("Vui lòng đưa ra 1 cái tên")
            
        if time is None:
            await ctx.send("Hãy đưa ra một thời lượng cụ thể để thực thi lệnh")
        if member == ctx.guild.me:
            return
        
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự thực hiện việc này lên bản thân mình", color=disnake.Color.red()))
            return
        
        elif ctx.author.id == ctx.guild.owner_id:
            pass

        elif member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể hực hiện việc này lên chủ server", color=disnake.Color.red()))
            return
        elif member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        elif member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        
        if reason is None:
            reason = "Không có lý do"
        
        tm = convert_tm(time)
        if tm["valid"] == False:
            return
        try:
            await member.timeout(duration=tm["tm"], reason=reason)
            await ctx.send(embed=disnake.Embed(title=f"<:timeout:1155781760571949118> Đã cấm {member} nói chuyện trong server trong {time}", color=disnake.Color.green()))
        except Exception as e:
            if "Missing Permissions" in str(e):
                await ctx.send("Tui chưa có quyền để thực hiện lệnh này, hãy đảm bảo đã thêm đủ quyền \n https://i.ibb.co/bsqLmRR/image.png")
                print(repr(e))
                return
            return
    
    @commands.command(name="unmute", description="Bỏ cấm chat cho người dùng")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: CustomContext, member: disnake.Member = None):
        if member is None: return
        if member.current_timeout is None:
            await ctx.send(f"Người dùng {member.mention} không bị hạn chế")
            return
        try: 
            await member.timeout(duration=0, reason=f"Unmute by {ctx.author.name}")
            await ctx.send(f"Đã unmute cho người dùng {member.name}")
        except Exception as e:
            if "Missing Permissions" in str(e):
                await ctx.send("Tui chưa có quyền để thực hiện lệnh này, hãy đảm bảo đã thêm đủ quyền \n https://i.ibb.co/bsqLmRR/image.png")
                return
            return            

    @commands.command(name="purge", description="Xóa tin nhắn trong kênh")
    @commands.has_permissions(manage_messages=True, read_message_history=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge_legacy(self, ctx: Union[CustomContext, disnake.AppCommandInteraction], amount: int = None):
        await ctx.message.delete()
        await self.purge.callback(self=self, ctx=ctx, amount=amount)

    @commands.slash_command(name="purge", description=f"{desc_prefix}Xóa tin nhắn trong kênh", 
                            options=[disnake.Option(name="amount", 
                                                    description="Số lượng tin nhắn cần xóa", 
                                                    type=disnake.OptionType.integer, 
                                                    required=True
                                                    )])
    @commands.has_permissions(manage_messages=True, read_message_history=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def purge(self, ctx: disnake.AppCommandInteraction, amount: int = None):
        if ctx.author.bot:
            return
        
        
        await ctx.response.defer(ephemeral=True)

        if amount is None:
            await ctx.edit_original_response("Thêm số lượng tin nhắn cần xóa !")
            return
        if amount > 100:
            await ctx.response.send_message(embed=disnake.Embed(title="❌ Số lượng tin nhắn cần xóa không được lớn hơn 100", color=disnake.Color.red()))
            return
        deleted = await ctx.channel.purge(limit=amount)
        try:
            await ctx.edit_original_response(embed=disnake.Embed(title=f"<:trash:1155781755601682433> Đã xóa {len(deleted)} tin nhắn", color=disnake.Color.green()))
        except AttributeError:
            await ctx.send(embed=disnake.Embed(title=f"<:trash:1155781755601682433> Đã xóa {len(deleted)} tin nhắn", color=disnake.Color.green()), delete_after=5)

    @commands.command(name="nuke", description="Xóa toàn bộ tin nhắn trong kênh và tạo lại kênh")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 86400, commands.BucketType.guild)
    async def nuke(self, ctx: CustomContext):
        if ctx.author.bot:
            return
        channel = await ctx.channel.clone()
        await ctx.channel.delete(reason="Nuke")
        await channel.send(f"<:ll:1138141608924172339> Nuked by `{ctx.author.name}`")


def setup(bot):
    bot.add_cog(Moderator(bot))