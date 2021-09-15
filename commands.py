# STANDARD LIB
import json
import os

# EXTERNAL LIB
import discord_slash
from discord_slash.utils import manage_commands

# LOCAL LIB
from client._const import *

import pdb

def register_commands(client):
    slash = discord_slash.SlashCommand(client, sync_commands=True)
    command_guilds = list(map(int, json.loads(os.getenv('GUILDS'))))
    
    @slash.slash(
        name='play', 
        description=f'Play a song, or resume playing if paused',
        guild_ids=command_guilds,
        options=[
            manage_commands.create_option(
                name='song',
                description=f'The name or url of the song you would like to play',
                option_type=3,
                required=False
            )
        ]
    )
    async def play(ctx, song=None):
        reqs = { REQUIRE_USER_IN_CALL: True }
        if not song: reqs[REQUIRE_BOT_IN_CALL] = True
        await client.music.reqs(
            ctx,
            lambda c=ctx, s=song or None: client.music.command_play(c, s),
            **reqs
        )
    
    @slash.slash(
        name='pause', 
        description='Pause the current song', 
        guild_ids=command_guilds
    )
    async def pause(ctx):
        reqs = { REQUIRE_USER_IN_CALL: True, REQUIRE_BOT_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.pause(c),
            **reqs
        )
    
    '''
    @slash.slash(
        name='skip', 
        description='Skips the currently playing song', 
        guild_ids=command_guilds
    )
    async def skip(ctx):
        reqs = { REQUIRE_USER_IN_CALL: True, REQUIRE_BOT_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.skip(ctx)
            **reqs
        )
    '''
    
    @slash.slash(
        name='reset', 
        description=f'Stop playing music and clears the queue',
        guild_ids=command_guilds
    )
    async def reset(ctx):
        reqs = { REQUIRE_USER_IN_CALL: True, REQUIRE_BOT_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.reset(ctx),
            **reqs
        )
        
    @slash.slash(
        name='toggle_download', 
        description='Toggle downloading of logs. Downloading is disabled by default', 
        guild_ids=command_guilds
    )
    async def toggle_download(ctx):
        reqs = { REQUIRE_USER_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.toggle_download(ctx),
            **reqs
        )
    
    @slash.slash(
        name='test', 
        description='A nonfunctional command that serves as a template for the developer', 
        guild_ids=command_guilds
    )
    async def test(ctx):
        await ctx.send('Command is registered!')