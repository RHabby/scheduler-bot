import config as c
from redis_worker import queue_len
from tg_sender import bot


def checking_queue_len():
    queue_lenght = queue_len("queue")

    if queue_lenght <= 14:
        for admin in c.ADMINS:
            bot.send_message(
                chat_id=admin,
                text="Queue lenght is smaller than 14. Add some new posts.",
                disable_notification=False
            )
