# STANDARD LIB
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
        self.download = DOWNLOAD_BY_DEFAULT
    
    def clear_queue(self):
        self.queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    
    def toggle_download(self):
        self.download = not self.download
    
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
        
        # clean up any audio files from last execution
        for filename in os.listdir('.'):
            if filename.endswith(('.mp3', '.m4a', '.webm')):
                with contextlib.suppress(FileNotFoundError):
                    os.remove(filename)
    
    def get_ffmpeg_options(self, guild):
        options = FFMPEG_BASE_OPTIONS
        if not self.settings_dict[guild].download: options['before_options'] = FFMPEG_STREAM_OPTIONS
        return options
    
    def get_title(self, video):
        if 'entries' in video:
            video = video['entries'][0]
        return video['title']
    
    def get_source(self, video, guild):
        if 'entries' in video:
            video = video['entries'][0]
        if self.settings_dict[guild].download:
            return self.ytdl.prepare_filename(video)
        else:
            return video['formats'][0]['url']
    
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
    
    def can_play(self, guild):
        return self.is_connected(guild) and not guild.voice_client.is_playing()
    
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
    
    async def download(self, query, download):
        search = False if link_valid(query.strip()) else True
        logging.info(f'Searching: {query}' if search else f'Playing: {query}')
        query = f'ytsearch:{query}' if search else query
        return await self.parent.loop.run_in_executor(None,
            lambda s=self, q=query, d=download: s.ytdl.extract_info(q, download=d))
    
    def enqueue(self, guild, video):
        try:
            self.settings_dict[guild].enqueue(video)
        except queue.Full:
            raise
        return True # successfully added to queue
        
    def dequeue(self, error, guild, prev_source):
        if error: logging.error(f'Error during play: {e}', exc_info=True)
        if not link_valid(prev_source):
            with contextlib.suppress(FileNotFoundError):
                os.remove(prev_source) # Clean up files that have finished playing

        if self.can_play(guild):
            try:
                video = self.settings_dict[guild].dequeue()
            except (KeyError, queue.Empty):
                return False
            else:
                self.play(video, guild)
    
    def play(self, video, guild):
        source = self.get_source(video, guild)
        logging.info(f'[{guild}] Playing from source: {source}')
        stream = discord.FFmpegPCMAudio(source, **self.get_ffmpeg_options(guild))
        
        if guild.voice_client.is_paused():
            return self.enqueue(guild, video)
        
        try:
            guild.voice_client.play(stream,
                after=lambda e, g=guild, s=source: self.dequeue(e, g, s))
            logging.info(f'[{guild}] Playing video...')
            return False # not queued
        except discord.errors.ClientException:
            logging.info(f'[{guild}] Queueing video...')
            return self.enqueue(guild, video) # try add to queue
    
    async def command_play(self, ctx, query):
        await ctx.defer()
        if not self.is_connected(ctx.guild):
            logging.info(f'[{ctx.guild}] Establishing connection to voice channel...')
            await self.parent.join(ctx.author.voice.channel)
        
        logging.info(f'[{ctx.guild}] Downloading video...')
        video = await self.download(query, self.settings_dict[ctx.guild].download)
        try:
            queued = self.play(video, ctx.guild)
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
        ctx.guild.voice_client.stop()
        return await ctx.send('✅ Skipped this song.')

    async def reset(self, ctx):
        self.settings_dict[ctx.guild].clear_queue()
        ctx.guild.voice_client.stop()
        return await ctx.send('✅ Stopped playing music. The queue has been cleared.')
    
    async def toggle_download(self, ctx):
        self.settings_dict[ctx.guild].toggle_download()
        if self.settings_dict[ctx.guild].download:
            return await ctx.send('✅ Enabled downloading. This may help with audio quality issues, but especially long files may take a while to play.')
        return await ctx.send('✅ Enabled streaming. This will reduce time to play streams, but there may be audio quality issues depending on the connection quality.')
