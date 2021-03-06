import json
import logging
import logging.config
from time import sleep

import telebot
from prawcore.exceptions import NotFound, Redirect
from telebot import types
from telebot.apihelper import ApiException

import config
import constants as cs
import image_worker as iw
import instagram_supplier as inst
import markups as m
import redis_worker as rw
from config import States
from decorators import retry
from reddit_supplier import get_full_info
from redis_worker import queue_len
from utils import download_file, get_html

bot = telebot.TeleBot(token=config.TOKEN)

bot.remove_webhook()
sleep(2)
bot.set_webhook(
    url=f"{config.WEBHOOK_URL_BASE}{config.WEBHOOK_URL_PATH}"
)

logging.config.dictConfig(config=cs.dict_log_config)
logger = logging.getLogger("bot_logger")


@bot.message_handler(
    func=lambda message: message.from_user.id not in config.ADMINS,
    content_types=["text", "audio", "document",
                   "photo", "sticker", "video", "video_note"])
@retry
def answer_not_admin(message: types.Message):
    reply_text = "Hi there! I am a bot. If you are not one of my admins,\
 you have nothing to do here. Please, leave me alone."
    text_to_owner = f"User @{message.chat.username} `({message.chat.first_name}\
 {message.chat.last_name})` with ID: `{message.chat.id}` sent me\
 a message: {message.text if message.text else message.content_type}"

    # answering to user
    bot.reply_to(message=message, text=reply_text)
    # notifying the owner of an attempt to start the bot
    bot.send_message(
        chat_id=config.OWNER_ID,
        text=text_to_owner,
        parse_mode="markdown"
    )
    if message.content_type != "text":
        bot.forward_message(
            chat_id=config.OWNER_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

    logger.info(f"User @{message.chat.username} `({message.chat.first_name}\
 {message.chat.last_name})` with ID: `{message.chat.id}` sent me\
 a message: {message.text if message.text else message.content_type}")


@bot.message_handler(commands=["start"])
@retry
def start(message: types.Message):
    welcome = f"Hello, {message.from_user.first_name}.\n{cs.welcome_message}"
    bot.send_message(
        chat_id=message.from_user.id,
        text=welcome,
        reply_markup=m.start_markup,
        parse_mode="markdown",
        disable_notification=True
    )

    rw.set_state(
        id=message.from_user.id,
        value=States.START_STATE.value
    )
    logger.info(
        f"Bot was started by user {message.chat.username} with ID: {message.chat.id}")


@bot.message_handler(commands=["help"])
@retry
def help(message: types.Message):
    text = "*Commands:*\n"
    for key, value in cs.commands.items():
        text += f"{key} — {value}\n"

    bot.send_message(
        chat_id=message.from_user.id,
        text=text,
        reply_markup=m.start_markup,
        parse_mode="markdown",
        disable_notification=True
    )


@bot.message_handler(commands={"settings"})
@retry
def settings(message: types.Message):
    text = "Here is some setting:"
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=m.settings_markup,
        disable_notification=True
    )
    rw.set_state(
        id=message.from_user.id,
        value=States.START_STATE.value
    )


@bot.message_handler(commands=["insta", "i"])
@retry
def instagram(message: types.Message):
    try:
        insta_link = message.text.split()[1]

        html = get_html(insta_link).text
        data = inst.process_scripts(html)
        links = inst.process_shared_data(data)

        for link in links:
            send_from_insta(
                chat_id=message.chat.id,
                link=link
            )

        bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        logger.info(
            f"Command: /insta. User {message.chat.username}, ID: {message.chat.id} sent links {links}")
    except IndexError:
        logger.info(
            f"Empty /insta command. User {message.chat.username}, ID: {message.chat.id}")
        bot.send_message(
            chat_id=message.chat.id,
            text="You did not send me a link after /insta command word. Try again.",
            reply_to_message_id=message.message_id,
            disable_notification=True
        )


