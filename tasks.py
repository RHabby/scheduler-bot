from time import sleep

from celery import Celery
from celery.schedules import crontab

import config
import redis_worker as rw
from tg_bot import checking_queue_len, send_with_file_id
from utils import control_folder_size

celery_app = Celery("tasks", broker="redis://localhost")

celery_app.conf.beat_schedule = {
    "send_telegram": {
        "task": "send_telegram",
        "schedule": crontab(minute='*/45')
    },
    "check_telegram_queue": {
        "task": "check_telegram_queue",
        "schedule": crontab(minute=0, hour="*/1")
    },
    "every_day": {
        "task": "control_attach_folder_size",
        "schedule": crontab(minute=0, hour=0)
    }
}


@celery_app.task(name="send_telegram")
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


@celery_app.task(name="check_telegram_queue")
def check_queue_len():
    checking_queue_len()


@celery_app.task(name="control_attach_folder_size")
def control_attach_folder_size():
    control_folder_size(folder=config.ATTACH_FOLDER)
