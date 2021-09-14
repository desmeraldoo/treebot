DEFAULT_CHANNEL = 'moonlight'
EMOJI_REGEX = r'<a:.+?:\d+>|<:.+?:\d+>'
MENTION_REGEX = r'<@!*&*[0-9]+>'
PROMPT = 'Enter command [[c]hange] [[j]oin] [[m]essage] [[n]on-interactive]: '
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

YTDL_OPTIONS = {
    'default_search': 'auto',
    'format': 'bestaudio/best',
    'ignoreerrors': False,
    'logtostderr': False,
    'noplaylist': True,
    'nocheckcertificate': True,
    'no_warnings': True,
    'quiet': True,
    'restrictfilenames': True,
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

#     ,
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'executable': 'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe'
}

