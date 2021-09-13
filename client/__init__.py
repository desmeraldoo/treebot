# -*- coding: utf-8 -*-

# STANDARD LIB
import logging
import requests

# EXTERNAL LIB
import discord
import emoji

# LOCAL LIB
from ._const import *
from ._prompt import InteractivePrompt

class TreeClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.voice_client = None
        self.prompt = InteractivePrompt(self).prompt

    def assemble_channel_dict(self):
        self.channel_dict = {}
        for channel in self.get_all_channels():
            if type(channel) in [discord.channel.TextChannel, discord.channel.VoiceChannel]:
                self.channel_dict[channel.name] = channel.id

    def assemble_emoji_dict(self):
        self.emoji_dict = {}
        for emoji in self.emojis:
            key = f':{emoji.name}:'
            if emoji.animated:
                value = f'<a:{emoji.name}:{emoji.id}>'
            else:
                value = f'<:{emoji.name}:{emoji.id}>'
            self.emoji_dict[key] = value

    def is_link_valid(self, link):
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
            logging.info('Error resolving link!')
            logging.debug('\n', exc_info=True)
            return False

    async def on_ready(self):
        for guild in self.guilds:
            logging.info(f'{self.user} has connected to {guild.name}!')
        
        if not self.initialized:
            # Assemble dictionary server assets
            self.assemble_channel_dict()
            self.assemble_emoji_dict()
            # Init command prompt functionality
            self.loop.create_task(self.prompt())
            
            self.initialized = True
    
    async def on_resumed(self):
        logging.info('Resuming Reg session...')
    
    async def on_message(self, message):
        if message.author == self.user:
            return
