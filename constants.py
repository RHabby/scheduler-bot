REDDIT_BASE = "https://reddit.com"

GFY_DOMAIN = "gfycat.com"
IMGUR_DOMAIN = "i.imgur.com", "m.imgur.com", "imgur.com"
RED_DOMAIN = "i.redd.it", "v.redd.it"
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

commands = {
    "/start": "Start the bot,",
    "/help": "Bot help,",
    "/reddit": "Gives content from reddit,",
    "/redis": "Gives saved content from Redis database,",
    "/instagram": "Gives content from Instagram."
}

# callback data
FORWARD = "forward"
FORWARD_NOW = "forward now"
QUEUE = "queue"
CANCEL = "cancel"
