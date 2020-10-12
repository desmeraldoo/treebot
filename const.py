import dotenv
import os

# CONSTANTS
dotenv.load_dotenv()

DEFAULT_CHANNEL = 'moonlight'
EMOJI_REGEX = r'<a:.+?:\d+>|<:.+?:\d+>'
ENABLED_CHANNELS = [750703990555279443, 750045079909040128]
IRREDEEMABLE = '度し難い…'
LOG_FILE_INFO = 'logs/reg-{}.log'
LOG_FILE_DEBUG = 'logs/reg-debug-{}.log'
LOG_FORMAT_FILE = u'%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
LOG_FORMAT_STREAM = u'%(asctime)s [%(levelname)s] %(message)s'
PROMPT = 'Enter command [[c]hange] [[j]oin] [[m]essage] [[n]on-interactive]: '
REDEEMABLE = '良い。'
TOKEN = os.getenv('DISCORD_TOKEN')
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
