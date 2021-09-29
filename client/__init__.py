# -*- coding: utf-8 -*-

# STANDARD LIB
import logging
import requests

# EXTERNAL LIB
import discord
import emoji

# LOCAL LIB
from ._const import *
from ._music import MusicModule
from ._prompt import InteractivePrompt

import pdb

class TreeClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.initialized = False
        # TODO: Add way to switch between guilds in interactive prompt
        # self.prompt = InteractivePrompt(self).prompt

    def assemble_channel_dict(self):
        self.channel_dict = dict()
        for channel in self.get_all_channels():
            if type(channel) in [discord.channel.TextChannel, discord.channel.VoiceChannel]:
                self.channel_dict[channel.name] = channel.id

    def assemble_emoji_dict(self):
        self.emoji_dict = dict()
        for emoji in self.emojis:
            key = f':{emoji.name}:'
            if emoji.animated:
                value = f'<a:{emoji.name}:{emoji.id}>'
            else:
                value = f'<:{emoji.name}:{emoji.id}>'
            self.emoji_dict[key] = value
    
    def is_connected(self, guild):
        return (
            hasattr(guild, 'voice_client') and
            guild.voice_client != None and
            guild.voice_client.is_connected()
        )
    
    async def join(self, channel):
        # Join a voice channel or leave it if already joined.
        if hasattr(self, 'voice_client') and channel.guild.voice_client.is_connected():
            current_channel = channel.guild.voice_client.channel
            if current_channel != channel:
                await channel.guild.voice_client.move_to(channel)
                logging.info(f'[{channel.guild}] \nSuccessfully switched from \'{current_channel}\' to \'{channel}\'.')
                return True
            else:
                logging.warning(f'[{channel.guild}] Tried to re-join the same channel!')
                return False
        else:
            try:
                await channel.connect()
            except discord.errors.ClientException:
                logging.warning(f'[{channel.guild}] Already connected to \'{channel}\'!')
            else:
                logging.info(f'Successfully connected to \'{channel}\'.')
            return True
    
    async def on_voice_state_update(self, member, before, after):
        if self.is_connected(member.guild) and len(member.guild.voice_client.channel.members) == 1:
            await member.guild.voice_client.disconnect()

    async def on_ready(self):
        for guild in self.guilds:
            logging.info(f'[{guild}] {self.user} has connected to {guild}!')
        
        if not self.initialized:
            # Assemble dictionary server assets
            self.assemble_channel_dict()
            self.assemble_emoji_dict()
            # Init command prompt (not currently active)
            # self.loop.create_task(self.prompt())
            
            # Init music here so the bot can build a settings dict for each guild
            self.music = MusicModule(self)
            
            self.initialized = True
    
    async def on_resumed(self):
        logging.info('Resuming Reg session...')
    
    async def on_message(self, message):
        if message.author == self.user or message.author.bot:
            return
