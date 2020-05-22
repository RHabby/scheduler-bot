import pprint
from time import sleep

import telebot
from prawcore.exceptions import Redirect
from telebot import types
from telebot.apihelper import ApiException

import config
import constants as cs
import image_worker as iw
import markups as m
import redis_worker as rw
from config import States
from reddit_supplier import download_file, get_full_info

bot = telebot.TeleBot(token=config.TOKEN)
# TODO: переделать на вебхуки.

welcome_message = "If you are allowed to be here you must know how \
    to use me. If you are not you can use the `/help` command to find out."


@bot.message_handler(
    func=lambda message: message.from_user.id != config.ADMIN_ID)
def answer_not_admin(message: types.Message):
    reply_text = "Hi, there! I am a bot. If you are not one of my admins,\
         you have nothing to do here. Please, leave me alone."
    bot.reply_to(message=message, text=reply_text)


@bot.message_handler(commands=["start"])
def start(message: types.Message):
    welcome = f"Hello, {message.from_user.first_name}.\n{welcome_message}"
    bot.send_message(
        chat_id=message.from_user.id,
        text=welcome,
        reply_markup=m.start_markup,
        parse_mode="markdown",
        disable_notification=True
    )

    rw.set_state(
        id=message.from_user.id,
        value=config.States.START_STATE.value
    )


@bot.message_handler(commands=["help"])
def help(message: types.Message):
    text = "Commands:\n"
    for key, value in cs.commands.items():
        text += f"`{key}` — {value}\n"

    bot.send_message(
        chat_id=message.from_user.id,
        text=text,
        reply_markup=m.start_markup,
        parse_mode="markdown",
        disable_notification=True
    )


@bot.message_handler(commands=["reddit"])
def choose_commands(message: types.Message):
    bot.send_message(
        chat_id=message.from_user.id,
        text="what subreddit would you like?",
        reply_markup=m.choose_channel_markup,
        disable_notification=True
    )
    rw.set_state(id=message.from_user.id,
                 value=config.States.ENTER_SUBREDDIT_STATE.value)


@bot.message_handler(
    func=lambda message: rw.get_current_state(message.from_user.id) == States.ENTER_SUBREDDIT_STATE.value)
def choose_channel(message: types.Message):
    rw.set_state_value(message.from_user.id,
                       "subreddit_name", message.text)
    bot.send_message(
        chat_id=message.from_user.id,
        text="What sorting would you like?",
        reply_markup=m.choose_sorting_markup,
        disable_notification=True
    )
    rw.set_state(id=message.from_user.id,
                 value=config.States.ENTER_SORTING_STATE.value)


@bot.message_handler(
    func=lambda message: rw.get_current_state(message.from_user.id) == States.ENTER_SORTING_STATE.value)
def choose_sorting(message: types.Message):
    rw.set_state_value(message.from_user.id,
                       "sorting", message.text)
    bot.send_message(
        chat_id=message.from_user.id,
        text="How many posts would you like to see?",
        reply_markup=m.choose_count_markup,
        disable_notification=True
    )
    rw.set_state(id=message.from_user.id,
                 value=config.States.ENTER_COUNT_STATE.value)

@bot.message_handler(
    func=lambda message: rw.get_current_state(message.from_user.id) == States.ENTER_COUNT_STATE.value)
def choose_count(message: types.Message):
    if message.text.lower() == "назад":
        pass

    if not message.text.isdigit():
        bot.send_message(
            chat_id=message.from_user.id,
            text="What you entering is not a number, try again",
            reply_to_message_id=message.message_id,
            reply_markup=m.choose_count_markup,
            disable_notification=True
        )
    elif int(message.text) < 1 or int(message.text) > 10:
        bot.send_message(
            chat_id=message.from_user.id,
            text="Some piece of advice here: try to enter a number between 1 and 10, please.",
            reply_to_message_id=message.message_id,
            reply_markup=m.choose_count_markup,
            disable_notification=True
        )
    else:
        rw.set_state_value(
            id=message.from_user.id,
            key="count",
            value=message.text
        )
        return send_reddit_photo(message)