@bot.message_handler(commands=["reddit", "r"])
@retry
def choose_commands(message: types.Message):
    markup = m.generate_kboard(
        kboard_type="reply",
        id=message.chat.id,
        key="channels"
    )
    bot.send_message(
        chat_id=message.from_user.id,
        text="what subreddit would you like?",
        reply_markup=markup,
        disable_notification=True
    )
    rw.set_state(id=message.from_user.id,
                 value=States.ENTER_SUBREDDIT_STATE.value)


@bot.message_handler(commands=["redis"])
@retry
def redis(message: types.Message):
    queue_len = rw.queue_len(key="queue")
    queue_entities = rw.queue_entities(key="queue")

    content = {
        "photo": 0,
        "video": 0,
        "document": 0
    }
    for entity in queue_entities:
        content[entity["content_type"]] += 1

    text = f"Queue lenght: {queue_len}\n\
 |Photo: {content['photo']}\n |Video: {content['video']}\n\
 |Document: {content['document']}"
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        disable_notification=True
    )


@bot.message_handler(content_types=["photo", "video", "document"])
def process_sent_photo(message: types.Message):
    content_type = message.content_type
    try:
        file_id = message.json[content_type][-1]["file_id"]
    except KeyError:
        file_id = message.json[content_type]["file_id"]

    send_with_file_id(
        chat_id=message.chat.id,
        content_type=content_type,
        file_id=file_id,
        reply_markup=m.forward_to_channel_markup
    )
    logger.info(f"User {message.chat.username}, ID: {message.chat.id}.\
 Sent file[{message.content_type}], file_id[{file_id}]")
    bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id
    )


@bot.message_handler(
    func=lambda message: rw.get_current_state(message.from_user.id) == States.ENTER_SUBREDDIT_STATE.value)
@retry
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
@retry
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
            text="What you are entering is not a number, try again",
            reply_to_message_id=message.message_id,
            reply_markup=m.choose_count_markup,
            disable_notification=True
        )
    elif int(message.text) < 1 or int(message.text) > 25:
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


@bot.message_handler(
    func=lambda message: rw.get_current_state(message.from_user.id) == States.ADD_SUBREDDIT_STATE.value)
def adding_subreddit_button(message: types.Message):
    add_button = m.set_kboard(
        id=message.chat.id,
        key="channels",
        value=message.text
    )
    rw.set_state(
        id=message.chat.id,
        value=States.START_STATE.value
    )
    if add_button:
        bot.send_message(
            chat_id=message.chat.id,
            text="The button was added",
            disable_notification=True
        )


@bot.message_handler(
    func=lambda message: rw.get_current_state(message.from_user.id) == States.DELETE_SUBREDDIT_STATE.value)
def deleting_subreddit_button(message: types.Message):
    del_button = m.delete_button(
        id=message.chat.id,
        key="channels",
        value=message.text
    )
    rw.set_state(
        id=message.chat.id,
        value=States.START_STATE.value
    )
    if del_button:
        bot.send_message(
            chat_id=message.chat.id,
            text="The button was deleted",
            disable_notification=True
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.FORWARD)
@retry
def callback_forward(call: types.CallbackQuery):
    if call.message:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=m.when_forward_markup
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.FORWARD_NOW)
@retry
def callback_forward_now(call: types.CallbackQuery):
    if call.message:
        content_type = call.message.content_type
        try:
            file_id = call.message.json[content_type][-1]["file_id"]
        except KeyError:
            file_id = call.message.json[content_type]["file_id"]

        send_with_file_id(
            chat_id=config.CHANNEL_ID,
            content_type=content_type,
            file_id=file_id
        )
        logger.info(
            f"Forwarded to channel: channel[{config.CHANNEL_ID}], content_type[{content_type}], file_id[{file_id}]")
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=m.forwarded_markup
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.QUEUE)
@retry
def callback_queue(call: types.CallbackQuery):
    if call.message:
        content_type = call.message.content_type
        try:
            file_id = call.message.json[content_type][-1]["file_id"]
        except KeyError:
            file_id = call.message.json[content_type]["file_id"]

        data = json.dumps({"content_type": content_type, "file_id": file_id})

        rw.add_to_queue(
            name="queue",
            data=data
        )
        logger.info(
            f"Added to queue: content_type[{content_type}], file_id[{file_id}]")
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=m.no_queue_markup
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.CANCEL)
def callback_cancel(call: types.CallbackQuery):
    if call.message:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=m.forward_to_channel_markup
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.OUT)
def callback_out_of_settings(call: types.CallbackQuery):
    if call.message:
        bot.delete_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.delete_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id-1
        )


