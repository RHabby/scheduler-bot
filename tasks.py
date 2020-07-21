from time import sleep

from celery import Celery
from celery.schedules import crontab

import config
import redis_worker as rw
from tg_bot import checking_queue_len, send_with_file_id

celery_app = Celery("tasks", broker="redis://localhost")

celery_app.conf.beat_schedule = {
    # executes every hour
    "every_hour": {
        "task": "send_from_queue",
        "schedule": crontab(minute='*/30')
    },
    "every_ten_hours": {
        "task": "check_queue_len",
        "schedule": crontab(minute="1", hour="*/10")
    }
}


@celery_app.task(name="send_from_queue")
def send_from_queue():
    file = rw.get_from_queue("queue")
    print(
        f"content_type: {file.get('content_type')}, file_id:{file.get('file_id')}")
    if file:
        try:
            send_with_file_id(
                chat_id=config.CHANNEL_ID,
                content_type=file.get("content_type"),
                file_id=file.get("file_id")
            )
        except Exception as e:
            print(f"Exceprion: {e}")
            sleep(2)
            send_with_file_id(
                chat_id=config.CHANNEL_ID,
                content_type=file.get("content_type"),
                file_id=file.get("file_id")
            )


@celery_app.task(name="check_queue_len")
def check_queue_len():
    checking_queue_len()