def send_reddit_photo(message: types.Message):
    try:
        args = rw.get_values(message.from_user.id)
        send_simple(
            subreddit_name=args.get(b"subreddit_name").decode("utf-8"),
            submission_sort=args.get(b"sorting").decode("utf-8"),
            limit=int(args.get(b"count").decode("utf-8")),
            where_to_post=config.ADMIN_ID,
            source="reddit"
        )
        rw.set_state(
            id=message.from_user.id,
            value=config.States.START_STATE.value
        )
    except Redirect:
        bot.send_message(
            chat_id=config.ADMIN_ID,
            text="There is no subreddit with that name, try another one",
            reply_markup=m.choose_channel_markup,
            parse_mode="markdown",
            disable_notification=True
        )
        rw.set_state(
            id=message.from_user.id,
            value=config.States.ENTER_SUBREDDIT_STATE.value
        )

    rw.clear_fields(
        message.from_user.id,
        "subreddit_name", "sorting", "count"
    )


def send_simple(
        subreddit_name: str,
        submission_sort: str,
        limit: int,
        where_to_post: str,
        source: str):

    submissions = get_full_info(
        subreddit_name=subreddit_name,
        submission_sort=submission_sort,
        limit=limit
    )

    for submission in submissions:
        if where_to_post == config.ADMIN_ID:
            markup = m.forward_to_channel_markup
            notification = True
            caption = \
                f'{submission["title"]}\n[Source]({submission["permalink"]})'
        else:
            markup = None
            notification = False
            caption = None

        submission_type = submission.get("content_type")

        if submission["domain"] == cs.GFY_DOMAIN:
            attach = submission.get("video_link")
        else:
            attach = submission.get("url")

        try:
            if submission_type == cs.IMG_TYPE:
                bot.send_photo(
                    chat_id=where_to_post,
                    photo=attach,
                    caption=caption,
                    reply_markup=markup,
                    parse_mode="markdown",
                    disable_notification=notification
                )
            elif submission_type == cs.GIF_TYPE:
                bot.send_video(
                    chat_id=where_to_post,
                    data=attach,
                    caption=caption,
                    reply_markup=markup,
                    parse_mode="markdown",
                    disable_notification=notification
                )
        except ApiException:
            attach = download_file(attach, source, subreddit_name)
            if submission_type == cs.IMG_TYPE:
                try:
                    with open(attach, "rb") as attach:
                        bot.send_photo(
                            chat_id=where_to_post,
                            photo=attach,
                            caption=caption,
                            reply_markup=markup,
                            parse_mode="markdown",
                            disable_notification=notification
                        )
                except ApiException:
                    attach = iw.resize_image(attach)
                    with open(attach, "rb") as attach:
                        bot.send_photo(
                            chat_id=where_to_post,
                            photo=attach,
                            caption=caption,
                            reply_markup=markup,
                            parse_mode="markdown",
                            disable_notification=notification
                        )
            elif submission_type == cs.GIF_TYPE:
                with open(attach, "rb") as attach:
                    bot.send_video(
                        chat_id=where_to_post,
                        data=attach,
                        caption=caption,
                        reply_markup=markup,
                        parse_mode="markdown",
                        disable_notification=notification,
                        timeout=150
                    )

        if submission_type == cs.TEXT_TYPE or submission_type == cs.OTHER_TYPE:
            bot.send_message(
                chat_id=where_to_post,
                text=caption,
                parse_mode="markdown",
                disable_notification=notification
            )
        sleep(0.5)


@bot.callback_query_handler(func=lambda call: call.data == cs.FORWARD)
def callback_forward(call: types.CallbackQuery):
    if call.message:
        # print(call.message.json[content_type])
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=m.when_forward_markup
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.FORWARD_NOW)
def callback_forward_now(call: types.CallbackQuery):
    if call.message:
        # print(call.message.json[content_type])
        content_type = call.message.content_type
        if content_type == "photo":
            attach = call.message.json[content_type][0]["file_id"]
            bot.send_photo(
                chat_id=config.CHANNEL_ID,
                photo=attach,
                caption=None,
                disable_notification=True
            )
        elif content_type == "video":
            attach = call.message.json[content_type]["file_id"]
            bot.send_video(
                chat_id=config.CHANNEL_ID,
                data=attach,
                disable_notification=True,
            )
        elif content_type == "document":
            attach = call.message.json[content_type]["file_id"]
            bot.send_document(
                chat_id=config.CHANNEL_ID,
                data=attach,
                disable_notification=True,
            )
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.QUEUE)
def callback_queue(call: types.CallbackQuery):
    if call.message:
        pass


@bot.callback_query_handler(func=lambda call: call.data == cs.CANCEL)
def callback_cancel(call: types.CallbackQuery):
    if call.message:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=m.forward_to_channel_markup
        )


@bot.message_handler(func=lambda message: True)
def echo(message: types.Message):
    bot.reply_to(message, message.text)


if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=False, timeout=50)
        except Exception as e:
            print(f"Exception: {e}")
            sleep(52)