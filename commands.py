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
    debug = os.getenv('DEBUG') == 'True' # Casting as bool can lead to unexpected results.
    debug_guild = int(os.getenv('DEV_GUILD'))
    command_guilds = [debug_guild] if debug else None
    slash = discord_slash.SlashCommand(client, sync_commands=True, delete_from_unused_guilds=True, debug_guild=debug_guild)
    
    @slash.slash(
        name='play', 
        description='Play a song. If already playing or paused, adds the song to the queue',
        guild_ids=command_guilds,
        options=[
            manage_commands.create_option(
                name='song',
                description=f'The name or url of the song you would like to play',
                option_type=3,
                required=True
            )
        ]
    )
    async def play(ctx, song):
        reqs = {
            REQUIRE_USER_IN_CALL: True,
            REQUIRE_FFMPEG: True
        }
        await client.music.reqs(
            ctx,
            lambda c=ctx, s=song: client.music.command_play(c, s),
            **reqs
        )
    
    @slash.slash(
        name='pause', 
        description='Pause the current song',
        guild_ids=command_guilds
    )
    async def pause(ctx):
        reqs = {
            REQUIRE_USER_IN_CALL: True,
            REQUIRE_BOT_IN_CALL: True,
            REQUIRE_BOT_PLAYING: True
        }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.pause(c),
            **reqs
        )
    
    @slash.slash(
        name='resume', 
        description='Resume playing a song that was paused',
        guild_ids=command_guilds
    )
    async def resume(ctx):
        reqs = {
            REQUIRE_USER_IN_CALL: True,
            REQUIRE_BOT_IN_CALL: True,
            REQUIRE_BOT_PAUSED: True
        }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.resume(c),
            **reqs
        )
    
    @slash.slash(
        name='skip', 
        description='Skips the currently playing song',
        guild_ids=command_guilds
    )
    async def skip(ctx):
        reqs = {
            REQUIRE_USER_IN_CALL: True,
            REQUIRE_BOT_IN_CALL: True,
            REQUIRE_BOT_QUEUE: True
        }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.skip(c),
            **reqs
        )
    
    @slash.slash(
        name='stop', 
        description=f'Stop playing music and clears the queue',
        guild_ids=command_guilds
    )
    async def stop(ctx):
        reqs = { REQUIRE_USER_IN_CALL: True, REQUIRE_BOT_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.reset(c),
            **reqs
        )
    
    @slash.slash(
        name='loop', 
        description='Toggles looping the currently playing song. The queue will not advance',
        guild_ids=command_guilds
    )
    async def loop(ctx):
        reqs = {
            REQUIRE_USER_IN_CALL: True,
            REQUIRE_BOT_IN_CALL: True
        }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.toggle_looping(c),
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
            lambda c=ctx: client.music.toggle_download(c),
            **reqs
        )
    
    @slash.slash(
        name='set_volume', 
        description='Sets the default volume on the bot. Applies to the next song played.',
        guild_ids=command_guilds,
        options=[
            manage_commands.create_option(
                name='volume',
                description='The new volume, a number between 0 and 200. 100 is the default volume.',
                option_type=4,
                required=True
            )
        ]
    )
    async def set_volume(ctx, volume):
        reqs = { REQUIRE_USER_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx, v=volume: client.music.set_volume(c, v),
            **reqs
        )
    
    @slash.slash(
        name='test', 
        description='A nonfunctional command that serves as a template for the developer', 
        guild_ids=[debug_guild]
    )
    async def test(ctx):
        await ctx.send('Command is registered!')