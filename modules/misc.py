# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import datetime
import json
import os.path
import platform
import traceback
from copy import deepcopy
from itertools import cycle
from os import getpid
from random import shuffle
from typing import TYPE_CHECKING

import aiofiles
import disnake
import humanize
import psutil
from aiohttp import ClientSession
from disnake.ext import commands

from utils.db import DBModel, db_models
from utils.music.checks import check_requester_channel
from utils.music.converters import time_format, URL_REG
from utils.others import select_bot_pool, CustomContext, paginator

if TYPE_CHECKING:
    from utils.client import BotCore


def remove_blank_spaces(d):

    for k, v in list(d.items()):

        new_k = k.strip()
        if new_k != k:
            d[new_k] = d.pop(k)

        if isinstance(v, str):
            new_v = v.strip()
            if new_v != v:
                d[new_k] = new_v
        elif isinstance(v, dict):
            remove_blank_spaces(v)


class Misc(commands.Cog):

    emoji = "🔰"
    name = "Hệ thống"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: BotCore):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.presences())
        self.extra_user_bots = []
        self.extra_user_bots_ids = [int(i) for i in bot.config['ADDITIONAL_BOT_IDS'].split() if i.isdigit()]

    def placeholders(self, text: str):

        if not text:
            return ""

        try:
            text = text.replace("{owner}", str(self.bot.owner))
        except AttributeError:
            pass

        if [i for i in ("{players_count}", "{players_count_allbotchannels}", "{players_count_allbotservers}") if i in text]:

            channels = set()
            guilds = set()
            users = set()
            player_count = 0

            for bot in self.bot.pool.bots:

                for player in bot.music.players.values():
                    if not player.auto_pause and not player.paused:
                        if bot == self.bot:
                            player_count += 1
                        try:
                            vc = player.guild.me.voice.channel
                        except AttributeError:
                            continue
                        channels.add(vc.id)
                        guilds.add(player.guild.id)
                        for u in vc.members:
                            if u.bot or u.voice.deaf or u.voice.self_deaf:
                                continue
                            users.add(u.id)

                if "{players_count}" in text:
                    if not player_count:
                        return
                    text = text.replace("{players_count}", str(player_count))

            if "{players_count_allbotchannels}" in text:

                if not channels:
                    return

                text = text.replace("{players_count_allbotchannels}", str(len(channels)))

            if "{players_count_allbotservers}" in text:

                if not guilds:
                    return

                text = text.replace("{players_count_allbotservers}", str(len(guilds)))

            if "{players_user_count}" in text:

                if not users:
                    return

                text = text.replace("{players_user_count}", str(len(users)))

        return text \
            .replace("{users}", f'{len([m for m in self.bot.users if not m.bot]):,}'.replace(",", ".")) \
            .replace("{playing}", f'{len(self.bot.music.players):,}'.replace(",", ".")) \
            .replace("{guilds}", f'{len(self.bot.guilds):,}'.replace(",", ".")) \
            .replace("{uptime}", time_format((disnake.utils.utcnow() - self.bot.uptime).total_seconds() * 1000,
                                             use_names=True))


    async def presences(self):

        try:

            activities = []

            for i in self.bot.config["LISTENING_PRESENCES"].split("||"):
                if i:
                    activities.append({"name":i, "type": "listening"})

            for i in self.bot.config["WATCHING_PRESENCES"].split("||"):
                if i:
                    activities.append({"name": i, "type": "watching"})

            for i in self.bot.config["PLAYING_PRESENCES"].split("||"):
                if i:
                    activities.append({"name": i, "type": "playing"})

            for i in self.bot.config["CUSTOM_STATUS_PRESENCES"].split("||"):
                if i:
                    activities.append({"name": i, "type": "custom_status"})

            for i in self.bot.config["STREAMING_PRESENCES"].split("|||"):
                if i:
                    try:
                        name, url = i.split("||")
                        activities.append({"name": name, "url": url.strip(" "), "type": "streaming"})
                    except Exception:
                        traceback.print_exc()

            if not activities:
                return

            shuffle(activities)

            activities = cycle(activities)

            ignore_sleep = False

            while True:

                try:
                    if self.bot._presence_loop_started and ignore_sleep is False:
                        await asyncio.sleep(self.bot.config["PRESENCE_INTERVAL"])
                except AttributeError:
                    self.bot._presence_loop_started = True

                await self.bot.wait_until_ready()

                activity_data = next(activities)

                activity_name = self.placeholders(activity_data["name"])

                if not activity_name:
                    await asyncio.sleep(15)
                    ignore_sleep = True
                    continue

                ignore_sleep = False

                if activity_data["type"] == "listening":
                    activity = disnake.Activity(
                        type=disnake.ActivityType.listening,
                        name=activity_name,
                    )

                elif activity_data["type"] == "watching":
                    activity = disnake.Activity(
                        type=disnake.ActivityType.watching,
                        name=activity_name,
                    )

                elif activity_data["type"] == "streaming":
                    activity = disnake.Activity(
                        type=disnake.ActivityType.streaming,
                        name=activity_name,
                        url=activity_data["url"]
                    )

                elif activity_data["type"] == "playing":
                    activity = disnake.Game(name=activity_name)

                else:
                    activity = disnake.Activity(
                        name="customstatus",
                        type=disnake.ActivityType.custom,
                        state=activity_name,
                    )

                await self.bot.change_presence(activity=activity)

                await asyncio.sleep(self.bot.config["PRESENCE_INTERVAL"])

        except Exception:
            traceback.print_exc()


    @commands.Cog.listener("on_guild_join")
    async def guild_add(self, guild: disnake.Guild):

        if str(self.bot.user.id) in self.bot.config["INTERACTION_BOTS_CONTROLLER"]:
            await guild.leave()
            return

        interaction_invite = ""

        bots_in_guild = []
        bots_outside_guild = []

        for bot in self.bot.pool.bots:

            if bot == self.bot:
                continue

            if not bot.bot_ready:
                continue

            if bot.user in guild.members:
                bots_in_guild.append(bot)
            else:
                bots_outside_guild.append(bot)

        components = [disnake.ui.Button(custom_id="bot_invite", label="Cần thêm bot âm nhạc hả? Bấm vào đây nè.")] if [b for b in self.bot.pool.bots if b.appinfo and b.appinfo.bot_public] else []

        if self.bot.pool.controller_bot != self.bot:
            interaction_invite = f"[`{disnake.utils.escape_markdown(str(self.bot.pool.controller_bot.user.name))}`]({disnake.utils.oauth_url(self.bot.pool.controller_bot.user.id, scopes=['applications.commands'])})"

        if cmd:=self.bot.get_command("setup"):
            cmd_text = f"Nếu muốn, hãy sử dụng lệnh **/{cmd.name}** để tạo kênh chuyên dụng để yêu cầu " \
                         "bài hát không có lệnh và để giao diện nhạc cố định ở kênh chuyên dụng.\n\n"
        else:
            cmd_text = ""

        if self.bot.config["SUPPORT_SERVER"]:
            support_server = f"Nếu bạn có bất kỳ câu hỏi hoặc muốn theo dõi những tin tức mới nhất, bạn có thể vào [`máy chủ hỗ trợ`]({self.bot.config['SUPPORT_SERVER']} của bé)"
        else:
            support_server = ""

        if self.bot.default_prefix and not self.bot.config["INTERACTION_COMMAND_ONLY"]:
            guild_data = await self.bot.get_global_data(guild.id, db_name=DBModel.guilds)
            prefix = disnake.utils.escape_markdown(guild_data['prefix'], as_needed=True)
        else:
            prefix = ""

        image = "https://cdn.discordapp.com/attachments/554468640942981147/1082887587770937455/rainbow_bar2.gif"

        color = self.bot.get_color()

        send_video = ""

        try:
            channel = guild.system_channel if guild.system_channel.permissions_for(guild.me).send_messages else None
        except AttributeError:
            channel = None

        if not channel:

            if guild.me.guild_permissions.view_audit_log:

                async for entry in guild.audit_logs(action=disnake.AuditLogAction.integration_create, limit=50):

                    if entry.target.application_id == self.bot.user.id:

                        embeds = []

                        embeds.append(
                            disnake.Embed(
                                color=color,
                                description=f"Xin chào :>\n"
                                            f"Cảm ơn bạn đã mời bé vào server {guild.name} nhé."
                            ).set_image(url=image)
                        )

                        if interaction_invite:
                            embeds.append(
                                disnake.Embed(
                                    color=color,
                                    description=f"**Lưu ý quan trọng:** Lệnh gạch chéo của bé hoạt động thông qua "
                                                 f"từ ứng dụng sau: {interaction_invite}\n\n"
                                                 f"Nếu các lệnh ứng dụng ở trên không được hiển thị khi gõ "
                                                 f"gạch chéo (**/**) trên kênh máy chủ **{guild.name}** bạn sẽ phải "
                                                 f"click vào tên bên trên để tích hợp lệnh gạch chéo trên server"
                                                 f"**{guild.name}**.\n`Lưu ý: Nếu các lệnh vẫn không xuất hiện sau "
                                                 f"tích hợp các lệnh, có lẽ máy chủ của bạn đã đạt đến "
                                                 f"bot có lệnh gạch chéo đã đăng ký.`"
                                ).set_image(url=image)
                            )
                        else:
                            embeds.append(
                                disnake.Embed(
                                    color=color,
                                    description=f"Để xem tất cả các lệnh của tôi sử dụng thanh (**/**) trên máy chủ " \
                                                 f"**{guild.name}**"
                                ).set_image(url=image)
                            )

                        if prefix:
                            prefix_msg = f"Prefix máy chủ của bé là **{guild.name}** là: **{prefix}**"
                        else:
                            prefix = self.bot.default_prefix
                            prefix_msg = f"Prefix của bé là **{prefix}**"

                        embeds.append(
                            disnake.Embed(
                                color=color,
                                description=f"Tôi cũng có lệnh văn bản theo tiền tố. {prefix_msg} (tôi đề cập đến "
                                             f" cũng hoạt động như một tiền tố). Để xem tất cả các lệnh văn bản của tôi "
                                             f"sử dụng **{prefix}help** trên kênh máy chủ **{guild.name}**."
                                             f"Nếu bạn muốn thay đổi tiền tố của tôi, hãy sử dụng lệnh **{prefix}setprefix** "
                                             f" (bạn có thể có tiền tố cá nhân bằng lệnh "
                                             f"**{prefix}setmyprefix**)."
                            ).set_image(url=image)
                        )

                        if bots_in_guild:

                            msg = f"Bé nhận thấy rằng có các bot khác trên máy chủ **{guild.name}** mà bé tương thích với " \
                                    f"hệ thống đa giọng nói: {', '.join(b.user.mention for b in bots_in_guild)}\n\n" \
                                    f"Khi sử dụng lệnh âm nhạc (ví dụ: phát) mà không có một trong các bot được kết nối với kênh, " \
                                     "một trong những bot trên máy chủ sẽ được sử dụng."

                            if not self.bot.pool.config.get("MULTIVOICE_VIDEO_DEMO_URL"):
                                embeds.append(
                                    disnake.Embed(
                                        color=color,
                                        description=msg
                                    ).set_image(url=image)
                                )

                            else:
                                send_video = msg

                        elif bots_outside_guild and self.bot.config.get('MULTIVOICE_VIDEO_DEMO_URL'):
                            send_video = "**Nếu có nhu cầu trên máy chủ của bạn, bạn cũng có thể thêm nhiều bot âm nhạc bổ sung.\n" \
                                          "Tất cả các bot đều có chung tiền tố và lệnh gạch chéo, điều này loại trừ sự cần thiết của " \
                                          f"ghi nhớ tiền tố và lệnh gạch chéo cho từng bot riêng lẻ.\n\n" \
                                          f"Hãy xem [video]({self.bot.config['MULTIVOICE_VIDEO_DEMO_URL']}) minh hoạ cách sử dụng nhiều bot trong thực tế.**"

                        if support_server:
                            embeds.append(disnake.Embed(color=color, description=support_server).set_image(url=image))

                        try:
                            await entry.user.send(embeds=embeds, components=components)
                            if send_video:
                                await asyncio.sleep(1)
                                await entry.user.send(f"{send_video}\n\nKiểm tra [**video**]({self.bot.config['MULTIVOICE_VIDEO_DEMO_URL']})thể hiện chức năng này.")
                            return
                        except disnake.Forbidden:
                            pass
                        except Exception:
                            traceback.print_exc()
                        break

        if not channel:

            for c in (guild.public_updates_channel, guild.rules_channel):

                if c and c.permissions_for(guild.me).send_messages:
                    channel = c
                    break

            if not channel:
                return

        embeds = []

        if interaction_invite:

            embeds.append(
                disnake.Embed(
                    color=color,
                    description=f"Xin chào! Để xem tất cả các lệnh của bé, hãy gõ dấu gạch chéo (**/**) và chọn "
                                 f"các lệnh của ứng dụng sau: {interaction_invite}\n\n"
                                 f"Nếu các lệnh ứng dụng trên không được hiển thị khi gõ dấu gạch chéo (**/**) bạn "
                                 f"bạn sẽ phải bấm vào tên bên trên để tích hợp các lệnh gạch chéo trên máy chủ của mình.\n"
                                 f"`Lưu ý: Nếu các lệnh vẫn không xuất hiện sau khi tích hợp các lệnh, có lẽ "
                                 f"server đã đạt đến giới hạn bot với các lệnh gạch chéo đã đăng ký.`"

                ).set_image(url=image)
            )

        else:
            embeds.append(
                disnake.Embed(
                    color=color, description="Xin chào! Để xem tất cả các lệnh của bé, hãy sử dụng dấu gạch chéo về phía trước (**/**)"
                ).set_image(url=image)
            )

        if prefix:
            prefix_msg = f"Prefix của tui là: **{prefix}**"
        else:
            prefix = self.bot.default_prefix
            prefix_msg = f"Prefix của tui là **{prefix}**"

        embeds.append(
            disnake.Embed(
                color=color,
                description=f"Tôi cũng có lệnh văn bản theo tiền tố. {prefix_msg} (tôi đề cập đến "
                             f" cũng hoạt động như một tiền tố). Để xem tất cả các lệnh văn bản của tôi, hãy sử dụng "
                             f"**{prefix}help**. Nếu bạn muốn thay đổi tiền tố của tôi, hãy sử dụng lệnh **{prefix}setprefix** "
                             f" (bạn có thể có tiền tố cá nhân bằng cách sử dụng lệnh **{prefix}setmyprefix**)."
            ).set_image(url=image)
        )

        if bots_in_guild:

            msg = f"Tôi nhận thấy rằng có các bot khác trên máy chủ **{guild.name}** mà tôi tương thích với " \
                   f"hệ thống đa giọng nói: {', '.join(b.user.mention for b in bots_in_guild)}\n\n" \
                   f"Khi sử dụng lệnh âm nhạc (ví dụ: phát) mà không có một trong các bot được kết nối với kênh, " \
                    f"của các bot miễn phí trên máy chủ."

            if not self.bot.config.get('MULTIVOICE_VIDEO_DEMO_URL'):
                embeds.append(
                    disnake.Embed(
                        color=color,
                        description=msg
                    ).set_image(url=image)
                )
            else:
                send_video = msg

        elif bots_outside_guild and self.bot.config.get('MULTIVOICE_VIDEO_DEMO_URL'):
            send_video = "**Nếu có nhu cầu trên máy chủ của bạn, bạn cũng có thể thêm nhiều bot âm nhạc bổ sung.\n" \
                           "Tất cả các bot đều có chung tiền tố và lệnh gạch chéo, điều này loại trừ sự cần thiết của " \
                           f"ghi nhớ tiền tố và lệnh gạch chéo cho từng bot riêng lẻ.\n\n" \
                         f"Hãy xem [video]({self.bot.config['MULTIVOICE_VIDEO_DEMO_URL']}) minh hoạ cách sử dụng nhiều bot trong thực tế.**"

        embeds.append(disnake.Embed(color=color, description=cmd_text).set_image(url=image))

        if support_server:
            embeds.append(disnake.Embed(color=color, description=support_server).set_image(url=image))

        kwargs = {"delete_after": 60} if channel == guild.rules_channel else {"delete_after": 300}

        timestamp = int((disnake.utils.utcnow() + datetime.timedelta(seconds=kwargs["delete_after"])).timestamp())

        embeds[-1].description += f"\nTin nhắn này sẽ tự động bị xóa sau <t:{timestamp}:R>"

        try:
            await channel.send(embeds=embeds, components=components, **kwargs)
            if send_video:
                if "delete_after" in kwargs:
                    kwargs["delete_after"] = 600
                await asyncio.sleep(1)
                await channel.send(f"{send_video}\n\nKiểm tra [**video**]({self.bot.config['MULTIVOICE_VIDEO_DEMO_URL']})thể hiện chức năng này.", **kwargs)
        except:
            print(f"Không gửi được tin nhắn từ máy chủ mới trên kênh: {channel}\n"
                   f"ID kênh: {channel.id}\n"
                   f"Loại kênh: {type(channel)}\n"
                  f"{traceback.format_exc()}")


    about_cd = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.member)

    @commands.command(name="about", aliases=["info", "botinfo"], description="Xem thông tin về tôi.",
                      cooldown=about_cd)
    async def about_legacy(self, ctx: CustomContext):
        await self.about.callback(self=self, interaction=ctx)


    @commands.slash_command(
        description=f"{desc_prefix}Xem thông tin về tôi.", cooldown=about_cd, dm_permission=False
    )
    async def about(
            self,
            interaction: disnake.AppCmdInter
    ):

        inter, bot = await select_bot_pool(interaction, first=True)

        if not bot:
            return

        await inter.response.defer(ephemeral=True)

        try:
            lavalink_ram = psutil.Process(self.bot.pool.lavalink_instance.pid).memory_info().rss
        except:
            lavalink_ram = 0

        python_ram = psutil.Process(getpid()).memory_info().rss

        ram_msg = f"> <:python:1204300262911774761> **⠂Sử dụng RAM (Python):** `{humanize.naturalsize(python_ram)}`\n"

        if lavalink_ram:
            ram_msg += f"> <:lavalink:1181833300772388984> **⠂Sử dụng RAM (Lavalink):** `{humanize.naturalsize(lavalink_ram)}`\n" \
                        f"> <:ram:1204300272957001778> **⠂Mức sử dụng RAM (Tổng cộng):** `{humanize.naturalsize(python_ram + lavalink_ram)}`\n"
        else:
            ram_msg += f"> <:lavalink:1181833300772388984> **⠂Sử dụng RAM (Lavalink):** `Offline`\n" \
                        f"> <:ram:1204300272957001778> **⠂Mức sử dụng RAM (Tổng cộng):** `{humanize.naturalsize(python_ram + 0)}`\n"

        guild = bot.get_guild(inter.guild_id) or inter.guild

        color = bot.get_color(inter.guild.me if inter.guild else guild.me)

        embed = disnake.Embed(description="", color=color)

        active_players_other_bots = 0
        inactive_players_other_bots = 0
        paused_players_other_bots = 0

        all_guilds_ids = set()

        for b in bot.pool.bots:
            for g in b.guilds:
                all_guilds_ids.add(g.id)

        guilds_size  = len(all_guilds_ids)

        latency = round(bot.latency * 100)
        if latency >= 1000:
            latency_bot = f"Độ trễ rất cao {latency}"
        elif latency >= 200:
            latency_bot = f"Độ trễ cao {latency}"
        elif latency >= 100:
            latency_bot = f"Độ trễ trung bình {latency}"
        else:
            latency_bot = f"{latency}"

        public_bot_count = 0
        private_bot_count = 0

        users = set()
        bots = set()
        listeners = set()

        user_count = 0
        bot_count = 0

        botpool_ids = [b.user.id for b in self.bot.pool.bots]

        node_data = {}
        nodes_available = set()
        nodes_unavailable = set()

        for user in bot.users:
            if user.bot:
                bot_count += 1
            else:
                user_count += 1

        for b in bot.pool.bots:

            for user in b.users:

                if user.id in botpool_ids:
                    continue

                if user.bot:
                    bots.add(user.id)
                else:
                    users.add(user.id)

            for n in b.music.nodes.values():

                identifier = f"{n.identifier} (v{n.version})"

                if not identifier in node_data:
                    node_data[identifier] = {"total": 0, "available": 0, "website": n.website}

                node_data[identifier]["total"] += 1

                if n.is_available:
                    node_data[identifier]["available"] += 1

            for p in b.music.players.values():

                if p.auto_pause:
                    inactive_players_other_bots += 1

                elif p.paused:
                    try:
                        if any(m for m in p.guild.me.voice.channel.members if not m.bot):
                            paused_players_other_bots += 1
                            continue
                    except AttributeError:
                        pass
                    inactive_players_other_bots += 1

                else:
                    active_players_other_bots += 1
                    try:
                        vc = p.guild.me.voice.channel
                    except AttributeError:
                        continue
                    for u in vc.members:
                        if u.bot:
                            continue
                        listeners.add(u.id)

            if not b.appinfo or not b.appinfo.bot_public:
                private_bot_count += 1
            else:
                public_bot_count += 1

        for identifier, data in node_data.items():

            if data["available"] > 0:
                if data['website']:
                    nodes_available.add(
                        f"> [`✅⠂{identifier}`]({data['website']}) `[{data['available']}/{data['total']}]`")
                else:
                    nodes_available.add(f"> `✅⠂{identifier} [{data['available']}/{data['total']}]`")
            else:
                nodes_unavailable.add(f"> `❌⠂{identifier}`")

        node_txt_final = "\n".join(nodes_available)

        if node_txt_final:
            node_txt_final += "\n"
        node_txt_final += "\n".join(nodes_unavailable)

        embed.description += f"### Thông tin của {bot.user.name}#{bot.user.discriminator}:\n" \
                            f"> <:AyakaAnnoyed:1135418690632957993> **⠂Tổng máy chủ:** `{len(bot.guilds)}`\n" \
                            f"> 👥 **⠂Số người dùng** `{user_count:,}`\n"

        if bot_count:
            embed.description += f"> 🤖 **⠂Bots:** `{bot_count:,}`\n"

        if len(bot.pool.bots) > 1:

            embed.description += "### Tổng số liệu thống kê trên tất cả các bot:\n"

            if public_bot_count:
                embed.description += f"> 🤖 **⠂Bot được cài đặt là công khai:** `{public_bot_count:,}`\n"

            embed.description += f"> 🏙️ **⠂Tổng máy chủ:** `{guilds_size}`\n"

            if users_amount := len(users):
                embed.description += f"> 👥 **⠂Tổng người dùng:** `{users_amount:,}`\n"

            if bots_amount := len(bots):
                embed.description += f"> 🤖 **⠂Bots:** `{bots_amount:,}`\n"

        embed.description += "### Các thông tin khác:\n"

        if active_players_other_bots:
            embed.description += f"> <:disc:1140220627781943339> **⠂Đang Phát:** `{active_players_other_bots:,}`\n"

        if paused_players_other_bots:
            embed.description += f"> <:pause:1140220668110180352> **⠂Tạm dừng:** `{paused_players_other_bots:,}`\n"

        if inactive_players_other_bots:
            embed.description += f"> <:stop:1140221258575925358> **⠂Không hoạt động (afk):** `{inactive_players_other_bots:,}`\n"

        if listeners:
            embed.description += f"> 🎧 **⠂Số người đang nghe:** `{len(listeners):,}`\n"

        if bot.pool.commit:
            embed.description += f"> <:upvote:1146329733102047242> **⠂Phiên bản hiện tại:** `{bot.pool.commit[:7]}`\n"

        embed.description += f"> <:python:1204300262911774761> **Phiên bản của Python:** `{platform.python_version()}`\n" \
                             f"> <:disnake:1204300267257069569> **Phiên bản của Disnake:** `Pre-release {disnake.__version__}`\n" \
                             f"> <:home:1208751844373827607> **Hệ điều hành đang sử dụng:** `{platform.system()} {platform.release()} {platform.machine()}`\n" \
                             f"> 📶 **Độ trễ API:** `{latency_bot}ms`\n" \
                             f"{ram_msg}" \
                             f"> <a:loading:1204300257874288681> **Lần khởi động lại cuối cùng:** <t:{int(bot.uptime.timestamp())}:R>\n"

        if not bot.config["INTERACTION_COMMAND_ONLY"]:

            try:
                guild_data = inter.global_guild_data
            except AttributeError:
                guild_data = await bot.get_global_data(inter.guild_id, db_name=DBModel.guilds)
                inter.global_guild_data = guild_data

            if guild_data["prefix"]:
                embed.description += f"> ⌨️ **⠂Prefix máy chủ:** `{disnake.utils.escape_markdown(guild_data['prefix'], as_needed=True)}`\n"
            else:
                embed.description += f"> ⌨️ **⠂Prefix tiêu chuẩn:** `{disnake.utils.escape_markdown(bot.default_prefix, as_needed=True)}`\n"

            try:
                user_data = inter.global_user_data
            except AttributeError:
                user_data = await bot.get_global_data(inter.author.id, db_name=DBModel.users)
                inter.global_user_data = user_data

            if user_data["custom_prefix"]:
                embed.description += f"> ⌨️ **⠂Prefix người dùng của bạn:** `{disnake.utils.escape_markdown(user_data['custom_prefix'], as_needed=True)}`\n"

        links = "Testing"

        if bot.config["SUPPORT_SERVER"]:
            links = f"[`[Hỗ Trợ]`]({bot.config['SUPPORT_SERVER']})  **|** {links}"

        embed.description += f"> 🌐 **⠂**{links}\n"

        try:
            owner = bot.appinfo.team.owner
        except AttributeError:
            owner = bot.appinfo.owner

        if node_txt_final:

            embed.description += f"### Máy chủ âm nhạc (Máy chủ Lavalink):\n{node_txt_final}"

        try:
            avatar = owner.avatar.with_static_format("png").url
        except AttributeError:
            avatar = owner.default_avatar.with_static_format("png").url

        embed.set_footer(
            icon_url=avatar,
            text=f"Chủ vận hành: {owner} [{owner.id}]"
        )

        components = [disnake.ui.Button(custom_id="bot_invite", label="Thêm tôi vào máy chủ của bạn")] if [b for b in bot.pool.bots if b.appinfo and (b.appinfo.bot_public or await b.is_owner(inter.author))] else None

        try:
            await inter.edit_original_message(embed=embed, components=components)
        except (AttributeError, disnake.InteractionNotEditable):
            try:
                await inter.response.edit_message(embed=embed, components=components)
            except:
                await inter.send(embed=embed, ephemeral=True, components=components)


    @commands.Cog.listener("on_button_click")
    async def invite_button(self, inter: disnake.MessageInteraction, is_command=False):

        if not is_command and inter.data.custom_id != "bot_invite":
            return

        bots_invites = []
        bots_in_guild = []

        guild = None

        if inter.guild_id:
            guild = inter.guild
        else:
            for bot in self.bot.pool.bots:
                if (guild:=bot.get_guild(inter.guild_id)):
                    break

        for bot in sorted(self.bot.pool.bots, key=lambda b: len(b.guilds)):

            try:
                if not bot.appinfo.bot_public and not await bot.is_owner(inter.author):
                    continue
            except:
                continue

            kwargs = {"redirect_uri": self.bot.config['INVITE_REDIRECT_URL']} if self.bot.config['INVITE_REDIRECT_URL'] else {}

            invite = f"[`{disnake.utils.escape_markdown(str(bot.user.name))}`]({disnake.utils.oauth_url(bot.user.id, permissions=disnake.Permissions(bot.config['INVITE_PERMISSIONS']), scopes=('bot', 'applications.commands'), **kwargs)})"

            if bot.appinfo.flags.gateway_message_content_limited:
                invite += f" ({len(bot.guilds)}/100)"
            else:
                invite += f" ({len(bot.guilds)})"

            if guild and inter.author.guild_permissions.manage_guild and bot.user in guild.members:
                bots_in_guild.append(invite)
            else:
                bots_invites.append(invite)

        txt = ""

        if bots_invites:
            txt += "**Các bot âm nhạc có sẵn:**\n"
            for i in disnake.utils.as_chunks(bots_invites, 2):
                txt += " | ".join(i) + "\n"
            txt += "\n"

        if bots_in_guild:
            txt += "**Các bot âm nhạc đã có trên máy chủ hiện tại:**\n"
            for i in disnake.utils.as_chunks(bots_in_guild, 2):
                txt += " | ".join(i) + "\n"

        if not txt:
            await inter.send(
                embed=disnake.Embed(
                    colour=self.bot.get_color(
                        inter.guild.me if inter.guild else guild.me if guild else None
                    ),
                    title="**Không có bot công khai nào..**",
                ), ephemeral=True
            )
            return

        controller_bot = self.bot.pool.controller_bot

        if (len(bots_in_guild) + len(bots_invites)) > 1 and f"client_id={controller_bot.user.id}" not in txt:
            invite = f"[`{disnake.utils.escape_markdown(str(controller_bot.user.name))}`]({disnake.utils.oauth_url(controller_bot.user.id, scopes=['applications.commands'])})"
            txt = f"**Đăng ký lệnh gạch chéo trên máy chủ:**\n{invite}\n\n" + txt

        color = self.bot.get_color(inter.guild.me if inter.guild else guild.me if guild else None)

        embeds = [
            disnake.Embed(
                colour=self.bot.get_color(inter.guild.me if inter.guild else guild.me if guild else None),
                description=p, color=color
            ) for p in paginator(txt)
        ]

        await inter.send(embeds=embeds, ephemeral=True)


    @commands.command(name="invite", aliases=["convidar"], description="Hiển thị liên kết mời của tôi để bạn có thể thêm tôi vào máy chủ của bạn.")
    async def invite_legacy(self, ctx):
        await self.invite.callback(self=self, inter=ctx)


    @commands.slash_command(
        description=f"{desc_prefix}Hiển thị liên kết lời mời của tôi để bạn thêm tôi vào máy chủ của bạn.",
        dm_permission=False
    )
    async def invite(self, inter: disnake.AppCmdInter):

        await inter.response.defer(ephemeral=True)

        await self.invite_button(inter, is_command=True)

    @commands.user_command(name="Avatar", dm_permission=False)
    async def avatar(self, inter: disnake.UserCommandInteraction):

        embeds = []

        assets = {}

        if self.bot.intents.members:
            user = (await self.bot.fetch_user(inter.target.id) if not inter.target.bot else self.bot.get_user(inter.target.id))
        else:
            user = inter.target

        try:
            if inter.target.guild_avatar:
                assets["Avatar (Server)"] = inter.target.guild_avatar.with_static_format("png")
        except AttributeError:
            pass
        assets["Avatar (User)"] = user.display_avatar.with_static_format("png")
        if user.banner:
            assets["Banner"] = user.banner.with_static_format("png")

        for name, asset in assets.items():
            embed = disnake.Embed(description=f"{inter.target.mention} **[{name}]({asset.with_size(2048).url})**",
                                  color=self.bot.get_color(inter.guild.me if inter.guild else None))
            embed.set_image(asset.with_size(256).url)
            embeds.append(embed)

        await inter.send(embeds=embeds, ephemeral=True)

    @commands.is_owner()
    @commands.max_concurrency(1, commands.BucketType.default)
    @commands.command(hidden=True, description="Lệnh tạm thời để sửa dấu trang có khoảng trắng"
                                                "gây ra lỗi trong một số trường hợp.")
    async def fixfavs(self, ctx: CustomContext):

        if not os.path.isdir("./local_database/fixfavs_backup"):
            os.makedirs("./local_database/fixfavs_backup")

        async with ctx.typing():

            for bot in self.bot.pool.bots:

                db_data = await bot.pool.database.query_data(collection=str(bot.user.id), db_name=DBModel.guilds, limit=300)
    
                async with aiofiles.open(f"./local_database/fixfavs_backup/guild_favs_{bot.user.id}.json", "w") as f:
                    await f.write(json.dumps(db_data, indent=4))

                for data in db_data:
                    try:
                        remove_blank_spaces(data["player_controller"]["fav_links"])
                    except KeyError:
                        continue
                    await bot.update_data(id_=data["_id"], data=data, db_name=DBModel.guilds)

            db_data = await self.bot.pool.database.query_data(collection="global", db_name=DBModel.users, limit=500)

            async with aiofiles.open("./local_database/fixfavs_backup/user_favs.json", "w") as f:
                await f.write(json.dumps(db_data, indent=4))

            for data in db_data:
                remove_blank_spaces(data["fav_links"])
                await self.bot.update_global_data(id_=data["_id"], data=data, db_name=DBModel.users)

            await ctx.send("Mục yêu thích đã được sửa thành công!")

    async def cog_check(self, ctx):
        return await check_requester_channel(ctx)

    def cog_unload(self):

        try:
            self.task.cancel()
        except:
            pass


