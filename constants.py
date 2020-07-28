REDDIT_BASE = "https://reddit.com"

GFY_DOMAIN = "gfycat.com"
IMGUR_DOMAIN = "i.imgur.com", "m.imgur.com", "imgur.com"
RED_DOMAIN = "i.redd.it", "v.redd.it", "external-preview.redd.it"
OTHER = "redgifs.com"

GIF_TYPE = "gif"
GIFV = "gifv"
GIF_TYPES = ["mp4", "gif"]
CONTENT_GIF = "image/gif"
CONTENT_MP4 = "video/mp4"

IMG_TYPE = "img"
IMG_TYPES = ["jpg", "jpeg", "png"]
CONTENT_IMG = "image/jpeg"
CONTENT_PNG = "image/png"

OTHER_TYPE = "other"
TEXT_TYPE = "text"
VIDEO_TYPE = "mp4"

TELEGRAM_VIDEO_LIMIT = 50 * 1024 * 1024

welcome_message = f"If you are allowed to be here you must know how \
 to use me. If you are not you can use the `/help` command to find out."

commands = {
    "/start": "start the bot;",
    "/help": "bot help;",
    "/settings": "set your subreddits list;",
    "/reddit": "gives content from reddit;",
    "/redis": "short info about queue and content types in it;",
    "/insta": "send command and link to instagram post."
}

# callback data
FORWARD = "forward"
FORWARD_NOW = "forward now"
QUEUE = "queue"
CANCEL = "cancel"
OUT = "out"
NO = "empty"
ADD_SUBREDDIT = "add subreddit"
DELETE_SUBREDDIT = "delete subreddit"
ADD_WHERE_TO = "add where"
DELETE_WHERE_TO = "delete where"

# logging configuration
dict_log_config = {
    "version": 1,
    "handlers": {
        "fileHandler": {
            "class": "logging.FileHandler",
            "formatter": "bot_formatter",
            "filename": "./logs/bot_logs.log"
        }
    },
    "loggers": {
        "bot_logger": {
            "handlers": ["fileHandler"],
            "level": "INFO"
        }
    },
    "formatters": {
        "bot_formatter": {
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        }
    }
}