@bot.callback_query_handler(func=lambda call: call.data == cs.ADD_SUBREDDIT)
def add_subreddit_button(call: types.CallbackQuery):
    if call.message:
        text = "What subreddit button would you like to add? Send me a text message."
        bot.send_message(
            chat_id=call.message.chat.id,
            text=text,
            disable_notification=True
        )

        rw.set_state(id=call.message.chat.id,
                     value=States.ADD_SUBREDDIT_STATE.value)


@bot.callback_query_handler(func=lambda call: call.data == cs.DELETE_SUBREDDIT)
def delete_subreddit_button(call: types.CallbackQuery):
    if call.message:
        text = "What subreddit button would you like to delete? Send me a text message."
        bot.send_message(
            chat_id=call.message.chat.id,
            text=text,
            disable_notification=True
        )

        rw.set_state(id=call.message.chat.id,
                     value=States.DELETE_SUBREDDIT_STATE.value)


def send_reddit_photo(message: types.Message):
    try:
        args = rw.get_values(message.from_user.id)
        logger.info(f'Command: /reddit. User {message.chat.username}\
 ID: {message.chat.id}.\
 Subreddit name: {args.get(b"subreddit_name").decode("utf-8")},\
 sorting: {args.get(b"sorting").decode("utf-8")},\
 count: {int(args.get(b"count").decode("utf-8"))}')
        send_simple(
            subreddit_name=args.get(b"subreddit_name").decode("utf-8"),
            submission_sort=args.get(b"sorting").decode("utf-8"),
            limit=int(args.get(b"count").decode("utf-8")),
            where_to_post=message.from_user.id,
            source="reddit"
        )
        rw.set_state(
            id=message.from_user.id,
            value=config.States.START_STATE.value
        )
        logger.info(f'Command: /reddit. User {message.chat.username}\
 ID: {message.chat.id}. Status: Done')

    except (Redirect, NotFound) as e:
        markup = m.generate_kboard(
            kboard_type="reply",
            id=message.chat.id,
            key="channels"
        )
        bot.send_message(
            chat_id=message.from_user.id,
            text="There is no subreddit with that name, try another one",
            reply_markup=markup,
            parse_mode="markdown",
            disable_notification=True
        )
        logger.info(f'{repr(e)}. Command: /reddit. User {message.chat.username}\
 ID: {message.chat.id}.\
 Subreddit name: {args.get(b"subreddit_name").decode("utf-8")},\
 sorting: {args.get(b"sorting").decode("utf-8")},\
 count: {int(args.get(b"count").decode("utf-8"))}')
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
        if where_to_post in config.ADMINS:
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

        logger.info(f"file: {attach}, content type: {submission_type}")
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
        except ApiException as e:
            logger.error(repr(e))
            attach = download_file(attach, source, subreddit_name)
            logger.info(f"Downloaded file: {attach}")
            if submission_type == cs.IMG_TYPE:
                try:
                    with open(attach, "rb") as file:
                        # in handling exception file doesn`t close
                        # if attach name and "as attach" are the same
                        # -> "seek of closed file" exception
                        bot.send_photo(
                            chat_id=where_to_post,
                            photo=file,
                            caption=caption,
                            reply_markup=markup,
                            parse_mode="markdown",
                            disable_notification=notification
                        )
                except ApiException as e:
                    logger.error(repr(e))
                    attach = iw.resize_image(attach)
                    with open(attach, "rb") as file:
                        bot.send_photo(
                            chat_id=where_to_post,
                            photo=file,
                            caption=caption,
                            reply_markup=markup,
                            parse_mode="markdown",
                            disable_notification=notification
                        )
            elif submission_type == cs.GIF_TYPE:
                with open(attach, "rb") as file:
                    bot.send_video(
                        chat_id=where_to_post,
                        data=file,
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


@retry
def send_with_file_id(chat_id, content_type, file_id, reply_markup=None):
    if content_type == "photo":
        bot.send_photo(
            chat_id=chat_id,
            photo=file_id,
            reply_markup=reply_markup,
            disable_notification=True
        )
    elif content_type == "video":
        bot.send_video(
            chat_id=chat_id,
            data=file_id,
            reply_markup=reply_markup,
            disable_notification=True,
        )
    elif content_type == "document":
        bot.send_document(
            chat_id=chat_id,
            data=file_id,
            reply_markup=reply_markup,
            disable_notification=True,
        )


def send_from_insta(chat_id, link):
    if "jpg" in link:
        bot.send_photo(
            chat_id=chat_id,
            photo=link,
            reply_markup=m.forward_to_channel_markup,
            disable_notification=True
        )
    elif "mp4" in link:
        bot.send_video(
            chat_id=chat_id,
            data=link,
            reply_markup=m.forward_to_channel_markup,
            disable_notification=True
        )


def checking_queue_len():
    queue_lenght = queue_len("queue")

    if queue_lenght <= 10:
        for admin in config.ADMINS:
            bot.send_message(
                chat_id=admin,
                text="Queue lenght is smaller than 14. Add some new posts.",
                disable_notification=False
            )


@bot.message_handler(func=lambda message: True)
def echo(message: types.Message):
    if message.json["entities"][0]["type"] == "url":
        try:
            send_from_insta(message.chat.id, message.text)
            bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
        except Exception:
            bot.reply_to(message, message.text)
    else:
        bot.reply_to(message, message.text)


# @bot.callback_query_handler(func=lambda call: call.data == cs.ADD_WHERE_TO)
# def add_where_to_button(call: types.CallbackQuery):
#     if call.data:
#         text = f"You have to send me two words with a space between them.\n\
# For instance, CHANNEL\_NAME @channelname.\n\n \
# CHANNEL\_NAME is what you want to see as a button text.\n\n \
# @channelname is your channel name and link where I am gonna send your posts."
#         bot.send_message(
#             chat_id=call.message.chat.id,
#             text=text,
#             parse_mode="markdown",
#             disable_notification=True
#         )
#
#         rw.set_state(id=call.message.chat.id,
#                      value=States.ADD_WHERE_TO_STATE.value)


# @bot.message_handler(
#     func=lambda message: rw.get_current_state(message.from_user.id) == States.ADD_WHERE_TO_STATE.value)
# def adding_where_to(message: types.Message):
#     button = message.text.split()
#     if button[1].startswith("@") or button[1].startswith("-"):
#         button = {"text": button[0], "callback_data": button[1]}
#     else:
#         button = {"text": button[0], "callback_data": f"@{button[1]}"}
#
#     add_button = m.set_kboard(
#         id=message.chat.id,
#         key="where_to",
#         value=button
#     )
#     rw.set_state(
#         id=message.chat.id,
#         value=States.START_STATE.value
#     )
#     if add_button:
#         bot.send_message(
#             chat_id=message.chat.id,
#             text="The button was added",
#             disable_notification=True
#         )


# @bot.callback_query_handler(func=lambda call: call.data == cs.DELETE_WHERE_TO)
# def delete_where_to_button(call: types.CallbackQuery):
#     pass


# @bot.message_handler(
#     func=lambda message: rw.get_current_state(message.from_user.id) == States.DELETE_WHERE_TO_STATE.value)
# def deleting_where_to(message: types.Message):
#     pass


if __name__ == "__main__":
    pass
    # bot.polling(none_stop=False, timeout=50)
