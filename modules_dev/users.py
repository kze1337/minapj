from __future__ import annotations

import disnake


from disnake.ext import commands
from disnake import OptionType, OptionChoice
from utils.client import BotCore
import json
import os
from utils.user.Key.Keyutils import KeyUtils

#################################################################

desc_prefix = "👤[Thành viên]👤"
success_icon = "https://cdn.discordapp.com/attachments/1117362735911538768/1131107858285600868/success.png"
fail_icon = "https://media.discordapp.net/attachments/1158024306006171722/1172548248712519690/New_Project_12_1F9D8FE.gif?ex=6560b7a7&is=654e42a7&hm=3e1ad259424752013faa667b7fd45f93dece5975d3eccdf4ba773f498fc02963&"

platform_icon = {
    "facebook": "<:facebook:1230516619248275526>",
    "tiktok": "<:Tiktok:1139078822453596170>",
    "github": "<:github_team:1103351450299543584>",
    "discord": "<:Discord:1155781686349545489>",
    "telegram": "☎️",
    "website": "<:chromium:1185186730781982772>",
    "youtube": "<:YouTube:1230516665599660164>",
}

def gen_banned_embed(time, reason):
    embed = disnake.Embed(
        title="Tài khoản bị cấm!",
        description=f"Tài khoản này đã bị cấm sử dụng các tính năng dành cho thành viên bot từ <t:{time}:R> với lý do: {reason}",
        color=disnake.Color.red()
    )
    embed.set_thumbnail(url=fail_icon)
    return embed

notfound_embed = disnake.Embed(
    title="Lỗi",
    description="Không tìm thấy tài khoản của bạn trên hệ thống.\nHãy sử dụng lệnh `/register` để đăng ký tài khoản.",
    color=disnake.Color.red()
).set_image(url=fail_icon)
notfound_embed.set_thumbnail(url=fail_icon)

#################################################################

