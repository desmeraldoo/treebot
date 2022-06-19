# STANDARD LIB
import logging
import os

# EXTERNAL LIB
import dotenv

# LOCAL LIB
import src.client.client as client
import src.log as log
from src.settings import DEBUG

if __name__ == "__main__":
    if os.name == "nt":
        os.system("chcp 65001")  # set Windows terminal output format to use utf-8
    log.init_logging()
    dotenv.load_dotenv()

    bot = client.TreeClient()
    # commands.register_commands(src)
    token = os.getenv("DEV_TOKEN") if DEBUG else os.getenv("LIVE_TOKEN")
    logging.info(f'{"[DEBUG MODE] " if DEBUG else ""}Initialization complete!')
    bot.run(token)
