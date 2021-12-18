
# STANDARD LIB
import logging
import os

# EXTERNAL LIB
import dotenv

# LOCAL LIB
import client
import commands
import logger

import pdb

if __name__ == '__main__':
    if os.name == 'nt':
        os.system('chcp 65001') # set Windows terminal output format to use utf-8
    logger.init_logging()
    dotenv.load_dotenv()
    debug = os.getenv('DEBUG') == 'True' # Casting as bool can lead to unexpected behavior.
    
    client = client.TreeClient()
    commands.register_commands(client)
    token = os.getenv('DEV_TOKEN') if debug else os.getenv('LIVE_TOKEN')
    logging.info(f'{"[DEBUG MODE] " if debug else ""}Initialization complete!')
    client.run(token)