class Users(commands.Cog):
    def __init__(self, bot):
        self.bot: BotCore = bot

    @commands.slash_command(name="delete_your_data", description=f"{desc_prefix} Xóa toàn bộ thông tin của bạn của bot này")
    async def del_data(self, ctx: disnake.ApplicationCommandInteraction):
        await ctx.response.defer(ephemeral=True)
        userinfo =  await self.bot.db_handler.get_userinfo(ctx.author.id)
        if userinfo["status"] == "notfound":
            await ctx.edit_original_response("Bạn không có dữ liệu người dùng nào được lưu trữ trong dịch vụ này!!")
        else:
            embed = disnake.Embed(title="Xóa dữ liệu", description="Bạn có chắc chắn là sẽ xóa dữ liệu không?\n Hành động này sẽ không thể hoàn tác!")
            view = disnake.ui.View()
            view.add_item(disnake.ui.Button(label="Xóa", custom_id="user_delete_confirm_btn")) 
            view.add_item(disnake.ui.Button(label="Khong", custom_id="user_delete_no_btn"))
            await ctx.edit_original_response(embed=embed, view=view)
        
    
    @commands.slash_command(name="profile",
                            description=f"{desc_prefix} Xem thông tin người dùng",
                            options=[
                                disnake.Option(name="user", description="Người dùng", type=OptionType.user, required=False),
                                disnake.Option(name="private", description="Chế độ riêng tư", type=OptionType.boolean, required=False, choices=[
                                    OptionChoice(name="Bật", value="True"),
                                    OptionChoice(name="Tắt", value="False")
                                ])
                            ])
    async def profile(self, ctx: disnake.ApplicationCommandInteraction, user: disnake.User = None, private: bool = False):
        await ctx.response.defer(ephemeral=private)
        user = user or ctx.author
        userinfo = await self.bot.db_handler.get_userinfo(user.id)
        if userinfo["status"] == "banned":
            await ctx.edit_original_response(embed=gen_banned_embed(userinfo["time"], userinfo["ban_reason"]))
            return
        if userinfo["status"] == "notfound":
            await ctx.edit_original_response(embed=notfound_embed)

        else:
            premium_mark = '『 <:diamond_1removebgpreview:1169250424499490866> PREMIUM 』\n'
            owner_mark = '『 <:A_IconOwner:1169250420368101396> OWNER 』\n'            
            embed = disnake.Embed(
                title=f"Thông tin của {user.display_name}",
                description=f"{owner_mark if user.id == self.bot.owner_id else premium_mark if userinfo['premium'] > int(disnake.utils.utcnow().timestamp()) else ''}*{userinfo['signature'] if userinfo['signature'] else 'Chưa thiết lập chữ kí'}*",
                color=ctx.author.roles[-1].color
            )
            embed.set_thumbnail(url=user.avatar.url)
            embed.add_field(
                name="💰 Số dư:",
                value=f"> <:m1_mora:1169483093233631304> `{userinfo['coin']}`\n"
                      f"> <:4611genesiscrystal:1169483098866602085> `{userinfo['money']}`",
                inline=True
            )
            embed.add_field(
                name="👑 Uy tín:",
                value=f"> 👑 `{userinfo['uytin']}`",
                inline=True
            )
            if userinfo["premium"] > int(disnake.utils.utcnow().timestamp()):
                embed.add_field(
                    name="<:diamond_1removebgpreview:1169250424499490866> Hạn dùng Premium:",
                    value=f"┕ <t:{userinfo['premium']}:R>",
                    inline=True
                )
            embed.add_field(
                name="📅 Tham gia:",
                value=f"┕ <t:{userinfo['creation_time']}:R>",
                inline=True
            )
            if user.id == ctx.author.id:
                embed.add_field(
                    name="🕓 Hoạt động gần đây:",
                    value="\n".join([f"> <t:{i['timestamp']}:R> {i['activity']}" for i in userinfo["activities"]]),
                    inline=False
                )
            embed.set_footer(
                text=ctx.author.display_name,
                icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless"
            )
            try:
                view = disnake.ui.View()
                if userinfo["premium"] > int(disnake.utils.utcnow().timestamp()):
                    for key in userinfo["link"]:
                        item = userinfo["link"][key]
                        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.link,
                                                        label=item["display_name"],
                                                        emoji=platform_icon[item["platform"]],
                                                        url=item["url"]))
                await ctx.edit_original_response(embed=embed, view=view)
            except TypeError:
                await ctx.edit_original_response(embed=embed)

    @commands.command(name="register", description=f"{desc_prefix}Đăng ký tài khoản")
    async def register_legacy(self, ctx: disnake.ApplicationCommandInteraction):
        pritave = False
        await self.register.callback(self, ctx, pritave)

    @commands.slash_command(name="register",
                            description=f"{desc_prefix} Đăng ký tài khoản",
                            options=[
                                disnake.Option(name="private", description="Chế độ riêng tư", type=OptionType.boolean, required=False, choices=[
                                    OptionChoice(name="Bật", value="True"),
                                    OptionChoice(name="Tắt", value="False")
                                ])
                            ])
    async def register(self, ctx: disnake.ApplicationCommandInteraction, private: bool = False):
        await ctx.response.defer(ephemeral=private)
        uid = ctx.author.id
        banned = await self.bot.db_handler.is_banned(uid)
        if banned["status"] == "banned":
            await ctx.edit_original_response(embed=gen_banned_embed(banned["time"], banned["ban_reason"]))
            return
        register_status = await self.bot.db_handler.register(uid)
        if register_status["status"] == "exist":
            embed = disnake.Embed(
                title="Lỗi",
                description="Bạn đã đăng ký tài khoản rồi!",
                color=disnake.Color.red()
            )
            embed.set_thumbnail(url=fail_icon)
            await ctx.edit_original_response(embed=embed)
        elif register_status["status"] == "success":
            embed = disnake.Embed(
                title="Xin chúc mừng!",
                description="Bạn đã đăng ký tài khoản thành công!\nHãy sử dụng lệnh `/profile` để xem thông tin tài khoản của bạn.",
                color=disnake.Color.green()
            )
            embed.set_thumbnail(url=success_icon)
            embed.set_footer(
                    text=ctx.author.display_name,
                    icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless"
                )
            await ctx.edit_original_response(embed=embed)


    @commands.slash_command(name="premium",
                            description=f"{desc_prefix} Xem các đặc quyền hoặc mua gói Premium")
    async def premium(self, ctx: disnake.ApplicationCommandInteraction):
        await ctx.response.defer()
        uid = ctx.author.id
        userinfo = await self.bot.db_handler.get_userinfo(uid)

        if userinfo["status"] == "banned":
            await ctx.edit_original_response(embed=gen_banned_embed(userinfo["time"], userinfo["ban_reason"]))
            return

        if userinfo["status"] == "notfound":
            userinfo = {"premium": 0}

        if userinfo["premium"] > int(disnake.utils.utcnow().timestamp()):
            embed = disnake.Embed(
                title=f"Xin chào {ctx.author.display_name} ❤️",
                description=f"Gói đăng kí Premium của bạn còn hiệu lực đến <t:{userinfo['premium']}:R>",
                color=disnake.Color.random()
            )
        else:
            embed = disnake.Embed(
                title=f"Xin chào {ctx.author.display_name} ❤️",
                description="Bạn hiện không phải là người dùng Premium.",
                color=disnake.Color.random()
            )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.add_field(
            name="<:diamond_1removebgpreview:1169250424499490866> Các đặc quyền dành cho người đăng kí Premium:",
            value=f"> Truy cập vào các tính năng giới hạn.\n"\
                    f"> [Music] Lưu & truy cập nhanh các danh sách phát yêu thích.\n"\
                    f"> [OpenAI] Sử dụng GPT-4, Bing chat, Bard ai.\n"\
                    f"> [PREMIUM] Tăng giới hạn sử dụng các dịch vụ\n"\
                    f"> ... và còn rất nhiều tính năng khác.\n",
            inline=False
        )
        embed.add_field(
            name="💰 Bảng giá Premium:",
            value=f"> `1 ngày` - `1000`🪙\n"\
                  f"> `30 ngày` - `30000`🪙\n"\
                  f"> `6 tháng` - `180000`🪙\n"\
                  f"> `1 năm` - ~~`360000`~~🪙 `350000`🪙\n",
            inline=False
        )

        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.secondary,
                                        label="Mua Premium [1 ngày]",
                                        custom_id="buy_premium_1", emoji="🪙", row=0))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.secondary,
                                        label="Mua Premium [30 ngày]",
                                        custom_id="buy_premium_30", emoji="🪙", row=0))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.secondary,
                                        label="Mua Premium [6 tháng]",
                                        custom_id="buy_premium_180", emoji="🪙", row=1))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.secondary,
                                        label="Mua Premium [1 năm]",
                                        custom_id="buy_premium_360", emoji="🪙", row=1))
        await ctx.edit_original_response(embed=embed, view=view)

    @commands.slash_command(name="claim_code",
                            description=f"{desc_prefix} Nhận mã code",
                            options=[
                                disnake.Option(name="code", description="Mã code, Theo dạng XXXX-XXXX-XXXX-XXXX", type=OptionType.string, required=True)
                            ])
    async def claim_code(self, ctx: disnake.ApplicationCommandInteraction, code: str):
        await ctx.response.defer(ephemeral=True)
        uid = ctx.author.id
        userinfo = await self.bot.db_handler.get_userinfo(uid)

        if userinfo["status"] == "banned":
            await ctx.edit_original_response(embed=gen_banned_embed(userinfo["time"], userinfo["ban_reason"]))
            return

        if userinfo["status"] == "notfound":
            userinfo = {"premium": 0}


        if userinfo["premium"] > int(disnake.utils.utcnow().timestamp()):
            action = await self.bot.db_handler.claim_code(uid, code)
            if action["status"] == "success":
                embed = disnake.Embed(
                    title="Thành công!",
                    description=f"Nhận mã code thành công!\nHạn dùng gói Premium của bạn bây giờ là <t:{action['valid_time']}:R>",
                    color=disnake.Color.green()
                )
                embed.set_thumbnail(url=success_icon)
                embed.set_footer(
                    icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless",
                    text=ctx.author.display_name
                )
                await ctx.edit_original_response(embed=embed)
            else:
                embed = disnake.Embed(
                    title="Lỗi",
                    description=action["reason"],
                    color=disnake.Color.red()
                )
                embed.set_thumbnail(url=fail_icon)
                await ctx.edit_original_response(embed=embed)
        else:   
            action = await self.bot.db_handler.claim_code(uid, code)
            if action["status"] == "success":
                embed = disnake.Embed(
                    title="Thành công!",
                    description=f"Nhận mã code và kích hoạt premium thành công!\nHạn dùng gói Premium của bạn bây giờ là <t:{action['valid_time']}:R>",
                    color=disnake.Color.green()
                )
                embed.set_thumbnail(url=success_icon)
                embed.set_footer(
                    icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless",
                    text=ctx.author.display_name
                )
                await ctx.edit_original_response(embed=embed)
            else:
                embed = disnake.Embed(
                    title="Lỗi",
                    description=action["reason"],
                    color=disnake.Color.red()
                )
                embed.set_thumbnail(url=fail_icon)
                await ctx.edit_original_response(embed=embed)
                return
    

    @commands.slash_command(name="signature",
                            description=f"{desc_prefix} Thiết lập chữ kí của bạn",
                            options=[
                                disnake.Option(name="signature", description="Chữ kí của bạn", type=OptionType.string, required=True)
                            ])
    async def signature(self, ctx: disnake.ApplicationCommandInteraction, signature: str):
        await ctx.response.defer()
        uid = ctx.author.id
        userinfo = await self.bot.db_handler.get_userinfo(uid)
        if userinfo["status"] == "banned":
            await ctx.edit_original_response(embed=gen_banned_embed(userinfo["time"], userinfo["ban_reason"]))
            return
        if userinfo["status"] == "notfound":
            await ctx.edit_original_response(embed=notfound_embed)
            return
        await self.bot.db_handler.signature(uid, signature)
        embed = disnake.Embed(
            title="Thành công!",
            description="Thiết lập chữ kí thành công!",
            color=disnake.Color.green()
        )
        embed.set_thumbnail(url=success_icon)
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless"
        )
        await ctx.edit_original_response(embed=embed)

    
    @commands.slash_command(name="edit_link",
                            description=f"{desc_prefix} Chỉnh sửa liên kết mạng xã hội của bạn ( 👑 Premium)",
                            options=[
                                disnake.Option(name="platform", description="Nền tảng", type=OptionType.string, required=True, choices=[
                                    OptionChoice(name="Facebook", value="facebook"),
                                    OptionChoice(name="TikTok", value="tiktok"),
                                    OptionChoice(name="GitHub", value="github"),
                                    OptionChoice(name="Discord", value="discord"),
                                    OptionChoice(name="Telegram", value="telegram"),
                                    OptionChoice(name="Website", value="website"),
                                    OptionChoice(name="YouTube", value="youtube"),
                                ]),
                                disnake.Option(name="url", description="URL", type=OptionType.string, required=True),
                                disnake.Option(name="display_name", description="Tên hiển thị", type=OptionType.string, required=False)
                            ])
    async def edit_link(self, ctx: disnake.ApplicationCommandInteraction, platform: str, url: str, display_name: str = None):
        await ctx.response.defer(ephemeral=True)
        uid = ctx.author.id
        userinfo = await self.bot.db_handler.get_userinfo(uid)
        if userinfo["status"] == "banned":
            await ctx.edit_original_response(embed=gen_banned_embed(userinfo["time"], userinfo["ban_reason"]))
            return
        if userinfo["status"] == "notfound":
            await ctx.edit_original_response(embed=notfound_embed)
            return
        if userinfo["premium"] < int(disnake.utils.utcnow().timestamp()):
            embed = disnake.Embed(
                title="Lỗi",
                description="Bạn không phải là người dùng Premium!",
                color=disnake.Color.red()
            )
            embed.set_thumbnail(url=fail_icon)
            await ctx.edit_original_response(embed=embed)
            return
        response = await self.bot.db_handler.edit_link(uid, platform, url, display_name)
        if response["status"] == "failed":
            embed = disnake.Embed(
                title="Lỗi",
                description=response["reason"],
                color=disnake.Color.red()
            )
            embed.set_thumbnail(url=fail_icon)
            await ctx.edit_original_response(embed=embed)
            return
        embed = disnake.Embed(
            title="Thành công!",
            description="Chỉnh sửa liên kết mạng xã hội thành công!",
            color=disnake.Color.green()
        )
        embed.set_thumbnail(url=success_icon)
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless"
        )
        await ctx.edit_original_response(embed=embed)



