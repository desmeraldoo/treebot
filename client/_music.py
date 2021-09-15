# STANDARD LIB
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
            logging.info(f'Link resolved successfully [Code {code}]')
            return True
        else:
            logging.info(f'Link received error [Code {code}]')
            return False
    except Exception:
        logging.debug(f'Error resolving link: {link}\n', exc_info=True)
        return False

class MusicModule():
    def __init__(self, parent):
        self.parent = parent
        self.ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
        self.download_dict = dict()
        self.pause_dict = dict()
        self.queue_dict = dict()
    
    def do_download(self, guild):
        return self.download_dict[guild] if guild in self.download_dict else DOWNLOAD_BY_DEFAULT
    
    def get_ffmpeg_options(self, guild):
        options = FFMPEG_BASE_OPTIONS
        if not self.do_download(guild): options['before_options'] = FFMPEG_STREAM_OPTIONS
        return options
    
    def get_source(self, video, guild):
        if 'entries' in video:
            video = video['entries'][0]
        if self.do_download(guild):
            return self.ytdl.prepare_filename(video)
        else:
            return video['formats'][0]['url']
    
    async def reqs(self, ctx, lamb, **kwargs):
        if REQUIRE_USER_IN_CALL in kwargs:
            if not ctx.author.voice:
                await ctx.send('You must be in a voice channel to use this command.')
                return
        if REQUIRE_BOT_IN_CALL in kwargs:
            if not self.parent.is_connected(ctx.author.guild):
                await ctx.send('I\'m not connected to any voice channels!')
                return
        return await lamb()
    
    async def download(self, query, download):
        search = False if link_valid(query.strip()) else True
        query = f'ytsearch:{query}' if search else query
        return await self.parent.loop.run_in_executor(None,
            lambda s=self, q=query, d=download: s.ytdl.extract_info(q, download=d))
        
    def dequeue(self, error, guild, prev_source):
        if error: logging.error(f'Error during play: {e}', exc_info=True)
        if not link_valid(prev_source):
            os.remove(prev_source) # Clean up files that have finished playing

        if guild.voice_client.is_connected() and not guild.voice_client.is_playing():
            try:
                video = self.queue_dict[guild].get_nowait()
            except (KeyError, queue.Empty):
                return False
            else:
                self.play(video, guild)
    
    def play(self, video, guild):
        source = self.get_source(video, guild)
        logging.info(f'Playing from source: {source}')
        stream = discord.FFmpegPCMAudio(source, **self.get_ffmpeg_options(guild))
        try:
            guild.voice_client.play(stream,
                after=lambda e, g=guild, s=source: self.dequeue(e, g, s))
            return True
        except discord.errors.ClientException:
            if guild not in self.queue_dict:
                self.queue_dict[guild] = queue.Queue(maxsize=QUEUE_MAXSIZE)
            try:
                self.queue_dict[guild].put_nowait(video)
            except queue.Full:
                raise
            else:
                return False
    
    async def command_play(self, ctx, query):
        await ctx.defer()
        if not self.parent.is_connected(ctx.author.guild):
            if ctx.author.guild in self.queue_dict:
                self.queue_dict[ctx.author.guild] = queue.Queue(maxsize=QUEUE_MAXSIZE)
            await self.parent.join(ctx.author.voice.channel)
        
        if not query:
            await self.resume(ctx)
            return
        
        video = await self.download(query, self.do_download(ctx.author.guild))
        try:
            status = self.play(video, ctx.author.guild)
        except queue.Full:
            await ctx.send(f'The queue is full (max: {QUEUE_MAXSIZE}, current: {self.queue_dict[ctx.author.guild].qsize()}).')
        else:
            title = video['title']
            if status:
                await ctx.send(f'**Now playing:** {title}')
            else:
                await ctx.send(f'{title} has been added to the queue.')

    async def pause(self, ctx):
        self.parent.calls[ctx.author.guild].pause()
        await ctx.send('Paused the current song.')
    
    async def resume(self, ctx):
        self.parent.calls[ctx.author.guild].resume()
        await ctx.send('Resumed the current song.')

    async def reset(self, ctx):
        self.queue_dict[ctx.author.guild] = queue.Queue(maxsize=QUEUE_MAXSIZE)
        if self.parent.is_connected(ctx.author.guild):
            self.parent.calls[ctx.author.guild].stop()
        await ctx.send('Queue cleared.')
    
    async def toggle_download(self, ctx):
        if ctx.author.guild not in self.download_dict:
            self.download_dict[ctx.author.guild] = True
        else:
            self.download_dict[ctx.author.guild] = not self.download_dict[ctx.author.guild]
        if self.download_dict[ctx.author.guild]:
            await ctx.send('Enabled downloading. This may help with audio quality issues, but especially long files may take a while to play.')
        else:
            await ctx.send('Enabled streaming. This will reduce time to play streams, but there may be audio quality issues depending on the quality of my connection.')

class Download(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename