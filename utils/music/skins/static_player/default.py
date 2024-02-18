# -*- coding: utf-8 -*-
import datetime
import itertools

import disnake

from utils.music.converters import fix_characters, time_format, get_button_style, music_source_image
from utils.music.models import LavalinkPlayer
from utils.others import ProgressBar, PlayerControls


class DefaultStaticSkin:

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

        good_p, norm_ping, weak_p = range(1, 100), range(101, 200), range(201, 100000)

    
            
        duration1 = "> 🔴 **Thời lượng:** `Livestream`\n" if player.current.is_stream else \
            (f"> <:timeout:1155781760571949118> **Thời lượng:** `{time_format(player.current.duration)} [`" +
            f"<t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=player.current.duration - player.position)).timestamp())}:R>`]`\n"
            if not player.paused else '')

        vc_txt = ""
        src_name = fix_characters(player.current.info['sourceName'], limit=16)
        src_emoji = ""
        if src_name == "spotify":
            s_name = "Spotify"
            src_emoji = "<:spo:1197427989630156843>"
        elif src_name == "youtube":
             s_name = "YouTube"
             src_emoji = "<:Youtube:1197428387917082735>"
        elif src_name == "soundcloud":
                s_name = "SoundCloud"
                src_emoji = "<:soundcloud:1197427982499856435>"
        elif src_name == "dezzer":
             s_name = "Dezzer"
             src_emoji = "<:deezer:1197427994533314600>"
        elif src_name == "twitch":
             s_name = "Twitch"
             src_emoji = "<:Twitch:1197427999981703238>"
        else:
             src_emoji = "<:LogoModSystem:1155781711024635934>"

        txt = f"[`{player.current.single_title}`]({player.current.uri})\n\n" \
              f"{duration1}" \
              f"> {src_emoji} **⠂Nguồn:** [`{s_name}`]({player.current.uri})\n" \
              f"> <:author:1140220381320466452>  **⠂Tác giả:** {player.current.authors_md}\n" \
              f"> <:volume:1140221293950668820> **⠂Âm lượng:** `{player.volume}%`\n" \
              f"> <:host:1140221179920138330> **⠂Máy chủ:** {player}\n" \
              f"> 🌐 **⠂Vùng:** {player.node.region.title()}" \
              
        if not player.ping:
            txt += f"\n> <a:loading:1204300257874288681> **⠂Đang lấy dữ liệu từ máy chủ**"
        else:
            if player.ping in good_p:
                txt += f"\n> <:emoji_57:1173431627607715871> **⠂Độ trễ:** `{player.ping}ms`"
            elif player.ping in norm_ping:
                txt += f"\n> <:emoji_58:1173431708071247983> **⠂Độ trễ:** `{player.ping}ms`"
            elif player.ping in weak_p:
                txt += f"\n> <:emoji_59:1173431772017590332> **⠂Độ trễ:** `{player.ping}ms`"

        if not player.current.autoplay:
                    txt += f"\n> ✋ **⠂Được yêu cầu bởi:** <@{player.current.requester}>"
        else:
                    try:
                        mode = f" [`Chế độ tự động`]({player.current.info['extra']['related']['uri']})"
                    except:
                        mode = "`Chế độ tự động`"
                    txt += f"\n> 👍 **⠂Được yêu cầu bởi:** {mode}"


        try:
            vc_txt += f"\n> <:AyakaCozy_mella:1135418504590393415> **⠂Người dùng đang kết nối:** `{len(player.guild.me.voice.channel.members) - 1}`"
        except AttributeError:
            pass

        try:
            vc_txt += f"\n> 🔊 **⠂Kênh** {player.guild.me.voice.channel.mention}"
        except AttributeError:
            pass
        
        if player.current.track_loops:
            txt += f"\n> <:loop:1140220877401772092> **⠂Lặp lại còn lại:** `{player.current.track_loops}`\n " \


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
            txt += f"\n> <:musicalbum:1183394320292790332> **⠂Bài hát đang chờ:** `{qlenght}`"

        if player.keep_connected:
            txt += f"\n> <:247:1140230869643169863> **⠂Chế độ 24/7:** `Kích hoạt`"

        if player.restrict_mode:
            txt += f"\n> <:restrictions:1183393857858191451> **⠂Hạn chế:** `Kích hoạt`"

        txt += f"{vc_txt}\n"

        if player.command_log:
            txt += f"> {player.command_log_emoji}``Tương tác cuối cùng``{player.command_log_emoji}\n"
            txt += f"> {player.command_log}\n"

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
                    embed_queue.description += f"\n`[⌛ Các bài hát sẽ kết thúc sau` <t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=(queue_duration + (player.current.duration if not player.current.is_stream else 0)) - player.position)).timestamp())}:R> `⌛]`"

            embed_queue.set_image(url="https://i.ibb.co/wKwpJZQ/ayakapfp-Banner2.gif")

        embed.description = txt
        embed.set_image(url=player.current.thumb if player.is_paused == False else "https://i.ibb.co/wKwpJZQ/ayakapfp-Banner2.gif")
        embed.set_thumbnail(url=player.current.thumb)
        embed.set_footer(
            text=f"Chisadin music system || {time_format(player.position)} / {time_format(player.current.duration)}" if not player.paused else f"Chisadin music system || Tạm dừng",
            icon_url="https://i.ibb.co/YtHsQWH/1125034330088034334.webp",
        )

        data["embeds"] = [embed_queue, embed] if embed_queue else [embed]

        data["components"] = [
            disnake.ui.Button(emoji="<:ayaka_tea:1122325362702037022> ", custom_id=PlayerControls.stop, style=disnake.ButtonStyle.red),
            disnake.ui.Button(emoji="⏮️", custom_id=PlayerControls.back, style=disnake.ButtonStyle.green),
            disnake.ui.Button(emoji="⏯️", custom_id=PlayerControls.pause_resume, style=get_button_style(player.paused)),
            disnake.ui.Button(emoji="⏭️", custom_id=PlayerControls.skip, style=disnake.ButtonStyle.green),
            disnake.ui.Button(emoji="<:pnv_cong1:1167732512336920606>", custom_id=PlayerControls.add_song, style=disnake.ButtonStyle.green, label="Thêm nhạc"),
            disnake.ui.Select(
                placeholder="Lựa chọn khác:",
                custom_id="musicplayer_dropdown_inter",
                min_values=0, max_values=1,
                options=[
                    disnake.SelectOption(
                        label="Thêm bài hát", emoji="<:add_music:588172015760965654>",
                        value=PlayerControls.add_song,
                        description="Thêm bài hát vào hàng đợi."
                    ),
                    disnake.SelectOption(
                        label="Thêm bài hát từ yêu thích", emoji="⭐",
                        value=PlayerControls.enqueue_fav,
                        description="Thêm bài hát từ yêu thích đã lưu trước đó"
                    ),
                    disnake.SelectOption(
                        label="Chơi lại từ đầu", emoji="⏪",
                        value=PlayerControls.seek_to_start,
                        description="Chơi lại từ đầu."
                    ),
                    disnake.SelectOption(
                        label=f"Volume: {player.volume}%", emoji="🔊",
                        value=PlayerControls.volume,
                        description="Điều chỉnh âm lượng."
                    ),
                    disnake.SelectOption(
                        label="Trộn bài", emoji="🔀",
                        value=PlayerControls.shuffle,
                        description="Trộn các bài hát trong hàng đợi."
                    ),
                    disnake.SelectOption(
                        label="Thêm lại các bài hát", emoji="🎶",
                        value=PlayerControls.readd,
                        description="Đưa các bài hát đã phát quay lại hàng đợi."
                    ),
                    disnake.SelectOption(
                        label="Chọn chế độ lặp lại", emoji="🔁",
                        value=PlayerControls.loop_mode,
                        description="Kích hoạt / Vô hiệu hóa chế độ lặp lại."
                    ),
                    disnake.SelectOption(
                        label=("Vô hiệu hóa" if player.nightcore else "Kích hoạt") + " chế độ Nightcore", emoji="🇳",
                        value=PlayerControls.nightcore,
                        description="Hiệu quả làm tăng tốc độ và giai điệu của âm nhạc."
                    ),
                    disnake.SelectOption(
                        label=("Vô hiệu hóa" if player.autoplay else "Kích hoạt") + " Chế độ autopilot", emoji="🔄",
                        value=PlayerControls.autoplay,
                        description="Hệ thống tự động thêm nhạc vào hàng đợi khi hết bài hát."
                    ),
                    disnake.SelectOption(
                        label=("Vô hiệu hóa" if player.restrict_mode else "Kích hoạt") + " chế độ khóa", emoji="🔐",
                        value=PlayerControls.restrict_mode,
                        description="Chế độ giúp bạn không bị người khác thêm nhạc vào hàng đợi (Chỉ người gọi bài hoặc Staff)."
                    ),
                    disnake.SelectOption(
                        label=("Vô hiệu hóa" if player.keep_connected else "Kích hoạt") + " chế độ 24/7", emoji="<:247:1140230869643169863>",
                        value=PlayerControls.keep_connected,
                        description="Kích hoạt chế độ 24/7."
                    ),
                ]
            ),
        ]

        if not player.static and not player.has_thread:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Chủ đề yêu cầu bài hát", emoji="💬",
                    value=PlayerControls.song_request_thread,
                    description="Tạo một cuộc trò chuyện chủ đề/tạm thời để đặt hàng nhạc chỉ bằng tên/liên kết."
                )
            )

        try:
            if isinstance(player.text_channel.parent, disnake.ForumChannel):
                data["content"] = f"`{emoji} {fix_characters(player.current.title, 50)}`"
        except:
            pass

        return data

def load():
    return DefaultStaticSkin()