#################################################################

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.author.bot:
            pass
        await inter.response.defer(ephemeral=True)

        uid = inter.author.id
        userinfo = await self.bot.db_handler.get_userinfo(uid)
        button_id = inter.component.custom_id
        if button_id.startswith("buy_premium_"):

            if userinfo["status"] == "banned":
                await inter.send(embed=gen_banned_embed(userinfo["time"], userinfo["ban_reason"]), ephemeral=True)
                return
            if userinfo["status"] == "notfound":
                try:
                    await inter.send(embed=notfound_embed, ephemeral=True)
                    print(inter.author.name)
                    print(inter.guild.name)
                    return
                except disnake.HTTPException:                
                    return
        
            if button_id == "buy_premium_1": value = {"coin": -1000, "days": 1}
            elif button_id == "buy_premium_30": value = {"coin": -30000, "days": 30}
            elif button_id == "buy_premium_180": value = {"coin": -180000, "days": 180}
            elif button_id == "buy_premium_360": value = {"coin": -350000, "days": 360}
            else:
                embed = disnake.Embed(
                    title="Lỗi",
                    description="Thao tác không hợp lệ.",
                    color=disnake.Color.red()
                )
                embed.set_thumbnail(url=fail_icon)
                await inter.response.send_message(embed=embed, ephemeral=True)
                return
        
            transaction = await self.bot.db_handler.transaction(uid, value["coin"], 0, f"Mua gói Premium {value['days']} ngày")
            if transaction["status"] == "success":
                action = await self.bot.db_handler.extend_premium(uid, value["days"])
                if action["status"] == "success":
                    embed = disnake.Embed(
                        title="Giao dịch thành công!",
                        description=f"Mua gói Premium {value['days']} ngày thành công!\nHạn dùng gói Premium của bạn là <t:{action['valid_time']}:R>",
                        color=disnake.Color.green()
                    )
                    embed.set_thumbnail(url=success_icon)
                    embed.set_footer(
                        text="Active Premium",
                        icon_url="https://cdn.discordapp.com/emojis/1119850673094283334.gif?size=96&quality=lossless"
                    )
                    await inter.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed(
                        title="Đã xảy ra lỗi",
                        description=f"Vui lòng liên hệ chủ sở hữu bot để được hỗ trợ.",
                        color=disnake.Color.red()
                    )
                    embed.set_thumbnail(url=fail_icon)
                    await inter.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Đã xảy ra lỗi",
                    description=f'Mua gói Premium {value["days"]} ngày thất bại.\n{transaction["reason"]}',
                    color=disnake.Color.red()
                )
                embed.set_thumbnail(url=fail_icon)
                await inter.response.send_message(embed=embed, ephemeral=True)

        elif button_id.startswith("user_delete"):
            if button_id == "user_delete_confirm_btn":
                    stat =  await self.bot.db_handler.delete_all_user_data(inter.author.id)
                    if stat["status"] == "error":
                        await inter.edit_original_response(f"Đã xảy ra lỗi {stat['msg']}", view=None, embed=None)
                    else:
                        await inter.edit_original_response("Tất cả dữ liệu đã được xóa, cảm ơn vì đã dùng dịch vụ của chúng tớ!", view=None, embed=None)
            else: 
                await inter.edit_original_response("Đã hủy tương tác", view=None, embed=None)

