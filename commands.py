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
    slash = discord_slash.SlashCommand(client, sync_commands=True, debug_guild=750703990555279440, delete_from_unused_guilds=True)

    @slash.slash(
        name='play', 
        description='Plays a song. If already playing or paused, adds the song to the queue',
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
        reqs = { REQUIRE_USER_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx, s=song: client.music.command_play(c, s),
            **reqs
        )
    
    @slash.slash(
        name='pause', 
        description='Pauses the current song', 
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
        description='Resumes playing a song that was paused', 
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
        description='Skips the currently playing song. If paused, plays the next song', 
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
        description='Stops playing music and clears the queue', 
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
        description='Toggles looping the currently playing song. The queue will not advance while looping', 
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
        description='Toggles downloading of logs. Downloading is disabled by default', 
    )
    async def toggle_download(ctx):
        reqs = { REQUIRE_USER_IN_CALL: True }
        await client.music.reqs(
            ctx,
            lambda c=ctx: client.music.toggle_download(c),
            **reqs
        )
    
    @slash.slash(
        name='test_global', 
        description='A nonfunctional command that serves as a template for the developer', 
    )
    async def test(ctx):
        await ctx.send('Command is registered!')
