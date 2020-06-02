from celery import Celery
from celery.schedules import crontab

import redis_worker as rw
from tg_sender import send_with_file_id

celery_app = Celery("tasks", broker="redis://localhost")

celery_app.conf.beat_schedule = {
    # executes every hour
    "every_hour": {
        "task": "send_from_queue",
        "schedule": crontab(minute='*/80')
    }
}


@celery_app.task(bind=True,
                 name="send_from_queue",
                 autoretry_for=(Exception,),
                 retry_kwargs={"max_retries": 3, "countdown": 2})
def send_from_queue():
    file = rw.get_from_queue("queue")
    if file:
        try:
            send_with_file_id(
                content_type=file.get("content_type"),
                file_id=file.get("file_id")
            )
        except Exception:
            pass
