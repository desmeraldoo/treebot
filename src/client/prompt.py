# STANDARD LIB
import asyncio
import logging

# EXTERNAL LIB
import aioconsole
import discord

# LOCAL LIB
from ._const import *


class InteractivePrompt:
    def __init__(self, parent):
        self.parent = parent

    async def prompt_switch_channel(self):
        while True:
            channel_name = await aioconsole.ainput(
                "Enter the initial channel ([enter] for default): "
            )
            if not channel_name:
                channel_name = DEFAULT_CHANNEL
                break
            elif channel_name not in self.parent.channel_dict.keys():
                logging.warning(
                    f"Channel name '{channel_name}' not recognized; please try again."
                )
            elif channel_name in self.parent.channel_dict.keys():
                break

        channel_id = self.parent.channel_dict[channel_name]
        channel = self.parent.get_channel(channel_id)
        logging.info(f"Successfully switched to channel '{channel}'.")
        return channel

    async def prompt_message(self, channel):
        if not isinstance(channel, discord.channel.TextChannel):
            logging.warning(
                f"'{channel}' is a '{type(channel)}' channel, not a text channel."
            )
            return

        while True:
            message = await aioconsole.ainput(
                f"Enter the message to send as Reg in {channel} (empty to quit): "
            )
            if not message:
                logging.info("Message is empty -- returning to main menu.")
                return

            tokens = message.split(" ")
            new_message = []
            for token in tokens:
                if token in self.parent.emoji_dict.keys():
                    new_message.append(self.parent.emoji_dict[token])
                else:
                    new_message.append(token)
            message = " ".join(new_message)
            logging.info(message)

            await channel.send(message)

    async def prompt_toggle_join(self, channel):
        if type(channel) == discord.channel.VoiceChannel:
            await self.parent.join(channel)
        else:
            logging.warning(f"'{channel}' is not a voice channel.")

    async def prompt_non_interactive(self):
        confirm = await aioconsole.ainput(
            "Enter [[y]es] if you are sure you want to enter non-interactive mode: "
        )
        if confirm == "y" or confirm == "yes":
            logging.info(f"Answer was '{confirm}': Entering non-interactive mode.")
            return True
        else:
            logging.info(f"Answer was '{confirm}': Did not enter non-interactive mode.")
            return False

    async def prompt(self):
        await self.parent.wait_until_ready()

        non_interactive = False
        channel = await self.prompt_switch_channel()

        try:
            while non_interactive == False:
                command = await aioconsole.ainput(PROMPT)
                if not command:
                    continue
                elif command == "c" or command == "change":
                    channel = await self.prompt_switch_channel()
                elif command == "j" or command == "join":
                    await self.prompt_toggle_join(channel)
                elif command == "m" or command == "message":
                    await self.prompt_message(channel)
                elif command == "n" or command == "non-interactive":
                    non_interactive = await self.prompt_non_interactive()
                else:
                    logging.warning(
                        f"Command '{command}' not recognized. Please try again."
                    )

            # non-interactive loop
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            for guild in self.parent.guilds:
                if self.parent.is_connected(guild):
                    await self.parent.close_connection(guild)
            await self.parent.close()
