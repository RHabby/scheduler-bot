import json

from telebot import types

import constants as cs
import redis_worker as rw

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

# forward now or add to queue
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

# when forwarded
forwarded_markup = types.InlineKeyboardMarkup(
    row_width=2
)
forwarded_markup.row(
    types.InlineKeyboardButton(
        text="Add to queue",
        callback_data=cs.QUEUE),
)

# when added to the queue
no_queue_markup = types.InlineKeyboardMarkup(
    row_width=2
)
no_queue_markup.row(
    types.InlineKeyboardButton(
        text="Now",
        callback_data=cs.FORWARD_NOW),
    types.InlineKeyboardButton(
        text="In queue✅",
        callback_data=cs.NO)
)


# settings keyboard
settings_markup = types.InlineKeyboardMarkup(
    row_width=2
)
settings_markup.row(
    types.InlineKeyboardButton(
        text="Add Subreddit",
        callback_data=cs.ADD_SUBREDDIT
    ),
    types.InlineKeyboardButton(
        text="Delete Subreddit",
        callback_data=cs.DELETE_SUBREDDIT
    )
)
settings_markup.row(
    types.InlineKeyboardButton(
        text="Add where to post",
        callback_data=cs.ADD_WHERE_TO
    ),
    types.InlineKeyboardButton(
        text="Delete where to post",
        callback_data=cs.DELETE_WHERE_TO
    )
)
settings_markup.row(
    types.InlineKeyboardButton(
        text="Go Back",
        callback_data=cs.OUT)
)


def set_kboard(id, key, value):
    try:
        kboard = json.loads(rw.get_value(id, key))
        if value not in kboard:
            print(f"value not in kboard: {value not in kboard}")
            kboard.append(value)
        else:
            return False
    except TypeError:
        kboard = [value]

    rw.set_state_value(id, key, json.dumps(kboard))
    return True


def delete_button(id, key, value):
    try:
        kboard = json.loads(rw.get_value(id, key))
        print(kboard)
        kboard.remove(value)
    except TypeError:
        return False

    rw.set_state_value(id, key, json.dumps(kboard))
    return True


def generate_kboard(kboard_type, id, key):
    if kboard_type.lower() == "reply":
        kboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
    elif kboard_type.lower() == "inline":
        kboard = types.InlineKeyboardMarkup(
            row_width=2
        )
    else:
        pass

    kboard_buttons = json.loads(rw.get_value(id, key))
    if isinstance(kboard, types.ReplyKeyboardMarkup):
        for button in kboard_buttons:
            kboard.add(types.KeyboardButton(text=button))
    elif isinstance(kboard, types.InlineKeyboardMarkup):
        for button in kboard_buttons:
            for text, callback_data in button.items():
                kboard.add(
                    types.InlineKeyboardButton(
                        text=text,
                        callback_data=callback_data
                    )
                )

    return kboard


if __name__ == "__main__":
    pass
