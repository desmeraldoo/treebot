
# STANDARD LIB
import logging
import os

# EXTERNAL LIB
import dotenv

# LOCAL LIB
import logger
from client import TreeClient
from commands import register_commands

if __name__ == '__main__':
    if os.name == 'nt':
        os.system('chcp 65001') # set Windows terminal output format to use utf-8
    logger.init_logging()
    dotenv.load_dotenv()
    
    client = TreeClient()
    register_commands(client)
    
    logging.info('Running bot!')
    client.run(os.getenv('DISCORD_TOKEN'))