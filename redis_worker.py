import json

import redis

import config

redis = redis.Redis(db=1)


def set_state(id, value):
    redis.hset(id, "state", value)
    return True


def set_kboard(id, key, value):
    try:
        kboard = json.loads(get_value(id, key))
        kboard.append(value)
    except TypeError:
        kboard = [value]

    set_state_value(id, key, json.dumps(kboard))
    return True


def get_current_state(id):
    try:
        return redis.hget(id, "state").decode("utf-8")
    except Exception as e:
        print(f"Exception: {e}")
        return config.States.START_STATE.value


def set_state_value(id, key, value):
    redis.hset(id, key, value)
    return True


def get_value(id, key):
    return redis.hget(id, key)


def get_values(id):
    return redis.hgetall(id)


def clear_fields(id, *args):
    redis.hdel(id, *args)
    return True


def add_to_queue(name, data):
    # добавляем в лист rpush
    redis.rpush(name, data)
    return True


def get_from_queue(name):
    # удаляем и возвращаем первое значение в лист lpop
    if redis.llen(name) > 0:
        file = json.loads(redis.lpop(name))
        return file
    else:
        return False


if __name__ == "__main__":
    pass