class GuildLog(commands.Cog):

    def __init__(self, bot: BotCore):
        self.bot = bot
        self.hook_url: str = ""

        if bot.config["BOT_ADD_REMOVE_LOG"]:

            if URL_REG.match(bot.config["BOT_ADD_REMOVE_LOG"]):
                self.hook_url = bot.config["BOT_ADD_REMOVE_LOG"]
            else:
                print("URL Webhook không hợp lệ (để gửi nhật ký khi thêm/xóa bot).")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):

        if str(self.bot.user.id) in self.bot.config["INTERACTION_BOTS_CONTROLLER"]:
            return

        print(f"Bị xóa khỏi máy chủ: {guild.name} - [{guild.id}]")

        try:
            await self.bot.music.players[guild.id].destroy()
        except KeyError:
            pass
        except:
            traceback.print_exc()

        if not self.hook_url:
            return

        try:
            await self.send_hook(guild, title="Đã loại tôi khỏi máy chủ", color=disnake.Color.red())
        except:
            traceback.print_exc()

        await self.bot.update_appinfo()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):

        if str(self.bot.user.id) in self.bot.config["INTERACTION_BOTS_CONTROLLER"]:
            return

        print(f"Máy chủ mới: {guild.name} - [{guild.id}]")

        try:
            guild_data = await self.bot.get_data(guild.id, db_name=DBModel.guilds)
            guild_data["player_controller"] = deepcopy(db_models[DBModel.guilds]["player_controller"])
            await self.bot.update_data(guild.id, guild_data, db_name=DBModel.guilds)
        except:
            traceback.print_exc()

        if not self.hook_url:
            return

        try:
            await self.send_hook(guild, title="Đã thêm tôi vào một máy chủ mới", color=disnake.Color.green())
        except:
            traceback.print_exc()

        await self.bot.update_appinfo()

    async def send_hook(self, guild: disnake.Guild, title: str, color: disnake.Color):

        created_at = int(guild.created_at.timestamp())

        embed = disnake.Embed(
            description=f"__**{title}:**__\n"
                        f"```{guild.name}```\n"
                        f"**ID:** `{guild.id}`\n"
                        f"**Chủ sở hữu:** `{guild.owner} [{guild.owner.id}]`\n"
                        f"**Ngày tạo** <t:{created_at}:f> - <t:{created_at}:R>\n"
                        f"**Cấp xác minh:** `{guild.verification_level or 'không có'}`\n"
                        f"**Số người dùng:** `{len([m for m in guild.members if not m.bot])}`\n"
                        f"**Bots:** `{len([m for m in guild.members if m.bot])}`\n",
            color=color
        )

        try:
            embed.set_thumbnail(url=guild.icon.replace(static_format="png").url)
        except AttributeError:
            pass

        async with ClientSession() as session:
            webhook = disnake.Webhook.from_url(self.hook_url, session=session)
            await webhook.send(
                content=f"Số máy chủ hiện tại {len(self.bot.guilds)} ",
                username=self.bot.user.name,
                avatar_url=self.bot.user.display_avatar.replace(size=256, static_format="png").url,
                embed=embed
            )


def setup(bot: BotCore):
    bot.add_cog(Misc(bot))
    bot.add_cog(GuildLog(bot))
