
# STANDARD LIB
import logging
import os

# EXTERNAL LIB
import dotenv

# LOCAL LIB
import logger
from client import TreeClient
from commands import register_commands

# TODO: Add a way for prompt to switch between guilds
# TODO: Add a way to examine the queue
# TODO: Add a way to play from file upload
# FIXME: Test behavior when file downloaded as part of queue is deleted if it's in the queue multiple times

if __name__ == '__main__':
    if os.name == 'nt':
        os.system('chcp 65001') # set Windows terminal output format to use utf-8
    logger.init_logging()
    dotenv.load_dotenv()
    
    client = TreeClient()
    register_commands(client)
    
    logging.info('Initialization complete')
    client.run(os.getenv('DISCORD_TOKEN'))