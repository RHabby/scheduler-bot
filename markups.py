from telebot import types

from config import default_subreddits as ds
import constants as cs

# start markup
start_markup = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=False
)
start_markup.row("/help")
start_markup.row("/reddit")
start_markup.row("/redis")
start_markup.row("/instagram")

# choose sorting markup
choose_sorting_markup = types.ReplyKeyboardMarkup(
    row_width=3,
    resize_keyboard=True,
    one_time_keyboard=True
)
choose_sorting_markup.row("new", "hot", "top", "rising")
choose_sorting_markup.row("Назад")

# choose channel markup
choose_channel_markup = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True
)
choose_channel_markup.row(
    ds["subreddit_01"],
    ds["subreddit_02"],
    ds["subreddit_03"]
)
choose_channel_markup.row(
    ds["subreddit_04"],
    ds["subreddit_05"],
    ds["subreddit_06"]
)
choose_channel_markup.row(
    ds["subreddit_07"],
    ds["subreddit_08"],
    ds["subreddit_09"],
    ds["subreddit_10"]
)
# choose_channel_markup.row(ds["step_back"])

# choose posts count
choose_count_markup = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True
)
choose_count_markup.row("1", "3")
choose_count_markup.row("5", "7")
choose_count_markup.row("Назад")

# forward to channel
forward_to_channel_markup = types.InlineKeyboardMarkup(
    row_width=1
)
forward_to_channel_markup.add(types.InlineKeyboardButton(
    text="Forward to channel",
    callback_data=cs.FORWARD
))

# forward now of add to queue
when_forward_markup = types.InlineKeyboardMarkup(
    row_width=2
)
when_forward_markup.row(
    types.InlineKeyboardButton(
        text="Now",
        callback_data=cs.FORWARD_NOW),
    types.InlineKeyboardButton(
        text="Add to queue",
        callback_data=cs.QUEUE),
)
when_forward_markup.row(
    types.InlineKeyboardButton(
        text="Cancel",
        callback_data=cs.CANCEL)
)
