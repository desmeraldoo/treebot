import os
from typing import Any, Final

DEBUG = os.getenv("DEUBG") == "True"
DEFAULT_CHANNEL: Final[str] = "moonlight"
DEFAULT_VOLUME: Final[int] = 100
DOWNLOAD_BY_DEFAULT: Final[bool] = False
EMOJI_REGEX: Final[str] = r"<a:.+?:\d+>|<:.+?:\d+>"
FFMPEG_STREAM_OPTIONS: Final[
    str
] = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
LOGGER_NAME: Final[str] = "treebot"
MENTION_REGEX: Final[str] = r"<@!*&*[0-9]+>"
PROMPT: Final[
    str
] = "Enter command [[c]hange] [[j]oin] [[m]essage] [[n]on-interactive]: "
QUEUE_MAXSIZE: Final[int] = 10
URL_REGEX: Final[
    str
] = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
YTDL_OPTIONS: Final[dict[str, Any]] = {
    "default_search": "auto",
    "format": "bestaudio/best",
    "ignoreerrors": False,
    "logtostderr": False,
    "noplaylist": True,
    "nocheckcertificate": True,
    "no_warnings": True,
    "quiet": True,
    "restrictfilenames": True,
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
