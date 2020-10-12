# -*- coding: utf-8 -*-

# STANDARD LIB
import asyncio
import datetime
import logging
import pdb
import os
import re
import requests
import sys
import traceback

# EXTERNAL LIB
import aioconsole
import discord
import dotenv
import emoji

# LOCAL LIB
from const import *

class RegClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.voice_client = None

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
            if (code > 199 or code < 400) and code != 301:
                logging.info(f'Link resolved successfully [Code {code}]')
                return True
            else:
                logging.info(f'Link received error [Code {code}]')
                return False
        except Exception:
            logging.info('Error resolving link!')
            logging.debug('\n', exc_info=True)
            return False
    
    def is_message_valid(self, message):
        content = message.content
        if content == '': return True, None # empty messages must be images
        # Find all links in the text.
        links = [''.join(x) for x in re.findall(URL_REGEX, content)]
        logging.debug(f'Links found: {links}')
        # Validate the links. Messages with invalid links are themselves invalid.
        for link in links:
            if link == '': continue
            logging.info(f'Testing link: {link}')
            if not self.is_link_valid(link):
                return False, f'{link} is not a valid link!'
        # Remove all links from the text and tokenize the content to check for emojis.
        content = re.sub(URL_REGEX, '', content)
        content = content.split(' ')
        logging.debug(f'Remaining content after removing URLs: {content}')
        # Remove all tokens that are not Unicode emojis.
        content = [tok for tok in content if tok not in emoji.UNICODE_EMOJI]
        logging.debug(f'Remaining content after removing unicode emojis: {content}')
        # Remove all tokens that are not Discord emojis.
        content = re.sub(EMOJI_REGEX, '', ' '.join(content))
        logging.debug(f'Remaining content after removing Discord emojis: {content}')
        # Remove all whitespace.
        content = re.sub(r'\s+', '', content)
        # If there is anything left, the message is not valid.
        if content != '':
            return False, f'There is non-emoji text content: {content}'
        
        return True, None

    async def on_ready(self):
        for guild in self.guilds:
            logging.info(f'{self.user} has connected to {guild.name}!')
        # Check all the messages from the past day for validity.
        await self.review_recent_messages()
        
        if not self.initialized:
            # Assemble dictionary server assets
            self.assemble_channel_dict()
            self.assemble_emoji_dict()
            # Init messenger functionality
            self.loop.create_task(self.messenger())
            
            self.initialized = True
    
    async def on_resumed(self):
        logging.info('Resuming Reg session...')
        await self.review_recent_messages()
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        logging.debug(f'channel: {message.channel}\nmessage: {message.content}')
        
        # Only run the bot's filter in designated channels.
        if message.channel.id in ENABLED_CHANNELS:
            # If the message isn't valid, delete it.
            valid, reason = self.is_message_valid(message)
            if valid:
                logging.debug('Message is valid')
            else:
                logging.info(
                    'Removed message by {} ({}).\n\t{}\n\tOriginal message: [{}]'.format(
                        message.author.name, message.author.nick, reason, message.content))
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass # Message was already deleted
        else:
            logging.debug('Ignoring message -- not in enabled channel.')
    
    async def on_message_edit(self, before, after):
        await self.on_message(after)

    async def review_recent_messages(self):
        for channel_id in ENABLED_CHANNELS:
            channel = self.get_channel(channel_id)
            yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
            logging.info(f'Reviewing messages in channel {channel_id} after {yesterday}')
            async for message in channel.history(after=yesterday, oldest_first=True):
                await self.on_message(message)

    async def prompt_switch_channel(self):
        while True:
            channel_name = await aioconsole.ainput(
                'Enter the initial channel ([enter] for default): ')
            if not channel_name:
                channel_name = DEFAULT_CHANNEL
                break
            elif channel_name not in self.channel_dict.keys():
                logging.warning(
                    f'Channel name \'{channel_name}\' not recognized; please try again.')
            elif channel_name in self.channel_dict.keys():
                break

        channel_id = self.channel_dict[channel_name]
        channel = self.get_channel(channel_id)
        logging.info(f'Successfully switched to channel \'{channel}\'.')
        return channel

    async def prompt_message(self, channel):
        if not isinstance(channel, discord.channel.TextChannel):
            logging.warning(f'\'{channel}\' is a \'{type(channel)}\' channel, not a text channel.')
            return
    
        while True:
            message = await aioconsole.ainput(
                f'Enter the message to send as Reg in {channel} (empty to quit): ')
            if not message:
                logging.info('Message is empty -- returning to main menu.')
                return
            
            tokens = message.split(' ')
            new_message = []
            for token in tokens:
                if token in self.emoji_dict.keys():
                    new_message.append(self.emoji_dict[token])
                else:
                    new_message.append(token)
            message = ' '.join(new_message)
            logging.info(message)
            
            await channel.send(message)
    
    async def prompt_toggle_join(self, channel):
        # Join a voice channel or leave it if already joined.
        if type(channel) == discord.channel.VoiceChannel:
            if self.voice_client and self.voice_client.is_connected():
                current_channel = self.voice_client.channel
                await self.voice_client.disconnect()
                if current_channel != channel:
                    # Switch channels
                    self.voice_client = await channel.connect()
            else:
                self.voice_client = await channel.connect()
        else:
            logging.warning(f'\{channel}\' is not a voice channel.')

    async def prompt_non_interactive(self):
        confirm = await aioconsole.ainput(
            'Enter [[y]es] if you are sure you want to enter non-interactive mode: ')
        if confirm == 'y' or confirm == 'yes':
            logging.info(f'Answer was \'{confirm}\': Entering non-interactive mode.')
            return True
        else:
            logging.info(f'Answer was \'{confirm}\': Did not enter non-interactive mode.')
            return False

    async def messenger(self):
        await self.wait_until_ready()
        
        non_interactive = False
        channel = await self.prompt_switch_channel()
        
        try:
            while non_interactive == False:
                command = await aioconsole.ainput(PROMPT)
                if not command:
                    continue
                elif command == 'c' or command == 'change':
                    channel = await self.prompt_switch_channel()
                elif command == 'j' or command == 'join':
                    await self.prompt_toggle_join(channel)
                elif command == 'm' or command == 'message':
                    await self.prompt_message(channel)
                elif command == 'n' or command == 'non-interactive':
                    non_interactive = await self.prompt_non_interactive()
                else:
                    logging.warning(f'Command \'{command}\' not recognized. Please try again.')
            
            # non-interactive loop
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()
            await self.close()

def init_logging():
    if not os.isdir('logs'):
        os.mkdir('logs')
    
    log = logging.getLogger()
    log.setLevel(logging.NOTSET)
    
    log_formatter_file = logging.Formatter(LOG_FORMAT_FILE)
    log_formatter_stream = logging.Formatter(LOG_FORMAT_STREAM)
    today = datetime.date.today().strftime('%m-%d-%y')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter_stream)
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler_info = logging.FileHandler(LOG_FILE_INFO.format(today), mode='a')
    file_handler_info.setFormatter(log_formatter_file)
    file_handler_info.setLevel(logging.INFO)
    log.addHandler(file_handler_info)

    file_handler_debug = logging.FileHandler(LOG_FILE_DEBUG.format(today), mode='a')
    file_handler_debug.setFormatter(log_formatter_file)
    file_handler_debug.setLevel(logging.DEBUG)
    log.addHandler(file_handler_debug)
    
    logging.raiseExceptions = False
    logging.getLogger('discord').setLevel(logging.INFO)

if __name__ == '__main__':
    if os.name == 'nt':
        os.system('chcp 65001') # set Windows terminal output format to use utf-8
    init_logging()

    client = RegClient()
    logging.info('Running bot!')
    client.run(TOKEN)