# -*- coding: utf-8 -*-
import datetime
import itertools

import disnake

from utils.music.converters import fix_characters, time_format, get_button_style, music_source_image
from utils.music.models import LavalinkPlayer
from utils.others import ProgressBar, PlayerControls


class DefaultProgressbarStaticSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = "default_progressbar_static"
        self.preview = "https://cdn.discordapp.com/attachments/554468640942981147/1047187414176759860/progressbar_static_skin.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = False
        player.controller_mode = True
        player.auto_update = 10
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = True

    def load(self, player: LavalinkPlayer) -> dict:

        data = {
            "content": None,
            "embeds": []
        }

        embed = disnake.Embed(color=player.bot.get_color(player.guild.me))
        embed_queue = None

        if not player.paused:
            emoji = "▶️"
            embed.set_author(
                name="Đang phát:",
                icon_url=music_source_image(player.current.info["sourceName"])
            )
        else:
            emoji = "⏸️"
            embed.set_author(
                name="Tạm dừng:",
                icon_url="https://cdn.discordapp.com/attachments/480195401543188483/896013933197013002/pause.png"
            )

        if player.current.is_stream:
            duration = "```ansi\n🔴 [31;1m Livestream[0m```"
        else:

            progress = ProgressBar(
                player.position,
                player.current.duration,
                bar_count=8
            )

            duration = f"```ansi\n[34;1m[{time_format(player.position)}] {('-'*progress.start)}[0m🔴️[36;1m{' '*progress.end} " \
                       f"[{time_format(player.current.duration)}][0m```\n"
            
        duration1 = "> 🔴 **Thời lượng:** `Livestream`\n" if player.current.is_stream else \
            (f"> ⏰ **Thời lượng:** `{time_format(player.current.duration)} [`" +
            f"<t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=player.current.duration - player.position)).timestamp())}:R>`]`\n"
            if not player.paused else '')

        vc_txt = ""

        txt = f"[`{fix_characters(player.current.single_title, limit=21)}`]({player.current.uri})\n\n" \
              f"{duration1}\n" \
              f"> <:author:1140220381320466452>  **⠂Tác giả:** {player.current.authors_md}\n" \
              f"> <:peppe_he:1161843804547072010> **⠂Người gọi bài:** <@{player.current.requester}>\n" \
              f"> <:volume:1140221293950668820> **⠂Âm lượng:** `{player.volume}%`\n" \
              f"> <:host:1140221179920138330> **⠂**{player}\n" \
              f"> 🌐 **⠂Vùng:** {player.node.region.title()}\n" \
              
        if not player.ping:
            txt += f"> <a:loading:1204300257874288681> **⠂Đang lấy dữ liệu từ máy chủ**\n"
        else:
            txt += f"> <a:loading:1204300257874288681> ╰[Độ trễ:{player.ping}ms\n" \
        
        if player.current.track_loops:
            txt += f"\n> <:loop:1140220877401772092> **⠂Lặp lại còn lại:** `{player.current.track_loops}` " \

        if player.current.autoplay:
            txt += f"> <:music:1140220553135931392> **⠂Tự động thêm nhạc:** `Bật`"

            try:
                txt += f" [`(link nhạc.)`]({player.current.info['extra']['related']['uri']})\n"
            except:
                txt += "\n"

        if player.loop:
            if player.loop == 'current':
                e = '<:loop:1140220877401772092>'
                m = 'Bài hát hiện tại'
            else:
                e = '<:loop:1140220877401772092>'
                m = 'Hàng'
            txt += f"\n> {e} **⠂Chế độ lặp lại:** `{m}`"

        if player.nightcore:
            txt += f"\n> <:nightcore:1140227024108130314> **⠂Hiệu ứng Nightcore:** `kích hoạt`"

        if player.current.album_name:
            txt += f"\n> <:soundcloud:1140277420033843241> **⠂Album:** [`{fix_characters(player.current.album_name, limit=16)}`]({player.current.album_url})"

        if player.current.playlist_name:
            txt += f"\n> <:library:1140220586640019556> **⠂Playlist:** [`{fix_characters(player.current.playlist_name, limit=16)}`]({player.current.playlist_url})"

        if (qlenght:=len(player.queue)) and not player.mini_queue_enabled:
            txt += f"\n> <a:raging:1117802405791268925> **⠂Bài hát trong dòng:** `{qlenght}`"

        if player.keep_connected:
            txt += f"\n> <:247:1140230869643169863> **⠂Chế độ 24/7:** `Kích hoạt`"

        elif player.restrict_mode:
            txt += f"\n> <:GuraCityCopStop:1135921852888395797> **⠂Hạn chế:** `Kích hoạt`"

        txt += f"{vc_txt}\n"

        if player.command_log:
            txt += f"``Tương tác cuối cùng``\n"
            txt += f"> {player.command_log_emoji} - {player.command_log}\n"

        txt += duration

        if qlenght and player.mini_queue_enabled:

            queue_txt = "\n".join(
                f"`{(n + 1):02}) [{time_format(t.duration) if not t.is_stream else '🔴 Livestream'}]` [`{fix_characters(t.title, 38)}`]({t.uri})"
                for n, t in (enumerate(itertools.islice(player.queue, 3)))
            )

            embed_queue = disnake.Embed(title=f"Bài hát đang chờ:  {qlenght}", color=player.bot.get_color(player.guild.me),
                                        description=f"\n{queue_txt}")

            if not player.loop and not player.keep_connected and not player.paused and not player.current.is_stream:

                queue_duration = 0

                for t in player.queue:
                    if not t.is_stream:
                        queue_duration += t.duration

                if queue_duration:
                    embed_queue.description += f"\n`[⌛ Các bài hát kết thúc sau` <t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=(queue_duration + (player.current.duration if not player.current.is_stream else 0)) - player.position)).timestamp())}:R> `⌛]`"

            embed_queue.set_image(url="https://media.discordapp.net/attachments/779998700981321749/865589761858600980/ayakapfpBanner2.gif")

        embed.description = txt
        embed.set_thumbnail(url=player.current.thumb)
        embed.set_footer(
            text="Kadin Music system",
            icon_url="https://cdn.discordapp.com/emojis/986511889142009856.webp?size=96&quality=lossless",
        )

        data["embeds"] = [embed_queue, embed] if embed_queue else [embed]

        data["components"] = [
            
        ]

        try:
            if isinstance(player.text_channel.parent, disnake.ForumChannel):
                data["content"] = f"`{emoji} {fix_characters(player.current.title, 50)}`"
        except:
            pass

        return data

def load():
    return DefaultProgressbarStaticSkin()
