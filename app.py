import logging
import logging.config

import flask
from telebot import types

import config
from tg_bot import bot

app = flask.Flask(__name__)

# logging.config.dictConfig(config=cs.dict_log_config)
# logger = logging.getLogger("bot_logger")


@app.route("/", methods=["GET", "HEAD"])
def index():
    # print(flask.request.headers.get("X-Forwarded-For"))
    return "Hello"


@app.route(config.WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if flask.request.headers.get("content-type") == "application/json":
        json_string = flask.request.get_data().decode("utf-8")
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ""
    else:
        flask.abort(403)


if __name__ == "__main__":
    logging.basicConfig(filename="./logs/flask_logs.log", level=logging.INFO)
    app.run(debug=True)
