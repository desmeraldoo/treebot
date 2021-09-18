# STANDARD LIB
import asyncio
import contextlib
import logging
import os
import queue

# EXTERNAL LIB
import discord
import requests
import youtube_dl

# LOCAL LIB
from ._const import *

import pdb

def async_lambda(func): return func.__anext__()

def link_valid(link):
    try:
        request = requests.head(link)
        code = request.status_code
        if (code > 199 or code < 400):
            logging.debug(f'Link resolved successfully [Code {code}]')
            return True
        else:
            logging.debug(f'Link received error [Code {code}]')
            return False
    except Exception:
        logging.debug(f'Error resolving link: {link}\n', exc_info=True)
        return False

class MusicSettings():
    def __init__(self):
        self.queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self.downloading = DOWNLOAD_BY_DEFAULT
        self.looping = False
        self.skip_next = False
    
    def clear_queue(self):
        self.queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    
    def toggle_download(self):
        self.downloading = not self.downloading
    
    def toggle_looping(self):
        self.looping = not self.looping
    
    def dequeue(self):
        return self.queue.get_nowait()
    
    def enqueue(self, item):
        return self.queue.put_nowait(item)
    
    def queue_size(self):
        return self.queue.qsize()

class MusicModule():
    def __init__(self, parent):
        self.parent = parent
        self.ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
        self.settings_dict = {guild: MusicSettings() for guild in self.parent.guilds}
        
        self.cleanup()
    
    def cleanup(self):
        # clean up any audio files from last execution
        for filename in os.listdir('.'):
            if filename.endswith(('.mp3', '.m4a', '.webm', '.part')):
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.remove(filename)
    
    def is_connected(self, guild):
        return (
            hasattr(guild, 'voice_client') and
            guild.voice_client != None and
            guild.voice_client.is_connected()
        )
    
    def is_playing(self, guild):
        return self.is_connected(guild) and guild.voice_client.is_playing()
    
    def is_paused(self, guild):
        return self.is_connected(guild) and guild.voice_client.is_paused()
    
    def can_dequeue(self, guild):
        return self.is_connected(guild) and not guild.voice_client.is_playing()
    
    def get_title(self, video):
        if 'entries' in video:
            video = video['entries'][0]
        return video['title']
    
    def get_source(self, video, guild):
        if 'entries' in video:
            video = video['entries'][0]
        if self.settings_dict[guild].downloading:
            return self.ytdl.prepare_filename(video)
        else:
            return video['formats'][0]['url']
    
    async def reqs(self, ctx, lamb, **kwargs):
        if REQUIRE_USER_IN_CALL in kwargs:
            if not ctx.author.voice:
                return await ctx.send('❌ You must be connected to a voice channel to use this command.')
        if REQUIRE_BOT_IN_CALL in kwargs:
            if not self.is_connected(ctx.guild):
                return await ctx.send('❌ I must be connected to a voice channel for this command to be valid.')
        if REQUIRE_BOT_PLAYING in kwargs:
            if not self.is_playing(ctx.guild):
                return await ctx.send('❌ I must be playing audio for this command to be valid.')
        if REQUIRE_BOT_PAUSED in kwargs:
            if not self.is_paused(ctx.guild):
                return await ctx.send('❌ I must be paused for this command to be valid.')
        if REQUIRE_BOT_QUEUE in kwargs:
            if not self.settings_dict[ctx.guild].queue_size() > 0:
                return await ctx.send('❌ There must be items in the queue for this command to be valid.')
        return await lamb()
    
    async def download(self, query, downloading):
        search = False if link_valid(query.strip()) else True
        logging.info(f'Searching: {query}' if search else f'Playing: {query}')
        query = f'ytsearch:{query}' if search else query
        try:
            return await self.parent.loop.run_in_executor(None,
                lambda s=self, q=query, d=downloading: s.ytdl.extract_info(q, download=d))
        except youtube_dl.utils.DownloadError:
            return False
    
    def enqueue(self, guild, video):
        try:
            self.settings_dict[guild].enqueue(video)
        except queue.Full:
            raise
        logging.info(f'[{guild}] Queueing {self.get_title(video)}...')
        return True # successfully added to queue
        
    def dequeue(self, error, guild, prev_video):
        if error: logging.error(f'Error during play: {e}', exc_info=True)

        # if we can't dequeue, we are either not connected or already playing something else
        if self.can_dequeue(guild):
            if self.settings_dict[guild].looping and not self.settings_dict[guild].skip_next:
                self.play(prev_video, guild)
            else:
                if self.settings_dict[guild].skip_next: self.settings_dict[guild].skip_next = False
                try:
                    video = self.settings_dict[guild].dequeue()
                except queue.Empty:
                    return False
                else:
                    prev_source = self.get_source(prev_video, guild)
                    if not link_valid(prev_source):
                        with contextlib.suppress(FileNotFoundError):
                            os.remove(prev_source) # Clean up files that have finished playing
                    self.play(video, guild)
    
    def play(self, video, guild):      
        if guild.voice_client.is_paused():
            return self.enqueue(guild, video)
        
        source = self.get_source(video, guild)
        try:
            stream = discord.FFmpegPCMAudio(
                source,
                executable=os.getenv('FFMPEG_EXEC_LOC'),
                before_options=FFMPEG_STREAM_OPTIONS if not self.settings_dict[guild].downloading else None
            )
            guild.voice_client.play(stream,
                after=lambda e, g=guild, v=video: self.dequeue(e, g, v))
        except (TypeError, PermissionError):
            raise
        except discord.errors.ClientException: # Watch out! If the bot queues for no reason, it may be due to a silent ClientException unrelated to expected behavior.
            return self.enqueue(guild, video) # try add to queue
        else:
            logging.info(f'[{guild}] Playing {self.get_title(video)}')
            return False # not queued

    
    async def command_play(self, ctx, query):
        await ctx.defer()
        if not self.is_connected(ctx.guild):
            logging.info(f'[{ctx.guild}] Establishing connection to voice channel...')
            await self.parent.join(ctx.author.voice.channel)
        
        logging.info(f'[{ctx.guild}] Downloading video...')
        video = await self.download(query, self.settings_dict[ctx.guild].downloading)
        if not video:
            return await ctx.send('❌ Sorry, the video failed to download.')
        
        try:
            queued = self.play(video, ctx.guild)
        except (TypeError, PermissionError):
            return await ctx.send('❌❌ Whoops, this is embarrassing. Looks like the machine I\'m running on may not be properly set up. Please contact the developer!')
        except queue.Full:
            num = self.settings_dict[ctx.guild].queue_size()
            logging.warning(f'User hit queue size cap: (max: {QUEUE_MAXSIZE}, current: {num})')
            return await ctx.send(f'The queue is full ({num}/{QUEUE_MAXSIZE}).')
        else:
            title = self.get_title(video)
            if queued:
                logging.info(f'[{ctx.guild}] ...successfully added to queue: {title}')
                return await ctx.send(f'**✅ Added to queue:** {title}')
            logging.info(f'[{ctx.guild}] ...successfully playing: {title}')
            return await ctx.send(f'✅ **Now playing:** {title}')
            
    async def pause(self, ctx):
        ctx.guild.voice_client.pause()
        return await ctx.send('✅ Paused the current song.')
    
    async def resume(self, ctx):
        ctx.guild.voice_client.resume()
        return await ctx.send('✅ Resumed the current song.')
    
    async def skip(self, ctx):
        self.settings_dict[ctx.guild].skip_next = True
        ctx.guild.voice_client.stop()
        return await ctx.send('✅ Skipped this song.')

    async def reset(self, ctx):
        self.settings_dict[ctx.guild].skip_next = True
        self.settings_dict[ctx.guild].clear_queue()
        ctx.guild.voice_client.stop()
        self.cleanup()
        return await ctx.send('✅ Stopped playing music. The queue has been cleared.')
    
    async def toggle_looping(self, ctx):
        self.settings_dict[ctx.guild].toggle_looping()
        if self.settings_dict[ctx.guild].looping:
            return await ctx.send('✅ Enabled looping. The queue will not advance while looping is enabled.')
        return await ctx.send('✅ Disabled looping. The queue can now advance.')
    
    async def toggle_download(self, ctx):
        self.settings_dict[ctx.guild].toggle_download()
        if self.settings_dict[ctx.guild].downloading:
            return await ctx.send('✅ Enabled downloading. This may help with audio quality issues, but especially long files may take a while to play.')
        return await ctx.send('✅ Enabled streaming. This will reduce time to play streams, but there may be audio quality issues depending on the connection quality.')
