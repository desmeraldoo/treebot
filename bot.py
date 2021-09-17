
# STANDARD LIB
import logging
import os

# EXTERNAL LIB
import dotenv

# LOCAL LIB
import logger
from client import TreeClient
from commands import register_commands

# TODO: Add a way to loop the same song
# TODO: Add a way to examine the queue
# TODO: Add a way to play from file upload
# TODO: Add a way to play a playlist
# TODO: Leave call when no one else is there
# TODO: Add a way for prompt to switch between guilds
# TODO: Add REQUIRE_USER_NOT_DEAF req
# TODO: Add progress bar for video downloads
# TODO: Add dedicated folder for videos
# TODO: Run a different event loop for each guild

# FIXME: Test behavior when file downloaded as part of queue is deleted if it's in the queue multiple times
# FIXME: Add failsafe for when Discord fails to render slash command and the user's message is sent as normal
# FIXME: Test behavior when downloading extremely long files and/or set download limit
# FIXME: Place logs in proper directory

if __name__ == '__main__':
    if os.name == 'nt':
        os.system('chcp 65001') # set Windows terminal output format to use utf-8
    logger.init_logging()
    dotenv.load_dotenv()
    
    client = TreeClient()
    register_commands(client)
    
    logging.info('Initialization complete')
    client.run(os.getenv('DISCORD_TOKEN'))