DEFAULT_CHANNEL = 'moonlight'
DOWNLOAD_BY_DEFAULT = False
EMOJI_REGEX = r'<a:.+?:\d+>|<:.+?:\d+>'
FFMPEG_STREAM_OPTIONS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
MENTION_REGEX = r'<@!*&*[0-9]+>'
PROMPT = 'Enter command [[c]hange] [[j]oin] [[m]essage] [[n]on-interactive]: '
QUEUE_MAXSIZE = 10
REQUIRE_BOT_IN_CALL = 'RequireBotInCall'
REQUIRE_BOT_PLAYING = 'RequireBotPlaying'
REQUIRE_BOT_PAUSED = 'RequireBotNotPaused'
REQUIRE_BOT_QUEUE = 'RequireBotQueue'
REQUIRE_USER_IN_CALL = 'RequireUserInCall'
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


