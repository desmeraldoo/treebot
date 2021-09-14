# STANDARD LIB
import logging

# EXTERNAL LIB
import discord
import requests
import youtube_dl

# LOCAL LIB
from ._const import *

import pdb

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
        logging.info(f'Error resolving link: {link}')
        logging.debug('\n', exc_info=True)
        return False

class MusicModule():
    def __init__(self, parent):
        self.parent = parent
        self.ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
        
    def search(self, query):
        info = None
        if link_valid(query.strip()):
            info = self.ytdl.extract_info(query, download=False)
        else:
            info = self.ytdl.extract_info(f'ytsearch:{query}', download=False)['entries'][0]
        return info['title'], info['formats'][0]['url']
    
    async def play(self, ctx, query):
        if not self.parent.is_connected(ctx.author.guild):
            if not ctx.author.voice:
                await ctx.send('You must be in a voice channel to use this command.')
                return
            await self.parent.join(ctx.author.voice.channel)
        
        await ctx.defer()
        title, source = self.search(query)
        stream = discord.FFmpegPCMAudio(source, **FFMPEG_OPTIONS)
        # filename = await Download.from_url(url, loop=self.parent.loop)
        
        try:
            ctx.author.guild.voice_client.play(stream, after=lambda e: logging.info(f'Finished playing {e}'))
            await ctx.send(f'**Now playing:** {title}')
        except discord.errors.ClientException:
            # TODO: Add queue
            await ctx.send('Music is already playing. A queue will be implemented soon!')

    async def stop(self, ctx):
        if not self.parent.is_connected(ctx.author.guild):
            await ctx.send('I\'m not connected to any voice channels!')
        else:
            await self.parent.close_connection(ctx.author.guild)
            await ctx.send('Successfully disconnected.')

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