#################################################################
################ Owner stuffs ###################################
#################################################################


class OwnerUser(commands.Cog):
    def __init__(self, bot: BotCore):
        self.bot = bot

    @commands.is_owner()
    @commands.slash_command(name="ban", description="Ban người dùng khỏi hệ thống", options=[
        disnake.Option(name="uid", description="ID người dùng", type=OptionType.integer, required=True),
        disnake.Option(name="reason", description="Lý do", type=OptionType.string, required=False)])
    async def ban(self, ctx: disnake.ApplicationCommandInteraction, uid: int = None, reason: str = None):
        await ctx.response.defer()
        if reason is None:
            reason = "Không có lý do"

        if uid is None:
            await ctx.edit_original_response(content="Bạn chưa nhập ID người dùng!")
            return
        elif uid == ctx.author.bot:
            await ctx.edit_original_response(content="Bạn không thể ban bot!")
            return
        elif uid == ctx.author.id:
            await ctx.edit_original_response(content="Bạn không thể ban chính mình!")
            return
        else:
            await self.bot.db_handler.ban(uid, reason=reason)
            await ctx.response.send_message(f"Đã ban người dùng {uid} khỏi hệ thống!")

    @commands.is_owner()
    @commands.slash_command(name="setcoin", description="Đặt số dư của người dùng", options=[
        disnake.Option(name="uid", description="ID người dùng", type=OptionType.string, required=False),
        disnake.Option(name="coin", description="Số dư", type=OptionType.integer, required=False),
        disnake.Option(name="money", description="Tiền", type=OptionType.integer, required=False)])
    async def setcoin(self, ctx: disnake.ApplicationCommandInteraction, uid: int = None, coin: int = None, money: int = None):
        await ctx.response.defer()
        if not uid:
            uid = ctx.author.id
        if not coin:
            coin = 0
        if not money:
            money = 0
        set = await self.bot.db_handler.transaction(uid=uid, coin=coin, money=money, reason="Set coin")
        if set["status"] == "success":
            await ctx.edit_original_response(f"Đã set số dư của người dùng {uid} thành công!")
        else:
            await ctx.edit_original_response(content=f"Đã xảy ra lỗi: {set['reason']}")
        
    @commands.is_owner()
    @commands.command()
    async def genkey(self, ctx: disnake.AppCommandInteraction):    
        file = "utils/user/Key/Premium_keys.json"    
        random_strings = {KeyUtils.generate_random_string(): 30 for _ in range(30)}
        with open(file, 'w') as file:
            json.dump(random_strings, file, indent=4)

        await ctx.author.send("Premium Keys Generated Successfully", file=disnake.File("Premium_keys.json"))

