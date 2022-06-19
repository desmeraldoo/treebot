import logging
from dataclasses import dataclass, field
from typing import Final, cast

import nextcord

from src.client.music.module import MusicModule
from src.settings import LOGGER_NAME

logger: Final[logging.Logger] = logging.getLogger(LOGGER_NAME)


@dataclass
class GuildState:
    music: MusicModule = field(default_factory=MusicModule)


class TreeClient(nextcord.Client):
    def __init__(self) -> None:
        super().__init__()
        self.initialized = False
        self.guild_state: dict[nextcord.Guild, GuildState] = dict()
        self.emoji_dict: dict[str, str] = dict()

    def init_guild_state(self) -> None:
        for guild in self.guilds:
            self.guild_state[guild] = GuildState()

    def init_emoji_dict(self) -> None:
        self.emoji_dict = dict()
        for emoji in self.emojis:
            key = f":{emoji.name}:"
            if emoji.animated:
                value = f"<a:{emoji.name}:{emoji.id}>"
            else:
                value = f"<:{emoji.name}:{emoji.id}>"
            self.emoji_dict[key] = value

    async def on_voice_state_update(
        self,
        member: nextcord.Member,
        before: nextcord.VoiceState,
        after: nextcord.VoiceState,
    ) -> None:
        if self.guild_state[member.guild].voice.is_connected():
            # cast required because otherwise the IDE considers the channel merely a Connectable, rather than a VoiceChannel
            channel = cast(
                nextcord.VoiceChannel, self.guild_state[member.guild].voice.channel
            )
            if len(channel.members) == 1:
                await member.guild.voice_client.disconnect()
                self.guild_state[member.guild].music.reset()

    async def on_ready(self) -> None:
        for guild in self.guilds:
            logger.info(f"[{guild}] {self.user} has connected to {guild}!")

        if not self.initialized:
            # Assemble dictionary server assets
            self.init_guild_state()
            self.init_emoji_dict()
            # Init command prompt (not currently active)
            # self.loop.create_task(self.prompt())

            self.initialized = True

    async def on_resumed(self) -> None:
        logger.info("Resuming Reg session...")

    async def on_message(self, message: nextcord.Message) -> None:
        if message.author == self.user or message.author.bot:
            return
