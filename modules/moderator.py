import disnake
from disnake.ext import commands
import datetime
from typing import Union
from utils.others import CustomContext
from utils.client import BotCore

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
    async def ban(self, ctx: CustomContext, member: disnake.Member, *, reason: str = None):
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự cấm mình", color=disnake.Color.red()))
            return
        if member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể cấm chủ server", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể cấm người này", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể cấm người này", color=disnake.Color.red()))
            return
        if reason is None:
            reason = "Không có lý do"
        await member.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Bạn đã bị cấm khỏi server {ctx.guild.name} với lý do: {reason}", color=disnake.Color.red()))
        await member.ban(reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Đã cấm {member} khỏi server", color=disnake.Color.green()))

    @commands.command(name="unban", description="Bỏ cấm người dùng khỏi server")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def unban(self, ctx: CustomContext, member: disnake.User, *, reason: str = None):
        if reason is None:
            reason = "Không có lý do"
        await ctx.guild.unban(member, reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Đã bỏ cấm {member} khỏi server", color=disnake.Color.green()))

    @commands.command(name="kick", description="Đá người dùng khỏi server")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def kick(self, ctx: CustomContext, member: disnake.Member, *, reason: str = None):
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự hực hiện việc này lên bản thân mình", color=disnake.Color.red()))
            return
        if member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể hực hiện việc này lên chủ server", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if reason is None:
            reason = "Không có lý do"
        await member.kick(reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:LogoModSystem:1155781711024635934> Đã đá {member} khỏi server", color=disnake.Color.green()))

    @commands.command(name="mute", description="Cấm người dùng nói chuyện trong server")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def mute(self, ctx: CustomContext, member: disnake.Member, *, reason: str = None):
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự hực hiện việc này lên bản thân mình", color=disnake.Color.red()))
            return
        if member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể hực hiện việc này lên chủ server", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if reason is None:
            reason = "Không có lý do"
        await member.add_roles(ctx.guild.get_role(882298634149703454), reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:timeout:1155781760571949118> Đã cấm {member} nói chuyện trong server", color=disnake.Color.green()))

    @commands.command(name="unmute", description="Bỏ cấm người dùng nói chuyện trong server")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def unmute(self, ctx: CustomContext, member: disnake.Member, *, reason: str = None):
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự hực hiện việc này lên bản thân mình", color=disnake.Color.red()))
            return
        if member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể hực hiện việc này lên chủ server", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if reason is None:
            reason = "Không có lý do"
        await member.remove_roles(ctx.guild.get_role(882298634149703454), reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:timeout:1155781760571949118> Đã bỏ cấm {member} nói chuyện trong server", color=disnake.Color.green()))

    @commands.command(name="timeout", description="Cấm người dùng nói chuyện trong server trong một khoảng thời gian nhất định")
    @commands.has_permissions(mute_members=True)
    @commands.bot_has_permissions(mute_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def timeout(self, ctx: CustomContext, member: disnake.Member, time: int, *, reason: str = None):
        if member == ctx.author:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể tự hực hiện việc này lên bản thân mình", color=disnake.Color.red()))
            return
        if member == ctx.guild.owner:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể hực hiện việc này lên chủ server", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Bạn không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(embed=disnake.Embed(title="❌ Tôi không thể thực hiện việc này lên thành viên này", color=disnake.Color.red()))
            return
        if reason is None:
            reason = "Không có lý do"
        await member.timeout(duration=time, reason=reason)
        await ctx.send(embed=disnake.Embed(title=f"<:timeout:1155781760571949118> Đã cấm {member} nói chuyện trong server trong {time} giây", color=disnake.Color.green()))

    
    @commands.command(name="purge", description="Xóa tin nhắn trong kênh")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_legacy(self, ctx: Union[CustomContext, disnake.AppCommandInteraction], amount: int):
        await self.purge.callback(self=self, ctx=ctx, amount=amount)

    @commands.slash_command(name="purge", description=f"{desc_prefix}Xóa tin nhắn trong kênh", 
                            options=[disnake.Option(name="amount", 
                                                    description="Số lượng tin nhắn cần xóa", 
                                                    type=disnake.OptionType.integer, 
                                                    required=True
                                                    )])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: disnake.AppCommandInteraction, amount: int):
        
        await ctx.response.defer(ephemeral=True)
        if amount > 100:
            await ctx.response.send_message(embed=disnake.Embed(title="❌ Số lượng tin nhắn cần xóa không được lớn hơn 100", color=disnake.Color.red()))
            return
        deleted = await ctx.channel.purge(limit=amount)
        try:
            await ctx.edit_original_response(embed=disnake.Embed(title=f"<:trash:1155781755601682433> Đã xóa {len(deleted)} tin nhắn", color=disnake.Color.green()))
        except AttributeError:
            await ctx.send(embed=disnake.Embed(title=f"<:trash:1155781755601682433> Đã xóa {len(deleted)} tin nhắn", color=disnake.Color.green()), delete_after=5)

    @commands.command(name="nuke", description="Xóa toàn bộ tin nhắn trong kênh và tạo lại kênh")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 86400, commands.BucketType.guild)
    async def nuke(self, ctx: CustomContext):
        channel = await ctx.channel.clone()
        await ctx.channel.delete(reason="Nuke")
        await channel.send(f"<:ll:1138141608924172339> Nuked by `{ctx.author.name}`, at `{datetime.datetime.utcnow()}`")


def setup(bot):
    bot.add_cog(Moderator(bot))