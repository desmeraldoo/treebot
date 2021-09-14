# STANDARD LIB
import json
import os

# EXTERNAL LIB
import discord_slash
from discord_slash.utils import manage_commands

import pdb

def register_commands(client):
    slash = discord_slash.SlashCommand(client, sync_commands=True)
    command_guilds = list(map(int, json.loads(os.getenv('GUILDS'))))
        
    @slash.slash(
        name='play', 
        description=f'Play a song',
        guild_ids=command_guilds,
        options=[
            manage_commands.create_option(
                name='url',
                description=f'The url of the song you would like to play',
                option_type=3,
                required=True
            )
        ]
    )
    async def play(ctx, url):
        await client.music.play(ctx, url)
    
    @slash.slash(
        name='stop', 
        description=f'Stop playing music and exit the channel',
        guild_ids=command_guilds,
    )
    async def stop(ctx):
        await client.music.stop(ctx)
    
    @slash.slash(
        name='custom', 
        description='Debug for slash commands', 
        guild_ids=command_guilds,
    )
    async def debug(ctx):
        await ctx.send('Command is registered!')