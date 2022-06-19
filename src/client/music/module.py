import contextlib
import logging
import os
import queue
from dataclasses import dataclass
from typing import Any

import aiohttp
import discord
import nextcord
import yt_dlp

from src.settings import (DEFAULT_VOLUME, DOWNLOAD_BY_DEFAULT,
                          FFMPEG_STREAM_OPTIONS, QUEUE_MAXSIZE, YTDL_OPTIONS)

logger = logging.getLogger()


async def link_valid(link, session: aiohttp.ClientSession) -> bool:
    try:
        response = await session.head(link, allow_redirects=True)
        if response.status > 199 or response.status < 400:
            logging.debug(f"Link resolved successfully [Code {response.status}]")
            return True
        else:
            logging.debug(f"Link received error [Code {response.status}]")
            return False
    except Exception:
        logging.debug(f"Error resolving link: {link}\n", exc_info=True)
        return False


@dataclass
class MusicModule:
    current: dict[str, Any] | None = None
    downloading: bool = DOWNLOAD_BY_DEFAULT
    ffmpeg: str | None = os.getenv("FFMPEG_EXEC_LOC")
    video_queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    looping: bool = False
    skip_next: bool = False
    voice: nextcord.VoiceClient | None = None
    volume: int = DEFAULT_VOLUME
    ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __post_init__(self) -> None:
        if not os.path.exists(self.ffmpeg):
            logger.warning(
                "FFMPEG executable not found! Streaming and downloading music is impossible."
            )
            self.ffmpeg = None

        self.cleanup()

    def cleanup(self) -> None:
        # clean up any audio files from last execution
        for filename in os.listdir("."):
            if filename.endswith((".mp3", ".m4a", ".webm", ".part")):
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.remove(filename)

    async def join(self, channel: nextcord.VoiceChannel) -> bool:
        if self.voice.is_connected():
            prev_channel = self.voice.channel
            if prev_channel != channel:
                await self.voice.move_to(channel)
                logger.info(
                    f"[{channel.guild}] \nSuccessfully switched from '{prev_channel}' to '{channel}'."
                )
                return True
            else:
                logger.warning(f"[{channel.guild}] Tried to re-join the same channel!")
                return False
        else:
            try:
                self.voice = await channel.connect()
            except nextcord.errors.ClientException:
                logger.warning(f"[{channel.guild}] Already connected to '{channel}'!")
            else:
                logger.info(f"Successfully connected to '{channel}'.")
            return True

    def get_title(self, video: dict[str, Any]) -> str:
        if "entries" in video:
            video = video["entries"][0]
        return video["title"]

    def get_source(self, video: dict[str, Any], download: bool) -> str:
        if "entries" in video:
            video = video["entries"][0]
        if download:
            return self.ytdl.prepare_filename(video)
        else:
            return video["formats"][0]["url"]

    @property
    def current(self) -> dict[str, Any]:
        return self.current

    @property.setter
    def current(self, video: dict[str, Any]) -> None:
        self.current = video

    def can_dequeue(self):
        return self.voice.is_connected() and not self.voice.is_playing()

    def get_queue_as_list(self) -> list:
        return list(self.video_queue.queue)

    def clear_queue(self) -> None:
        self.video_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)

    def dequeue(self) -> Any:
        return self.video_queue.get_nowait()

    def enqueue(self, video) -> None:
        return self.video_queue.put_nowait(video)

    def toggle_download(self) -> None:
        self.downloading = not self.downloading

    def toggle_looping(self) -> None:
        self.looping = not self.looping

    async def download(self, query, downloading) -> Any:
        search = False if link_valid(query.strip()) else True
        logging.info(f"Searching: {query}" if search else f"Playing: {query}")
        query = f"ytsearch:{query}" if search else query
        try:
            return await self.parent.loop.run_in_executor(
                None,
                lambda q=query, d=downloading: self.ytdl.extract_info(
                    url=q, download=d
                ),
            )
        except yt_dlp.utils.DownloadError as exc:
            raise RuntimeError("MusicModule failed to extract video info!") from exc

    def enqueue(self, guild, video):
        try:
            self.state[guild].enqueue(video)
        except queue.Full:
            raise
        return True  # successfully added to queue

    def dequeue(self, error, guild, prev_video):
        if error:
            logging.error(f"Error during play: {error}", exc_info=True)

        # if we can't dequeue, we are either not connected or already playing something else
        if self.can_dequeue(guild):
            if self.state[guild].looping and not self.state[guild].skip_next:
                self.play(prev_video, guild)
            else:
                if self.state[guild].skip_next:
                    self.state[guild].skip_next = False
                try:
                    video = self.state[guild].dequeue()
                except queue.Empty:
                    return False
                else:
                    prev_source = self.get_source(
                        prev_video, self.state[guild].downloading
                    )
                    if not link_valid(prev_source):
                        with contextlib.suppress(FileNotFoundError):
                            os.remove(
                                prev_source
                            )  # Clean up files that have finished playing
                    self.play(video, guild)

    def play(self, video, guild):
        source = self.get_source(video, self.state[guild].downloading)
        logging.debug(f"[{guild}] Playing from source: {source}")

        if guild.voice_client.is_paused():
            return self.enqueue(guild, video)

        logging.info(f"[{guild}] Playing {self.get_title(video)}...")
        options = FFMPEG_STREAM_OPTIONS if not self.state[guild].downloading else None
        try:
            stream = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    source, executable=self.ffmpeg, before_options=options
                ),
                self.state[guild].volume * 0.01,
            )
            guild.voice_client.play(
                stream, after=lambda e, g=guild, v=video: self.dequeue(e, g, v)
            )
            self.state[guild].set_current(video)
            return False  # not queued
        except discord.errors.ClientException:
            logging.info(f"[{guild}] Queueing {self.get_title(video)}...")
            return self.enqueue(guild, video)  # try add to queue

    async def command_play(self, ctx, query):
        await ctx.defer()
        if not self.is_connected(ctx.guild):
            logging.info(f"[{ctx.guild}] Establishing connection to voice channel...")
            await self.parent.join(ctx.author.voice.channel)

        logging.info(f"[{ctx.guild}] Downloading video...")
        try:
            video = await self.download(query, self.state[ctx.guild].downloading)
        except RuntimeError:
            return await ctx.send("❌ Sorry, the video failed to download.")

        try:
            queued = self.play(video, ctx.guild)
        except queue.Full:
            num = self.state[ctx.guild].queue_size()
            logging.warning(
                f"User hit queue size cap: (max: {QUEUE_MAXSIZE}, current: {num})"
            )
            return await ctx.send(f"The queue is full ({num}/{QUEUE_MAXSIZE}).")
        else:
            title = self.get_title(video)
            if queued:
                logging.info(f"[{ctx.guild}] ...successfully added to queue: {title}")
                return await ctx.send(f"**✅ Added to queue:** {title}")
            logging.info(f"[{ctx.guild}] ...successfully playing: {title}")
            return await ctx.send(f"✅ **Now playing:** {title}")

    async def pause(self, ctx):
        ctx.guild.voice_client.pause()
        return await ctx.send("✅ Paused the current song.")

    async def resume(self, ctx):
        ctx.guild.voice_client.resume()
        return await ctx.send("✅ Resumed the current song.")

    async def skip(self, ctx):
        self.state[ctx.guild].skip_next = True
        ctx.guild.voice_client.stop()
        return await ctx.send("✅ Skipped this song.")

    async def reset(self, guild, ctx=None):
        self.state[guild].skip_next = True
        self.state[guild].clear_queue()
        guild.voice_client.stop()
        self.cleanup()
        if ctx:
            return await ctx.send(
                "✅ Stopped playing music. The queue has been cleared."
            )

    async def view(self, ctx):
        current = self.state[ctx.guild].get_current()
        lst = self.state[ctx.guild].get_queue_as_list()
        if len(lst) == 0 and not current:
            return await ctx.send(
                "✅ No music is playing right now, and the queue is empty."
            )
        else:
            embed = discord.Embed(title="View")
            embed.add_field(name="Currently playing 🎶", value=self.get_title(current))
            if len(lst) > 0:
                embed.add_field(
                    name="Coming up ⬇️",
                    value="\n".join(
                        [
                            f"**{idx + 1}:** {self.get_title(video)}"
                            for idx, video in enumerate(lst)
                        ]
                    ),
                )
            return await ctx.send(embed=embed)

    async def toggle_looping(self, ctx):
        self.state[ctx.guild].toggle_looping()
        if self.state[ctx.guild].looping:
            return await ctx.send(
                "✅ Enabled looping. The queue will not advance while looping is enabled."
            )
        return await ctx.send("✅ Disabled looping. The queue can now advance.")

    async def toggle_download(self, ctx):
        self.state[ctx.guild].toggle_download()
        if self.state[ctx.guild].downloading:
            return await ctx.send(
                "✅ Enabled downloading. This may help with audio quality issues, but especially long files may take a while to play."
            )
        return await ctx.send(
            "✅ Enabled streaming. This will reduce time to play streams, but there may be audio quality issues depending on the connection quality."
        )

    async def set_volume(self, ctx, new_volume):
        # Integer checking is done at the slash command level, so we don't need to do it here
        if self.state[ctx.guild].volume == new_volume:
            return await ctx.send(
                f"❌ The volume is already {new_volume}%. No settings were changed."
            )
        elif new_volume <= 0 or new_volume > 200:
            return await ctx.send(
                f"❌ The proposed volume ({new_volume}%) is invalid. Please choose a volume greater than 0 and less than or equal to 200."
            )
        else:
            old_volume = self.state[ctx.guild].volume
            self.state[ctx.guild].volume = new_volume
            return await ctx.send(
                f"✅ Changed volume from {old_volume}% to {new_volume}%. This change will take effect when the next song is played."
            )
