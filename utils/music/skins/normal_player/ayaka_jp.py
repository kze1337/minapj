# -*- coding: utf-8 -*-
import datetime
import itertools
from os.path import basename
import disnake

from utils.music.converters import fix_characters, time_format, get_button_style, music_source_image
from utils.music.models import LavalinkPlayer
from utils.others import ProgressBar, PlayerControls


class DefaultProgressbarSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = basename(__file__)[:-3]
        self.preview = "https://cdn.discordapp.com/attachments/554468640942981147/1047184550230495272/skin_progressbar.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = True
        player.controller_mode = True
        player.auto_update = 10
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = False

    def load(self, player: LavalinkPlayer) -> dict:

        data = {
            "content": None,
            "embeds": []
        }
        trans = {
            "spotify": "スポティファイ",
            "youTube": "ユーチューブ",
            "soundcloud": "サウンドクラウド",
            "dezzer": "ディーザー",
            "twitch": "ツイッチ",
            "applemusic": "アップルミュージック",
            "Unknown": "不明"
        }

        embed = disnake.Embed(color=player.bot.get_color(player.guild.me))
        embed_queue = None

        if not player.paused:
            embed.set_author(
                name=f"{trans.get(player.current.info['sourceName'], '不明')} から音楽を再生しています:",
                icon_url=music_source_image(player.current.info["sourceName"])
            )
        else:
            embed.set_author(
                name="一時停止",
                icon_url="https://i.ibb.co/xYj7ysN/pause.png"
            )

     
        duration1 = "> 🔴 **⠂時間:** `Livestream`\n" if player.current.is_stream else \
            (f"> <:timeout:1155781760571949118> **⠂時間:** `{time_format(player.current.duration)} [`" +
            f"<t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=player.current.duration - player.position)).timestamp())}:R>`]`\n"
            if not player.paused else '')

        vc_txt = ""
        src_name = fix_characters(player.current.info['sourceName'], limit=16)
        src_emoji = ""

        match src_name:
            case "spotify":
                s_name = "Spotify"
                src_emoji = "<:spo:1197427989630156843>"
            case "youtube":
                s_name = "YouTube"
                src_emoji = "<:Youtube:1197428387917082735>"
            case "soundcloud":
                s_name = "SoundCloud"
                src_emoji = "<:soundcloud:1197427982499856435>"
            case "dezzer":
                s_name = "Dezzer"
                src_emoji = "<:deezer:1197427994533314600>"
            case "twitch":
                s_name = "Twitch"
                src_emoji = "<:Twitch:1197427999981703238>"
            case "applemusic":
                s_name = "Apple Music"
                src_emoji = "<:applemusic:1232560350449242123>"
            case "http":
                s_name = "HTTP"
                src_emoji = "<:link:1372085354424832000>"
            case _:
                s_name = "分からない"
                src_emoji = "<:LogoModSystem:1155781711024635934>"


        txt = f"[`{player.current.single_title}`]({player.current.uri})\n\n" \
              f"{duration1}" \
              f"> {src_emoji} **⠂音楽ソース:** [`{s_name}`]({player.current.uri})\n" \
              f"> <:author:1140220381320466452> **⠂著者:** {player.current.authors_md}\n" \
              f"> <:volume:1140221293950668820> **⠂音量:** `{player.volume}%`\n" \
              f"> <:host:1140221179920138330> **⠂サーバ:** {player}\n" \
              f"> 🌐 **⠂地域:** {player.node.region.title()}" \
              
        if not player.ping:
            txt += f"\n> <a:loading:1204300257874288681> **⠂サーバーからデータを取得する**"
        else:
            if player.ping in range(0, 100):
                txt += f"\n> <:emoji_57:1173431627607715871> **⠂レイテンシ:** `{player.ping}ms`"
            elif player.ping in range(101, 300):
                txt += f"\n> <:emoji_58:1173431708071247983> **⠂レイテンシ:** `{player.ping}ms`"
            elif player.ping in range(301, 1000):
                txt += f"\n> <:emoji_59:1173431772017590332> **⠂レイテンシ:** `{player.ping}ms`"

        if not player.current.autoplay:
                    txt += f"\n> ✋ **⠂に要求された:** <@{player.current.requester}>"
        else:
                    try:
                        mode = f" [`自動モード`]({player.current.info['extra']['related']['uri']})"
                    except:
                        mode = "`自動モード`"
                    txt += f"\n> 👍 **⠂に要求された:** {mode}"


        try:
            if not player.keep_connected:
                vc_txt += f"\n> <:star3:1155781751914889236> **⠂ユーザーを接続する:** `{len(player.guild.me.voice.channel.members) - 1}`"
            else:
                vc_txt += f"\n> <:star3:1155781751914889236> **⠂ユーザーを接続する:** `24/7 モード`"
        except AttributeError:
            pass

        try:
            vc_txt += f"\n> 🔊 **⠂チャネル:** {player.guild.me.voice.channel.mention}"
        except AttributeError:
            pass
        
        if player.current.track_loops:
            txt += f"\n> <:loop:1140220877401772092> **⠂残りを繰り返します:** `{player.current.track_loops}` " \


        if player.loop:
            if player.loop == 'current':
                e = '<:loop:1140220877401772092>'
                m = '現在の曲'
            else:
                e = '<:loop:1140220877401772092>'
                m = '列'
            txt += f"\n> {e} **⠂リピートモード：** `{m}`"

        if player.nightcore:
            txt += f"\n> <:nightcore:1140227024108130314> **⠂ナイトコアエフェクト:** `アクティブ化された`"

        if player.current.album_name:
            txt += f"\n> <:soundcloud:1140277420033843241> **⠂アルバム:** [`{fix_characters(player.current.album_name, limit=16)}`]({player.current.album_url})"

        if player.current.playlist_name:
            txt += f"\n> <:library:1140220586640019556> **⠂プレイリスト:** [`{fix_characters(player.current.playlist_name, limit=16)}`]({player.current.playlist_url})"

        if (qlenght:=len(player.queue)) and not player.mini_queue_enabled:
            txt += f"\n> <:musicalbum:1183394320292790332> **⠂歌が待っている:** `{qlenght}`"

        if player.keep_connected:
            txt += f"\n> <:247:1140230869643169863> **⠂24/7モード:** `アクティブ化された`"

        if player.restrict_mode:
            txt += f"\n> <:restrictions:1183393857858191451> **⠂限界:** `アクティブ化された`"

        txt += f"{vc_txt}\n"

        if player.command_log:
            txt += f"> {player.command_log_emoji}``最終的なやり取り``{player.command_log_emoji}\n"
            txt += f"> {player.command_log}\n"

        if qlenght and player.mini_queue_enabled:

            queue_txt = "\n".join(
                f"`{(n + 1):02}) [{time_format(t.duration) if not t.is_stream else '🔴 ライブストリーム'}]` [`{fix_characters(t.title, 38)}`]({t.uri})"
                for n, t in (enumerate(itertools.islice(player.queue, 3)))
            )

            embed_queue = disnake.Embed(title=f"待ちの曲：  {qlenght}", color=player.bot.get_color(player.guild.me),
                                        description=f"\n{queue_txt}")

            if not player.loop and not player.keep_connected and not player.paused and not player.current.is_stream:

                queue_duration = 0

                for t in player.queue:
                    if not t.is_stream:
                        queue_duration += t.duration

                if queue_duration:
                    embed_queue.description += f"\n`[⌛ 歌は後で終わります` <t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=(queue_duration + (player.current.duration if not player.current.is_stream else 0)) - player.position)).timestamp())}:R> `⌛]`"

            embed_queue.set_image(url="https://i.ibb.co/wKwpJZQ/ayakapfp-Banner2.gif")

        embed.description = txt
        embed.set_image(url=player.current.thumb if player.is_paused == False else "https://i.ibb.co/wKwpJZQ/ayakapfp-Banner2.gif")
        embed.set_thumbnail(url=player.current.thumb)
        embed.set_footer(
            text=f"Chisadin Music Service || {time_format(player.position)} / {time_format(player.current.duration)}" if not player.current.is_stream else "チサディン音楽システム || 現在ストリーミング中" if not player.paused else "Chisadin 音楽システム || 一時停止",
            icon_url="https://i.ibb.co/YtHsQWH/1125034330088034334.webp",
        )

        data["embeds"] = [embed_queue, embed] if embed_queue else [embed]

        data["components"] = [
            disnake.ui.Button(emoji="<:stop:1140221258575925358>", custom_id=PlayerControls.stop, style=disnake.ButtonStyle.red),
            disnake.ui.Button(emoji="⏮️", custom_id=PlayerControls.back, style=disnake.ButtonStyle.green),
            disnake.ui.Button(emoji="⏯️", custom_id=PlayerControls.pause_resume, style=get_button_style(player.paused)),
            disnake.ui.Button(emoji="⏭️", custom_id=PlayerControls.skip, style=disnake.ButtonStyle.green),
            disnake.ui.Button(emoji="<:addsong:1140220013580664853>", custom_id=PlayerControls.add_song, style=disnake.ButtonStyle.green, label="音楽を追加する", disabled= True if player.paused else False),
            disnake.ui.Select(
                placeholder="別の選択肢:",
                custom_id="musicplayer_dropdown_inter",
                min_values=0, max_values=1,
                options=[
                    disnake.SelectOption(
                        label="曲を追加する", emoji="<:add_music:588172015760965654>",
                        value=PlayerControls.add_song,
                        description="曲/プレイリストをキューに追加します。"
                    ),
                    disnake.SelectOption(
                        label="お気に入りに追加", emoji="💗",
                        value=PlayerControls.add_favorite,
                        description="現在の曲をお気に入りに追加します。"
                    ),
                    disnake.SelectOption(
                        label="記事の先頭まで巻き戻す", emoji="⏪",
                        value=PlayerControls.seek_to_start,
                        description="現在の曲を 00:00 にタイムスキップします。"
                    ),
                    disnake.SelectOption(
                        label=f"音量: {player.volume}%", emoji="🔊",
                        value=PlayerControls.volume,
                        description="音量を調整する"
                    ),
                    disnake.SelectOption(
                        label="キュー内の曲をミックスする", emoji="🔀",
                        value=PlayerControls.shuffle,
                        description="キュー内で音楽をミックスする."
                    ),
                    disnake.SelectOption(
                        label="再生したすべての曲をもう一度再生する", emoji="🎶",
                        value=PlayerControls.readd,
                        description="再生した曲をキューに戻します。"
                    ),
                    disnake.SelectOption(
                        label="リピートモード", emoji="🔁",
                        value=PlayerControls.loop_mode,
                        description="繰り返しの有効化/無効化."
                    ),
                    disnake.SelectOption(
                        label=("無効にする" if player.autoplay else "アクティブ化された") + " 音楽自動追加モード", emoji="🔄",
                        value=PlayerControls.autoplay,
                        description="回線が空の場合、システムは自動的に音楽を追加します。"
                    ),
                    disnake.SelectOption(
                        label=("無効にする" if player.nightcore else "アクティブ化された") + " ナイトコア効果", emoji="<:nightcore:1140227024108130314>",
                        value=PlayerControls.nightcore,
                        description="ナイトコアエフェクト."
                    ),
                    disnake.SelectOption(
                        label=("無効にする" if player.restrict_mode else "アクティブ化された") + " 限定モード", emoji="🔐",
                        value=PlayerControls.restrict_mode,
                        description="Chỉ DJ/Staff mới có thể sử dụng các lệnh bị hạn chế."
                    ),
                    disnake.SelectOption(
                        label="曲リスト", emoji="<:music_queue:703761160679194734>",
                        value=PlayerControls.queue,
                        description="あなただけが見ることができるリストを表示します"
                    ),
                    disnake.SelectOption(
                        label=("オンにする" if not player.keep_connected else "消す") + " モード 24/7", emoji="<:247:1140230869643169863>",
                        value=PlayerControls.keep_connected,
                        description="ノンストップランニングモード 24/7。"
                    ),
                ]
            ),
        ]

        if player.current.ytid and player.node.lyric_support:
                    data["components"][5].options.append(
                        disnake.SelectOption(
                            label="歌詞を見る", emoji="📃",
                            value=PlayerControls.lyrics,
                            description="現在の曲の歌詞を取得します。"
                        )
                    )

        if player.mini_queue_feature:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="ミニプレイリスト", emoji="<:music_queue:703761160679194734>",
                    value=PlayerControls.miniqueue,
                    description="プレーヤーのミニプレイリストを有効/無効にする."
                )
            )

        if not player.static and not player.has_thread:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="トピックリクエスト曲", emoji="💬",
                    value=PlayerControls.song_request_thread,
                    description="トピック/一時チャットを作成し、名前/リンクを指定するだけで音楽を追加します。"
                )
            )

        return data

def load():
    return DefaultProgressbarSkin()