class UytinSystem(commands.Cog):
    def __init__(self, bot: BotCore):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="addut", description="Set uy tín cho người dùng", hidden = True)
    async def addut(self, ctx: disnake.ApplicationCommandInteraction, user: disnake.User = None, uytin: int = None):
        if user and uytin is None:
            await ctx.send("Tham số không hợp lệ")
            return
        uy_tin = await self.bot.db_handler.uytin(uid=user.id, uytin=uytin)
        if uy_tin["status"] == "success":
            embed = disnake.Embed(
                title="Thành công!",
                description=f"Set uy tín cho người dùng {user.display_name} thành công!\n"
                            f"Uy tín hiện tại của người dùng là {uy_tin['uytin']}",
                color=disnake.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(
                title="Lỗi",
                description=uy_tin["reason"],
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed) 

    @commands.is_owner()
    @commands.command(name="delut", decription="Xóa uy tín của người dùng", hidden = True)
    async def delut(self, ctx: disnake.ApplicationCommandInteraction, user: disnake.User = None, uytin: int = None):
        if user and uytin is None:
            await ctx.send("Tham số không hợp lệ")
            return
        uy_tin = await self.bot.db_handler.uytin(uid=user.id, uytin=-uytin)
        if uy_tin["status"] == "success":
            embed = disnake.Embed(
                title="Thành công!",
                description=f"Set uy tín cho người dùng {user.display_name} thành công!\n"
                            f"Uy tín hiện tại của người dùng là {uy_tin['uytin']}",
                color=disnake.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(
                title="Lỗi",
                description=uy_tin["reason"],
                color=disnake.Color.red()
            )
            await ctx.send(embed=embed) 
   

class BankingSystem(commands.Cog):
    def __init__(self, bot: BotCore):
        self.bot = bot

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Chuyển tiền")
    async def bank(self, ctx: disnake.AppCommandInteraction, amount: int = None, user: disnake.Member = None):
        if amount is None:
            return
        elif user is None:
            return
        userinfo = await self.bot.db_handler.get_userinfo(user.id)
        _userinfo = await self.bot.db_handler.get_userinfo(ctx.author.id)
        if userinfo["status"] == "notfound" or _userinfo["status"] == "notfound":
            await ctx.channel.send(embed=notfound_embed)
        if int(_userinfo["coin"]) < int(amount) or int(_userinfo["coin"]) == 0:
            await ctx.channel.send(f"STK [{ctx.author.id}] Giao dịch thất bại, lý do: ```Vượt hạn mức giao dịch được cấp```")
            return
        await self.bot.db_handler.transaction(ctx.author.id, -int(amount), 0, reason=f"Chuyển tiền cho {user.name}")
        await self.bot.db_handler.transaction(user.id, int(amount), 0, reason=f"Nhận tiền từ {ctx.author.name}")
        await ctx.channel.send(f"Đã chuyển {amount} Mora đến STK {user.id}")
        
def setup(bot: BotCore):
    bot.add_cog(Users(bot))
    bot.add_cog(OwnerUser(bot))
    bot.add_cog(UytinSystem(bot))
    bot.add_cog(BankingSystem(bot))