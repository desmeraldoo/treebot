import enum
import os
from typing import Final

import nextcord

from src.client.client import TreeClient
from src.client.music.module import MusicModule
from src.settings import DEBUG

DEBUG_GUILD = int(os.getenv("DEBUG_GUILD"))
DEBUG_GUILDS: Final[list[int] | None] = [DEBUG_GUILD] if DEBUG else None


class Constraint(enum.Enum):
    REQUIRE_BOT_IN_CALL = enum.auto()
    REQUIRE_BOT_PAUSED = enum.auto()
    REQUIRE_BOT_PLAYING = enum.auto()
    REQUIRE_BOT_QUEUE = enum.auto()
    REQUIRE_FFMPEG = enum.auto()
    REQUIRE_USER_IN_CALL = enum.auto()


async def reqs(
    music: MusicModule, interaction: nextcord.Interaction, constraints: set[Constraint]
) -> bool:
    if Constraint.REQUIRE_FFMPEG in constraints:
        if not music.ffmpeg:
            await interaction.send(
                "❌❌ Sorry, FFMPEG hasn't been installed correctly on my machine. Please contact a developer."
            )
            return False
    if Constraint.REQUIRE_USER_IN_CALL in constraints:
        if not interaction.user.voice:
            await interaction.send(
                "❌ You must be connected to a voice channel to use this command."
            )
            return False
    if Constraint.REQUIRE_BOT_IN_CALL in constraints:
        if not music.voice.is_connected():
            await interaction.send(
                "❌ I must be connected to a voice channel for this command to be valid."
            )
            return False
    if Constraint.REQUIRE_BOT_PLAYING in constraints:
        if not music.voice.is_playing():
            await interaction.send(
                "❌ I must be playing audio for this command to be valid."
            )
            return False
    if Constraint.REQUIRE_BOT_PAUSED in constraints:
        if not music.voice.is_paused():
            await interaction.send("❌ I must be paused for this command to be valid.")
            return False
    if Constraint.REQUIRE_BOT_QUEUE in constraints:
        if not music.video_queue.qsize() > 0:
            await interaction.send(
                "❌ There must be items in the queue for this command to be valid."
            )
            return False
    return True


def register_commands(client: TreeClient) -> None:
    @nextcord.slash_command(
        name="play",
        description="Play a song. If already playing or paused, adds the song to the queue",
        guild_ids=DEBUG_GUILDS,
    )
    async def play(interaction: nextcord.Interaction, song: str) -> None:
        constraints = {Constraint.REQUIRE_USER_IN_CALL, Constraint.REQUIRE_FFMPEG}
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.command_play(interaction, song)

    @nextcord.slash_command(
        name="pause", description="Pause the current song", guild_ids=DEBUG_GUILDS
    )
    async def pause(interaction: nextcord.Interaction) -> None:
        constraints = {
            Constraint.REQUIRE_USER_IN_CALL,
            Constraint.REQUIRE_BOT_IN_CALL,
            Constraint.REQUIRE_BOT_PLAYING,
        }
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.pause(interaction)

    @nextcord.slash_command(
        name="resume",
        description="Resume playing a song that was paused",
        guild_ids=DEBUG_GUILDS,
    )
    async def resume(interaction: nextcord.Interaction) -> None:
        constraints = {
            Constraint.REQUIRE_USER_IN_CALL,
            Constraint.REQUIRE_BOT_IN_CALL,
            Constraint.REQUIRE_BOT_PAUSED,
        }
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.resume(interaction)

    @nextcord.slash_command(
        name="skip",
        description="Skips the currently playing song",
        guild_ids=DEBUG_GUILDS,
    )
    async def skip(interaction: nextcord.Interaction) -> None:
        constraints = {
            Constraint.REQUIRE_USER_IN_CALL,
            Constraint.REQUIRE_BOT_IN_CALL,
            Constraint.REQUIRE_BOT_QUEUE,
        }
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.skip(interaction)

    @nextcord.slash_command(
        name="stop",
        description=f"Stop playing music and clears the queue",
        guild_ids=DEBUG_GUILDS,
    )
    async def stop(interaction: nextcord.Interaction) -> None:
        constraints = {Constraint.REQUIRE_USER_IN_CALL, Constraint.REQUIRE_BOT_IN_CALL}
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.reset(interaction)

    @nextcord.slash_command(
        name="loop",
        description="Toggles looping the currently playing song. The queue will not advance",
        guild_ids=DEBUG_GUILDS,
    )
    async def loop(interaction: nextcord.Interaction):
        constraints = {Constraint.REQUIRE_USER_IN_CALL}
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.toggle_looping(interaction)

    @nextcord.slash_command(
        name="toggle_download",
        description="Toggle downloading of logs. Downloading is disabled by default",
        guild_ids=DEBUG_GUILDS,
    )
    async def toggle_download(interaction: nextcord.Interaction):
        constraints = {Constraint.REQUIRE_USER_IN_CALL}
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.toggle_download(interaction)

    @nextcord.slash_command(
        name="set_volume",
        description="Sets the default volume on the bot. Applies to the next song played.",
        guild_ids=DEBUG_GUILDS,
    )
    async def set_volume(interaction: nextcord.Interaction, volume: int):
        constraints = {Constraint.REQUIRE_USER_IN_CALL}
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.set_volume(interaction)

    @nextcord.slash_command(
        name="view", description="Displays the current queue", guild_ids=DEBUG_GUILDS
    )
    async def view(interaction: nextcord.Interaction):
        constraints = {Constraint.REQUIRE_USER_IN_CALL}
        music = client.guild_state[interaction.guild].music
        if await reqs(music, interaction, constraints):
            await music.view(interaction)

    @nextcord.slash_command(
        name="test",
        description="A nonfunctional command that serves as a template for the developer",
        guild_ids=[DEBUG_GUILD],  # users should never see this command
    )
    async def test(interaction: nextcord.Interaction):
        await interaction.send("Command is registered!")
